"""Reusable UI components for Memex CLI."""

from enum import Enum
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cli import __version__
from cli.display.colors import COLORS, STYLES

console = Console()


class StatusIndicator(Enum):
    """Status indicators for visual display."""
    RUNNING = ("●", "success")
    STOPPED = ("○", "muted")
    PROGRESS = ("◐", "warning")
    ERROR = ("✗", "error")
    WARNING = ("⚠", "warning")
    SUCCESS = ("✓", "success")


LOGO = """    ┌───────────┐
    │  MEMEX    │
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │
    └───────────┘"""

LOGO_MINIMAL = "▣ Memex"


def print_logo():
    """Print the Memex logo with version info."""
    lines = LOGO.split("\n")
    info_lines = [
        "",
        "",
        f"memex v{__version__}",
        "───────────────",
        '"your digital memory"',
        "",
        "",
        "",
    ]

    for i, line in enumerate(lines):
        info = info_lines[i] if i < len(info_lines) else ""
        if info:
            console.print(f"[{COLORS['primary']}]{line}[/]     {info}")
        else:
            console.print(f"[{COLORS['primary']}]{line}[/]")


def print_header(title: str):
    """Print a styled header."""
    console.print()
    console.print(f"  [{COLORS['primary']}]{LOGO_MINIMAL}[/] {title}")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print()


def print_section(title: str, char: str = "─"):
    """Print a section divider."""
    console.print()
    console.print(f"  [bold]{title}[/bold]")
    console.print(f"  [dim]{char * 50}[/dim]")


def print_status_line(label: str, status: StatusIndicator, value: str, extra: str = ""):
    """Print a status line with indicator."""
    indicator, color = status.value
    extra_text = f"  [dim]{extra}[/dim]" if extra else ""
    console.print(f"  [{color}]{indicator}[/] {label:<12} {value}{extra_text}")


def print_key_value(key: str, value: str, indent: int = 2):
    """Print a key-value pair."""
    spaces = " " * indent
    console.print(f"{spaces}[dim]{key}[/dim]  {value}")


def print_success(message: str):
    """Print a success message."""
    console.print(f"  [{COLORS['success']}]✓[/] {message}")


def print_error(message: str):
    """Print an error message."""
    console.print(f"  [{COLORS['error']}]✗[/] {message}")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"  [{COLORS['warning']}]⚠[/] {message}")


def print_check(label: str, passed: bool, value: str = "", suggestion: str = ""):
    """Print a check result (for doctor command)."""
    if passed:
        console.print(f"  [{COLORS['success']}]✓[/] {label:<22} [dim]{value}[/dim]")
    else:
        console.print(f"  [{COLORS['error']}]✗[/] {label:<22} [dim]{value}[/dim]")
        if suggestion:
            console.print(f"    [dim]→ {suggestion}[/dim]")


def print_check_warning(label: str, value: str = "", suggestion: str = ""):
    """Print a warning check result."""
    console.print(f"  [{COLORS['warning']}]⚠[/] {label:<22} [dim]{value}[/dim]")
    if suggestion:
        console.print(f"    [dim]→ {suggestion}[/dim]")


def create_bar(value: float, max_value: float, width: int = 40) -> str:
    """Create an ASCII progress bar."""
    if max_value == 0:
        return "░" * width
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


def format_number(n: int) -> str:
    """Format a number with commas."""
    return f"{n:,}"


def format_bytes(b: int) -> str:
    """Format bytes to human readable."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"
