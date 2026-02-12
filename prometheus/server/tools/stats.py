#!/usr/bin/env python3
"""
Stats Tool for Memex Prometheus Server
Adapted for multi-instance deployment with configurable paths.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def now() -> datetime:
    return datetime.now().astimezone()


class StatsTool:
    """Tool for getting Memex system statistics."""

    def __init__(self, ocr_data_dir: Path, chroma_host: str = "localhost",
                 chroma_port: int = 8000, chroma_collection: str = "screen_ocr_history"):
        self.ocr_data_dir = ocr_data_dir
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.chroma_collection_name = chroma_collection
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

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        try:
            ocr_files = list(self.ocr_data_dir.glob("*.json"))
            total_files = len(ocr_files)

            if total_files == 0:
                return {
                    "ocr_files": {"count": 0, "directory": str(self.ocr_data_dir)},
                    "date_range": None, "unique_screens": 0,
                    "chroma_collection": {"name": self.chroma_collection_name, "status": "no_data"},
                    "last_updated": now().isoformat(),
                }

            ocr_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            sample_size = min(500, total_files)
            sample_files = ocr_files[:sample_size]

            total_text_length = 0
            unique_screens = set()
            timestamps = []
            valid_files = 0
            content_files = 0

            for file_path in sample_files:
                data = self._read_ocr_file(file_path)
                if not data:
                    continue
                valid_files += 1
                text_length = data.get('text_length', 0)
                total_text_length += text_length
                if text_length > 10:
                    content_files += 1
                unique_screens.add(data.get('screen_name', 'unknown'))
                timestamps.append(data.get('timestamp', ''))

            valid_timestamps = [ts for ts in timestamps if ts]
            date_range = None
            if valid_timestamps:
                try:
                    dates = []
                    for ts in valid_timestamps:
                        if ts.endswith('Z'):
                            ts = ts[:-1] + '+00:00'
                        dates.append(datetime.fromisoformat(ts))
                    if dates:
                        earliest = min(dates)
                        latest = max(dates)
                        date_range = {
                            "earliest": earliest.isoformat(),
                            "latest": latest.isoformat(),
                            "span_days": (latest - earliest).days,
                            "span_hours": round((latest - earliest).total_seconds() / 3600, 1),
                        }
                except Exception as e:
                    logger.warning(f"Error parsing timestamps: {e}")

            chroma_status = await self._get_chroma_status()
            activity_rate = round(total_files / date_range["span_hours"], 2) if date_range and date_range["span_hours"] > 0 else 0
            content_percentage = round((content_files / valid_files) * 100) if valid_files > 0 else 0

            return {
                "ocr_files": {
                    "count": total_files, "directory": str(self.ocr_data_dir),
                    "valid_files": valid_files, "content_files": content_files,
                    "content_percentage": content_percentage,
                },
                "date_range": date_range,
                "unique_screens": len(unique_screens),
                "screen_names": sorted(list(unique_screens)),
                "text_analysis": {
                    "total_text_length": total_text_length,
                    "avg_text_length": total_text_length // valid_files if valid_files > 0 else 0,
                },
                "activity_metrics": {
                    "captures_per_hour": activity_rate,
                    "sample_size": valid_files,
                },
                "chroma_collection": chroma_status,
                "last_updated": now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e), "ocr_files": {"count": 0}, "last_updated": now().isoformat()}

    async def _get_chroma_status(self) -> Dict[str, Any]:
        try:
            import chromadb
            client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
            client.heartbeat()
            return {
                "name": self.chroma_collection_name,
                "status": "server_running",
                "server_url": f"http://{self.chroma_host}:{self.chroma_port}",
            }
        except Exception as e:
            return {"name": self.chroma_collection_name, "status": "unavailable", "error": str(e)}
