"""Integration tests for backend switching and compatibility."""

import pytest
from unittest.mock import patch, Mock
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from momo_vector_store import VectorStoreManager, create_vectorstore
from momo_vector_store.exceptions import BackendError


class TestEmbeddings(Embeddings):
    """Test embeddings that return predictable vectors."""

    def embed_documents(self, texts):
        """Return consistent embeddings for documents."""
        return [[0.1 * i, 0.2 * i, 0.3 * i] for i in range(1, len(texts) + 1)]

    def embed_query(self, text):
        """Return consistent embedding for queries."""
        return [0.15, 0.25, 0.35]


@pytest.fixture
def embeddings():
    """Test embeddings fixture."""
    return TestEmbeddings()


@pytest.fixture
def test_documents():
    """Test documents for backend switching tests."""
    return [
        Document(
            page_content="Vector databases enable semantic search capabilities.",
            metadata={"topic": "vector_db", "difficulty": "beginner"},
        ),
        Document(
            page_content="Embedding models convert text into numerical representations.",
            metadata={"topic": "embeddings", "difficulty": "intermediate"},
        ),
        Document(
            page_content="Similarity search finds related documents using vector distance.",
            metadata={"topic": "search", "difficulty": "advanced"},
        ),
    ]


class TestMemoryBackendIntegration:
    """Test InMemory backend integration."""

    @pytest.mark.asyncio
    async def test_memory_backend_full_integration(self, embeddings, test_documents):
        """Test complete integration with InMemory backend."""
        # Create manager with memory backend
        manager = VectorStoreManager.create("memory", embeddings)

        # Verify backend type
        info = manager.get_backend_info()
        assert "InMemoryVectorStore" in info["backend_type"]

        # Add documents
        doc_ids = await manager.add_documents(test_documents)
        assert len(doc_ids) == 3

        # Test search functionality
        results = await manager.similarity_search("vector search", k=2)
        assert len(results) <= 2

        # Test search with metadata filter
        filtered_results = await manager.similarity_search(
            "search", k=5, filter={"topic": "vector_db"}
        )

        for doc in filtered_results:
            assert doc.metadata.get("topic") == "vector_db"

    @pytest.mark.asyncio
    async def test_memory_backend_with_scores(self, embeddings, test_documents):
        """Test InMemory backend with similarity scores."""
        manager = VectorStoreManager.create("memory", embeddings)
        await manager.add_documents(test_documents)

        # Test scored search
        scored_results = await manager.similarity_search_with_score("embedding", k=3)

        assert len(scored_results) <= 3
        for doc, score in scored_results:
            assert isinstance(doc, Document)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0


class TestBackendSwitching:
    """Test switching between different backends."""

    def test_factory_backend_switching(self, embeddings):
        """Test that factory can create different backend types."""
        # Test memory backend creation
        memory_store = create_vectorstore("memory", embeddings)
        assert "InMemoryVectorStore" in str(type(memory_store))

        # Test that different backend types can be requested
        with pytest.raises(BackendError) as exc_info:
            create_vectorstore("unsupported_backend", embeddings)

        assert "Unsupported backend type" in str(exc_info.value)
        assert exc_info.value.backend == "unsupported_backend"

    def test_manager_backend_switching(self, embeddings):
        """Test creating managers with different backends."""
        # Create memory backend manager
        memory_manager = VectorStoreManager.create("memory", embeddings)
        memory_info = memory_manager.get_backend_info()

        assert "InMemoryVectorStore" in memory_info["backend_type"]

        # Test that the same interface works regardless of backend
        assert hasattr(memory_manager, "add_texts")
        assert hasattr(memory_manager, "add_documents")
        assert hasattr(memory_manager, "similarity_search")
        assert hasattr(memory_manager, "similarity_search_with_score")

    @pytest.mark.asyncio
    async def test_consistent_interface_across_backends(
        self, embeddings, test_documents
    ):
        """Test that interface is consistent across different backends."""
        # Test with memory backend
        memory_manager = VectorStoreManager.create("memory", embeddings)

        # Add documents and search
        await memory_manager.add_documents(test_documents)
        memory_results = await memory_manager.similarity_search("vector", k=2)

        assert len(memory_results) <= 2
        assert all(isinstance(doc, Document) for doc in memory_results)

        # Verify that results have expected structure
        for doc in memory_results:
            assert hasattr(doc, "page_content")
            assert hasattr(doc, "metadata")
            assert isinstance(doc.page_content, str)
            assert isinstance(doc.metadata, dict)


class TestBackendConfiguration:
    """Test backend-specific configuration handling."""

    def test_memory_backend_config_ignored(self, embeddings):
        """Test that InMemory backend ignores extra config gracefully."""
        # InMemory backend should ignore extra configuration
        manager = VectorStoreManager.create(
            "memory",
            embeddings,
            # These config options are for other backends
            persist_directory="/tmp/test",
            collection_name="test_collection",
            url="http://localhost:8080",
        )

        info = manager.get_backend_info()
        assert "InMemoryVectorStore" in info["backend_type"]

    def test_chroma_backend_config_validation(self, embeddings):
        """Test Chroma backend configuration (without actual Chroma)."""
        # Test that Chroma backend would be configured correctly if available
        with pytest.raises(BackendError) as exc_info:
            VectorStoreManager.create(
                "chroma",
                embeddings,
                collection_name="test_collection",
                persist_directory="/tmp/chroma_test",
            )

        # Should fail because Chroma is not installed
        assert "Chroma not available" in str(exc_info.value)
        assert exc_info.value.backend == "chroma"

    def test_weaviate_backend_config_validation(self, embeddings):
        """Test Weaviate backend configuration (without actual Weaviate)."""
        # Test that Weaviate backend would be configured correctly if available
        with pytest.raises(BackendError) as exc_info:
            VectorStoreManager.create(
                "weaviate",
                embeddings,
                url="http://localhost:8080",
                index_name="TestIndex",
            )

        # Should fail because Weaviate is not installed
        assert "Weaviate not available" in str(exc_info.value)
        assert exc_info.value.backend == "weaviate"

    def test_milvus_backend_config_validation(self, embeddings):
        """Test Milvus backend configuration (without actual Milvus)."""
        # Test that Milvus backend would be configured correctly if available
        with pytest.raises(BackendError) as exc_info:
            VectorStoreManager.create(
                "milvus",
                embeddings,
                connection_args={"host": "localhost", "port": "19530"},
                collection_name="momo_collection",
            )

        # Should fail because Milvus is not installed
        assert "Milvus not available" in str(exc_info.value)
        assert exc_info.value.backend == "milvus"


class TestBackendErrorHandling:
    """Test error handling across different backends."""

    @pytest.mark.asyncio
    async def test_memory_backend_error_consistency(self, embeddings):
        """Test that memory backend errors are handled consistently."""
        manager = VectorStoreManager.create("memory", embeddings)

        # Test error handling in add operations
        with patch.object(
            manager.vectorstore, "aadd_texts", side_effect=Exception("Mock error")
        ):
            with pytest.raises(
                Exception
            ):  # Should be VectorStoreError in real scenarios
                await manager.add_texts(["test"])

    def test_backend_creation_error_handling(self, embeddings):
        """Test error handling during backend creation."""
        # Test with completely invalid backend type
        with pytest.raises(BackendError) as exc_info:
            create_vectorstore("invalid_backend", embeddings)

        assert exc_info.value.backend == "invalid_backend"
        assert "Unsupported backend type" in str(exc_info.value)

        # Test with None backend type
        with pytest.raises(Exception):
            create_vectorstore(None, embeddings)


class TestAsyncBackendOperations:
    """Test async operations across backends."""

    @pytest.mark.asyncio
    async def test_async_manager_creation_consistency(self, embeddings):
        """Test that async manager creation is consistent."""
        # Test async creation
        async_manager = await VectorStoreManager.acreate("memory", embeddings)
        sync_manager = VectorStoreManager.create("memory", embeddings)

        # Both should have same backend type
        async_info = async_manager.get_backend_info()
        sync_info = sync_manager.get_backend_info()

        assert async_info["backend_type"] == sync_info["backend_type"]
        assert "InMemoryVectorStore" in async_info["backend_type"]

    @pytest.mark.asyncio
    async def test_concurrent_backend_operations(self, embeddings, test_documents):
        """Test concurrent operations with backend."""
        import asyncio

        manager = VectorStoreManager.create("memory", embeddings)

        # Split documents for concurrent operations
        docs_batch1 = test_documents[:2]
        docs_batch2 = test_documents[2:]

        # Run concurrent add operations
        results = await asyncio.gather(
            manager.add_documents(docs_batch1),
            manager.add_documents(docs_batch2),
            return_exceptions=True,
        )

        # Both operations should succeed
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent operation failed: {result}")
            else:
                assert len(result) >= 1  # Should return document IDs

        # Test concurrent searches
        search_results = await asyncio.gather(
            manager.similarity_search("vector", k=1),
            manager.similarity_search("embedding", k=1),
            manager.similarity_search("search", k=1),
            return_exceptions=True,
        )

        for result in search_results:
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent search failed: {result}")
            else:
                assert isinstance(result, list)
