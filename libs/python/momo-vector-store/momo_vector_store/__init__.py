"""
Momo Vector Store

A unified vector store implementation for the Momo AI knowledge base.
Uses LangChain VectorStore abstractions with swappable backends and sensible defaults.

Quick Start:
    from momo_vector_store import VectorStore

    # Simple usage with defaults (no dependencies required)
    store = VectorStore()
    await store.add_texts(["Hello world", "Python rocks"])
    results = await store.search("greeting")

    # Custom configuration
    store = VectorStore(backend_type="chroma", embeddings=my_embeddings)
"""

__version__ = "0.1.0"

# Primary interface with sensible defaults
from .main import VectorStore
from .manager import VectorStoreManager

# Factory functions for advanced usage
from .factory import create_vectorstore, acreate_vectorstore

# Local embeddings that work without external dependencies
from .embeddings import LocalEmbeddings, SimpleEmbeddings

# Exception handling
from .exceptions import VectorStoreError, EmbeddingError, BackendError, SearchError

# Re-export LangChain types for convenience
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore as LangChainVectorStore

__all__ = [
    # Primary interface (recommended)
    "VectorStore",
    # Advanced interfaces
    "VectorStoreManager",
    "create_vectorstore",
    "acreate_vectorstore",
    # Default embeddings (no external dependencies)
    "LocalEmbeddings",
    "SimpleEmbeddings",
    # Exception handling
    "VectorStoreError",
    "EmbeddingError",
    "BackendError",
    "SearchError",
    # LangChain compatibility
    "Document",
    "LangChainVectorStore",
]
