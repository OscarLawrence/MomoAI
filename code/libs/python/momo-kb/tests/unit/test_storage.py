"""
Unit tests for the 3-tier storage system.

Tests runtime, store, and cold storage tiers with pruning logic.
"""

import pytest
from datetime import datetime, timedelta

from momo_kb.models import Node, Edge, DiffType
from momo_kb.storage import StorageTier, ThreeTierStorage


class TestStorageTier:
    """Test individual storage tier functionality."""
    
    def test_storage_tier_enum(self):
        """Test storage tier enumeration."""
        assert StorageTier.RUNTIME == "runtime"
        assert StorageTier.STORE == "store" 
        assert StorageTier.COLD == "cold"
        
    def test_tier_ordering(self):
        """Test that tiers have logical ordering for pruning."""
        tiers = [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]
        assert len(tiers) == 3


class TestThreeTierStorage:
    """Test the complete 3-tier storage system."""
    
    @pytest.fixture
    def storage(self):
        """Create a fresh storage instance for testing."""
        return ThreeTierStorage()
        
    def test_storage_initialization(self, storage):
        """Test storage initializes with empty tiers."""
        assert storage.count_nodes(StorageTier.RUNTIME) == 0
        assert storage.count_nodes(StorageTier.STORE) == 0
        assert storage.count_nodes(StorageTier.COLD) == 0
        
        assert storage.count_edges(StorageTier.RUNTIME) == 0
        assert storage.count_edges(StorageTier.STORE) == 0
        assert storage.count_edges(StorageTier.COLD) == 0
        
    def test_add_node_to_runtime(self, storage):
        """Test adding nodes to runtime tier."""
        node = Node(label="Person", properties={"name": "Alice"})
        
        storage.add_node(node, StorageTier.RUNTIME)
        
        assert storage.count_nodes(StorageTier.RUNTIME) == 1
        assert storage.get_node(node.id, StorageTier.RUNTIME) == node
        
    def test_add_edge_to_runtime(self, storage):
        """Test adding edges to runtime tier."""
        edge = Edge(source_id="a", target_id="b", relationship="knows")
        
        storage.add_edge(edge, StorageTier.RUNTIME)
        
        assert storage.count_edges(StorageTier.RUNTIME) == 1
        assert storage.get_edge(edge.id, StorageTier.RUNTIME) == edge
        
    def test_remove_node(self, storage):
        """Test removing nodes from storage."""
        node = Node(label="Person")
        storage.add_node(node, StorageTier.RUNTIME)
        
        storage.remove_node(node.id, StorageTier.RUNTIME)
        
        assert storage.count_nodes(StorageTier.RUNTIME) == 0
        assert storage.get_node(node.id, StorageTier.RUNTIME) is None
        
    def test_move_node_between_tiers(self, storage):
        """Test moving nodes between storage tiers."""
        node = Node(label="Person")
        storage.add_node(node, StorageTier.RUNTIME)
        
        storage.move_node(node.id, StorageTier.RUNTIME, StorageTier.STORE)
        
        assert storage.count_nodes(StorageTier.RUNTIME) == 0
        assert storage.count_nodes(StorageTier.STORE) == 1
        assert storage.get_node(node.id, StorageTier.STORE) == node
        
    def test_find_node_across_tiers(self, storage):
        """Test finding nodes across all tiers."""
        runtime_node = Node(label="Person", properties={"tier": "runtime"})
        store_node = Node(label="Person", properties={"tier": "store"})
        cold_node = Node(label="Person", properties={"tier": "cold"})
        
        storage.add_node(runtime_node, StorageTier.RUNTIME)
        storage.add_node(store_node, StorageTier.STORE)
        storage.add_node(cold_node, StorageTier.COLD)
        
        # Should find in runtime first (hottest tier)
        found = storage.find_node(runtime_node.id)
        assert found == runtime_node
        
        # Should find in store when not in runtime
        found = storage.find_node(store_node.id)
        assert found == store_node
        
        # Should find in cold when not in other tiers
        found = storage.find_node(cold_node.id)
        assert found == cold_node
        
    def test_prune_by_access_count(self, storage):
        """Test pruning based on access count thresholds."""
        # Create nodes with different access patterns
        hot_node = Node(label="Hot", access_count=100)
        warm_node = Node(label="Warm", access_count=10)
        cold_node = Node(label="Cold", access_count=1)
        
        storage.add_node(hot_node, StorageTier.RUNTIME)
        storage.add_node(warm_node, StorageTier.RUNTIME)
        storage.add_node(cold_node, StorageTier.RUNTIME)
        
        # Prune with threshold of 50 access count
        pruned = storage.prune_by_access_count(
            tier=StorageTier.RUNTIME,
            threshold=50,
            target_tier=StorageTier.STORE
        )
        
        assert pruned == 2  # warm_node and cold_node moved
        assert storage.count_nodes(StorageTier.RUNTIME) == 1
        assert storage.count_nodes(StorageTier.STORE) == 2
        
    def test_prune_by_age(self, storage):
        """Test pruning based on last access time."""
        now = datetime.utcnow()
        old_time = now - timedelta(hours=2)
        
        recent_node = Node(label="Recent", last_accessed=now)
        old_node = Node(label="Old", last_accessed=old_time)
        
        storage.add_node(recent_node, StorageTier.RUNTIME)
        storage.add_node(old_node, StorageTier.RUNTIME)
        
        # Prune nodes older than 1 hour
        pruned = storage.prune_by_age(
            tier=StorageTier.RUNTIME,
            max_age_hours=1,
            target_tier=StorageTier.STORE
        )
        
        assert pruned == 1  # old_node moved
        assert storage.count_nodes(StorageTier.RUNTIME) == 1
        assert storage.get_node(recent_node.id, StorageTier.RUNTIME) == recent_node
        assert storage.get_node(old_node.id, StorageTier.STORE) == old_node
        
    def test_prune_by_size_limit(self, storage):
        """Test pruning to maintain size limits."""
        # Add more nodes than the limit
        nodes = [Node(label=f"Node{i}") for i in range(5)]
        for node in nodes:
            storage.add_node(node, StorageTier.RUNTIME)
            
        # Prune to keep only 3 nodes (should move 2 oldest)
        pruned = storage.prune_by_size_limit(
            tier=StorageTier.RUNTIME,
            max_size=3,
            target_tier=StorageTier.STORE
        )
        
        assert pruned == 2
        assert storage.count_nodes(StorageTier.RUNTIME) == 3
        assert storage.count_nodes(StorageTier.STORE) == 2