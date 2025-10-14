#!/usr/bin/env python3
"""
OpenAI Client for Flow Dashboard Chat
Handles OpenAI API integration with tool calling support.
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path

from openai import AsyncOpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client with tool calling support for Flow MCP tools."""
    
    def __init__(self):
        # Load environment variables
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)
        
        # Get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Use faster, cheaper model for chat
        
        # Define tools matching MCP server tools
        self.tools = self._get_tool_definitions()
        
        logger.info("OpenAI client initialized successfully")
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI function definitions for all MCP tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_screenshots",
                    "description": "Search OCR data from screenshots with optional date range parameters",
                    "parameters": {
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
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stats",
                    "description": "Get statistics about OCR data files and ChromaDB collection",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "activity_graph",
                    "description": "Generate activity timeline graph data showing when Flow was active capturing screens",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to include in the graph (default: 7)",
                                "default": 7,
                            },
                            "grouping": {
                                "type": "string",
                                "description": "How to group the data: 'hourly' or 'daily' (default: 'hourly')",
                                "enum": ["hourly", "daily"],
                                "default": "hourly",
                            },
                            "include_empty": {
                                "type": "boolean",
                                "description": "Include time periods with no activity (default: true)",
                                "default": True,
                            },
                        },
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "time_range_summary",
                    "description": "Get a sampled summary of OCR data over a specified time range",
                    "parameters": {
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
                                "description": "Maximum number of results to return (default: 24)",
                                "default": 24,
                            },
                            "include_text": {
                                "type": "boolean",
                                "description": "Include OCR text content in results (default: true)",
                                "default": True,
                            },
                        },
                        "required": ["start_time", "end_time"],
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "start_flow",
                    "description": "Start Flow screenshot recording (starts ChromaDB server and Python capture process)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "stop_flow",
                    "description": "Stop Flow screenshot recording (stops Python capture process and ChromaDB server)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "what_can_i_do",
                    "description": "Get information about what you can do with Flow",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                }
            },
        ]
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a chat completion request with tool calling support.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            
        Yields:
            Chunks of the response including tool calls
        """
        try:
            logger.info(f"Sending chat completion request with {len(messages)} messages")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                stream=stream,
                temperature=0.7,
            )
            
            if stream:
                # Stream response chunks
                async for chunk in response:
                    yield self._process_chunk(chunk)
            else:
                # Return complete response
                yield self._process_response(response)
                
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "message": f"Failed to get response from OpenAI: {str(e)}"
            }
    
    def _process_response(self, response) -> Dict[str, Any]:
        """Process a complete (non-streamed) response."""
        try:
            message = response.choices[0].message
            
            result = {
                "type": "message",
                "content": message.content,
                "role": "assistant",
            }
            
            # Check for tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                result["type"] = "tool_calls"
                result["tool_calls"] = []
                
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {
                "type": "error",
                "error": str(e)
            }
    
    def _process_chunk(self, chunk) -> Dict[str, Any]:
        """Process a streaming response chunk."""
        try:
            delta = chunk.choices[0].delta
            
            result = {"type": "chunk"}
            
            if hasattr(delta, 'content') and delta.content:
                result["content"] = delta.content
            
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                result["type"] = "tool_call_chunk"
                result["tool_calls"] = []
                
                for tool_call in delta.tool_calls:
                    tc_data = {"index": tool_call.index}
                    
                    if hasattr(tool_call, 'id'):
                        tc_data["id"] = tool_call.id
                    
                    if hasattr(tool_call, 'function'):
                        tc_data["function"] = {}
                        if hasattr(tool_call.function, 'name'):
                            tc_data["function"]["name"] = tool_call.function.name
                        if hasattr(tool_call.function, 'arguments'):
                            tc_data["function"]["arguments"] = tool_call.function.arguments
                    
                    result["tool_calls"].append(tc_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            return {
                "type": "error",
                "error": str(e)
            }
    
    @staticmethod
    def format_tool_result(tool_name: str, tool_result: Any) -> str:
        """Format tool result for display in chat."""
        try:
            if isinstance(tool_result, dict):
                # Format based on tool type
                if tool_name == "search_screenshots":
                    results = tool_result.get("results", [])
                    total = tool_result.get("total_found", 0)
                    
                    if total == 0:
                        return "No results found."
                    
                    formatted = f"Found {total} result(s):\n\n"
                    for i, result in enumerate(results[:5], 1):  # Show first 5
                        formatted += f"{i}. {result.get('timestamp', 'Unknown time')}\n"
                        formatted += f"   Screen: {result.get('screen_name', 'Unknown')}\n"
                        formatted += f"   Preview: {result.get('text_preview', '')[:150]}...\n\n"
                    
                    if total > 5:
                        formatted += f"... and {total - 5} more results."
                    
                    return formatted
                
                elif tool_name == "get_stats":
                    stats = tool_result
                    formatted = "System Statistics:\n\n"
                    formatted += f"Total Captures: {stats.get('total_captures', 0)}\n"
                    formatted += f"Unique Screens: {stats.get('unique_screens', 0)}\n"
                    formatted += f"Date Range: {stats.get('date_range', 'N/A')}\n"
                    return formatted
                
                elif tool_name == "activity_graph":
                    summary = tool_result.get("data_summary", {})
                    formatted = "Activity Graph Generated:\n\n"
                    formatted += f"Total Captures: {summary.get('total_captures', 0)}\n"
                    formatted += f"Active Periods: {summary.get('active_periods', 0)}\n"
                    formatted += f"Total Periods: {summary.get('total_periods', 0)}\n"
                    formatted += f"Unique Screens: {', '.join(summary.get('unique_screens', []))}\n"
                    return formatted
                
                else:
                    # Generic formatting
                    return json.dumps(tool_result, indent=2)
            
            return str(tool_result)
            
        except Exception as e:
            logger.error(f"Error formatting tool result: {e}")
            return f"Tool executed but failed to format result: {str(e)}"

