"""Graph command - live terminal dashboard for Memex usage."""

import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from cli.display.colors import COLORS
from cli.display.components import print_header, format_number
from cli.config import get_settings

console = Console()


def _parse_ocr_filename_date(filename: str) -> Optional[datetime]:
    """Extract datetime from OCR filename (fast, no JSON parsing)."""
    try:
        # Format: 2025-09-13T02-11-59-273071_Display_1.json
        # or:     2026-02-12T08-52-44-335601-08-00_Display_2.json
        ts_part = filename.split("_")[0]  # everything before first _Display
        date_str, time_str = ts_part.split("T")
        parts = time_str.split("-")
        # parts: [HH, MM, SS, microseconds, ...] or [HH, MM, SS, microseconds, tz offset...]
        h, m, s = parts[0], parts[1], parts[2]
        return datetime(
            int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10]),
            int(h), int(m), int(s),
        )
    except Exception:
        return None


def _count_files_by_period(ocr_path: Path, start: datetime, end: datetime, bucket_fmt: str):
    """Count OCR files grouped by time bucket. Uses filename parsing only (fast)."""
    buckets = defaultdict(int)
    for f in ocr_path.glob("*.json"):
        dt = _parse_ocr_filename_date(f.name)
        if dt and start <= dt <= end:
            buckets[dt.strftime(bucket_fmt)] += 1
    return buckets


def _count_mcp_calls(log_path: Path, start: datetime, end: datetime, bucket_fmt: str):
    """Count MCP tool calls from the server log grouped by time bucket."""
    buckets = defaultdict(int)
    if not log_path.exists():
        return buckets

    # Match: 2025-10-14 19:36:00,218 - mcp.server.lowlevel.server - INFO - Processing request of type CallToolRequest
    pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - .+ - INFO - Processing request of type (\w+)"
    )
    with open(log_path, "r") as f:
        for line in f:
            m = pattern.match(line)
            if not m:
                continue
            req_type = m.group(2)
            if req_type != "CallToolRequest":
                continue
            try:
                dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if start <= dt <= end:
                    buckets[dt.strftime(bucket_fmt)] += 1
            except ValueError:
                continue
    return buckets


def _render_bar(value: int, max_val: int, width: int = 38) -> str:
    """Render a single bar using Unicode blocks."""
    if max_val == 0:
        return "░" * width
    filled = int((value / max_val) * width)
    filled = min(filled, width)
    return "█" * filled + "░" * (width - filled)


def _render_dual_chart(
    title: str,
    labels: list[str],
    captures: dict,
    mcp_calls: dict,
    label_width: int = 7,
):
    """Render a dual bar chart (captures + MCP calls) in the terminal."""
    console.print()
    console.print(f"  [bold]{title}[/bold]")
    console.print(f"  [dim]{'─' * 62}[/dim]")

    all_cap_vals = [captures.get(l, 0) for l in labels]
    all_mcp_vals = [mcp_calls.get(l, 0) for l in labels]
    max_cap = max(all_cap_vals) if all_cap_vals else 1
    max_mcp = max(all_mcp_vals) if all_mcp_vals else 1

    for label in labels:
        cap = captures.get(label, 0)
        mcp = mcp_calls.get(label, 0)
        cap_bar = _render_bar(cap, max_cap, 30)
        mcp_bar = _render_bar(mcp, max_mcp, 14)
        cap_str = str(cap) if cap > 0 else "-"
        mcp_str = str(mcp) if mcp > 0 else "-"
        console.print(
            f"  {label:>{label_width}}  [{COLORS['primary']}]{cap_bar}[/] {cap_str:>5}"
            f"  [{COLORS['secondary']}]{mcp_bar}[/] {mcp_str:>3}"
        )

    # Legend
    console.print()
    console.print(
        f"  {'':>{label_width}}  [{COLORS['primary']}]██[/] Captures"
        f"                          [{COLORS['secondary']}]██[/] MCP Calls"
    )


def graph(
    week: bool = typer.Option(False, "--week", "-w", help="Show last 7 days (daily bars)"),
    month: bool = typer.Option(False, "--month", "-m", help="Show last 30 days (daily bars)"),
    all_time: bool = typer.Option(False, "--all", "-a", help="Show all-time (weekly bars)"),
):
    """Live usage graph - captures and MCP calls over time."""
    settings = get_settings()
    ocr_path = settings.ocr_data_path
    log_path = settings.project_root / "logs" / "mcp-server.log"
    now = datetime.now()

    print_header("Graph")

    # --- Summary boxes ---
    total_files = sum(1 for _ in ocr_path.glob("*.json")) if ocr_path.exists() else 0

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    epoch = datetime(2020, 1, 1)

    today_caps = _count_files_by_period(ocr_path, today_start, now, "%Y-%m-%d")
    today_cap_count = sum(today_caps.values())

    week_caps = _count_files_by_period(ocr_path, week_start, now, "%Y-%m-%d")
    week_cap_count = sum(week_caps.values())

    today_mcp = _count_mcp_calls(log_path, today_start, now, "%Y-%m-%d")
    today_mcp_count = sum(today_mcp.values())

    week_mcp = _count_mcp_calls(log_path, week_start, now, "%Y-%m-%d")
    week_mcp_count = sum(week_mcp.values())

    all_mcp = _count_mcp_calls(log_path, epoch, now, "%Y-%m-%d")
    all_mcp_count = sum(all_mcp.values())

    console.print(f"  {'Captures':26s} {'MCP Calls':26s}")
    console.print(f"  [dim]{'─' * 25}[/dim]   [dim]{'─' * 25}[/dim]")
    console.print(
        f"  Today:     [bold]{format_number(today_cap_count):>10}[/bold]"
        f"        Today:     [bold]{format_number(today_mcp_count):>10}[/bold]"
    )
    console.print(
        f"  This week: [bold]{format_number(week_cap_count):>10}[/bold]"
        f"        This week: [bold]{format_number(week_mcp_count):>10}[/bold]"
    )
    console.print(
        f"  All time:  [bold]{format_number(total_files):>10}[/bold]"
        f"        All time:  [bold]{format_number(all_mcp_count):>10}[/bold]"
    )

    # --- Charts ---
    if all_time:
        # Weekly buckets over all time
        # Find earliest file
        earliest = now
        for f in ocr_path.glob("*.json"):
            dt = _parse_ocr_filename_date(f.name)
            if dt and dt < earliest:
                earliest = dt

        # Generate week labels
        week_start_dt = earliest - timedelta(days=earliest.weekday())
        week_start_dt = week_start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        labels = []
        cur = week_start_dt
        while cur <= now:
            labels.append(cur.strftime("%Y-W%W"))
            cur += timedelta(weeks=1)

        captures = _count_files_by_period(ocr_path, earliest, now, "%Y-W%W")
        mcp_calls = _count_mcp_calls(log_path, earliest, now, "%Y-W%W")

        # Show last 20 weeks max to keep it readable
        if len(labels) > 20:
            labels = labels[-20:]

        _render_dual_chart(
            f"All Time (last {len(labels)} weeks)",
            labels, captures, mcp_calls, label_width=9,
        )

    elif month:
        # Daily bars for last 30 days
        labels = []
        for i in range(29, -1, -1):
            d = now - timedelta(days=i)
            labels.append(d.strftime("%Y-%m-%d"))

        month_start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        captures = _count_files_by_period(ocr_path, month_start, now, "%Y-%m-%d")
        mcp_calls = _count_mcp_calls(log_path, month_start, now, "%Y-%m-%d")

        # Map raw labels to short display labels
        display_labels = []
        cap_display = {}
        mcp_display = {}
        for l in labels:
            d = datetime.strptime(l, "%Y-%m-%d")
            dl = d.strftime("%b %d")
            display_labels.append(dl)
            cap_display[dl] = captures.get(l, 0)
            mcp_display[dl] = mcp_calls.get(l, 0)

        _render_dual_chart(
            "Last 30 Days",
            display_labels, cap_display, mcp_display, label_width=8,
        )

    elif week:
        # Daily bars for last 7 days
        labels = []
        display_labels = []
        for i in range(6, -1, -1):
            d = now - timedelta(days=i)
            labels.append(d.strftime("%Y-%m-%d"))
            day_name = d.strftime("%a")
            if i == 0:
                display_labels.append("Today")
            else:
                display_labels.append(f"{day_name} {d.strftime('%d')}")

        captures = _count_files_by_period(ocr_path, week_start, now, "%Y-%m-%d")
        mcp_calls = _count_mcp_calls(log_path, week_start, now, "%Y-%m-%d")

        # Map raw labels to display labels
        cap_display = {dl: captures.get(rl, 0) for rl, dl in zip(labels, display_labels)}
        mcp_display = {dl: mcp_calls.get(rl, 0) for rl, dl in zip(labels, display_labels)}

        _render_dual_chart(
            "Last 7 Days",
            display_labels, cap_display, mcp_display, label_width=9,
        )

    else:
        # Default: today hourly view + last 7 days daily
        # Hourly chart for today
        hour_labels = []
        for h in range(24):
            hour_labels.append(f"{h:02d}:00")

        captures_hourly = _count_files_by_period(ocr_path, today_start, now, "%H:00")
        mcp_hourly = _count_mcp_calls(log_path, today_start, now, "%H:00")

        # Only show hours from first activity to current
        first_active = None
        for h in range(24):
            key = f"{h:02d}:00"
            if captures_hourly.get(key, 0) > 0 or mcp_hourly.get(key, 0) > 0:
                first_active = h
                break

        if first_active is not None:
            current_hour = now.hour
            active_labels = [f"{h:02d}:00" for h in range(first_active, current_hour + 1)]
        else:
            active_labels = [f"{now.hour:02d}:00"]

        _render_dual_chart(
            f"Today ({now.strftime('%b %d, %Y')})",
            active_labels, captures_hourly, mcp_hourly, label_width=7,
        )

        # Also show last 7 days
        labels = []
        display_labels = []
        for i in range(6, -1, -1):
            d = now - timedelta(days=i)
            labels.append(d.strftime("%Y-%m-%d"))
            if i == 0:
                display_labels.append("Today")
            else:
                display_labels.append(f"{d.strftime('%a %d')}")

        captures_daily = _count_files_by_period(ocr_path, week_start, now, "%Y-%m-%d")
        mcp_daily = _count_mcp_calls(log_path, week_start, now, "%Y-%m-%d")

        cap_display = {dl: captures_daily.get(rl, 0) for rl, dl in zip(labels, display_labels)}
        mcp_display = {dl: mcp_daily.get(rl, 0) for rl, dl in zip(labels, display_labels)}

        _render_dual_chart(
            "Last 7 Days",
            display_labels, cap_display, mcp_display, label_width=9,
        )

    console.print()
