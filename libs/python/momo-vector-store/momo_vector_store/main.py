"""
Core vector store interface using LangChain abstractions.

This module provides the main interface for vector storage operations,
leveraging LangChain's VectorStore ecosystem for maximum compatibility.
"""

from typing import Any, List, Dict, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from .manager import VectorStoreManager
from .embeddings import LocalEmbeddings


class VectorStore:
    """
    Simple vector store with sensible defaults.

    This is the main entry point for the momo-vector-store module.
    It provides a clean interface with defaults that work out of the box
    while still allowing full customization.

    Default configuration:
    - Backend: InMemory ('memory')
    - Embeddings: LocalEmbeddings (no external dependencies)
    - All operations are async-first

    Example:
        # Simple usage with defaults
        store = VectorStore()
        await store.add_texts(["Hello world", "Python rocks"])
        results = await store.search("greeting")

        # Customized usage
        store = VectorStore(
            backend_type="chroma",
            embeddings=custom_embeddings,
            persist_directory="/data/vectors"
        )
    """

    def __init__(
        self,
        backend_type: str = "memory",
        embeddings: Optional[Embeddings] = None,
        **config: Any,
    ):
        """
        Initialize VectorStore with sensible defaults.

        Args:
            backend_type: Vector backend type (default: "memory")
            embeddings: Embedding model (default: LocalEmbeddings())
            **config: Backend-specific configuration options
        """
        # Use local embeddings by default
        if embeddings is None:
            embeddings = LocalEmbeddings()

        # Initialize the underlying manager
        self.manager = VectorStoreManager.create(backend_type, embeddings, **config)
        self.backend_type = backend_type
        self.embeddings = embeddings

    @classmethod
    async def acreate(
        cls,
        backend_type: str = "memory",
        embeddings: Optional[Embeddings] = None,
        **config: Any,
    ) -> "VectorStore":
        """
        Async factory method to create VectorStore.

        Args:
            backend_type: Vector backend type (default: "memory")
            embeddings: Embedding model (default: LocalEmbeddings())
            **config: Backend-specific configuration options

        Returns:
            VectorStore instance
        """
        # Use local embeddings by default
        if embeddings is None:
            embeddings = LocalEmbeddings()

        manager = await VectorStoreManager.acreate(backend_type, embeddings, **config)

        # Create instance and set attributes
        instance = cls.__new__(cls)
        instance.manager = manager
        instance.backend_type = backend_type
        instance.embeddings = embeddings

        return instance

    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add texts to the vector store.

        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs

        Returns:
            List of document IDs
        """
        return await self.manager.add_texts(texts, metadatas, ids)

    async def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            documents: List of LangChain Document objects

        Returns:
            List of document IDs
        """
        return await self.manager.add_documents(documents)

    async def search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """
        Search for similar documents.

        Args:
            query: Search query text
            k: Number of results to return (default: 4)
            filter: Optional metadata filter dict
            **kwargs: Additional search parameters

        Returns:
            List of similar documents
        """
        return await self.manager.similarity_search(query, k, filter, **kwargs)

    async def search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[tuple[Document, float]]:
        """
        Search with relevance scores.

        Args:
            query: Search query text
            k: Number of results to return (default: 4)
            filter: Optional metadata filter dict
            **kwargs: Additional search parameters

        Returns:
            List of (document, score) tuples
        """
        return await self.manager.similarity_search_with_score(
            query, k, filter, **kwargs
        )

    def get_info(self) -> Dict[str, Any]:
        """
        Get vector store information.

        Returns:
            Dict with backend info, embedding stats, etc.
        """
        backend_info = self.manager.get_backend_info()

        # Add embedding information if available
        embedding_info = {"type": type(self.embeddings).__name__}
        if hasattr(self.embeddings, "get_stats"):
            stats = self.embeddings.get_stats()
            embedding_info.update(stats)
        elif hasattr(self.embeddings, "model_name"):
            embedding_info["model_name"] = self.embeddings.model_name

        return {
            "backend": backend_info,
            "embeddings": embedding_info,
            "default_backend": self.backend_type,
        }

    # Convenience properties for direct access to underlying components
    @property
    def vectorstore(self):
        """Access to underlying LangChain VectorStore."""
        return self.manager.vectorstore

    def __repr__(self) -> str:
        """String representation of VectorStore."""
        return (
            f"VectorStore(backend_type='{self.backend_type}', "
            f"embeddings={type(self.embeddings).__name__})"
        )
