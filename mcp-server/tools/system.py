#!/usr/bin/env python3
"""
System Tool for Flow MCP Server

Provides system information and control functionality.
"""

import asyncio
import json
import logging
import subprocess
import signal
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def now() -> datetime:
    """Get current timezone-aware datetime in local timezone."""
    return datetime.now().astimezone()


class SystemTool:
    """Tool for system information and control."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.refinery_path = workspace_root / "refinery"
        self.dashboard_path = workspace_root / "dashboard"
        
        # Process tracking
        self.chroma_process: Optional[subprocess.Popen] = None
        self.flow_runner_process: Optional[subprocess.Popen] = None
    
    async def what_can_i_do(self) -> Dict[str, Any]:
        """Get information about Flow capabilities."""
        try:
            # Check system status
            chroma_running = await self._is_chroma_running()
            dashboard_running = await self._is_dashboard_running()
            
            return {
                "flow_capabilities": [
                    "Search for anything that you worked on while using Flow. This includes URLs, document titles, Jira tickets, etc.",
                    "Search OCR data from screenshots with optional date ranges",
                    "Start and stop screenshot recording with ChromaDB integration",
                    "Get statistics about captured data and system performance",
                    "Generate activity timeline graphs showing when Flow was actively capturing screens",
                    "Get time-range summaries with sampled OCR data (up to 100 evenly distributed results)",
                    "Control Flow system processes (ChromaDB server and screen capture)"
                ],
                "description": "Flow is a screen activity tracking and analysis tool that helps you search and analyze your work patterns through OCR data from automatic screenshots.",
                "available_tools": [
                    "search-screenshots - Search through captured OCR text data",
                    "what-can-i-do - Get information about Flow capabilities",
                    "get-stats - Get detailed system and data statistics", 
                    "activity-graph - Generate activity timeline visualizations",
                    "time-range-summary - Get sampled data over specific time ranges",
                    "start-flow - Start the Flow capture system",
                    "stop-flow - Stop the Flow capture system"
                ],
                "current_status": {
                    "chroma_db_running": chroma_running,
                    "dashboard_running": dashboard_running,
                    "workspace_root": str(self.workspace_root),
                    "ocr_data_directory": str(self.refinery_path / "data" / "ocr"),
                    "mcp_server": "python_standalone"
                },
                "system_info": {
                    "version": "2.0.0",
                    "server_type": "Python MCP Server",
                    "architecture": "Standalone",
                    "data_source": "Local OCR JSON files",
                    "search_method": "Text-based with ChromaDB integration"
                },
                "usage_examples": [
                    "Search for 'email' to find screenshots containing email content",
                    "Use date ranges like start_date='2024-01-01' to filter results",
                    "Generate activity graphs to see your work patterns over time",
                    "Get system stats to understand your data collection"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "error": str(e),
                "flow_capabilities": [],
                "current_status": {"error": "Unable to determine system status"}
            }
    
    async def start_flow(self) -> Dict[str, Any]:
        """Start the Flow system (ChromaDB + screen capture)."""
        try:
            logger.info("Starting Flow system...")
            
            # Check if already running
            chroma_running = await self._is_chroma_running()
            
            results = {
                "operation": "start_flow",
                "timestamp": now().isoformat(),
                "steps": [],
                "final_status": {}
            }
            
            # Start ChromaDB if not running
            if not chroma_running:
                chroma_result = await self._start_chroma_db()
                results["steps"].append({
                    "step": "start_chromadb",
                    "success": chroma_result["success"],
                    "message": chroma_result["message"]
                })
                
                if not chroma_result["success"]:
                    results["success"] = False
                    results["message"] = f"Failed to start ChromaDB: {chroma_result['message']}"
                    return results
            else:
                results["steps"].append({
                    "step": "start_chromadb",
                    "success": True,
                    "message": "ChromaDB already running"
                })
            
            # Wait a moment for ChromaDB to be ready
            await asyncio.sleep(2)
            
            # Start screen capture
            capture_result = await self._start_screen_capture()
            results["steps"].append({
                "step": "start_screen_capture",
                "success": capture_result["success"],
                "message": capture_result["message"]
            })
            
            # Determine overall success
            overall_success = all(step["success"] for step in results["steps"])
            results["success"] = overall_success
            
            if overall_success:
                results["message"] = "Flow system started successfully"
            else:
                failed_steps = [step["step"] for step in results["steps"] if not step["success"]]
                results["message"] = f"Flow system start failed at: {', '.join(failed_steps)}"
            
            # Get final status
            results["final_status"] = {
                "chroma_db_running": await self._is_chroma_running(),
                "screen_capture_running": self.flow_runner_process is not None,
                "overall_running": overall_success
            }
            
            logger.info(f"Flow start result: {results['message']}")
            return results
            
        except Exception as e:
            logger.error(f"Error starting Flow system: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "start_flow",
                "message": f"Failed to start Flow system: {str(e)}"
            }
    
    async def stop_flow(self) -> Dict[str, Any]:
        """Stop the Flow system."""
        try:
            logger.info("Stopping Flow system...")
            
            results = {
                "operation": "stop_flow",
                "timestamp": now().isoformat(),
                "steps": [],
                "final_status": {}
            }
            
            # Stop screen capture
            capture_result = await self._stop_screen_capture()
            results["steps"].append({
                "step": "stop_screen_capture",
                "success": capture_result["success"],
                "message": capture_result["message"]
            })
            
            # Stop ChromaDB
            chroma_result = await self._stop_chroma_db()
            results["steps"].append({
                "step": "stop_chromadb",
                "success": chroma_result["success"],
                "message": chroma_result["message"]
            })
            
            # Determine overall success
            overall_success = all(step["success"] for step in results["steps"])
            results["success"] = overall_success
            
            if overall_success:
                results["message"] = "Flow system stopped successfully"
            else:
                failed_steps = [step["step"] for step in results["steps"] if not step["success"]]
                results["message"] = f"Flow system stop had issues: {', '.join(failed_steps)}"
            
            # Get final status
            results["final_status"] = {
                "chroma_db_running": await self._is_chroma_running(),
                "screen_capture_running": self.flow_runner_process is not None,
                "overall_running": False
            }
            
            logger.info(f"Flow stop result: {results['message']}")
            return results
            
        except Exception as e:
            logger.error(f"Error stopping Flow system: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": "stop_flow",
                "message": f"Failed to stop Flow system: {str(e)}"
            }
    
    async def _is_chroma_running(self) -> bool:
        """Check if ChromaDB server is running."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/v1/heartbeat", timeout=2.0)
                return response.status_code == 200
        except Exception:
            return False
    
    async def _is_dashboard_running(self) -> bool:
        """Check if Flow dashboard is running."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8080/health", timeout=2.0)
                return response.status_code == 200
        except Exception:
            return False
    
    async def _start_chroma_db(self) -> Dict[str, Any]:
        """Start ChromaDB server."""
        try:
            if self.chroma_process and self.chroma_process.poll() is None:
                return {"success": True, "message": "ChromaDB already running"}
            
            # Check if virtual environment exists
            venv_python = self.refinery_path / ".venv" / "bin" / "python"
            if not venv_python.exists():
                return {
                    "success": False,
                    "message": f"Python virtual environment not found at {venv_python}"
                }
            
            # Start ChromaDB process
            cmd = [str(venv_python), "-m", "chromadb.cli.cli", "run", "--host", "localhost", "--port", "8000"]
            
            self.chroma_process = subprocess.Popen(
                cmd,
                cwd=str(self.refinery_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for ChromaDB to start
            for i in range(10):
                if await self._is_chroma_running():
                    return {"success": True, "message": "ChromaDB server started successfully"}
                await asyncio.sleep(1)
            
            # If we get here, ChromaDB didn't start properly
            if self.chroma_process:
                self.chroma_process.terminate()
                self.chroma_process = None
            
            return {"success": False, "message": "ChromaDB server failed to start within timeout"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to start ChromaDB: {str(e)}"}
    
    async def _stop_chroma_db(self) -> Dict[str, Any]:
        """Stop ChromaDB server."""
        try:
            if not self.chroma_process:
                return {"success": True, "message": "ChromaDB not running"}
            
            # Terminate the process group
            try:
                os.killpg(os.getpgid(self.chroma_process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            
            # Wait for process to terminate
            try:
                self.chroma_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self.chroma_process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            
            self.chroma_process = None
            return {"success": True, "message": "ChromaDB server stopped"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to stop ChromaDB: {str(e)}"}
    
    async def _start_screen_capture(self) -> Dict[str, Any]:
        """Start screen capture process."""
        try:
            if self.flow_runner_process and self.flow_runner_process.poll() is None:
                return {"success": True, "message": "Screen capture already running"}
            
            # Check paths
            venv_python = self.refinery_path / ".venv" / "bin" / "python"
            run_py = self.refinery_path / "run.py"
            
            if not venv_python.exists():
                return {"success": False, "message": f"Python virtual environment not found at {venv_python}"}
            
            if not run_py.exists():
                return {"success": False, "message": f"run.py not found at {run_py}"}
            
            # Start screen capture process
            cmd = [str(venv_python), "run.py"]
            
            self.flow_runner_process = subprocess.Popen(
                cmd,
                cwd=str(self.refinery_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Give it a moment to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if self.flow_runner_process.poll() is None:
                return {"success": True, "message": "Screen capture started successfully"}
            else:
                # Process terminated immediately
                stdout, stderr = self.flow_runner_process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.flow_runner_process = None
                return {"success": False, "message": f"Screen capture failed to start: {error_msg}"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to start screen capture: {str(e)}"}
    
    async def _stop_screen_capture(self) -> Dict[str, Any]:
        """Stop screen capture process."""
        try:
            if not self.flow_runner_process:
                return {"success": True, "message": "Screen capture not running"}
            
            # Terminate the process group
            try:
                os.killpg(os.getpgid(self.flow_runner_process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            
            # Wait for process to terminate
            try:
                self.flow_runner_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(self.flow_runner_process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            
            self.flow_runner_process = None
            return {"success": True, "message": "Screen capture stopped"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to stop screen capture: {str(e)}"}
