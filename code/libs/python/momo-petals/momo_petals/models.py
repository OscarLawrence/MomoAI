"""Pydantic models for Petals configuration and results."""

from typing import Optional, List
from pydantic import BaseModel, Field


class PetalsConfig(BaseModel):
    """Configuration for Petals client."""

    model_name: str = Field(
        default="bigscience/bloom-560m",
        description="Name of the model to use from Hugging Face",
    )
    device: Optional[str] = Field(
        default=None,
        description="Device to use (e.g., 'cpu', 'cuda', 'cuda:0')",
    )
    initial_peers: Optional[List[str]] = Field(
        default=None,
        description="List of initial peers to connect to",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for operations",
    )
    timeout: float = Field(
        default=30.0,
        description="Timeout for operations in seconds",
    )


class GenerationConfig(BaseModel):
    """Configuration for text generation."""

    max_new_tokens: int = Field(
        default=100,
        description="Maximum number of tokens to generate",
    )
    temperature: float = Field(
        default=1.0,
        description="Temperature for sampling",
    )
    top_p: float = Field(
        default=0.9,
        description="Top-p (nucleus) sampling parameter",
    )
    top_k: int = Field(
        default=50,
        description="Top-k sampling parameter",
    )
    do_sample: bool = Field(
        default=True,
        description="Whether to use sampling or greedy decoding",
    )
    repetition_penalty: float = Field(
        default=1.0,
        description="Penalty for repeating tokens",
    )


class GenerationResult(BaseModel):
    """Result of text generation."""

    text: str = Field(description="Generated text")
    prompt: str = Field(description="Original prompt")
    tokens_generated: int = Field(description="Number of tokens generated")
    generation_time: float = Field(description="Time taken to generate in seconds")
    model_name: str = Field(description="Model used for generation")


class PeerInfo(BaseModel):
    """Information about a peer in the network."""

    peer_id: str = Field(description="Unique identifier of the peer")
    throughput: Optional[float] = Field(
        default=None,
        description="Throughput of the peer in tokens/sec",
    )
    active_sessions: Optional[int] = Field(
        default=None,
        description="Number of active sessions on the peer",
    )


class NetworkInfo(BaseModel):
    """Information about the Petals network."""

    model_name: str = Field(description="Model being served")
    peer_count: int = Field(description="Number of active peers")
    total_throughput: Optional[float] = Field(
        default=None,
        description="Total network throughput in tokens/sec",
    )
    peers: List[PeerInfo] = Field(
        default_factory=list,
        description="List of peer information",
    )
    is_connected: bool = Field(
        default=False,
        description="Whether client is connected to the network",
    )