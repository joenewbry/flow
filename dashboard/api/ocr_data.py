#!/usr/bin/env python3
"""
OCR Data API for Flow Dashboard

Provides endpoints for accessing and analyzing OCR data from the Flow system.
Includes activity timelines, statistics, and search functionality.
"""

import asyncio
import json
import logging
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ocr-data"])


class OCRDataService:
    """Service for handling OCR data operations."""
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        self.ocr_data_dir = self.workspace_root / "refinery" / "data" / "ocr"
        
        # Ensure OCR data directory exists
        self.ocr_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for performance
        self._file_cache = {}
        self._cache_timestamp = 0
        self._cache_duration = 300  # 5 minutes
    
    def _get_ocr_files(self, force_refresh: bool = False) -> List[Path]:
        """Get list of OCR files with caching."""
        current_time = datetime.now().timestamp()
        
        if force_refresh or (current_time - self._cache_timestamp) > self._cache_duration:
            files = list(self.ocr_data_dir.glob("*.json"))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Most recent first
            self._file_cache = {"files": files}
            self._cache_timestamp = current_time
            logger.debug(f"Refreshed OCR file cache: {len(files)} files")
        
        return self._file_cache.get("files", [])
    
    def _parse_filename_timestamp(self, filename: str) -> Optional[datetime]:
        """Parse timestamp from OCR filename."""
        try:
            # Format: YYYY-MM-DDTHH-MM-SS-microseconds_ScreenName.json
            if not filename.endswith('.json'):
                return None
            
            timestamp_part = filename.split('_')[0]
            # Convert filename timestamp to datetime
            # Replace hyphens with colons for time part
            parts = timestamp_part.split('T')
            if len(parts) != 2:
                return None
            
            date_part = parts[0]  # YYYY-MM-DD
            time_part = parts[1]  # HH-MM-SS-microseconds
            
            # Split time part
            time_components = time_part.split('-')
            if len(time_components) < 3:
                return None
            
            hour, minute = time_components[0], time_components[1]
            
            # Handle seconds and microseconds
            if len(time_components) >= 4:
                second = time_components[2]
                microsecond = time_components[3][:6].ljust(6, '0')  # Pad to 6 digits
            else:
                second_part = time_components[2]
                if '.' in second_part:
                    second, microsecond = second_part.split('.', 1)
                    microsecond = microsecond[:6].ljust(6, '0')
                else:
                    second = second_part
                    microsecond = '000000'
            
            # Reconstruct ISO format
            iso_string = f"{date_part}T{hour}:{minute}:{second}.{microsecond}"
            return datetime.fromisoformat(iso_string)
            
        except Exception as e:
            logger.debug(f"Error parsing timestamp from filename {filename}: {e}")
            return None
    
    def _read_ocr_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read and parse OCR file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ensure required fields exist
            if 'timestamp' not in data:
                # Try to get timestamp from filename
                file_timestamp = self._parse_filename_timestamp(file_path.name)
                if file_timestamp:
                    data['timestamp'] = file_timestamp.isoformat()
                else:
                    data['timestamp'] = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            
            # Ensure other fields have defaults
            data.setdefault('screen_name', 'unknown')
            data.setdefault('text_length', len(data.get('text', '')))
            data.setdefault('word_count', len(data.get('text', '').split()) if data.get('text') else 0)
            data.setdefault('text', '')
            
            return data
            
        except Exception as e:
            logger.warning(f"Error reading OCR file {file_path}: {e}")
            return None
    
    async def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic OCR data statistics."""
        try:
            ocr_files = self._get_ocr_files()
            total_files = len(ocr_files)
            
            if total_files == 0:
                return {
                    "total_captures": 0,
                    "date_range": None,
                    "unique_screens": 0,
                    "total_text_length": 0,
                    "avg_text_length": 0,
                    "last_updated": datetime.now().isoformat()
                }
            
            # Sample files for quick stats (use more recent files)
            sample_size = min(200, total_files)
            sample_files = ocr_files[:sample_size]  # Most recent files
            
            total_text_length = 0
            unique_screens = set()
            timestamps = []
            valid_files = 0
            
            for file_path in sample_files:
                data = self._read_ocr_file(file_path)
                if not data:
                    continue
                
                valid_files += 1
                total_text_length += data.get('text_length', 0)
                unique_screens.add(data.get('screen_name', 'unknown'))
                timestamps.append(data.get('timestamp', ''))
            
            # Calculate date range
            valid_timestamps = [ts for ts in timestamps if ts]
            date_range = None
            if valid_timestamps:
                try:
                    dates = []
                    for ts in valid_timestamps:
                        # Handle different timestamp formats
                        if 'T' in ts:
                            if ts.endswith('Z'):
                                ts = ts[:-1] + '+00:00'
                            elif '+' not in ts and 'Z' not in ts:
                                # Assume local time
                                pass
                        dates.append(datetime.fromisoformat(ts))
                    
                    if dates:
                        date_range = {
                            "earliest": min(dates).isoformat(),
                            "latest": max(dates).isoformat()
                        }
                except Exception as e:
                    logger.warning(f"Error parsing timestamps for date range: {e}")
            
            return {
                "total_captures": total_files,
                "date_range": date_range,
                "unique_screens": len(unique_screens),
                "screen_names": sorted(list(unique_screens)),
                "total_text_length": total_text_length,
                "avg_text_length": total_text_length // valid_files if valid_files > 0 else 0,
                "sample_size": valid_files,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting basic stats: {e}")
            return {
                "error": str(e),
                "total_captures": 0,
                "date_range": None,
                "unique_screens": 0,
                "last_updated": datetime.now().isoformat()
            }
    
    async def get_activity_timeline(
        self, 
        hours: int = 24, 
        grouping: str = "hourly",
        include_empty: bool = True
    ) -> Dict[str, Any]:
        """Get activity timeline data for visualization."""
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            logger.info(f"Getting activity timeline: {hours}h, {grouping}, from {start_time} to {end_time}")
            
            # Get OCR files
            ocr_files = self._get_ocr_files()
            activity_data = []
            processed_files = 0
            
            for file_path in ocr_files:
                try:
                    # Quick timestamp check from filename first
                    file_timestamp = self._parse_filename_timestamp(file_path.name)
                    if not file_timestamp:
                        # Fallback to file modification time
                        file_timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    # Skip files outside time range
                    if file_timestamp < start_time or file_timestamp > end_time:
                        continue
                    
                    # Read file data
                    data = self._read_ocr_file(file_path)
                    if not data:
                        continue
                    
                    processed_files += 1
                    activity_data.append({
                        "timestamp": data.get("timestamp", file_timestamp.isoformat()),
                        "screen_name": data.get("screen_name", "unknown"),
                        "text_length": data.get("text_length", 0),
                        "word_count": data.get("word_count", 0),
                        "has_content": (data.get("text_length", 0) > 10)  # Consider 10+ chars as content
                    })
                    
                except Exception as e:
                    logger.debug(f"Error processing file {file_path}: {e}")
                    continue
            
            logger.info(f"Processed {processed_files} files, found {len(activity_data)} activities")
            
            # Group data by time period
            grouped_data = {}
            
            for activity in activity_data:
                try:
                    timestamp_str = activity["timestamp"]
                    # Parse timestamp
                    if 'T' in timestamp_str:
                        if timestamp_str.endswith('Z'):
                            timestamp_str = timestamp_str[:-1] + '+00:00'
                        timestamp = datetime.fromisoformat(timestamp_str)
                    else:
                        timestamp = datetime.fromisoformat(timestamp_str)
                    
                    # Create grouping key
                    if grouping == "daily":
                        key = timestamp.strftime("%Y-%m-%d")
                    elif grouping == "minutely":
                        key = timestamp.strftime("%Y-%m-%d %H:%M")
                    else:  # hourly
                        key = timestamp.strftime("%Y-%m-%d %H:00")
                    
                    if key not in grouped_data:
                        grouped_data[key] = {
                            "timestamp": key,
                            "capture_count": 0,
                            "total_text_length": 0,
                            "total_word_count": 0,
                            "screens": set(),
                            "has_content_count": 0
                        }
                    
                    grouped_data[key]["capture_count"] += 1
                    grouped_data[key]["total_text_length"] += activity["text_length"]
                    grouped_data[key]["total_word_count"] += activity["word_count"]
                    grouped_data[key]["screens"].add(activity["screen_name"])
                    
                    if activity["has_content"]:
                        grouped_data[key]["has_content_count"] += 1
                        
                except Exception as e:
                    logger.debug(f"Error grouping activity data: {e}")
                    continue
            
            # Convert to timeline data
            timeline_data = []
            for key, data in grouped_data.items():
                timeline_data.append({
                    "timestamp": key,
                    "capture_count": data["capture_count"],
                    "avg_text_length": data["total_text_length"] // data["capture_count"] if data["capture_count"] > 0 else 0,
                    "avg_word_count": data["total_word_count"] // data["capture_count"] if data["capture_count"] > 0 else 0,
                    "unique_screens": len(data["screens"]),
                    "content_percentage": round((data["has_content_count"] / data["capture_count"]) * 100) if data["capture_count"] > 0 else 0,
                    "screen_names": sorted(list(data["screens"]))
                })
            
            # Fill in empty periods if requested
            if include_empty:
                timeline_data = self._fill_empty_periods(timeline_data, start_time, end_time, grouping)
            
            # Sort by timestamp
            timeline_data.sort(key=lambda x: x["timestamp"])
            
            logger.info(f"Generated timeline with {len(timeline_data)} periods")
            
            return {
                "timeline_data": timeline_data,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours": hours
                },
                "grouping": grouping,
                "summary": {
                    "total_periods": len(timeline_data),
                    "active_periods": len([d for d in timeline_data if d["capture_count"] > 0]),
                    "total_captures": sum(d["capture_count"] for d in timeline_data),
                    "unique_screens": len(set().union(*[d["screen_names"] for d in timeline_data if d["screen_names"]])),
                    "processed_files": processed_files
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting activity timeline: {e}")
            return {
                "error": str(e),
                "timeline_data": [],
                "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat(), "hours": hours},
                "grouping": grouping,
                "summary": {"total_periods": 0, "active_periods": 0, "total_captures": 0}
            }
    
    def _fill_empty_periods(self, timeline_data: List[Dict], start_time: datetime, end_time: datetime, grouping: str) -> List[Dict]:
        """Fill in empty time periods with zero data."""
        try:
            existing_timestamps = {item["timestamp"] for item in timeline_data}
            
            current_time = start_time
            if grouping == "daily":
                increment = timedelta(days=1)
            elif grouping == "minutely":
                increment = timedelta(minutes=1)
            else:  # hourly
                increment = timedelta(hours=1)
            
            while current_time <= end_time:
                if grouping == "daily":
                    key = current_time.strftime("%Y-%m-%d")
                elif grouping == "minutely":
                    key = current_time.strftime("%Y-%m-%d %H:%M")
                else:  # hourly
                    key = current_time.strftime("%Y-%m-%d %H:00")
                
                if key not in existing_timestamps:
                    timeline_data.append({
                        "timestamp": key,
                        "capture_count": 0,
                        "avg_text_length": 0,
                        "avg_word_count": 0,
                        "unique_screens": 0,
                        "content_percentage": 0,
                        "screen_names": []
                    })
                
                current_time += increment
            
            return timeline_data
            
        except Exception as e:
            logger.error(f"Error filling empty periods: {e}")
            return timeline_data
    
    async def search_ocr_data(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search OCR data (basic text search for now)."""
        try:
            # Parse date filters
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date + "T00:00:00")
            if end_date:
                end_dt = datetime.fromisoformat(end_date + "T23:59:59")
            
            ocr_files = self._get_ocr_files()
            results = []
            processed = 0
            
            for file_path in ocr_files:
                if len(results) >= limit:
                    break
                
                try:
                    # Check date filter using filename timestamp
                    file_timestamp = self._parse_filename_timestamp(file_path.name)
                    if file_timestamp:
                        if start_dt and file_timestamp < start_dt:
                            continue
                        if end_dt and file_timestamp > end_dt:
                            continue
                    
                    data = self._read_ocr_file(file_path)
                    if not data:
                        continue
                    
                    processed += 1
                    
                    # Simple text search
                    text = data.get('text', '').lower()
                    if query.lower() in text:
                        results.append({
                            "timestamp": data.get("timestamp"),
                            "screen_name": data.get("screen_name"),
                            "text_length": data.get("text_length", 0),
                            "word_count": data.get("word_count", 0),
                            "text_preview": text[:200] + "..." if len(text) > 200 else text,
                            "relevance": text.count(query.lower())  # Simple relevance score
                        })
                
                except Exception as e:
                    logger.debug(f"Error searching file {file_path}: {e}")
                    continue
            
            # Sort by relevance
            results.sort(key=lambda x: x["relevance"], reverse=True)
            
            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "processed_files": processed,
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching OCR data: {e}")
            return {
                "error": str(e),
                "query": query,
                "results": [],
                "total_found": 0
            }
    
    async def get_enhanced_metrics(self) -> Dict[str, Any]:
        """Get enhanced metrics for dashboard monitoring and debugging."""
        try:
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)
            
            ocr_files = self._get_ocr_files()
            
            # Initialize counters
            today_count = 0
            today_text_length = 0
            today_hours_active = set()
            
            week_counts_by_day = {}
            week_text_length = 0
            week_screens = set()
            week_empty_count = 0
            week_total_count = 0
            
            last_capture_time = None
            total_disk_size = 0
            
            # Process files
            for file_path in ocr_files:
                try:
                    # Get file size for disk usage
                    total_disk_size += file_path.stat().st_size
                    
                    # Parse timestamp
                    file_timestamp = self._parse_filename_timestamp(file_path.name)
                    if not file_timestamp:
                        file_timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    # Track last capture
                    if last_capture_time is None or file_timestamp > last_capture_time:
                        last_capture_time = file_timestamp
                    
                    # Read file data
                    data = self._read_ocr_file(file_path)
                    if not data:
                        continue
                    
                    text_length = data.get('text_length', 0)
                    screen_name = data.get('screen_name', 'unknown')
                    
                    # Today's metrics
                    if file_timestamp >= today_start:
                        today_count += 1
                        today_text_length += text_length
                        today_hours_active.add(file_timestamp.hour)
                    
                    # 7-day metrics
                    if file_timestamp >= week_ago:
                        week_total_count += 1
                        week_text_length += text_length
                        week_screens.add(screen_name)
                        
                        if text_length <= 10:  # Consider 10 chars or less as "empty"
                            week_empty_count += 1
                        
                        # Count by day
                        day_key = file_timestamp.strftime("%Y-%m-%d")
                        if day_key not in week_counts_by_day:
                            week_counts_by_day[day_key] = 0
                        week_counts_by_day[day_key] += 1
                
                except Exception as e:
                    logger.debug(f"Error processing file {file_path} for metrics: {e}")
                    continue
            
            # Calculate derived metrics
            avg_per_day_7d = week_total_count / 7 if week_total_count > 0 else 0
            most_active_day = max(week_counts_by_day.items(), key=lambda x: x[1]) if week_counts_by_day else (None, 0)
            active_days_count = len(week_counts_by_day)
            empty_rate = (week_empty_count / week_total_count * 100) if week_total_count > 0 else 0
            success_rate = 100 - empty_rate
            
            # Calculate trend (compare first 3 days vs last 3 days)
            if len(week_counts_by_day) >= 6:
                sorted_days = sorted(week_counts_by_day.items())
                first_half_avg = sum(count for _, count in sorted_days[:3]) / 3
                second_half_avg = sum(count for _, count in sorted_days[-3:]) / 3
                
                if second_half_avg > first_half_avg * 1.1:
                    trend = "increasing"
                    trend_symbol = "↑"
                elif second_half_avg < first_half_avg * 0.9:
                    trend = "decreasing"
                    trend_symbol = "↓"
                else:
                    trend = "stable"
                    trend_symbol = "→"
            else:
                trend = "insufficient_data"
                trend_symbol = "—"
            
            # Get ChromaDB stats
            chroma_stats = await self._get_chroma_stats()
            
            # Calculate time since last capture
            time_since_last = None
            if last_capture_time:
                delta = now - last_capture_time
                minutes = int(delta.total_seconds() / 60)
                if minutes < 60:
                    time_since_last = f"{minutes}m ago"
                elif minutes < 1440:  # Less than 24 hours
                    hours = minutes // 60
                    time_since_last = f"{hours}h ago"
                else:
                    days = minutes // 1440
                    time_since_last = f"{days}d ago"
            
            # Format disk size
            disk_size_mb = total_disk_size / (1024 * 1024)
            if disk_size_mb < 1024:
                disk_size_formatted = f"{disk_size_mb:.1f} MB"
            else:
                disk_size_gb = disk_size_mb / 1024
                disk_size_formatted = f"{disk_size_gb:.2f} GB"
            
            return {
                "today": {
                    "screenshot_count": today_count,
                    "text_captured": today_text_length,
                    "active_hours": len(today_hours_active)
                },
                "seven_day": {
                    "total_screenshots": week_total_count,
                    "daily_average": round(avg_per_day_7d, 1),
                    "most_active_day": most_active_day[0] if most_active_day[0] else "N/A",
                    "most_active_day_count": most_active_day[1] if most_active_day[0] else 0,
                    "active_days": active_days_count,
                    "trend": trend,
                    "trend_symbol": trend_symbol,
                    "avg_text_length": round(week_text_length / week_total_count) if week_total_count > 0 else 0,
                    "unique_screens": len(week_screens),
                    "empty_capture_rate": round(empty_rate, 1)
                },
                "chromadb": {
                    "total_documents": chroma_stats.get("total_documents", 0),
                    "collections": chroma_stats.get("collections", []),
                    "status": chroma_stats.get("status", "unknown"),
                    "last_sync": chroma_stats.get("last_sync", "N/A")
                },
                "system": {
                    "ocr_files_on_disk": len(ocr_files),
                    "disk_space_used": disk_size_formatted,
                    "disk_space_bytes": total_disk_size,
                    "last_capture_time": last_capture_time.isoformat() if last_capture_time else None,
                    "time_since_last_capture": time_since_last,
                    "capture_success_rate": round(success_rate, 1)
                },
                "last_updated": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting enhanced metrics: {e}")
            return {
                "error": str(e),
                "today": {"screenshot_count": 0, "text_captured": 0, "active_hours": 0},
                "seven_day": {"total_screenshots": 0, "daily_average": 0, "trend": "error"},
                "chromadb": {"total_documents": 0, "status": "error"},
                "system": {"ocr_files_on_disk": 0, "disk_space_used": "0 MB"}
            }
    
    async def _get_chroma_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics."""
        try:
            import chromadb
            from chromadb.errors import ChromaError
            import requests.exceptions
            
            # Try to connect to ChromaDB
            try:
                client = chromadb.HttpClient(host="localhost", port=8000)
                
                # Test connection
                client.heartbeat()
                
                # Try to get the screen_ocr_history collection
                try:
                    collection = client.get_collection("screen_ocr_history")
                    count = collection.count()
                    
                    # Get all collections
                    all_collections = client.list_collections()
                    
                    return {
                        "status": "connected",
                        "total_documents": count,
                        "collections": [{"name": c.name, "metadata": c.metadata if hasattr(c, 'metadata') else {}} for c in all_collections],
                        "last_sync": datetime.now().isoformat()
                    }
                except Exception as col_error:
                    logger.warning(f"Collection not found or error: {col_error}")
                    # Collection doesn't exist or is empty
                    all_collections = client.list_collections()
                    return {
                        "status": "connected",
                        "total_documents": 0,
                        "collections": [{"name": c.name, "metadata": c.metadata if hasattr(c, 'metadata') else {}} for c in all_collections],
                        "last_sync": datetime.now().isoformat()
                    }
                    
            except requests.exceptions.ConnectionError as conn_error:
                logger.warning(f"ChromaDB server connection failed: {conn_error}")
                return {
                    "status": "unavailable",
                    "total_documents": 0,
                    "collections": [],
                    "error": "ChromaDB server not running"
                }
            except Exception as e:
                logger.warning(f"Could not get ChromaDB stats: {e}")
                return {
                    "status": "unavailable",
                    "total_documents": 0,
                    "collections": [],
                    "error": str(e)
                }
                
        except Exception as e:
            logger.error(f"Error getting ChromaDB stats: {e}")
            return {
                "status": "error",
                "total_documents": 0,
                "collections": [],
                "error": str(e)
            }


# Global service instance
ocr_service = OCRDataService()


@router.get("/stats")
async def get_stats():
    """Get OCR data statistics."""
    try:
        stats = await ocr_service.get_basic_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error in get_stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-data")
async def get_activity_data(
    hours: int = Query(72, ge=1, le=168, description="Number of hours to include"),
    grouping: str = Query("minutely", regex="^(minutely|hourly|daily)$", description="Time grouping"),
    include_empty: bool = Query(True, description="Include empty time periods")
):
    """Get activity timeline data for graphs."""
    try:
        data = await ocr_service.get_activity_timeline(
            hours=hours, 
            grouping=grouping, 
            include_empty=include_empty
        )
        return JSONResponse(content=data)
    except Exception as e:
        logger.error(f"Error in get_activity_data endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_ocr(
    q: str = Query(..., description="Search query"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results")
):
    """Search OCR data."""
    try:
        results = await ocr_service.search_ocr_data(
            query=q,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Error in search_ocr endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/count")
async def get_file_count():
    """Get count of OCR files."""
    try:
        files = ocr_service._get_ocr_files()
        return JSONResponse(content={
            "total_files": len(files),
            "directory": str(ocr_service.ocr_data_dir),
            "last_updated": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_file_count endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enhanced-metrics")
async def get_enhanced_metrics():
    """Get enhanced metrics for dashboard monitoring and debugging."""
    try:
        metrics = await ocr_service.get_enhanced_metrics()
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Error in get_enhanced_metrics endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
