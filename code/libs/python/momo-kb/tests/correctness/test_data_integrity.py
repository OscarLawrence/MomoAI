"""
Data integrity and edge case tests for Momo KnowledgeBase.

Tests that our system maintains data integrity under various conditions
and handles edge cases correctly.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from momo_kb import KnowledgeBase, Node, Edge


class TestDataIntegrity:
    """Test data integrity and consistency."""

    @pytest.fixture
    async def kb(self):
        """Fresh knowledge base for each test."""
        kb = KnowledgeBase()
        await kb.initialize()
        yield kb
        await kb.close()

    async def test_node_uniqueness_and_identity(self, kb):
        """Test that nodes maintain unique identity."""
        # Create a node
        original = await kb.insert_node(
            Node(label="TestNode", properties={"name": "test", "value": 42})
        )

        # Query it back
        result = await kb.query_nodes(properties={"name": "test"})
        assert len(result.nodes) == 1

        found_node = result.nodes[0]

        # Verify identity
        assert found_node.id == original.node.id
        assert found_node.label == original.node.label
        assert found_node.properties == original.node.properties

        # Verify immutability - the found node should be the same object or equivalent
        assert found_node.created_at == original.node.created_at

    async def test_edge_referential_integrity(self, kb):
        """Test that edges maintain referential integrity."""
        # Create nodes
        node1 = await kb.insert_node(Node(label="Node1", properties={"id": 1}))
        node2 = await kb.insert_node(Node(label="Node2", properties={"id": 2}))

        # Create edge
        edge = await kb.insert_edge(
            Edge(
                source_id=node1.node.id,
                target_id=node2.node.id,
                relationship="connects",
            )
        )

        # Verify edge references correct nodes
        edges = await kb.query_edges(relationship="connects")
        assert len(edges.edges) == 1

        found_edge = edges.edges[0]
        assert found_edge.source_id == node1.node.id
        assert found_edge.target_id == node2.node.id

        # Verify connected nodes query works
        connected = await kb.query_connected_nodes(
            start_node_id=node1.node.id, relationship="connects", direction="outgoing"
        )
        assert len(connected.nodes) == 1
        assert connected.nodes[0].id == node2.node.id

    async def test_rollback_data_integrity(self, kb):
        """Test that rollback maintains data integrity."""
        # Create initial state
        node1 = await kb.insert_node(Node(label="Node1", properties={"value": 1}))
        node2 = await kb.insert_node(Node(label="Node2", properties={"value": 2}))
        edge1 = await kb.insert_edge(
            Edge(
                source_id=node1.node.id,
                target_id=node2.node.id,
                relationship="connects",
            )
        )

        # Verify initial state
        nodes = await kb.query_nodes(label="Node1")
        edges = await kb.query_edges(relationship="connects")
        assert len(nodes.nodes) == 1
        assert len(edges.edges) == 1

        # Add more data
        node3 = await kb.insert_node(Node(label="Node3", properties={"value": 3}))
        edge2 = await kb.insert_edge(
            Edge(
                source_id=node2.node.id,
                target_id=node3.node.id,
                relationship="connects",
            )
        )

        # Verify expanded state
        all_nodes = await kb.query_nodes()
        all_edges = await kb.query_edges()
        assert len(all_nodes.nodes) == 3
        assert len(all_edges.edges) == 2

        # Rollback the last 2 operations
        await kb.rollback(steps=2)

        # Verify rollback integrity
        final_nodes = await kb.query_nodes()
        final_edges = await kb.query_edges()
        assert len(final_nodes.nodes) == 2
        assert len(final_edges.edges) == 1

        # Verify the remaining data is correct
        remaining_node_values = {node.properties["value"] for node in final_nodes.nodes}
        assert remaining_node_values == {1, 2}

    async def test_concurrent_operations_integrity(self, kb):
        """Test data integrity under concurrent operations."""

        # Create concurrent node insertions
        async def insert_batch(start_id: int, count: int):
            for i in range(count):
                await kb.insert_node(
                    Node(
                        label="ConcurrentNode",
                        properties={"batch_id": start_id, "node_id": i},
                    )
                )

        # Run 3 concurrent batches
        await asyncio.gather(
            insert_batch(1, 10), insert_batch(2, 10), insert_batch(3, 10)
        )

        # Verify all nodes were inserted correctly
        all_nodes = await kb.query_nodes(label="ConcurrentNode")
        assert len(all_nodes.nodes) == 30

        # Verify each batch is complete
        for batch_id in [1, 2, 3]:
            batch_nodes = await kb.query_nodes(properties={"batch_id": batch_id})
            assert len(batch_nodes.nodes) == 10

            # Verify node IDs are correct
            node_ids = {node.properties["node_id"] for node in batch_nodes.nodes}
            assert node_ids == set(range(10))

    async def test_large_property_values(self, kb):
        """Test handling of large property values."""
        # Create node with large properties
        large_text = "x" * 10000  # 10KB string
        large_list = list(range(1000))  # Large list

        node = await kb.insert_node(
            Node(
                label="LargeNode",
                properties={
                    "large_text": large_text,
                    "large_number": 999999999999999,
                    "nested_data": {
                        "level1": {
                            "level2": {
                                "data": large_list[
                                    :100
                                ]  # Subset for JSON serialization
                            }
                        }
                    },
                },
            )
        )

        # Query it back
        result = await kb.query_nodes(label="LargeNode")
        assert len(result.nodes) == 1

        found_node = result.nodes[0]
        assert found_node.properties["large_text"] == large_text
        assert found_node.properties["large_number"] == 999999999999999
        assert (
            found_node.properties["nested_data"]["level1"]["level2"]["data"]
            == large_list[:100]
        )

    async def test_special_characters_and_unicode(self, kb):
        """Test handling of special characters and Unicode."""
        special_cases = [
            {"name": "emoji_test", "value": "🚀🎉🔥💯"},
            {"name": "unicode_test", "value": "こんにちは世界"},
            {"name": "special_chars", "value": "!@#$%^&*()[]{}|\\:;\"'<>?,."},
            {"name": "newlines", "value": "line1\nline2\r\nline3"},
            {"name": "tabs", "value": "col1\tcol2\tcol3"},
            {"name": "quotes", "value": "He said \"Hello 'world'\""},
        ]

        # Insert nodes with special characters
        for i, props in enumerate(special_cases):
            await kb.insert_node(Node(label="SpecialNode", properties=props))

        # Query them back
        for props in special_cases:
            result = await kb.query_nodes(properties={"name": props["name"]})
            assert len(result.nodes) == 1
            assert result.nodes[0].properties["value"] == props["value"]

    async def test_null_and_empty_values(self, kb):
        """Test handling of null and empty values."""
        # Test various empty/null cases
        test_cases = [
            {"empty_string": ""},
            {"zero": 0},
            {"false": False},
            {"empty_list": []},
            {"empty_dict": {}},
            # Note: None values are not allowed in our property system
        ]

        for i, props in enumerate(test_cases):
            node = await kb.insert_node(
                Node(label="EmptyValueNode", properties={**props, "test_id": i})
            )

            # Query back by test_id
            result = await kb.query_nodes(properties={"test_id": i})
            assert len(result.nodes) == 1

            found_props = result.nodes[0].properties
            for key, value in props.items():
                assert found_props[key] == value

    async def test_property_type_consistency(self, kb):
        """Test that property types are preserved correctly."""
        node = await kb.insert_node(
            Node(
                label="TypeTestNode",
                properties={
                    "string_prop": "hello",
                    "int_prop": 42,
                    "float_prop": 3.14159,
                    "bool_prop": True,
                    "list_prop": [1, 2, 3],
                    "dict_prop": {"key": "value"},
                },
            )
        )

        # Query back
        result = await kb.query_nodes(label="TypeTestNode")
        found_node = result.nodes[0]

        # Verify types are preserved
        assert isinstance(found_node.properties["string_prop"], str)
        assert isinstance(found_node.properties["int_prop"], int)
        assert isinstance(found_node.properties["float_prop"], float)
        assert isinstance(found_node.properties["bool_prop"], bool)
        assert isinstance(found_node.properties["list_prop"], list)
        assert isinstance(found_node.properties["dict_prop"], dict)

        # Verify values
        assert found_node.properties["string_prop"] == "hello"
        assert found_node.properties["int_prop"] == 42
        assert found_node.properties["float_prop"] == 3.14159
        assert found_node.properties["bool_prop"] is True
        assert found_node.properties["list_prop"] == [1, 2, 3]
        assert found_node.properties["dict_prop"] == {"key": "value"}

    async def test_query_edge_cases(self, kb):
        """Test edge cases in queries."""
        # Create test data
        await kb.insert_node(Node(label="Test", properties={"value": 1}))
        await kb.insert_node(Node(label="Test", properties={"value": 2}))

        # Test empty queries
        empty_label = await kb.query_nodes(label="NonExistent")
        assert len(empty_label.nodes) == 0

        empty_props = await kb.query_nodes(properties={"nonexistent": "value"})
        assert len(empty_props.nodes) == 0

        # Test queries with no filters (should return all)
        all_nodes = await kb.query_nodes()
        assert len(all_nodes.nodes) == 2

        # Test case sensitivity
        case_result = await kb.query_nodes(label="test")  # lowercase
        assert len(case_result.nodes) == 0  # Should be case sensitive

    async def test_storage_tier_consistency(self, kb):
        """Test that data remains consistent across storage tiers."""
        # Add enough data to trigger pruning
        nodes = []
        for i in range(100):
            node = await kb.insert_node(
                Node(
                    label="TierTestNode",
                    properties={"index": i, "category": f"cat_{i % 10}"},
                )
            )
            nodes.append(node.node)

        # Force pruning to move data between tiers
        await kb.prune(runtime_limit=20)

        # Verify all data is still accessible
        all_nodes = await kb.query_nodes(label="TierTestNode")
        assert len(all_nodes.nodes) == 100

        # Verify specific queries work across tiers
        cat_5_nodes = await kb.query_nodes(properties={"category": "cat_5"})
        assert len(cat_5_nodes.nodes) == 10

        # Verify specific node lookup
        node_50 = await kb.query_nodes(properties={"index": 50})
        assert len(node_50.nodes) == 1
        assert node_50.nodes[0].properties["index"] == 50
