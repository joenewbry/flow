"""Stop command - stop capture daemon."""

import typer
from rich.console import Console

from cli.display.components import print_header, print_success, print_error, format_number
from cli.display.colors import COLORS
from cli.services.capture import CaptureService
from cli.services.health import HealthService

console = Console()


def stop(
    stop_chroma: bool = typer.Option(
        False, "--stop-chroma", help="Also stop ChromaDB server"
    ),
):
    """Stop the capture daemon."""
    print_header("Stopping")

    capture = CaptureService()
    health = HealthService()

    # Check if running
    running, pid = capture.is_running()
    if not running:
        console.print(f"  [{COLORS['muted']}]○[/] Capture process not running")
    else:
        # Get today's stats before stopping
        today_count = health.get_today_capture_count()

        # Stop capture
        success, message = capture.stop()
        if success:
            print_success(f"Screen capture stopped (pid {pid})")
        else:
            print_error(f"Failed to stop: {message}")

        # Show session stats
        if today_count > 0:
            console.print()
            console.print(f"  Today's captures: [bold]{format_number(today_count)}[/bold]")

    # Optionally stop ChromaDB
    if stop_chroma:
        import subprocess
        try:
            result = subprocess.run(
                ["pkill", "-f", "chroma run"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                print_success("ChromaDB server stopped")
            else:
                console.print(f"  [{COLORS['muted']}]○[/] ChromaDB server not running")
        except Exception as e:
            print_error(f"Failed to stop ChromaDB: {e}")

    console.print()
