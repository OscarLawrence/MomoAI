"""
Unit tests for core data models.

Tests the immutable node, edge, and diff models.
"""

import pytest
from datetime import datetime
from uuid import UUID

from momo_kb.models import Node, Edge, Diff, DiffType, QueryResult


class TestNode:
    """Test the immutable Node model."""

    def test_node_creation(self):
        """Test basic node creation with required fields."""
        node = Node(label="Person", properties={"name": "Alice"})

        assert node.label == "Person"
        assert node.properties == {"name": "Alice"}
        assert UUID(node.id)  # Valid UUID
        assert isinstance(node.created_at, datetime)
        assert node.access_count == 0

    def test_node_immutability(self):
        """Test that nodes are immutable."""
        node = Node(label="Person")

        with pytest.raises(Exception):  # Pydantic frozen model
            node.label = "NewLabel"

    def test_node_access_tracking(self):
        """Test access tracking creates new node instance."""
        node = Node(label="Person")
        original_count = node.access_count
        original_time = node.last_accessed

        accessed_node = node.with_access()

        # Original unchanged
        assert node.access_count == original_count
        assert node.last_accessed == original_time

        # New node updated
        assert accessed_node.access_count == original_count + 1
        assert accessed_node.last_accessed > original_time
        assert accessed_node.id == node.id  # Same node, different instance


class TestEdge:
    """Test the immutable Edge model."""

    def test_edge_creation(self):
        """Test basic edge creation with required fields."""
        edge = Edge(source_id="node1", target_id="node2", relationship="knows")

        assert edge.source_id == "node1"
        assert edge.target_id == "node2"
        assert edge.relationship == "knows"
        assert UUID(edge.id)  # Valid UUID
        assert isinstance(edge.created_at, datetime)
        assert edge.access_count == 0

    def test_edge_immutability(self):
        """Test that edges are immutable."""
        edge = Edge(source_id="a", target_id="b", relationship="knows")

        with pytest.raises(Exception):  # Pydantic frozen model
            edge.relationship = "likes"

    def test_edge_access_tracking(self):
        """Test access tracking creates new edge instance."""
        edge = Edge(source_id="a", target_id="b", relationship="knows")
        original_count = edge.access_count

        accessed_edge = edge.with_access()

        assert edge.access_count == original_count
        assert accessed_edge.access_count == original_count + 1
        assert accessed_edge.id == edge.id


class TestDiff:
    """Test the immutable Diff model for operations."""

    def test_node_insert_diff(self):
        """Test creating a diff for node insertion."""
        node = Node(label="Person", properties={"name": "Alice"})
        diff = Diff(operation=DiffType.INSERT_NODE, node=node)

        assert diff.operation == DiffType.INSERT_NODE
        assert diff.node == node
        assert diff.edge is None
        assert isinstance(diff.timestamp, datetime)

    def test_edge_insert_diff(self):
        """Test creating a diff for edge insertion."""
        edge = Edge(source_id="a", target_id="b", relationship="knows")
        diff = Diff(operation=DiffType.INSERT_EDGE, edge=edge)

        assert diff.operation == DiffType.INSERT_EDGE
        assert diff.edge == edge
        assert diff.node is None

    def test_diff_reverse(self):
        """Test creating reverse diffs for rollback."""
        node = Node(label="Person")
        insert_diff = Diff(operation=DiffType.INSERT_NODE, node=node)

        reverse_diff = insert_diff.reverse()

        assert reverse_diff.operation == DiffType.DELETE_NODE
        assert reverse_diff.node == node
        assert reverse_diff.id != insert_diff.id  # New diff ID
        assert reverse_diff.timestamp > insert_diff.timestamp

    def test_all_diff_reversals(self):
        """Test all diff operation reversals."""
        test_cases = [
            (DiffType.INSERT_NODE, DiffType.DELETE_NODE),
            (DiffType.DELETE_NODE, DiffType.INSERT_NODE),
            (DiffType.INSERT_EDGE, DiffType.DELETE_EDGE),
            (DiffType.DELETE_EDGE, DiffType.INSERT_EDGE),
        ]

        for original, expected_reverse in test_cases:
            diff = Diff(operation=original)
            reverse_diff = diff.reverse()
            assert reverse_diff.operation == expected_reverse


class TestQueryResult:
    """Test query result model."""

    def test_empty_query_result(self):
        """Test creating empty query result."""
        result = QueryResult()

        assert result.nodes == []
        assert result.edges == []
        assert result.metadata == {}
        assert result.query_time_ms == 0.0
        assert result.storage_tier == "runtime"

    def test_query_result_with_data(self):
        """Test query result with nodes and edges."""
        node = Node(label="Person")
        edge = Edge(source_id="a", target_id="b", relationship="knows")

        result = QueryResult(
            nodes=[node], edges=[edge], query_time_ms=1.5, storage_tier="store"
        )

        assert len(result.nodes) == 1
        assert len(result.edges) == 1
        assert result.query_time_ms == 1.5
        assert result.storage_tier == "store"
