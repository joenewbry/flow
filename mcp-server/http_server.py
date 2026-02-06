#!/usr/bin/env python3
"""
HTTP wrapper for Flow MCP Server to enable ngrok exposure.
This allows the MCP server to be accessed over HTTP instead of stdio.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict
import argparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from server import FlowMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Flow MCP HTTP Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Flow MCP server
flow_server = None

# Store active SSE connections
active_connections = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the Flow MCP server on startup."""
    global flow_server
    flow_server = FlowMCPServer()
    logger.info("Flow MCP HTTP Server initialized")


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Flow MCP HTTP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "list_tools": "/tools/list",
            "call_tool": "/tools/call"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "flow-mcp-server"}


@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools."""
    try:
        tools = await flow_server.list_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
        }
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/call")
async def call_tool(request: Request):
    """Call an MCP tool with the given parameters."""
    try:
        body = await request.json()
        tool_name = body.get("tool")
        arguments = body.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing 'tool' parameter")
        
        logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
        result = await flow_server.call_tool(tool_name, arguments)
        
        return {
            "success": True,
            "tool": tool_name,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    Generic MCP endpoint that handles both list_tools and call_tool requests.
    This matches the standard MCP protocol over HTTP.
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        
        if method == "tools/list":
            tools = await flow_server.list_tools()
            return {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in tools
                ]
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                raise HTTPException(status_code=400, detail="Missing tool name")
            
            result = await flow_server.call_tool(tool_name, arguments)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return {
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


@app.get("/sse")
async def sse_endpoint(request: Request):
    """
    Server-Sent Events endpoint for MCP protocol over HTTP.
    Cursor uses this for streaming MCP communication.
    """
    import uuid
    connection_id = str(uuid.uuid4())
    
    async def event_generator():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connection', 'id': connection_id})}\n\n"
            
            # Store connection
            active_connections[connection_id] = {
                "queue": asyncio.Queue(),
                "initialized": False
            }
            
            # Send initialization response
            init_response = {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "flow",
                        "version": "1.0.0"
                    }
                }
            }
            yield f"data: {json.dumps(init_response)}\n\n"
            active_connections[connection_id]["initialized"] = True
            
            # Send tools list
            tools = await flow_server.list_tools()
            tools_response = {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            }
            yield f"data: {json.dumps(tools_response)}\n\n"
            
            # Keep connection alive and process messages
            while True:
                try:
                    # Check for messages in queue
                    try:
                        message = await asyncio.wait_for(
                            active_connections[connection_id]["queue"].get(),
                            timeout=1.0
                        )
                        yield f"data: {json.dumps(message)}\n\n"
                    except asyncio.TimeoutError:
                        # Send keepalive
                        yield ": keepalive\n\n"
                        continue
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in SSE generator: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
        finally:
            # Clean up connection
            if connection_id in active_connections:
                del active_connections[connection_id]
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/sse")
async def sse_post_endpoint(request: Request):
    """
    Handle POST requests to SSE endpoint for sending MCP messages.
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Handle initialization
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "flow",
                        "version": "1.0.0"
                    }
                }
            }
        
        # Handle tools/list
        elif method == "tools/list":
            tools = await flow_server.list_tools()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            }
        
        # Handle tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing tool name"
                    }
                }
            
            try:
                result = await flow_server.call_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }
            
    except Exception as e:
        logger.error(f"Error handling SSE POST request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


def main():
    """Main entry point for the HTTP server."""
    parser = argparse.ArgumentParser(description='Flow MCP HTTP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8082, help='Port to serve on')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    args = parser.parse_args()
    
    logger.info(f"Starting Flow MCP HTTP Server on {args.host}:{args.port}")
    
    uvicorn.run(
        "http_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()


