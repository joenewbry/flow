"""Doctor command - comprehensive system diagnostics."""

from rich.console import Console

from cli.display.components import (
    print_header,
    print_section,
    print_check,
    print_check_warning,
    format_number,
)
from cli.display.colors import COLORS
from cli.services.health import HealthService
from cli.services.database import DatabaseService
from cli.config import get_settings

console = Console()


def doctor():
    """Full system diagnostics with fix suggestions."""
    print_header("Doctor")

    health = HealthService()
    db = DatabaseService()
    settings = get_settings()

    issues = 0
    warnings = 0

    # Dependencies
    print_section("Dependencies")

    python = health.check_python()
    print_check("Python", python.installed, f"{python.version}  {python.path or ''}")
    if not python.installed:
        issues += 1

    tesseract = health.check_tesseract()
    print_check(
        "Tesseract",
        tesseract.installed,
        f"{tesseract.version or ''}  {tesseract.path or ''}",
        "brew install tesseract" if not tesseract.installed else "",
    )
    if not tesseract.installed:
        issues += 1

    chroma_pkg = health.check_chroma_package()
    chroma_suggestion = ""
    if not chroma_pkg.installed:
        chroma_suggestion = "Run: ./install.sh or ~/.memex/.venv/bin/pip install chromadb"
        issues += 1
    print_check("ChromaDB", chroma_pkg.installed, chroma_pkg.version or "Not installed", chroma_suggestion)

    ngrok = health.check_ngrok()
    if ngrok.installed:
        print_check("NGROK", True, ngrok.path or "")
    else:
        print_check_warning("NGROK", "Not found (optional for remote)")

    uv = health.check_uv()
    if uv.installed:
        print_check("uv", True, uv.version or uv.path or "")
    else:
        print_check_warning("uv", "Not found (helps MCP server: brew install uv)")

    # Services
    print_section("Services")

    chroma_server = health.check_chroma_server()
    chroma_start_suggestion = ""
    if not chroma_server.running and chroma_pkg.installed:
        chroma_start_suggestion = "Run: memex start (auto-starts ChromaDB)"
    elif not chroma_server.running:
        chroma_start_suggestion = "Install ChromaDB first, then memex start"
    print_check(
        "ChromaDB Server",
        chroma_server.running,
        chroma_server.details,
        chroma_start_suggestion,
    )
    if not chroma_server.running:
        issues += 1

    capture = health.check_capture_process()
    print_check(
        "Capture Process",
        capture.running,
        f"pid {capture.pid}" if capture.running else "NOT RUNNING",
        "Run: memex start" if not capture.running else "",
    )
    if not capture.running:
        issues += 1

    mcp_server = health.check_mcp_server()
    mcp_suggestion = ""
    if not mcp_server.running:
        mcp_suggestion = "cd mcp-server && uv sync, then memex start (choose MCP)"
    print_check(
        "MCP HTTP Server",
        mcp_server.running,
        mcp_server.details,
        mcp_suggestion,
    )

    # Permissions
    print_section("Permissions")

    screen_perm = health.check_screen_recording_permission()
    print_check(
        "Screen Recording",
        screen_perm.granted,
        screen_perm.details,
        "System Preferences > Privacy > Screen Recording" if not screen_perm.granted else "",
    )
    if not screen_perm.granted:
        issues += 1

    data_perm = health.check_data_directory()
    print_check("Data Directory", data_perm.granted, data_perm.details)
    if not data_perm.granted:
        issues += 1

    # Data Integrity
    print_section("Data Integrity")

    ocr_count = health.get_ocr_file_count()
    print_check("OCR Files", True, f"{format_number(ocr_count)} files")

    if chroma_server.running:
        doc_count = db.get_document_count()
        print_check("ChromaDB Collection", True, f"{format_number(doc_count)} documents")

        # Check sync gap
        gap = ocr_count - doc_count
        if gap > 10:
            print_check_warning("Sync Gap", f"{format_number(gap)} files not in ChromaDB", "Run: memex sync")
            warnings += 1
        elif gap > 0:
            print_check("Sync Gap", True, f"{gap} files (acceptable)")
    else:
        console.print(f"  [{COLORS['muted']}]○[/] ChromaDB Collection   [dim]Unavailable (server not running)[/dim]")

    # Configuration
    print_section("Configuration")

    print_check("Capture Interval", True, f"{settings.capture_interval}s")

    screens = health.get_unique_screens()
    if screens:
        print_check("Screens Detected", True, f"{len(screens)} ({', '.join(screens)})")
    else:
        print_check("Screens Detected", True, "Will detect on first capture")

    print_check("Storage Path", True, str(settings.ocr_data_path))

    # Summary
    console.print()
    console.print(f"  [dim]{'═' * 55}[/dim]")

    if issues == 0 and warnings == 0:
        console.print(f"  [{COLORS['success']}]✓[/] All checks passed!")
    else:
        parts = []
        if issues > 0:
            parts.append(f"[{COLORS['error']}]{issues} issue{'s' if issues != 1 else ''}[/]")
        if warnings > 0:
            parts.append(f"[{COLORS['warning']}]{warnings} warning{'s' if warnings != 1 else ''}[/]")
        console.print(f"  Summary: {', '.join(parts)}")

        if issues > 0:
            console.print()
            console.print("  Quick fixes:")
            if not chroma_server.running:
                console.print("    [dim]chroma run --host localhost --port 8000[/dim]")
            if not capture.running:
                console.print("    [dim]memex start[/dim]")

    console.print()
