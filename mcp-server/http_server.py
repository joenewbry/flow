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
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import markdown

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

# Website paths
WEBSITE_ROOT = Path(__file__).parent.parent / "website-builder"
PAGES_DIR = WEBSITE_ROOT / "pages"
STATIC_DIR = WEBSITE_ROOT / "static"

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


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
            "call_tool": "/tools/call",
            "pages": "/pages",
            "page": "/page/{page_name}"
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


@app.get("/pages")
async def list_pages():
    """List all available pages."""
    if not PAGES_DIR.exists():
        return {"pages": []}
    
    pages = []
    # Look for both .md and .html files
    for file_path in PAGES_DIR.glob("*"):
        if file_path.suffix in [".md", ".html"]:
            pages.append({
                "name": file_path.stem,
                "type": file_path.suffix[1:],
                "url": f"/page/{file_path.stem}"
            })
    
    return {"pages": sorted(pages, key=lambda x: x["name"])}


@app.get("/page/{page_name}", response_class=HTMLResponse)
async def serve_page(page_name: str):
    """Serve a page (markdown or HTML)."""
    # Try markdown first
    md_path = PAGES_DIR / f"{page_name}.md"
    if md_path.exists():
        return await serve_markdown_page(md_path, page_name)
    
    # Fall back to HTML
    html_path = PAGES_DIR / f"{page_name}.html"
    if html_path.exists():
        return FileResponse(html_path)
    
    raise HTTPException(status_code=404, detail=f"Page '{page_name}' not found")


async def serve_markdown_page(md_path: Path, page_name: str) -> HTMLResponse:
    """Render and serve a markdown file as HTML."""
    try:
        # Read markdown content
        md_content = md_path.read_text(encoding='utf-8')
        
        # Initialize markdown processor
        md = markdown.Markdown(extensions=[
            'fenced_code',
            'tables',
            'nl2br',
            'sane_lists',
            'codehilite'
        ])
        
        # Convert to HTML
        html_content = md.convert(md_content)
        
        # Get metadata
        from datetime import datetime
        stat = md_path.stat()
        modified_date = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # Extract title from first heading or use page name
        title = page_name.replace('-', ' ').title()
        lines = md_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        # Build complete HTML page
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Flow</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>{title}</h1>
            <div class="meta">
                <span class="date">{modified_date}</span>
            </div>
        </div>
    </header>
    
    <main class="container markdown-content">
        {html_content}
    </main>
    
    <footer>
        <div class="container">
            <p>Generated by <a href="https://github.com/joenewbry/flow">Flow</a></p>
        </div>
    </footer>
</body>
</html>"""
        
        return HTMLResponse(content=html)
        
    except Exception as e:
        logger.error(f"Error rendering markdown: {e}")
        raise HTTPException(status_code=500, detail=f"Error rendering markdown: {str(e)}")


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


