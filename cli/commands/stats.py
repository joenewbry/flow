"""Stats command - activity statistics."""

from datetime import datetime, timedelta
from typing import Optional
import typer
from rich.console import Console

from cli.display.components import (
    print_header,
    print_section,
    create_bar,
    format_number,
    format_bytes,
)
from cli.display.colors import COLORS
from cli.services.database import DatabaseService
from cli.services.health import HealthService
from cli.config import get_settings

console = Console()


def stats(
    today: bool = typer.Option(False, "--today", "-t", help="Show only today's stats"),
    week: bool = typer.Option(False, "--week", "-w", help="Show this week's stats"),
    month: bool = typer.Option(False, "--month", "-m", help="Show this month's stats"),
    all_time: bool = typer.Option(False, "--all", "-a", help="Show all-time stats"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Activity statistics and charts."""
    db = DatabaseService()
    health = HealthService()
    settings = get_settings()

    now = datetime.now()

    # Determine date range (default to today)
    if all_time:
        start_date = None
        end_date = None
        period_name = "All Time"
    elif month:
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        period_name = now.strftime("%B %Y")
    elif week:
        # Start of week (Monday)
        start_date = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = now
        period_name = "This Week"
    else:
        # Today (default)
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
        period_name = now.strftime("%b %d, %Y")

    # Get stats
    day_stats = db.get_stats(
        start_date=now.replace(hour=0, minute=0, second=0, microsecond=0),
        end_date=now,
    )

    if json_output:
        import json
        output = {
            "period": period_name,
            "captures": day_stats["captures"],
            "words": day_stats["words"],
            "screens": day_stats["screens"],
            "hours": day_stats["hours"],
        }
        console.print(json.dumps(output, indent=2))
        return

    print_header("Stats")

    # Today section
    console.print(f"  [bold]Today[/bold] ({now.strftime('%b %d, %Y')})")
    console.print(f"  [dim]{'─' * 55}[/dim]")

    captures = day_stats["captures"]
    words = day_stats["words"]
    screens = len(day_stats["screens"])

    # Calculate hours active
    hours_active = len(day_stats["hours"])
    if day_stats["hours"]:
        first_hour = min(day_stats["hours"].keys())
        last_hour = max(day_stats["hours"].keys())
        avg_per_hour = captures / hours_active if hours_active > 0 else 0
    else:
        first_hour = last_hour = 0
        avg_per_hour = 0

    # Format words nicely
    if words >= 1_000_000:
        words_str = f"{words / 1_000_000:.1f}M"
    elif words >= 1_000:
        words_str = f"{words / 1_000:.1f}K"
    else:
        words_str = str(words)

    console.print(f"  Screenshots: [bold]{format_number(captures)}[/bold]           Words captured: [bold]{words_str}[/bold]")
    console.print(f"  Screens:     [bold]{screens}[/bold]             Avg per hour:   [bold]{int(avg_per_hour)}[/bold]")
    console.print()

    # Hour activity bar
    if day_stats["hours"]:
        max_captures = max(day_stats["hours"].values()) if day_stats["hours"] else 1
        bar_parts = []
        for h in range(8, 21):  # 8 AM to 8 PM
            if h in day_stats["hours"]:
                intensity = day_stats["hours"][h] / max_captures
                if intensity > 0.7:
                    bar_parts.append("█")
                elif intensity > 0.3:
                    bar_parts.append("▓")
                else:
                    bar_parts.append("░")
            else:
                bar_parts.append("░")

        bar = "".join(bar_parts)
        console.print(f"  Hours active: [{COLORS['primary']}]{bar}[/]", end="")
        if first_hour and last_hour:
            console.print(f" {first_hour}:00 - {last_hour}:59")
        else:
            console.print()

        console.print("                8  9  10 11 12 13 14 15 16 17 18 19 20")

    # Summary counts (always shown in default view)
    if not (week or month or all_time):
        console.print()
        console.print(f"  [bold]Summary[/bold]")
        console.print(f"  [dim]{'─' * 55}[/dim]")

        week_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        year_start = (now - timedelta(days=365)).replace(hour=0, minute=0, second=0, microsecond=0)

        week_count = db.get_capture_count(start_date=week_start, end_date=now)
        month_count = db.get_capture_count(start_date=month_start, end_date=now)
        year_count = db.get_capture_count(start_date=year_start, end_date=now)

        console.print(f"  Last 7 days:   [bold]{format_number(week_count)}[/bold]")
        console.print(f"  Last 30 days:  [bold]{format_number(month_count)}[/bold]")
        console.print(f"  Last 365 days: [bold]{format_number(year_count)}[/bold]")

    # Week section if requested
    if week or all_time or month:
        console.print()
        print_section("This Week")

        # Get stats for each day of the week
        week_data = {}
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for i in range(7):
            day_date = (now - timedelta(days=now.weekday() - i))
            day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            if day_start <= now:
                day_data = db.get_stats(start_date=day_start, end_date=min(day_end, now))
                week_data[i] = day_data["captures"]
            else:
                week_data[i] = 0

        max_day = max(week_data.values()) if week_data.values() else 1

        for i, day_name in enumerate(day_names):
            count = week_data.get(i, 0)
            is_today = i == now.weekday()

            if count > 0:
                bar = create_bar(count, max_day, 40)
                count_str = format_number(count)
                if is_today:
                    count_str += "  (today)"
                console.print(f"  {day_name} [{COLORS['primary']}]{bar}[/]  {count_str}")
            else:
                bar = "░" * 40
                console.print(f"  {day_name} [dim]{bar}[/dim]  -")

    # All time section
    if all_time:
        console.print()
        print_section("All Time")

        total_files = health.get_ocr_file_count()
        storage = health.get_storage_size()

        # Try to get earliest file date
        import os
        earliest_date = None
        if settings.ocr_data_path.exists():
            files = list(settings.ocr_data_path.glob("*.json"))
            if files:
                earliest_file = min(files, key=lambda f: f.stat().st_mtime)
                earliest_date = datetime.fromtimestamp(earliest_file.stat().st_mtime)

        console.print(f"  Total captures:  [bold]{format_number(total_files)}[/bold]", end="")
        if earliest_date:
            console.print(f"      Since: {earliest_date.strftime('%b %d, %Y')}")
        else:
            console.print()

        # Estimate total words (sample-based)
        if total_files > 0:
            # Use today's average as estimate
            if captures > 0:
                avg_words_per_capture = words / captures
                estimated_total_words = int(total_files * avg_words_per_capture)
                if estimated_total_words >= 1_000_000:
                    total_words_str = f"{estimated_total_words / 1_000_000:.1f}M"
                else:
                    total_words_str = f"{estimated_total_words / 1_000:.0f}K"
                console.print(f"  Total words:     [bold]~{total_words_str}[/bold]", end="")
            else:
                console.print(f"  Total words:     [bold]-[/bold]", end="")

            if earliest_date:
                days_active = (now - earliest_date).days + 1
                avg_per_day = total_files / days_active
                console.print(f"       Days active: {days_active}")
                console.print(f"  Storage used:    [bold]{format_bytes(storage)}[/bold]       Avg/day: {int(avg_per_day)}")
            else:
                console.print()
                console.print(f"  Storage used:    [bold]{format_bytes(storage)}[/bold]")

    console.print()
