#!/usr/bin/env python3
"""
Flow MCP Server
Provides tools for interacting with Flow CLI via Model Context Protocol
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
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

# Add the src directory to the path to import chroma_client
sys.path.append('/Users/joe/dev/flow/src')
from lib.chroma_client import chroma_client

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class FlowMCPServer:
    def __init__(self):
        self.server = Server("flow")
        self.chroma_initialized = False
        
    async def ensure_chroma_initialized(self):
        """Ensure ChromaDB is initialized."""
        if not self.chroma_initialized:
            try:
                await chroma_client.init()
                self.chroma_initialized = True
                logger.info("ChromaDB initialized for MCP server")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                raise
        
    def setup_tools(self):
        """Define available MCP tools."""
        tools = [
            Tool(
                name="what-can-i-do",
                description="Get information about what you can do with Flow",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            Tool(
                name="search-screenshots",
                description="Search OCR data from screenshots with optional date range parameters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for the OCR text content"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date for search (YYYY-MM-DD format, optional)"
                        },
                        "end_date": {
                            "type": "string", 
                            "description": "End date for search (YYYY-MM-DD format, optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="fetch-flow-stats",
                description="Get statistics about screenshots saved in the screenshots collection",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
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
            
            if tool_name == "what-can-i-do":
                result = {
                    "flow_capabilities": [
                        "Search for anything that you worked on while using flow. This includes urls, document titles, jira tickets, etc.",
                        "Get statistics about your screenshot collection",
                        "Search OCR data from screenshots with optional date ranges"
                    ],
                    "description": "Flow is a screen activity tracking and analysis tool that helps you search and analyze your work patterns.",
                    "available_tools": [
                        "what-can-i-do",
                        "search-screenshots", 
                        "fetch-flow-stats"
                    ]
                }
            
            elif tool_name == "search-screenshots":
                await self.ensure_chroma_initialized()
                
                query = request.params.arguments.get("query")
                start_date = request.params.arguments.get("start_date")
                end_date = request.params.arguments.get("end_date")
                limit = request.params.arguments.get("limit", 10)
                
                # Build search parameters
                search_params = {
                    "query": query,
                    "limit": limit
                }
                
                # Add date filtering if provided
                where_clause = {}
                if start_date:
                    where_clause["timestamp"] = {"$gte": f"{start_date}T00:00:00"}
                if end_date:
                    if "timestamp" in where_clause:
                        where_clause["timestamp"]["$lte"] = f"{end_date}T23:59:59"
                    else:
                        where_clause["timestamp"] = {"$lte": f"{end_date}T23:59:59"}
                
                if where_clause:
                    search_params["where"] = where_clause
                
                # Perform search
                search_results = await chroma_client.search_documents(
                    collection_name="screenshots",
                    **search_params
                )
                
                result = {
                    "query": query,
                    "results": search_results,
                    "total_found": len(search_results),
                    "date_range": {
                        "start_date": start_date,
                        "end_date": end_date
                    }
                }
            
            elif tool_name == "fetch-flow-stats":
                await self.ensure_chroma_initialized()
                
                # Get collection info
                collection_info = await chroma_client.get_collection_info("screenshots")
                
                # Count total documents
                total_count = await chroma_client.count_documents("screenshots")
                
                # Get some sample documents to determine date range
                sample_docs = await chroma_client.search_documents(
                    collection_name="screenshots",
                    query="",
                    limit=100
                )
                
                timestamps = []
                for doc in sample_docs:
                    if doc.get("metadata", {}).get("timestamp"):
                        timestamps.append(doc["metadata"]["timestamp"])
                
                result = {
                    "collection_name": "screenshots",
                    "total_screenshots": total_count,
                    "collection_info": collection_info,
                    "date_range": {
                        "earliest": min(timestamps) if timestamps else None,
                        "latest": max(timestamps) if timestamps else None
                    },
                    "sample_timestamps": sorted(timestamps)[:5] if timestamps else []
                }
            
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
    server = FlowMCPServer()
    
    try:
        logger.info("Flow MCP Server starting on stdio transport")
        logger.info("Available tools: what-can-i-do")
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as error:
        logger.error(f"Server error: {error}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
