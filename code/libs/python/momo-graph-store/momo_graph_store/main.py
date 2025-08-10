"""
Main GraphStore interface following LangChain patterns.

This module provides the main interface for graph storage operations,
following LangChain's GraphStore abstraction for maximum compatibility.
"""

from typing import Any, Dict, List

from langchain_community.graphs.graph_document import GraphDocument

from .backends.base import BaseGraphBackend
from .factory import create_graph_backend


class GraphStore:
    """
    Simple graph store with sensible defaults.

    This is the main entry point for the momo-graph-store module.
    It provides a clean interface with defaults that work out of the box
    while still allowing full customization.

    Default configuration:
    - Backend: InMemory ('memory')
    - All operations are async-first

    Example:
        # Simple usage with defaults
        store = GraphStore()
        await store.add_graph_documents([graph_doc])
        results = await store.query("MATCH (n) RETURN n")

        # Customized usage
        store = GraphStore(
            backend_type="memory",
            **config
        )
    """

    def __init__(
        self,
        backend_type: str = "memory",
        **config: Any,
    ):
        """
        Initialize GraphStore with sensible defaults.

        Args:
            backend_type: Graph backend type (default: "memory")
            **config: Backend-specific configuration options
        """
        # Initialize the underlying backend
        self.backend = create_graph_backend(backend_type, **config)
        self.backend_type = backend_type

    @classmethod
    async def acreate(
        cls,
        backend_type: str = "memory",
        **config: Any,
    ) -> "GraphStore":
        """
        Async factory method to create GraphStore.

        Args:
            backend_type: Graph backend type (default: "memory")
            **config: Backend-specific configuration options

        Returns:
            GraphStore instance
        """
        backend = create_graph_backend(backend_type, **config)

        # Create instance and set attributes
        instance = cls.__new__(cls)
        instance.backend = backend
        instance.backend_type = backend_type

        return instance

    async def add_graph_documents(
        self,
        graph_documents: List[GraphDocument],
        include_source: bool = False,
    ) -> None:
        """
        Add graph documents to the store.

        Args:
            graph_documents: List of GraphDocument objects to add
            include_source: Whether to include source document information
        """
        await self.backend.add_graph_documents(graph_documents, include_source)

    async def query(
        self,
        query: str,
        params: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query against the graph.

        Args:
            query: Query string (syntax depends on backend)
            params: Optional query parameters

        Returns:
            List of query results as dictionaries
        """
        if params is None:
            params = {}
        return await self.backend.query(query, params)

    @property
    def get_schema(self) -> str:
        """
        Return the schema of the Graph database.

        Returns:
            String representation of the graph schema
        """
        return self.backend.get_schema()

    @property
    def get_structured_schema(self) -> Dict[str, Any]:
        """
        Return the schema of the Graph database.

        Returns:
            Dictionary representation of the graph schema
        """
        return self.backend.get_structured_schema()

    async def refresh_schema(self) -> None:
        """Refresh the graph schema information."""
        await self.backend.refresh_schema()

    def get_info(self) -> Dict[str, Any]:
        """
        Get graph store information.

        Returns:
            Dict with backend info, schema stats, etc.
        """
        backend_info = self.backend.get_backend_info()
        schema_info = self.get_structured_schema

        return {
            "backend": backend_info,
            "schema": schema_info,
            "default_backend": self.backend_type,
        }

    # Convenience properties for direct access to underlying components
    @property
    def graph_backend(self) -> BaseGraphBackend:
        """Access to underlying graph backend."""
        return self.backend

    def __repr__(self) -> str:
        """String representation of GraphStore."""
        return f"GraphStore(backend_type='{self.backend_type}')"
