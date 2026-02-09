"""Automate command - run automations from markdown instruction files."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from cli.display.components import print_header, print_error, print_success
from cli.display.colors import COLORS
from cli.services.ai import AIService
from cli.config.credentials import get_configured_providers

console = Console()
app = typer.Typer(help="Run and manage automations.")


@app.command()
def run(
    instruction_file: str = typer.Argument(help="Path to a markdown instruction file"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save output to ~/.memex/automations/output/"),
):
    """Run an automation from a markdown instruction file."""
    print_header("Automate")

    # Check AI is configured
    if not get_configured_providers():
        print_error("No AI provider configured")
        console.print()
        console.print("  To run automations, configure an API key first:")
        console.print("    [bold]memex auth login[/bold]")
        console.print()
        return

    # Read instruction file
    filepath = Path(instruction_file).expanduser().resolve()
    if not filepath.exists():
        print_error(f"File not found: {filepath}")
        console.print()
        return

    if not filepath.suffix == ".md":
        print_error("Instruction file must be a markdown (.md) file")
        console.print()
        return

    instruction = filepath.read_text().strip()
    if not instruction:
        print_error("Instruction file is empty")
        console.print()
        return

    console.print(f"  [dim]Running automation: {filepath.name}[/dim]")
    console.print()

    # Build the prompt with Memex context
    prompt = f"""You are Memex, running an automation. You have access to the user's screen capture history via tools.

Use search_screenshots and get_activity_stats to gather data as needed to fulfill the instruction below.

## Instruction
{instruction}

## Guidelines
- Use tools to gather relevant data before generating output
- Be thorough but concise in your output
- Format output in clean markdown
"""

    # Stream the AI response
    ai = AIService()
    collected_output = ""

    for event in ai.chat_stream(prompt):
        if event.type == "text":
            console.print(event.content, end="")
            collected_output += event.content
        elif event.type == "tool_call" and event.tool_call:
            console.print(f"  [dim]Using tool: {event.tool_call.name}[/dim]")
        elif event.type == "error":
            print_error(event.content)
            return

    console.print()
    console.print()

    # Save output
    if save and collected_output.strip():
        output_dir = Path.home() / ".memex" / "automations" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        stem = filepath.stem
        output_path = output_dir / f"{stem}_{timestamp}.md"

        output_path.write_text(collected_output.strip() + "\n")
        print_success(f"Saved to {output_path}")
        console.print()


@app.command("list")
def list_automations():
    """List saved automation outputs."""
    print_header("Automation Outputs")

    output_dir = Path.home() / ".memex" / "automations" / "output"
    if not output_dir.exists():
        console.print("  [dim]No automation outputs found.[/dim]")
        console.print()
        console.print("  Run an automation first:")
        console.print("    [bold]memex automate run <instruction.md>[/bold]")
        console.print()
        return

    files = sorted(output_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)

    if not files:
        console.print("  [dim]No automation outputs found.[/dim]")
        console.print()
        return

    for f in files[:20]:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        size = f.stat().st_size
        size_str = f"{size / 1024:.1f}K" if size >= 1024 else f"{size}B"
        console.print(f"  {mtime.strftime('%Y-%m-%d %H:%M')}  {size_str:>6}  {f.name}")

    if len(files) > 20:
        console.print(f"  [dim]... and {len(files) - 20} more[/dim]")

    console.print()
    console.print(f"  [dim]Output directory: {output_dir}[/dim]")
    console.print()
