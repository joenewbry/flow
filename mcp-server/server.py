#!/usr/bin/env python3
"""
Flow MCP Server - Python Implementation

A standalone MCP server for the Flow screen capture system.
Provides tools for searching OCR data, generating activity graphs, and system management.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
    ServerCapabilities,
)

# Flow imports
from tools.search import SearchTool
from tools.stats import StatsTool
from tools.activity import ActivityTool
from tools.system import SystemTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


class FlowMCPServer:
    """Main Flow MCP Server class."""
    
    def __init__(self):
        self.server = Server("flow")
        self.workspace_root = Path(__file__).parent.parent
        
        # Initialize tools
        self.search_tool = SearchTool(self.workspace_root)
        self.stats_tool = StatsTool(self.workspace_root)
        self.activity_tool = ActivityTool(self.workspace_root)
        self.system_tool = SystemTool(self.workspace_root)
        
        # Register tools
        self.tools = {
            "search-screenshots": self.search_tool,
            "what-can-i-do": self.system_tool,
            "get-stats": self.stats_tool,
            "activity-graph": self.activity_tool,
            "time-range-summary": self.activity_tool,
            "start-flow": self.system_tool,
            "stop-flow": self.system_tool,
        }
        
        logger.info(f"Initialized Flow MCP Server with {len(self.tools)} tools")
    
    async def list_tools(self) -> List[Tool]:
        """List all available tools."""
        tools = []
        
        # Search Screenshots
        tools.append(Tool(
            name="search-screenshots",
            description="Search OCR data from screenshots with optional date range parameters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for the OCR text content",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for search (YYYY-MM-DD format, optional)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for search (YYYY-MM-DD format, optional)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        ))
        
        # What Can I Do
        tools.append(Tool(
            name="what-can-i-do",
            description="Get information about what you can do with Flow",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ))
        
        # Get Stats
        tools.append(Tool(
            name="get-stats",
            description="Get statistics about OCR data files and ChromaDB collection",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ))
        
        # Activity Graph
        tools.append(Tool(
            name="activity-graph",
            description="Generate activity timeline graph data showing when Flow was active capturing screens",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer", 
                        "description": "Number of days to include in the graph (default: 7)",
                        "default": 7,
                    },
                    "grouping": {
                        "type": "string",
                        "description": "How to group the data: 'hourly', 'daily' (default: 'hourly')",
                        "enum": ["hourly", "daily"],
                        "default": "hourly",
                    },
                    "include_empty": {
                        "type": "boolean",
                        "description": "Include time periods with no activity (default: true)",
                        "default": True,
                    },
                },
                "additionalProperties": False,
            },
        ))
        
        # Time Range Summary
        tools.append(Tool(
            name="time-range-summary",
            description="Get a sampled summary of OCR data over a specified time range by returning up to 24 evenly distributed results",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS) or date format (YYYY-MM-DD)",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in ISO format (YYYY-MM-DDTHH:MM:SS) or date format (YYYY-MM-DD)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 24, max: 100)",
                        "default": 24,
                    },
                    "include_text": {
                        "type": "boolean",
                        "description": "Include OCR text content in results (default: true)",
                        "default": True,
                    },
                },
                "required": ["start_time", "end_time"],
                "additionalProperties": False,
            },
        ))
        
        # Start Flow
        tools.append(Tool(
            name="start-flow",
            description="Start Flow screenshot recording (starts ChromaDB server and Python capture process)",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ))
        
        # Stop Flow
        tools.append(Tool(
            name="stop-flow",
            description="Stop Flow screenshot recording (stops Python capture process and ChromaDB server)",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ))
        
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name with given arguments."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        
        tool = self.tools[name]
        
        try:
            if name == "search-screenshots":
                return await tool.search_screenshots(
                    query=arguments["query"],
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date"),
                    limit=arguments.get("limit", 10)
                )
            elif name == "what-can-i-do":
                return await tool.what_can_i_do()
            elif name == "get-stats":
                return await tool.get_stats()
            elif name == "activity-graph":
                return await tool.activity_graph(
                    days=arguments.get("days", 7),
                    grouping=arguments.get("grouping", "hourly"),
                    include_empty=arguments.get("include_empty", True)
                )
            elif name == "time-range-summary":
                return await tool.time_range_summary(
                    start_time=arguments["start_time"],
                    end_time=arguments["end_time"],
                    max_results=arguments.get("max_results", 24),
                    include_text=arguments.get("include_text", True)
                )
            elif name == "start-flow":
                return await tool.start_flow()
            elif name == "stop-flow":
                return await tool.stop_flow()
            else:
                raise ValueError(f"Tool {name} not implemented")
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return {
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Flow MCP Server...")
    
    # Create server instance
    flow_server = FlowMCPServer()
    
    # Create MCP server
    server = Server("flow")
    
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """Handle list tools request."""
        return await flow_server.list_tools()
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
        """Handle call tool request."""
        try:
            result = await flow_server.call_tool(name, arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error in handle_call_tool: {e}")
            error_result = {"error": str(e), "tool": name}
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Flow MCP Server running on stdio transport")
        
        # Create initialization options
        init_options = InitializationOptions(
            server_name="flow",
            server_version="1.0.0",
            capabilities=ServerCapabilities(),
        )
        
        await server.run(
            read_stream,
            write_stream,
            init_options,
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
