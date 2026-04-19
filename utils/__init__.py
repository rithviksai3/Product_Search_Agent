"""Utility functions for displaying results in the terminal."""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

console = Console()


def print_welcome():
    """Print welcome banner."""
    console.print(
        Panel(
            Text.from_markup(
                "[bold cyan]🛒 Product Search Agent[/bold cyan]\n\n"
                "[dim]I'll help you find the best products by searching across\n"
                "e-commerce platforms, comparing prices, and gathering reviews.[/dim]\n\n"
                "[yellow]Type your product query (e.g., 'best wireless earbuds under $100')\n"
                "Type 'quit' or 'exit' to stop. Type 'reset' to start fresh.[/yellow]"
            ),
            title="Welcome",
            border_style="cyan",
        )
    )


def print_tool_call(tool_name: str, arguments: dict):
    """Print a tool call notification."""
    tool_labels = {
        "find_trending_products": "🔍 Finding trending products",
        "extract_brands_and_models": "🏷️  Extracting top brands & models",
        "search_products_on_ecommerce": "🛍️  Searching e-commerce sites",
        "search_google_shopping": "🛒 Searching Google Shopping",
        "compare_prices": "💰 Comparing prices across platforms",
        "get_product_reviews": "⭐ Fetching product reviews & ratings",
        "get_expert_reviews": "📝 Fetching expert reviews",
    }
    label = tool_labels.get(tool_name, f"🔧 Calling {tool_name}")
    query = arguments.get("product_query") or arguments.get("product_name", "")
    specs = arguments.get("specifications", "")

    detail = query
    if specs:
        detail += f" ({specs})"

    console.print(f"  [dim]{label}: {detail}[/dim]")


def print_response(response: str):
    """Print the agent's response as formatted markdown."""
    console.print()
    console.print(Markdown(response))
    console.print()


def print_error(message: str):
    """Print an error message."""
    console.print(f"[red]Error: {message}[/red]")
