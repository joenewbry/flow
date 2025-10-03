#!/usr/bin/env python3
"""
Process Manager for Flow Dashboard

Manages ChromaDB server and screen capture processes.
Provides start/stop functionality and status monitoring.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

import psutil

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages Flow system processes (ChromaDB server and screen capture)."""
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        self.refinery_path = self.workspace_root / "refinery"
        self.state_file = self.workspace_root / "dashboard" / ".flow-state.json"
        
        # Process references
        self.chroma_process: Optional[subprocess.Popen] = None
        self.screen_capture_process: Optional[subprocess.Popen] = None
        
        # State tracking
        self.is_running = False
        self.chroma_running = False
        self.screen_capture_running = False
        
        # Process monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        
    async def load_state(self):
        """Load previous state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                self.is_running = state.get('is_running', False)
                self.chroma_running = state.get('chroma_running', False)
                self.screen_capture_running = state.get('screen_capture_running', False)
                
                logger.info(f"Loaded state: running={self.is_running}, chroma={self.chroma_running}, capture={self.screen_capture_running}")
                
                # Try to restore processes if they were running
                if self.is_running:
                    await self._attempt_restore()
            else:
                logger.info("No previous state found, starting fresh")
                
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            # Reset to safe state
            self.is_running = False
            self.chroma_running = False
            self.screen_capture_running = False
    
    async def save_state(self):
        """Save current state to file."""
        try:
            state = {
                'is_running': self.is_running,
                'chroma_running': self.chroma_running,
                'screen_capture_running': self.screen_capture_running,
                'last_updated': time.time()
            }
            
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    async def _attempt_restore(self):
        """Attempt to restore processes from previous state."""
        try:
            logger.info("Attempting to restore previous process state...")
            
            # Check if processes are actually running
            if self.chroma_running and not await self._is_chroma_healthy():
                logger.warning("ChromaDB was marked as running but is not healthy")
                self.chroma_running = False
            
            if self.screen_capture_running and not await self._is_screen_capture_healthy():
                logger.warning("Screen capture was marked as running but is not healthy")
                self.screen_capture_running = False
            
            # Update overall running state
            self.is_running = self.chroma_running and self.screen_capture_running
            
            if self.is_running:
                logger.info("Successfully restored process state")
                await self._start_monitoring()
            else:
                logger.info("Could not restore all processes, system marked as stopped")
                await self.save_state()
                
        except Exception as e:
            logger.error(f"Error during state restoration: {e}")
            self.is_running = False
            self.chroma_running = False
            self.screen_capture_running = False
            await self.save_state()
    
    async def start_system(self) -> Dict[str, Any]:
        """Start the complete Flow system."""
        try:
            if self.is_running:
                return {
                    "success": True,
                    "message": "System is already running",
                    "status": await self.get_status()
                }
            
            logger.info("Starting Flow system...")
            
            # Start ChromaDB first
            chroma_result = await self.start_chroma()
            if not chroma_result["success"]:
                return chroma_result
            
            # Wait a moment for ChromaDB to be ready
            await asyncio.sleep(2)
            
            # Start screen capture
            capture_result = await self.start_screen_capture()
            if not capture_result["success"]:
                # If screen capture fails, stop ChromaDB
                await self.stop_chroma()
                return capture_result
            
            self.is_running = True
            await self.save_state()
            await self._start_monitoring()
            
            logger.info("Flow system started successfully")
            
            return {
                "success": True,
                "message": "Flow system started successfully",
                "status": await self.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            return {
                "success": False,
                "message": f"Failed to start system: {str(e)}",
                "status": await self.get_status()
            }
    
    async def stop_system(self) -> Dict[str, Any]:
        """Stop the complete Flow system."""
        try:
            if not self.is_running:
                return {
                    "success": True,
                    "message": "System is already stopped",
                    "status": await self.get_status()
                }
            
            logger.info("Stopping Flow system...")
            
            # Stop monitoring
            if self._monitoring_task:
                self._monitoring_task.cancel()
                self._monitoring_task = None
            
            # Stop screen capture first
            await self.stop_screen_capture()
            
            # Stop ChromaDB
            await self.stop_chroma()
            
            self.is_running = False
            await self.save_state()
            
            logger.info("Flow system stopped successfully")
            
            return {
                "success": True,
                "message": "Flow system stopped successfully",
                "status": await self.get_status()
            }
            
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
            return {
                "success": False,
                "message": f"Failed to stop system: {str(e)}",
                "status": await self.get_status()
            }
    
    async def start_chroma(self) -> Dict[str, Any]:
        """Start ChromaDB server."""
        try:
            if self.chroma_running:
                return {"success": True, "message": "ChromaDB is already running"}
            
            logger.info("Starting ChromaDB server...")
            
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
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait for ChromaDB to start
            for i in range(10):  # Wait up to 10 seconds
                if await self._is_chroma_healthy():
                    self.chroma_running = True
                    await self.save_state()
                    logger.info("ChromaDB server started successfully")
                    return {"success": True, "message": "ChromaDB server started"}
                await asyncio.sleep(1)
            
            # If we get here, ChromaDB didn't start properly
            if self.chroma_process:
                self.chroma_process.terminate()
                self.chroma_process = None
            
            return {
                "success": False,
                "message": "ChromaDB server failed to start within timeout"
            }
            
        except Exception as e:
            logger.error(f"Error starting ChromaDB: {e}")
            return {"success": False, "message": f"Failed to start ChromaDB: {str(e)}"}
    
    async def stop_chroma(self) -> Dict[str, Any]:
        """Stop ChromaDB server."""
        try:
            if not self.chroma_running:
                return {"success": True, "message": "ChromaDB is already stopped"}
            
            logger.info("Stopping ChromaDB server...")
            
            if self.chroma_process:
                # Terminate the process group
                try:
                    os.killpg(os.getpgid(self.chroma_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass  # Process already terminated
                
                # Wait for process to terminate
                try:
                    self.chroma_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    try:
                        os.killpg(os.getpgid(self.chroma_process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                
                self.chroma_process = None
            
            self.chroma_running = False
            await self.save_state()
            
            logger.info("ChromaDB server stopped")
            return {"success": True, "message": "ChromaDB server stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping ChromaDB: {e}")
            return {"success": False, "message": f"Failed to stop ChromaDB: {str(e)}"}
    
    async def start_screen_capture(self) -> Dict[str, Any]:
        """Start screen capture process."""
        try:
            if self.screen_capture_running:
                return {"success": True, "message": "Screen capture is already running"}
            
            logger.info("Starting screen capture process...")
            
            # Check if virtual environment and run.py exist
            venv_python = self.refinery_path / ".venv" / "bin" / "python"
            run_py = self.refinery_path / "run.py"
            
            if not venv_python.exists():
                return {
                    "success": False,
                    "message": f"Python virtual environment not found at {venv_python}"
                }
            
            if not run_py.exists():
                return {
                    "success": False,
                    "message": f"run.py not found at {run_py}"
                }
            
            # Start screen capture process
            cmd = [str(venv_python), "run.py"]
            
            self.screen_capture_process = subprocess.Popen(
                cmd,
                cwd=str(self.refinery_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Give it a moment to start
            await asyncio.sleep(2)
            
            # Check if process is still running
            if self.screen_capture_process.poll() is None:
                self.screen_capture_running = True
                await self.save_state()
                logger.info("Screen capture process started successfully")
                return {"success": True, "message": "Screen capture started"}
            else:
                # Process terminated immediately, check error
                stdout, stderr = self.screen_capture_process.communicate()
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.screen_capture_process = None
                
                return {
                    "success": False,
                    "message": f"Screen capture process failed to start: {error_msg}"
                }
            
        except Exception as e:
            logger.error(f"Error starting screen capture: {e}")
            return {"success": False, "message": f"Failed to start screen capture: {str(e)}"}
    
    async def stop_screen_capture(self) -> Dict[str, Any]:
        """Stop screen capture process."""
        try:
            if not self.screen_capture_running:
                return {"success": True, "message": "Screen capture is already stopped"}
            
            logger.info("Stopping screen capture process...")
            
            if self.screen_capture_process:
                # Terminate the process group
                try:
                    os.killpg(os.getpgid(self.screen_capture_process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass  # Process already terminated
                
                # Wait for process to terminate
                try:
                    self.screen_capture_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    try:
                        os.killpg(os.getpgid(self.screen_capture_process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                
                self.screen_capture_process = None
            
            self.screen_capture_running = False
            await self.save_state()
            
            logger.info("Screen capture process stopped")
            return {"success": True, "message": "Screen capture stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping screen capture: {e}")
            return {"success": False, "message": f"Failed to stop screen capture: {str(e)}"}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        # Check actual process health (this now includes detection of existing processes)
        chroma_healthy = await self._is_chroma_healthy()
        capture_healthy = await self._is_screen_capture_healthy()
        
        # Also check for existing processes if we don't have tracked ones
        if not self.chroma_running:
            chroma_detected = await self._detect_existing_chroma()
            if chroma_detected:
                self.chroma_running = True
                logger.info("Detected existing ChromaDB process, updating status")
        
        if not self.screen_capture_running:
            capture_detected = await self._detect_existing_screen_capture()
            if capture_detected:
                self.screen_capture_running = True
                logger.info("Detected existing screen capture process, updating status")
        
        # Update our state based on actual health
        if self.chroma_running and not chroma_healthy:
            self.chroma_running = False
            self.chroma_process = None
        
        if self.screen_capture_running and not capture_healthy:
            self.screen_capture_running = False
            self.screen_capture_process = None
        
        # Update overall running state
        was_running = self.is_running
        self.is_running = self.chroma_running and self.screen_capture_running
        
        # Save state if it changed
        if was_running != self.is_running:
            await self.save_state()
        
        return {
            "overall_status": "running" if self.is_running else "stopped",
            "chroma_db": {
                "running": self.chroma_running,
                "healthy": chroma_healthy,
                "pid": self.chroma_process.pid if self.chroma_process else None
            },
            "screen_capture": {
                "running": self.screen_capture_running,
                "healthy": capture_healthy,
                "pid": self.screen_capture_process.pid if self.screen_capture_process else None
            },
            "last_updated": time.time()
        }
    
    async def _is_chroma_healthy(self) -> bool:
        """Check if ChromaDB server is healthy."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Try v2 API first (newer ChromaDB versions)
                try:
                    response = await client.get("http://localhost:8000/api/v2/heartbeat", timeout=2.0)
                    if response.status_code == 200:
                        return True
                except Exception:
                    pass
                
                # Fallback to v1 API for older versions
                try:
                    response = await client.get("http://localhost:8000/api/v1/heartbeat", timeout=2.0)
                    return response.status_code == 200
                except Exception:
                    pass
                
                # Also try root endpoint as a basic connectivity test
                try:
                    response = await client.get("http://localhost:8000/", timeout=2.0)
                    return response.status_code == 200
                except Exception:
                    pass
                    
                return False
        except Exception:
            return False
    
    async def _is_screen_capture_healthy(self) -> bool:
        """Check if screen capture process is healthy."""
        # First check if we have a tracked process
        if self.screen_capture_process:
            try:
                # Check if process is still running
                if self.screen_capture_process.poll() is not None:
                    self.screen_capture_process = None
                    return False
                
                # Check if process is responsive (basic check)
                process = psutil.Process(self.screen_capture_process.pid)
                return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.screen_capture_process = None
                return False
        
        # If no tracked process, look for existing screen capture processes
        return await self._detect_existing_screen_capture()
    
    async def _detect_existing_chroma(self) -> bool:
        """Detect if ChromaDB is running independently."""
        try:
            # First check if it's healthy via HTTP
            if await self._is_chroma_healthy():
                # Look for the process
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info['cmdline']
                        if cmdline and any('chroma' in str(arg) and 'run' in str(arg) for arg in cmdline):
                            logger.info(f"Detected existing ChromaDB process: PID {proc.info['pid']}")
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                return True  # HTTP healthy but can't find process - still consider it running
            return False
        except Exception as e:
            logger.debug(f"Error detecting existing ChromaDB: {e}")
            return False
    
    async def _detect_existing_screen_capture(self) -> bool:
        """Detect if screen capture is running independently."""
        try:
            # Look for python processes running run.py in the refinery directory
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    cmdline = proc.info['cmdline']
                    if (cmdline and 
                        'python' in proc.info['name'].lower() and 
                        any('run.py' in str(arg) for arg in cmdline)):
                        
                        # Check if it's running in the refinery directory
                        try:
                            cwd = proc.cwd()
                            if 'refinery' in cwd:
                                logger.info(f"Detected existing screen capture process: PID {proc.info['pid']}")
                                return True
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            # Can't check cwd, but cmdline matches
                            logger.info(f"Detected likely screen capture process: PID {proc.info['pid']}")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.debug(f"Error detecting existing screen capture: {e}")
            return False
    
    async def _start_monitoring(self):
        """Start background monitoring of processes."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        self._monitoring_task = asyncio.create_task(self._monitor_processes())
    
    async def _monitor_processes(self):
        """Background task to monitor process health."""
        try:
            while self.is_running:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Check process health
                chroma_healthy = await self._is_chroma_healthy()
                capture_healthy = await self._is_screen_capture_healthy()
                
                # Log any issues
                if self.chroma_running and not chroma_healthy:
                    logger.warning("ChromaDB process appears to be unhealthy")
                
                if self.screen_capture_running and not capture_healthy:
                    logger.warning("Screen capture process appears to be unhealthy")
                
        except asyncio.CancelledError:
            logger.info("Process monitoring stopped")
        except Exception as e:
            logger.error(f"Error in process monitoring: {e}")
    
    async def cleanup(self):
        """Clean up all processes and resources."""
        logger.info("Cleaning up processes...")
        
        # Stop monitoring
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
        
        # Stop all processes
        await self.stop_screen_capture()
        await self.stop_chroma()
        
        logger.info("Process cleanup complete")
