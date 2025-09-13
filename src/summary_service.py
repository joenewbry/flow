"""
Summary Service for Flow CLI
Handles generation and retrieval of screen activity summaries
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from lib.chroma_client import chroma_client
from lib.ollama_client import ollama_client

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SummaryService:
    def __init__(self):
        self.ollama_model = "gemma2:9b"
        self.screenhistory_dir = Path("data/screen_history")
        self.summaries_dir = Path("data/summaries")
        self.max_tokens_per_summary = 8000  # Conservative limit for Ollama
        self.chars_per_token = 4  # Rough estimate
        self.max_chars_per_summary = self.max_tokens_per_summary * self.chars_per_token
        self.last_summary_check = None  # Track when we last checked for summaries
        
    async def init(self):
        """Initialize the summary service."""
        # Check if Ollama is running and model is available
        if not ollama_client.health_check():
            raise ValueError("Ollama service is not running. Start with: brew services start ollama")
        
        if not ollama_client.is_model_available(self.ollama_model):
            raise ValueError(f"Model '{self.ollama_model}' is not available. Download with: ollama pull {self.ollama_model}")
        
        # Ensure directories exist
        await self._ensure_summary_dirs()
        
        # Initialize ChromaDB
        await chroma_client.init()
    
    async def _ensure_summary_dirs(self):
        """Ensure summary directories exist."""
        dirs = [
            self.summaries_dir,
            self.summaries_dir / "hourly",
            self.summaries_dir / "daily",
            self.summaries_dir / "monthly",
            self.summaries_dir / "yearly"
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _convert_filename_timestamp_to_iso(self, timestamp_str: str) -> str:
        """Convert filename-style timestamps to ISO 8601."""
        if not isinstance(timestamp_str, str):
            return timestamp_str
        
        # Check if already in ISO format
        if ('T' in timestamp_str and ':' in timestamp_str and 
            ('.' in timestamp_str or timestamp_str.endswith('Z'))):
            try:
                datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return timestamp_str
            except ValueError:
                pass
        
        # Parse filename format
        parts = timestamp_str.split('T')
        if len(parts) != 2:
            return timestamp_str
        
        time_part = parts[1]
        z_suffix = 'Z' if time_part.endswith('Z') else ''
        if z_suffix:
            time_part = time_part[:-1]
        
        time_segments = time_part.split('-')
        if len(time_segments) == 4:
            return f"{parts[0]}T{time_segments[0]}:{time_segments[1]}:{time_segments[2]}.{time_segments[3]}{z_suffix}"
        elif len(time_segments) == 3:
            return f"{parts[0]}T{time_segments[0]}:{time_segments[1]}:{time_segments[2]}{z_suffix}"
        
        return timestamp_str
    
    def _get_hour_key(self, dt: datetime) -> str:
        """Get hour key for caching."""
        return dt.strftime('%Y-%m-%d-%H')
    
    def _get_summary_file_path(self, hour_key: str) -> Path:
        """Get summary file path."""
        return self.summaries_dir / f"{hour_key}.json"
    
    def _get_hourly_summary_file_path(self, hour_start: datetime) -> Path:
        """Get hourly summary file path."""
        day_hour = hour_start.strftime('%Y-%m-%d-%H')
        return self.summaries_dir / "hourly" / f"{day_hour}.txt"
    
    def _get_daily_summary_file_path(self, day: datetime) -> Path:
        """Get daily summary file path."""
        day_str = day.strftime('%Y-%m-%d')
        return self.summaries_dir / "daily" / f"{day_str}.txt"
    
    async def _read_json_files_in_time_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Read and parse JSON files within a time range."""
        if not self.screenhistory_dir.exists():
            logger.warning(f"Screen history directory not found: {self.screenhistory_dir}")
            return []
        
        data_entries = []
        
        try:
            json_files = list(self.screenhistory_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files in {self.screenhistory_dir}")
            
            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content or content == 'null':
                        continue
                    
                    data = json.loads(content)
                    
                    if not isinstance(data, dict) or 'timestamp' not in data:
                        continue
                    
                    # Convert timestamp to ISO format
                    timestamp_str = self._convert_filename_timestamp_to_iso(data['timestamp'])
                    
                    try:
                        file_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if file_time.tzinfo is None:
                            file_time = file_time.replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        logger.warning(f"Invalid timestamp in {file_path}: {timestamp_str}")
                        continue
                    
                    # Check if within time range
                    if start_time <= file_time <= end_time:
                        data['timestamp'] = timestamp_str
                        data_entries.append(data)
                
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"Error reading {file_path}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error reading {file_path}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scanning directory {self.screenhistory_dir}: {e}")
        
        # Sort by timestamp
        data_entries.sort(key=lambda x: x['timestamp'])
        logger.info(f"Found {len(data_entries)} entries in time range")
        
        return data_entries
    
    async def _generate_summary_with_ai(self, content: str, summary_type: str, time_info: str) -> str:
        """Generate summary using AI."""
        try:
            prompt = f"""
You are analyzing screen activity data for a {summary_type} summary covering {time_info}.

Please analyze the following screen capture data and provide a comprehensive summary:

{content}

Provide a summary that includes:
1. **Overview**: Brief description of main activities
2. **Applications Used**: Primary applications and tools
3. **Key Activities**: Important tasks or workflows identified
4. **Productivity Insights**: Patterns, focus areas, or notable behaviors
5. **Time Distribution**: How time was spent across different activities

Keep the summary concise but informative, focusing on actionable insights.
"""

            system_msg = "You are Flow's AI assistant specialized in analyzing screen activity data and generating insightful summaries."

            response = await asyncio.to_thread(
                ollama_client.generate,
                model=self.ollama_model,
                prompt=prompt,
                system=system_msg
            )
            
            return response
            
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            return f"Summary generation failed: {str(e)}"
    
    def _truncate_content_for_ai(self, content: str, max_chars: int = None) -> str:
        """Truncate content to fit within AI token limits."""
        if max_chars is None:
            max_chars = self.max_chars_per_summary
        
        if len(content) <= max_chars:
            return content
        
        # Truncate and add notice
        truncated = content[:max_chars - 200]
        truncated += f"\n\n[Content truncated - original length: {len(content)} chars, showing first {len(truncated)} chars]"
        
        return truncated
    
    async def get_daily_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Get daily summary for a specific date."""
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        else:
            target_date = datetime.now(timezone.utc)
        
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Check if summary already exists
        summary_file = self._get_daily_summary_file_path(target_date)
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    existing_summary = f.read()
                
                return {
                    "date": target_date.strftime('%Y-%m-%d'),
                    "summary": existing_summary,
                    "cached": True,
                    "entry_count": 0
                }
            except Exception as e:
                logger.warning(f"Error reading cached summary: {e}")
        
        # Generate new summary
        entries = await self._read_json_files_in_time_range(start_time, end_time)
        
        if not entries:
            return {
                "date": target_date.strftime('%Y-%m-%d'),
                "summary": "No screen activity data found for this date.",
                "cached": False,
                "entry_count": 0
            }
        
        # Prepare content for AI
        content_parts = []
        for entry in entries:
            timestamp = entry.get('timestamp', 'Unknown time')
            summary = entry.get('summary', 'No summary')
            app = entry.get('active_app', 'Unknown app')
            extracted_text = entry.get('extracted_text', '')[:200]  # Limit text length
            
            content_parts.append(f"[{timestamp}] {app}: {summary}")
            if extracted_text:
                content_parts.append(f"  Text: {extracted_text}")
        
        content = '\n'.join(content_parts)
        content = self._truncate_content_for_ai(content)
        
        # Generate AI summary
        ai_summary = await self._generate_summary_with_ai(
            content, 
            "daily", 
            target_date.strftime('%Y-%m-%d')
        )
        
        # Cache the summary
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(ai_summary)
        except Exception as e:
            logger.error(f"Error caching daily summary: {e}")
        
        return {
            "date": target_date.strftime('%Y-%m-%d'),
            "summary": ai_summary,
            "cached": False,
            "entry_count": len(entries)
        }
    
    async def get_time_range_summary(self, start_time_str: str, end_time_str: str) -> Dict[str, Any]:
        """Get summary for a custom time range."""
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
                
        except ValueError as e:
            raise ValueError(f"Invalid time format: {e}")
        
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
        
        entries = await self._read_json_files_in_time_range(start_time, end_time)
        
        if not entries:
            return {
                "start_time": start_time_str,
                "end_time": end_time_str,
                "summary": "No screen activity data found for this time range.",
                "entry_count": 0
            }
        
        # Prepare content for AI
        content_parts = []
        for entry in entries:
            timestamp = entry.get('timestamp', 'Unknown time')
            summary = entry.get('summary', 'No summary')
            app = entry.get('active_app', 'Unknown app')
            extracted_text = entry.get('extracted_text', '')[:200]
            
            content_parts.append(f"[{timestamp}] {app}: {summary}")
            if extracted_text:
                content_parts.append(f"  Text: {extracted_text}")
        
        content = '\n'.join(content_parts)
        content = self._truncate_content_for_ai(content)
        
        # Generate AI summary
        duration = end_time - start_time
        time_info = f"{start_time_str} to {end_time_str} (duration: {duration})"
        
        ai_summary = await self._generate_summary_with_ai(content, "time range", time_info)
        
        return {
            "start_time": start_time_str,
            "end_time": end_time_str,
            "summary": ai_summary,
            "entry_count": len(entries),
            "duration": str(duration)
        }
    
    async def get_last_hours_summary(self, hours: int) -> Dict[str, Any]:
        """Get summary for the last N hours."""
        if hours < 1 or hours > 168:
            raise ValueError("Hours must be between 1 and 168 (1 week)")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        return await self.get_time_range_summary(
            start_time.isoformat(),
            end_time.isoformat()
        )
    
    async def get_hourly_summary(self, hour_str: str) -> Dict[str, Any]:
        """Get summary for a specific hour."""
        # Validate hour format
        if not re.match(r'^\d{4}-\d{2}-\d{2}-\d{2}$', hour_str):
            raise ValueError("Hour must be in YYYY-MM-DD-HH format")
        
        try:
            # Parse hour string
            year, month, day, hour = map(int, hour_str.split('-'))
            start_time = datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)
            end_time = start_time + timedelta(hours=1)
            
        except ValueError as e:
            raise ValueError(f"Invalid hour format: {e}")
        
        # Check if summary already exists
        summary_file = self._get_hourly_summary_file_path(start_time)
        if summary_file.exists():
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    existing_summary = f.read()
                
                return {
                    "hour": hour_str,
                    "summary": existing_summary,
                    "cached": True,
                    "entry_count": 0
                }
            except Exception as e:
                logger.warning(f"Error reading cached hourly summary: {e}")
        
        # Generate new summary
        entries = await self._read_json_files_in_time_range(start_time, end_time)
        
        if not entries:
            return {
                "hour": hour_str,
                "summary": "No screen activity data found for this hour.",
                "cached": False,
                "entry_count": 0
            }
        
        # Prepare content for AI
        content_parts = []
        for entry in entries:
            timestamp = entry.get('timestamp', 'Unknown time')
            summary = entry.get('summary', 'No summary')
            app = entry.get('active_app', 'Unknown app')
            extracted_text = entry.get('extracted_text', '')[:200]
            
            content_parts.append(f"[{timestamp}] {app}: {summary}")
            if extracted_text:
                content_parts.append(f"  Text: {extracted_text}")
        
        content = '\n'.join(content_parts)
        content = self._truncate_content_for_ai(content)
        
        # Generate AI summary
        ai_summary = await self._generate_summary_with_ai(
            content,
            "hourly",
            f"{hour_str}:00-{hour_str}:59"
        )
        
        # Cache the summary
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(ai_summary)
        except Exception as e:
            logger.error(f"Error caching hourly summary: {e}")
        
        return {
            "hour": hour_str,
            "summary": ai_summary,
            "cached": False,
            "entry_count": len(entries)
        }
    
    async def ensure_summaries_up_to_date(self) -> Dict[str, Any]:
        """Ensure all summaries are up to date, generating missing ones."""
        logger.info("Checking for missing summaries...")
        
        current_time = datetime.now(timezone.utc)
        stats = {
            "hourly_generated": 0,
            "daily_generated": 0,
            "errors": 0,
            "last_check": current_time.isoformat()
        }
        
        try:
            # Generate missing hourly summaries
            hourly_stats = await self._catch_up_hourly_summaries(current_time)
            stats["hourly_generated"] = hourly_stats["generated"]
            stats["errors"] += hourly_stats["errors"]
            
            # Generate missing daily summaries 
            daily_stats = await self._catch_up_daily_summaries(current_time)
            stats["daily_generated"] = daily_stats["generated"]
            stats["errors"] += daily_stats["errors"]
            
            # Store summaries in ChromaDB
            await self._sync_summaries_to_chroma()
            
            self.last_summary_check = current_time
            logger.info(f"Summary catch-up complete: {stats['hourly_generated']} hourly, {stats['daily_generated']} daily")
            
        except Exception as e:
            logger.error(f"Error during summary catch-up: {e}")
            stats["errors"] += 1
        
        return stats
    
    async def _catch_up_hourly_summaries(self, current_time: datetime) -> Dict[str, int]:
        """Generate missing hourly summaries up to current time."""
        stats = {"generated": 0, "errors": 0}
        
        # Find the earliest data point
        earliest_data = await self._find_earliest_data_timestamp()
        if not earliest_data:
            logger.info("No data found, skipping hourly summary catch-up")
            return stats
        
        # Start from the hour of earliest data
        start_hour = earliest_data.replace(minute=0, second=0, microsecond=0)
        current_hour = current_time.replace(minute=0, second=0, microsecond=0)
        
        # Don't generate summary for current incomplete hour
        if current_hour == current_time.replace(minute=0, second=0, microsecond=0):
            current_hour -= timedelta(hours=1)
        
        hour = start_hour
        while hour <= current_hour:
            hour_str = self._get_hour_key(hour)
            summary_file = self._get_hourly_summary_file_path(hour)
            
            if not summary_file.exists():
                try:
                    logger.info(f"Generating missing hourly summary for {hour_str}")
                    result = await self.get_hourly_summary(hour_str)
                    if result.get("entry_count", 0) > 0:
                        stats["generated"] += 1
                        
                        # Store in ChromaDB
                        await self._store_summary_in_chroma(
                            "hourly_summaries",
                            hour_str,
                            result["summary"],
                            {
                                "timestamp": hour.isoformat(),
                                "hour": hour_str,
                                "entry_count": result["entry_count"],
                                "type": "hourly"
                            }
                        )
                        
                except Exception as e:
                    logger.error(f"Error generating hourly summary for {hour_str}: {e}")
                    stats["errors"] += 1
            
            hour += timedelta(hours=1)
        
        return stats
    
    async def _catch_up_daily_summaries(self, current_time: datetime) -> Dict[str, int]:
        """Generate missing daily summaries up to current time."""
        stats = {"generated": 0, "errors": 0}
        
        # Find the earliest data point
        earliest_data = await self._find_earliest_data_timestamp()
        if not earliest_data:
            logger.info("No data found, skipping daily summary catch-up")
            return stats
        
        # Start from the day of earliest data
        start_day = earliest_data.replace(hour=0, minute=0, second=0, microsecond=0)
        current_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Don't generate summary for current incomplete day
        if current_day == current_time.replace(hour=0, minute=0, second=0, microsecond=0):
            current_day -= timedelta(days=1)
        
        day = start_day
        while day <= current_day:
            day_str = day.strftime('%Y-%m-%d')
            summary_file = self._get_daily_summary_file_path(day)
            
            if not summary_file.exists():
                try:
                    logger.info(f"Generating missing daily summary for {day_str}")
                    result = await self.get_daily_summary(day_str)
                    if result.get("entry_count", 0) > 0:
                        stats["generated"] += 1
                        
                        # Store in ChromaDB
                        await self._store_summary_in_chroma(
                            "daily_summaries",
                            day_str,
                            result["summary"],
                            {
                                "timestamp": day.isoformat(),
                                "date": day_str,
                                "entry_count": result["entry_count"],
                                "type": "daily"
                            }
                        )
                        
                except Exception as e:
                    logger.error(f"Error generating daily summary for {day_str}: {e}")
                    stats["errors"] += 1
            
            day += timedelta(days=1)
        
        return stats
    
    async def _find_earliest_data_timestamp(self) -> Optional[datetime]:
        """Find the earliest timestamp in screen history data."""
        if not self.screenhistory_dir.exists():
            return None
        
        earliest = None
        try:
            json_files = list(self.screenhistory_dir.glob("*.json"))
            for file_path in json_files[:100]:  # Sample first 100 files for performance
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content or content == 'null':
                        continue
                    
                    data = json.loads(content)
                    if not isinstance(data, dict) or 'timestamp' not in data:
                        continue
                    
                    timestamp_str = self._convert_filename_timestamp_to_iso(data['timestamp'])
                    try:
                        file_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if file_time.tzinfo is None:
                            file_time = file_time.replace(tzinfo=timezone.utc)
                        
                        if earliest is None or file_time < earliest:
                            earliest = file_time
                            
                    except ValueError:
                        continue
                        
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                    
        except Exception as e:
            logger.error(f"Error finding earliest data timestamp: {e}")
        
        return earliest
    
    async def _store_summary_in_chroma(self, collection_name: str, doc_id: str, 
                                      summary: str, metadata: Dict[str, Any]):
        """Store a summary in ChromaDB."""
        try:
            await chroma_client.add_document(
                collection_name=collection_name,
                doc_id=doc_id,
                content=summary,
                metadata=metadata
            )
            logger.debug(f"Stored summary {doc_id} in {collection_name}")
        except Exception as e:
            logger.error(f"Error storing summary in ChromaDB: {e}")
            raise
    
    async def _sync_summaries_to_chroma(self):
        """Sync all file-based summaries to ChromaDB collections."""
        try:
            # Sync hourly summaries
            hourly_dir = self.summaries_dir / "hourly"
            if hourly_dir.exists():
                for summary_file in hourly_dir.glob("*.txt"):
                    hour_str = summary_file.stem
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary_content = f.read()
                        
                        # Parse hour string to get timestamp
                        year, month, day, hour = map(int, hour_str.split('-'))
                        timestamp = datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)
                        
                        await self._store_summary_in_chroma(
                            "hourly_summaries",
                            hour_str,
                            summary_content,
                            {
                                "timestamp": timestamp.isoformat(),
                                "hour": hour_str,
                                "type": "hourly"
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Error syncing hourly summary {summary_file}: {e}")
            
            # Sync daily summaries
            daily_dir = self.summaries_dir / "daily"
            if daily_dir.exists():
                for summary_file in daily_dir.glob("*.txt"):
                    day_str = summary_file.stem
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary_content = f.read()
                        
                        # Parse date string to get timestamp
                        day_date = datetime.strptime(day_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                        
                        await self._store_summary_in_chroma(
                            "daily_summaries",
                            day_str,
                            summary_content,
                            {
                                "timestamp": day_date.isoformat(),
                                "date": day_str,
                                "type": "daily"
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Error syncing daily summary {summary_file}: {e}")
                        
        except Exception as e:
            logger.error(f"Error syncing summaries to ChromaDB: {e}")
    
    async def should_generate_hourly_summary(self) -> bool:
        """Check if we should generate an hourly summary (on the hour)."""
        current_time = datetime.now(timezone.utc)
        
        # Generate summary if we're at the start of a new hour
        if current_time.minute < 5:  # Within first 5 minutes of the hour
            last_hour = current_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            last_hour_str = self._get_hour_key(last_hour)
            summary_file = self._get_hourly_summary_file_path(last_hour)
            
            return not summary_file.exists()
        
        return False
    
    async def generate_hourly_summary_if_needed(self) -> Optional[Dict[str, Any]]:
        """Generate hourly summary if we're at the start of a new hour."""
        if await self.should_generate_hourly_summary():
            current_time = datetime.now(timezone.utc)
            last_hour = current_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            last_hour_str = self._get_hour_key(last_hour)
            
            logger.info(f"Auto-generating hourly summary for {last_hour_str}")
            result = await self.get_hourly_summary(last_hour_str)
            
            # Store in ChromaDB
            if result.get("entry_count", 0) > 0:
                await self._store_summary_in_chroma(
                    "hourly_summaries",
                    last_hour_str,
                    result["summary"],
                    {
                        "timestamp": last_hour.isoformat(),
                        "hour": last_hour_str,
                        "entry_count": result["entry_count"],
                        "type": "hourly"
                    }
                )
            
            return result
        
        return None
