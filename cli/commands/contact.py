"""Contact command - display support contact information."""

from rich.console import Console

from cli.display.components import print_header

console = Console()

CONTACT_EMAIL = "joenewbry+memex@gmail.com"


def contact():
    """Display contact information for support."""
    print_header("Contact")
    console.print()
    console.print(f"  To get help please contact {CONTACT_EMAIL}")
    console.print()
