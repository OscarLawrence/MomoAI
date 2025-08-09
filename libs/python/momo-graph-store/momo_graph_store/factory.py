"""
Factory for creating graph store backends.

Provides a unified interface for creating different graph store backends.
"""

from typing import Any, Dict

from .backends.base import BaseGraphBackend
from .backends.memory import InMemoryGraphBackend
from .exceptions import BackendError


def create_graph_backend(backend_type: str, **config: Any) -> BaseGraphBackend:
    """
    Create a graph store backend.

    Args:
        backend_type: Type of backend to create ("memory", "neo4j", etc.)
        **config: Backend-specific configuration

    Returns:
        Configured graph store backend instance

    Raises:
        BackendError: If backend_type is not supported
    """
    backend_registry: Dict[str, type] = {
        "memory": InMemoryGraphBackend,
    }

    if backend_type not in backend_registry:
        available = ", ".join(backend_registry.keys())
        raise BackendError(
            f"Unsupported backend type: {backend_type}. Available backends: {available}"
        )

    backend_class = backend_registry[backend_type]
    return backend_class(**config)  # type: ignore[no-any-return]


async def acreate_graph_backend(backend_type: str, **config: Any) -> BaseGraphBackend:
    """
    Async factory for creating graph store backends.

    Args:
        backend_type: Type of backend to create
        **config: Backend-specific configuration

    Returns:
        Configured graph store backend instance
    """
    return create_graph_backend(backend_type, **config)
