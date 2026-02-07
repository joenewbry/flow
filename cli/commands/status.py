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
from cli.display.colors import COLORS
from cli.services.health import HealthService

console = Console()


def status():
    """Quick health check and current state."""
    print_header("Status")

    health = HealthService()
    settings = health.settings

    # Check capture - based on recent activity, not just process
    latest = health.get_latest_capture_time()
    capture_active = False
    if latest:
        seconds_since_capture = (datetime.now() - latest).total_seconds()
        # Consider active if capture happened within 2x the interval
        capture_active = seconds_since_capture < (settings.capture_interval * 2)

    if capture_active:
        print_status_line(
            "Capture",
            StatusIndicator.RUNNING,
            "Active",
            f"every {settings.capture_interval}s",
        )
    else:
        # Check if process is running but no recent captures
        capture_process = health.check_capture_process()
        if capture_process.running:
            print_status_line(
                "Capture",
                StatusIndicator.WARNING,
                "Running",
                f"pid {capture_process.pid} (no recent captures)",
            )
        else:
            print_status_line("Capture", StatusIndicator.STOPPED, "Stopped")

    # Check ChromaDB
    chroma = health.check_chroma_server()
    if chroma.running:
        print_status_line("ChromaDB", StatusIndicator.RUNNING, "Connected", chroma.details)
    else:
        print_status_line("ChromaDB", StatusIndicator.STOPPED, "Disconnected")

    # Check MCP server
    mcp = health.check_mcp_server()
    if mcp.running:
        print_status_line("MCP Server", StatusIndicator.RUNNING, "Ready", mcp.details)
    else:
        print_status_line("MCP Server", StatusIndicator.STOPPED, "Not running", mcp.details)

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
