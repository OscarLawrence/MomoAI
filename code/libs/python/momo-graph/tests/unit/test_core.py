"""
Unit tests for the GraphBackend core functionality.

Tests immutable operations, diff-based rollback, and query pipeline.
"""

import pytest
from datetime import datetime

from momo_graph import GraphBackend, GraphNode, GraphEdge, GraphDiff, GraphDiffType


class TestGraphBackend:
    """Test core graph backend operations."""

    @pytest.fixture
    async def graph(self):
        """Create a fresh graph backend for testing."""
        graph = GraphBackend()
        await graph.initialize()
        yield graph
        await graph.close()

    @pytest.mark.asyncio
    async def test_graph_initialization(self, graph):
        """Test graph backend initialization and cleanup."""
        assert graph._initialized is True

        # Test context manager
        async with GraphBackend() as ctx_graph:
            assert ctx_graph._initialized is True
        # After context exit, should be closed

    @pytest.mark.asyncio
    async def test_insert_node(self, graph):
        """Test node insertion creates diff and stores node."""
        node = GraphNode(label="Person", properties={"name": "Alice"})
        diff = await graph.insert_node(node)

        # Check diff was created
        assert isinstance(diff, GraphDiff)
        assert diff.operation == GraphDiffType.INSERT_NODE
        assert diff.node == node

        # Check node was stored
        node_count = await graph.count_nodes()
        assert node_count == 1

    @pytest.mark.asyncio
    async def test_insert_edge(self, graph):
        """Test edge insertion creates diff and stores edge."""
        # First create nodes
        node1 = GraphNode(label="Person", properties={"name": "Alice"})
        node2 = GraphNode(label="Person", properties={"name": "Bob"})
        await graph.insert_node(node1)
        await graph.insert_node(node2)

        # Create edge
        edge = GraphEdge(source_id=node1.id, target_id=node2.id, relationship="KNOWS")
        diff = await graph.insert_edge(edge)

        # Check diff was created
        assert isinstance(diff, GraphDiff)
        assert diff.operation == GraphDiffType.INSERT_EDGE
        assert diff.edge == edge

        # Check edge was stored
        edge_count = await graph.count_edges()
        assert edge_count == 1

    @pytest.mark.asyncio
    async def test_delete_node(self, graph):
        """Test node deletion creates diff and removes node."""
        # Insert a node first
        node = GraphNode(label="Person", properties={"name": "Alice"})
        await graph.insert_node(node)
        assert await graph.count_nodes() == 1

        # Delete the node
        diff = await graph.delete_node(node.id)

        # Check diff was created
        assert isinstance(diff, GraphDiff)
        assert diff.operation == GraphDiffType.DELETE_NODE
        assert diff.node.id == node.id

        # Check node was removed
        assert await graph.count_nodes() == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_node(self, graph):
        """Test deleting nonexistent node raises error."""
        with pytest.raises(ValueError, match="Node nonexistent not found"):
            await graph.delete_node("nonexistent")

    @pytest.mark.asyncio
    async def test_rollback_operations(self, graph):
        """Test rollback functionality with multiple operations."""
        # Insert two nodes
        node1 = GraphNode(label="Person", properties={"name": "Alice"})
        node2 = GraphNode(label="Person", properties={"name": "Bob"})

        await graph.insert_node(node1)
        await graph.insert_node(node2)
        assert await graph.count_nodes() == 2

        # Rollback last operation
        await graph.rollback(steps=1)
        assert await graph.count_nodes() == 1

        # Rollback all operations
        await graph.rollback(steps=2)  # One more rollback operation was added
        assert await graph.count_nodes() == 0

    @pytest.mark.asyncio
    async def test_rollback_to_timestamp(self, graph):
        """Test rollback to specific timestamp."""
        # Insert a node
        node1 = GraphNode(label="Person", properties={"name": "Alice"})
        await graph.insert_node(node1)

        # Record timestamp
        checkpoint = datetime.utcnow()

        # Insert another node after checkpoint
        node2 = GraphNode(label="Person", properties={"name": "Bob"})
        await graph.insert_node(node2)
        assert await graph.count_nodes() == 2

        # Rollback to checkpoint
        await graph.rollback_to_timestamp(checkpoint)
        assert await graph.count_nodes() == 1

    @pytest.mark.asyncio
    async def test_diff_history(self, graph):
        """Test diff history tracking."""
        # Initially empty
        history = await graph.get_diff_history()
        assert len(history) == 0

        # Insert a node
        node = GraphNode(label="Person", properties={"name": "Alice"})
        await graph.insert_node(node)

        # Check history
        history = await graph.get_diff_history()
        assert len(history) == 1
        assert history[0].operation == GraphDiffType.INSERT_NODE

    @pytest.mark.asyncio
    async def test_query_nodes_basic(self, graph):
        """Test basic node querying."""
        # Insert test nodes
        person_node = GraphNode(label="Person", properties={"name": "Alice", "age": 25})
        place_node = GraphNode(
            label="Place", properties={"name": "Paris", "country": "France"}
        )

        await graph.insert_node(person_node)
        await graph.insert_node(place_node)

        # Query by label
        result = await graph.query_nodes(label="Person")
        assert len(result.nodes) == 1
        assert result.nodes[0].label == "Person"
        assert result.query_time_ms > 0

        # Query by properties
        result = await graph.query_nodes(properties={"name": "Alice"})
        assert len(result.nodes) == 1
        assert result.nodes[0].properties["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_query_edges_basic(self, graph):
        """Test basic edge querying."""
        # Create nodes and edge
        node1 = GraphNode(label="Person", properties={"name": "Alice"})
        node2 = GraphNode(label="Person", properties={"name": "Bob"})
        await graph.insert_node(node1)
        await graph.insert_node(node2)

        edge = GraphEdge(
            source_id=node1.id,
            target_id=node2.id,
            relationship="KNOWS",
            properties={"since": "2020"},
        )
        await graph.insert_edge(edge)

        # Query by relationship
        result = await graph.query_edges(relationship="KNOWS")
        assert len(result.edges) == 1
        assert result.edges[0].relationship == "KNOWS"

        # Query by source
        result = await graph.query_edges(source_id=node1.id)
        assert len(result.edges) == 1
        assert result.edges[0].source_id == node1.id

    @pytest.mark.asyncio
    async def test_connected_nodes_query(self, graph):
        """Test querying connected nodes."""
        # Create a small graph: Alice -> Bob -> Charlie
        alice = GraphNode(label="Person", properties={"name": "Alice"})
        bob = GraphNode(label="Person", properties={"name": "Bob"})
        charlie = GraphNode(label="Person", properties={"name": "Charlie"})

        await graph.insert_node(alice)
        await graph.insert_node(bob)
        await graph.insert_node(charlie)

        # Create edges
        edge1 = GraphEdge(source_id=alice.id, target_id=bob.id, relationship="KNOWS")
        edge2 = GraphEdge(source_id=bob.id, target_id=charlie.id, relationship="KNOWS")
        await graph.insert_edge(edge1)
        await graph.insert_edge(edge2)

        # Query outgoing connections from Alice
        result = await graph.query_connected_nodes(
            alice.id, "KNOWS", direction="outgoing"
        )
        assert len(result.nodes) == 1
        assert result.nodes[0].properties["name"] == "Bob"

        # Query incoming connections to Bob
        result = await graph.query_connected_nodes(
            bob.id, "KNOWS", direction="incoming"
        )
        assert len(result.nodes) == 1
        assert result.nodes[0].properties["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_export_json(self, graph):
        """Test JSON export functionality."""
        # Insert some test data
        node = GraphNode(label="Person", properties={"name": "Alice"})
        await graph.insert_node(node)

        # Export to JSON
        data = await graph.export_json()

        # Validate structure
        assert "nodes" in data
        assert "edges" in data
        assert "diffs" in data
        assert "metadata" in data

        assert len(data["nodes"]) == 1
        assert len(data["diffs"]) == 1
        assert data["metadata"]["total_nodes"] == 1
        assert data["metadata"]["total_edges"] == 0
