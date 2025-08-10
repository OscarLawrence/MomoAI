"""
Momo Graph Store - Graph database abstraction following LangChain patterns.

This module provides a unified API for graph database operations with
swappable backends and full LangChain compatibility.
"""

from .backends import InMemoryGraphBackend
from .exceptions import (
    BackendError,
    GraphStoreError,
    NodeNotFoundError,
    QueryError,
    SchemaError,
)
from .factory import acreate_graph_backend, create_graph_backend
from .main import GraphStore

__version__ = "0.1.0"

__all__ = [
    # Main interface
    "GraphStore",
    # Factory functions
    "create_graph_backend",
    "acreate_graph_backend",
    # Backend implementations
    "InMemoryGraphBackend",
    # Exceptions
    "GraphStoreError",
    "NodeNotFoundError",
    "QueryError",
    "BackendError",
    "SchemaError",
]
