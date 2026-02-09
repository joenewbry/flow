"""Start command - start capture daemon."""

import subprocess
import time
import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.prompt import Confirm

from cli.display.components import print_header, print_success, print_error, print_warning
from cli.display.colors import COLORS
from cli.services.capture import CaptureService
from cli.services.chroma import get_chroma_command
from cli.services.health import HealthService
from cli.services.mcp import MCPService
from cli.config import get_settings
from cli.config.credentials import get_configured_providers

console = Console()


def _wait_for_service(check_fn, timeout=15, interval=1):
    """Poll a health check function until it reports running or timeout is reached."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        result = check_fn()
        if result.running:
            return result
    return result


def start(
    foreground: bool = typer.Option(
        False, "--foreground", "-f", help="Run in foreground with live output"
    ),
    no_chroma: bool = typer.Option(
        False, "--no-chroma", help="Don't auto-start ChromaDB"
    ),
    mcp: bool = typer.Option(
        None, "--mcp/--no-mcp", help="Start MCP server for Claude/Cursor (prompts if not specified)"
    ),
    skip_token_check: bool = typer.Option(
        False, "--skip-token-check", help="Skip AI token requirement (not recommended)"
    ),
):
    """Start the capture daemon. Requires a valid AI token (Anthropic, OpenAI, or Grok) for chat."""
    print_header("Starting")

    capture = CaptureService()
    health = HealthService()
    mcp_svc = MCPService()
    settings = get_settings()

    # Require valid AI token (unless skipped)
    if not skip_token_check:
        configured = get_configured_providers()
        if not configured:
            print_error("No AI token configured. Memex requires Anthropic, OpenAI, or Grok for chat.")
            console.print()
            console.print("  Configure an API key first:")
            console.print("    [bold]memex auth login[/bold]")
            console.print()
            console.print("  Or set an environment variable:")
            console.print("    export ANTHROPIC_API_KEY=sk-ant-...")
            console.print("    export OPENAI_API_KEY=sk-...")
            console.print("    export XAI_API_KEY=xai-...")
            console.print()
            return

    # Ask about MCP server if not specified
    start_mcp = mcp
    if mcp is None:
        console.print(f"  Start MCP server for connecting Memex to Claude or other tools? (port {settings.mcp_http_port})")
        start_mcp = Confirm.ask("  Start MCP server?", default=False)
        console.print()

    # Check if already running - stop it so we can restart fresh
    running, pid = capture.is_running()
    if running:
        console.print(f"  [{COLORS['muted']}]○[/] Stopping existing capture process (pid {pid})...")
        success, _ = capture.stop()
        time.sleep(1)
        still_running, _ = capture.is_running()
        if still_running:
            print_warning("Could not stop existing process. Run [bold]memex stop[/bold] first, then try again.")
            console.print()
            return
        console.print()

    # Check ChromaDB
    chroma_check = health.check_chroma_server()
    if not chroma_check.running and not no_chroma:
        console.print(f"  [{COLORS['muted']}]○[/] ChromaDB not running, starting...")

        chroma_exe, chroma_cmd = get_chroma_command()
        if not chroma_cmd:
            print_error("ChromaDB not found in venv or PATH")
            console.print()
            console.print("  [dim]To fix:[/dim]")
            console.print("    • Re-run [bold]./install.sh[/bold] to ensure ~/.memex venv has chromadb")
            console.print("    • Or: ~/.memex/.venv/bin/pip install chromadb")
            console.print("    • Or from repo: pip install chromadb (in your venv)")
            console.print()
        else:
            try:
                chroma_proc = subprocess.Popen(
                    chroma_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                chroma_check = _wait_for_service(health.check_chroma_server)
                if chroma_check.running:
                    print_success(f"ChromaDB started ({settings.chroma_host}:{settings.chroma_port})")
                else:
                    print_error("ChromaDB failed to start")
                    console.print()
                    console.print("  [dim]To fix:[/dim]")
                    console.print(f"    • Try manually: chroma run --host {settings.chroma_host} --port {settings.chroma_port}")
                    console.print("    • Run [bold]memex doctor[/bold] for full diagnostics")
                    console.print()
            except FileNotFoundError:
                print_error("ChromaDB command not found")
                console.print()
                console.print("  [dim]To fix: ./install.sh or ~/.memex/.venv/bin/pip install chromadb[/dim]")
                console.print()
    elif chroma_check.running:
        print_success(f"ChromaDB already running ({settings.chroma_host}:{settings.chroma_port})")

    # Start MCP server if requested (before capture so it runs in both foreground/background)
    if start_mcp:
        mcp_running, mcp_pid = mcp_svc.is_running()
        if mcp_running:
            console.print(f"  [{COLORS['muted']}]○[/] MCP server already running (pid {mcp_pid})")
        else:
            success, message = mcp_svc.start()
            if success:
                mcp_verify = _wait_for_service(health.check_mcp_server)
                if mcp_verify.running:
                    print_success(f"MCP server started - connect Claude/Cursor to port {settings.mcp_http_port}")
                else:
                    print_warning("MCP server process started but is not responding on port 8082")
                    console.print()
                    console.print("  [dim]The server may have crashed. Common fixes:[/dim]")
                    console.print("    • Install uv and run: cd mcp-server && uv sync (ensures fastapi, uvicorn)")
                    console.print("    • Or: pip install -r mcp-server/requirements.txt (use your venv)")
                    console.print("    • Re-run [bold]./install.sh[/bold] to refresh ~/.memex (if using install)")
                    console.print("    • Run [bold]memex doctor[/bold] for full diagnostics")
                    console.print()
            else:
                print_error(f"MCP server failed: {message}")
                console.print()
                console.print("  [dim]To fix:[/dim]")
                console.print("    • Ensure mcp-server is installed: ~/.memex/mcp-server/ or repo mcp-server/")
                console.print("    • Install deps: pip install -r mcp-server/requirements.txt")
                console.print("    • Run [bold]memex doctor[/bold] for diagnostics")
                console.print()

    # Start capture process
    console.print(f"  [{COLORS['muted']}]○[/] Starting screen capture...")

    if foreground:
        # Run in foreground - blocking
        print_success("Screen capture starting in foreground")
        console.print()
        console.print("  [dim]Press Ctrl+C to stop[/dim]")
        console.print()

        success, message = capture.start(foreground=True)
        if not success:
            print_error(message)
    else:
        # Run in background
        success, message = capture.start(foreground=False)
        if success:
            time.sleep(1)
            capture_running, capture_pid = capture.is_running()
            if capture_running:
                print_success(f"Screen capture started ({message})")

                # Get screen info
                screens = health.get_unique_screens()
                if screens:
                    print_success(f"Monitoring {len(screens)} screens")
                else:
                    print_success("Monitoring screens (will detect on first capture)")

                console.print()
                console.print("  Memex is now recording. Run [bold]memex status[/bold] to check.")
            else:
                print_warning("Screen capture process exited immediately")
                console.print()
                console.print("  [dim]Possible causes:[/dim]")
                console.print("    • Missing Tesseract: brew install tesseract (macOS)")
                console.print("    • Screen Recording permission: System Settings → Privacy & Security")
                console.print(f"    • Check refinery path: {settings.refinery_path}")
                console.print("    • Run [bold]memex doctor[/bold] for full diagnostics")
                console.print()
        else:
            print_error(f"Failed to start: {message}")
            console.print()
            console.print("  [dim]Run [bold]memex doctor[/bold] for diagnostics and fix suggestions.[/dim]")
            console.print()

    console.print()
