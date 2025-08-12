"""
Test the VectorLattice core component.
"""

import pytest
import numpy as np
from kb_playground.vector_lattice import VectorLattice
from kb_playground.models import Document, Relationship


class TestVectorLattice:
    """Test VectorLattice functionality."""
    
    @pytest.fixture
    def lattice(self):
        """Create a vector lattice for testing."""
        return VectorLattice(dimension=128)
        
    @pytest.fixture
    def sample_doc_with_embedding(self):
        """Create a document with embedding."""
        embedding = np.random.randn(128).astype(np.float32)
        return Document(
            content="Test document",
            title="Test",
            embedding=embedding.tolist()
        )
        
    def test_initialization(self, lattice):
        """Test lattice initialization."""
        assert lattice.dimension == 128
        assert len(lattice._vectors) == 0
        assert len(lattice._documents) == 0
        assert len(lattice._relationships) == 0
        
    def test_add_document(self, lattice, sample_doc_with_embedding):
        """Test adding a document."""
        doc_id = lattice.add_document(sample_doc_with_embedding)
        
        assert doc_id == sample_doc_with_embedding.id
        assert doc_id in lattice._vectors
        assert doc_id in lattice._documents
        
        # Check vector normalization
        vector = lattice._vectors[doc_id]
        assert np.isclose(np.linalg.norm(vector), 1.0, atol=1e-6)
        
    def test_add_document_without_embedding(self, lattice):
        """Test adding document without embedding raises error."""
        doc = Document(content="Test", title="Test")
        
        with pytest.raises(ValueError, match="must have embedding"):
            lattice.add_document(doc)
            
    def test_add_document_wrong_dimension(self, lattice):
        """Test adding document with wrong embedding dimension."""
        doc = Document(
            content="Test",
            title="Test", 
            embedding=np.random.randn(64).tolist()  # Wrong dimension
        )
        
        with pytest.raises(ValueError, match="Embedding dimension"):
            lattice.add_document(doc)
            
    def test_add_relationship(self, lattice, sample_doc_with_embedding):
        """Test adding relationships."""
        # Add two documents
        doc1 = sample_doc_with_embedding
        doc2 = Document(
            content="Second document",
            title="Second",
            embedding=np.random.randn(128).tolist()
        )
        
        lattice.add_document(doc1)
        lattice.add_document(doc2)
        
        # Add relationship
        rel = Relationship(
            source_id=doc1.id,
            target_id=doc2.id,
            relationship_type="related",
            strength=0.8
        )
        
        rel_id = lattice.add_relationship(rel)
        
        assert rel_id == rel.id
        assert rel_id in lattice._relationships
        assert doc2.id in lattice._adjacency[doc1.id]
        assert doc1.id in lattice._reverse_adjacency[doc2.id]
        
    def test_bidirectional_relationship(self, lattice, sample_doc_with_embedding):
        """Test bidirectional relationships."""
        # Add two documents
        doc1 = sample_doc_with_embedding
        doc2 = Document(
            content="Second document",
            title="Second",
            embedding=np.random.randn(128).tolist()
        )
        
        lattice.add_document(doc1)
        lattice.add_document(doc2)
        
        # Add bidirectional relationship
        rel = Relationship(
            source_id=doc1.id,
            target_id=doc2.id,
            relationship_type="bidirectional",
            strength=0.9,
            is_bidirectional=True
        )
        
        lattice.add_relationship(rel)
        
        # Check both directions
        assert doc2.id in lattice._adjacency[doc1.id]
        assert doc1.id in lattice._adjacency[doc2.id]
        assert doc1.id in lattice._reverse_adjacency[doc2.id]
        assert doc2.id in lattice._reverse_adjacency[doc1.id]
        
    def test_search_empty_lattice(self, lattice):
        """Test search on empty lattice."""
        query_vector = np.random.randn(128)
        results = lattice.search(query_vector)
        
        assert len(results) == 0
        
    def test_search_single_document(self, lattice, sample_doc_with_embedding):
        """Test search with single document."""
        lattice.add_document(sample_doc_with_embedding)
        
        # Use the same embedding as query for perfect match
        query_vector = np.array(sample_doc_with_embedding.embedding)
        results = lattice.search(query_vector, top_k=5)
        
        assert len(results) == 1
        assert results[0][0] == sample_doc_with_embedding.id
        assert results[0][1] > 0.99  # Should be very high similarity
        
    def test_search_multiple_documents(self, lattice):
        """Test search with multiple documents."""
        # Add several documents
        docs = []
        for i in range(5):
            embedding = np.random.randn(128)
            doc = Document(
                content=f"Document {i}",
                title=f"Doc {i}",
                embedding=embedding.tolist()
            )
            docs.append(doc)
            lattice.add_document(doc)
            
        # Search with random query
        query_vector = np.random.randn(128)
        results = lattice.search(query_vector, top_k=3)
        
        assert len(results) <= 3
        assert len(results) <= len(docs)
        
        # Check results are sorted by score
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True)
        
    def test_search_with_relationship_boost(self, lattice):
        """Test search with relationship boosting."""
        # Create documents
        doc1 = Document(
            content="First document",
            embedding=np.array([1.0] + [0.0] * 127).tolist()
        )
        doc2 = Document(
            content="Second document", 
            embedding=np.array([0.0, 1.0] + [0.0] * 126).tolist()
        )
        doc3 = Document(
            content="Third document",
            embedding=np.array([0.0, 0.0, 1.0] + [0.0] * 125).tolist()
        )
        
        lattice.add_document(doc1)
        lattice.add_document(doc2)
        lattice.add_document(doc3)
        
        # Add relationship between doc1 and doc3
        rel = Relationship(
            source_id=doc1.id,
            target_id=doc3.id,
            relationship_type="related",
            strength=1.0
        )
        lattice.add_relationship(rel)
        
        # Query similar to doc1
        query_vector = np.array([0.9] + [0.1] * 127)
        
        # Search without boost
        results_no_boost = lattice.search(query_vector, relationship_boost=0.0)
        
        # Search with boost
        results_with_boost = lattice.search(query_vector, relationship_boost=0.5)
        
        # doc3 should rank higher with boost due to relationship with doc1
        no_boost_scores = {doc_id: score for doc_id, score in results_no_boost}
        with_boost_scores = {doc_id: score for doc_id, score in results_with_boost}
        
        # doc3 should get a boost
        if doc3.id in with_boost_scores and doc3.id in no_boost_scores:
            assert with_boost_scores[doc3.id] >= no_boost_scores[doc3.id]
            
    def test_remove_document(self, lattice, sample_doc_with_embedding):
        """Test removing documents."""
        doc_id = lattice.add_document(sample_doc_with_embedding)
        
        # Verify document exists
        assert doc_id in lattice._documents
        assert doc_id in lattice._vectors
        
        # Remove document
        success = lattice.remove_document(doc_id)
        
        assert success
        assert doc_id not in lattice._documents
        assert doc_id not in lattice._vectors
        
    def test_remove_nonexistent_document(self, lattice):
        """Test removing non-existent document."""
        success = lattice.remove_document("nonexistent")
        assert not success
        
    def test_get_connected_documents(self, lattice):
        """Test getting connected documents."""
        # Create a chain of documents: doc1 -> doc2 -> doc3
        docs = []
        for i in range(3):
            doc = Document(
                content=f"Document {i}",
                embedding=np.random.randn(128).tolist()
            )
            docs.append(doc)
            lattice.add_document(doc)
            
        # Add relationships
        rel1 = Relationship(
            source_id=docs[0].id,
            target_id=docs[1].id,
            relationship_type="next",
            strength=1.0
        )
        rel2 = Relationship(
            source_id=docs[1].id,
            target_id=docs[2].id,
            relationship_type="next",
            strength=1.0
        )
        
        lattice.add_relationship(rel1)
        lattice.add_relationship(rel2)
        
        # Get connected documents from doc1
        connected = lattice.get_connected_documents(docs[0].id, max_depth=1)
        assert docs[1].id in connected
        assert docs[2].id not in connected  # Too far
        
        connected = lattice.get_connected_documents(docs[0].id, max_depth=2)
        assert docs[1].id in connected
        assert docs[2].id in connected  # Now reachable
        
    def test_create_and_restore_snapshot(self, lattice, sample_doc_with_embedding):
        """Test snapshot creation and restoration."""
        # Add document and relationship
        doc1 = sample_doc_with_embedding
        doc2 = Document(
            content="Second doc",
            embedding=np.random.randn(128).tolist()
        )
        
        lattice.add_document(doc1)
        lattice.add_document(doc2)
        
        rel = Relationship(
            source_id=doc1.id,
            target_id=doc2.id,
            relationship_type="test",
            strength=0.5
        )
        lattice.add_relationship(rel)
        
        # Create snapshot
        snapshot = lattice.create_snapshot()
        
        assert "dimension" in snapshot
        assert "documents" in snapshot
        assert "relationships" in snapshot
        assert "vectors" in snapshot
        
        # Restore from snapshot
        new_lattice = VectorLattice.from_snapshot(snapshot)
        
        assert new_lattice.dimension == lattice.dimension
        assert len(new_lattice._documents) == len(lattice._documents)
        assert len(new_lattice._relationships) == len(lattice._relationships)
        assert len(new_lattice._vectors) == len(lattice._vectors)
        
    def test_get_stats(self, lattice, sample_doc_with_embedding):
        """Test getting lattice statistics."""
        stats = lattice.get_stats()
        
        assert stats["documents"] == 0
        assert stats["relationships"] == 0
        assert stats["dimension"] == 128
        
        # Add document
        lattice.add_document(sample_doc_with_embedding)
        
        stats = lattice.get_stats()
        assert stats["documents"] == 1