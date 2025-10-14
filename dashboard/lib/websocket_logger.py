"""
WebSocket logging handler for real-time log streaming.
Writes logs to both file and broadcasts via WebSocket.
"""

import logging
import json
import asyncio
from logging.handlers import RotatingFileHandler
from typing import Optional, Set
from datetime import datetime


class WebSocketLogHandler(logging.Handler):
    """
    Custom logging handler that broadcasts logs via WebSocket.
    Should be used alongside a file handler.
    """
    
    def __init__(self, subsystem_name: str, websocket_manager=None):
        super().__init__()
        self.subsystem_name = subsystem_name
        self.websocket_manager = websocket_manager
        
    def emit(self, record):
        """Send log record via WebSocket."""
        try:
            if self.websocket_manager and hasattr(self.websocket_manager, 'broadcast_log'):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'subsystem': self.subsystem_name,
                    'message': self.format(record),
                    'logger': record.name
                }
                
                # Broadcast asynchronously
                asyncio.create_task(
                    self.websocket_manager.broadcast_log(log_entry)
                )
        except Exception:
            self.handleError(record)


def setup_logger(
    name: str,
    log_file: str,
    subsystem_name: str,
    level=logging.INFO,
    websocket_manager=None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up a logger with both file and WebSocket handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file
        subsystem_name: Name of the subsystem (for WebSocket broadcasting)
        level: Logging level
        websocket_manager: WebSocket manager instance for broadcasting
        max_bytes: Max size of log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # WebSocket handler (if manager provided)
    if websocket_manager:
        ws_handler = WebSocketLogHandler(subsystem_name, websocket_manager)
        ws_handler.setLevel(level)
        ws_handler.setFormatter(file_formatter)
        logger.addHandler(ws_handler)
    
    # Console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)
    
    return logger


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts log messages.
    """
    
    def __init__(self):
        self.connections: Set = set()
    
    def add_connection(self, websocket):
        """Add a WebSocket connection."""
        self.connections.add(websocket)
    
    def remove_connection(self, websocket):
        """Remove a WebSocket connection."""
        self.connections.discard(websocket)
    
    async def broadcast_log(self, log_entry: dict):
        """Broadcast a log entry to all connected clients."""
        if not self.connections:
            return
        
        message = json.dumps({
            'type': 'log_message',
            'data': log_entry
        })
        
        # Send to all connections
        disconnected = set()
        for websocket in self.connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.connections.discard(websocket)


# Global WebSocket manager instance
_websocket_manager = None


def get_websocket_manager():
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def set_websocket_manager(manager):
    """Set the global WebSocket manager instance."""
    global _websocket_manager
    _websocket_manager = manager

