"""
Integration tests for DuckDB document backend.

Tests the DuckDB backend integration with the broader KnowledgeBase system,
including real-world usage scenarios and performance characteristics.
"""

import pytest
import asyncio
import tempfile
import os
import shutil

from momo_kb import KnowledgeBase, Document, DocumentMetadata
from momo_store_document import PandasDocumentBackend
from momo_store_document.persistence import DuckDBPersistence


class TestDuckDBKnowledgeBaseIntegration:
    """Test DuckDB backend integrated with KnowledgeBase."""

    @pytest.fixture
    def duckdb_kb(self):
        """Create KnowledgeBase with DuckDB document backend."""
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(":memory:")
        )
        return KnowledgeBase(document_backend=backend)

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            Document(
                content="Python is a versatile programming language used for web development, data science, and automation.",
                metadata=DocumentMetadata(
                    source="python_guide",
                    author="developer",
                    type="tutorial",
                    category="programming",
                    tags=["python", "programming", "tutorial"],
                    language="en",
                ),
            ),
            Document(
                content="Machine learning algorithms can automatically identify patterns in large datasets without explicit programming.",
                metadata=DocumentMetadata(
                    source="ml_course",
                    author="data_scientist",
                    type="course",
                    category="ai",
                    tags=["machine_learning", "ai", "algorithms"],
                    language="en",
                ),
            ),
            Document(
                content="JavaScript enables interactive web applications through dynamic DOM manipulation and event handling.",
                metadata=DocumentMetadata(
                    source="js_tutorial",
                    author="web_developer",
                    type="tutorial",
                    category="programming",
                    tags=["javascript", "web", "frontend"],
                    language="en",
                ),
            ),
        ]

    @pytest.mark.asyncio
    async def test_save_and_retrieve_documents(self, duckdb_kb, sample_documents):
        """Test saving and retrieving documents through KnowledgeBase."""
        # Save documents
        saved_ids = await duckdb_kb.save(*sample_documents)
        assert len(saved_ids) == 3

        # Retrieve each document
        for i, doc in enumerate(sample_documents):
            retrieved = await duckdb_kb.get(saved_ids[i])
            assert retrieved.content == doc.content
            assert retrieved.metadata.source == doc.metadata.source
            assert retrieved.metadata.author == doc.metadata.author

    @pytest.mark.asyncio
    async def test_search_documents(self, duckdb_kb, sample_documents):
        """Test document search functionality."""
        await duckdb_kb.save(*sample_documents)

        # Search for programming content
        results = await duckdb_kb.search("programming")
        programming_results = [
            r for r in results if "programming" in r.document.content.lower()
        ]
        assert len(programming_results) >= 1

        # Search for Python specific content
        results = await duckdb_kb.search("Python")
        python_results = [r for r in results if "Python" in r.document.content]
        assert len(python_results) == 1

    @pytest.mark.asyncio
    async def test_list_documents_with_filters(self, duckdb_kb, sample_documents):
        """Test listing documents with metadata filters."""
        await duckdb_kb.save(*sample_documents)

        # List all documents
        all_docs = await duckdb_kb.list_documents()
        assert len(all_docs) == 3

        # Filter by type
        tutorials = await duckdb_kb.list_documents(filters={"type": "tutorial"})
        assert len(tutorials) == 2
        assert all(doc.metadata.type == "tutorial" for doc in tutorials)

        # Filter by category
        programming_docs = await duckdb_kb.list_documents(
            filters={"category": "programming"}
        )
        assert len(programming_docs) == 2
        assert all(doc.metadata.category == "programming" for doc in programming_docs)

    @pytest.mark.asyncio
    async def test_update_document(self, duckdb_kb, sample_documents):
        """Test updating documents."""
        doc = sample_documents[0]
        saved_ids = await duckdb_kb.save(doc)
        doc_id = saved_ids[0]

        # Update document content and metadata
        updated_doc = Document(
            id=doc_id,
            content="Updated: " + doc.content,
            metadata=DocumentMetadata(
                source=doc.metadata.source,
                author=doc.metadata.author,
                type="updated_tutorial",
                category=doc.metadata.category,
                tags=doc.metadata.tags + ["updated"],
                language=doc.metadata.language,
            ),
        )

        success = await duckdb_kb.update(updated_doc)
        assert success is True

        # Verify update
        retrieved = await duckdb_kb.get(doc_id)
        assert retrieved.content.startswith("Updated:")
        assert retrieved.metadata.type == "updated_tutorial"
        assert "updated" in retrieved.metadata.tags

    @pytest.mark.asyncio
    async def test_delete_document(self, duckdb_kb, sample_documents):
        """Test deleting documents."""
        doc = sample_documents[0]
        saved_ids = await duckdb_kb.save(doc)
        doc_id = saved_ids[0]

        # Verify document exists
        retrieved = await duckdb_kb.get(doc_id)
        assert retrieved is not None

        # Delete document
        success = await duckdb_kb.delete(doc_id)
        assert success is True

        # Verify deletion
        from momo_kb.exceptions import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError):
            await duckdb_kb.get(doc_id)

    @pytest.mark.asyncio
    async def test_count_documents(self, duckdb_kb, sample_documents):
        """Test counting documents with filters."""
        await duckdb_kb.save(*sample_documents)

        # Count all documents
        total = await duckdb_kb.count()
        assert total == 3

        # Count with filters
        tutorial_count = await duckdb_kb.count(filters={"type": "tutorial"})
        assert tutorial_count == 2

        programming_count = await duckdb_kb.count(filters={"category": "programming"})
        assert programming_count == 2


class TestDuckDBPerformanceIntegration:
    """Test performance characteristics of DuckDB backend."""

    @pytest.fixture
    def duckdb_kb(self):
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(":memory:")
        )
        return KnowledgeBase(document_backend=backend)

    @pytest.mark.asyncio
    async def test_bulk_document_operations(self, duckdb_kb):
        """Test performance with larger document sets."""
        import time

        # Generate test documents
        documents = []
        for i in range(100):
            doc = Document(
                content=f"Document {i} content about programming with keywords like python, javascript, machine learning, data science.",
                metadata=DocumentMetadata(
                    source=f"source_{i % 10}",
                    author=f"author_{i % 5}",
                    type=["tutorial", "course", "reference"][i % 3],
                    category=["programming", "ai", "data_science"][i % 3],
                    tags=[f"tag_{j}" for j in range(i % 5 + 1)],
                    language="en",
                ),
            )
            documents.append(doc)

        # Time bulk save
        start_time = time.time()
        saved_ids = await duckdb_kb.save(*documents)
        save_time = time.time() - start_time

        assert len(saved_ids) == 100
        print(f"Bulk save of 100 documents: {save_time:.3f}s")

        # Time search operations
        start_time = time.time()
        results = await duckdb_kb.search("programming")
        search_time = time.time() - start_time

        print(f"Search across 100 documents: {search_time:.3f}s")
        assert len(results) > 0

        # Time filtered listing
        start_time = time.time()
        tutorials = await duckdb_kb.list_documents(filters={"type": "tutorial"})
        filter_time = time.time() - start_time

        print(f"Filtered listing: {filter_time:.3f}s")
        assert len(tutorials) > 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, duckdb_kb):
        """Test concurrent document operations."""
        # Create documents for concurrent operations
        documents = [
            Document(
                content=f"Concurrent document {i}",
                metadata=DocumentMetadata(source=f"concurrent_{i}"),
            )
            for i in range(10)
        ]

        # Save documents concurrently
        save_tasks = [duckdb_kb.save(doc) for doc in documents]
        results = await asyncio.gather(*save_tasks)

        assert len(results) == 10
        assert all(len(saved_ids) == 1 for saved_ids in results)

        # Retrieve documents concurrently
        doc_ids = [result[0] for result in results]
        get_tasks = [duckdb_kb.get(doc_id) for doc_id in doc_ids]
        retrieved_docs = await asyncio.gather(*get_tasks)

        assert len(retrieved_docs) == 10
        assert all(doc is not None for doc in retrieved_docs)


class TestDuckDBFilePersistence:
    """Test file-based persistence scenarios."""

    @pytest.mark.asyncio
    async def test_persistent_knowledge_base(self):
        """Test KnowledgeBase persistence across sessions."""
        sample_doc = Document(
            content="Persistent knowledge base content",
            metadata=DocumentMetadata(source="persistence_test", type="test"),
        )

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "persistent.duckdb")

        try:
            # Session 1: Create KB and save document
            backend1 = PandasDocumentBackend(
                persistence_strategy=DuckDBPersistence(db_path)
            )
            kb1 = KnowledgeBase(document_backend=backend1)

            saved_ids = await kb1.save(sample_doc)
            doc_id = saved_ids[0]

            # Verify save
            retrieved = await kb1.get(doc_id)
            assert retrieved.content == sample_doc.content

            await backend1.close()

            # Session 2: New KB instance, same database file
            backend2 = PandasDocumentBackend(
                persistence_strategy=DuckDBPersistence(db_path)
            )
            kb2 = KnowledgeBase(document_backend=backend2)

            # Should retrieve the same document
            retrieved = await kb2.get(doc_id)
            assert retrieved is not None
            assert retrieved.content == sample_doc.content
            assert retrieved.metadata.source == sample_doc.metadata.source

            # Should be able to search
            results = await kb2.search("Persistent")
            assert len(results) >= 1
            assert any("Persistent" in result.document.content for result in results)

            await backend2.close()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_database_recovery_after_crash(self):
        """Test that data survives simulated crashes."""
        documents = [
            Document(
                content=f"Recovery test document {i}",
                metadata=DocumentMetadata(source=f"recovery_{i}"),
            )
            for i in range(5)
        ]

        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "recovery.duckdb")

        try:
            # Save documents
            backend = PandasDocumentBackend(
                persistence_strategy=DuckDBPersistence(db_path)
            )
            kb = KnowledgeBase(document_backend=backend)

            saved_ids = await kb.save(*documents)
            assert len(saved_ids) == 5

            # Simulate crash (close without cleanup)
            await backend.close()

            # Recovery: Create new instances
            new_backend = PandasDocumentBackend(
                persistence_strategy=DuckDBPersistence(db_path)
            )
            new_kb = KnowledgeBase(document_backend=new_backend)

            # All documents should still be accessible
            for doc_id in saved_ids:
                retrieved = await new_kb.get(doc_id)
                assert retrieved is not None
                assert "Recovery test document" in retrieved.content

            # Search should work
            results = await new_kb.search("Recovery")
            assert len(results) == 5

            await new_backend.close()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestDuckDBAdvancedQueries:
    """Test advanced querying capabilities."""

    @pytest.fixture
    def duckdb_kb(self):
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(":memory:")
        )
        return KnowledgeBase(document_backend=backend)

    @pytest.fixture
    async def time_series_documents(self, duckdb_kb):
        """Create documents with specific timestamps for time-based queries."""
        documents = [
            Document(
                content=f"Time series document {i}",
                metadata=DocumentMetadata(
                    source="time_series",
                ),
            )
            for i in range(10)
        ]

        await duckdb_kb.save(*documents)
        return duckdb_kb

    @pytest.mark.asyncio
    async def test_complex_metadata_filtering(self, duckdb_kb):
        """Test complex metadata filtering scenarios."""
        # Documents with nested metadata
        complex_docs = [
            Document(
                content="Complex metadata document 1",
                metadata=DocumentMetadata(
                    source="complex_test",
                    author="alice",
                    tags=["important", "production"],
                ),
            ),
            Document(
                content="Complex metadata document 2",
                metadata=DocumentMetadata(
                    source="complex_test",
                    author="bob",
                    tags=["experimental", "testing"],
                ),
            ),
        ]

        await duckdb_kb.save(*complex_docs)

        # Filter by nested metadata (if supported)
        results = await duckdb_kb.list_documents(filters={"author": "alice"})
        assert len(results) == 1
        assert results[0].metadata.author == "alice"

        results = await duckdb_kb.list_documents(filters={"source": "complex_test"})
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, duckdb_kb):
        """Test handling of large result sets."""
        # Create many documents
        large_doc_set = [
            Document(
                content=f"Large dataset document {i} with content about {'python' if i % 2 == 0 else 'javascript'}",
                metadata=DocumentMetadata(
                    source="large_dataset",
                    category=["programming", "web", "data"][i % 3],
                ),
            )
            for i in range(500)
        ]

        # Save in batches to avoid memory issues
        batch_size = 50
        for i in range(0, len(large_doc_set), batch_size):
            batch = large_doc_set[i : i + batch_size]
            await duckdb_kb.save(*batch)

        # Test search across large dataset
        results = await duckdb_kb.search("python")
        python_results = [r for r in results if "python" in r.document.content]
        assert len(python_results) >= 10  # Should find many results

        # Test filtered listing
        programming_docs = await duckdb_kb.list_documents(
            filters={"category": "programming"}
        )
        assert len(programming_docs) > 50  # Should find programming docs

        # Test counting
        total_count = await duckdb_kb.count()
        assert total_count == 500
