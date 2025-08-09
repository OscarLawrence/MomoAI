"""
Core unified knowledge base implementation.

This module provides the core implementation that combines vector, graph,
and document storage backends behind a unified interface.
"""

from typing import List, Dict, Any, Optional
from langchain_core.embeddings import Embeddings

from .base import BaseKnowledgeBase
from .types import (
    Document,
    DocumentMetadata,
    SearchResult,
    SearchOptions,
    QueryStrategy,
    IndexingPipeline,
)
from .exceptions import KnowledgeBaseError, DocumentNotFoundError, SearchError


class CoreKnowledgeBase(BaseKnowledgeBase):
    """
    Main KnowledgeBase class - the primary public interface.

    This is the main class users should instantiate. It provides a flexible,
    modular knowledge base that can combine vector search, graph traversal,
    and document storage behind a unified interface.

    Features:
    - Simple, intuitive API for document storage and retrieval
    - Pluggable storage backends (vector, graph, document)
    - Configurable query strategies
    - Async-first design with sync wrappers
    - Context manager support
    - Advanced filtering and search options

    Example:
        ```python
        from momo_kb import KnowledgeBase, Document

        # Basic usage
        kb = KnowledgeBase()

        # Save documents
        doc = Document(content="Hello world", metadata={"type": "greeting"})
        await kb.save(doc)

        # Search
        results = await kb.search("greeting")
        ```
    """

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        vector_backend=None,
        graph_backend=None,
        document_backend=None,
        indexing_pipeline: Optional[IndexingPipeline] = None,
        default_strategy: QueryStrategy = QueryStrategy.AUTO,
    ):
        """
        Initialize the core knowledge base.

        Args:
            embeddings: Embedding model for vector operations
            vector_backend: Vector storage backend (string or instance, defaults to 'memory')
            graph_backend: Graph storage backend (string or instance, defaults to 'memory')
            document_backend: Document storage backend (string or instance, defaults to 'memory')
            indexing_pipeline: Configuration for document processing
            default_strategy: Default query strategy
        """
        super().__init__(
            embeddings=embeddings,
            vector_backend=vector_backend,
            graph_backend=graph_backend,
            document_backend=document_backend,
            indexing_pipeline=indexing_pipeline,
            default_strategy=default_strategy,
        )

    async def save(self, *documents: Document) -> List[str]:
        """Save documents to all configured backends."""
        try:
            saved_ids = []
            lc_documents = []

            for doc in documents:
                self._document_metadata[doc.id] = doc
                saved_ids.append(doc.id)

                lc_doc = self._document_to_langchain(doc)
                lc_documents.append(lc_doc)

                await self.document_backend.put(
                    doc.id,
                    {
                        "content": doc.content,
                        "metadata": doc.metadata.model_dump(exclude_none=True),
                    },
                )

                await self.graph_backend.add_node(
                    doc.id, doc.metadata.model_dump(exclude_none=True)
                )

                relationships = await self._extract_relationships(doc)
                for source_id, target_id, rel_type, properties in relationships:
                    await self.graph_backend.add_relationship(
                        source_id, target_id, rel_type, properties
                    )

            if self.vector_backend and lc_documents:
                await self.vector_backend.add_documents(lc_documents)

            return saved_ids

        except Exception as e:
            raise KnowledgeBaseError(f"Failed to save documents: {e}") from e

    async def search(
        self,
        query: str,
        options: Optional[SearchOptions] = None,
        strategy: Optional[QueryStrategy] = None,
        **kwargs,
    ) -> List[SearchResult]:
        """Search using specified or auto-detected strategy."""
        if options is None:
            options = SearchOptions()

        # Override with kwargs
        for key, value in kwargs.items():
            if hasattr(options, key):
                setattr(options, key, value)

        strategy = strategy or self.default_strategy
        if strategy == QueryStrategy.AUTO:
            strategy = self._determine_strategy(query, options)

        try:
            if strategy == QueryStrategy.VECTOR_ONLY:
                if self.vector_backend:
                    return await self._vector_search(query, options)
                else:
                    return await self._document_search(query, options)
            elif strategy == QueryStrategy.GRAPH_ONLY:
                return await self._graph_search(query, options)
            elif strategy == QueryStrategy.HYBRID:
                return await self._hybrid_search(query, options)
            else:
                if self.vector_backend:
                    return await self._vector_search(query, options)
                else:
                    return await self._document_search(query, options)

        except Exception as e:
            raise SearchError(f"Search failed: {e}") from e

    async def get(self, document_id: str) -> Document:
        """Get document by ID."""
        if document_id in self._document_metadata:
            return self._document_metadata[document_id]

        doc_data = await self.document_backend.get(document_id)
        if doc_data:
            metadata = DocumentMetadata(**doc_data.get("metadata", {}))
            document = Document(
                id=doc_data["id"], content=doc_data["content"], metadata=metadata
            )
            self._document_metadata[document_id] = document
            return document

        raise DocumentNotFoundError(document_id)

    async def delete(self, document_id: str) -> bool:
        """Delete document from all backends."""
        try:
            success = True

            if document_id in self._document_metadata:
                del self._document_metadata[document_id]

            doc_success = await self.document_backend.delete(document_id)
            success = success and doc_success

            if self.vector_backend:
                vector_success = await self.vector_backend.delete([document_id])
                success = success and vector_success

            return success

        except Exception:
            return False

    async def update(self, document: Document) -> bool:
        """Update existing document."""
        try:
            existing = await self.get(document.id)
            if not existing:
                return False

            await self.delete(document.id)
            await self.save(document)

            return True

        except DocumentNotFoundError:
            return False
        except Exception:
            return False

    async def list_documents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """List documents with filtering."""
        try:
            scan_results = await self.document_backend.scan(filters=filters)

            documents = []
            for item in scan_results[offset : offset + limit]:
                if item.get("key") in self._document_metadata:
                    documents.append(self._document_metadata[item["key"]])

            return documents

        except Exception as e:
            raise KnowledgeBaseError(f"Failed to list documents: {e}") from e

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching filters."""
        try:
            scan_results = await self.document_backend.scan(filters=filters)
            return len(scan_results)
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to count documents: {e}") from e

    # Convenience methods with sync wrappers
    def search_sync(self, query: str, **kwargs) -> List[SearchResult]:
        """Synchronous wrapper for search."""
        import asyncio

        options = SearchOptions(**kwargs) if kwargs else None
        return asyncio.run(self.search(query, options))

    def save_sync(self, *documents: Document) -> List[str]:
        """Synchronous wrapper for save."""
        import asyncio

        return asyncio.run(self.save(*documents))

    def get_sync(self, document_id: str) -> Document:
        """Synchronous wrapper for get."""
        import asyncio

        return asyncio.run(self.get(document_id))

    def delete_sync(self, document_id: str) -> bool:
        """Synchronous wrapper for delete."""
        import asyncio

        return asyncio.run(self.delete(document_id))

    def update_sync(self, document: Document) -> bool:
        """Synchronous wrapper for update."""
        import asyncio

        return asyncio.run(self.update(document))

    def list_documents_sync(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """Synchronous wrapper for list_documents."""
        import asyncio

        return asyncio.run(self.list_documents(filters, limit, offset))

    def count_sync(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Synchronous wrapper for count."""
        import asyncio

        return asyncio.run(self.count(filters))

    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Async context manager exit."""
        # Close any backend connections if they support it
        if hasattr(self.document_backend, "close"):
            await self.document_backend.close()
        pass

    def __enter__(self):
        """Sync context manager entry."""
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Sync context manager exit."""
        import asyncio

        if hasattr(self.document_backend, "close"):
            asyncio.run(self.document_backend.close())
        pass
