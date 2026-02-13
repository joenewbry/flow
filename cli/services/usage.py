"""Usage tracking for Memex CLI.

Logs every MCP tool call and data storage event to ~/.memex/usage.jsonl.
Append-only JSONL format — no database required.
Foundation for future pricing; no billing logic here, just metering.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from cli.config.settings import get_settings


def _get_usage_path() -> Path:
    """Get path to usage log file."""
    settings = get_settings()
    return settings.config_dir / "usage.jsonl"


def _ensure_config_dir():
    """Ensure config directory exists."""
    settings = get_settings()
    settings.config_dir.mkdir(parents=True, exist_ok=True)


class UsageTracker:
    """Tracks MCP tool calls and data storage events."""

    def __init__(self):
        self._path = _get_usage_path()

    def log_tool_call(
        self,
        tool_name: str,
        instance_name: str = "personal",
        query_length: int = 0,
        result_count: int = 0,
        duration_ms: int = 0,
    ):
        """Log an MCP tool call event."""
        event = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "event": "tool_call",
            "instance": instance_name,
            "tool": tool_name,
            "query_len": query_length,
            "results": result_count,
            "duration_ms": duration_ms,
        }
        self._append(event)

    def log_data_sync(
        self,
        instance_name: str = "personal",
        files: int = 0,
        bytes_stored: int = 0,
    ):
        """Log a data sync/storage event."""
        event = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "event": "data_sync",
            "instance": instance_name,
            "files": files,
            "bytes": bytes_stored,
        }
        self._append(event)

    def _append(self, event: dict):
        """Append a single JSON line to the usage log."""
        _ensure_config_dir()
        try:
            with open(self._path, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass  # Never fail the caller over metering

    def _read_events(
        self,
        since: Optional[datetime] = None,
    ) -> list[dict]:
        """Read events from the log, optionally filtered by time."""
        if not self._path.exists():
            return []

        events = []
        since_iso = since.isoformat(timespec="seconds") if since else None

        try:
            with open(self._path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        if since_iso and event.get("ts", "") < since_iso:
                            continue
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        return events

    def get_usage_summary(self, period: str = "day") -> dict:
        """Return usage counts and totals for a time period.

        Args:
            period: "day", "week", or "month"

        Returns:
            Dict with tool_calls, data_syncs, total_results, total_bytes, total_duration_ms.
        """
        now = datetime.now()
        if period == "day":
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            since = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            since = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)

        events = self._read_events(since=since)

        summary = {
            "period": period,
            "tool_calls": 0,
            "data_syncs": 0,
            "total_results": 0,
            "total_bytes": 0,
            "total_duration_ms": 0,
        }

        for event in events:
            if event.get("event") == "tool_call":
                summary["tool_calls"] += 1
                summary["total_results"] += event.get("results", 0)
                summary["total_duration_ms"] += event.get("duration_ms", 0)
            elif event.get("event") == "data_sync":
                summary["data_syncs"] += 1
                summary["total_bytes"] += event.get("bytes", 0)

        return summary

    def get_storage_by_instance(self) -> dict[str, int]:
        """Return total bytes stored per instance (all time)."""
        events = self._read_events()
        storage: dict[str, int] = {}
        for event in events:
            if event.get("event") == "data_sync":
                instance = event.get("instance", "unknown")
                storage[instance] = storage.get(instance, 0) + event.get("bytes", 0)
        return storage
