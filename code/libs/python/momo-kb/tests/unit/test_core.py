"""
Unit tests for the core KnowledgeBase functionality.

Tests immutable operations, diff-based rollback, and query pipeline.
"""

import pytest
from datetime import datetime

from momo_kb.core import KnowledgeBase
from momo_kb.models import Node, Edge, DiffType, QueryResult


class TestKnowledgeBase:
    """Test core knowledge base operations."""

    @pytest.fixture
    async def kb(self):
        """Create a fresh knowledge base for testing."""
        kb = KnowledgeBase()
        await kb.initialize()
        return kb

    async def test_kb_initialization(self, kb):
        """Test knowledge base initializes correctly."""
        assert await kb.count_nodes() == 0
        assert await kb.count_edges() == 0
        assert len(await kb.get_diff_history()) == 0

    async def test_insert_node(self, kb):
        """Test inserting a node creates diff and updates storage."""
        node = Node(label="Person", properties={"name": "Alice"})

        result = await kb.insert_node(node)

        assert result.operation == DiffType.INSERT_NODE
        assert result.node == node
        assert await kb.count_nodes() == 1

        # Check diff history
        history = await kb.get_diff_history()
        assert len(history) == 1
        assert history[0].operation == DiffType.INSERT_NODE

    async def test_insert_edge(self, kb):
        """Test inserting an edge between nodes."""
        # First create nodes
        alice = Node(label="Person", properties={"name": "Alice"})
        bob = Node(label="Person", properties={"name": "Bob"})

        await kb.insert_node(alice)
        await kb.insert_node(bob)

        # Then create edge
        edge = Edge(source_id=alice.id, target_id=bob.id, relationship="knows")
        result = await kb.insert_edge(edge)

        assert result.operation == DiffType.INSERT_EDGE
        assert result.edge == edge
        assert await kb.count_edges() == 1

    async def test_delete_node(self, kb):
        """Test deleting a node creates diff and removes from storage."""
        node = Node(label="Person")
        await kb.insert_node(node)

        result = await kb.delete_node(node.id)

        assert result.operation == DiffType.DELETE_NODE
        assert result.node.id == node.id
        assert await kb.count_nodes() == 0

    async def test_delete_edge(self, kb):
        """Test deleting an edge."""
        alice = Node(label="Person", properties={"name": "Alice"})
        bob = Node(label="Person", properties={"name": "Bob"})
        await kb.insert_node(alice)
        await kb.insert_node(bob)

        edge = Edge(source_id=alice.id, target_id=bob.id, relationship="knows")
        await kb.insert_edge(edge)

        result = await kb.delete_edge(edge.id)

        assert result.operation == DiffType.DELETE_EDGE
        assert result.edge.id == edge.id
        assert await kb.count_edges() == 0

    async def test_rollback_single_step(self, kb):
        """Test rolling back one operation."""
        node = Node(label="Person")
        await kb.insert_node(node)
        assert await kb.count_nodes() == 1

        await kb.rollback(steps=1)

        assert await kb.count_nodes() == 0

        # History should show both original and rollback operations
        history = await kb.get_diff_history()
        assert len(history) == 2
        assert history[0].operation == DiffType.INSERT_NODE
        assert history[1].operation == DiffType.DELETE_NODE

    async def test_rollback_multiple_steps(self, kb):
        """Test rolling back multiple operations."""
        # Create several operations
        alice = Node(label="Person", properties={"name": "Alice"})
        bob = Node(label="Person", properties={"name": "Bob"})
        await kb.insert_node(alice)
        await kb.insert_node(bob)

        edge = Edge(source_id=alice.id, target_id=bob.id, relationship="knows")
        await kb.insert_edge(edge)

        assert await kb.count_nodes() == 2
        assert await kb.count_edges() == 1

        # Rollback all 3 operations
        await kb.rollback(steps=3)

        assert await kb.count_nodes() == 0
        assert await kb.count_edges() == 0

    async def test_rollback_to_timestamp(self, kb):
        """Test rolling back to a specific timestamp."""
        # Record timestamp before operations
        checkpoint = datetime.utcnow()

        # Add some operations after checkpoint
        node = Node(label="Person")
        await kb.insert_node(node)

        # Rollback to checkpoint
        await kb.rollback_to_timestamp(checkpoint)

        assert await kb.count_nodes() == 0

    async def test_query_by_label(self, kb):
        """Test querying nodes by label."""
        alice = Node(label="Person", properties={"name": "Alice"})
        company = Node(label="Company", properties={"name": "TechCorp"})

        await kb.insert_node(alice)
        await kb.insert_node(company)

        result = await kb.query_nodes(label="Person")

        assert len(result.nodes) == 1
        assert result.nodes[0].properties["name"] == "Alice"

    async def test_query_by_properties(self, kb):
        """Test querying nodes by properties."""
        alice = Node(label="Person", properties={"name": "Alice", "age": 30})
        bob = Node(label="Person", properties={"name": "Bob", "age": 25})

        await kb.insert_node(alice)
        await kb.insert_node(bob)

        result = await kb.query_nodes(properties={"age": 30})

        assert len(result.nodes) == 1
        assert result.nodes[0].properties["name"] == "Alice"

    async def test_query_relationships(self, kb):
        """Test querying edges by relationship type."""
        alice = Node(label="Person", properties={"name": "Alice"})
        bob = Node(label="Person", properties={"name": "Bob"})
        await kb.insert_node(alice)
        await kb.insert_node(bob)

        knows_edge = Edge(source_id=alice.id, target_id=bob.id, relationship="knows")
        likes_edge = Edge(source_id=alice.id, target_id=bob.id, relationship="likes")
        await kb.insert_edge(knows_edge)
        await kb.insert_edge(likes_edge)

        result = await kb.query_edges(relationship="knows")

        assert len(result.edges) == 1
        assert result.edges[0].relationship == "knows"

    async def test_prune_runtime_storage(self, kb):
        """Test pruning runtime storage to manage memory."""
        # Add many nodes to runtime
        nodes = [Node(label=f"Node{i}") for i in range(10)]
        for node in nodes:
            await kb.insert_node(node)

        # Prune to keep only 5 in runtime
        pruned_count = await kb.prune(runtime_limit=5)

        assert pruned_count > 0
        # Runtime should have at most 5 nodes now
        runtime_count = await kb.count_nodes(tier="runtime")
        assert runtime_count <= 5

    async def test_export_json(self, kb):
        """Test exporting knowledge base to JSON format."""
        alice = Node(label="Person", properties={"name": "Alice"})
        bob = Node(label="Person", properties={"name": "Bob"})
        await kb.insert_node(alice)
        await kb.insert_node(bob)

        edge = Edge(source_id=alice.id, target_id=bob.id, relationship="knows")
        await kb.insert_edge(edge)

        export_data = await kb.export_json()

        assert "nodes" in export_data
        assert "edges" in export_data
        assert "diffs" in export_data
        assert len(export_data["nodes"]) == 2
        assert len(export_data["edges"]) == 1
