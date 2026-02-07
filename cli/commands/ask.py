"""Ask command - AI-powered search with streaming and tool calls."""

import sys
from typing import Optional
import typer
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from rich.spinner import Spinner

from cli.display.components import print_header
from cli.display.colors import COLORS
from cli.services.ai import AIService, StreamEvent, ToolCall

console = Console()


def format_tool_call(tool_call: ToolCall) -> Panel:
    """Format a tool call for display."""
    args_str = ", ".join(f"{k}={repr(v)}" for k, v in tool_call.arguments.items())
    content = Text()
    content.append("", style=f"bold {COLORS['primary']}")
    content.append(f"{tool_call.name}", style="bold")
    content.append(f"({args_str})", style="dim")

    return Panel(
        content,
        title="[dim]Tool Call[/dim]",
        title_align="left",
        border_style="dim",
        padding=(0, 1),
    )


def format_tool_result(tool_name: str, result: str, collapsed: bool = True) -> Panel:
    """Format a tool result for display."""
    if collapsed:
        # Show truncated result
        lines = result.strip().split("\n")
        if len(lines) > 3:
            preview = "\n".join(lines[:3]) + f"\n... ({len(lines) - 3} more lines)"
        else:
            preview = result.strip()
        content = Text(preview, style="dim")
    else:
        content = Text(result.strip())

    return Panel(
        content,
        title=f"[dim]{tool_name} result[/dim]",
        title_align="left",
        border_style="dim",
        padding=(0, 1),
    )


def ask(
    query: str = typer.Argument(..., help="Your question about your screen history"),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="AI provider (anthropic or openai)"
    ),
    show_tools: bool = typer.Option(
        True, "--show-tools/--hide-tools", help="Show tool calls"
    ),
    raw: bool = typer.Option(
        False, "--raw", help="Show raw output without formatting"
    ),
):
    """Ask a question about your screen history using AI.

    Examples:
        memex ask "What was I working on yesterday?"
        memex ask "Find any mentions of the API bug"
        memex ask "Summarize my activity this week"
    """
    ai = AIService()

    if not ai.is_configured():
        console.print()
        console.print(f"  [{COLORS['error']}]✗[/] No AI provider configured")
        console.print()
        console.print("  To get started, run:")
        console.print("    [bold]memex auth login[/bold]")
        console.print()
        console.print("  This will let you configure an Anthropic or OpenAI API key.")
        console.print()
        return

    provider_name = ai.get_provider_name()

    if not raw:
        console.print()
        console.print(f"  [dim]Using {provider_name}...[/dim]")
        console.print()

    # Track state for display
    response_text = ""
    tool_panels = []

    def on_tool_call(tc: ToolCall):
        if show_tools and not raw:
            console.print(format_tool_call(tc))

    def on_tool_result(name: str, result: str):
        if show_tools and not raw:
            console.print(format_tool_result(name, result))
            console.print()

    # Stream the response
    if raw:
        # Simple streaming without formatting
        for event in ai.chat_stream(query, on_tool_call, on_tool_result):
            if event.type == "text":
                sys.stdout.write(event.content)
                sys.stdout.flush()
            elif event.type == "error":
                console.print(f"Error: {event.content}", style="red")
        print()
    else:
        # Rich streaming with live updates
        response_started = False

        for event in ai.chat_stream(query, on_tool_call, on_tool_result):
            if event.type == "text":
                if not response_started:
                    response_started = True
                # Print text as it streams
                console.print(event.content, end="")
                response_text += event.content

            elif event.type == "error":
                console.print()
                console.print(f"  [{COLORS['error']}]✗[/] {event.content}")
                console.print()
                return

            elif event.type == "done":
                pass

        # Final newline
        if response_started:
            console.print()
            console.print()


# Create a typer app for potential subcommands
app = typer.Typer(help="AI-powered search")


@app.callback(invoke_without_command=True)
def ask_callback(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Your question"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p"),
    show_tools: bool = typer.Option(True, "--show-tools/--hide-tools"),
    raw: bool = typer.Option(False, "--raw"),
):
    """Ask a question about your screen history."""
    if ctx.invoked_subcommand is not None:
        return

    if query:
        ask(query, provider, show_tools, raw)
    else:
        # Interactive mode
        interactive_chat()


CHAT_GREETING = """How can I help? I can find URLs, summarize your day, generate a response to an email using my context.

And if you need anything contact joenewbry+memex@gmail.com."""


def interactive_chat():
    """Run an interactive chat session."""
    console.print()
    console.print("  [bold]Memex AI Chat[/bold]")
    console.print(f"  [bold]{CHAT_GREETING}[/bold]")
    console.print()
    console.print("  [dim]Type 'quit' or 'exit' to end the chat.[/dim]")
    console.print()

    ai = AIService()

    if not ai.is_configured():
        console.print(f"  [{COLORS['error']}]✗[/] No AI provider configured")
        console.print("  Run 'memex auth login' first.")
        console.print()
        return

    provider_name = ai.get_provider_name()
    console.print(f"  [dim]Using {provider_name}[/dim]")
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

            # Stream response
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
