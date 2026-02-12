"""Audio recording service for managing the memex-recorder process."""

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional

from cli.config import get_settings


class AudioService:
    """Service for managing the audio recorder daemon."""

    def __init__(self):
        self.settings = get_settings()
        self.recorder_binary = self.settings.project_root / "recorder" / ".build" / "release" / "memex-recorder"
        self.output_dir = self.settings.audio_data_path

    def is_built(self) -> bool:
        """Check if the Swift recorder binary has been compiled."""
        return self.recorder_binary.exists()

    def is_running(self) -> tuple[bool, Optional[int]]:
        """Check if the recorder process is running. Returns (running, pid)."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "memex-recorder"],
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

    def start(self) -> tuple[bool, str]:
        """Start the audio recorder process."""
        running, pid = self.is_running()
        if running:
            return False, f"Already running (pid {pid})"

        if not self.is_built():
            return False, f"Recorder not built. Run: cd recorder && swift build -c release"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            process = subprocess.Popen(
                [
                    str(self.recorder_binary),
                    "--output-dir", str(self.output_dir),
                    "--rotation-interval", str(self.settings.audio_rotation_interval),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True, f"Started (pid {process.pid})"
        except Exception as e:
            return False, str(e)

    def stop(self) -> tuple[bool, str]:
        """Stop the audio recorder. Uses SIGTERM first, then SIGKILL if needed."""
        running, pid = self.is_running()
        if not running:
            return False, "Not running"

        def process_exists(p: int) -> bool:
            try:
                os.kill(p, 0)
                return True
            except ProcessLookupError:
                return False
            except PermissionError:
                return True

        try:
            # Kill whole process group
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
            except (ProcessLookupError, OSError):
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    return True, f"Stopped (pid {pid})"

            for _ in range(10):
                time.sleep(0.5)
                if not process_exists(pid):
                    return True, f"Stopped (pid {pid})"

            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
            return True, f"Stopped (pid {pid})"
        except ProcessLookupError:
            return True, f"Stopped (pid {pid})"
        except PermissionError:
            return False, "Permission denied"
        except Exception as e:
            return False, str(e)

    def get_recording_count(self) -> int:
        """Get the number of audio recording files."""
        count = 0
        if self.output_dir.exists():
            for subdir in ["system", "mic"]:
                d = self.output_dir / subdir
                if d.exists():
                    count += sum(1 for f in d.iterdir() if f.suffix in (".m4a", ".wav"))
        return count

    def get_total_size(self) -> int:
        """Get total size of audio recordings in bytes."""
        total = 0
        if self.output_dir.exists():
            for subdir in ["system", "mic"]:
                d = self.output_dir / subdir
                if d.exists():
                    total += sum(f.stat().st_size for f in d.iterdir() if f.suffix in (".m4a", ".wav"))
        return total
