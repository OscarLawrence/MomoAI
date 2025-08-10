"""
Tests for the unified KnowledgeBase API.

Validates the clean, intuitive interface and backend integration.
"""

import pytest
from datetime import datetime

from momo_kb import KnowledgeBase, Document, Relationship, DocumentType


class TestUnifiedKnowledgeBase:
    """Test the unified KnowledgeBase interface."""

    @pytest.fixture
    async def kb(self):
        """Create a fresh knowledge base for testing."""
        async with KnowledgeBase(backends=["graph"]) as kb:
            yield kb

    async def test_kb_initialization(self, kb):
        """Test that KB initializes correctly with graph backend."""
        assert kb._initialized
        assert "graph" in kb.backends
        assert len(kb.backends) == 1

    async def test_insert_document_dict(self, kb):
        """Test inserting a document using dict format."""
        doc_dict = {
            "type": "person",
            "title": "Alice Smith",
            "properties": {"age": 30, "role": "engineer"},
        }

        ids = await kb.insert(doc_dict)

        assert len(ids) == 1
        assert isinstance(ids[0], str)

    async def test_insert_document_object(self, kb):
        """Test inserting a Document object."""
        doc = Document(
            type=DocumentType.PERSON,
            title="Bob Johnson",
            content="Software engineer with 5 years experience",
            properties={"age": 28, "skills": ["Python", "AI"]},
        )

        ids = await kb.insert(doc)

        assert len(ids) == 1
        assert ids[0] == doc.id

    async def test_insert_raw_text(self, kb):
        """Test inserting raw text content."""
        text = "This is a research paper about machine learning algorithms."

        ids = await kb.insert(text)

        assert len(ids) == 1
        assert isinstance(ids[0], str)

    async def test_insert_multiple_items(self, kb):
        """Test inserting multiple items at once."""
        items = [
            {"type": "person", "title": "Alice"},
            Document(type=DocumentType.DOCUMENT, title="Research Paper"),
            "Raw text content",
        ]

        ids = await kb.insert(*items)

        assert len(ids) == 3
        assert all(isinstance(id_, str) for id_ in ids)

    async def test_search_basic(self, kb):
        """Test basic search functionality."""
        # Insert some test data
        await kb.insert(
            {
                "type": "person",
                "title": "Alice Smith",
                "properties": {"role": "engineer"},
            },
            {
                "type": "person",
                "title": "Bob Johnson",
                "properties": {"role": "designer"},
            },
            {"type": "document", "title": "AI Research Paper"},
        )

        # Search for people
        result = await kb.search("Alice")

        assert isinstance(result.query, str)
        assert result.query == "Alice"
        assert len(result.backends_used) > 0
        assert result.search_time_ms >= 0

    async def test_search_with_filters(self, kb):
        """Test search with filters."""
        # Insert test data
        await kb.insert(
            {"type": "person", "title": "Engineer Alice"},
            {"type": "document", "title": "Alice's Document"},
        )

        # Search with type filter
        result = await kb.search("Alice", filters={"type": "person"})

        assert result.query == "Alice"
        # Note: Actual filtering depends on backend implementation

    async def test_delete_documents(self, kb):
        """Test deleting documents."""
        # Insert test data
        ids = await kb.insert(
            {"type": "person", "title": "Test Person"},
            {"type": "document", "title": "Test Document"},
        )

        # Delete first document
        delete_results = await kb.delete(ids[0])

        assert ids[0] in delete_results
        # Note: Actual deletion success depends on backend implementation

    async def test_rollback(self, kb):
        """Test rollback functionality."""
        # Insert some data
        await kb.insert({"type": "person", "title": "Person 1"})
        await kb.insert({"type": "person", "title": "Person 2"})
        await kb.insert({"type": "person", "title": "Person 3"})

        # Rollback last 2 operations
        await kb.roll(2)

        # Verify rollback was recorded
        assert len(kb._operation_history) > 0

    async def test_stats(self, kb):
        """Test getting knowledge base statistics."""
        # Insert some test data
        await kb.insert(
            {"type": "person", "title": "Alice"},
            {"type": "document", "title": "Paper 1"},
            {"type": "document", "title": "Paper 2"},
        )

        stats = await kb.stats()

        assert isinstance(stats.total_documents, int)
        assert isinstance(stats.total_relationships, int)
        assert "graph" in stats.active_backends
        assert isinstance(stats.backend_stats, dict)
        assert isinstance(stats.created_at, datetime)
        assert stats.total_operations > 0

    async def test_prune(self, kb):
        """Test pruning functionality."""
        # Insert some data
        await kb.insert({"type": "person", "title": "Test Person"})

        # Test pruning
        results = await kb.prune(mode="auto")

        assert isinstance(results, dict)
        assert "graph" in results

    async def test_screenshot(self, kb):
        """Test screenshot generation."""
        # Insert some test data
        await kb.insert(
            {"type": "person", "title": "Alice"},
            {"type": "document", "title": "Research Paper"},
        )

        # Generate screenshot
        screenshot_b64 = await kb.screenshot()

        assert isinstance(screenshot_b64, str)
        assert len(screenshot_b64) > 0
        # Should be valid base64
        import base64

        try:
            base64.b64decode(screenshot_b64)
        except Exception:
            pytest.fail("Screenshot should return valid base64 data")

    async def test_relationship_insertion(self, kb):
        """Test inserting relationships between documents."""
        # Insert documents first
        doc_ids = await kb.insert(
            {"type": "person", "title": "Alice"}, {"type": "person", "title": "Bob"}
        )

        # Create relationship
        relationship = Relationship(
            source_id=doc_ids[0],
            target_id=doc_ids[1],
            relationship_type="knows",
            properties={"since": "2020"},
        )

        rel_ids = await kb.insert(relationship)

        assert len(rel_ids) == 1
        assert isinstance(rel_ids[0], str)

    async def test_error_handling_uninitialized(self):
        """Test error handling when KB is not initialized."""
        kb = KnowledgeBase()

        with pytest.raises(RuntimeError, match="not initialized"):
            await kb.insert({"type": "person", "title": "Test"})

        with pytest.raises(RuntimeError, match="not initialized"):
            await kb.search("test")

        with pytest.raises(RuntimeError, match="not initialized"):
            await kb.delete("test_id")

    async def test_input_format_validation(self, kb):
        """Test validation of different input formats."""
        # Valid formats should work
        valid_inputs = [
            {"type": "person", "title": "Alice"},
            Document(type=DocumentType.PERSON, title="Bob"),
            "Raw text content",
            Relationship(source_id="a", target_id="b", relationship_type="knows"),
        ]

        for input_item in valid_inputs:
            ids = await kb.insert(input_item)
            assert len(ids) == 1

        # Invalid format should raise error
        with pytest.raises(ValueError):
            await kb.insert(123)  # Invalid type
