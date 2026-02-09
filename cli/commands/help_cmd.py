"""Help command - extended help with contact info and GitHub links."""

from rich.console import Console
from rich.panel import Panel

from cli.display.components import print_header

console = Console()

GITHUB_PR_URL = "https://github.com/joenewbry/memex/pulls"
CONTACT_EMAIL = "joenewbry+memex@gmail.com"


def help_cmd():
    """Show extended help with contact info and GitHub PRs link."""
    print_header("Help")

    content = f"""  Commands:
    status    Quick health check
    doctor    Full system diagnostics
    stats     Activity statistics
    chat      Interactive chat with Memex
    ask       AI-powered search (streaming)
    search    Direct text search
    start     Start capture daemon (optionally MCP server)
    stop      Stop capture daemon
    watch     Live capture view
    auth      Manage API keys (Anthropic, OpenAI, Grok)
    config    View/edit settings
    sync      Sync files to database
    contact   Contact information

  GitHub PRs: {GITHUB_PR_URL}
  A good place to look to see if anything is broken or currently being worked on.
  We ❤️ people that open PRs to fix issues!

  For support: {CONTACT_EMAIL}

  Troubleshooting:
    ChromaDB terminal stuck? Run [bold]memex stop --stop-chroma[/bold] in another terminal.
    MCP server won't start? Run [bold]cd mcp-server && uv sync[/bold] then retry.
"""
    console.print(content)
    console.print()
