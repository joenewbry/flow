"""Status command - quick health check."""

from datetime import datetime
from rich.console import Console

from cli.display.components import (
    print_header,
    print_status_line,
    StatusIndicator,
    format_bytes,
    format_number,
)
from cli.services.health import HealthService

console = Console()


def status():
    """Quick health check and current state."""
    print_header("Status")

    health = HealthService()

    # Check capture process
    capture = health.check_capture_process()
    if capture.running:
        print_status_line(
            "Capture",
            StatusIndicator.RUNNING,
            "Running",
            f"pid {capture.pid}",
        )
    else:
        print_status_line("Capture", StatusIndicator.STOPPED, "Stopped")

    # Check ChromaDB
    chroma = health.check_chroma_server()
    if chroma.running:
        print_status_line("ChromaDB", StatusIndicator.RUNNING, "Connected", chroma.details)
    else:
        print_status_line("ChromaDB", StatusIndicator.STOPPED, "Disconnected")

    # Check storage
    storage_bytes = health.get_storage_size()
    print_status_line(
        "Storage",
        StatusIndicator.RUNNING,
        "Healthy",
        format_bytes(storage_bytes),
    )

    console.print()

    # Today's stats
    today_count = health.get_today_capture_count()
    screens = health.get_unique_screens()
    screen_count = len(screens) if screens else 0

    console.print(f"  Today: [bold]{format_number(today_count)}[/bold] captures", end="")
    if screen_count > 0:
        console.print(f" across [bold]{screen_count}[/bold] screens")
    else:
        console.print()

    # Last capture time
    latest = health.get_latest_capture_time()
    if latest:
        delta = datetime.now() - latest
        if delta.total_seconds() < 60:
            ago = f"{int(delta.total_seconds())} seconds ago"
        elif delta.total_seconds() < 3600:
            ago = f"{int(delta.total_seconds() / 60)} minutes ago"
        else:
            ago = f"{int(delta.total_seconds() / 3600)} hours ago"
        console.print(f"  Last capture: [dim]{ago}[/dim]")
    else:
        console.print("  Last capture: [dim]No captures yet[/dim]")

    console.print()
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print()
