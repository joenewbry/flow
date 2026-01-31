"""Auth command - configure API keys for AI providers."""

from typing import Optional
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

from cli.display.components import print_header, print_success, print_error
from cli.display.colors import COLORS
from cli.config.credentials import (
    save_api_key,
    get_api_key,
    delete_api_key,
    get_configured_providers,
    get_default_provider,
)
from cli.config import get_settings

console = Console()

app = typer.Typer(help="Manage API key authentication")


PROVIDER_INFO = {
    "anthropic": {
        "name": "Anthropic",
        "url": "https://console.anthropic.com/settings/keys",
        "env_var": "ANTHROPIC_API_KEY",
        "prefix": "sk-ant-",
    },
    "openai": {
        "name": "OpenAI",
        "url": "https://platform.openai.com/api-keys",
        "env_var": "OPENAI_API_KEY",
        "prefix": "sk-",
    },
}


@app.callback(invoke_without_command=True)
def auth(ctx: typer.Context):
    """View authentication status."""
    if ctx.invoked_subcommand is not None:
        return

    print_header("Authentication")

    configured = get_configured_providers()
    default = get_default_provider()

    if not configured:
        console.print("  No API keys configured.")
        console.print()
        console.print("  [dim]To add an API key, run:[/dim]")
        console.print("    memex auth login")
        console.print()
        return

    # Show configured providers
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Provider", style="bold")
    table.add_column("Status")
    table.add_column("Key")

    for provider in ["anthropic", "openai"]:
        info = PROVIDER_INFO[provider]
        key = get_api_key(provider)

        if key:
            # Mask the key
            masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
            status = f"[{COLORS['success']}]●[/] Configured"
            if provider == default:
                status += " (default)"
        else:
            masked = "-"
            status = f"[dim]○ Not configured[/dim]"

        table.add_row(info["name"], status, f"[dim]{masked}[/dim]")

    console.print(table)
    console.print()
    console.print("  [dim]Commands: memex auth login, memex auth logout[/dim]")
    console.print()


@app.command("login")
def auth_login(
    provider: Optional[str] = typer.Argument(
        None, help="Provider to configure (anthropic or openai)"
    ),
):
    """Configure an API key."""
    print_header("Login")

    # If no provider specified, show menu
    if provider is None:
        console.print("  Select a provider:")
        console.print()
        console.print("    [bold]1.[/bold] Anthropic (Claude)")
        console.print("        [dim]Get key: https://console.anthropic.com/settings/keys[/dim]")
        console.print()
        console.print("    [bold]2.[/bold] OpenAI (GPT-4)")
        console.print("        [dim]Get key: https://platform.openai.com/api-keys[/dim]")
        console.print()

        choice = Prompt.ask("  Enter choice", choices=["1", "2", "anthropic", "openai"])
        provider = "anthropic" if choice in ["1", "anthropic"] else "openai"

    provider = provider.lower()
    if provider not in PROVIDER_INFO:
        print_error(f"Unknown provider: {provider}")
        console.print("  [dim]Valid providers: anthropic, openai[/dim]")
        return

    info = PROVIDER_INFO[provider]
    console.print()
    console.print(f"  Configuring [bold]{info['name']}[/bold]")
    console.print(f"  [dim]Get your API key at: {info['url']}[/dim]")
    console.print()

    # Check if already configured
    existing = get_api_key(provider)
    if existing:
        masked = existing[:8] + "..." + existing[-4:]
        console.print(f"  [dim]Current key: {masked}[/dim]")
        if not Confirm.ask("  Replace existing key?", default=False):
            console.print("  [dim]Cancelled[/dim]")
            return

    # Get the API key
    api_key = Prompt.ask("  Enter API key", password=True)

    if not api_key:
        print_error("No API key provided")
        return

    # Basic validation
    if provider == "anthropic" and not api_key.startswith("sk-ant-"):
        console.print(f"  [{COLORS['warning']}]![/] Key doesn't start with 'sk-ant-' - are you sure this is an Anthropic key?")
        if not Confirm.ask("  Save anyway?", default=False):
            return

    if provider == "openai" and not api_key.startswith("sk-"):
        console.print(f"  [{COLORS['warning']}]![/] Key doesn't start with 'sk-' - are you sure this is an OpenAI key?")
        if not Confirm.ask("  Save anyway?", default=False):
            return

    # Save the key
    save_api_key(provider, api_key)
    print_success(f"{info['name']} API key saved")

    # Test the key
    console.print()
    console.print("  [dim]Testing connection...[/dim]")

    if test_api_key(provider, api_key):
        print_success("Connection successful!")
    else:
        console.print(f"  [{COLORS['warning']}]![/] Could not verify key (may still be valid)")

    console.print()


@app.command("logout")
def auth_logout(
    provider: Optional[str] = typer.Argument(
        None, help="Provider to remove (anthropic or openai)"
    ),
    all_providers: bool = typer.Option(False, "--all", "-a", help="Remove all API keys"),
):
    """Remove configured API keys."""
    print_header("Logout")

    if all_providers:
        for p in ["anthropic", "openai"]:
            if delete_api_key(p):
                console.print(f"  Removed {PROVIDER_INFO[p]['name']} API key")
        console.print()
        return

    if provider is None:
        configured = get_configured_providers()
        if not configured:
            console.print("  No API keys configured.")
            console.print()
            return

        console.print("  Configured providers:")
        for i, p in enumerate(configured, 1):
            console.print(f"    [bold]{i}.[/bold] {PROVIDER_INFO[p]['name']}")
        console.print()

        choice = Prompt.ask("  Which provider to remove?", choices=[str(i) for i in range(1, len(configured) + 1)] + configured)

        try:
            idx = int(choice) - 1
            provider = configured[idx]
        except (ValueError, IndexError):
            provider = choice

    provider = provider.lower()
    if provider not in PROVIDER_INFO:
        print_error(f"Unknown provider: {provider}")
        return

    if delete_api_key(provider):
        print_success(f"Removed {PROVIDER_INFO[provider]['name']} API key")
    else:
        console.print(f"  [dim]No API key found for {PROVIDER_INFO[provider]['name']}[/dim]")

    console.print()


def test_api_key(provider: str, api_key: str) -> bool:
    """Test if an API key is valid."""
    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            # Make a minimal request
            client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        elif provider == "openai":
            import openai
            client = openai.OpenAI(api_key=api_key)
            client.models.list()
            return True
    except Exception:
        pass
    return False
