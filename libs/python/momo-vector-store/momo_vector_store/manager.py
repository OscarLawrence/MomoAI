"""
VectorStoreManager for advanced vector store operations.

This module provides the VectorStoreManager class for users who need
direct access to the underlying LangChain VectorStore operations.
"""

from typing import Any, List, Dict, Optional, Callable, Union
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore as LangChainVectorStore

from .factory import create_vectorstore, acreate_vectorstore
from .exceptions import VectorStoreError


class VectorStoreManager:
    """
    Advanced manager for vector store operations.

    Provides a unified interface for common vector store operations
    while maintaining access to the underlying LangChain VectorStore.

    For simple use cases, prefer the VectorStore class from main.py.
    This class is for advanced users who need direct control over
    the underlying LangChain VectorStore operations.
    """

    def __init__(self, vectorstore: LangChainVectorStore):
        """Initialize with a LangChain VectorStore instance."""
        self.vectorstore = vectorstore

    @classmethod
    def create(
        cls, backend_type: str, embeddings: Embeddings, **config: Any
    ) -> "VectorStoreManager":
        """Create manager with specified backend."""
        vectorstore = create_vectorstore(backend_type, embeddings, **config)
        return cls(vectorstore)

    @classmethod
    async def acreate(
        cls, backend_type: str, embeddings: Embeddings, **config: Any
    ) -> "VectorStoreManager":
        """Async create manager with specified backend."""
        vectorstore = await acreate_vectorstore(backend_type, embeddings, **config)
        return cls(vectorstore)

    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add texts to the vector store."""
        try:
            return await self.vectorstore.aadd_texts(
                texts=texts, metadatas=metadatas, ids=ids
            )
        except Exception as e:
            raise VectorStoreError(
                f"Failed to add texts: {str(e)}",
                backend=type(self.vectorstore).__name__,
            ) from e

    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        try:
            return await self.vectorstore.aadd_documents(documents)
        except Exception as e:
            raise VectorStoreError(
                f"Failed to add documents: {str(e)}",
                backend=type(self.vectorstore).__name__,
            ) from e

    async def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Perform similarity search."""
        try:
            # Convert dict filter to callable for LangChain compatibility
            search_filter: Any = None
            if filter and isinstance(filter, dict):

                def filter_func(doc):
                    return all(doc.metadata.get(k) == v for k, v in filter.items())

                search_filter = filter_func
            else:
                search_filter = filter

            return await self.vectorstore.asimilarity_search(
                query=query, k=k, filter=search_filter, **kwargs
            )
        except Exception as e:
            raise VectorStoreError(
                f"Search failed: {str(e)}", backend=type(self.vectorstore).__name__
            ) from e

    async def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[tuple[Document, float]]:
        """Perform similarity search with relevance scores."""
        try:
            # Convert dict filter to callable for LangChain compatibility
            search_filter: Any = None
            if filter and isinstance(filter, dict):

                def filter_func(doc):
                    return all(doc.metadata.get(k) == v for k, v in filter.items())

                search_filter = filter_func
            else:
                search_filter = filter

            return await self.vectorstore.asimilarity_search_with_score(
                query=query, k=k, filter=search_filter, **kwargs
            )
        except Exception as e:
            raise VectorStoreError(
                f"Search with score failed: {str(e)}",
                backend=type(self.vectorstore).__name__,
            ) from e

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the current backend."""
        return {
            "backend_type": type(self.vectorstore).__name__,
            "backend_module": type(self.vectorstore).__module__,
        }
