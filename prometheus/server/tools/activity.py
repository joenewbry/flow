#!/usr/bin/env python3
"""
Activity Tool for Memex Prometheus Server
Adapted for multi-instance deployment with configurable paths.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def now() -> datetime:
    return datetime.now().astimezone()


class ActivityTool:
    """Tool for generating activity timelines and summaries."""

    def __init__(self, ocr_data_dir: Path, **kwargs):
        self.ocr_data_dir = ocr_data_dir
        self.ocr_data_dir.mkdir(parents=True, exist_ok=True)

    def _parse_filename_timestamp(self, filename: str) -> Optional[datetime]:
        try:
            if not filename.endswith('.json'):
                return None
            timestamp_part = filename.split('_')[0]
            parts = timestamp_part.split('T')
            if len(parts) != 2:
                return None
            date_part = parts[0]
            time_part = parts[1]
            time_components = time_part.split('-')
            if len(time_components) < 3:
                return None
            hour, minute = time_components[0], time_components[1]
            if len(time_components) >= 4:
                second = time_components[2]
                microsecond = time_components[3][:6].ljust(6, '0')
            else:
                second_part = time_components[2]
                if '.' in second_part:
                    second, microsecond = second_part.split('.', 1)
                    microsecond = microsecond[:6].ljust(6, '0')
                else:
                    second = second_part
                    microsecond = '000000'
            iso_string = f"{date_part}T{hour}:{minute}:{second}.{microsecond}"
            return datetime.fromisoformat(iso_string)
        except Exception:
            return None

    def _read_ocr_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'timestamp' not in data:
                file_timestamp = self._parse_filename_timestamp(file_path.name)
                if file_timestamp:
                    data['timestamp'] = file_timestamp.isoformat()
                else:
                    data['timestamp'] = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            data.setdefault('screen_name', 'unknown')
            data.setdefault('text_length', len(data.get('text', '')))
            data.setdefault('word_count', len(data.get('text', '').split()) if data.get('text') else 0)
            data.setdefault('text', '')
            return data
        except Exception as e:
            logger.warning(f"Error reading OCR file {file_path}: {e}")
            return None

    async def activity_graph(self, days: int = 7, grouping: str = "hourly",
                             include_empty: bool = True) -> Dict[str, Any]:
        try:
            end_time = now()
            start_time = end_time - timedelta(days=days)

            ocr_files = list(self.ocr_data_dir.glob("*.json"))
            activity_data = []

            for file_path in ocr_files:
                try:
                    file_timestamp = self._parse_filename_timestamp(file_path.name)
                    if not file_timestamp:
                        file_timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_timestamp < start_time or file_timestamp > end_time:
                        continue
                    data = self._read_ocr_file(file_path)
                    if not data:
                        continue
                    activity_data.append({
                        "timestamp": data.get("timestamp", file_timestamp.isoformat()),
                        "screen_name": data.get("screen_name", "unknown"),
                        "text_length": data.get("text_length", 0),
                        "word_count": data.get("word_count", 0),
                        "has_content": data.get("text_length", 0) > 10,
                    })
                except Exception:
                    continue

            grouped_data = {}
            for activity in activity_data:
                try:
                    ts = activity["timestamp"]
                    if ts.endswith('Z'):
                        ts = ts[:-1] + '+00:00'
                    timestamp = datetime.fromisoformat(ts)
                    key = timestamp.strftime("%Y-%m-%d") if grouping == "daily" else timestamp.strftime("%Y-%m-%d %H:00")
                    if key not in grouped_data:
                        grouped_data[key] = {
                            "timestamp": key, "capture_count": 0,
                            "total_text_length": 0, "total_word_count": 0,
                            "screens": set(), "has_content_count": 0,
                        }
                    grouped_data[key]["capture_count"] += 1
                    grouped_data[key]["total_text_length"] += activity["text_length"]
                    grouped_data[key]["total_word_count"] += activity["word_count"]
                    grouped_data[key]["screens"].add(activity["screen_name"])
                    if activity["has_content"]:
                        grouped_data[key]["has_content_count"] += 1
                except Exception:
                    continue

            timeline_data = []
            for key, data in grouped_data.items():
                cc = data["capture_count"]
                timeline_data.append({
                    "timestamp": key,
                    "capture_count": cc,
                    "avg_text_length": data["total_text_length"] // cc if cc else 0,
                    "avg_word_count": data["total_word_count"] // cc if cc else 0,
                    "unique_screens": len(data["screens"]),
                    "content_percentage": round((data["has_content_count"] / cc) * 100) if cc else 0,
                    "screen_names": sorted(list(data["screens"])),
                })

            if include_empty:
                existing = {item["timestamp"] for item in timeline_data}
                current = start_time
                increment = timedelta(days=1) if grouping == "daily" else timedelta(hours=1)
                while current <= end_time:
                    key = current.strftime("%Y-%m-%d") if grouping == "daily" else current.strftime("%Y-%m-%d %H:00")
                    if key not in existing:
                        timeline_data.append({
                            "timestamp": key, "capture_count": 0, "avg_text_length": 0,
                            "avg_word_count": 0, "unique_screens": 0,
                            "content_percentage": 0, "screen_names": [],
                        })
                    current += increment

            timeline_data.sort(key=lambda x: x["timestamp"])

            return {
                "graph_type": "activity_timeline",
                "time_range": {"start_date": start_time.isoformat(), "end_date": end_time.isoformat(), "days": days},
                "grouping": grouping,
                "data_summary": {
                    "total_captures": len(activity_data),
                    "total_periods": len(timeline_data),
                    "active_periods": len([d for d in timeline_data if d["capture_count"] > 0]),
                },
                "timeline_data": timeline_data,
            }
        except Exception as e:
            logger.error(f"Error generating activity graph: {e}")
            return {"error": str(e), "graph_type": "activity_timeline", "timeline_data": []}

    async def time_range_summary(self, start_time: str, end_time: str,
                                 max_results: int = 24, include_text: bool = True) -> Dict[str, Any]:
        try:
            start_dt = datetime.fromisoformat(start_time + "T00:00:00" if 'T' not in start_time else start_time)
            end_dt = datetime.fromisoformat(end_time + "T23:59:59" if 'T' not in end_time else end_time)

            if start_dt >= end_dt:
                raise ValueError("Start time must be before end time")

            ocr_files = list(self.ocr_data_dir.glob("*.json"))
            filtered_data = []

            for file_path in ocr_files:
                try:
                    file_timestamp = self._parse_filename_timestamp(file_path.name)
                    if not file_timestamp:
                        file_timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if start_dt <= file_timestamp <= end_dt:
                        data = self._read_ocr_file(file_path)
                        if data:
                            filtered_data.append({
                                "filename": file_path.name,
                                "timestamp": data.get("timestamp", file_timestamp.isoformat()),
                                "screen_name": data.get("screen_name", "unknown"),
                                "text_length": data.get("text_length", 0),
                                "word_count": data.get("word_count", 0),
                                "text": data.get("text", "") if include_text else None,
                                "has_content": data.get("text_length", 0) > 10,
                            })
                except Exception:
                    continue

            filtered_data.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]))

            sampled_data = filtered_data
            sampling_info = {"sampled": False, "total_items": len(filtered_data)}

            if len(filtered_data) > max_results:
                sampling_info["sampled"] = True
                sampling_info["sampling_method"] = "evenly_distributed"
                step = len(filtered_data) / max_results
                sampled_data = [filtered_data[int(i * step)] for i in range(max_results) if int(i * step) < len(filtered_data)]

            return {
                "summary_type": "time_range_sampling",
                "time_range": {
                    "start_time": start_dt.isoformat(), "end_time": end_dt.isoformat(),
                    "duration_hours": round((end_dt - start_dt).total_seconds() / 3600, 2),
                },
                "sampling_info": sampling_info,
                "results_summary": {
                    "total_items_in_range": len(filtered_data),
                    "returned_items": len(sampled_data),
                    "unique_screens": list(set(item["screen_name"] for item in sampled_data)),
                },
                "data": sampled_data,
            }
        except Exception as e:
            logger.error(f"Error generating time range summary: {e}")
            return {"error": str(e), "summary_type": "time_range_sampling", "data": []}
