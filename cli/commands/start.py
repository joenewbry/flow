"""Start command - start capture daemon."""

import subprocess
import time
import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from cli.display.components import print_header, print_success, print_error
from cli.display.colors import COLORS
from cli.services.capture import CaptureService
from cli.services.health import HealthService
from cli.config import get_settings

console = Console()


def start(
    foreground: bool = typer.Option(
        False, "--foreground", "-f", help="Run in foreground with live output"
    ),
    no_chroma: bool = typer.Option(
        False, "--no-chroma", help="Don't auto-start ChromaDB"
    ),
):
    """Start the capture daemon."""
    print_header("Starting")

    capture = CaptureService()
    health = HealthService()
    settings = get_settings()

    # Check if already running
    running, pid = capture.is_running()
    if running:
        console.print(f"  [{COLORS['warning']}]![/] Already running (pid {pid})")
        console.print()
        return

    # Check ChromaDB
    chroma_check = health.check_chroma_server()
    if not chroma_check.running and not no_chroma:
        console.print(f"  [{COLORS['muted']}]○[/] ChromaDB not running, starting...")

        # Try to start ChromaDB
        try:
            chroma_proc = subprocess.Popen(
                ["chroma", "run", "--host", settings.chroma_host, "--port", str(settings.chroma_port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            # Wait a moment for it to start
            time.sleep(2)

            # Verify it started
            chroma_check = health.check_chroma_server()
            if chroma_check.running:
                print_success(f"ChromaDB started ({settings.chroma_host}:{settings.chroma_port})")
            else:
                print_error("ChromaDB failed to start")
                console.print(f"    [dim]Try manually: chroma run --host {settings.chroma_host} --port {settings.chroma_port}[/dim]")
        except FileNotFoundError:
            print_error("ChromaDB command not found")
            console.print("    [dim]Install with: pip install chromadb[/dim]")
    elif chroma_check.running:
        print_success(f"ChromaDB already running ({settings.chroma_host}:{settings.chroma_port})")

    # Start capture process
    console.print(f"  [{COLORS['muted']}]○[/] Starting screen capture...")

    if foreground:
        # Run in foreground - blocking
        print_success("Screen capture starting in foreground")
        console.print()
        console.print("  [dim]Press Ctrl+C to stop[/dim]")
        console.print()

        success, message = capture.start(foreground=True)
        if not success:
            print_error(message)
    else:
        # Run in background
        success, message = capture.start(foreground=False)
        if success:
            print_success(f"Screen capture started ({message})")

            # Get screen info
            screens = health.get_unique_screens()
            if screens:
                print_success(f"Monitoring {len(screens)} screens")
            else:
                print_success("Monitoring screens (will detect on first capture)")

            console.print()
            console.print("  Memex is now recording. Run [bold]memex status[/bold] to check.")
        else:
            print_error(f"Failed to start: {message}")

    console.print()
