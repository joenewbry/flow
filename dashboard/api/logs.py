#!/usr/bin/env python3
"""
Logs API for Flow Dashboard
Provides endpoints for reading log files.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["logs"])


class LogsService:
    """Service for reading and managing log files."""
    
    def __init__(self):
        self.log_dir = Path(__file__).parent.parent.parent / "logs"
        self.log_files = {
            "screen-capture": "screen-capture.log",
            "dashboard": "dashboard.log",
            "mcp-server": "mcp-server.log",
            "chromadb": "chromadb.log"
        }
    
    def read_log_file(
        self,
        subsystem: str,
        max_lines: int = 100,
        level_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Read log file for a subsystem."""
        try:
            if subsystem not in self.log_files:
                return []
            
            log_file = self.log_dir / self.log_files[subsystem]
            
            if not log_file.exists():
                logger.warning(f"Log file not found: {log_file}")
                return []
            
            # Read the file
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Parse log entries
            log_entries = []
            for line in lines[-max_lines:]:  # Get last N lines
                line = line.strip()
                if not line:
                    continue
                
                # Try to parse log format: timestamp - name - level - message
                parts = line.split(' - ', 3)
                if len(parts) >= 4:
                    timestamp, name, level, message = parts
                    
                    # Apply level filter
                    if level_filter and level_filter != "all" and level != level_filter:
                        continue
                    
                    log_entries.append({
                        "timestamp": timestamp,
                        "logger": name,
                        "level": level,
                        "message": message,
                        "subsystem": subsystem
                    })
                else:
                    # Fallback for unparsed lines
                    log_entries.append({
                        "timestamp": "",
                        "logger": subsystem,
                        "level": "INFO",
                        "message": line,
                        "subsystem": subsystem
                    })
            
            return log_entries
            
        except Exception as e:
            logger.error(f"Error reading log file for {subsystem}: {e}")
            return []
    
    def get_all_logs(
        self,
        max_lines_per_subsystem: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get logs from all subsystems."""
        all_logs = {}
        
        for subsystem in self.log_files.keys():
            all_logs[subsystem] = self.read_log_file(subsystem, max_lines_per_subsystem)
        
        return all_logs
    
    def get_log_status(self) -> Dict[str, Any]:
        """Get status of all log files."""
        status = {}
        
        for subsystem, filename in self.log_files.items():
            log_file = self.log_dir / filename
            status[subsystem] = {
                "available": log_file.exists(),
                "path": str(log_file),
                "size": log_file.stat().st_size if log_file.exists() else 0
            }
        
        return status


# Create service instance
logs_service = LogsService()


@router.get("/{subsystem}")
async def get_logs(
    subsystem: str,
    max_lines: int = 100,
    level: Optional[str] = None
):
    """Get logs for a specific subsystem."""
    try:
        logs = logs_service.read_log_file(subsystem, max_lines, level)
        return JSONResponse(content={
            "subsystem": subsystem,
            "logs": logs,
            "total": len(logs)
        })
    except Exception as e:
        logger.error(f"Error getting logs for {subsystem}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_all_logs(max_lines: int = 50):
    """Get logs from all subsystems."""
    try:
        logs = logs_service.get_all_logs(max_lines)
        return JSONResponse(content={
            "logs": logs,
            "subsystems": list(logs.keys())
        })
    except Exception as e:
        logger.error(f"Error getting all logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/all")
async def get_log_status():
    """Get status of all log files."""
    try:
        status = logs_service.get_log_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting log status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

