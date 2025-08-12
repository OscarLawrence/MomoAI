"""
Unit tests for graph data models.

Tests the immutable GraphNode, GraphEdge, and GraphDiff models.
"""

import pytest
from datetime import datetime
from uuid import UUID

from momo_graph import GraphNode, GraphEdge, GraphDiff, GraphDiffType


class TestGraphNode:
    """Test the immutable GraphNode model."""

    def test_node_creation(self):
        """Test basic node creation with required fields."""
        node = GraphNode(label="Person", properties={"name": "Alice"})

        assert node.label == "Person"
        assert node.properties["name"] == "Alice"
        assert isinstance(UUID(node.id), UUID)
        assert node.access_count == 0
        assert isinstance(node.created_at, datetime)
        assert isinstance(node.last_accessed, datetime)

    def test_node_immutability(self):
        """Test that nodes are immutable."""
        node = GraphNode(label="Person", properties={"name": "Alice"})

        # This should raise an error due to frozen=True
        with pytest.raises(Exception):
            node.label = "NewLabel"

    def test_node_with_access(self):
        """Test access tracking functionality."""
        node = GraphNode(label="Person", properties={"name": "Alice"})
        original_count = node.access_count
        original_time = node.last_accessed

        # Create new node with updated access
        updated_node = node.with_access()

        assert updated_node.access_count == original_count + 1
        assert updated_node.last_accessed > original_time
        assert updated_node.id == node.id  # Same node
        assert updated_node.label == node.label

    def test_node_with_embedding(self):
        """Test embedding functionality."""
        node = GraphNode(label="Person", properties={"name": "Alice"})
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        model = "test-model"

        # Create new node with embedding
        embedded_node = node.with_embedding(embedding, model)

        assert embedded_node.embedding == embedding
        assert embedded_node.embedding_model == model
        assert isinstance(embedded_node.embedding_timestamp, datetime)
        assert embedded_node.id == node.id  # Same node


class TestGraphEdge:
    """Test the immutable GraphEdge model."""

    def test_edge_creation(self):
        """Test basic edge creation with required fields."""
        edge = GraphEdge(
            source_id="node1",
            target_id="node2",
            relationship="KNOWS",
            properties={"since": "2020"},
        )

        assert edge.source_id == "node1"
        assert edge.target_id == "node2"
        assert edge.relationship == "KNOWS"
        assert edge.properties["since"] == "2020"
        assert isinstance(UUID(edge.id), UUID)
        assert edge.access_count == 0

    def test_edge_immutability(self):
        """Test that edges are immutable."""
        edge = GraphEdge(source_id="n1", target_id="n2", relationship="KNOWS")

        # This should raise an error due to frozen=True
        with pytest.raises(Exception):
            edge.relationship = "LIKES"

    def test_edge_with_access(self):
        """Test access tracking functionality."""
        edge = GraphEdge(source_id="n1", target_id="n2", relationship="KNOWS")
        original_count = edge.access_count

        # Create new edge with updated access
        updated_edge = edge.with_access()

        assert updated_edge.access_count == original_count + 1
        assert updated_edge.id == edge.id  # Same edge
        assert updated_edge.relationship == edge.relationship


class TestGraphDiff:
    """Test the immutable GraphDiff model."""

    def test_diff_creation(self):
        """Test basic diff creation."""
        node = GraphNode(label="Person", properties={"name": "Alice"})
        diff = GraphDiff(operation=GraphDiffType.INSERT_NODE, node=node)

        assert diff.operation == GraphDiffType.INSERT_NODE
        assert diff.node == node
        assert diff.edge is None
        assert isinstance(UUID(diff.id), UUID)
        assert isinstance(diff.timestamp, datetime)

    def test_diff_reverse(self):
        """Test diff reversal for rollback."""
        node = GraphNode(label="Person", properties={"name": "Alice"})
        insert_diff = GraphDiff(operation=GraphDiffType.INSERT_NODE, node=node)

        # Create reverse diff
        delete_diff = insert_diff.reverse()

        assert delete_diff.operation == GraphDiffType.DELETE_NODE
        assert delete_diff.node == node
        assert delete_diff.id != insert_diff.id  # New diff
        assert delete_diff.timestamp > insert_diff.timestamp

    def test_all_diff_types_reversible(self):
        """Test that all diff types can be reversed."""
        node = GraphNode(label="Person", properties={"name": "Alice"})
        edge = GraphEdge(source_id="n1", target_id="n2", relationship="KNOWS")

        test_cases = [
            (GraphDiffType.INSERT_NODE, GraphDiffType.DELETE_NODE, node, None),
            (GraphDiffType.DELETE_NODE, GraphDiffType.INSERT_NODE, node, None),
            (GraphDiffType.INSERT_EDGE, GraphDiffType.DELETE_EDGE, None, edge),
            (GraphDiffType.DELETE_EDGE, GraphDiffType.INSERT_EDGE, None, edge),
        ]

        for original_op, expected_reverse_op, test_node, test_edge in test_cases:
            diff = GraphDiff(operation=original_op, node=test_node, edge=test_edge)
            reverse_diff = diff.reverse()
            assert reverse_diff.operation == expected_reverse_op


class TestGraphDiffType:
    """Test the GraphDiffType enumeration."""

    def test_all_diff_types_exist(self):
        """Test that all expected diff types are available."""
        expected_types = ["INSERT_NODE", "DELETE_NODE", "INSERT_EDGE", "DELETE_EDGE"]

        for type_name in expected_types:
            assert hasattr(GraphDiffType, type_name)
            assert isinstance(getattr(GraphDiffType, type_name), GraphDiffType)

    def test_diff_type_values(self):
        """Test that diff type values are correct."""
        assert GraphDiffType.INSERT_NODE.value == "insert_node"
        assert GraphDiffType.DELETE_NODE.value == "delete_node"
        assert GraphDiffType.INSERT_EDGE.value == "insert_edge"
        assert GraphDiffType.DELETE_EDGE.value == "delete_edge"
