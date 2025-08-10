"""
Main entry point for creating KnowledgeBase instances.

This module provides the primary KnowledgeBase class with sensible defaults
that can be overridden via environment variables.
"""

from typing import Optional, Any, Union
from langchain_core.embeddings import Embeddings

from .constants import (
    DEFAULT_EMBEDDINGS,
    DEFAULT_VECTOR_BACKEND,
    DEFAULT_GRAPH_BACKEND,
    DEFAULT_DOCUMENT_BACKEND,
)
from .core import CoreKnowledgeBase
from .types import QueryStrategy, IndexingPipeline


def KnowledgeBase(
    embeddings: Optional[Embeddings] = DEFAULT_EMBEDDINGS,
    vector_backend: Union[str, Any] = DEFAULT_VECTOR_BACKEND,
    graph_backend: Union[str, Any] = DEFAULT_GRAPH_BACKEND,
    document_backend: Union[str, Any] = DEFAULT_DOCUMENT_BACKEND,
    indexing_pipeline: Optional[IndexingPipeline] = None,
    default_strategy: QueryStrategy = QueryStrategy.AUTO,
    **kwargs,
) -> CoreKnowledgeBase:
    """
    Create a KnowledgeBase with sensible defaults for most use cases.

    This is the main entry point for creating a knowledge base. It provides:
    - Local embeddings (all-MiniLM-L6-v2) by default for semantic search
    - In-memory backends for fast development
    - Environment variable overrides for production
    - No API keys or internet connection required

    Environment Variables (override defaults):
    - MOMO_KB_EMBEDDINGS: "local" (default), "none"
    - MOMO_KB_VECTOR_BACKEND: "memory" (default), "chroma", "pinecone", etc.
    - MOMO_KB_GRAPH_BACKEND: "memory" (default), "neo4j", etc.
    - MOMO_KB_DOCUMENT_BACKEND: "memory" (default), "duckdb", "sqlite", etc.

    Args:
        embeddings: Embedding model for vector operations (auto-configured by default)
        vector_backend: Vector storage backend (defaults to in-memory)
        graph_backend: Graph storage backend (defaults to in-memory)
        document_backend: Document storage backend (defaults to in-memory)
        indexing_pipeline: Configuration for document processing
        default_strategy: Default query strategy
        **kwargs: Additional configuration options

    Returns:
        CoreKnowledgeBase: Ready-to-use knowledge base instance

    Example:
        ```python
        from momo_kb import KnowledgeBase, Document

        # Use defaults - works offline, no configuration needed
        kb = KnowledgeBase()

        # Custom configuration
        kb = KnowledgeBase(
            vector_backend="chroma",
            document_backend="duckdb"
        )

        # Save and search documents
        doc = Document(content="Hello world", metadata={"type": "greeting"})
        await kb.save(doc)
        results = await kb.search("greeting")
        ```
    """
    return CoreKnowledgeBase(
        embeddings=embeddings,
        vector_backend=vector_backend,
        graph_backend=graph_backend,
        document_backend=document_backend,
        indexing_pipeline=indexing_pipeline,
        default_strategy=default_strategy,
        **kwargs,
    )
