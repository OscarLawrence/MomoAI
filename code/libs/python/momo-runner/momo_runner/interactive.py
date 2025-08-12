"""
Interactive Momo Terminal

This module provides an advanced interactive terminal interface for chatting with Momo,
with auto-suggestion, command completion, and inline help similar to Claude Code.
"""

import asyncio
import sys
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn

from .chat import MomoChat
from .personality import momo_personality
from .style import momo_style, RECOMMENDED_MODELS, get_models_by_category


@dataclass
class CommandInfo:
    """Information about a command."""

    name: str
    description: str
    usage: str
    category: str
    examples: List[str]


class MomoCompleter(Completer):
    """Auto-completion for Momo commands and context-aware suggestions."""

    def __init__(self, interactive_session):
        self.session = interactive_session
        self.commands = {
            # Chat commands
            "/help": CommandInfo(
                name="/help",
                description="Show available commands and help",
                usage="/help [command]",
                category="Help",
                examples=["/help", "/help models", "/help download"],
            ),
            "/clear": CommandInfo(
                name="/clear",
                description="Clear the terminal screen",
                usage="/clear",
                category="Interface",
                examples=["/clear"],
            ),
            "/status": CommandInfo(
                name="/status",
                description="Show connection and session status",
                usage="/status",
                category="System",
                examples=["/status"],
            ),
            "/history": CommandInfo(
                name="/history",
                description="Show conversation history",
                usage="/history [count]",
                category="Chat",
                examples=["/history", "/history 10"],
            ),
            # Model management commands
            "/models": CommandInfo(
                name="/models",
                description="List available models",
                usage="/models [--detailed]",
                category="Models",
                examples=["/models", "/models --detailed"],
            ),
            "/model": CommandInfo(
                name="/model",
                description="Switch to a different model",
                usage="/model [model_name]",
                category="Models",
                examples=["/model llama3.2", "/model"],
            ),
            "/download": CommandInfo(
                name="/download",
                description="Download and install a new model",
                usage="/download <model_name>",
                category="Models",
                examples=["/download llama3.2", "/download mistral"],
            ),
            "/remove": CommandInfo(
                name="/remove",
                description="Remove a model from local storage",
                usage="/remove <model_name>",
                category="Models",
                examples=["/remove llama3.2"],
            ),
            "/discover": CommandInfo(
                name="/discover",
                description="Discover and browse recommended models to install",
                usage="/discover [category]",
                category="Models",
                examples=["/discover", "/discover coding", "/discover general"],
            ),
            # Session commands
            "/save": CommandInfo(
                name="/save",
                description="Save current conversation",
                usage="/save [filename]",
                category="Session",
                examples=["/save", "/save my_chat.json"],
            ),
            "/load": CommandInfo(
                name="/load",
                description="Load a saved conversation",
                usage="/load <filename>",
                category="Session",
                examples=["/load my_chat.json"],
            ),
            "/new": CommandInfo(
                name="/new",
                description="Start a new conversation session",
                usage="/new",
                category="Session",
                examples=["/new"],
            ),
            # System commands
            "/quit": CommandInfo(
                name="/quit",
                description="Exit the Momo terminal",
                usage="/quit",
                category="System",
                examples=["/quit", "/exit", "/bye"],
            ),
        }

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Command completion
        if text.startswith("/"):
            for cmd_name, cmd_info in self.commands.items():
                if cmd_name.startswith(text):
                    yield Completion(
                        cmd_name[len(text) :],
                        display=HTML(f"<b>{cmd_name}</b> - {cmd_info.description}"),
                        display_meta=cmd_info.usage,
                    )

        # Model name completion for model commands
        elif (
            text.startswith("/model ")
            or text.startswith("/download ")
            or text.startswith("/remove ")
        ):
            model_prefix = text.split(" ")[-1]
            if hasattr(self.session, "available_models"):
                for model in self.session.available_models:
                    if model.startswith(model_prefix):
                        yield Completion(
                            model[len(model_prefix) :],
                            display=f"{model}",
                            display_meta="Available model",
                        )

        # Category completion for discover command
        elif text.startswith("/discover "):
            category_prefix = text.split(" ")[-1]
            categories = ["general", "coding", "chat"]
            for category in categories:
                if category.startswith(category_prefix):
                    yield Completion(
                        category[len(category_prefix) :],
                        display=f"{category}",
                        display_meta="Model category",
                    )


class InteractiveMomo:
    """Interactive Momo terminal interface with advanced features."""

    def __init__(self, model: Optional[str] = None, host: str = "http://localhost:11434"):
        self.console = Console()
        self.chat = MomoChat(model=model or "auto", host=host)
        self.history = InMemoryHistory()
        self.completer = MomoCompleter(self)
        self.available_models: List[str] = []
        self.is_running = False
        self.current_model = model

        # Create prompt session with styling
        self.session = PromptSession(
            history=self.history,
            completer=self.completer,
            complete_while_typing=True,
            enable_history_search=True,
            style=momo_style,
        )

        # Setup key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()

    def _setup_key_bindings(self):
        """Setup custom key bindings."""

        @self.kb.add("c-c")
        def _(event):
            """Handle Ctrl+C gracefully."""
            event.app.exit(result="quit")

        @self.kb.add("c-d")
        def _(event):
            """Handle Ctrl+D (EOF) gracefully."""
            event.app.exit(result="quit")

    async def start(self) -> None:
        """Start the interactive Momo terminal."""

        # Display startup banner
        self._display_startup_banner()

        # Initialize connection
        if not await self._initialize_connection():
            return

        # Start interactive loop
        self.is_running = True
        await self._interactive_loop()

    def _display_startup_banner(self) -> None:
        """Display the startup banner."""

        banner = Panel(
            Text.assemble(
                ("🌟 ", "bold yellow"),
                ("Welcome to Momo Interactive Terminal", "bold magenta"),
                (" 🌟\n", "bold yellow"),
                (
                    "Your intelligent AI assistant with advanced terminal features\n\n",
                    "italic cyan",
                ),
                ("Features:", "bold white"),
                ("\n• Auto-completion and suggestions", "dim white"),
                ("\n• In-chat model management", "dim white"),
                ("\n• Command history and search", "dim white"),
                ("\n• Rich formatting and help", "dim white"),
                ("\n\nType ", "dim white"),
                ("/help", "bold cyan"),
                (" for commands or just start chatting!", "dim white"),
            ),
            title="Momo AI Interactive",
            border_style="magenta",
            padding=(1, 2),
        )

        self.console.print(banner)

    async def _initialize_connection(self) -> bool:
        """Initialize connection to Ollama."""

        with self.console.status("[bold yellow]🔌 Connecting to Ollama...", spinner="dots"):
            # Auto-select best model if not specified
            if self.current_model is None or self.current_model == "auto":
                status_info = await self.chat.check_ollama_status()
                if not status_info["connected"]:
                    self._display_connection_error(status_info.get("error", "Unknown error"))
                    return False

                self.available_models = status_info["available_models"]
                if not self.available_models:
                    self.console.print(
                        "❌ No models available. Install one with: ollama pull llama3.2",
                        style="red",
                    )
                    return False

                # Select best available model
                preferred = ["llama3.2", "llama3.1", "llama3", "mistral", "phi3", "gemma2"]
                selected_model = None
                for pref in preferred:
                    for available in self.available_models:
                        if available.startswith(pref):
                            selected_model = available
                            break
                    if selected_model:
                        break

                if not selected_model:
                    selected_model = self.available_models[0]

                self.current_model = selected_model
                self.chat.model = selected_model

            # Connect
            connected = await self.chat.connect()
            if not connected:
                self._display_connection_error()
                return False

        # Update available models
        status_info = await self.chat.check_ollama_status()
        self.available_models = status_info.get("available_models", [])

        self.console.print(
            f"✅ Connected! Using model: [bold cyan]{self.current_model}[/bold cyan]"
        )

        # Start session and show greeting
        session = self.chat.start_new_session()
        self.console.print(f"💬 Session started: [dim]{session.session_id}[/dim]")

        greeting = await self.chat.get_momo_greeting(first_time=True)
        self._display_momo_message(greeting)

        return True

    def _display_connection_error(self, error: Optional[str] = None) -> None:
        """Display connection error."""

        error_panel = Panel(
            Text.assemble(
                "❌ ",
                ("Connection Failed", "bold red"),
                "\n\n",
                f"Error: {error}\n\n" if error else "",
                "Please ensure:\n",
                "• Ollama is installed and running\n",
                "• At least one model is installed\n",
                "• Ollama is accessible at the configured host\n\n",
                ("Quick setup:", "bold"),
                "\n",
                "1. Install Ollama: https://ollama.ai\n",
                "2. Download a model: ollama pull llama3.2\n",
                "3. Start Ollama service",
            ),
            title="Connection Error",
            border_style="red",
            padding=(1, 2),
        )

        self.console.print(error_panel)

    async def _interactive_loop(self) -> None:
        """Main interactive loop with prompt-toolkit."""

        self._show_help_hint()

        while self.is_running:
            try:
                # Create dynamic prompt
                prompt_text = self._create_prompt()

                # Get user input with completion
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.session.prompt(prompt_text, key_bindings=self.kb)
                )

                if user_input == "quit":
                    break

                user_input = user_input.strip()
                if not user_input:
                    continue

                # Handle commands vs chat
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                else:
                    await self._handle_chat_message(user_input)

            except (KeyboardInterrupt, EOFError):
                await self._handle_quit()
                break
            except Exception as e:
                self.console.print(f"\n❌ Unexpected error: {e}", style="red")

    def _create_prompt(self) -> FormattedText:
        """Create dynamic prompt with model info."""
        return FormattedText(
            [
                ("class:prompt-icon", "🤖 "),
                ("class:model-name", f"{self.current_model}"),
                ("class:prompt-separator", " > "),
            ]
        )

    def _show_help_hint(self) -> None:
        """Show help hint at bottom."""
        help_text = Text.assemble(
            ("💡 Tip: ", "bold yellow"),
            ("Type ", "dim"),
            ("/help", "cyan"),
            (" for commands, ", "dim"),
            ("Tab", "cyan"),
            (" for auto-completion, ", "dim"),
            ("Ctrl+C", "cyan"),
            (" to exit", "dim"),
        )
        self.console.print(help_text)
        self.console.print()

    async def _handle_command(self, command: str) -> None:
        """Handle slash commands."""

        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        try:
            if cmd in ["/quit", "/exit", "/bye"]:
                await self._handle_quit()

            elif cmd == "/help":
                await self._cmd_help(args)

            elif cmd == "/clear":
                self.console.clear()
                self._display_startup_banner()
                self._show_help_hint()

            elif cmd == "/status":
                await self._cmd_status()

            elif cmd == "/models":
                await self._cmd_models(args)

            elif cmd == "/model":
                await self._cmd_switch_model(args)

            elif cmd == "/download":
                await self._cmd_download(args)

            elif cmd == "/remove":
                await self._cmd_remove(args)

            elif cmd == "/discover":
                await self._cmd_discover(args)

            elif cmd == "/history":
                await self._cmd_history(args)

            elif cmd == "/new":
                await self._cmd_new_session()

            elif cmd == "/save":
                await self._cmd_save(args)

            elif cmd == "/load":
                await self._cmd_load(args)

            else:
                self.console.print(f"❌ Unknown command: {cmd}", style="red")
                self.console.print("Type [cyan]/help[/cyan] to see available commands")

        except Exception as e:
            self.console.print(f"❌ Command error: {e}", style="red")

    async def _handle_chat_message(self, message: str) -> None:
        """Handle regular chat message."""

        # Show typing indicator
        with Live(
            Text.assemble(
                ("🤖 ", "bold magenta"), ("Momo is thinking", "bold green"), ("...", "dim green")
            ),
            refresh_per_second=2,
            transient=True,
        ) as live:
            response_text = ""

            # Stream response
            async for chunk in self.chat.send_message(message, stream=True):
                response_text += chunk

        # Display response
        if response_text:
            self._display_momo_message(response_text)

    def _display_momo_message(self, message: str) -> None:
        """Display Momo's message with rich formatting."""

        self.console.print()

        # Create header
        header = Text()
        header.append("🤖 ", style="bold magenta")
        header.append("Momo", style="bold magenta")
        header.append(f" ({self.current_model})", style="dim magenta")
        header.append(":", style="bold magenta")

        self.console.print(header)

        # Display message content
        try:
            markdown = Markdown(message)
            self.console.print(markdown)
        except Exception:
            self.console.print(message)

        self.console.print()

    async def _cmd_help(self, args: List[str]) -> None:
        """Show help information."""

        if args:
            # Specific command help
            cmd = f"/{args[0]}"
            if cmd in self.completer.commands:
                info = self.completer.commands[cmd]

                help_panel = Panel(
                    Text.assemble(
                        (f"{info.name}", "bold cyan"),
                        "\n",
                        f"{info.description}\n\n",
                        ("Usage:", "bold"),
                        f" {info.usage}\n\n",
                        ("Examples:", "bold"),
                        "\n",
                        "\n".join(f"  {ex}" for ex in info.examples),
                    ),
                    title=f"Help: {info.name}",
                    border_style="cyan",
                )
                self.console.print(help_panel)
            else:
                self.console.print(f"❌ Unknown command: {cmd}", style="red")
        else:
            # General help
            await self._show_general_help()

    async def _show_general_help(self) -> None:
        """Show general help with command categories."""

        # Group commands by category
        categories = {}
        for cmd_info in self.completer.commands.values():
            if cmd_info.category not in categories:
                categories[cmd_info.category] = []
            categories[cmd_info.category].append(cmd_info)

        # Create help table
        for category, commands in categories.items():
            self.console.print(f"\n[bold cyan]{category} Commands:[/bold cyan]")

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column(style="cyan", width=15)
            table.add_column(style="white")

            for cmd in commands:
                table.add_row(cmd.name, cmd.description)

            self.console.print(table)

        # Usage hints
        self.console.print(f"\n[bold yellow]💡 Tips:[/bold yellow]")
        self.console.print("• Use [cyan]Tab[/cyan] for auto-completion")
        self.console.print("• Use [cyan]/help <command>[/cyan] for detailed help")
        self.console.print("• Use [cyan]Ctrl+R[/cyan] for history search")
        self.console.print("• Just type naturally to chat with Momo!")

    async def _cmd_status(self) -> None:
        """Show system status."""

        ollama_status = await self.chat.check_ollama_status()
        session_info = self.chat.get_session_summary()

        status_table = Table(title="System Status", box=None, padding=(0, 1))
        status_table.add_column("Setting", style="cyan")
        status_table.add_column("Value", style="white")

        # Connection status
        connection_status = "🟢 Connected" if ollama_status["connected"] else "🔴 Disconnected"
        status_table.add_row("Connection", connection_status)
        status_table.add_row("Host", ollama_status["host"])
        status_table.add_row("Current Model", self.current_model)
        status_table.add_row("Available Models", f"{len(self.available_models)} models")

        # Session info
        if session_info.get("session_id"):
            status_table.add_row("Session ID", session_info["session_id"])
            status_table.add_row("Messages", str(session_info["message_count"]))
            status_table.add_row("Started", session_info["created_at"])

        self.console.print(status_table)

    async def _cmd_models(self, args: List[str]) -> None:
        """List available models."""

        detailed = "--detailed" in args

        status_info = await self.chat.check_ollama_status()
        self.available_models = status_info.get("available_models", [])

        if not self.available_models:
            self.console.print("❌ No models available", style="red")
            self.console.print("Install one with: [cyan]/download llama3.2[/cyan]")
            return

        self.console.print("[bold cyan]📚 Available Models:[/bold cyan]\n")

        if detailed:
            # Get detailed model info
            try:
                models_response = await asyncio.wait_for(
                    asyncio.to_thread(self.chat.client.list), timeout=5.0
                )

                for model in models_response.get("models", []):
                    model_name = model.get("name", "Unknown")
                    size_gb = model.get("size", 0) / (1024**3)
                    is_current = "🟢" if model_name == self.current_model else "⚪"

                    self.console.print(f"{is_current} [green]{model_name}[/green]")
                    self.console.print(f"   Size: {size_gb:.1f} GB", style="dim")

                    details = model.get("details", {})
                    if details:
                        family = details.get("family", "Unknown")
                        params = details.get("parameter_size", "Unknown")
                        self.console.print(
                            f"   Family: {family}, Parameters: {params}", style="dim"
                        )

                    self.console.print()

            except Exception as e:
                self.console.print(f"Error getting details: {e}", style="red")
                for model in self.available_models:
                    is_current = "🟢" if model == self.current_model else "⚪"
                    self.console.print(f"{is_current} [green]{model}[/green]")
        else:
            for model in self.available_models:
                is_current = "🟢" if model == self.current_model else "⚪"
                self.console.print(f"{is_current} [green]{model}[/green]")

        self.console.print(f"\n💡 Switch models with: [cyan]/model <name>[/cyan]")
        self.console.print(f"💡 Download new models with: [cyan]/download <name>[/cyan]")

    async def _cmd_switch_model(self, args: List[str]) -> None:
        """Switch to a different model."""

        if not args:
            # Show model selector
            await self._show_model_selector()
            return

        model_name = args[0]

        # Check if model is available
        status_info = await self.chat.check_ollama_status()
        self.available_models = status_info.get("available_models", [])

        if model_name not in self.available_models:
            self.console.print(f"❌ Model '{model_name}' not found locally", style="red")
            self.console.print("Available models:", style="dim")
            for model in self.available_models:
                self.console.print(f"  • {model}", style="cyan")
            return

        # Switch model
        with self.console.status(f"[yellow]Switching to {model_name}...", spinner="dots"):
            self.current_model = model_name
            self.chat.model = model_name

            # Reconnect with new model
            await self.chat.connect()

        self.console.print(f"✅ Switched to model: [bold cyan]{model_name}[/bold cyan]")

    async def _show_model_selector(self) -> None:
        """Show interactive model selector."""

        status_info = await self.chat.check_ollama_status()
        self.available_models = status_info.get("available_models", [])

        if not self.available_models:
            self.console.print("❌ No models available", style="red")
            return

        self.console.print("[bold cyan]Select a model:[/bold cyan]\n")

        for i, model in enumerate(self.available_models, 1):
            is_current = "🟢" if model == self.current_model else f" {i}."
            self.console.print(f"{is_current} [green]{model}[/green]")

        self.console.print(f"\n💡 Enter model name or use: [cyan]/model <name>[/cyan]")

    async def _cmd_download(self, args: List[str]) -> None:
        """Download a new model."""

        if not args:
            self.console.print("❌ Please specify a model name", style="red")
            self.console.print("Example: [cyan]/download llama3.2[/cyan]")
            return

        model_name = args[0]

        # Show download progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=False,
        ) as progress:
            task = progress.add_task(f"📥 Downloading {model_name}...", total=None)

            try:
                import ollama

                client = ollama.Client(host=self.chat.host)

                await asyncio.wait_for(
                    asyncio.to_thread(client.pull, model_name),
                    timeout=300.0,  # 5 minute timeout
                )

                progress.remove_task(task)
                self.console.print(f"✅ Successfully downloaded: [green]{model_name}[/green]")
                self.console.print(f"💬 Switch to it with: [cyan]/model {model_name}[/cyan]")

                # Update available models
                status_info = await self.chat.check_ollama_status()
                self.available_models = status_info.get("available_models", [])

            except asyncio.TimeoutError:
                progress.remove_task(task)
                self.console.print(f"❌ Download timed out for '{model_name}'", style="red")
            except Exception as e:
                progress.remove_task(task)
                self.console.print(f"❌ Download failed: {e}", style="red")

    async def _cmd_remove(self, args: List[str]) -> None:
        """Remove a model."""

        if not args:
            self.console.print("❌ Please specify a model name", style="red")
            self.console.print("Example: [cyan]/remove llama3.2[/cyan]")
            return

        model_name = args[0]

        if model_name == self.current_model:
            self.console.print("❌ Cannot remove currently active model", style="red")
            return

        # Confirm removal
        if not await asyncio.get_event_loop().run_in_executor(
            None, lambda: confirm(f"Are you sure you want to remove '{model_name}'?")
        ):
            self.console.print("❌ Removal cancelled", style="yellow")
            return

        try:
            import ollama

            client = ollama.Client(host=self.chat.host)

            with self.console.status(f"[red]Removing {model_name}...", spinner="dots"):
                await asyncio.wait_for(asyncio.to_thread(client.delete, model_name), timeout=30.0)

            self.console.print(f"✅ Removed model: [green]{model_name}[/green]")

            # Update available models
            status_info = await self.chat.check_ollama_status()
            self.available_models = status_info.get("available_models", [])

        except Exception as e:
            self.console.print(f"❌ Failed to remove model: {e}", style="red")

    async def _cmd_discover(self, args: List[str]) -> None:
        """Discover recommended models by category."""

        categories = get_models_by_category()

        if args:
            # Show specific category
            category = args[0].lower()
            if category not in categories:
                self.console.print(f"❌ Unknown category: {category}", style="red")
                self.console.print("Available categories:", style="dim")
                for cat in categories.keys():
                    self.console.print(f"  • {cat}", style="cyan")
                return

            await self._show_category_models(category, categories[category])
        else:
            # Show all categories
            self.console.print("[bold cyan]📚 Discover Models by Category:[/bold cyan]\n")

            for category, models in categories.items():
                category_title = category.replace("_", " ").title()
                self.console.print(f"[bold yellow]{category_title} Models:[/bold yellow]")

                table = Table(show_header=False, box=None, padding=(0, 2))
                table.add_column(style="green", width=20)
                table.add_column(style="white", width=40)
                table.add_column(style="dim", width=15)

                for model in models[:3]:  # Show top 3 per category
                    name = model["name"]
                    description = (
                        model["description"][:50] + "..."
                        if len(model["description"]) > 50
                        else model["description"]
                    )
                    size = model["size"]

                    # Check if already installed
                    if name in self.available_models:
                        name = f"✅ {name}"

                    table.add_row(name, description, size)

                self.console.print(table)
                self.console.print()

            self.console.print("💡 Use [cyan]/discover <category>[/cyan] for detailed view")
            self.console.print("💡 Install with [cyan]/download <model>[/cyan]")

    async def _show_category_models(self, category: str, models: List[Dict]) -> None:
        """Show detailed models for a specific category."""

        category_title = category.replace("_", " ").title()
        self.console.print(f"[bold cyan]{category_title} Models:[/bold cyan]\n")

        for model in models:
            name = model["name"]
            description = model["description"]
            use_case = model["use_case"]
            size = model["size"]

            # Check if already installed
            is_installed = name in self.available_models
            is_current = name == self.current_model

            if is_current:
                status = "🟢 Current"
            elif is_installed:
                status = "✅ Installed"
            else:
                status = "📥 Available"

            self.console.print(f"{status} [bold green]{name}[/bold green]")
            self.console.print(f"   [white]{description}[/white]")
            self.console.print(f"   [dim]Use case: {use_case} | Size: {size}[/dim]")

            if not is_installed:
                self.console.print(f"   [cyan]Install: /download {name}[/cyan]")
            elif not is_current:
                self.console.print(f"   [cyan]Switch: /model {name}[/cyan]")

            self.console.print()

    async def _cmd_history(self, args: List[str]) -> None:
        """Show conversation history."""

        count = 10
        if args and args[0].isdigit():
            count = int(args[0])

        history = self.chat.get_conversation_history()
        recent_history = history[-count:] if len(history) > count else history

        if not recent_history:
            self.console.print("No conversation history yet", style="dim")
            return

        self.console.print(
            f"[bold cyan]Recent History (last {len(recent_history)} messages):[/bold cyan]\n"
        )

        for msg in recent_history:
            role = msg["role"]
            content = msg["content"]
            timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")

            if role == "user":
                self.console.print(f"[dim]{timestamp}[/dim] [bold cyan]You:[/bold cyan] {content}")
            elif role == "assistant":
                self.console.print(
                    f"[dim]{timestamp}[/dim] [bold magenta]Momo:[/bold magenta] {content[:100]}{'...' if len(content) > 100 else ''}"
                )

    async def _cmd_new_session(self) -> None:
        """Start a new conversation session."""

        if await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: confirm("Start a new conversation session? (Current history will be lost)"),
        ):
            session = self.chat.start_new_session()
            self.console.print(f"✅ Started new session: [cyan]{session.session_id}[/cyan]")

            greeting = await self.chat.get_momo_greeting(first_time=False)
            self._display_momo_message(greeting)
        else:
            self.console.print("❌ Cancelled", style="yellow")

    async def _cmd_save(self, args: List[str]) -> None:
        """Save conversation to file."""
        self.console.print("💡 Save functionality coming soon!", style="yellow")

    async def _cmd_load(self, args: List[str]) -> None:
        """Load conversation from file."""
        self.console.print("💡 Load functionality coming soon!", style="yellow")

    async def _handle_quit(self) -> None:
        """Handle quit command."""

        farewell = self.chat.get_momo_farewell()
        self._display_momo_message(farewell)

        self.is_running = False
        self.console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]")
