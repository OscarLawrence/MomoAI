"""
Momo CLI Interface

This module provides the command-line interface for chatting with Momo.
It handles user interaction, displays responses beautifully, and manages
the chat session.
"""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

from .chat import MomoChat
from .personality import momo_personality
from .interactive import InteractiveMomo


console = Console()


class MomoCLI:
    """Command-line interface for chatting with Momo."""

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        self.chat = MomoChat(model=model, host=host)
        self.is_running = False

    async def start_chat_session(self) -> None:
        """Start an interactive chat session with Momo."""

        # Display welcome banner
        self._display_welcome()

        # Try to connect to Ollama
        console.print("\n🔌 Connecting to Ollama...", style="yellow")

        connected = await self.chat.connect()
        if not connected:
            self._display_connection_error()
            return

        console.print("✅ Connected successfully!", style="green")

        # Start new session
        session = self.chat.start_new_session()
        console.print(f"💬 Started chat session: {session.session_id}", style="blue")

        # Display Momo's greeting
        greeting = await self.chat.get_momo_greeting(first_time=True)
        self._display_momo_message(greeting)

        # Start interactive loop
        self.is_running = True
        await self._interactive_loop()

    async def _interactive_loop(self) -> None:
        """Main interactive chat loop."""

        while self.is_running:
            try:
                # Get user input
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ")

                # Handle special commands
                if user_input.lower() in ["/quit", "/exit", "/bye"]:
                    await self._handle_quit()
                    break
                elif user_input.lower() in ["/help", "/?"]:
                    self._display_help()
                    continue
                elif user_input.lower() == "/status":
                    await self._display_status()
                    continue
                elif user_input.lower() == "/clear":
                    console.clear()
                    continue
                elif not user_input.strip():
                    continue

                # Send message to Momo and display response
                await self._handle_user_message(user_input)

            except KeyboardInterrupt:
                await self._handle_quit()
                break
            except EOFError:
                await self._handle_quit()
                break
            except Exception as e:
                console.print(f"\n❌ An error occurred: {e}", style="red")

    async def _handle_user_message(self, message: str) -> None:
        """Handle a user message and display Momo's response."""

        # Show that Momo is thinking
        with console.status("[bold green]Momo is thinking...", spinner="dots"):
            response_text = ""

            # Stream Momo's response
            async for chunk in self.chat.send_message(message, stream=True):
                response_text += chunk

        # Display the complete response
        if response_text:
            self._display_momo_message(response_text)

    def _display_welcome(self) -> None:
        """Display the welcome banner."""

        welcome_text = Text()
        welcome_text.append("🌟 Welcome to ", style="bold white")
        welcome_text.append("Momo AI", style="bold magenta")
        welcome_text.append(" Chat! 🌟", style="bold white")

        subtitle = Text()
        subtitle.append("Your warm, intelligent AI assistant", style="italic cyan")

        panel = Panel(
            Text.assemble(welcome_text, "\n", subtitle),
            title="Momo AI",
            border_style="magenta",
            padding=(1, 2),
        )

        console.print(panel)
        console.print("\n💡 Type '/help' for commands or just start chatting!", style="dim")

    def _display_momo_message(self, message: str) -> None:
        """Display a message from Momo with nice formatting."""

        # Create Momo's response panel
        momo_text = Text()
        momo_text.append("🤖 Momo: ", style="bold magenta")

        # Try to render as markdown for better formatting
        try:
            markdown = Markdown(message)
            console.print("\n")
            console.print(momo_text)
            console.print(markdown)
        except Exception:
            # Fallback to plain text
            console.print(f"\n🤖 [bold magenta]Momo:[/bold magenta] {message}")

    def _display_connection_error(self) -> None:
        """Display connection error information."""

        error_panel = Panel(
            Text.assemble(
                "❌ ",
                ("Connection Failed", "bold red"),
                "\n\n",
                "I couldn't connect to Ollama. Please make sure:\n",
                "• Ollama is installed and running\n",
                "• Ollama is accessible at the default port (11434)\n",
                "• You have at least one model installed\n\n",
                ("Quick setup:", "bold"),
                "\n",
                "1. Install Ollama: https://ollama.ai\n",
                "2. Run: ollama pull llama3.2\n",
                "3. Start Ollama service\n",
                "4. Try running 'momo' again",
            ),
            title="Connection Error",
            border_style="red",
            padding=(1, 2),
        )

        console.print(error_panel)

    def _display_help(self) -> None:
        """Display help information."""

        help_text = Text.assemble(
            ("Available Commands:", "bold cyan"),
            "\n\n",
            ("Chat Commands:", "bold"),
            "\n",
            "• Just type your message and press Enter\n",
            "• Ask me about MomoAI, development, or anything else!\n\n",
            ("Special Commands:", "bold"),
            "\n",
            "• /help or /? - Show this help\n",
            "• /status - Show connection and session status\n",
            "• /clear - Clear the screen\n",
            "• /quit, /exit, /bye - End the chat\n",
            "• Ctrl+C - Quick exit\n\n",
            ("CLI Commands:", "bold"),
            "\n",
            "• momo models - List available and recommended models\n",
            "• momo install <model> - Install a new model\n",
            "• momo status - Check Ollama connection\n",
            "• momo chat --auto - Auto-select best model\n\n",
            ("About Momo:", "bold"),
            "\n",
            "I'm your AI assistant, named after the developer's daughter.\n",
            "I'm here to help with MomoAI system questions, development,\n",
            "and provide warm, intelligent assistance!",
        )

        help_panel = Panel(help_text, title="Momo Chat Help", border_style="cyan", padding=(1, 2))

        console.print(help_panel)

    async def _display_status(self) -> None:
        """Display current status information."""

        # Get Ollama status
        ollama_status = await self.chat.check_ollama_status()

        # Get session info
        session_info = self.chat.get_session_summary()

        status_text = Text()

        # Connection status
        if ollama_status["connected"]:
            status_text.append("🟢 Connected to Ollama\n", style="green")
        else:
            status_text.append("🔴 Not connected to Ollama\n", style="red")
            if ollama_status["error"]:
                status_text.append(f"   Error: {ollama_status['error']}\n", style="red")

        # Model info
        status_text.append(f"🤖 Current model: {ollama_status['current_model']}\n")

        # Available models
        if ollama_status["available_models"]:
            status_text.append(
                f"📚 Available models: {', '.join(ollama_status['available_models'])}\n"
            )

        # Session info
        if session_info.get("session_id"):
            status_text.append(f"\n💬 Session: {session_info['session_id']}\n")
            status_text.append(f"📝 Messages: {session_info['message_count']}\n")
            status_text.append(f"⏰ Started: {session_info['created_at']}\n")

        status_panel = Panel(status_text, title="Momo Status", border_style="blue", padding=(1, 2))

        console.print(status_panel)

    async def _handle_quit(self) -> None:
        """Handle quit command."""

        farewell = self.chat.get_momo_farewell()
        self._display_momo_message(farewell)

        self.is_running = False
        console.print("\nGoodbye! 👋", style="bold cyan")


@click.group()
def cli() -> None:
    """Momo AI Chat Interface - Talk to your warm, intelligent AI assistant."""
    pass


@cli.command()
@click.option(
    "--model",
    default=None,
    help="Ollama model to use (auto-selects if not specified)",
)
@click.option("--host", default="http://localhost:11434", help="Ollama host URL", show_default=True)
def interactive(model: Optional[str], host: str) -> None:
    """Start interactive Momo terminal with auto-completion and in-chat commands."""
    
    async def run_interactive():
        momo_terminal = InteractiveMomo(model=model, host=host)
        await momo_terminal.start()
    
    try:
        asyncio.run(run_interactive())
    except KeyboardInterrupt:
        console.print("\n\nGoodbye! 👋", style="bold cyan")
    except Exception as e:
        console.print(f"\n❌ An unexpected error occurred: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option(
    "--model",
    default=None,
    help="Ollama model to use for chat (if not specified, will prompt to select)",
)
@click.option("--host", default="http://localhost:11434", help="Ollama host URL", show_default=True)
@click.option(
    "--auto", is_flag=True, help="Automatically select best available model without prompting"
)
def chat(model: Optional[str], host: str, auto: bool) -> None:
    """Start an interactive chat session with Momo."""

    async def select_model() -> Optional[str]:
        """Select the best available model."""
        temp_chat = MomoChat(host=host)
        status_info = await temp_chat.check_ollama_status()

        if not status_info["connected"]:
            console.print("❌ Cannot connect to Ollama", style="red")
            if status_info["error"]:
                console.print(f"Error: {status_info['error']}", style="red")
            return None

        available_models = status_info["available_models"]
        if not available_models:
            console.print("❌ No models available in Ollama", style="red")
            console.print("Install a model with: ollama pull llama3.2", style="dim")
            return None

        # If specific model requested and available, use it
        if model and model in available_models:
            return model

        # If specific model requested but not available, inform user
        if model and model not in available_models:
            console.print(f"⚠️  Model '{model}' not found locally", style="yellow")
            console.print(f"Available models: {', '.join(available_models)}", style="dim")

        # Auto-select best model
        if auto or model:
            # Preference order for auto-selection
            preferred_order = [
                "llama3.2",
                "llama3.2:latest",
                "llama3.2:3b",
                "llama3.1",
                "llama3.1:latest",
                "llama3.1:8b",
                "llama3",
                "llama3:latest",
                "llama3:8b",
                "mistral",
                "mistral:latest",
                "phi3",
                "phi3:latest",
                "gemma2",
                "gemma2:latest",
            ]

            for preferred in preferred_order:
                if preferred in available_models:
                    if model:  # Was looking for specific model
                        console.print(f"Using '{preferred}' instead", style="green")
                    return preferred

            # Fallback to first available model
            selected = available_models[0]
            if model:  # Was looking for specific model
                console.print(f"Using '{selected}' instead", style="green")
            return selected

        # Interactive model selection
        console.print("\n🤖 Select a model for your chat session:", style="bold cyan")
        for i, model_name in enumerate(available_models, 1):
            console.print(f"  {i}. {model_name}", style="green")

        console.print("\n💡 Tip: Use --auto to automatically select the best model", style="dim")

        while True:
            try:
                choice = console.input(
                    "\nEnter your choice (1-{0}) or model name: ".format(len(available_models))
                )
                choice = choice.strip()

                # Check if it's a number
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_models):
                        return available_models[idx]
                    else:
                        console.print(
                            f"Please enter a number between 1 and {len(available_models)}",
                            style="red",
                        )
                        continue

                # Check if it's a model name
                if choice in available_models:
                    return choice

                console.print(
                    f"'{choice}' not found. Please select from the available models.", style="red"
                )

            except KeyboardInterrupt:
                console.print("\nCancelled model selection", style="yellow")
                return None

    async def run_chat():
        # Select model if needed
        selected_model = await select_model() if not model else model
        if selected_model is None:
            return

        momo_cli = MomoCLI(model=selected_model, host=host)
        await momo_cli.start_chat_session()

    try:
        asyncio.run(run_chat())
    except KeyboardInterrupt:
        console.print("\n\nGoodbye! 👋", style="bold cyan")
    except Exception as e:
        console.print(f"\n❌ An unexpected error occurred: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--host", default="http://localhost:11434", help="Ollama host URL", show_default=True)
def status(host: str) -> None:
    """Check Ollama connection status and available models."""

    async def check_status():
        chat = MomoChat(host=host)
        status_info = await chat.check_ollama_status()

        if status_info["connected"]:
            console.print("✅ Ollama is running and accessible", style="green")
            console.print(f"🌐 Host: {status_info['host']}")
            console.print(f"📚 Available models: {', '.join(status_info['available_models'])}")
        else:
            console.print("❌ Cannot connect to Ollama", style="red")
            if status_info["error"]:
                console.print(f"Error: {status_info['error']}", style="red")

    try:
        asyncio.run(check_status())
    except Exception as e:
        console.print(f"❌ Error checking status: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option("--host", default="http://localhost:11434", help="Ollama host URL", show_default=True)
@click.option("--detailed", is_flag=True, help="Show detailed model information")
def models(host: str, detailed: bool) -> None:
    """List available local models and popular models to install."""

    async def list_models():
        chat = MomoChat(host=host)
        status_info = await chat.check_ollama_status()

        if status_info["connected"]:
            console.print("📚 Local Models Available:", style="bold cyan")

            if detailed:
                # Get detailed model info
                try:
                    client = chat.client
                    models_response = await asyncio.wait_for(
                        asyncio.to_thread(client.list), timeout=5.0
                    )

                    for model in models_response.get("models", []):
                        model_name = model.get("name", model.get("model", "Unknown"))
                        size_bytes = model.get("size", 0)
                        size_gb = size_bytes / (1024**3) if size_bytes > 0 else 0
                        modified = model.get("modified_at", "Unknown")

                        console.print(f"  • {model_name}", style="green")
                        console.print(f"    Size: {size_gb:.1f} GB", style="dim")
                        if modified != "Unknown":
                            console.print(
                                f"    Modified: {modified.strftime('%Y-%m-%d %H:%M')}", style="dim"
                            )

                        details = model.get("details", {})
                        if details:
                            family = details.get("family", "Unknown")
                            param_size = details.get("parameter_size", "Unknown")
                            console.print(
                                f"    Family: {family}, Parameters: {param_size}", style="dim"
                            )
                        console.print()

                except Exception as e:
                    console.print(f"Error getting detailed info: {e}", style="red")
                    for model_name in status_info["available_models"]:
                        console.print(f"  • {model_name}", style="green")
            else:
                for model_name in status_info["available_models"]:
                    console.print(f"  • {model_name}", style="green")

            console.print(f"\n🎯 Recommended Models to Install:", style="bold yellow")
            recommended = [
                ("llama3.2", "Fast and capable 3B model, great for general chat"),
                ("llama3.2:1b", "Ultra-fast 1B model for quick responses"),
                ("codellama", "Specialized for code generation and assistance"),
                ("mistral", "Excellent reasoning and instruction following"),
                ("phi3", "Compact but powerful 3.8B model"),
                ("gemma2", "Google's efficient and capable model"),
            ]

            for model, description in recommended:
                if model not in status_info["available_models"]:
                    console.print(f"  • {model}", style="blue")
                    console.print(f"    {description}", style="dim")
                else:
                    console.print(f"  ✅ {model} (already installed)", style="dim green")
                    console.print(f"    {description}", style="dim")

            console.print(f"\n💡 Install a model with: ollama pull <model-name>", style="dim")

        else:
            console.print("❌ Cannot connect to Ollama", style="red")
            if status_info["error"]:
                console.print(f"Error: {status_info['error']}", style="red")

    try:
        asyncio.run(list_models())
    except Exception as e:
        console.print(f"❌ Error listing models: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.argument("model_name")
@click.option("--host", default="http://localhost:11434", help="Ollama host URL", show_default=True)
def install(model_name: str, host: str) -> None:
    """Install a model via Ollama."""

    async def install_model():
        console.print(f"📥 Installing model '{model_name}'...", style="yellow")

        try:
            # Initialize Ollama client
            import ollama

            client = ollama.Client(host=host)

            # Start installation with progress tracking
            with console.status(f"[bold yellow]Pulling {model_name}...", spinner="dots"):
                # Run pull in thread to avoid blocking
                await asyncio.wait_for(
                    asyncio.to_thread(client.pull, model_name),
                    timeout=300.0,  # 5 minute timeout for model downloads
                )

            console.print(f"✅ Successfully installed '{model_name}'", style="green")
            console.print(f"💬 Start chatting with: momo chat --model {model_name}", style="cyan")

        except asyncio.TimeoutError:
            console.print(f"❌ Installation timed out for '{model_name}'", style="red")
            console.print(
                "Try installing manually: ollama pull {0}".format(model_name), style="dim"
            )
        except Exception as e:
            console.print(f"❌ Failed to install '{model_name}': {e}", style="red")
            console.print(
                "Try installing manually: ollama pull {0}".format(model_name), style="dim"
            )

    try:
        asyncio.run(install_model())
    except KeyboardInterrupt:
        console.print(f"\n❌ Installation of '{model_name}' was cancelled", style="yellow")
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        sys.exit(1)


@cli.command()
def info() -> None:
    """Show information about Momo and the MomoAI system."""

    info_text = Text.assemble(
        ("About Momo:", "bold magenta"),
        "\n",
        momo_personality.identity_summary,
        "\n\n",
        ("Key Capabilities:", "bold cyan"),
        "\n",
    )

    for capability, description in momo_personality.capabilities.items():
        info_text.append(f"• {capability.replace('_', ' ').title()}: {description}\n")

    info_text.append("\n")
    info_text.append("MomoAI System:", style="bold green")
    info_text.append("\n")

    system_info = momo_personality.momoai_system_info
    info_text.append(f"Architecture: {system_info['architecture']['type']}\n")
    info_text.append("Components:\n")

    for component in system_info["architecture"]["components"]:
        info_text.append(f"  • {component}\n")

    info_panel = Panel(
        info_text, title="Momo AI Information", border_style="magenta", padding=(1, 2)
    )

    console.print(info_panel)


def main() -> None:
    """Main entry point for the Momo CLI."""

    # If no command is provided, default to interactive
    if len(sys.argv) == 1:
        sys.argv.append("interactive")

    cli()


if __name__ == "__main__":
    main()
