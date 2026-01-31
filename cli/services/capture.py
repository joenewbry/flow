"""Capture service for managing the screen capture process."""

import os
import signal
import subprocess
from pathlib import Path
from typing import Optional

from cli.config import get_settings


class CaptureService:
    """Service for managing the capture daemon."""

    def __init__(self):
        self.settings = get_settings()
        self.run_script = self.settings.refinery_path / "run.py"
        self.venv_python = self.settings.refinery_path / ".venv" / "bin" / "python"

    def is_running(self) -> tuple[bool, Optional[int]]:
        """Check if capture process is running. Returns (running, pid)."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "refinery/run.py"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                pid = int(result.stdout.strip().split("\n")[0])
                return True, pid
            return False, None
        except Exception:
            return False, None

    def start(self, foreground: bool = False) -> tuple[bool, str]:
        """Start the capture process."""
        running, pid = self.is_running()
        if running:
            return False, f"Already running (pid {pid})"

        if not self.run_script.exists():
            return False, f"Run script not found: {self.run_script}"

        python_path = str(self.venv_python) if self.venv_python.exists() else "python3"

        try:
            if foreground:
                # Run in foreground (blocking)
                subprocess.run(
                    [python_path, str(self.run_script)],
                    cwd=str(self.settings.refinery_path),
                )
                return True, "Stopped"
            else:
                # Run in background
                process = subprocess.Popen(
                    [python_path, str(self.run_script)],
                    cwd=str(self.settings.refinery_path),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True, f"Started (pid {process.pid})"
        except Exception as e:
            return False, str(e)

    def stop(self) -> tuple[bool, str]:
        """Stop the capture process."""
        running, pid = self.is_running()
        if not running:
            return False, "Not running"

        try:
            os.kill(pid, signal.SIGTERM)
            return True, f"Stopped (pid {pid})"
        except ProcessLookupError:
            return False, "Process not found"
        except PermissionError:
            return False, "Permission denied"
        except Exception as e:
            return False, str(e)

    def get_venv_path(self) -> Optional[Path]:
        """Get the refinery virtual environment path."""
        if self.venv_python.exists():
            return self.venv_python.parent.parent
        return None
