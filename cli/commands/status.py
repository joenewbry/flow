"""Status command - quick health check."""

from datetime import datetime, timedelta
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
from cli.services.database import DatabaseService
from cli.services.audio import AudioService
from cli.services.instance import InstanceService
from cli.services.usage import UsageTracker

console = Console()


def status():
    """Quick health check and current state."""
    print_header("Status")

    health = HealthService()
    settings = health.settings

    # Show hosting mode
    instance_svc = InstanceService()
    instance_config = instance_svc.load()
    mode = instance_config.hosting_mode
    mode_detail = ""
    if mode == "jetson" and instance_config.jetson_host:
        mode_detail = instance_config.jetson_host
    elif mode == "remote" and instance_config.remote_host:
        mode_detail = instance_config.remote_host
    print_status_line("Hosting", StatusIndicator.RUNNING, mode, mode_detail)

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

    # Check audio recording
    audio = AudioService()
    audio_running, audio_pid = audio.is_running()
    if audio_running:
        audio_count = audio.get_recording_count()
        audio_size = audio.get_total_size()
        detail = f"pid {audio_pid}"
        if audio_count > 0:
            detail += f", {format_number(audio_count)} files ({format_bytes(audio_size)})"
        print_status_line("Audio", StatusIndicator.RUNNING, "Recording", detail)
    else:
        print_status_line("Audio", StatusIndicator.STOPPED, "Stopped")

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

    # Last 7 days and all-time counts
    db = DatabaseService()
    now = datetime.now()
    week_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_count = db.get_capture_count(start_date=week_start, end_date=now)
    all_time_count = health.get_ocr_file_count()

    console.print(f"  Last 7 days: [bold]{format_number(week_count)}[/bold] captures")
    console.print(f"  All time: [bold]{format_number(all_time_count)}[/bold] captures")

    # Usage tracking summary
    tracker = UsageTracker()
    day_usage = tracker.get_usage_summary("day")
    if day_usage["tool_calls"] > 0 or day_usage["data_syncs"] > 0:
        console.print()
        console.print(f"  [dim]Usage today:[/dim] [bold]{day_usage['tool_calls']}[/bold] tool calls", end="")
        if day_usage["data_syncs"] > 0:
            console.print(f", [bold]{day_usage['data_syncs']}[/bold] syncs ({format_bytes(day_usage['total_bytes'])})")
        else:
            console.print()

    console.print()
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print()
