#!/usr/bin/env python3
"""
MCP Summary Server for Flow CLI
Provides screen activity summaries via Model Context Protocol
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
)

from summary_service import SummaryService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SummaryMCPServer:
    def __init__(self):
        self.server = Server("screen-summary-mcp")
        self.summary_service = SummaryService()
        
    def setup_tools(self):
        """Define available MCP tools."""
        tools = [
            Tool(
                name="get_daily_summary",
                description="Get a summary of screen activity for a specific day",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (optional, defaults to today)",
                            "format": "date"
                        }
                    }
                }
            ),
            Tool(
                name="get_time_range_summary",
                description="Get a summary of screen activity for a custom time range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_time": {
                            "type": "string",
                            "description": "Start time in ISO 8601 format (e.g., 2025-07-17T09:00:00Z)",
                            "format": "date-time"
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End time in ISO 8601 format (e.g., 2025-07-17T17:00:00Z)",
                            "format": "date-time"
                        }
                    },
                    "required": ["start_time", "end_time"]
                }
            ),
            Tool(
                name="get_last_hours_summary",
                description="Get a summary of screen activity for the last N hours",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "number",
                            "description": "Number of hours to look back (e.g., 8 for last 8 hours)",
                            "minimum": 1,
                            "maximum": 168  # 1 week max
                        }
                    },
                    "required": ["hours"]
                }
            ),
            Tool(
                name="get_hourly_summary",
                description="Get a summary of screen activity for a specific hour",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hour": {
                            "type": "string",
                            "description": "Hour in YYYY-MM-DD-HH format (e.g., 2025-07-17-14 for 2 PM)",
                            "pattern": r"^\d{4}-\d{2}-\d{2}-\d{2}$"
                        }
                    },
                    "required": ["hour"]
                }
            )
        ]
        
        return tools

    async def handle_list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """Handle list tools request."""
        tools = self.setup_tools()
        return ListToolsResult(tools=tools)

    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool call request."""
        try:
            tool_name = request.params.name
            arguments = request.params.arguments or {}
            
            result = None
            
            if tool_name == "get_daily_summary":
                date_str = arguments.get("date")
                result = await self.summary_service.get_daily_summary(date_str)
                
            elif tool_name == "get_time_range_summary":
                start_time = arguments.get("start_time")
                end_time = arguments.get("end_time")
                if not start_time or not end_time:
                    raise ValueError("start_time and end_time are required")
                result = await self.summary_service.get_time_range_summary(start_time, end_time)
                
            elif tool_name == "get_last_hours_summary":
                hours = arguments.get("hours")
                if not hours:
                    raise ValueError("hours parameter is required")
                result = await self.summary_service.get_last_hours_summary(hours)
                
            elif tool_name == "get_hourly_summary":
                hour = arguments.get("hour")
                if not hour:
                    raise ValueError("hour parameter is required")
                result = await self.summary_service.get_hourly_summary(hour)
                
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Format result as JSON
            result_text = json.dumps(result, indent=2, ensure_ascii=False)
            
            return CallToolResult(
                content=[TextContent(type="text", text=result_text)]
            )
            
        except Exception as error:
            logger.error(f"Error executing tool {request.params.name}: {error}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(error)}")],
                isError=True
            )

    async def run(self):
        """Run the MCP server."""
        # Set up request handlers
        self.server.list_tools = self.handle_list_tools
        self.server.call_tool = self.handle_call_tool
        
        # Initialize summary service
        await self.summary_service.init()
        
        # Run server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # MCP uses stdout for communication
    )
    
    # Create and run server
    server = SummaryMCPServer()
    
    try:
        logger.info("MCP Summary Server starting on stdio transport")
        logger.info("Available tools: get_daily_summary, get_time_range_summary, get_last_hours_summary, get_hourly_summary")
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as error:
        logger.error(f"Server error: {error}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
