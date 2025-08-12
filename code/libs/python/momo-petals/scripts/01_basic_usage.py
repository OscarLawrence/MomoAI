#!/usr/bin/env python3
"""Basic usage example for Petals distributed inference."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.prompt import Prompt

from momo_petals import PetalsClient, PetalsConfig, GenerationConfig
from momo_petals.exceptions import NoPeersError, PetalsError, GenerationError

console = Console()


async def main():
    """Run a basic Petals example."""
    console.print("[bold cyan]Petals Basic Usage Example[/bold cyan]\n")

    # Configuration
    model_name = "bigscience/bloom-560m"  # Small model for testing
    config = PetalsConfig(model_name=model_name)

    # Create client
    client = PetalsClient(config)

    try:
        # Connect to the network
        console.print(f"Connecting to Petals network for model: [yellow]{model_name}[/yellow]")
        await client.connect()
        console.print("[green]✓[/green] Connected successfully!\n")

        # Get network info
        network_info = await client.get_network_info()
        console.print(f"Network status:")
        console.print(f"  • Model: {network_info.model_name}")
        console.print(f"  • Active peers: {network_info.peer_count}")
        console.print(f"  • Connected: {'Yes' if network_info.is_connected else 'No'}\n")

        # Interactive generation loop
        console.print("[bold]Interactive Text Generation[/bold]")
        console.print("Enter a prompt to generate text, or 'quit' to exit.\n")

        while True:
            # Get prompt from user
            prompt = Prompt.ask("[cyan]Prompt[/cyan]")
            
            if prompt.lower() in ["quit", "exit", "q"]:
                break

            # Configure generation
            gen_config = GenerationConfig(
                max_new_tokens=50,
                temperature=0.8,
                top_p=0.9,
                do_sample=True,
            )

            try:
                # Generate text
                console.print("\n[dim]Generating...[/dim]")
                result = await client.generate(prompt, gen_config)

                # Display result
                console.print(f"\n[bold green]Generated text:[/bold green]")
                console.print(f"{result.text}\n")
                
                # Show statistics
                console.print(f"[dim]Statistics:[/dim]")
                console.print(f"  • Tokens generated: {result.tokens_generated}")
                console.print(f"  • Generation time: {result.generation_time:.2f}s")
                console.print(f"  • Speed: {result.tokens_generated / result.generation_time:.2f} tokens/s\n")

            except GenerationError as e:
                console.print(f"[red]Generation failed: {e}[/red]\n")
            except Exception as e:
                console.print(f"[red]Unexpected error: {e}[/red]\n")

    except NoPeersError as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("\n[yellow]Tips:[/yellow]")
        console.print("  • Make sure someone is serving this model on the Petals network")
        console.print("  • Try using a more popular model like 'bigscience/bloom-560m'")
        console.print("  • Check https://health.petals.dev for network status")
        return 1

    except PetalsError as e:
        console.print(f"\n[red]Petals error: {e}[/red]")
        return 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 0

    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        console.print("[dim]Full traceback:[/dim]")
        console.print_exception()
        return 1

    finally:
        # Clean up
        if client:
            console.print("\n[dim]Disconnecting...[/dim]")
            await client.disconnect()

    console.print("\n[green]Example completed successfully![/green]")
    return 0


if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)