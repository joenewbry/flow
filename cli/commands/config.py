"""Config command - view and manage configuration."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from cli.display.components import print_header
from cli.display.colors import COLORS
from cli.config import get_settings
from cli.services.health import HealthService

console = Console()

app = typer.Typer(help="View and manage configuration")


@app.callback(invoke_without_command=True)
def config(ctx: typer.Context):
    """View current configuration."""
    if ctx.invoked_subcommand is not None:
        return

    print_header("Configuration")

    settings = get_settings()
    health = HealthService()

    # Create table
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
    )
    table.add_column("Key", style="dim", width=20)
    table.add_column("Value", style="bold")
    table.add_column("Description", style="dim")

    # Add config values
    table.add_row(
        "capture_interval",
        f"{settings.capture_interval}",
        "Seconds between captures",
    )

    table.add_row(
        "data_path",
        str(settings.ocr_data_path),
        "",
    )

    table.add_row(
        "chroma_host",
        settings.chroma_host,
        "",
    )

    table.add_row(
        "chroma_port",
        str(settings.chroma_port),
        "",
    )

    screens = health.get_unique_screens()
    screens_str = f"{len(screens)} ({', '.join(screens)})" if screens else "Will detect"
    table.add_row(
        "screens",
        screens_str,
        "Detected screens",
    )

    table.add_row(
        "config_dir",
        str(settings.config_dir),
        "Config file location",
    )

    console.print(table)
    console.print()
    console.print(f"  [dim]Edit: memex config set <key> <value>[/dim]")
    console.print(f"  [dim]File: {settings.config_dir / 'config.toml'}[/dim]")
    console.print()


@app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="New value"),
):
    """Set a configuration value."""
    settings = get_settings()

    valid_keys = ["capture_interval", "chroma_host", "chroma_port"]

    if key not in valid_keys:
        console.print(f"  [{COLORS['error']}]✗[/] Unknown key: {key}")
        console.print(f"  [dim]Valid keys: {', '.join(valid_keys)}[/dim]")
        return

    # For now, just show what would be set
    # TODO: Implement actual config file writing
    console.print(f"  [{COLORS['warning']}]![/] Config file not yet implemented")
    console.print(f"  [dim]Would set {key} = {value}[/dim]")
    console.print()


@app.command("path")
def config_path():
    """Show configuration file path."""
    settings = get_settings()
    config_file = settings.config_dir / "config.toml"

    console.print(f"  Config directory: {settings.config_dir}")
    console.print(f"  Config file:      {config_file}")
    console.print()

    if config_file.exists():
        console.print(f"  [{COLORS['success']}]✓[/] Config file exists")
    else:
        console.print(f"  [{COLORS['muted']}]○[/] Config file not created yet")
    console.print()


# Export the main config function for use in main.py
def config_cmd(ctx: typer.Context = typer.Context):
    """View and manage configuration."""
    config(ctx)
