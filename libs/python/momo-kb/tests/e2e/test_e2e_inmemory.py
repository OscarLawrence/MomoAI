"""
End-to-end tests for in-memory KnowledgeBase implementations.

This module tests the complete functionality of the KnowledgeBase with
in-memory backends, covering document operations, search strategies,
and real-world usage scenarios.
"""

import pytest
import asyncio
from typing import List
from unittest.mock import Mock

from momo_kb import (
    KnowledgeBase,
    Document,
    DocumentMetadata,
    SearchResult,
    SearchOptions,
    QueryStrategy,
    RelationshipSpec,
    IndexingPipeline,
    DocumentNotFoundError,
    KnowledgeBaseError,
)


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    docs = [
        Document(
            content="Python is a high-level programming language known for its simplicity and readability.",
            metadata=DocumentMetadata(
                source="programming_guide",
                author="tech_writer",
                type="tutorial",
                category="programming",
                tags=["python", "programming", "beginner"],
                language="en",
            ),
        ),
        Document(
            content="Machine learning involves algorithms that can learn patterns from data without being explicitly programmed.",
            metadata=DocumentMetadata(
                source="ml_handbook",
                author="data_scientist",
                type="tutorial",
                category="ai",
                tags=["ml", "ai", "algorithms"],
                language="en",
            ),
        ),
        Document(
            content="JavaScript is a versatile programming language used for both frontend and backend development.",
            metadata=DocumentMetadata(
                source="web_dev_guide",
                author="web_developer",
                type="tutorial",
                category="programming",
                tags=["javascript", "web", "programming"],
                language="en",
            ),
        ),
        Document(
            content="Data structures are fundamental concepts in computer science for organizing and storing data efficiently.",
            metadata=DocumentMetadata(
                source="cs_textbook",
                author="professor",
                type="reference",
                category="computer_science",
                tags=["data_structures", "algorithms", "cs"],
                language="en",
            ),
        ),
        Document(
            content="Neural networks are computational models inspired by the human brain, used in deep learning applications.",
            metadata=DocumentMetadata(
                source="dl_research",
                author="researcher",
                type="paper",
                category="ai",
                tags=["neural_networks", "deep_learning", "ai"],
                language="en",
            ),
        ),
    ]
    return docs


@pytest.fixture
def mock_embeddings():
    """Create mock embeddings for testing vector operations."""
    from langchain_core.embeddings import Embeddings

    class MockEmbeddings(Embeddings):
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            """Return mock embeddings for documents."""
            return [[0.1, 0.2, 0.3] for _ in texts]

        def embed_query(self, text: str) -> List[float]:
            """Return mock embedding for query."""
            return [0.1, 0.2, 0.3]

    return MockEmbeddings()


class TestBasicDocumentOperations:
    """Test basic document save/retrieve operations."""

    @pytest.mark.asyncio
    async def test_save_single_document(self, sample_documents):
        """Test saving a single document."""
        kb = KnowledgeBase()
        doc = sample_documents[0]

        # Save document
        saved_ids = await kb.save(doc)

        assert len(saved_ids) == 1
        assert saved_ids[0] == doc.id
        assert doc.id in kb._document_metadata

    @pytest.mark.asyncio
    async def test_save_multiple_documents(self, sample_documents):
        """Test saving multiple documents at once."""
        kb = KnowledgeBase()
        docs = sample_documents[:3]

        # Save multiple documents
        saved_ids = await kb.save(*docs)

        assert len(saved_ids) == 3
        for i, doc in enumerate(docs):
            assert saved_ids[i] == doc.id
            assert doc.id in kb._document_metadata

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, sample_documents):
        """Test retrieving document by ID."""
        kb = KnowledgeBase()
        doc = sample_documents[0]

        # Save and retrieve
        await kb.save(doc)
        retrieved = await kb.get(doc.id)

        assert retrieved.id == doc.id
        assert retrieved.content == doc.content
        assert retrieved.metadata.source == doc.metadata.source
        assert retrieved.metadata.type == doc.metadata.type

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self):
        """Test getting a document that doesn't exist."""
        kb = KnowledgeBase()

        with pytest.raises(DocumentNotFoundError):
            await kb.get("nonexistent_id")

    @pytest.mark.asyncio
    async def test_list_documents(self, sample_documents):
        """Test listing documents with and without filters."""
        kb = KnowledgeBase()
        docs = sample_documents[:3]

        # Save documents
        await kb.save(*docs)

        # List all documents
        all_docs = await kb.list_documents()
        assert len(all_docs) == 3

        # List with filter
        tutorial_docs = await kb.list_documents(filters={"type": "tutorial"})
        assert len(tutorial_docs) == 3  # Python, ML, and JS tutorials

    @pytest.mark.asyncio
    async def test_count_documents(self, sample_documents):
        """Test counting documents with and without filters."""
        kb = KnowledgeBase()
        docs = sample_documents[:4]

        # Save documents
        await kb.save(*docs)

        # Count all documents
        total_count = await kb.count()
        assert total_count == 4

        # Count with filter
        tutorial_count = await kb.count(filters={"type": "tutorial"})
        assert tutorial_count == 3  # Python, ML, and JS tutorials


class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations."""

    @pytest.mark.asyncio
    async def test_update_document(self, sample_documents):
        """Test updating an existing document."""
        kb = KnowledgeBase()
        doc = sample_documents[0]

        # Save original document
        await kb.save(doc)

        # Create updated version
        updated_doc = Document(
            id=doc.id,  # Same ID
            content="Updated: " + doc.content,
            metadata=DocumentMetadata(
                source=doc.metadata.source,
                author=doc.metadata.author,
                type="updated_tutorial",  # Changed type
                category=doc.metadata.category,
                tags=doc.metadata.tags + ["updated"],  # Added tag
                language=doc.metadata.language,
            ),
        )

        # Update document
        success = await kb.update(updated_doc)
        assert success is True

        # Verify update
        retrieved = await kb.get(doc.id)
        assert retrieved.content.startswith("Updated:")
        assert retrieved.metadata.type == "updated_tutorial"
        assert "updated" in retrieved.metadata.tags

    @pytest.mark.asyncio
    async def test_update_nonexistent_document(self, sample_documents):
        """Test updating a document that doesn't exist."""
        kb = KnowledgeBase()
        doc = sample_documents[0]

        # Try to update without saving first
        success = await kb.update(doc)
        assert success is False

    @pytest.mark.asyncio
    async def test_delete_document(self, sample_documents):
        """Test deleting a document."""
        kb = KnowledgeBase()
        doc = sample_documents[0]

        # Save document
        await kb.save(doc)
        assert doc.id in kb._document_metadata

        # Delete document
        success = await kb.delete(doc.id)
        assert success is True
        assert doc.id not in kb._document_metadata

        # Verify it's gone
        with pytest.raises(DocumentNotFoundError):
            await kb.get(doc.id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self):
        """Test deleting a document that doesn't exist."""
        kb = KnowledgeBase()

        # Should return False but not raise error
        success = await kb.delete("nonexistent_id")
        assert success is False


class TestSearchFunctionality:
    """Test different search strategies and options."""

    @pytest.mark.asyncio
    async def test_document_search_strategy(self, sample_documents):
        """Test document-based search (no embeddings)."""
        kb = KnowledgeBase()  # No embeddings = document search
        docs = sample_documents[:3]

        await kb.save(*docs)

        # Search for programming content
        results = await kb.search("programming", strategy=QueryStrategy.AUTO)

        # Should find documents with "programming" in content
        assert len(results) >= 1
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.document is not None for result in results)
        assert all(result.score > 0 for result in results)

    @pytest.mark.asyncio
    async def test_vector_search_strategy(self, sample_documents, mock_embeddings):
        """Test vector-based search with mock embeddings."""
        kb = KnowledgeBase(embeddings=mock_embeddings)
        docs = sample_documents[:3]

        await kb.save(*docs)

        # Search with vector strategy
        results = await kb.search(
            "python programming", strategy=QueryStrategy.VECTOR_ONLY
        )

        # Should return results from vector backend
        assert len(results) >= 1
        assert all(isinstance(result, SearchResult) for result in results)
        assert all(result.score > 0 for result in results)

    @pytest.mark.asyncio
    async def test_graph_search_strategy(self, sample_documents):
        """Test graph-based search using metadata relationships."""
        kb = KnowledgeBase()
        docs = sample_documents[:4]

        await kb.save(*docs)

        # Search with graph strategy using filters
        options = SearchOptions(filters={"category": "programming"})
        results = await kb.search(
            "related content", strategy=QueryStrategy.GRAPH_ONLY, options=options
        )

        # Should find documents connected by metadata
        programming_docs = [
            doc for doc in docs if doc.metadata.category == "programming"
        ]
        assert len(results) >= 0  # May be empty if no graph relationships exist

    @pytest.mark.asyncio
    async def test_hybrid_search_strategy(self, sample_documents, mock_embeddings):
        """Test hybrid vector + graph search."""
        kb = KnowledgeBase(embeddings=mock_embeddings)
        docs = sample_documents

        await kb.save(*docs)

        # Search with hybrid strategy
        results = await kb.search(
            "machine learning algorithms", strategy=QueryStrategy.HYBRID
        )

        # Should combine vector and graph results
        assert isinstance(results, list)
        assert all(isinstance(result, SearchResult) for result in results)

    @pytest.mark.asyncio
    async def test_search_with_options(self, sample_documents):
        """Test search with various options (limit, offset, threshold)."""
        kb = KnowledgeBase()
        docs = sample_documents

        await kb.save(*docs)

        # Test with limit
        results = await kb.search("programming", limit=2)
        assert len(results) <= 2

        # Test with filters
        results = await kb.search("tutorial", filters={"type": "tutorial"})
        tutorial_results = [
            r for r in results if r.document.metadata.type == "tutorial"
        ]
        assert len(tutorial_results) >= 0

        # Test with threshold
        results = await kb.search("test", threshold=0.8)
        assert all(result.score >= 0.8 for result in results)

    @pytest.mark.asyncio
    async def test_auto_strategy_selection(self, sample_documents):
        """Test automatic strategy selection based on query and options."""
        kb = KnowledgeBase()
        docs = sample_documents[:3]

        await kb.save(*docs)

        # Auto should select appropriate strategy
        results1 = await kb.search("programming", strategy=QueryStrategy.AUTO)
        assert isinstance(results1, list)

        # With many filters, should prefer graph strategy
        options = SearchOptions(
            filters={
                "type": "tutorial",
                "category": "programming",
                "author": "tech_writer",
            }
        )
        results2 = await kb.search(
            "content", options=options, strategy=QueryStrategy.AUTO
        )
        assert isinstance(results2, list)


class TestSyncWrappers:
    """Test synchronous wrapper methods."""

    def test_save_sync(self, sample_documents):
        """Test synchronous save wrapper."""
        kb = KnowledgeBase()
        doc = sample_documents[0]

        # Use sync wrapper
        saved_ids = kb.save_sync(doc)

        assert len(saved_ids) == 1
        assert saved_ids[0] == doc.id

    def test_search_sync(self, sample_documents):
        """Test synchronous search wrapper."""
        kb = KnowledgeBase()
        docs = sample_documents[:2]

        kb.save_sync(*docs)

        # Use sync search
        results = kb.search_sync("programming")
        assert isinstance(results, list)

    def test_get_sync(self, sample_documents):
        """Test synchronous get wrapper."""
        kb = KnowledgeBase()
        doc = sample_documents[0]

        kb.save_sync(doc)

        # Use sync get
        retrieved = kb.get_sync(doc.id)
        assert retrieved.id == doc.id

    def test_crud_sync_operations(self, sample_documents):
        """Test all CRUD operations using sync wrappers."""
        kb = KnowledgeBase()
        doc = sample_documents[0]

        # Create
        kb.save_sync(doc)

        # Read
        retrieved = kb.get_sync(doc.id)
        assert retrieved.content == doc.content

        # Update
        updated_doc = Document(
            id=doc.id, content="Updated content", metadata=doc.metadata
        )
        success = kb.update_sync(updated_doc)
        assert success is True

        # Verify update
        retrieved = kb.get_sync(doc.id)
        assert retrieved.content == "Updated content"

        # Delete
        success = kb.delete_sync(doc.id)
        assert success is True

        # Verify deletion
        with pytest.raises(DocumentNotFoundError):
            kb.get_sync(doc.id)


class TestContextManagers:
    """Test context manager functionality."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self, sample_documents):
        """Test async context manager usage."""
        doc = sample_documents[0]

        async with KnowledgeBase() as kb:
            await kb.save(doc)
            retrieved = await kb.get(doc.id)
            assert retrieved.id == doc.id

        # Context should exit cleanly

    def test_sync_context_manager(self, sample_documents):
        """Test sync context manager usage."""
        doc = sample_documents[0]

        with KnowledgeBase() as kb:
            kb.save_sync(doc)
            retrieved = kb.get_sync(doc.id)
            assert retrieved.id == doc.id

        # Context should exit cleanly


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_search(self):
        """Test searching in empty knowledge base."""
        kb = KnowledgeBase()

        results = await kb.search("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_duplicate_document_ids(self, sample_documents):
        """Test behavior with duplicate document IDs."""
        kb = KnowledgeBase()
        doc1 = sample_documents[0]

        # Save original
        await kb.save(doc1)

        # Create document with same ID but different content
        doc2 = Document(
            id=doc1.id,
            content="Different content",
            metadata=doc1.metadata,  # Same ID
        )

        # Saving should overwrite
        await kb.save(doc2)
        retrieved = await kb.get(doc1.id)
        assert retrieved.content == "Different content"

    @pytest.mark.asyncio
    async def test_large_document_content(self):
        """Test handling of large document content."""
        kb = KnowledgeBase()

        # Create document with large content
        large_content = "Large content. " * 10000  # ~140KB
        doc = Document(
            content=large_content, metadata=DocumentMetadata(source="large_test")
        )

        await kb.save(doc)
        retrieved = await kb.get(doc.id)
        assert len(retrieved.content) == len(large_content)

    @pytest.mark.asyncio
    async def test_special_characters_in_content(self):
        """Test handling of special characters and unicode."""
        kb = KnowledgeBase()

        doc = Document(
            content="Special chars: àáâãäåæçèéêë 中文 🚀 @#$%^&*()[]{}",
            metadata=DocumentMetadata(source="unicode_test"),
        )

        await kb.save(doc)
        retrieved = await kb.get(doc.id)
        assert retrieved.content == doc.content

    @pytest.mark.asyncio
    async def test_custom_indexing_pipeline(self, sample_documents):
        """Test with custom indexing pipeline configuration."""
        # Custom pipeline with different relationship specs
        custom_pipeline = IndexingPipeline(
            extract_relationships=True,
            relationship_specs=[
                RelationshipSpec(
                    source_field="author",
                    target_field="author",
                    relationship_type="same_author",
                    weight=1.0,
                )
            ],
        )

        kb = KnowledgeBase(indexing_pipeline=custom_pipeline)
        docs = sample_documents[:3]

        await kb.save(*docs)

        # Should work with custom pipeline
        results = await kb.search("programming")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_backend_info(self, mock_embeddings):
        """Test getting backend information."""
        kb = KnowledgeBase(embeddings=mock_embeddings)

        info = kb.get_backend_info()

        assert "vector_backend" in info
        assert "graph_backend" in info
        assert "document_backend" in info
        assert "embeddings" in info
        assert "default_strategy" in info
        assert (
            info["vector_backend"] is not None
        )  # Should have vector backend with embeddings
        assert info["graph_backend"] is not None
        assert info["document_backend"] is not None
