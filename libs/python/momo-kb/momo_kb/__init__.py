"""
Momo KnowledgeBase - Core abstractions and types.

This module provides the fundamental abstractions for Momo's knowledge management system.
It defines clean interfaces that can be implemented by various backends while maintaining
a simple, intuitive API for consumers.
"""

from .main import KnowledgeBase
from .core import CoreKnowledgeBase
from .base import BaseKnowledgeBase
from .types import (
    Document,
    DocumentMetadata,
    SearchResult,
    SearchOptions,
    QueryStrategy,
    StorageBackend,
    IndexingPipeline,
    RelationshipSpec,
    BackendConfig,
)
from .exceptions import KnowledgeBaseError, DocumentNotFoundError, SearchError
from momo_store_vector import (
    VectorBackend,
    InMemoryVectorBackend,
)
from momo_store_graph import (
    GraphBackend,
    InMemoryGraphBackend,
)
from momo_store_document import (
    DocumentBackend,
    PandasDocumentBackend,
)
from .factory import (
    create_document_backend,
    create_vector_backend,
    create_graph_backend,
    register_document_backend,
    register_vector_backend,
    register_graph_backend,
    list_available_backends,
)
from .embeddings import (
    get_default_embeddings,
    create_local_embeddings,
    list_local_models,
)

__version__ = "0.1.0"

__all__ = [
    # Main public interface
    "KnowledgeBase",
    "CoreKnowledgeBase",
    # Core types
    "Document",
    "DocumentMetadata",
    "SearchResult",
    "SearchOptions",
    # Configuration types
    "QueryStrategy",
    "StorageBackend",
    "IndexingPipeline",
    "RelationshipSpec",
    "BackendConfig",
    # Exceptions
    "KnowledgeBaseError",
    "DocumentNotFoundError",
    "SearchError",
    # Advanced interfaces (for custom implementations)
    "BaseKnowledgeBase",
    # Backends
    "VectorBackend",
    "InMemoryVectorBackend",
    "GraphBackend",
    "InMemoryGraphBackend",
    "DocumentBackend",
    "PandasDocumentBackend",
    # Factory system
    "create_document_backend",
    "create_vector_backend",
    "create_graph_backend",
    "register_document_backend",
    "register_vector_backend",
    "register_graph_backend",
    "list_available_backends",
    # Embeddings
    "get_default_embeddings",
    "create_local_embeddings",
    "list_local_models",
]
