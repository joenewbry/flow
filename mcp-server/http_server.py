#!/usr/bin/env python3
"""
HTTP wrapper for Memex MCP Server.
Implements the MCP Streamable HTTP transport (protocol version 2025-11-25)
for use with Anthropic connectors, Cursor, and other MCP clients over ngrok.
"""

import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any, Dict
import argparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
import uvicorn

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from server import FlowMCPServer

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(log_dir / "mcp-server.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

PROTOCOL_VERSION = "2025-11-25"
SERVER_NAME = "memex"
SERVER_VERSION = "1.0.0"

app = FastAPI(title="Memex MCP HTTP Server", version=SERVER_VERSION)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["MCP-Session-Id"],
)

# Initialize Flow MCP server
flow_server = None

# Active sessions
sessions = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the Flow MCP server on startup."""
    global flow_server
    flow_server = FlowMCPServer()
    logger.info("Memex MCP HTTP Server initialized")


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Memex MCP HTTP Server",
        "version": SERVER_VERSION,
        "status": "running",
        "protocolVersion": PROTOCOL_VERSION,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "memex-mcp-server"}


async def _build_tools_list():
    """Build the tools list response payload."""
    tools = await flow_server.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
        }
        for tool in tools
    ]


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    MCP Streamable HTTP transport endpoint.
    Handles all JSON-RPC messages: initialize, notifications, tools/list, tools/call.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            },
        )

    method = body.get("method")
    request_id = body.get("id")  # None for notifications
    params = body.get("params", {})

    logger.info(f"MCP request: method={method} id={request_id}")

    # --- Notifications (no id field) ---
    if request_id is None:
        # notifications/initialized, notifications/cancelled, etc.
        logger.info(f"MCP notification: {method}")
        return Response(status_code=202)

    # --- Requests (have id field) ---

    if method == "initialize":
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"initialized": True}
        logger.info(f"MCP initialize: new session {session_id}")

        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                },
            },
            headers={"MCP-Session-Id": session_id},
        )

    elif method == "tools/list":
        tools = await _build_tools_list()
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools},
            }
        )

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "Missing tool name"},
                }
            )

        try:
            logger.info(f"MCP tools/call: {tool_name} args={arguments}")
            result = await flow_server.call_tool(tool_name, arguments)
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2),
                            }
                        ],
                        "isError": False,
                    },
                }
            )
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({"error": str(e)}),
                            }
                        ],
                        "isError": True,
                    },
                }
            )

    elif method == "ping":
        return JSONResponse(
            content={"jsonrpc": "2.0", "id": request_id, "result": {}}
        )

    else:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        )


# --- Legacy endpoints (kept for direct HTTP usage) ---


@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools (legacy REST endpoint)."""
    try:
        tools = await _build_tools_list()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/call")
async def call_tool(request: Request):
    """Call an MCP tool (legacy REST endpoint)."""
    try:
        body = await request.json()
        tool_name = body.get("tool")
        arguments = body.get("arguments", {})

        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing 'tool' parameter")

        logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
        result = await flow_server.call_tool(tool_name, arguments)

        return {"success": True, "tool": tool_name, "result": result}
    except Exception as e:
        logger.error(f"Error calling tool: {e}")
        return {"success": False, "error": str(e)}


# --- Legacy SSE endpoints (kept for older Cursor versions) ---


@app.get("/sse")
async def sse_endpoint(request: Request):
    """Legacy SSE endpoint for older MCP clients."""
    connection_id = str(uuid.uuid4())

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connection', 'id': connection_id})}\n\n"

            init_response = {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            }
            yield f"data: {json.dumps(init_response)}\n\n"

            tools = await _build_tools_list()
            tools_response = {
                "jsonrpc": "2.0",
                "id": None,
                "result": {"tools": tools},
            }
            yield f"data: {json.dumps(tools_response)}\n\n"

            while True:
                await asyncio.sleep(15)
                yield ": keepalive\n\n"

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"SSE connection error: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/sse")
async def sse_post_endpoint(request: Request):
    """Legacy SSE POST endpoint for older MCP clients."""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            }

        elif method == "tools/list":
            tools = await _build_tools_list()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "Missing tool name"},
                }

            result = await flow_server.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2)}
                    ]
                },
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"},
            }

    except Exception as e:
        logger.error(f"Error handling SSE POST request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if "body" in locals() else None,
            "error": {"code": -32603, "message": str(e)},
        }


def main():
    """Main entry point for the HTTP server."""
    parser = argparse.ArgumentParser(description="Memex MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8082, help="Port to serve on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    logger.info(f"Starting Memex MCP HTTP Server on {args.host}:{args.port}")

    uvicorn.run(
        "http_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
