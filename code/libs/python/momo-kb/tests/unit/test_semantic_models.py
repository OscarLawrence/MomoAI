"""
Test-driven development for semantic retrieval models.

Tests the extended data models and interfaces needed for semantic search
before implementing the actual functionality.
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

# These imports will fail initially - that's expected for TDD
try:
    from momo_kb.models import Node, Edge, SemanticQueryResult
    from momo_kb.semantic import EmbeddingManager, VectorIndex, SemanticSearch
except ImportError:
    # Expected during TDD - we'll implement these
    pass


class TestSemanticDataModels:
    """Test enhanced data models with embedding support."""
    
    def test_node_with_embedding(self):
        """Test that nodes can store embeddings."""
        from momo_kb.models import Node
        
        # Create node with embedding
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        node = Node(
            label="Document",
            properties={"title": "AI Research Paper", "content": "Machine learning..."},
            embedding=embedding,
            embedding_model="text-embedding-ada-002"
        )
        
        assert node.embedding == embedding
        assert node.embedding_model == "text-embedding-ada-002"
        assert isinstance(node.embedding_timestamp, datetime)
        
    def test_node_embedding_immutability(self):
        """Test that embedding updates create new node instances."""
        from momo_kb.models import Node
        
        original_node = Node(
            label="Document",
            properties={"title": "Test Doc"}
        )
        
        # Add embedding
        embedding = [0.1, 0.2, 0.3]
        updated_node = original_node.with_embedding(embedding, "test-model")
        
        # Original unchanged
        assert original_node.embedding is None
        assert original_node.embedding_model is None
        
        # New node has embedding
        assert updated_node.embedding == embedding
        assert updated_node.embedding_model == "test-model"
        assert updated_node.id == original_node.id  # Same identity
        
    def test_semantic_query_result(self):
        """Test semantic query result model."""
        from momo_kb.models import Node, SemanticQueryResult
        
        nodes = [
            Node(label="Doc1", properties={"title": "AI Paper"}),
            Node(label="Doc2", properties={"title": "ML Research"})
        ]
        
        scores = [0.95, 0.87]
        
        result = SemanticQueryResult(
            nodes=nodes,
            similarity_scores=scores,
            query_embedding=[0.1, 0.2, 0.3],
            threshold=0.8,
            query_time_ms=15.5
        )
        
        assert len(result.nodes) == 2
        assert len(result.similarity_scores) == 2
        assert result.similarity_scores[0] == 0.95
        assert result.threshold == 0.8
        assert result.query_time_ms == 15.5
        
    def test_hybrid_query_result(self):
        """Test hybrid query result combining semantic and structural."""
        from momo_kb.models import Node, HybridQueryResult
        
        nodes = [Node(label="Person", properties={"name": "Alice"})]
        
        result = HybridQueryResult(
            nodes=nodes,
            semantic_scores=[0.92],
            structural_matches=[True],
            combined_scores=[0.88],
            alpha=0.5,  # Balance between semantic and structural
            query_time_ms=25.3
        )
        
        assert len(result.nodes) == 1
        assert result.semantic_scores[0] == 0.92
        assert result.structural_matches[0] is True
        assert result.combined_scores[0] == 0.88
        assert result.alpha == 0.5


class TestEmbeddingManager:
    """Test embedding generation and management."""
    
    @pytest.fixture
    def embedding_manager(self):
        """Create embedding manager for testing."""
        from momo_kb.semantic import EmbeddingManager
        return EmbeddingManager()
        
    async def test_generate_embedding(self, embedding_manager):
        """Test embedding generation for text."""
        text = "This is a test document about machine learning"
        
        embedding = await embedding_manager.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)
        
    async def test_embed_node_content(self, embedding_manager):
        """Test generating embeddings for node content."""
        from momo_kb.models import Node
        
        node = Node(
            label="Document",
            properties={
                "title": "AI Research",
                "content": "Machine learning algorithms...",
                "tags": ["AI", "ML", "research"]
            }
        )
        
        embedded_node = await embedding_manager.embed_node_content(node)
        
        assert embedded_node.embedding is not None
        assert len(embedded_node.embedding) > 0
        assert embedded_node.embedding_model is not None
        assert embedded_node.id == node.id  # Same identity
        
    async def test_multiple_embedding_models(self, embedding_manager):
        """Test support for multiple embedding models."""
        text = "Test content"
        
        # Test different models
        openai_embedding = await embedding_manager.generate_embedding(
            text, model="openai-ada-002"
        )
        sentence_embedding = await embedding_manager.generate_embedding(
            text, model="sentence-transformers"
        )
        
        assert isinstance(openai_embedding, list)
        assert isinstance(sentence_embedding, list)
        # Different models should produce different embeddings
        assert openai_embedding != sentence_embedding
        
    def test_extract_embeddable_content(self, embedding_manager):
        """Test content extraction from nodes for embedding."""
        from momo_kb.models import Node
        
        node = Node(
            label="Person",
            properties={
                "name": "Alice Smith",
                "bio": "Software engineer with expertise in AI",
                "age": 30,  # Non-string property
                "skills": ["Python", "Machine Learning"]  # List property
            }
        )
        
        content = embedding_manager._extract_embeddable_content(node)
        
        assert "Person" in content
        assert "Alice Smith" in content
        assert "Software engineer" in content
        # Should handle non-string properties gracefully
        assert isinstance(content, str)


class TestVectorIndex:
    """Test vector indexing and similarity search."""
    
    @pytest.fixture
    def vector_index(self):
        """Create vector index for testing."""
        from momo_kb.semantic import VectorIndex
        return VectorIndex(dimension=384)  # Smaller dimension for testing
        
    def test_add_vectors(self, vector_index):
        """Test adding vectors to index."""
        node_ids = ["node1", "node2", "node3"]
        embeddings = [
            [0.1, 0.2, 0.3] + [0.0] * 381,  # Pad to 384 dimensions
            [0.4, 0.5, 0.6] + [0.0] * 381,
            [0.7, 0.8, 0.9] + [0.0] * 381
        ]
        
        vector_index.add_vectors(node_ids, embeddings)
        
        assert vector_index.size() == 3
        assert "node1" in vector_index.get_node_ids()
        assert "node2" in vector_index.get_node_ids()
        assert "node3" in vector_index.get_node_ids()
        
    def test_similarity_search(self, vector_index):
        """Test similarity search functionality."""
        # Add some vectors
        node_ids = ["doc1", "doc2", "doc3"]
        embeddings = [
            [1.0, 0.0, 0.0] + [0.0] * 381,  # Similar to query
            [0.0, 1.0, 0.0] + [0.0] * 381,  # Different from query
            [0.9, 0.1, 0.0] + [0.0] * 381   # Somewhat similar to query
        ]
        
        vector_index.add_vectors(node_ids, embeddings)
        
        # Search with query similar to first vector
        query_embedding = [0.95, 0.05, 0.0] + [0.0] * 381
        results = vector_index.similarity_search(query_embedding, k=2)
        
        assert len(results) == 2
        # Results should be sorted by similarity (highest first)
        assert results[0][0] == "doc1"  # Most similar
        assert results[0][1] > results[1][1]  # Higher score than second result
        
    def test_cosine_similarity_calculation(self, vector_index):
        """Test cosine similarity calculation."""
        # Test with known vectors
        vec1 = [1.0, 0.0, 0.0] + [0.0] * 381
        vec2 = [1.0, 0.0, 0.0] + [0.0] * 381  # Identical
        vec3 = [0.0, 1.0, 0.0] + [0.0] * 381  # Orthogonal
        
        vector_index.add_vectors(["identical", "orthogonal"], [vec2, vec3])
        
        results = vector_index.similarity_search(vec1, k=2)
        
        # Identical vector should have similarity ~1.0
        assert abs(results[0][1] - 1.0) < 0.01
        # Orthogonal vector should have similarity ~0.0
        assert abs(results[1][1] - 0.0) < 0.01
        
    def test_remove_vectors(self, vector_index):
        """Test removing vectors from index."""
        node_ids = ["temp1", "temp2"]
        embeddings = [
            [0.1, 0.2] + [0.0] * 382,
            [0.3, 0.4] + [0.0] * 382
        ]
        
        vector_index.add_vectors(node_ids, embeddings)
        assert vector_index.size() == 2
        
        vector_index.remove_vector("temp1")
        assert vector_index.size() == 1
        assert "temp1" not in vector_index.get_node_ids()
        assert "temp2" in vector_index.get_node_ids()


class TestSemanticSearch:
    """Test high-level semantic search functionality."""
    
    @pytest.fixture
    async def semantic_search(self):
        """Create semantic search instance for testing."""
        from momo_kb.semantic import SemanticSearch
        from momo_kb import KnowledgeBase
        
        kb = KnowledgeBase()
        await kb.initialize()
        
        semantic_search = SemanticSearch(kb)
        yield semantic_search
        
        await kb.close()
        
    async def test_semantic_node_search(self, semantic_search):
        """Test semantic search for nodes."""
        # This test defines the interface we want
        query = "machine learning research"
        
        result = await semantic_search.search_nodes(
            query=query,
            top_k=5,
            threshold=0.7
        )
        
        assert hasattr(result, 'nodes')
        assert hasattr(result, 'similarity_scores')
        assert hasattr(result, 'query_time_ms')
        assert len(result.nodes) <= 5
        assert all(score >= 0.7 for score in result.similarity_scores)
        
    async def test_hybrid_search(self, semantic_search):
        """Test hybrid semantic + structural search."""
        result = await semantic_search.hybrid_search(
            semantic_query="artificial intelligence",
            structural_filters={"label": "Document"},
            alpha=0.6  # 60% semantic, 40% structural
        )
        
        assert hasattr(result, 'nodes')
        assert hasattr(result, 'combined_scores')
        assert hasattr(result, 'alpha')
        assert result.alpha == 0.6
        
    async def test_find_similar_nodes(self, semantic_search):
        """Test finding nodes similar to a given node."""
        from momo_kb.models import Node
        
        reference_node = Node(
            label="Document",
            properties={"title": "Deep Learning Fundamentals"}
        )
        
        result = await semantic_search.find_similar_nodes(
            reference_node=reference_node,
            top_k=3,
            exclude_self=True
        )
        
        assert len(result.nodes) <= 3
        # Should not include the reference node itself
        assert reference_node.id not in [node.id for node in result.nodes]
        
    async def test_semantic_recommendations(self, semantic_search):
        """Test semantic recommendations based on user interests."""
        user_interests = [
            "machine learning",
            "natural language processing", 
            "computer vision"
        ]
        
        result = await semantic_search.get_recommendations(
            interests=user_interests,
            top_k=10,
            diversity_threshold=0.8  # Ensure diverse recommendations
        )
        
        assert len(result.nodes) <= 10
        assert hasattr(result, 'diversity_scores')
        
    async def test_contextual_search(self, semantic_search):
        """Test contextual search using conversation history."""
        conversation_context = [
            "User asked about deployment strategies",
            "Mentioned Kubernetes and Docker",
            "Interested in scalability"
        ]
        
        result = await semantic_search.contextual_search(
            context=conversation_context,
            max_results=15
        )
        
        assert len(result.nodes) <= 15
        assert hasattr(result, 'context_relevance_scores')


class TestSemanticIntegration:
    """Test integration with existing KnowledgeBase functionality."""
    
    @pytest.fixture
    async def kb_with_semantic(self):
        """Create KB with semantic capabilities enabled."""
        from momo_kb import KnowledgeBase
        
        kb = KnowledgeBase(enable_semantic=True)
        await kb.initialize()
        yield kb
        await kb.close()
        
    async def test_automatic_embedding_generation(self, kb_with_semantic):
        """Test that embeddings are automatically generated for new nodes."""
        from momo_kb.models import Node
        
        node = Node(
            label="Article",
            properties={"title": "AI Ethics", "content": "Discussion of AI ethics..."}
        )
        
        diff = await kb_with_semantic.insert_node(node)
        
        # Node should automatically get an embedding
        stored_node = diff.node
        assert stored_node.embedding is not None
        assert stored_node.embedding_model is not None
        
    async def test_semantic_rollback(self, kb_with_semantic):
        """Test that rollback works with embeddings."""
        from momo_kb.models import Node
        
        # Add node with embedding
        node = Node(label="Test", properties={"content": "test content"})
        await kb_with_semantic.insert_node(node)
        
        # Verify embedding exists
        result = await kb_with_semantic.query_nodes(label="Test")
        assert len(result.nodes) == 1
        assert result.nodes[0].embedding is not None
        
        # Rollback
        await kb_with_semantic.rollback(steps=1)
        
        # Node and embedding should be gone
        result = await kb_with_semantic.query_nodes(label="Test")
        assert len(result.nodes) == 0
        
    async def test_performance_with_embeddings(self, kb_with_semantic):
        """Test that existing exact queries maintain performance."""
        from momo_kb.models import Node
        import time
        
        # Add nodes with embeddings
        for i in range(100):
            node = Node(
                label="TestNode",
                properties={"index": i, "category": f"cat_{i % 10}"}
            )
            await kb_with_semantic.insert_node(node)
        
        # Test exact query performance (should be unaffected)
        start = time.perf_counter()
        result = await kb_with_semantic.query_nodes(properties={"category": "cat_5"})
        query_time = (time.perf_counter() - start) * 1000
        
        assert len(result.nodes) == 10
        assert query_time < 10  # Should still be very fast
        
    async def test_backward_compatibility(self, kb_with_semantic):
        """Test that all existing functionality works unchanged."""
        from momo_kb.models import Node, Edge
        
        # All existing operations should work exactly the same
        alice = await kb_with_semantic.insert_node(Node(
            label="Person", properties={"name": "Alice"}
        ))
        bob = await kb_with_semantic.insert_node(Node(
            label="Person", properties={"name": "Bob"}
        ))
        
        edge = await kb_with_semantic.insert_edge(Edge(
            source_id=alice.node.id,
            target_id=bob.node.id,
            relationship="knows"
        ))
        
        # Existing queries work unchanged
        people = await kb_with_semantic.query_nodes(label="Person")
        assert len(people.nodes) == 2
        
        relationships = await kb_with_semantic.query_edges(relationship="knows")
        assert len(relationships.edges) == 1
        
        # Graph traversal works unchanged
        friends = await kb_with_semantic.query_connected_nodes(
            start_node_id=alice.node.id,
            relationship="knows",
            direction="outgoing"
        )
        assert len(friends.nodes) == 1
        assert friends.nodes[0].id == bob.node.id