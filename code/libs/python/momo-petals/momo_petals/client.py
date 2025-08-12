"""Petals client wrapper for distributed inference."""

import asyncio
import time
from typing import Optional, Dict, Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from transformers import AutoTokenizer

from .exceptions import (
    PetalsError,
    NetworkError,
    NoPeersError,
    ModelLoadError,
    GenerationError,
)
from .models import (
    PetalsConfig,
    GenerationConfig,
    GenerationResult,
    NetworkInfo,
    PeerInfo,
)

console = Console()


class PetalsClient:
    """Client for interacting with Petals distributed inference network."""

    def __init__(self, config: Optional[PetalsConfig] = None):
        """Initialize Petals client.

        Args:
            config: Configuration for the client. If None, uses defaults.
        """
        self.config = config or PetalsConfig()
        self.model = None
        self.tokenizer = None
        self._session = None
        self._is_connected = False

    async def connect(self) -> None:
        """Connect to the Petals network and load the model."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Connecting to Petals network for {self.config.model_name}...",
                    total=None,
                )

                # Import petals here to handle import errors gracefully
                try:
                    from petals import AutoDistributedModelForCausalLM
                except ImportError as e:
                    raise ModelLoadError(
                        self.config.model_name,
                        "Petals is not installed. Please install it with: pip install petals",
                    ) from e

                # Load tokenizer
                progress.update(task, description="Loading tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)

                # Load distributed model
                progress.update(task, description="Loading distributed model...")
                try:
                    self.model = AutoDistributedModelForCausalLM.from_pretrained(
                        self.config.model_name,
                        initial_peers=self.config.initial_peers,
                        device=self.config.device,
                    )
                    self._is_connected = True
                    progress.update(task, description="Connected successfully!")
                except Exception as e:
                    if "no peers" in str(e).lower():
                        raise NoPeersError(self.config.model_name)
                    else:
                        raise ModelLoadError(self.config.model_name, str(e))

        except Exception as e:
            console.print(f"[red]Error connecting to Petals: {e}[/red]")
            raise

    async def disconnect(self) -> None:
        """Disconnect from the Petals network."""
        if self._session:
            self._session = None
        self._is_connected = False
        self.model = None
        self.tokenizer = None
        console.print("[yellow]Disconnected from Petals network[/yellow]")

    async def generate(
        self,
        prompt: str,
        generation_config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt
            generation_config: Configuration for generation. If None, uses defaults.

        Returns:
            GenerationResult with the generated text and metadata
        """
        if not self._is_connected or not self.model or not self.tokenizer:
            raise PetalsError("Not connected to Petals network. Call connect() first.")

        config = generation_config or GenerationConfig()

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating text...", total=None)

                # Tokenize input
                inputs = self.tokenizer(prompt, return_tensors="pt")
                input_length = inputs["input_ids"].shape[1]

                # Generate
                start_time = time.time()
                with self.model.inference_session() as session:
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=config.max_new_tokens,
                        temperature=config.temperature,
                        top_p=config.top_p,
                        top_k=config.top_k,
                        do_sample=config.do_sample,
                        repetition_penalty=config.repetition_penalty,
                        session=session,
                    )

                generation_time = time.time() - start_time

                # Decode output
                generated_text = self.tokenizer.decode(
                    outputs[0][input_length:], skip_special_tokens=True
                )

                progress.update(task, description="Generation complete!")

                return GenerationResult(
                    text=generated_text,
                    prompt=prompt,
                    tokens_generated=outputs[0].shape[0] - input_length,
                    generation_time=generation_time,
                    model_name=self.config.model_name,
                )

        except Exception as e:
            raise GenerationError(f"Failed to generate text: {e}") from e

    async def get_network_info(self) -> NetworkInfo:
        """Get information about the Petals network.

        Returns:
            NetworkInfo with details about the network and peers
        """
        if not self._is_connected:
            return NetworkInfo(
                model_name=self.config.model_name,
                peer_count=0,
                is_connected=False,
            )

        try:
            # In a real implementation, we would query the DHT for peer info
            # For now, we'll return basic info
            peers = []
            
            # Try to get some network statistics if available
            if hasattr(self.model, "dht") and self.model.dht:
                # This is a simplified version - actual implementation would
                # query the DHT for real peer information
                peer_count = len(self.model.dht.get_visible_peers()) if hasattr(self.model.dht, "get_visible_peers") else 1
            else:
                peer_count = 1  # At least one peer if we're connected

            return NetworkInfo(
                model_name=self.config.model_name,
                peer_count=peer_count,
                is_connected=True,
                peers=peers,
            )

        except Exception as e:
            console.print(f"[yellow]Warning: Could not get full network info: {e}[/yellow]")
            return NetworkInfo(
                model_name=self.config.model_name,
                peer_count=1,  # We're connected, so at least 1
                is_connected=True,
            )

    def __enter__(self):
        """Context manager entry."""
        asyncio.run(self.connect())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        asyncio.run(self.disconnect())

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()