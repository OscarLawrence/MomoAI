"""
Exceptions for momo-graph-store module.

Custom exception classes for graph database operations.
"""


class GraphStoreError(Exception):
    """Base exception for graph store operations."""

    pass


class NodeNotFoundError(GraphStoreError):
    """Raised when a requested node is not found."""

    pass


class QueryError(GraphStoreError):
    """Raised when a graph query fails."""

    pass


class BackendError(GraphStoreError):
    """Raised when a backend operation fails."""

    pass


class SchemaError(GraphStoreError):
    """Raised when schema operations fail."""

    pass
