#!/usr/bin/env python3
"""
Flow MCP Server
Provides tools for interacting with Flow CLI via Model Context Protocol
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta, timezone
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
        self.screenhistory_dir = Path("data/screen_history")
        
        # Set server capabilities to indicate tools are supported
        from mcp.types import ServerCapabilities
        self.server.capabilities = ServerCapabilities(
            tools={}  # Indicate that tools are supported
        )
        
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
    
    async def _read_json_files_in_time_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Read and parse JSON files within a time range."""
        if not self.screenhistory_dir.exists():
            logger.warning(f"Screen history directory not found: {self.screenhistory_dir}")
            return []
        
        data_entries = []
        
        try:
            json_files = list(self.screenhistory_dir.glob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files in {self.screenhistory_dir}")
            
            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content or content == 'null':
                        continue
                    
                    data = json.loads(content)
                    
                    if not isinstance(data, dict) or 'timestamp' not in data:
                        continue
                    
                    # Convert timestamp to ISO format
                    timestamp_str = self._convert_filename_timestamp_to_iso(data['timestamp'])
                    
                    try:
                        file_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if file_time.tzinfo is None:
                            file_time = file_time.replace(tzinfo=timezone.utc)
                    except ValueError as e:
                        logger.warning(f"Invalid timestamp in {file_path}: {timestamp_str}")
                        continue
                    
                    # Check if within time range
                    if start_time <= file_time <= end_time:
                        data['timestamp'] = timestamp_str
                        data_entries.append(data)
                
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"Error reading {file_path}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error reading {file_path}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scanning directory {self.screenhistory_dir}: {e}")
        
        # Sort by timestamp
        data_entries.sort(key=lambda x: x['timestamp'])
        logger.info(f"Found {len(data_entries)} entries in time range")
        
        return data_entries
    
    def _convert_filename_timestamp_to_iso(self, timestamp_str: str) -> str:
        """Convert filename-style timestamps to ISO 8601."""
        if not isinstance(timestamp_str, str):
            return timestamp_str
        
        # Check if already in ISO format
        if ('T' in timestamp_str and ':' in timestamp_str and 
            ('.' in timestamp_str or timestamp_str.endswith('Z'))):
            try:
                datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return timestamp_str
            except ValueError:
                pass
        
        # Parse filename format
        parts = timestamp_str.split('T')
        if len(parts) != 2:
            return timestamp_str
        
        time_part = parts[1]
        z_suffix = 'Z' if time_part.endswith('Z') else ''
        if z_suffix:
            time_part = time_part[:-1]
        
        time_segments = time_part.split('-')
        if len(time_segments) == 4:
            return f"{parts[0]}T{time_segments[0]}:{time_segments[1]}:{time_segments[2]}.{time_segments[3]}{z_suffix}"
        elif len(time_segments) == 3:
            return f"{parts[0]}T{time_segments[0]}:{time_segments[1]}:{time_segments[2]}{z_suffix}"
        
        return timestamp_str
    
    async def _generate_summary_with_ai(self, content: str, summary_type: str, time_info: str) -> str:
        """Generate summary using text analysis (no AI required)."""
        try:
            # Parse the content to extract useful information
            entries = []
            for line in content.split('\n'):
                if line.strip() and not line.startswith('='):
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            if not entries:
                return f"No activity data found for {summary_type} summary covering {time_info}."
            
            # Extract basic statistics
            apps = {}
            total_chars = 0
            total_words = 0
            activities = []
            
            for entry in entries:
                app = entry.get('active_app', 'Unknown')
                apps[app] = apps.get(app, 0) + 1
                
                text = entry.get('text', '')
                total_chars += len(text)
                total_words += len(text.split())
                
                summary = entry.get('summary', '')
                if summary:
                    activities.append(summary)
            
            # Create simple text summary
            summary_parts = [
                f"# {summary_type.title()} Summary - {time_info}",
                "",
                "## Overview",
                f"- Total entries: {len(entries)}",
                f"- Text captured: {total_chars:,} characters, {total_words:,} words",
                "",
                "## Applications Used",
            ]
            
            # Top 5 most used applications
            top_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)[:5]
            for app, count in top_apps:
                summary_parts.append(f"- {app}: {count} entries")
            
            if activities:
                summary_parts.extend([
                    "",
                    "## Key Activities",
                ])
                # Show first few unique activities
                unique_activities = list(set(activities))[:5]
                for activity in unique_activities:
                    summary_parts.append(f"- {activity}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Summary generation failed: {str(e)}"
    
    async def get_daily_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Get daily summary for a specific date."""
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
        else:
            target_date = datetime.now(timezone.utc)
        
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Generate new summary
        entries = await self._read_json_files_in_time_range(start_time, end_time)
        
        if not entries:
            return {
                "date": target_date.strftime('%Y-%m-%d'),
                "summary": "No screen activity data found for this date.",
                "entry_count": 0
            }
        
        # Prepare content for AI
        content_parts = []
        for entry in entries:
            timestamp = entry.get('timestamp', 'Unknown time')
            summary = entry.get('summary', 'No summary')
            app = entry.get('active_app', 'Unknown app')
            extracted_text = entry.get('extracted_text', '')[:200]  # Limit text length
            
            content_parts.append(f"[{timestamp}] {app}: {summary}")
            if extracted_text:
                content_parts.append(f"  Text: {extracted_text}")
        
        content = '\n'.join(content_parts)
        
        # Generate AI summary
        ai_summary = await self._generate_summary_with_ai(
            content, 
            "daily", 
            target_date.strftime('%Y-%m-%d')
        )
        
        return {
            "date": target_date.strftime('%Y-%m-%d'),
            "summary": ai_summary,
            "entry_count": len(entries)
        }
    
    async def get_time_range_summary(self, start_time_str: str, end_time_str: str) -> Dict[str, Any]:
        """Get summary for a custom time range."""
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
                
        except ValueError as e:
            raise ValueError(f"Invalid time format: {e}")
        
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
        
        entries = await self._read_json_files_in_time_range(start_time, end_time)
        
        if not entries:
            return {
                "start_time": start_time_str,
                "end_time": end_time_str,
                "summary": "No screen activity data found for this time range.",
                "entry_count": 0
            }
        
        # Prepare content for AI
        content_parts = []
        for entry in entries:
            timestamp = entry.get('timestamp', 'Unknown time')
            summary = entry.get('summary', 'No summary')
            app = entry.get('active_app', 'Unknown app')
            extracted_text = entry.get('extracted_text', '')[:200]
            
            content_parts.append(f"[{timestamp}] {app}: {summary}")
            if extracted_text:
                content_parts.append(f"  Text: {extracted_text}")
        
        content = '\n'.join(content_parts)
        
        # Generate AI summary
        duration = end_time - start_time
        time_info = f"{start_time_str} to {end_time_str} (duration: {duration})"
        
        ai_summary = await self._generate_summary_with_ai(content, "time range", time_info)
        
        return {
            "start_time": start_time_str,
            "end_time": end_time_str,
            "summary": ai_summary,
            "entry_count": len(entries),
            "duration": str(duration)
        }
    
    async def get_last_hours_summary(self, hours: int) -> Dict[str, Any]:
        """Get summary for the last N hours."""
        if hours < 1 or hours > 168:
            raise ValueError("Hours must be between 1 and 168 (1 week)")
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        return await self.get_time_range_summary(
            start_time.isoformat(),
            end_time.isoformat()
        )
    
    async def get_hourly_summary(self, hour_str: str) -> Dict[str, Any]:
        """Get summary for a specific hour."""
        import re
        
        # Validate hour format
        if not re.match(r'^\d{4}-\d{2}-\d{2}-\d{2}$', hour_str):
            raise ValueError("Hour must be in YYYY-MM-DD-HH format")
        
        try:
            # Parse hour string
            year, month, day, hour = map(int, hour_str.split('-'))
            start_time = datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)
            end_time = start_time + timedelta(hours=1)
            
        except ValueError as e:
            raise ValueError(f"Invalid hour format: {e}")
        
        # Generate new summary
        entries = await self._read_json_files_in_time_range(start_time, end_time)
        
        if not entries:
            return {
                "hour": hour_str,
                "summary": "No screen activity data found for this hour.",
                "entry_count": 0
            }
        
        # Prepare content for AI
        content_parts = []
        for entry in entries:
            timestamp = entry.get('timestamp', 'Unknown time')
            summary = entry.get('summary', 'No summary')
            app = entry.get('active_app', 'Unknown app')
            extracted_text = entry.get('extracted_text', '')[:200]
            
            content_parts.append(f"[{timestamp}] {app}: {summary}")
            if extracted_text:
                content_parts.append(f"  Text: {extracted_text}")
        
        content = '\n'.join(content_parts)
        
        # Generate AI summary
        ai_summary = await self._generate_summary_with_ai(
            content,
            "hourly",
            f"{hour_str}:00-{hour_str}:59"
        )
        
        return {
            "hour": hour_str,
            "summary": ai_summary,
            "entry_count": len(entries)
        }
        
    def setup_tools(self):
        """Define available MCP tools."""
        tools = [
            Tool(
                name="hello-world",
                description="A simple hello world tool for testing MCP client connection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name to greet (optional)",
                            "default": "World"
                        }
                    },
                    "additionalProperties": False
                }
            )
            # Commented out all other tools for debugging
            # Tool(
            #     name="what-can-i-do",
            #     description="Get information about what you can do with Flow",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {},
            #         "additionalProperties": False
            #     }
            # ),
            # Tool(
            #     name="search-screenshots",
            #     description="Search OCR data from screenshots with optional date range parameters",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {
            #             "query": {
            #                 "type": "string",
            #                 "description": "Search query for the OCR text content"
            #             },
            #             "start_date": {
            #                 "type": "string",
            #                 "description": "Start date for search (YYYY-MM-DD format, optional)"
            #             },
            #             "end_date": {
            #                 "type": "string", 
            #                 "description": "End date for search (YYYY-MM-DD format, optional)"
            #             },
            #             "limit": {
            #                 "type": "integer",
            #                 "description": "Maximum number of results to return (default: 10)",
            #                 "default": 10
            #             }
            #         },
            #         "required": ["query"],
            #         "additionalProperties": False
            #     }
            # ),
            # Tool(
            #     name="fetch-flow-stats",
            #     description="Get statistics about screenshots saved in the screenshots collection",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {},
            #         "additionalProperties": False
            #     }
            # ),
            # Tool(
            #     name="get-daily-summary",
            #     description="Get a summary of screen activity for a specific day",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {
            #             "date": {
            #                 "type": "string",
            #                 "description": "Date in YYYY-MM-DD format (optional, defaults to today)",
            #                 "format": "date"
            #             }
            #         },
            #         "additionalProperties": False
            #     }
            # ),
            # Tool(
            #     name="get-time-range-summary",
            #     description="Get a summary of screen activity for a custom time range",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {
            #             "start_time": {
            #                 "type": "string",
            #                 "description": "Start time in ISO 8601 format (e.g., 2025-07-17T09:00:00Z)",
            #                 "format": "date-time"
            #             },
            #             "end_time": {
            #                 "type": "string",
            #                 "description": "End time in ISO 8601 format (e.g., 2025-07-17T17:00:00Z)",
            #                 "format": "date-time"
            #             }
            #         },
            #         "required": ["start_time", "end_time"],
            #         "additionalProperties": False
            #     }
            # ),
            # Tool(
            #     name="get-hourly-summary",
            #     description="Get a summary of screen activity for a specific hour",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {
            #             "hour": {
            #                 "type": "string",
            #                 "description": "Hour in YYYY-MM-DD-HH format (e.g., 2025-07-17-14)"
            #             }
            #         },
            #         "required": ["hour"],
            #         "additionalProperties": False
            #     }
            # ),
            # Tool(
            #     name="get-last-hours-summary",
            #     description="Get a summary of screen activity for the last N hours",
            #     inputSchema={
            #         "type": "object",
            #         "properties": {
            #             "hours": {
            #                 "type": "integer",
            #                 "description": "Number of hours to look back (1-168)",
            #                 "minimum": 1,
            #                 "maximum": 168
            #             }
            #         },
            #         "required": ["hours"],
            #         "additionalProperties": False
            #     }
            # )
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
            
            if tool_name == "hello-world":
                name = request.params.arguments.get("name", "World")
                result = {
                    "message": f"Hello, {name}!",
                    "status": "success",
                    "tool": "hello-world",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            
            # Commented out all other tool handlers for debugging
            # elif tool_name == "what-can-i-do":
            #     result = {
            #         "flow_capabilities": [
            #             "Search for anything that you worked on while using flow. This includes urls, document titles, jira tickets, etc.",
            #             "Get statistics about your screenshot collection",
            #             "Search OCR data from screenshots with optional date ranges",
            #             "Generate summaries of your screen activity for daily, hourly, or custom time ranges"
            #         ],
            #         "description": "Flow is a screen activity tracking and analysis tool that helps you search and analyze your work patterns.",
            #         "available_tools": [
            #             "what-can-i-do",
            #             "search-screenshots", 
            #             "fetch-flow-stats",
            #             "get-daily-summary",
            #             "get-time-range-summary",
            #             "get-hourly-summary",
            #             "get-last-hours-summary"
            #         ]
            #     }
            # 
            # elif tool_name == "search-screenshots":
            #     await self.ensure_chroma_initialized()
            #     
            #     query = request.params.arguments.get("query")
            #     start_date = request.params.arguments.get("start_date")
            #     end_date = request.params.arguments.get("end_date")
            #     limit = request.params.arguments.get("limit", 10)
            #     
            #     # Build search parameters
            #     search_params = {
            #         "query": query,
            #         "limit": limit
            #     }
            #     
            #     # Add date filtering if provided
            #     where_clause = {}
            #     if start_date:
            #         where_clause["timestamp"] = {"$gte": f"{start_date}T00:00:00"}
            #     if end_date:
            #         if "timestamp" in where_clause:
            #             where_clause["timestamp"]["$lte"] = f"{end_date}T23:59:59"
            #         else:
            #             where_clause["timestamp"] = {"$lte": f"{end_date}T23:59:59"}
            #     
            #     if where_clause:
            #         search_params["where"] = where_clause
            #     
            #     # Perform search
            #     search_results = await chroma_client.search_documents(
            #         collection_name="screenshots",
            #         **search_params
            #     )
            #     
            #     result = {
            #         "query": query,
            #         "results": search_results,
            #         "total_found": len(search_results),
            #         "date_range": {
            #             "start_date": start_date,
            #             "end_date": end_date
            #         }
            #     }
            # 
            # elif tool_name == "fetch-flow-stats":
            #     await self.ensure_chroma_initialized()
            #     
            #     # Get collection info
            #     collection_info = await chroma_client.get_collection_info("screenshots")
            #     
            #     # Count total documents
            #     total_count = await chroma_client.count_documents("screenshots")
            #     
            #     # Get some sample documents to determine date range
            #     sample_docs = await chroma_client.search_documents(
            #         collection_name="screenshots",
            #         query="",
            #         limit=100
            #     )
            #     
            #     timestamps = []
            #     for doc in sample_docs:
            #         if doc.get("metadata", {}).get("timestamp"):
            #             timestamps.append(doc["metadata"]["timestamp"])
            #     
            #     result = {
            #         "collection_name": "screenshots",
            #         "total_screenshots": total_count,
            #         "collection_info": collection_info,
            #         "date_range": {
            #             "earliest": min(timestamps) if timestamps else None,
            #             "latest": max(timestamps) if timestamps else None
            #         },
            #         "sample_timestamps": sorted(timestamps)[:5] if timestamps else []
            #     }
            # 
            # elif tool_name == "get-daily-summary":
            #     date_str = request.params.arguments.get("date")
            #     result = await self.get_daily_summary(date_str)
            # 
            # elif tool_name == "get-time-range-summary":
            #     start_time = request.params.arguments.get("start_time")
            #     end_time = request.params.arguments.get("end_time")
            #     result = await self.get_time_range_summary(start_time, end_time)
            # 
            # elif tool_name == "get-hourly-summary":
            #     hour_str = request.params.arguments.get("hour")
            #     result = await self.get_hourly_summary(hour_str)
            # 
            # elif tool_name == "get-last-hours-summary":
            #     hours = request.params.arguments.get("hours")
            #     result = await self.get_last_hours_summary(hours)
            
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
        tools = server.setup_tools()
        tool_names = [tool.name for tool in tools]
        logger.info(f"Available tools: {', '.join(tool_names)}")
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as error:
        logger.error(f"Server error: {error}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
