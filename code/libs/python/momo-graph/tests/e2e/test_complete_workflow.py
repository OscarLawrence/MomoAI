"""
End-to-end tests for complete GraphBackend workflows.

Tests realistic usage patterns and integration scenarios.
"""

import pytest
from datetime import datetime

from momo_graph import GraphBackend, GraphNode, GraphEdge


class TestCompleteWorkflow:
    """Test complete graph backend workflows."""

    @pytest.fixture
    async def graph(self):
        """Create a fresh graph backend for testing."""
        async with GraphBackend() as graph:
            yield graph

    @pytest.mark.asyncio
    async def test_social_network_workflow(self, graph):
        """Test a realistic social network scenario."""
        # Create users
        alice = GraphNode(
            label="User",
            properties={
                "name": "Alice Smith",
                "email": "alice@example.com",
                "joined": "2020-01-15",
            },
        )
        bob = GraphNode(
            label="User",
            properties={
                "name": "Bob Jones",
                "email": "bob@example.com",
                "joined": "2020-02-10",
            },
        )
        charlie = GraphNode(
            label="User",
            properties={
                "name": "Charlie Brown",
                "email": "charlie@example.com",
                "joined": "2020-03-05",
            },
        )

        # Insert users
        await graph.insert_node(alice)
        await graph.insert_node(bob)
        await graph.insert_node(charlie)

        # Create friendships
        friendship1 = GraphEdge(
            source_id=alice.id,
            target_id=bob.id,
            relationship="FRIEND",
            properties={"since": "2020-02-15", "strength": 0.8},
        )
        friendship2 = GraphEdge(
            source_id=bob.id,
            target_id=charlie.id,
            relationship="FRIEND",
            properties={"since": "2020-03-10", "strength": 0.6},
        )

        await graph.insert_edge(friendship1)
        await graph.insert_edge(friendship2)

        # Query: Find all users
        users = await graph.query_nodes(label="User")
        assert len(users.nodes) == 3
        assert all(node.label == "User" for node in users.nodes)

        # Query: Find Alice's friends
        alice_friends = await graph.query_connected_nodes(
            alice.id, "FRIEND", direction="outgoing"
        )
        assert len(alice_friends.nodes) == 1
        assert alice_friends.nodes[0].properties["name"] == "Bob Jones"

        # Query: Find who is friends with Bob (incoming connections)
        bob_friends = await graph.query_connected_nodes(
            bob.id, "FRIEND", direction="incoming"
        )
        assert len(bob_friends.nodes) == 1
        assert bob_friends.nodes[0].properties["name"] == "Alice Smith"

        # Query: Find all friendships
        friendships = await graph.query_edges(relationship="FRIEND")
        assert len(friendships.edges) == 2

        # Test rollback: Remove last friendship and rollback
        await graph.delete_edge(friendship2.id)
        assert len((await graph.query_edges(relationship="FRIEND")).edges) == 1

        # Rollback the deletion
        await graph.rollback(steps=1)
        friendships_after_rollback = await graph.query_edges(relationship="FRIEND")
        assert len(friendships_after_rollback.edges) == 2

    @pytest.mark.asyncio
    async def test_knowledge_graph_workflow(self, graph):
        """Test a knowledge graph scenario with concepts and relationships."""
        # Create concepts
        ai = GraphNode(
            label="Concept",
            properties={
                "name": "Artificial Intelligence",
                "description": "Machine intelligence",
                "category": "Technology",
            },
        )
        ml = GraphNode(
            label="Concept",
            properties={
                "name": "Machine Learning",
                "description": "Learning from data",
                "category": "Technology",
            },
        )
        python = GraphNode(
            label="Technology",
            properties={
                "name": "Python",
                "type": "Programming Language",
                "created": "1991",
            },
        )

        await graph.insert_node(ai)
        await graph.insert_node(ml)
        await graph.insert_node(python)

        # Create relationships
        is_subset = GraphEdge(
            source_id=ml.id,
            target_id=ai.id,
            relationship="IS_SUBSET_OF",
            properties={"confidence": 0.95},
        )
        implemented_in = GraphEdge(
            source_id=ml.id,
            target_id=python.id,
            relationship="IMPLEMENTED_IN",
            properties={"frequency": "often"},
        )

        await graph.insert_edge(is_subset)
        await graph.insert_edge(implemented_in)

        # Test complex queries

        # Find all technology concepts
        tech_concepts = await graph.query_nodes(
            label="Concept", properties={"category": "Technology"}
        )
        assert len(tech_concepts.nodes) == 2

        # Find what ML is a subset of
        ml_parents = await graph.query_connected_nodes(
            ml.id, "IS_SUBSET_OF", direction="outgoing"
        )
        assert len(ml_parents.nodes) == 1
        assert ml_parents.nodes[0].properties["name"] == "Artificial Intelligence"

        # Find what can be implemented in Python
        python_implementations = await graph.query_connected_nodes(
            python.id, "IMPLEMENTED_IN", direction="incoming"
        )
        assert len(python_implementations.nodes) == 1
        assert python_implementations.nodes[0].properties["name"] == "Machine Learning"

    @pytest.mark.asyncio
    async def test_performance_with_moderate_dataset(self, graph):
        """Test performance characteristics with moderate data."""
        import time

        # Create 100 nodes
        nodes = []
        start_time = time.time()

        for i in range(100):
            node = GraphNode(
                label="TestNode", properties={"id": i, "category": f"cat_{i % 10}"}
            )
            nodes.append(node)
            await graph.insert_node(node)

        insert_time = time.time() - start_time

        # Create 200 edges (2 per node on average)
        start_time = time.time()

        for i in range(200):
            source_idx = i % 100
            target_idx = (i + 1) % 100
            edge = GraphEdge(
                source_id=nodes[source_idx].id,
                target_id=nodes[target_idx].id,
                relationship="CONNECTED",
                properties={"weight": i * 0.01},
            )
            await graph.insert_edge(edge)

        edge_insert_time = time.time() - start_time

        # Test query performance
        start_time = time.time()

        # Query by label (should be fast with indexing)
        result = await graph.query_nodes(label="TestNode")
        assert len(result.nodes) == 100

        label_query_time = time.time() - start_time

        # Query by property (should be fast with indexing)
        start_time = time.time()

        result = await graph.query_nodes(properties={"category": "cat_5"})
        assert len(result.nodes) == 10  # Every 10th node

        property_query_time = time.time() - start_time

        # Verify performance is reasonable (these are loose bounds)
        assert insert_time < 1.0  # Should insert 100 nodes in under 1 second
        assert edge_insert_time < 2.0  # Should insert 200 edges in under 2 seconds
        assert label_query_time < 0.1  # Should query by label in under 100ms
        assert property_query_time < 0.1  # Should query by property in under 100ms

        # Verify query timing is recorded
        assert result.query_time_ms > 0

    @pytest.mark.asyncio
    async def test_export_import_workflow(self, graph):
        """Test exporting and analyzing graph data."""
        # Create some test data
        node1 = GraphNode(label="Person", properties={"name": "Alice"})
        node2 = GraphNode(label="Person", properties={"name": "Bob"})
        edge = GraphEdge(source_id=node1.id, target_id=node2.id, relationship="KNOWS")

        await graph.insert_node(node1)
        await graph.insert_node(node2)
        await graph.insert_edge(edge)

        # Export to JSON
        export_data = await graph.export_json()

        # Verify export structure and content
        assert len(export_data["nodes"]) == 2
        assert len(export_data["edges"]) == 1
        assert len(export_data["diffs"]) == 3  # 2 node inserts + 1 edge insert

        # Verify metadata
        metadata = export_data["metadata"]
        assert metadata["total_nodes"] == 2
        assert metadata["total_edges"] == 1
        assert metadata["total_diffs"] == 3
        assert "export_timestamp" in metadata

        # Verify node data integrity
        exported_nodes = export_data["nodes"]
        node_names = {node["properties"]["name"] for node in exported_nodes}
        assert node_names == {"Alice", "Bob"}

        # Verify edge data integrity
        exported_edges = export_data["edges"]
        assert exported_edges[0]["relationship"] == "KNOWS"
        assert exported_edges[0]["source_id"] == node1.id
        assert exported_edges[0]["target_id"] == node2.id
