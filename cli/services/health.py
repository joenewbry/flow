"""Health check utilities for Memex CLI."""

import os
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime

from cli.config import get_settings


@dataclass
class DependencyCheck:
    """Result of a dependency check."""
    name: str
    installed: bool
    version: Optional[str] = None
    path: Optional[str] = None


@dataclass
class ServiceCheck:
    """Result of a service check."""
    name: str
    running: bool
    details: str = ""
    pid: Optional[int] = None


@dataclass
class PermissionCheck:
    """Result of a permission check."""
    name: str
    granted: bool
    details: str = ""


class HealthService:
    """Service for checking system health."""

    def __init__(self):
        self.settings = get_settings()

    def check_python(self) -> DependencyCheck:
        """Check Python installation."""
        try:
            result = subprocess.run(
                ["python3", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.strip().replace("Python ", "")
            path = shutil.which("python3")
            return DependencyCheck("Python", True, version, path)
        except Exception:
            return DependencyCheck("Python", False)

    def check_tesseract(self) -> DependencyCheck:
        """Check Tesseract OCR installation."""
        try:
            result = subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            # First line contains version
            version = result.stdout.split("\n")[0].replace("tesseract ", "")
            path = shutil.which("tesseract")
            return DependencyCheck("Tesseract", True, version, path)
        except Exception:
            return DependencyCheck("Tesseract", False)

    def check_chroma_package(self) -> DependencyCheck:
        """Check if chromadb package is installed."""
        try:
            result = subprocess.run(
                ["pip", "show", "chromadb"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        version = line.split(":")[1].strip()
                        return DependencyCheck("ChromaDB", True, f"pip: {version}")
            return DependencyCheck("ChromaDB", False)
        except Exception:
            return DependencyCheck("ChromaDB", False)

    def check_ngrok(self) -> DependencyCheck:
        """Check if ngrok is installed (optional)."""
        try:
            path = shutil.which("ngrok")
            if path:
                result = subprocess.run(
                    ["ngrok", "version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                version = result.stdout.strip()
                return DependencyCheck("NGROK", True, version, path)
            return DependencyCheck("NGROK", False, None, "Not found (optional)")
        except Exception:
            return DependencyCheck("NGROK", False, None, "Not found (optional)")

    def check_chroma_server(self) -> ServiceCheck:
        """Check if ChromaDB server is running."""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.settings.chroma_host, self.settings.chroma_port))
            sock.close()
            if result == 0:
                return ServiceCheck(
                    "ChromaDB Server",
                    True,
                    f"Running on {self.settings.chroma_host}:{self.settings.chroma_port}",
                )
            return ServiceCheck("ChromaDB Server", False, "Not running")
        except Exception as e:
            return ServiceCheck("ChromaDB Server", False, str(e))

    def check_capture_process(self) -> ServiceCheck:
        """Check if the capture process is running."""
        try:
            # Look for run.py process
            result = subprocess.run(
                ["pgrep", "-f", "refinery/run.py"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                pid = int(result.stdout.strip().split("\n")[0])
                return ServiceCheck("Capture Process", True, f"pid {pid}", pid)
            return ServiceCheck("Capture Process", False, "NOT RUNNING")
        except Exception:
            return ServiceCheck("Capture Process", False, "Unable to check")

    def check_screen_recording_permission(self) -> PermissionCheck:
        """Check macOS screen recording permission."""
        import platform
        if platform.system() != "Darwin":
            return PermissionCheck("Screen Recording", True, "N/A (not macOS)")

        # Try to import Quartz - if we can capture, permission is granted
        try:
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            if windows is not None:
                return PermissionCheck("Screen Recording", True, "Granted")
            return PermissionCheck("Screen Recording", False, "May need permission")
        except ImportError:
            return PermissionCheck("Screen Recording", True, "Unable to verify (Quartz not available)")
        except Exception:
            return PermissionCheck("Screen Recording", False, "Check System Preferences")

    def check_data_directory(self) -> PermissionCheck:
        """Check if data directory is writable."""
        try:
            if self.settings.ocr_data_path.exists():
                # Try to create a test file
                test_file = self.settings.ocr_data_path / ".write_test"
                test_file.touch()
                test_file.unlink()
                return PermissionCheck("Data Directory", True, "Writable")
            else:
                # Directory doesn't exist yet
                return PermissionCheck("Data Directory", True, "Will be created")
        except Exception as e:
            return PermissionCheck("Data Directory", False, str(e))

    def get_ocr_file_count(self) -> int:
        """Get the number of OCR files."""
        if not self.settings.ocr_data_path.exists():
            return 0
        return len(list(self.settings.ocr_data_path.glob("*.json")))

    def get_today_capture_count(self) -> int:
        """Get the number of captures from today."""
        if not self.settings.ocr_data_path.exists():
            return 0

        today = datetime.now().strftime("%Y-%m-%d")
        count = 0
        for f in self.settings.ocr_data_path.glob("*.json"):
            if f.name.startswith(today):
                count += 1
        return count

    def get_latest_capture_time(self) -> Optional[datetime]:
        """Get the timestamp of the most recent capture."""
        if not self.settings.ocr_data_path.exists():
            return None

        files = list(self.settings.ocr_data_path.glob("*.json"))
        if not files:
            return None

        latest = max(files, key=lambda f: f.stat().st_mtime)
        return datetime.fromtimestamp(latest.stat().st_mtime)

    def get_storage_size(self) -> int:
        """Get total storage size in bytes."""
        total = 0
        if self.settings.ocr_data_path.exists():
            for f in self.settings.ocr_data_path.glob("*.json"):
                total += f.stat().st_size
        if self.settings.chroma_path.exists():
            for f in self.settings.chroma_path.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
        return total

    def get_unique_screens(self) -> list[str]:
        """Get list of unique screen names from OCR files."""
        screens = set()
        if not self.settings.ocr_data_path.exists():
            return []

        # Sample last 100 files for efficiency
        files = sorted(
            self.settings.ocr_data_path.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[:100]

        for f in files:
            # Filename format: timestamp_screen_name.json
            parts = f.stem.rsplit("_", 1)
            if len(parts) == 2:
                screens.add(parts[1])

        return sorted(screens)
