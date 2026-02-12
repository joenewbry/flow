"""Record command - manage audio recording."""

import typer
from rich.console import Console

from cli.display.components import (
    print_header,
    print_success,
    print_error,
    print_warning,
    print_status_line,
    StatusIndicator,
    format_bytes,
    format_number,
)
from cli.display.colors import COLORS
from cli.services.audio import AudioService

app = typer.Typer(help="Manage audio recording.")
console = Console()


@app.command()
def start():
    """Start audio recording (system audio + microphone)."""
    print_header("Audio Recording")

    audio = AudioService()

    if not audio.is_built():
        print_error("Audio recorder not built")
        console.print()
        console.print("  Build it first:")
        console.print("    [bold]cd recorder && swift build -c release[/bold]")
        console.print()
        return

    running, pid = audio.is_running()
    if running:
        print_warning(f"Already recording (pid {pid})")
        console.print()
        return

    success, message = audio.start()
    if success:
        print_success(f"Audio recording started ({message})")
        console.print()
        console.print(f"  Output: [dim]{audio.output_dir}[/dim]")
        console.print(f"  Rotation: every [bold]{audio.settings.audio_rotation_interval}s[/bold]")
        console.print()
        console.print("  Recording system audio (Zoom/Teams/browser) and microphone.")
        console.print("  Run [bold]memex record status[/bold] to check.")
    else:
        print_error(f"Failed to start: {message}")

    console.print()


@app.command()
def stop():
    """Stop audio recording."""
    print_header("Audio Recording")

    audio = AudioService()
    running, pid = audio.is_running()

    if not running:
        console.print(f"  [{COLORS['muted']}]○[/] Audio recorder not running")
        console.print()
        return

    success, message = audio.stop()
    if success:
        print_success(f"Audio recording stopped (pid {pid})")
        count = audio.get_recording_count()
        size = audio.get_total_size()
        if count > 0:
            console.print(f"  Recordings: [bold]{format_number(count)}[/bold] files ({format_bytes(size)})")
    else:
        print_error(f"Failed to stop: {message}")

    console.print()


@app.command()
def status():
    """Check audio recording status."""
    print_header("Audio Recording")

    audio = AudioService()

    # Build status
    if not audio.is_built():
        print_status_line("Recorder", StatusIndicator.STOPPED, "Not built")
        console.print()
        console.print("  Build: [bold]cd recorder && swift build -c release[/bold]")
        console.print()
        return

    # Running status
    running, pid = audio.is_running()
    if running:
        print_status_line("Recording", StatusIndicator.RUNNING, "Active", f"pid {pid}")
    else:
        print_status_line("Recording", StatusIndicator.STOPPED, "Stopped")

    # File stats
    count = audio.get_recording_count()
    size = audio.get_total_size()
    print_status_line("Files", StatusIndicator.RUNNING if count > 0 else StatusIndicator.STOPPED,
                      f"{format_number(count)} recordings", format_bytes(size))

    console.print(f"\n  Output: [dim]{audio.output_dir}[/dim]")
    console.print()
