#!/usr/bin/env python3
"""
System Tool for Memex Prometheus Server
Remote-only version: start-flow/stop-flow disabled (no capture on Jetson).
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def now() -> datetime:
    return datetime.now().astimezone()


class SystemTool:
    """Tool for system information. Capture control is disabled on remote server."""

    def __init__(self, ocr_data_dir: Path, instance_name: str = "unknown",
                 chroma_host: str = "localhost", chroma_port: int = 8000,
                 chroma_collection: str = "screen_ocr_history", **kwargs):
        self.ocr_data_dir = ocr_data_dir
        self.instance_name = instance_name
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.chroma_collection = chroma_collection

    async def what_can_i_do(self) -> Dict[str, Any]:
        try:
            chroma_running = await self._is_chroma_running()
            return {
                "flow_capabilities": [
                    f"Search OCR data for the '{self.instance_name}' Memex instance",
                    "Search with optional date ranges and data type filters",
                    "Get statistics about captured data",
                    "Generate activity timeline graphs",
                    "Get time-range summaries with sampled OCR data",
                    "Perform semantic vector search with windowing",
                    "Find recent and relevant information with combined scoring",
                    "Get structured daily summaries by time period",
                ],
                "description": f"Memex remote instance '{self.instance_name}' on Prometheus. "
                               "Data is synced from the source laptop via rsync. "
                               "Screen capture control (start/stop) is not available on the remote server.",
                "available_tools": [
                    "search-screenshots - Search through captured OCR text data",
                    "what-can-i-do - Get information about capabilities",
                    "get-stats - Get detailed data statistics",
                    "activity-graph - Generate activity timeline visualizations",
                    "time-range-summary - Get sampled data over specific time ranges",
                    "sample-time-range - Flexible time range sampling with windowing",
                    "vector-search-windowed - Semantic search across time with windows",
                    "search-recent-relevant - Combined relevance + recency scoring",
                    "daily-summary - Structured daily breakdown by time periods",
                ],
                "current_status": {
                    "instance": self.instance_name,
                    "chroma_db_running": chroma_running,
                    "server_type": "prometheus_remote",
                    "ocr_data_directory": str(self.ocr_data_dir),
                },
                "usage_examples": [
                    "Search for 'quarterly report' to find screenshots containing that text",
                    "Use date ranges like start_date='2025-01-01' to filter results",
                    "Generate activity graphs to see work patterns over time",
                    "Get a daily summary for yesterday to review what you worked on",
                ],
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e), "flow_capabilities": []}

    async def start_flow(self) -> Dict[str, Any]:
        return {
            "success": False,
            "operation": "start_flow",
            "message": "Screen capture control is not available on the remote Prometheus server. "
                       "Start/stop capture on the source laptop directly.",
        }

    async def stop_flow(self) -> Dict[str, Any]:
        return {
            "success": False,
            "operation": "stop_flow",
            "message": "Screen capture control is not available on the remote Prometheus server. "
                       "Start/stop capture on the source laptop directly.",
        }

    async def _is_chroma_running(self) -> bool:
        try:
            import chromadb
            client = chromadb.HttpClient(host=self.chroma_host, port=self.chroma_port)
            client.heartbeat()
            return True
        except Exception:
            return False
