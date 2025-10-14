#!/usr/bin/env python3
"""
Flow Dashboard - Main FastAPI Application

A web-based dashboard for managing and monitoring the Flow screen capture system.
Provides real-time status monitoring, OCR data visualization, and system controls.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

# Add the parent directory to the path to import from refinery
sys.path.append(str(Path(__file__).parent.parent))

from dashboard.lib.process_manager import ProcessManager
from dashboard.lib.data_handler import DataHandler
from dashboard.api.ocr_data import router as ocr_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
process_manager: Optional[ProcessManager] = None
data_handler: Optional[DataHandler] = None

# WebSocket connections for real-time updates
websocket_connections: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global process_manager, data_handler
    
    # Startup
    logger.info("Starting Flow Dashboard...")
    
    # Initialize components
    process_manager = ProcessManager()
    data_handler = DataHandler()
    
    # Load initial state
    await process_manager.load_state()
    
    logger.info("Flow Dashboard started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Flow Dashboard...")
    
    if process_manager:
        await process_manager.cleanup()
    
    logger.info("Flow Dashboard shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Flow Dashboard",
    description="Web-based dashboard for Flow screen capture system",
    version="1.0.0",
    lifespan=lifespan
)

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(ocr_router)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    try:
        # Get current system status
        status = await process_manager.get_status()
        
        # Get basic OCR statistics
        stats = await data_handler.get_basic_stats()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "status": status,
            "stats": stats,
            "title": "Flow Dashboard"
        })
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hampsters", response_class=HTMLResponse)
async def hampsters_visualization(request: Request):
    """Hamster visualization page."""
    try:
        # Get current system status for real-time integration
        status = await process_manager.get_status()
        
        return templates.TemplateResponse("hampsters.html", {
            "request": request,
            "status": status,
            "title": "Hamsters at Work - Flow Visualization"
        })
    except Exception as e:
        logger.error(f"Error loading hamsters page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    try:
        status = await process_manager.get_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/start")
async def start_system():
    """Start the Flow system (ChromaDB + Screen Capture)."""
    try:
        result = await process_manager.start_system()
        
        # Notify WebSocket clients
        await broadcast_status_update()
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error starting system: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stop")
async def stop_system():
    """Stop the Flow system."""
    try:
        result = await process_manager.stop_system()
        
        # Notify WebSocket clients
        await broadcast_status_update()
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error stopping system: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get OCR data statistics."""
    try:
        stats = await data_handler.get_detailed_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Activity data endpoint is now handled by the OCR API router


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send initial status
        status = await process_manager.get_status()
        await websocket.send_json({"type": "status_update", "data": status})
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages (ping/pong to keep connection alive)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


async def broadcast_status_update():
    """Broadcast status updates to all connected WebSocket clients."""
    if not websocket_connections:
        return
        
    try:
        status = await process_manager.get_status()
        message = {"type": "status_update", "data": status}
        
        # Send to all connected clients
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            websocket_connections.remove(websocket)
            
    except Exception as e:
        logger.error(f"Error broadcasting status update: {e}")


async def broadcast_hamster_state_update(state_data: Dict[str, Any]):
    """Broadcast hamster state update to all connected WebSocket clients."""
    if not websocket_connections:
        return
        
    try:
        message = {"type": "hamster_state_update", "data": state_data}
        
        # Send to all connected clients
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            websocket_connections.remove(websocket)
            
    except Exception as e:
        logger.error(f"Error broadcasting hamster state update: {e}")


async def broadcast_hamster_event(event_data: Dict[str, Any]):
    """Broadcast hamster event to all connected WebSocket clients."""
    if not websocket_connections:
        return
        
    try:
        message = {"type": "hamster_event", "data": event_data}
        
        # Send to all connected clients
        disconnected = []
        for websocket in websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            websocket_connections.remove(websocket)
            
    except Exception as e:
        logger.error(f"Error broadcasting hamster event: {e}")


@app.post("/api/hamster-state-update")
async def trigger_hamster_state_update(state_data: Dict[str, Any]):
    """Trigger a hamster state update for testing."""
    try:
        await broadcast_hamster_state_update(state_data)
        return {"status": "success", "message": "Hamster state update broadcasted"}
    except Exception as e:
        logger.error(f"Error triggering hamster state update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hamster-event")
async def trigger_hamster_event(event_data: Dict[str, Any]):
    """Trigger a hamster event for testing."""
    try:
        await broadcast_hamster_event(event_data)
        return {"status": "success", "message": "Hamster event broadcasted"}
    except Exception as e:
        logger.error(f"Error triggering hamster event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mcp-status")
async def get_mcp_status():
    """Get MCP server status and client information."""
    try:
        # Check if MCP server is running
        import subprocess
        import os
        
        mcp_status = {
            "running": False,
            "clients": 0,
            "last_request": None,
            "active_connections": []
        }
        
        # Check if MCP server process is running
        try:
            # Look for the MCP server process
            result = subprocess.run(['pgrep', '-f', 'mcp-server'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                mcp_status["running"] = True
                
                # Simulate client tracking (in real implementation, this would be actual data)
                # You could track this via log files, shared memory, or a database
                mcp_status["clients"] = 1 if result.stdout.strip() else 0
                mcp_status["last_request"] = "2024-01-01T12:00:00Z"  # Placeholder
                
        except Exception as e:
            logger.error(f"Error checking MCP server process: {e}")
        
        return JSONResponse(content=mcp_status)
        
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "flow-dashboard"}


if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8082"))
    
    # Log the address we're trying to bind to
    logger.info(f"Starting Flow Dashboard server on {host}:{port}")
    logger.info(f"Dashboard will be available at: http://{host}:{port}")
    
    try:
        # Run the server
        uvicorn.run(
            "app:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {port} is already in use!")
            logger.error(f"To fix this, either:")
            logger.error(f"  1. Stop the process using port {port}")
            logger.error(f"  2. Use a different port by setting PORT environment variable")
            logger.error(f"     Example: PORT=8082 python app.py")
            
            # Try to find what's using the port
            import subprocess
            try:
                result = subprocess.run(['lsof', '-i', f':{port}'], 
                                      capture_output=True, text=True)
                if result.stdout:
                    logger.error(f"Process using port {port}:")
                    logger.error(result.stdout)
            except Exception:
                pass
        else:
            logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error starting server: {e}")
        sys.exit(1)
