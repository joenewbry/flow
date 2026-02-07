"""Chat command - interactive chat with Memex."""

from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from cli.display.components import print_header
from cli.display.colors import COLORS
from cli.services.ai import AIService
from cli.commands.ask import (
    format_tool_call,
    format_tool_result,
    CHAT_GREETING,
)

console = Console()


def chat():
    """Start an interactive chat session with Memex."""
    print_header("Chat")

    ai = AIService()

    if not ai.is_configured():
        console.print(f"  [{COLORS['error']}]✗[/] No AI provider configured")
        console.print()
        console.print("  To chat with Memex, configure an API key first:")
        console.print("    [bold]memex auth login[/bold]")
        console.print()
        console.print("  Supports: Anthropic (Claude), OpenAI (GPT-4), or Grok (xAI)")
        console.print()
        return

    provider_name = ai.get_provider_name()
    console.print(f"  [dim]Using {provider_name}[/dim]")
    console.print()
    console.print(f"  [bold]{CHAT_GREETING}[/bold]")
    console.print()
    console.print("  [dim]Type 'quit' or 'exit' to end the chat.[/dim]")
    console.print()

    while True:
        try:
            query = console.input(f"  [{COLORS['primary']}]>[/] ").strip()

            if not query:
                continue

            if query.lower() in ["quit", "exit", "q"]:
                console.print("  [dim]Goodbye![/dim]")
                break

            console.print()

            for event in ai.chat_stream(query):
                if event.type == "text":
                    console.print(event.content, end="")
                elif event.type == "tool_call":
                    console.print()
                    console.print(format_tool_call(event.tool_call))
                elif event.type == "tool_result" and event.tool_call:
                    console.print(format_tool_result(event.tool_call.name, event.tool_result or ""))
                    console.print()
                elif event.type == "error":
                    console.print(f"  [{COLORS['error']}]Error:[/] {event.content}")

            console.print()
            console.print()

        except KeyboardInterrupt:
            console.print()
            console.print("  [dim]Goodbye![/dim]")
            break
        except EOFError:
            break

    console.print()
