"""Help command - categorized help with quick start and troubleshooting."""

from rich.console import Console

from cli.display.components import print_header
from cli.display.colors import COLORS

console = Console()

GITHUB_URL = "https://github.com/joenewbry/memex"
GITHUB_PR_URL = "https://github.com/joenewbry/memex/pulls"
CONTACT_EMAIL = "joenewbry+memex@gmail.com"


def help_cmd():
    """Show categorized help with quick start guide."""
    print_header("Help")

    console.print("  [bold]Quick Start[/bold]")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print("  1. Run [bold]memex auth login[/bold] to set your API key")
    console.print("  2. Run [bold]memex start[/bold] to begin capturing")
    console.print("  3. Run [bold]memex chat[/bold] to talk to your memory")
    console.print("  4. Run [bold]memex status[/bold] to check everything works")
    console.print()

    console.print("  [bold]Memory & Search[/bold]")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print(f"  [bold]chat[/bold]      Interactive chat with your memory")
    console.print(f"  [bold]ask[/bold]       One-shot AI question (streaming)")
    console.print(f"  [bold]search[/bold]    Direct text search (no AI, instant)")
    console.print(f"  [bold]stats[/bold]     Activity statistics and word counts")
    console.print(f"  [bold]logs[/bold]      View capture logs")
    console.print()

    console.print("  [bold]System[/bold]")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print(f"  [bold]start[/bold]     Start capture daemon (+ optional MCP)")
    console.print(f"  [bold]stop[/bold]      Stop capture daemon")
    console.print(f"  [bold]status[/bold]    Quick health check")
    console.print(f"  [bold]doctor[/bold]    Full system diagnostics")
    console.print(f"  [bold]watch[/bold]     Live capture view")
    console.print(f"  [bold]sync[/bold]      Sync files to database")
    console.print()

    console.print("  [bold]Configuration[/bold]")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print(f"  [bold]auth[/bold]      Manage API keys (Anthropic, OpenAI, Grok)")
    console.print(f"  [bold]config[/bold]    View/edit settings")
    console.print()

    console.print("  [bold]Example Questions[/bold]")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print(f"  [dim]\"What was I working on yesterday?\"[/dim]")
    console.print(f"  [dim]\"Find any URLs I visited today\"[/dim]")
    console.print(f"  [dim]\"Summarize my activity this week\"[/dim]")
    console.print(f"  [dim]\"Generate a standup update from my activity\"[/dim]")
    console.print()

    console.print("  [bold]Troubleshooting[/bold]")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print(f"  ChromaDB stuck?   [bold]memex stop --stop-chroma[/bold]")
    console.print(f"  MCP won't start?  [bold]cd mcp-server && uv sync[/bold]")
    console.print(f"  DB out of date?   [bold]memex sync[/bold]")
    console.print()

    console.print(f"  [dim]GitHub:[/dim]  {GITHUB_URL}")
    console.print(f"  [dim]PRs:[/dim]    {GITHUB_PR_URL}")
    console.print(f"  [dim]Support:[/dim] {CONTACT_EMAIL}")
    console.print()


def print_chat_help():
    """Print in-chat help showing slash commands and example queries."""
    console.print()
    console.print("  [bold]Slash Commands[/bold]")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print(f"  [bold]/help[/bold]           Show this help")
    console.print(f"  [bold]/status[/bold]         Quick health check")
    console.print(f"  [bold]/stats[/bold]          Today's capture count and words")
    console.print(f"  [bold]/search <query>[/bold] Search without AI (instant)")
    console.print(f"  [bold]/clear[/bold]          Clear conversation and screen")
    console.print(f"  [bold]/tips[/bold]           Show a random tip")
    console.print()
    console.print("  [bold]Try Asking[/bold]")
    console.print(f"  [dim]{'─' * 45}[/dim]")
    console.print(f"  [dim]\"What was I working on yesterday?\"[/dim]")
    console.print(f"  [dim]\"Find any URLs I visited today\"[/dim]")
    console.print(f"  [dim]\"Summarize my activity this week\"[/dim]")
    console.print(f"  [dim]\"Generate a standup update from my activity\"[/dim]")
    console.print()
    console.print("  [dim]Or just type naturally -- I'll search your memory.[/dim]")
    console.print()
