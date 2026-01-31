"""Watch command - live view of captures."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from cli.display.components import print_header
from cli.display.colors import COLORS
from cli.config import get_settings

console = Console()


def create_watch_table(recent_captures: list, stats: dict) -> Table:
    """Create the watch display table."""
    table = Table(
        show_header=True,
        header_style="bold",
        box=None,
        padding=(0, 1),
        expand=True,
    )

    table.add_column("Time", style="dim", width=10)
    table.add_column("Screen", width=10)
    table.add_column("Words", justify="right", width=8)
    table.add_column("Preview", overflow="ellipsis")

    for capture in recent_captures[-10:]:  # Show last 10
        time_str = capture["time"].strftime("%H:%M:%S")
        preview = capture["text"][:60].replace("\n", " ") + "..." if len(capture["text"]) > 60 else capture["text"].replace("\n", " ")

        table.add_row(
            time_str,
            capture["screen"],
            str(capture["words"]),
            f'"{preview}"',
        )

    return table


def watch(
    interval: float = typer.Option(1.0, "--interval", "-i", help="Refresh interval in seconds"),
):
    """Live view of captures as they happen."""
    print_header("Watch (live)")

    settings = get_settings()
    ocr_path = settings.ocr_data_path

    if not ocr_path.exists():
        console.print("  [dim]No data directory found. Run 'memex start' first.[/dim]")
        console.print()
        return

    console.print("  [dim]Watching for new captures... Press Ctrl+C to stop[/dim]")
    console.print()

    recent_captures = []
    seen_files = set()
    stats = {"total": 0, "errors": 0}

    # Initialize with existing recent files
    existing_files = sorted(
        ocr_path.glob("*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:10]

    for f in reversed(existing_files):
        seen_files.add(f.name)
        try:
            with open(f, "r") as fp:
                data = json.load(fp)
                recent_captures.append({
                    "time": datetime.fromtimestamp(f.stat().st_mtime),
                    "screen": data.get("screen_name", "unknown"),
                    "words": data.get("word_count", 0),
                    "text": data.get("text", "")[:100],
                })
        except Exception:
            pass

    try:
        with Live(console=console, refresh_per_second=2) as live:
            while True:
                # Check for new files
                current_files = list(ocr_path.glob("*.json"))

                for f in current_files:
                    if f.name not in seen_files:
                        seen_files.add(f.name)
                        stats["total"] += 1

                        try:
                            with open(f, "r") as fp:
                                data = json.load(fp)
                                recent_captures.append({
                                    "time": datetime.fromtimestamp(f.stat().st_mtime),
                                    "screen": data.get("screen_name", "unknown"),
                                    "words": data.get("word_count", 0),
                                    "text": data.get("text", "")[:100],
                                })
                        except Exception:
                            stats["errors"] += 1

                # Keep only last 20 captures in memory
                if len(recent_captures) > 20:
                    recent_captures = recent_captures[-20:]

                # Build display
                output = Text()
                table = create_watch_table(recent_captures, stats)

                # Add stats footer
                footer = Text()
                footer.append("\n  ")
                footer.append(f"New: {stats['total']}", style=COLORS["success"])
                footer.append("  │  ")
                footer.append(f"Errors: {stats['errors']}", style=COLORS["error"] if stats["errors"] > 0 else "dim")
                footer.append("  │  ")
                footer.append("Press Ctrl+C to stop", style="dim")

                # Combine table and footer
                live.update(table)

                time.sleep(interval)

    except KeyboardInterrupt:
        console.print()
        console.print(f"  [dim]Stopped watching. New captures during session: {stats['total']}[/dim]")
        console.print()
