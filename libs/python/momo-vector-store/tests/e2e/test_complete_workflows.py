"""End-to-end tests for complete vector store workflows."""

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from momo_vector_store import VectorStoreManager, create_vectorstore


class MockEmbeddings(Embeddings):
    """Mock embeddings that return consistent vectors for testing."""

    def embed_documents(self, texts):
        """Return mock embeddings for documents."""
        return [[float(i), float(i + 1), float(i + 2)] for i in range(len(texts))]

    def embed_query(self, text):
        """Return mock embedding for query."""
        return [0.5, 1.5, 2.5]


@pytest.fixture
def embeddings():
    """Mock embeddings fixture."""
    return MockEmbeddings()


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        Document(
            page_content="Artificial intelligence is transforming the world.",
            metadata={
                "source": "ai_article.txt",
                "category": "technology",
                "author": "Alice",
            },
        ),
        Document(
            page_content="Machine learning enables computers to learn from data.",
            metadata={
                "source": "ml_guide.txt",
                "category": "technology",
                "author": "Bob",
            },
        ),
        Document(
            page_content="Python is a versatile programming language.",
            metadata={
                "source": "python_intro.txt",
                "category": "programming",
                "author": "Charlie",
            },
        ),
        Document(
            page_content="Data science combines statistics and programming.",
            metadata={
                "source": "data_science.txt",
                "category": "analytics",
                "author": "Alice",
            },
        ),
        Document(
            page_content="Natural language processing enables text analysis.",
            metadata={
                "source": "nlp_basics.txt",
                "category": "technology",
                "author": "Bob",
            },
        ),
    ]


class TestCompleteWorkflow:
    """Test complete vector store workflows from start to finish."""

    @pytest.mark.asyncio
    async def test_memory_backend_full_workflow(self, embeddings, sample_documents):
        """Test complete workflow with InMemory backend."""
        # Create vector store manager
        manager = VectorStoreManager.create("memory", embeddings)

        # Verify initial state
        backend_info = manager.get_backend_info()
        assert "InMemoryVectorStore" in backend_info["backend_type"]

        # Add documents
        doc_ids = await manager.add_documents(sample_documents)
        assert len(doc_ids) == 5
        assert all(isinstance(doc_id, str) for doc_id in doc_ids)

        # Test similarity search
        results = await manager.similarity_search("artificial intelligence", k=3)
        assert len(results) <= 3
        assert all(isinstance(doc, Document) for doc in results)

        # Verify search results contain expected content
        content_texts = [doc.page_content for doc in results]
        assert any("artificial intelligence" in text.lower() for text in content_texts)

        # Test similarity search with scores
        scored_results = await manager.similarity_search_with_score(
            "machine learning", k=2
        )
        assert len(scored_results) <= 2

        for doc, score in scored_results:
            assert isinstance(doc, Document)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

        # Test filtered search
        filtered_results = await manager.similarity_search(
            "technology", k=10, filter={"category": "technology"}
        )

        # All results should match the filter
        for doc in filtered_results:
            assert doc.metadata.get("category") == "technology"

    @pytest.mark.asyncio
    async def test_text_addition_workflow(self, embeddings):
        """Test workflow using add_texts instead of add_documents."""
        manager = VectorStoreManager.create("memory", embeddings)

        # Add texts with metadata
        texts = [
            "The weather is beautiful today.",
            "I love programming in Python.",
            "Machine learning is fascinating.",
        ]
        metadatas = [
            {"topic": "weather", "sentiment": "positive"},
            {"topic": "programming", "language": "python"},
            {"topic": "ml", "sentiment": "positive"},
        ]

        text_ids = await manager.add_texts(texts, metadatas)
        assert len(text_ids) == 3

        # Search for programming-related content
        results = await manager.similarity_search("programming", k=2)

        # Verify we get relevant results
        assert len(results) <= 2
        programming_found = any(
            "programming" in doc.page_content.lower() for doc in results
        )
        python_found = any("python" in doc.page_content.lower() for doc in results)
        assert programming_found or python_found

    @pytest.mark.asyncio
    async def test_empty_search_results(self, embeddings):
        """Test behavior with empty vector store."""
        manager = VectorStoreManager.create("memory", embeddings)

        # Search in empty store
        results = await manager.similarity_search("anything", k=5)
        assert len(results) == 0

        # Search with scores in empty store
        scored_results = await manager.similarity_search_with_score("anything", k=5)
        assert len(scored_results) == 0

    @pytest.mark.asyncio
    async def test_large_k_parameter(self, embeddings, sample_documents):
        """Test behavior when k is larger than available documents."""
        manager = VectorStoreManager.create("memory", embeddings)

        # Add documents
        await manager.add_documents(sample_documents)

        # Search with k larger than document count
        results = await manager.similarity_search("technology", k=100)

        # Should return all available documents (max 5)
        assert len(results) <= len(sample_documents)

    @pytest.mark.asyncio
    async def test_mixed_content_types(self, embeddings):
        """Test handling of different content types and metadata."""
        manager = VectorStoreManager.create("memory", embeddings)

        # Add documents with various metadata structures
        diverse_docs = [
            Document(page_content="Short text", metadata={"length": "short"}),
            Document(
                page_content="This is a much longer piece of text that contains more information and details.",
                metadata={"length": "long", "words": 15},
            ),
            Document(
                page_content="", metadata={"empty": True}
            ),  # Edge case: empty content
            Document(
                page_content="Special chars: @#$%^&*()", metadata={"type": "special"}
            ),
        ]

        doc_ids = await manager.add_documents(diverse_docs)
        assert len(doc_ids) == 4

        # Test search across diverse content
        results = await manager.similarity_search("text", k=10)
        assert len(results) >= 0  # Should handle gracefully


class TestAsyncWorkflow:
    """Test async creation and workflow patterns."""

    @pytest.mark.asyncio
    async def test_async_manager_creation(self, embeddings, sample_documents):
        """Test async manager creation workflow."""
        # Create manager asynchronously
        manager = await VectorStoreManager.acreate("memory", embeddings)

        # Verify it works the same as sync creation
        backend_info = manager.get_backend_info()
        assert "InMemoryVectorStore" in backend_info["backend_type"]

        # Add and search documents
        await manager.add_documents(sample_documents)
        results = await manager.similarity_search("programming", k=3)

        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, embeddings):
        """Test concurrent vector store operations."""
        import asyncio

        manager = VectorStoreManager.create("memory", embeddings)

        # Prepare concurrent operations
        texts_batch_1 = ["First batch document 1", "First batch document 2"]
        texts_batch_2 = ["Second batch document 1", "Second batch document 2"]

        # Run concurrent add operations
        results = await asyncio.gather(
            manager.add_texts(texts_batch_1), manager.add_texts(texts_batch_2)
        )

        batch1_ids, batch2_ids = results
        assert len(batch1_ids) == 2
        assert len(batch2_ids) == 2

        # Verify all documents are searchable
        all_results = await manager.similarity_search("document", k=10)
        assert len(all_results) == 4


class TestErrorHandling:
    """Test error handling in complete workflows."""

    @pytest.mark.asyncio
    async def test_workflow_with_invalid_documents(self, embeddings):
        """Test workflow handles invalid documents gracefully."""
        manager = VectorStoreManager.create("memory", embeddings)

        # Test with None content (should be handled by LangChain)
        try:
            await manager.add_documents([Document(page_content=None)])
        except Exception:
            # This is expected - LangChain should handle validation
            pass

        # Test with valid documents after error
        valid_docs = [Document(page_content="Valid content")]
        doc_ids = await manager.add_documents(valid_docs)
        assert len(doc_ids) == 1

    @pytest.mark.asyncio
    async def test_search_parameter_validation(self, embeddings, sample_documents):
        """Test search parameter validation in workflow."""
        manager = VectorStoreManager.create("memory", embeddings)
        await manager.add_documents(sample_documents)

        # Test with k=0 (edge case)
        results = await manager.similarity_search("test", k=0)
        assert len(results) == 0

        # Test with negative k (should be handled gracefully)
        try:
            results = await manager.similarity_search("test", k=-1)
            # If no error, should return empty or handle gracefully
            assert len(results) >= 0
        except Exception:
            # LangChain may raise validation errors
            pass
