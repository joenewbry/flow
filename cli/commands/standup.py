"""Standup command - generate daily standup summaries from screen captures."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.markdown import Markdown

from cli.display.components import print_header, print_error, print_success
from cli.display.colors import COLORS
from cli.services.ai import AIService, execute_tool
from cli.config.credentials import get_configured_providers

console = Console()


def _get_lookback_date(target_date: datetime) -> datetime:
    """Get the lookback start date (Friday if Monday, otherwise yesterday)."""
    weekday = target_date.weekday()
    if weekday == 0:  # Monday
        return target_date - timedelta(days=3)  # Friday
    else:
        return target_date - timedelta(days=1)


def _get_lookback_label(target_date: datetime) -> str:
    """Get a human-readable label for the lookback period."""
    weekday = target_date.weekday()
    if weekday == 0:
        return "Last Friday"
    else:
        return "Yesterday"


def _format_standup_date(dt: datetime) -> str:
    """Format date for standup header."""
    return dt.strftime("%A, %b %d, %Y")


def standup(
    save: bool = typer.Option(False, "--save", "-s", help="Save standup to ~/.memex/standups/"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Generate for a specific date (YYYY-MM-DD)"),
):
    """Generate a daily standup summary from screen captures."""
    print_header("Standup")

    # Check AI is configured
    if not get_configured_providers():
        print_error("No AI provider configured")
        console.print()
        console.print("  To generate standups, configure an API key first:")
        console.print("    [bold]memex auth login[/bold]")
        console.print()
        return

    # Parse target date
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
            target_date = target_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            print_error(f"Invalid date format: {date}. Use YYYY-MM-DD.")
            console.print()
            return
    else:
        target_date = datetime.now()

    # Determine lookback period
    lookback_start = _get_lookback_date(target_date)
    lookback_start = lookback_start.replace(hour=0, minute=0, second=0, microsecond=0)
    lookback_end = lookback_start.replace(hour=23, minute=59, second=59)
    lookback_label = _get_lookback_label(target_date)

    console.print(f"  [dim]Generating standup for {_format_standup_date(target_date)}[/dim]")
    console.print(f"  [dim]Looking back at: {lookback_label} ({lookback_start.strftime('%b %d')})[/dim]")
    console.print()

    # Gather data from the lookback period
    stats_result = execute_tool("get_activity_stats", {
        "period": "yesterday" if target_date.weekday() != 0 else "today"
    })

    # Search for activity context
    search_result = execute_tool("search_screenshots", {
        "query": "work project code meeting",
        "start_date": lookback_start.isoformat(),
        "end_date": lookback_end.isoformat(),
        "limit": 20,
    })

    # Build the AI prompt
    standup_date_str = _format_standup_date(target_date)
    lookback_date_str = lookback_start.strftime("%A, %b %d")

    prompt = f"""Generate a daily standup summary based on the following screen capture data.

Today is {standup_date_str}. The lookback period is {lookback_label} ({lookback_date_str}).

## Activity Stats
{stats_result}

## Screen Capture Content ({lookback_label})
{search_result}

## Instructions
Write a standup summary in this exact format:

## Standup — {standup_date_str}

**{lookback_label} I worked on:**
- [Summarize the main activities from the screen captures above. Group related items. Be specific about projects/topics.]

**Today I'm going to work on:**
- [Infer likely next steps from the context, or write "Continue work on [topics]" if unclear]

**Blockers:**
- None identified

Keep it concise — 3-5 bullet points per section max. If there's no capture data, say "No screen captures found for this period."
"""

    # Stream the AI response
    ai = AIService()
    collected_output = ""

    for event in ai.chat_stream(prompt):
        if event.type == "text":
            console.print(event.content, end="")
            collected_output += event.content
        elif event.type == "error":
            print_error(event.content)
            return

    console.print()
    console.print()

    # Save if requested
    if save:
        standups_dir = Path.home() / ".memex" / "standups"
        standups_dir.mkdir(parents=True, exist_ok=True)

        filename = target_date.strftime("%Y-%m-%d") + ".md"
        filepath = standups_dir / filename

        filepath.write_text(collected_output.strip() + "\n")
        print_success(f"Saved to {filepath}")
        console.print()
