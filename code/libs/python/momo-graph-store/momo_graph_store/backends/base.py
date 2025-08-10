"""
Base classes and protocols for graph store backends.

Defines the interface that all graph store backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Protocol

from langchain_community.graphs.graph_document import GraphDocument


class GraphBackendProtocol(Protocol):
    """Protocol for graph storage backends."""

    async def add_graph_documents(
        self, graph_documents: List[GraphDocument], include_source: bool = False
    ) -> None:
        """Add graph documents to the store."""
        ...

    async def query(
        self, query: str, params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """Execute a query against the graph."""
        ...

    def get_schema(self) -> str:
        """Return the schema of the Graph database as a string."""
        ...

    def get_structured_schema(self) -> Dict[str, Any]:
        """Return the schema of the Graph database as a dictionary."""
        ...

    async def refresh_schema(self) -> None:
        """Refresh the graph schema information."""
        ...


class BaseGraphBackend(ABC):
    """Abstract base class for graph backends."""

    @abstractmethod
    async def add_graph_documents(
        self, graph_documents: List[GraphDocument], include_source: bool = False
    ) -> None:
        """Add graph documents to the store."""
        pass

    @abstractmethod
    async def query(
        self, query: str, params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """Execute a query against the graph."""
        pass

    @abstractmethod
    def get_schema(self) -> str:
        """Return the schema of the Graph database as a string."""
        pass

    @abstractmethod
    def get_structured_schema(self) -> Dict[str, Any]:
        """Return the schema of the Graph database as a dictionary."""
        pass

    @abstractmethod
    async def refresh_schema(self) -> None:
        """Refresh the graph schema information."""
        pass

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about this backend."""
        return {
            "type": type(self).__name__,
            "backend_name": getattr(self, "backend_name", "unknown"),
        }
