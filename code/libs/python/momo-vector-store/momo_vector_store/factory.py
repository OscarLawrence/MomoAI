"""Factory for creating vector store backends."""

from typing import Any, Dict, Optional
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from .exceptions import BackendError


def create_vectorstore(
    backend_type: str, embeddings: Embeddings, **config: Any
) -> VectorStore:
    """
    Create a vector store backend.

    Args:
        backend_type: Type of backend ("memory", "chroma", "weaviate", etc.)
        embeddings: Embedding model instance
        **config: Backend-specific configuration options

    Returns:
        VectorStore instance

    Raises:
        BackendError: If backend type is unsupported or creation fails
    """
    try:
        if backend_type == "memory":
            return _create_memory_backend(embeddings, **config)
        elif backend_type == "chroma":
            return _create_chroma_backend(embeddings, **config)
        elif backend_type == "weaviate":
            return _create_weaviate_backend(embeddings, **config)
        elif backend_type == "milvus":
            return _create_milvus_backend(embeddings, **config)
        else:
            raise BackendError(
                f"Unsupported backend type: {backend_type}", backend=backend_type
            )
    except Exception as e:
        if isinstance(e, BackendError):
            raise
        raise BackendError(
            f"Failed to create {backend_type} backend: {str(e)}",
            backend=backend_type,
            operation="create",
        )


def _create_memory_backend(embeddings: Embeddings, **config: Any) -> VectorStore:
    """Create InMemory vector store backend."""
    from langchain_core.vectorstores.in_memory import InMemoryVectorStore

    return InMemoryVectorStore(embedding=embeddings)


def _create_chroma_backend(embeddings: Embeddings, **config: Any) -> VectorStore:
    """Create Chroma vector store backend."""
    try:
        from langchain_chroma import Chroma  # type: ignore[import-not-found]
    except ImportError as e:
        raise BackendError(
            "Chroma not available. Install with: pip install langchain-chroma",
            backend="chroma",
        ) from e

    # Extract Chroma-specific config
    chroma_config = {
        "collection_name": config.get("collection_name", "momo_collection"),
        "persist_directory": config.get("persist_directory", None),
        "client_settings": config.get("client_settings", None),
        "collection_metadata": config.get("collection_metadata", None),
    }

    # Remove None values
    chroma_config = {k: v for k, v in chroma_config.items() if v is not None}

    return Chroma(embedding_function=embeddings, **chroma_config)


def _create_weaviate_backend(embeddings: Embeddings, **config: Any) -> VectorStore:
    """Create Weaviate vector store backend."""
    try:
        from langchain_weaviate import WeaviateVectorStore  # type: ignore[import-not-found]
    except ImportError as e:
        raise BackendError(
            "Weaviate not available. Install with: pip install langchain-weaviate",
            backend="weaviate",
        ) from e

    # Extract Weaviate-specific config
    url = config.get("url", "http://localhost:8080")
    index_name = config.get("index_name", "MomoIndex")
    text_key = config.get("text_key", "content")

    return WeaviateVectorStore(
        embedding=embeddings,
        url=url,
        index_name=index_name,
        text_key=text_key,
        **{
            k: v
            for k, v in config.items()
            if k not in ["url", "index_name", "text_key"]
        },
    )


def _create_milvus_backend(embeddings: Embeddings, **config: Any) -> VectorStore:
    """Create Milvus vector store backend."""
    try:
        from langchain_milvus import Milvus  # type: ignore[import-not-found]
    except ImportError as e:
        raise BackendError(
            "Milvus not available. Install with: pip install langchain-milvus pymilvus",
            backend="milvus",
        ) from e

    # Extract Milvus-specific config with sensible defaults
    connection_args = config.get("connection_args", {"host": "localhost", "port": "19530"})
    collection_name = config.get("collection_name", "momo_collection")
    primary_field = config.get("primary_field", "id")
    text_field = config.get("text_field", "content")
    vector_field = config.get("vector_field", "vector")
    index_params = config.get("index_params", None)
    search_params = config.get("search_params", None)

    # Create Milvus vector store with provided configuration
    return Milvus(
        embedding_function=embeddings,
        connection_args=connection_args,
        collection_name=collection_name,
        primary_field=primary_field,
        text_field=text_field,
        vector_field=vector_field,
        index_params=index_params,
        search_params=search_params,
        **{
            k: v
            for k, v in config.items()
            if k
            not in [
                "connection_args",
                "collection_name",
                "primary_field",
                "text_field",
                "vector_field",
                "index_params",
                "search_params",
            ]
        },
    )


async def acreate_vectorstore(
    backend_type: str, embeddings: Embeddings, **config: Any
) -> VectorStore:
    """
    Async version of create_vectorstore.

    Currently just wraps sync version, but allows for future async initialization.
    """
    return create_vectorstore(backend_type, embeddings, **config)
