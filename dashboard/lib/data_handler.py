#!/usr/bin/env python3
"""
Data Handler for Flow Dashboard

Handles OCR data processing, statistics, and activity timeline generation.
Provides APIs for dashboard data visualization.
"""

import asyncio
import json
import logging
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DataHandler:
    """Handles OCR data processing and statistics for the dashboard."""
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        self.ocr_data_dir = self.workspace_root / "refinery" / "data" / "ocr"
        
        # Ensure OCR data directory exists
        self.ocr_data_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic OCR data statistics using the OCR service."""
        try:
            # Import here to avoid circular imports
            from dashboard.api.ocr_data import ocr_service
            return await ocr_service.get_basic_stats()
        except Exception as e:
            logger.error(f"Error getting basic stats: {e}")
            return {
                "error": str(e),
                "total_captures": 0,
                "date_range": None,
                "unique_screens": 0
            }
    
    async def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed OCR data statistics."""
        try:
            basic_stats = await self.get_basic_stats()
            
            # Add ChromaDB stats if available
            chroma_stats = await self._get_chroma_stats()
            
            # Add recent activity
            recent_activity = await self.get_activity_timeline(hours=24, grouping="hourly")
            
            return {
                **basic_stats,
                "chroma_db": chroma_stats,
                "recent_activity_summary": {
                    "last_24h_captures": len([d for d in recent_activity.get("timeline_data", []) if d["capture_count"] > 0]),
                    "most_active_hour": self._find_most_active_period(recent_activity.get("timeline_data", [])),
                    "activity_trend": self._calculate_activity_trend(recent_activity.get("timeline_data", []))
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed stats: {e}")
            return {"error": str(e)}
    
    async def get_activity_timeline(self, hours: int = 24, grouping: str = "hourly") -> Dict[str, Any]:
        """Get activity timeline data for visualization."""
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get OCR files in time range
            ocr_files = list(self.ocr_data_dir.glob("*.json"))
            activity_data = []
            
            for file_path in ocr_files:
                try:
                    # Parse timestamp from filename
                    filename = file_path.name
                    # Format: YYYY-MM-DDTHH-MM-SS-microseconds_ScreenName.json
                    if not filename.endswith('.json'):
                        continue
                    
                    timestamp_part = filename.split('_')[0]
                    # Convert filename timestamp to datetime
                    timestamp_str = timestamp_part.replace('-', ':', 3)  # Replace first 3 hyphens with colons
                    timestamp_str = timestamp_str.replace('-', '.', 1)   # Replace next hyphen with dot for microseconds
                    
                    try:
                        file_time = datetime.fromisoformat(timestamp_str)
                    except ValueError:
                        # Try alternative parsing
                        continue
                    
                    if start_time <= file_time <= end_time:
                        # Read file data
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        activity_data.append({
                            "timestamp": data.get("timestamp", file_time.isoformat()),
                            "screen_name": data.get("screen_name", "unknown"),
                            "text_length": data.get("text_length", 0),
                            "word_count": data.get("word_count", 0),
                            "has_content": (data.get("text_length", 0) > 0)
                        })
                        
                except Exception as e:
                    logger.debug(f"Error processing file {file_path}: {e}")
                    continue
            
            # Group data by time period
            grouped_data = {}
            
            for activity in activity_data:
                try:
                    timestamp = datetime.fromisoformat(activity["timestamp"].replace('Z', '+00:00'))
                    
                    if grouping == "daily":
                        key = timestamp.strftime("%Y-%m-%d")
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
                    "screen_names": list(data["screens"])
                })
            
            # Fill in empty periods
            timeline_data = self._fill_empty_periods(timeline_data, start_time, end_time, grouping)
            
            # Sort by timestamp
            timeline_data.sort(key=lambda x: x["timestamp"])
            
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
                    "unique_screens": len(set().union(*[d["screen_names"] for d in timeline_data if d["screen_names"]]))
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting activity timeline: {e}")
            return {
                "error": str(e),
                "timeline_data": [],
                "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat(), "hours": hours},
                "grouping": grouping
            }
    
    def _fill_empty_periods(self, timeline_data: List[Dict], start_time: datetime, end_time: datetime, grouping: str) -> List[Dict]:
        """Fill in empty time periods with zero data."""
        try:
            existing_timestamps = {item["timestamp"] for item in timeline_data}
            
            current_time = start_time
            increment = timedelta(days=1) if grouping == "daily" else timedelta(hours=1)
            
            while current_time <= end_time:
                if grouping == "daily":
                    key = current_time.strftime("%Y-%m-%d")
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
    
    def _find_most_active_period(self, timeline_data: List[Dict]) -> Optional[Dict]:
        """Find the most active time period."""
        if not timeline_data:
            return None
        
        try:
            most_active = max(timeline_data, key=lambda x: x.get("capture_count", 0))
            return {
                "timestamp": most_active["timestamp"],
                "capture_count": most_active["capture_count"]
            } if most_active.get("capture_count", 0) > 0 else None
        except Exception:
            return None
    
    def _calculate_activity_trend(self, timeline_data: List[Dict]) -> str:
        """Calculate activity trend (increasing, decreasing, stable)."""
        if len(timeline_data) < 2:
            return "insufficient_data"
        
        try:
            # Compare first half vs second half
            mid_point = len(timeline_data) // 2
            first_half_avg = sum(d.get("capture_count", 0) for d in timeline_data[:mid_point]) / mid_point
            second_half_avg = sum(d.get("capture_count", 0) for d in timeline_data[mid_point:]) / (len(timeline_data) - mid_point)
            
            if second_half_avg > first_half_avg * 1.1:
                return "increasing"
            elif second_half_avg < first_half_avg * 0.9:
                return "decreasing"
            else:
                return "stable"
                
        except Exception:
            return "unknown"
    
    async def _get_chroma_stats(self) -> Dict[str, Any]:
        """Get ChromaDB collection statistics."""
        try:
            import httpx
            
            # Try to connect to ChromaDB
            async with httpx.AsyncClient() as client:
                # Check if ChromaDB is running
                response = await client.get("http://localhost:8000/api/v1/heartbeat", timeout=2.0)
                if response.status_code != 200:
                    return {"status": "unavailable", "error": "ChromaDB not responding"}
                
                # Try to get collection info (this is a simplified approach)
                # In a real implementation, you'd use the ChromaDB client
                return {
                    "status": "available",
                    "server_running": True,
                    "note": "Detailed stats require ChromaDB client integration"
                }
                
        except Exception as e:
            return {
                "status": "unavailable",
                "error": str(e)
            }
