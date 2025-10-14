#!/usr/bin/env python3
"""
Tool Executor for Flow Dashboard Chat
Executes MCP tools and returns results.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes MCP tools for the chat interface."""
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        
        # Import MCP tools
        try:
            from mcp_server.tools.search import SearchTool
            from mcp_server.tools.stats import StatsTool
            from mcp_server.tools.activity import ActivityTool
            from mcp_server.tools.system import SystemTool
            
            self.search_tool = SearchTool(self.workspace_root)
            self.stats_tool = StatsTool(self.workspace_root)
            self.activity_tool = ActivityTool(self.workspace_root)
            self.system_tool = SystemTool(self.workspace_root)
            
            logger.info("Tool executor initialized with all MCP tools")
            
        except Exception as e:
            logger.error(f"Error importing MCP tools: {e}")
            raise
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments for the tool
            
        Returns:
            Dictionary containing the tool result
        """
        try:
            logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
            
            # Map tool name to method
            if tool_name == "search_screenshots":
                result = await self.search_tool.search_screenshots(
                    query=arguments.get("query", ""),
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date"),
                    limit=arguments.get("limit", 10)
                )
            
            elif tool_name == "get_stats":
                result = await self.stats_tool.get_stats()
            
            elif tool_name == "activity_graph":
                result = await self.activity_tool.activity_graph(
                    days=arguments.get("days", 7),
                    grouping=arguments.get("grouping", "hourly"),
                    include_empty=arguments.get("include_empty", True)
                )
            
            elif tool_name == "time_range_summary":
                result = await self.activity_tool.time_range_summary(
                    start_time=arguments.get("start_time"),
                    end_time=arguments.get("end_time"),
                    max_results=arguments.get("max_results", 24),
                    include_text=arguments.get("include_text", True)
                )
            
            elif tool_name == "start_flow":
                result = await self.system_tool.start_flow()
            
            elif tool_name == "stop_flow":
                result = await self.system_tool.stop_flow()
            
            elif tool_name == "what_can_i_do":
                result = await self.system_tool.what_can_i_do()
            
            else:
                result = {
                    "error": f"Unknown tool: {tool_name}",
                    "tool": tool_name
                }
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "error": str(e),
                "tool": tool_name,
                "arguments": arguments
            }

