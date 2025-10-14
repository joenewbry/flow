#!/usr/bin/env python3
"""
Multi-instance MCP client for connecting to multiple Flow instances.
This allows querying multiple team members' Flow servers through their ngrok URLs.
"""

import asyncio
import json
import sys
from typing import Dict, List, Any, Optional
import aiohttp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiInstanceFlowClient:
    """Client that can connect to multiple Flow instances."""
    
    def __init__(self, instances: Dict[str, str]):
        """
        Initialize with a dictionary of instance names to URLs.
        
        Args:
            instances: Dict mapping user names to their Flow HTTP server URLs
                      e.g., {"john": "https://john-flow.ngrok.io", 
                             "jill": "https://jill-flow.ngrok.io"}
        """
        self.instances = instances
        logger.info(f"Initialized with {len(instances)} Flow instances: {list(instances.keys())}")
    
    async def list_tools(self) -> List[Tool]:
        """List all available tools from all instances."""
        all_tools = []
        
        # For each instance, fetch its tools and prefix with the user name
        for user_name, url in self.instances.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/tools/list") as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Add prefixed tools for this user
                            for tool_data in data.get("tools", []):
                                # Create a prefixed tool name
                                prefixed_name = f"{user_name}-{tool_data['name']}"
                                
                                # Update description to indicate which user
                                description = f"[{user_name.upper()}] {tool_data['description']}"
                                
                                all_tools.append(Tool(
                                    name=prefixed_name,
                                    description=description,
                                    inputSchema=tool_data['inputSchema']
                                ))
            except Exception as e:
                logger.error(f"Error fetching tools from {user_name} ({url}): {e}")
        
        return all_tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on a specific instance.
        
        Args:
            name: Tool name in format "username-toolname" (e.g., "john-search-screenshots")
            arguments: Tool arguments
        """
        # Parse the user name from the tool name
        if "-" not in name:
            return {"error": "Tool name must be in format 'username-toolname'"}
        
        parts = name.split("-", 1)
        user_name = parts[0]
        tool_name = parts[1]
        
        if user_name not in self.instances:
            return {"error": f"Unknown user: {user_name}. Available users: {list(self.instances.keys())}"}
        
        url = self.instances[user_name]
        
        # Handle local instance specially
        if url.lower() == "local":
            # Import and use the local Flow server directly
            try:
                from pathlib import Path
                import sys
                sys.path.append(str(Path(__file__).parent))
                from server import FlowMCPServer
                
                if not hasattr(self, '_local_server'):
                    self._local_server = FlowMCPServer()
                
                result = await self._local_server.call_tool(tool_name, arguments)
                result["_source_user"] = user_name
                result["_source_url"] = "local"
                return result
            except Exception as e:
                logger.error(f"Error calling local tool {tool_name}: {e}")
                return {
                    "error": str(e),
                    "user": user_name,
                    "tool": tool_name
                }
        
        # Handle remote instance via HTTP
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "tool": tool_name,
                    "arguments": arguments
                }
                
                async with session.post(f"{url}/tools/call", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Add metadata about which user this came from
                        if data.get("success"):
                            result = data.get("result", {})
                            result["_source_user"] = user_name
                            result["_source_url"] = url
                            return result
                        else:
                            return data
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"HTTP {response.status}: {error_text}",
                            "user": user_name
                        }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on {user_name}: {e}")
            return {
                "error": str(e),
                "user": user_name,
                "tool": tool_name
            }


async def main():
    """Main entry point for the multi-instance client."""
    
    # Read instance configuration from environment variable
    # Format: "john:https://john.ngrok.io,jill:https://jill.ngrok.io"
    instances_env = os.getenv("FLOW_INSTANCES", "")
    
    if not instances_env:
        logger.error("FLOW_INSTANCES environment variable not set")
        logger.info("Set it like: export FLOW_INSTANCES='john:https://john.ngrok.io,jill:https://jill.ngrok.io'")
        sys.exit(1)
    
    # Parse instances
    instances = {}
    for instance_str in instances_env.split(","):
        if ":" in instance_str:
            name, url = instance_str.split(":", 1)
            # Ensure URL starts with http:// or https://
            if not url.startswith("http"):
                url = f"https://{url}"
            instances[name.strip()] = url.strip()
    
    if not instances:
        logger.error("No valid instances found in FLOW_INSTANCES")
        sys.exit(1)
    
    logger.info(f"Configured Flow instances: {list(instances.keys())}")
    
    # Create multi-instance client
    client = MultiInstanceFlowClient(instances)
    
    # Create MCP server
    server = Server("flow-multi")
    
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """Handle list tools request."""
        return await client.list_tools()
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
        """Handle call tool request."""
        try:
            result = await client.call_tool(name, arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error in handle_call_tool: {e}")
            error_result = {"error": str(e), "tool": name}
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Flow Multi-Instance MCP Server running on stdio transport")
        
        # Create initialization options
        init_options = InitializationOptions(
            server_name="flow-multi",
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

