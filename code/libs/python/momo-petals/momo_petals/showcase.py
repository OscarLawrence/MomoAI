"""High-level showcase interface for Petals demonstrations."""

import asyncio
from typing import Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .client import PetalsClient
from .models import PetalsConfig, GenerationConfig, GenerationResult, NetworkInfo
from .exceptions import PetalsError, NoPeersError

console = Console()


class PetalsShowcase:
    """High-level interface for showcasing Petals capabilities."""

    def __init__(self, model_name: str = "bigscience/bloom-560m"):
        """Initialize the showcase.

        Args:
            model_name: The model to use for demonstrations
        """
        self.model_name = model_name
        self.client: Optional[PetalsClient] = None

    async def setup(self) -> None:
        """Set up the Petals client and connect to the network."""
        console.print(
            Panel.fit(
                f"[bold cyan]Petals Showcase[/bold cyan]\n"
                f"Model: [yellow]{self.model_name}[/yellow]",
                border_style="cyan",
            )
        )

        config = PetalsConfig(model_name=self.model_name)
        self.client = PetalsClient(config)

        try:
            await self.client.connect()
            console.print("[green]✓[/green] Successfully connected to Petals network")
            
            # Show network info
            await self.show_network_info()
            
        except NoPeersError:
            console.print(
                "[red]✗[/red] No peers available for this model.\n"
                "[yellow]This is common for less popular models. "
                "Try using 'bigscience/bloom-560m' or check if anyone is serving the model.[/yellow]"
            )
            raise
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect: {e}")
            raise

    async def show_network_info(self) -> None:
        """Display information about the Petals network."""
        if not self.client:
            raise PetalsError("Client not initialized. Call setup() first.")

        info = await self.client.get_network_info()
        
        table = Table(title="Network Information", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Model", info.model_name)
        table.add_row("Connected", "✓" if info.is_connected else "✗")
        table.add_row("Active Peers", str(info.peer_count))
        
        if info.total_throughput:
            table.add_row("Total Throughput", f"{info.total_throughput:.2f} tokens/sec")
        
        console.print(table)

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 50,
        temperature: float = 0.8,
    ) -> GenerationResult:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature

        Returns:
            GenerationResult with the generated text
        """
        if not self.client:
            raise PetalsError("Client not initialized. Call setup() first.")

        console.print(f"\n[bold]Prompt:[/bold] {prompt}")
        console.print("[dim]Generating...[/dim]")

        config = GenerationConfig(
            max_new_tokens=max_tokens,
            temperature=temperature,
        )

        result = await self.client.generate(prompt, config)

        # Display result
        console.print(f"\n[bold]Generated:[/bold] [green]{result.text}[/green]")
        console.print(
            f"[dim]Tokens: {result.tokens_generated} | "
            f"Time: {result.generation_time:.2f}s | "
            f"Speed: {result.tokens_generated / result.generation_time:.2f} tokens/s[/dim]"
        )

        return result

    async def run_demo(self, prompts: Optional[List[str]] = None) -> None:
        """Run a demonstration with multiple prompts.

        Args:
            prompts: List of prompts to generate from. If None, uses defaults.
        """
        if prompts is None:
            prompts = [
                "Once upon a time in a distant galaxy",
                "The key to artificial intelligence is",
                "In the year 2050, humanity will",
            ]

        console.print("\n[bold cyan]Running Petals Demo[/bold cyan]\n")

        for i, prompt in enumerate(prompts, 1):
            console.print(f"\n[bold]Example {i}/{len(prompts)}[/bold]")
            console.rule(style="dim")
            
            try:
                await self.generate_text(prompt)
            except Exception as e:
                console.print(f"[red]Error generating text: {e}[/red]")

        console.print("\n[bold green]Demo complete![/bold green]")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.disconnect()
            self.client = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


async def run_showcase(model_name: str = "bigscience/bloom-560m") -> None:
    """Run a complete Petals showcase.

    Args:
        model_name: The model to use for the showcase
    """
    async with PetalsShowcase(model_name) as showcase:
        await showcase.run_demo()


def main():
    """Main entry point for the showcase."""
    try:
        asyncio.run(run_showcase())
    except KeyboardInterrupt:
        console.print("\n[yellow]Showcase interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Showcase failed: {e}[/red]")
        raise


if __name__ == "__main__":
    main()