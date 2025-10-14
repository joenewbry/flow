#!/usr/bin/env python3
"""
Chat Manager for Flow Dashboard
Handles message queue, OpenAI integration, and tool execution coordination.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from collections import deque

from dashboard.lib.openai_client import OpenAIClient
from dashboard.lib.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


class ChatMessage:
    """Represents a chat message in the queue."""
    
    def __init__(self, message_id: str, role: str, content: str, timestamp: Optional[str] = None):
        self.id = message_id
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.status = "queued"  # queued, processing, completed, error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "status": self.status
        }


class ChatManager:
    """Manages chat conversations, message queue, and tool execution."""
    
    def __init__(self, websocket_broadcast_callback: Optional[Callable] = None):
        """
        Initialize chat manager.
        
        Args:
            websocket_broadcast_callback: Async function to broadcast updates to clients
        """
        self.openai_client = OpenAIClient()
        self.tool_executor = ToolExecutor()
        self.broadcast = websocket_broadcast_callback
        
        # Message queue
        self.message_queue = deque()
        self.processing = False
        self.current_message: Optional[ChatMessage] = None
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant for the Flow screen capture system. "
                    "You have access to tools that can search screenshots, generate activity reports, "
                    "and control the Flow system. When users ask about their screen history or activity, "
                    "use the appropriate tools to help them find the information they need."
                )
            }
        ]
        
        logger.info("Chat manager initialized")
    
    async def add_message(self, message_id: str, content: str) -> None:
        """
        Add a message to the queue and start processing if not already processing.
        
        Args:
            message_id: Unique ID for the message
            content: Message content
        """
        message = ChatMessage(message_id, "user", content)
        self.message_queue.append(message)
        
        logger.info(f"Message {message_id} added to queue. Queue size: {len(self.message_queue)}")
        
        # Broadcast queue update
        await self._broadcast_queue_update()
        
        # Start processing if not already processing
        if not self.processing:
            asyncio.create_task(self._process_queue())
    
    async def _process_queue(self) -> None:
        """Process messages in the queue one at a time."""
        if self.processing:
            return
        
        self.processing = True
        
        try:
            while self.message_queue:
                message = self.message_queue.popleft()
                self.current_message = message
                message.status = "processing"
                
                logger.info(f"Processing message {message.id}")
                
                # Broadcast processing status
                await self._broadcast_message_status(message, "processing")
                
                # Process the message
                await self._process_message(message)
                
                # Mark as completed
                message.status = "completed"
                self.current_message = None
                
                # Broadcast completion
                await self._broadcast_message_status(message, "completed")
                
        except Exception as e:
            logger.error(f"Error in queue processing: {e}")
            if self.current_message:
                self.current_message.status = "error"
                await self._broadcast_message_status(self.current_message, "error", str(e))
        
        finally:
            self.processing = False
            self.current_message = None
            await self._broadcast_queue_update()
    
    async def _process_message(self, message: ChatMessage) -> None:
        """Process a single message."""
        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message.content
            })
            
            # Get response from OpenAI
            response_generator = self.openai_client.chat_completion(
                messages=self.conversation_history,
                stream=False
            )
            
            # Get the response
            async for response in response_generator:
                if response.get("type") == "error":
                    # Handle error
                    error_msg = response.get("message", "Unknown error")
                    await self._broadcast_chat_message("error", error_msg)
                    logger.error(f"OpenAI error: {error_msg}")
                    return
                
                if response.get("type") == "tool_calls":
                    # Execute tools
                    await self._handle_tool_calls(response.get("tool_calls", []))
                    
                elif response.get("type") == "message":
                    # Regular message response
                    content = response.get("content", "")
                    if content:
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": content
                        })
                        await self._broadcast_chat_message("assistant", content)
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._broadcast_chat_message("error", f"Failed to process message: {str(e)}")
    
    async def _handle_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> None:
        """Handle tool calls from OpenAI."""
        try:
            # Add tool calls to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls
            })
            
            tool_results = []
            
            for tool_call in tool_calls:
                tool_id = tool_call.get("id")
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})
                
                logger.info(f"Executing tool: {tool_name}")
                
                # Broadcast tool execution status
                await self._broadcast_tool_status(tool_name, "executing", tool_args)
                
                # Execute the tool
                result = await self.tool_executor.execute_tool(tool_name, tool_args)
                
                # Broadcast tool result
                await self._broadcast_tool_status(tool_name, "completed", tool_args, result)
                
                # Add tool result to conversation history
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": json.dumps(result)
                })
            
            # Add all tool results to conversation
            self.conversation_history.extend(tool_results)
            
            # Get final response from OpenAI with tool results
            response_generator = self.openai_client.chat_completion(
                messages=self.conversation_history,
                stream=False
            )
            
            async for response in response_generator:
                if response.get("type") == "message":
                    content = response.get("content", "")
                    if content:
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": content
                        })
                        await self._broadcast_chat_message("assistant", content)
        
        except Exception as e:
            logger.error(f"Error handling tool calls: {e}")
            await self._broadcast_chat_message("error", f"Tool execution failed: {str(e)}")
    
    async def _broadcast_chat_message(self, role: str, content: str) -> None:
        """Broadcast a chat message to connected clients."""
        if self.broadcast:
            await self.broadcast({
                "type": "chat_message",
                "data": {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
            })
    
    async def _broadcast_tool_status(
        self,
        tool_name: str,
        status: str,
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Broadcast tool execution status."""
        if self.broadcast:
            data = {
                "tool_name": tool_name,
                "status": status,
                "arguments": arguments,
                "timestamp": datetime.now().isoformat()
            }
            
            if result:
                data["result"] = result
            
            await self.broadcast({
                "type": "tool_status",
                "data": data
            })
    
    async def _broadcast_message_status(
        self,
        message: ChatMessage,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """Broadcast message processing status."""
        if self.broadcast:
            data = {
                "message_id": message.id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            if error:
                data["error"] = error
            
            await self.broadcast({
                "type": "message_status",
                "data": data
            })
    
    async def _broadcast_queue_update(self) -> None:
        """Broadcast queue status update."""
        if self.broadcast:
            queue_items = [msg.to_dict() for msg in self.message_queue]
            
            await self.broadcast({
                "type": "queue_update",
                "data": {
                    "queue": queue_items,
                    "queue_size": len(queue_items),
                    "processing": self.processing,
                    "current_message": self.current_message.to_dict() if self.current_message else None,
                    "timestamp": datetime.now().isoformat()
                }
            })
    
    async def clear_queue(self) -> None:
        """Clear all queued messages."""
        self.message_queue.clear()
        await self._broadcast_queue_update()
        logger.info("Message queue cleared")
    
    async def clear_conversation(self) -> None:
        """Clear conversation history (keep system message)."""
        self.conversation_history = [self.conversation_history[0]]  # Keep system message
        await self._broadcast_chat_message("system", "Conversation cleared")
        logger.info("Conversation history cleared")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            "queue_size": len(self.message_queue),
            "processing": self.processing,
            "current_message": self.current_message.to_dict() if self.current_message else None,
            "queue": [msg.to_dict() for msg in self.message_queue]
        }

