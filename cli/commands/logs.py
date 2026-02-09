"""Logs command - view service log files."""

import re
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.text import Text

from cli.display.components import print_header
from cli.display.colors import COLORS
from cli.config import get_settings

console = Console()

# Log file locations relative to project root
LOG_FILES = {
    "mcp": ("MCP Server", "logs/mcp-server.log"),
    "capture": ("Screen Capture", "refinery/logs/screen-capture.log"),
}

# Log format: 2024-01-15 10:30:45,123 - name - LEVEL - message
LOG_LINE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+) - (\S+) - (\w+) - (.*)$")

LEVEL_STYLES = {
    "ERROR": COLORS["error"],
    "WARNING": COLORS["warning"],
    "INFO": COLORS["success"],
    "DEBUG": COLORS["dim"],
}


def _format_log_line(line: str) -> Text:
    """Format a single log line with Rich styling."""
    text = Text()
    match = LOG_LINE_RE.match(line)
    if match:
        timestamp, name, level, message = match.groups()
        level_style = LEVEL_STYLES.get(level, "")
        text.append(timestamp, style="dim")
        text.append(" ")
        text.append(f"{level:<8}", style=level_style)
        text.append(message)
    else:
        text.append(line, style="dim")
    return text


def _read_last_lines(path: Path, n: int) -> list[str]:
    """Read the last n lines from a file."""
    try:
        with open(path, "r") as f:
            lines = f.readlines()
        return [l.rstrip("\n") for l in lines[-n:]]
    except Exception:
        return []


def _show_log(path: Path, service_name: str, lines: int, level: Optional[str], follow: bool):
    """Display log for a single service."""
    if not path.exists():
        console.print(f"  [dim]No log file found at {path}[/dim]")
        console.print(f"  [dim]Start the service first to generate logs.[/dim]")
        console.print()
        return

    console.print(f"  [{COLORS['primary']}]{service_name}[/]  [dim]{path}[/dim]")
    console.print()

    recent = _read_last_lines(path, lines)

    # Filter by level if specified
    if level:
        level_upper = level.upper()
        recent = [l for l in recent if level_upper in l]

    for line in recent:
        if line:
            console.print(Text("  ").append_text(_format_log_line(line)))

    if not recent:
        console.print("  [dim]No matching log entries.[/dim]")

    if follow:
        console.print()
        console.print("  [dim]Watching for new entries... Press Ctrl+C to stop[/dim]")
        console.print()
        try:
            with open(path, "r") as f:
                f.seek(0, 2)  # Seek to end
                while True:
                    new_line = f.readline()
                    if new_line:
                        new_line = new_line.rstrip("\n")
                        if level and level.upper() not in new_line:
                            continue
                        if new_line:
                            console.print(Text("  ").append_text(_format_log_line(new_line)))
                    else:
                        time.sleep(0.5)
        except KeyboardInterrupt:
            console.print()
            console.print("  [dim]Stopped watching.[/dim]")
            console.print()


def logs(
    service: str = typer.Argument("mcp", help="Service to show logs for: mcp, capture, or all"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output in real time"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of recent lines to show"),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="Filter by log level (INFO, WARNING, ERROR)"),
):
    """View service logs."""
    print_header("Logs")

    settings = get_settings()

    if service == "all":
        for key, (name, rel_path) in LOG_FILES.items():
            path = settings.project_root / rel_path
            _show_log(path, name, lines, level, follow=False)
            console.print()
        if follow:
            console.print("  [dim]--follow is only supported for a single service.[/dim]")
            console.print("  [dim]Use: memex logs mcp -f[/dim]")
            console.print()
    elif service in LOG_FILES:
        name, rel_path = LOG_FILES[service]
        path = settings.project_root / rel_path
        _show_log(path, name, lines, level, follow)
    else:
        console.print(f"  [{COLORS['error']}]Unknown service: {service}[/]")
        console.print(f"  [dim]Available: {', '.join(LOG_FILES.keys())}, all[/dim]")
        console.print()
