"""Product Search Agent — Main entry point."""

import sys
from rich.console import Console
from agent.product_agent import ProductSearchAgent
from utils import print_welcome, print_tool_call, print_response, print_error
from config import GROQ_API_KEY, ZENSERP_API_KEY

console = Console()


def check_config():
    """Verify required API keys are configured."""
    if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
        print_error(
            "GROQ_API_KEY not set. Add your key to .env file.\n"
            "Get a free key at: https://console.groq.com/keys"
        )
        sys.exit(1)
    if not ZENSERP_API_KEY:
        console.print(
            "[yellow]Warning: ZENSERP_API_KEY not set. "
            "DuckDuckGo search will be used as fallback.[/yellow]\n"
        )


def main():
    """Run the interactive product search agent."""
    check_config()
    print_welcome()

    agent = ProductSearchAgent()

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        if user_input.lower() == "reset":
            agent.reset()
            console.print("[dim]Conversation reset.[/dim]\n")
            continue

        console.print("\n[bold cyan]Agent:[/bold cyan] Researching your query...\n")

        try:
            response = agent.chat(user_input, on_tool_call=print_tool_call)
            print_response(response)
        except Exception as e:
            print_error(str(e))


if __name__ == "__main__":
    main()
