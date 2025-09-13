#!/usr/bin/env python3
"""
HTTP Bridge for MCP Summary Server
Provides RESTful API access to MCP tools
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from summary_service import SummaryService

logger = logging.getLogger(__name__)

# Pydantic models for request validation
class DailySummaryRequest(BaseModel):
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")

class TimeRangeSummaryRequest(BaseModel):
    start_time: str = Field(..., description="Start time in ISO 8601 format")
    end_time: str = Field(..., description="End time in ISO 8601 format")

class LastHoursSummaryRequest(BaseModel):
    hours: int = Field(..., ge=1, le=168, description="Number of hours to look back")

class HourlySummaryRequest(BaseModel):
    hour: str = Field(..., regex=r"^\d{4}-\d{2}-\d{2}-\d{2}$", description="Hour in YYYY-MM-DD-HH format")


class MCPHttpBridge:
    def __init__(self, port: int = 3000):
        self.port = port
        self.app = FastAPI(
            title="Flow MCP HTTP Bridge",
            description="RESTful API bridge for Flow's MCP Summary Server",
            version="1.0.0"
        )
        self.summary_service = SummaryService()
        self.mcp_process: Optional[subprocess.Popen] = None
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up FastAPI routes."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "mcp_server_running": self.mcp_process is not None and self.mcp_process.poll() is None,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/tools")
        async def list_tools():
            """List available tools."""
            tools = [
                {
                    "name": "get_daily_summary",
                    "description": "Get a summary of screen activity for a specific day",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format (optional, defaults to today)",
                                "format": "date"
                            }
                        }
                    }
                },
                {
                    "name": "get_time_range_summary",
                    "description": "Get a summary of screen activity for a custom time range",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "start_time": {
                                "type": "string",
                                "description": "Start time in ISO 8601 format",
                                "format": "date-time"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "End time in ISO 8601 format",
                                "format": "date-time"
                            }
                        },
                        "required": ["start_time", "end_time"]
                    }
                },
                {
                    "name": "get_last_hours_summary",
                    "description": "Get a summary of screen activity for the last N hours",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "hours": {
                                "type": "number",
                                "description": "Number of hours to look back",
                                "minimum": 1,
                                "maximum": 168
                            }
                        },
                        "required": ["hours"]
                    }
                },
                {
                    "name": "get_hourly_summary",
                    "description": "Get a summary of screen activity for a specific hour",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "hour": {
                                "type": "string",
                                "description": "Hour in YYYY-MM-DD-HH format",
                                "pattern": r"^\d{4}-\d{2}-\d{2}-\d{2}$"
                            }
                        },
                        "required": ["hour"]
                    }
                }
            ]
            
            return {"tools": tools}
        
        @self.app.post("/tools/get_daily_summary")
        async def get_daily_summary(request: DailySummaryRequest = DailySummaryRequest()):
            """Get daily summary."""
            try:
                result = await self.summary_service.get_daily_summary(request.date)
                return result
            except Exception as e:
                logger.error(f"Error getting daily summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/get_time_range_summary")
        async def get_time_range_summary(request: TimeRangeSummaryRequest):
            """Get time range summary."""
            try:
                result = await self.summary_service.get_time_range_summary(
                    request.start_time, request.end_time
                )
                return result
            except Exception as e:
                logger.error(f"Error getting time range summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/get_last_hours_summary")
        async def get_last_hours_summary(request: LastHoursSummaryRequest):
            """Get last hours summary."""
            try:
                result = await self.summary_service.get_last_hours_summary(request.hours)
                return result
            except Exception as e:
                logger.error(f"Error getting last hours summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/get_hourly_summary")
        async def get_hourly_summary(request: HourlySummaryRequest):
            """Get hourly summary."""
            try:
                result = await self.summary_service.get_hourly_summary(request.hour)
                return result
            except Exception as e:
                logger.error(f"Error getting hourly summary: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/{tool_name}")
        async def generic_tool_execution(tool_name: str, request_data: Dict[str, Any]):
            """Generic tool execution endpoint."""
            try:
                if tool_name == "get_daily_summary":
                    result = await self.summary_service.get_daily_summary(
                        request_data.get("date")
                    )
                elif tool_name == "get_time_range_summary":
                    result = await self.summary_service.get_time_range_summary(
                        request_data.get("start_time"),
                        request_data.get("end_time")
                    )
                elif tool_name == "get_last_hours_summary":
                    result = await self.summary_service.get_last_hours_summary(
                        request_data.get("hours")
                    )
                elif tool_name == "get_hourly_summary":
                    result = await self.summary_service.get_hourly_summary(
                        request_data.get("hour")
                    )
                else:
                    raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_mcp_server(self):
        """Start the MCP server as a subprocess."""
        try:
            logger.info("Starting MCP server...")
            
            # Find the MCP server script
            mcp_script = Path(__file__).parent / "mcp_summary_server.py"
            
            if not mcp_script.exists():
                raise FileNotFoundError(f"MCP server script not found: {mcp_script}")
            
            # Start the MCP server process
            self.mcp_process = subprocess.Popen(
                [sys.executable, str(mcp_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"MCP server started with PID: {self.mcp_process.pid}")
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    def stop_mcp_server(self):
        """Stop the MCP server."""
        if self.mcp_process:
            logger.info("Stopping MCP server...")
            self.mcp_process.terminate()
            try:
                self.mcp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("MCP server didn't stop gracefully, killing...")
                self.mcp_process.kill()
            
            self.mcp_process = None
    
    async def startup(self):
        """Application startup."""
        logger.info("Starting MCP HTTP Bridge...")
        
        # Initialize summary service
        await self.summary_service.init()
        
        # Note: We're using the summary service directly instead of the MCP server
        # for simplicity and better error handling
        logger.info("Summary service initialized")
    
    async def shutdown(self):
        """Application shutdown."""
        logger.info("Shutting down MCP HTTP Bridge...")
        self.stop_mcp_server()
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Run the HTTP bridge server."""
        self.setup_signal_handlers()
        
        # Set up startup and shutdown events
        self.app.add_event_handler("startup", self.startup)
        self.app.add_event_handler("shutdown", self.shutdown)
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=self.app,
            host="localhost",
            port=self.port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        
        logger.info(f"MCP HTTP Bridge starting on http://localhost:{self.port}")
        logger.info(f"Health check: http://localhost:{self.port}/health")
        logger.info(f"Available tools: http://localhost:{self.port}/tools")
        
        try:
            await server.serve()
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


async def main():
    """Main entry point."""
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="MCP HTTP Bridge for Flow CLI")
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.getenv("MCP_HTTP_PORT", 3000)),
        help="Port to run the HTTP server on (default: 3000)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging level"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run bridge
    bridge = MCPHttpBridge(port=args.port)
    
    try:
        await bridge.run()
    except Exception as e:
        logger.error(f"Failed to start MCP HTTP Bridge: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
