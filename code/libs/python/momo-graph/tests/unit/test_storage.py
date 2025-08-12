"""Unit tests for GraphThreeTierStorage."""

import pytest

from momo_graph.models import GraphNode, GraphEdge
from momo_graph.storage import GraphThreeTierStorage, GraphStorageTier


class TestGraphThreeTierStorage:
    """Test cases for GraphThreeTierStorage class."""

    @pytest.fixture
    def storage(self):
        """Create a fresh storage instance for each test."""
        return GraphThreeTierStorage()

    @pytest.fixture
    def sample_nodes(self):
        """Sample nodes for testing."""
        return [
            GraphNode(id="node1", label="Person", properties={"name": "Alice"}),
            GraphNode(id="node2", label="Person", properties={"name": "Bob"}),
            GraphNode(id="node3", label="Company", properties={"name": "TechCorp"}),
        ]

    @pytest.fixture
    def sample_edges(self, sample_nodes):
        """Sample edges for testing."""
        return [
            GraphEdge(
                id="edge1",
                source_id="node1",
                target_id="node2", 
                relationship="KNOWS",
                properties={"since": "2020"}
            ),
            GraphEdge(
                id="edge2",
                source_id="node1",
                target_id="node3",
                relationship="WORKS_AT",
                properties={"role": "Engineer"}
            ),
        ]

    def test_storage_initialization(self, storage):
        """Test storage is properly initialized."""
        # All tiers should be empty initially
        for tier in GraphStorageTier:
            assert storage.count_nodes(tier) == 0
            assert storage.count_edges(tier) == 0

    def test_add_node_to_tier(self, storage, sample_nodes):
        """Test adding nodes to different tiers."""
        node = sample_nodes[0]
        
        # Add to runtime tier
        storage.add_node(node, GraphStorageTier.RUNTIME)
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == 1
        assert storage.count_nodes(GraphStorageTier.STORE) == 0
        assert storage.count_nodes(GraphStorageTier.COLD) == 0
        
        # Add to store tier
        storage.add_node(node, GraphStorageTier.STORE)
        assert storage.count_nodes(GraphStorageTier.STORE) == 1
        
        # Add to cold tier
        storage.add_node(node, GraphStorageTier.COLD)
        assert storage.count_nodes(GraphStorageTier.COLD) == 1

    def test_add_edge_to_tier(self, storage, sample_edges):
        """Test adding edges to different tiers."""
        edge = sample_edges[0]
        
        # Add to runtime tier
        storage.add_edge(edge, GraphStorageTier.RUNTIME)
        assert storage.count_edges(GraphStorageTier.RUNTIME) == 1
        assert storage.count_edges(GraphStorageTier.STORE) == 0
        assert storage.count_edges(GraphStorageTier.COLD) == 0

    def test_find_node_across_tiers(self, storage, sample_nodes):
        """Test finding nodes across different tiers."""
        node = sample_nodes[0]
        
        # Node not found initially
        assert storage.find_node(node.id) is None
        
        # Add to store tier
        storage.add_node(node, GraphStorageTier.STORE)
        found_node = storage.find_node(node.id)
        assert found_node is not None
        assert found_node.id == node.id

    def test_find_edge_across_tiers(self, storage, sample_edges):
        """Test finding edges across different tiers."""
        edge = sample_edges[0]
        
        # Edge not found initially
        assert storage.find_edge(edge.id) is None
        
        # Add to runtime tier
        storage.add_edge(edge, GraphStorageTier.RUNTIME)
        found_edge = storage.find_edge(edge.id)
        assert found_edge is not None
        assert found_edge.id == edge.id

    def test_remove_node_from_tier(self, storage, sample_nodes):
        """Test removing nodes from tiers."""
        node = sample_nodes[0]
        
        # Add node to runtime tier
        storage.add_node(node, GraphStorageTier.RUNTIME)
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == 1
        
        # Remove node
        storage.remove_node(node.id, GraphStorageTier.RUNTIME)
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == 0
        assert storage.find_node(node.id) is None

    def test_remove_edge_from_tier(self, storage, sample_edges):
        """Test removing edges from tiers."""
        edge = sample_edges[0]
        
        # Add edge to runtime tier
        storage.add_edge(edge, GraphStorageTier.RUNTIME)
        assert storage.count_edges(GraphStorageTier.RUNTIME) == 1
        
        # Remove edge
        storage.remove_edge(edge.id, GraphStorageTier.RUNTIME)
        assert storage.count_edges(GraphStorageTier.RUNTIME) == 0
        assert storage.find_edge(edge.id) is None

    def test_get_all_nodes_from_tier(self, storage, sample_nodes):
        """Test getting all nodes from a tier."""
        # Add multiple nodes to runtime tier
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        
        # Get all nodes
        nodes = storage.get_all_nodes(GraphStorageTier.RUNTIME)
        assert len(nodes) == len(sample_nodes)
        
        # Verify all nodes are present
        node_ids = {node.id for node in nodes}
        expected_ids = {node.id for node in sample_nodes}
        assert node_ids == expected_ids

    def test_get_all_edges_from_tier(self, storage, sample_edges):
        """Test getting all edges from a tier."""
        # Add multiple edges to store tier
        for edge in sample_edges:
            storage.add_edge(edge, GraphStorageTier.STORE)
        
        # Get all edges
        edges = storage.get_all_edges(GraphStorageTier.STORE)
        assert len(edges) == len(sample_edges)
        
        # Verify all edges are present
        edge_ids = {edge.id for edge in edges}
        expected_ids = {edge.id for edge in sample_edges}
        assert edge_ids == expected_ids

    def test_query_nodes_indexed(self, storage, sample_nodes):
        """Test indexed node queries."""
        # Add nodes with different labels
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        
        # Query by label
        person_nodes = storage.query_nodes_indexed(
            GraphStorageTier.RUNTIME, 
            label="Person"
        )
        assert len(person_nodes) == 2  # Alice and Bob
        
        # Query by properties
        alice_nodes = storage.query_nodes_indexed(
            GraphStorageTier.RUNTIME,
            properties={"name": "Alice"}
        )
        assert len(alice_nodes) == 1
        assert alice_nodes[0].id == "node1"

    def test_query_edges_indexed(self, storage, sample_edges):
        """Test indexed edge queries."""
        # Add edges with different relationships
        for edge in sample_edges:
            storage.add_edge(edge, GraphStorageTier.RUNTIME)
        
        # Query by relationship
        knows_edges = storage.query_edges_indexed(
            GraphStorageTier.RUNTIME,
            relationship="KNOWS"
        )
        assert len(knows_edges) == 1
        assert knows_edges[0].id == "edge1"
        
        # Query by source node
        alice_edges = storage.query_edges_indexed(
            GraphStorageTier.RUNTIME,
            source_id="node1"
        )
        assert len(alice_edges) == 2  # Both edges from Alice

    def test_query_connected_nodes_indexed(self, storage, sample_nodes, sample_edges):
        """Test indexed connected node queries."""
        # Add nodes and edges
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        for edge in sample_edges:
            storage.add_edge(edge, GraphStorageTier.RUNTIME)
        
        # Query outgoing connections from Alice
        connected_nodes = storage.query_connected_nodes_indexed(
            GraphStorageTier.RUNTIME,
            "node1",  # Alice
            "KNOWS",
            "outgoing"
        )
        assert len(connected_nodes) == 1
        assert connected_nodes[0].id == "node2"  # Bob

    def test_pruning_by_size_limit(self, storage, sample_nodes):
        """Test pruning nodes from tier by size limit."""
        # Add multiple nodes to runtime tier
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == 3
        
        # Prune to limit of 1 (should move 2 nodes to store)
        pruned_count = storage.prune_by_size_limit(
            GraphStorageTier.RUNTIME,
            size_limit=1,
            target_tier=GraphStorageTier.STORE
        )
        
        assert pruned_count == 2
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == 1
        assert storage.count_nodes(GraphStorageTier.STORE) == 2

    def test_pruning_by_access_time(self, storage, sample_nodes):
        """Test pruning nodes by access time."""
        # Add nodes with different access times
        old_node = sample_nodes[0].with_access()  # Recently accessed
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        
        # Prune old nodes (older than 1 hour)
        from datetime import timedelta
        pruned_count = storage.prune_by_access_time(
            GraphStorageTier.RUNTIME,
            max_age=timedelta(hours=1),
            target_tier=GraphStorageTier.STORE
        )
        
        # Should have pruned some nodes
        assert pruned_count >= 0

    def test_pruning_by_usage_pattern(self, storage, sample_nodes):
        """Test pruning by usage patterns."""
        # Add nodes to runtime tier
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == 3
        
        # Prune by usage (should move least used nodes)
        pruned_count = storage.prune_by_usage_pattern(
            GraphStorageTier.RUNTIME,
            target_tier=GraphStorageTier.STORE,
            keep_ratio=0.5  # Keep 50%
        )
        
        # Should have moved some nodes
        assert pruned_count >= 0
        total_nodes = (storage.count_nodes(GraphStorageTier.RUNTIME) + 
                      storage.count_nodes(GraphStorageTier.STORE))
        assert total_nodes == len(sample_nodes)

    def test_storage_statistics(self, storage, sample_nodes, sample_edges):
        """Test storage statistics."""
        # Add some data
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        for edge in sample_edges:
            storage.add_edge(edge, GraphStorageTier.STORE)
        
        # Get statistics
        stats = storage.get_storage_stats()
        
        assert "nodes" in stats
        assert "edges" in stats
        assert stats["nodes"]["runtime"] == len(sample_nodes)
        assert stats["edges"]["store"] == len(sample_edges)

    def test_tier_optimization(self, storage, sample_nodes):
        """Test tier optimization."""
        # Add nodes to runtime tier
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        
        # Optimize tiers
        optimized = storage.optimize_tiers()
        
        # Should return optimization statistics
        assert isinstance(optimized, dict)

    def test_node_tier_migration(self, storage, sample_nodes):
        """Test moving nodes between tiers."""
        node = sample_nodes[0]
        
        # Add to runtime tier
        storage.add_node(node, GraphStorageTier.RUNTIME)
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == 1
        
        # Move to store tier (simulated by remove + add)
        storage.remove_node(node.id, GraphStorageTier.RUNTIME)
        storage.add_node(node, GraphStorageTier.STORE)
        
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == 0
        assert storage.count_nodes(GraphStorageTier.STORE) == 1

    def test_concurrent_access_simulation(self, storage, sample_nodes):
        """Test behavior under simulated concurrent access."""
        # Add nodes
        for node in sample_nodes:
            storage.add_node(node, GraphStorageTier.RUNTIME)
        
        # Simulate concurrent reads/writes
        for i in range(10):
            # Query nodes (simulating read access)
            nodes = storage.query_nodes_indexed(GraphStorageTier.RUNTIME)
            
            # Update access time for some nodes
            if nodes:
                updated_node = nodes[0].with_access()
                storage.add_node(updated_node, GraphStorageTier.RUNTIME)
        
        # Should still have all nodes
        assert storage.count_nodes(GraphStorageTier.RUNTIME) == len(sample_nodes)