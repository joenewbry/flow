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
from dashboard.lib.chat_manager import ChatManager
from dashboard.api.ocr_data import router as ocr_router
from dashboard.api.logs import router as logs_router

# Configure logging with file and console handlers
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler
file_handler = logging.FileHandler(log_dir / "dashboard.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

# Global instances
process_manager: Optional[ProcessManager] = None
data_handler: Optional[DataHandler] = None
chat_manager: Optional[ChatManager] = None

# WebSocket connections for real-time updates
websocket_connections: list[WebSocket] = []


async def broadcast_to_websockets(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients."""
    if not websocket_connections:
        return
    
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for websocket in disconnected:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global process_manager, data_handler, chat_manager
    
    # Startup
    logger.info("Starting Flow Dashboard...")
    
    # Initialize components
    process_manager = ProcessManager()
    data_handler = DataHandler()
    
    # Initialize chat manager with broadcast callback
    try:
        chat_manager = ChatManager(websocket_broadcast_callback=broadcast_to_websockets)
        logger.info("Chat manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chat manager: {e}")
        logger.warning("Chat functionality will be disabled")
        chat_manager = None
    
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
app.include_router(logs_router)


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


async def broadcast_log(log_entry: dict):
    """Broadcast a log entry to all connected WebSocket clients."""
    if not websocket_connections:
        return
        
    try:
        message = {"type": "log_message", "data": log_entry}
        
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
        logger.error(f"Error broadcasting log: {e}")


async def broadcast_countdown(countdown_data: dict):
    """Broadcast countdown update to all connected WebSocket clients."""
    if not websocket_connections:
        return
        
    try:
        message = {"type": "countdown_update", "data": countdown_data}
        
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
        logger.error(f"Error broadcasting countdown: {e}")


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


@app.post("/api/broadcast-countdown")
async def broadcast_countdown_update(countdown_data: Dict[str, Any]):
    """Receive countdown update from refinery and broadcast to clients."""
    try:
        await broadcast_countdown(countdown_data)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error broadcasting countdown: {e}")
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
            # Look for the MCP server process - check for multiple possible process names
            mcp_processes = ['Flow MCP Server', 'mcp-server/server.py', 'mcp-server', 'start.sh']
            for proc_name in mcp_processes:
                result = subprocess.run(['pgrep', '-f', proc_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    mcp_status["running"] = True
                    # Count the number of PIDs found
                    pids = result.stdout.strip().split('\n')
                    mcp_status["clients"] = len(pids)
                    mcp_status["last_request"] = None  # Would need to track this separately
                    break
                
        except Exception as e:
            logger.error(f"Error checking MCP server process: {e}")
        
        return JSONResponse(content=mcp_status)
        
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/send")
async def send_chat_message(request: Request):
    """Send a chat message."""
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat service not available")
        
        data = await request.json()
        message_id = data.get("message_id")
        content = data.get("content")
        
        if not message_id or not content:
            raise HTTPException(status_code=400, detail="message_id and content are required")
        
        # Add message to queue
        await chat_manager.add_message(message_id, content)
        
        return JSONResponse(content={"status": "queued", "message_id": message_id})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/clear-queue")
async def clear_chat_queue():
    """Clear the chat message queue."""
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat service not available")
        
        await chat_manager.clear_queue()
        return JSONResponse(content={"status": "success", "message": "Queue cleared"})
        
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/clear-conversation")
async def clear_chat_conversation():
    """Clear the conversation history."""
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat service not available")
        
        await chat_manager.clear_conversation()
        return JSONResponse(content={"status": "success", "message": "Conversation cleared"})
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/queue-status")
async def get_chat_queue_status():
    """Get current queue status."""
    try:
        if not chat_manager:
            raise HTTPException(status_code=503, detail="Chat service not available")
        
        status = chat_manager.get_queue_status()
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
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
