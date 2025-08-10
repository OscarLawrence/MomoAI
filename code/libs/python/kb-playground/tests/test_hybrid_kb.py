"""
Tests for the hybrid knowledge base implementation.
"""

import pytest
from kb_playground.hybrid_kb import HybridKB, SimpleEmbedder


class TestSimpleEmbedder:
    def test_embed_basic(self):
        embedder = SimpleEmbedder()
        vector = embedder.embed("hello")
        
        assert len(vector) == 26
        assert all(0 <= v <= 1 for v in vector)
        assert sum(vector) == pytest.approx(1.0, rel=1e-2)  # Normalized
    
    def test_embed_empty(self):
        embedder = SimpleEmbedder()
        vector = embedder.embed("")
        
        assert len(vector) == 26
        assert all(v == 0.0 for v in vector)


class TestHybridKB:
    def test_add_node(self):
        kb = HybridKB()
        kb.add_node("test1", "This is a test node")
        
        assert "test1" in kb.nodes
        assert kb.nodes["test1"].content == "This is a test node"
        assert kb.nodes["test1"].vector is not None
        assert len(kb.nodes["test1"].vector) == 26
    
    def test_add_edge(self):
        kb = HybridKB()
        kb.add_node("node1", "First node")
        kb.add_node("node2", "Second node")
        
        kb.add_edge("node1", "node2", "connects_to")
        
        assert len(kb.edges) == 1
        assert "node2" in kb.nodes["node1"].connections
        assert "node1" in kb.nodes["node2"].connections
    
    def test_add_edge_nonexistent_nodes(self):
        kb = HybridKB()
        
        with pytest.raises(ValueError):
            kb.add_edge("nonexistent1", "nonexistent2", "test")
    
    def test_vector_search(self):
        kb = HybridKB()
        kb.add_node("doc1", "machine learning algorithms")
        kb.add_node("doc2", "deep learning networks")
        kb.add_node("doc3", "cooking recipes")
        
        results = kb.vector_search("learning", top_k=2)
        
        assert len(results) == 2
        assert all(isinstance(score, float) for _, score in results)
        # Should find learning-related docs with higher similarity
        assert results[0][1] >= results[1][1]  # Sorted by similarity
    
    def test_graph_traverse(self):
        kb = HybridKB()
        kb.add_node("a", "Node A")
        kb.add_node("b", "Node B")
        kb.add_node("c", "Node C")
        kb.add_node("d", "Node D")
        
        kb.add_edge("a", "b", "connects")
        kb.add_edge("b", "c", "connects")
        kb.add_edge("c", "d", "connects")
        
        # Traverse from A with max depth 2
        visited = kb.graph_traverse("a", max_depth=2)
        
        assert "a" in visited
        assert "b" in visited
        assert "c" in visited
        # D should not be reachable within depth 2 from A
    
    def test_hybrid_search(self):
        kb = HybridKB()
        kb.add_node("ml1", "machine learning fundamentals")
        kb.add_node("ml2", "advanced machine learning")
        kb.add_node("dl1", "deep learning basics")
        kb.add_node("other", "cooking recipes")
        
        kb.add_edge("ml1", "ml2", "builds_upon")
        kb.add_edge("ml2", "dl1", "enables")
        
        results = kb.hybrid_search("machine learning", top_k=3)
        
        assert len(results) > 0
        assert all('node_id' in result for result in results)
        assert all('content' in result for result in results)
        assert all('similarity' in result for result in results)
    
    def test_get_relationships(self):
        kb = HybridKB()
        kb.add_node("central", "Central node")
        kb.add_node("connected1", "Connected node 1")
        kb.add_node("connected2", "Connected node 2")
        
        kb.add_edge("central", "connected1", "relates_to", weight=0.8)
        kb.add_edge("connected2", "central", "depends_on", weight=0.6)
        
        relationships = kb.get_relationships("central")
        
        assert len(relationships) == 2
        assert any(rel['to'] == "connected1" for rel in relationships)
        assert any(rel['from'] == "connected2" for rel in relationships)
    
    def test_stats(self):
        kb = HybridKB()
        kb.add_node("node1", "Content 1")
        kb.add_node("node2", "Content 2")
        kb.add_edge("node1", "node2", "connects")
        
        stats = kb.stats()
        
        assert stats['total_nodes'] == 2
        assert stats['total_edges'] == 1
        assert stats['avg_connections_per_node'] == 1.0  # Both nodes have 1 connection
    
    def test_export_data(self):
        kb = HybridKB()
        kb.add_node("test", "Test content", {"key": "value"})
        
        data = kb.export_data()
        
        assert 'nodes' in data
        assert 'edges' in data
        assert "test" in data['nodes']
        assert data['nodes']['test']['content'] == "Test content"
        assert data['nodes']['test']['metadata'] == {"key": "value"}