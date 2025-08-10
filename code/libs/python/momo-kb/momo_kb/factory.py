"""
Backend Factory System for Dynamic Backend Loading

This module provides a factory system for dynamically loading backends
based on string identifiers, enabling clean configuration like:
    document_backend = 'duckdb'
    graph_backend = 'neo4j'
"""

from typing import Any, Dict, Type, Union, Optional, Callable
from .exceptions import KnowledgeBaseError


class BackendFactory:
    """Factory for creating backend instances from string identifiers."""

    def __init__(self):
        self._document_backends: Dict[str, Union[Type, Callable]] = {}
        self._vector_backends: Dict[str, Type] = {}
        self._graph_backends: Dict[str, Type] = {}
        self._register_builtin_backends()

    def _register_builtin_backends(self):
        """Register built-in backend implementations."""
        # Document backends - all pandas-based with different persistence strategies
        from momo_store_document import PandasDocumentBackend
        from momo_store_document.persistence import (
            NoPersistence,
            CSVPersistence,
            HDF5Persistence,
            DuckDBPersistence,
        )

        self._document_backends = {
            "memory": lambda *args, **kwargs: PandasDocumentBackend(NoPersistence()),
            "csv": lambda file_path, *args, **kwargs: PandasDocumentBackend(
                CSVPersistence(file_path)
            ),
            "hdf5": lambda file_path, *args, **kwargs: PandasDocumentBackend(
                HDF5Persistence(file_path)
            ),
            "duckdb": lambda database_path=":memory:",
            *args,
            **kwargs: PandasDocumentBackend(DuckDBPersistence(database_path)),
        }

        # Vector backends
        from momo_store_vector import InMemoryVectorBackend

        self._vector_backends = {
            "memory": InMemoryVectorBackend,
            "in_memory": InMemoryVectorBackend,
        }

        # Graph backends
        from momo_store_graph import InMemoryGraphBackend

        self._graph_backends = {
            "memory": InMemoryGraphBackend,
            "in_memory": InMemoryGraphBackend,
        }

    def create_document_backend(self, backend: Union[str, Any], *args, **kwargs):
        """Create a document backend from string identifier or return existing instance."""
        if isinstance(backend, str):
            if backend not in self._document_backends:
                available = list(self._document_backends.keys())
                raise KnowledgeBaseError(
                    f"Unknown document backend '{backend}'. Available: {available}"
                )

            backend_class = self._document_backends[backend]
            return backend_class(*args, **kwargs)

        # Already an instance, return as-is
        return backend

    def create_vector_backend(self, backend: Union[str, Any], *args, **kwargs):
        """Create a vector backend from string identifier or return existing instance."""
        if isinstance(backend, str):
            if backend not in self._vector_backends:
                available = list(self._vector_backends.keys())
                raise KnowledgeBaseError(
                    f"Unknown vector backend '{backend}'. Available: {available}"
                )

            backend_class = self._vector_backends[backend]
            return backend_class(*args, **kwargs)

        # Already an instance, return as-is
        return backend

    def create_graph_backend(self, backend: Union[str, Any], *args, **kwargs):
        """Create a graph backend from string identifier or return existing instance."""
        if isinstance(backend, str):
            if backend not in self._graph_backends:
                available = list(self._graph_backends.keys())
                raise KnowledgeBaseError(
                    f"Unknown graph backend '{backend}'. Available: {available}"
                )

            backend_class = self._graph_backends[backend]
            return backend_class(*args, **kwargs)

        # Already an instance, return as-is
        return backend

    def register_document_backend(self, name: str, backend_class: Type):
        """Register a new document backend implementation."""
        self._document_backends[name] = backend_class

    def register_vector_backend(self, name: str, backend_class: Type):
        """Register a new vector backend implementation."""
        self._vector_backends[name] = backend_class

    def register_graph_backend(self, name: str, backend_class: Type):
        """Register a new graph backend implementation."""
        self._graph_backends[name] = backend_class

    def list_available_backends(self) -> Dict[str, list]:
        """List all available backend types."""
        return {
            "document": list(self._document_backends.keys()),
            "vector": list(self._vector_backends.keys()),
            "graph": list(self._graph_backends.keys()),
        }


# Global factory instance
_factory = BackendFactory()


def create_document_backend(backend: Union[str, Any], *args, **kwargs):
    """Create a document backend from string identifier."""
    return _factory.create_document_backend(backend, *args, **kwargs)


def create_vector_backend(backend: Union[str, Any], *args, **kwargs):
    """Create a vector backend from string identifier."""
    return _factory.create_vector_backend(backend, *args, **kwargs)


def create_graph_backend(backend: Union[str, Any], *args, **kwargs):
    """Create a graph backend from string identifier."""
    return _factory.create_graph_backend(backend, *args, **kwargs)


def register_document_backend(name: str, backend_class: Type):
    """Register a custom document backend."""
    _factory.register_document_backend(name, backend_class)


def register_vector_backend(name: str, backend_class: Type):
    """Register a custom vector backend."""
    _factory.register_vector_backend(name, backend_class)


def register_graph_backend(name: str, backend_class: Type):
    """Register a custom graph backend."""
    _factory.register_graph_backend(name, backend_class)


def list_available_backends() -> Dict[str, list]:
    """List all available backend implementations."""
    return _factory.list_available_backends()
