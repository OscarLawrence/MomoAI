"""
Test the main KnowledgeBase interface.
"""

import pytest
from kb_playground import KnowledgeBase, Document


class TestKnowledgeBaseBasics:
    """Test basic KB operations."""
    
    def test_initialization(self, temp_dir):
        """Test KB initialization."""
        kb = KnowledgeBase(
            dimension=128,
            data_dir=str(temp_dir / "test_kb"),
            enable_dvc=False
        )
        
        assert kb.dimension == 128
        assert not kb._is_fitted
        assert len(kb._operations) == 0
        assert kb._current_version == 0
        
    def test_add_single_document(self, kb):
        """Test adding a single document."""
        doc = Document(
            content="Test document content",
            title="Test Document"
        )
        
        ids = kb.add(doc)
        
        assert len(ids) == 1
        assert ids[0] == doc.id
        assert kb._is_fitted  # Should auto-fit
        assert len(kb._operations) == 1
        assert kb._current_version == 1
        
    def test_add_multiple_documents(self, kb, sample_documents):
        """Test adding multiple documents."""
        ids = kb.add(*sample_documents)
        
        assert len(ids) == len(sample_documents)
        assert all(doc_id for doc_id in ids)
        assert kb._is_fitted
        assert len(kb._operations) == 1
        
    def test_add_string_content(self, kb):
        """Test adding documents as strings."""
        content = "This is a test document as a string."
        
        ids = kb.add(content)
        
        assert len(ids) == 1
        retrieved = kb.get(ids[0])
        assert retrieved[0].content == content
        
    def test_add_dict_content(self, kb):
        """Test adding documents as dictionaries."""
        doc_dict = {
            "content": "Dictionary document content",
            "title": "Dict Document",
            "metadata": {"source": "test"}
        }
        
        ids = kb.add(doc_dict)
        
        assert len(ids) == 1
        retrieved = kb.get(ids[0])
        assert retrieved[0].content == doc_dict["content"]
        assert retrieved[0].title == doc_dict["title"]
        assert retrieved[0].metadata["source"] == "test"


class TestKnowledgeBaseRetrieval:
    """Test KB retrieval operations."""
    
    def test_get_existing_documents(self, populated_kb, sample_documents):
        """Test retrieving existing documents."""
        # Get first document
        doc_id = sample_documents[0].id
        retrieved = populated_kb.get(doc_id)
        
        assert len(retrieved) == 1
        assert retrieved[0] is not None
        assert retrieved[0].id == doc_id
        assert retrieved[0].content == sample_documents[0].content
        
    def test_get_multiple_documents(self, populated_kb, sample_documents):
        """Test retrieving multiple documents."""
        doc_ids = [doc.id for doc in sample_documents[:3]]
        retrieved = populated_kb.get(*doc_ids)
        
        assert len(retrieved) == 3
        assert all(doc is not None for doc in retrieved)
        assert [doc.id for doc in retrieved] == doc_ids
        
    def test_get_nonexistent_document(self, populated_kb):
        """Test retrieving non-existent document."""
        retrieved = populated_kb.get("nonexistent-id")
        
        assert len(retrieved) == 1
        assert retrieved[0] is None
        
    def test_search_basic(self, populated_kb):
        """Test basic search functionality."""
        result = populated_kb.search("programming language", top_k=3)
        
        assert len(result.documents) <= 3
        assert result.query == "programming language"
        assert result.total_results == len(result.documents)
        assert result.search_time_ms > 0
        assert len(result.scores) == len(result.documents)
        
    def test_search_with_caller_id(self, populated_kb):
        """Test search with caller ID."""
        result = populated_kb.search(
            "machine learning", 
            caller_id="test_agent",
            top_k=2
        )
        
        assert result.caller_enrichment["caller_id"] == "test_agent"
        assert len(result.documents) <= 2
        
    def test_search_empty_kb(self, kb):
        """Test search on empty KB."""
        result = kb.search("test query")
        
        assert len(result.documents) == 0
        assert result.total_results == 0


class TestKnowledgeBaseDeletion:
    """Test KB deletion operations."""
    
    def test_delete_existing_document(self, populated_kb, sample_documents):
        """Test deleting an existing document."""
        doc_id = sample_documents[0].id
        
        # Verify document exists
        retrieved = populated_kb.get(doc_id)
        assert retrieved[0] is not None
        
        # Delete document
        results = populated_kb.delete(doc_id)
        
        assert results[doc_id] is True
        
        # Verify document is gone
        retrieved = populated_kb.get(doc_id)
        assert retrieved[0] is None
        
    def test_delete_multiple_documents(self, populated_kb, sample_documents):
        """Test deleting multiple documents."""
        doc_ids = [doc.id for doc in sample_documents[:2]]
        
        results = populated_kb.delete(*doc_ids)
        
        assert all(results[doc_id] for doc_id in doc_ids)
        
        # Verify documents are gone
        retrieved = populated_kb.get(*doc_ids)
        assert all(doc is None for doc in retrieved)
        
    def test_delete_nonexistent_document(self, populated_kb):
        """Test deleting non-existent document."""
        results = populated_kb.delete("nonexistent-id")
        
        assert results["nonexistent-id"] is False


class TestKnowledgeBaseRollback:
    """Test KB rollback functionality."""
    
    def test_roll_back_one_operation(self, kb, sample_documents):
        """Test rolling back one operation."""
        # Add documents
        initial_ids = kb.add(sample_documents[0])
        assert len(kb.get(initial_ids[0])) == 1
        assert kb._current_version == 1
        
        # Add more documents
        second_ids = kb.add(sample_documents[1])
        assert len(kb.get(second_ids[0])) == 1
        assert kb._current_version == 2
        
        # Roll back one operation
        success = kb.roll(1)
        assert success
        assert kb._current_version == 1
        
        # Second document should be gone
        retrieved = kb.get(second_ids[0])
        assert retrieved[0] is None
        
        # First document should still exist
        retrieved = kb.get(initial_ids[0])
        assert retrieved[0] is not None
        
    def test_roll_back_multiple_operations(self, kb, sample_documents):
        """Test rolling back multiple operations."""
        # Perform several operations
        kb.add(sample_documents[0])  # Version 1
        kb.add(sample_documents[1])  # Version 2
        kb.add(sample_documents[2])  # Version 3
        
        assert kb._current_version == 3
        
        # Roll back to beginning
        success = kb.roll(3)
        assert success
        assert kb._current_version == 0
        
        # All documents should be gone
        for doc in sample_documents[:3]:
            retrieved = kb.get(doc.id)
            assert retrieved[0] is None
            
    def test_roll_invalid_steps(self, populated_kb):
        """Test rolling back invalid number of steps."""
        current_version = populated_kb._current_version
        
        # Try to roll back more than available
        success = populated_kb.roll(current_version + 5)
        assert not success
        assert populated_kb._current_version == current_version
        
        # Try to roll back negative steps (not implemented)
        success = populated_kb.roll(-1)
        assert not success


class TestKnowledgeBaseConfiguration:
    """Test KB configuration and enrichment."""
    
    def test_configure_global_enrichment(self, kb):
        """Test configuring global enrichment."""
        kb.configure_enrichment(
            expansion_factor=2.0,
            relationship_depth=3,
            semantic_threshold=0.8
        )
        
        config = kb._get_enrichment_config(None, None)
        assert config.expansion_factor == 2.0
        assert config.relationship_depth == 3
        assert config.semantic_threshold == 0.8
        
    def test_configure_caller_enrichment(self, kb):
        """Test configuring caller-specific enrichment."""
        kb.configure_enrichment(
            caller_id="test_agent",
            expansion_factor=1.5,
            relationship_depth=2
        )
        
        config = kb._get_enrichment_config("test_agent", None)
        assert config.expansion_factor == 1.5
        assert config.relationship_depth == 2
        
    def test_configure_collection_enrichment(self, kb):
        """Test configuring collection-specific enrichment."""
        kb.configure_enrichment(
            collection="test_collection",
            semantic_threshold=0.9,
            include_metadata_fields=["category"]
        )
        
        config = kb._get_enrichment_config(None, "test_collection")
        assert config.semantic_threshold == 0.9
        assert "category" in config.include_metadata_fields


class TestKnowledgeBaseStats:
    """Test KB statistics and analytics."""
    
    def test_get_stats_empty_kb(self, kb):
        """Test getting stats from empty KB."""
        stats = kb.get_stats()
        
        assert stats["documents"] == 0
        assert stats["relationships"] == 0
        assert stats["operations"] == 0
        assert stats["current_version"] == 0
        assert not stats["is_fitted"]
        
    def test_get_stats_populated_kb(self, populated_kb):
        """Test getting stats from populated KB."""
        stats = populated_kb.get_stats()
        
        assert stats["documents"] > 0
        assert stats["operations"] > 0
        assert stats["current_version"] > 0
        assert stats["is_fitted"]
        assert "embedding_stats" in stats
        assert "relationship_analytics" in stats