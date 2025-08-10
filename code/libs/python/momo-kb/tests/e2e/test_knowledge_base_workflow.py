"""
End-to-end tests for complete knowledge base workflows.

Tests the full specs implementation including multi-tier storage,
diff-based rollback, and agent-optimized queries.
"""

import pytest
from datetime import datetime, timedelta

from momo_kb import KnowledgeBase, Node, Edge


class TestKnowledgeBaseWorkflow:
    """Test complete knowledge base workflows as specified."""

    @pytest.fixture
    async def kb(self):
        """Create a fresh knowledge base for testing."""
        kb = KnowledgeBase()
        await kb.initialize()
        yield kb
        await kb.close()

    async def test_basic_agent_workflow(self, kb):
        """Test basic agent workflow: add knowledge, query, rollback."""
        # Agent adds knowledge about people
        alice = await kb.insert_node(
            Node(label="Person", properties={"name": "Alice", "role": "engineer"})
        )
        bob = await kb.insert_node(
            Node(label="Person", properties={"name": "Bob", "role": "designer"})
        )

        # Agent creates relationships
        knows_edge = await kb.insert_edge(
            Edge(
                source_id=alice.node.id,
                target_id=bob.node.id,
                relationship="knows",
                properties={"since": "2023"},
            )
        )

        # Agent queries for engineers
        engineers = await kb.query_nodes(properties={"role": "engineer"})
        assert len(engineers.nodes) == 1
        assert engineers.nodes[0].properties["name"] == "Alice"

        # Agent queries for relationships
        relationships = await kb.query_edges(relationship="knows")
        assert len(relationships.edges) == 1

        # Agent realizes mistake and rolls back the relationship
        await kb.rollback(steps=1)

        # Relationship should be gone but people remain
        assert await kb.count_nodes() == 2
        assert await kb.count_edges() == 0

    async def test_multi_tier_storage_workflow(self, kb):
        """Test data moving through storage tiers based on usage."""
        # Create nodes with different access patterns
        hot_nodes = []
        cold_nodes = []

        # Add hot data (frequently accessed)
        for i in range(3):
            node = await kb.insert_node(Node(label="HotData", properties={"id": i}))
            hot_nodes.append(node.node)

        # Add cold data (rarely accessed)
        for i in range(5):
            node = await kb.insert_node(Node(label="ColdData", properties={"id": i}))
            cold_nodes.append(node.node)

        # Simulate hot data access
        for node in hot_nodes:
            await kb.query_nodes(properties={"id": node.properties["id"]})
            await kb.query_nodes(properties={"id": node.properties["id"]})

        # Trigger pruning to move cold data to store tier
        pruned = await kb.prune(runtime_limit=5)
        assert pruned > 0

        # Hot data should still be quickly accessible
        hot_result = await kb.query_nodes(label="HotData")
        assert len(hot_result.nodes) == 3
        assert hot_result.storage_tier in ["runtime", "store"]

        # Cold data should be accessible but from store tier
        cold_result = await kb.query_nodes(label="ColdData")
        assert len(cold_result.nodes) == 5

    async def test_versioning_and_audit_trail(self, kb):
        """Test complete versioning with audit trail."""
        # Record initial state
        initial_time = datetime.utcnow()

        # Agent 1 adds initial knowledge
        alice_diff = await kb.insert_node(
            Node(label="Person", properties={"name": "Alice"})
        )

        # Agent 2 adds more knowledge
        bob_diff = await kb.insert_node(
            Node(label="Person", properties={"name": "Bob"})
        )

        # Agent 1 creates relationship
        edge_diff = await kb.insert_edge(
            Edge(
                source_id=alice_diff.node.id,
                target_id=bob_diff.node.id,
                relationship="collaborates",
            )
        )

        # Check complete history
        history = await kb.get_diff_history()
        assert len(history) == 3
        assert all(diff.timestamp > initial_time for diff in history)

        # Rollback to after Alice was added
        await kb.rollback(steps=2)  # Remove edge and Bob

        # Should have Alice but not Bob or edge
        assert await kb.count_nodes() == 1
        assert await kb.count_edges() == 0

        remaining_nodes = await kb.query_nodes(label="Person")
        assert len(remaining_nodes.nodes) == 1
        assert remaining_nodes.nodes[0].properties["name"] == "Alice"

        # History should show rollback operations
        final_history = await kb.get_diff_history()
        assert len(final_history) > 3  # Original + rollback diffs

    async def test_complex_query_workflow(self, kb):
        """Test complex queries across relationships."""
        # Build a small knowledge graph
        # People
        alice = await kb.insert_node(
            Node(
                label="Person",
                properties={"name": "Alice", "department": "Engineering"},
            )
        )
        bob = await kb.insert_node(
            Node(label="Person", properties={"name": "Bob", "department": "Design"})
        )
        charlie = await kb.insert_node(
            Node(
                label="Person",
                properties={"name": "Charlie", "department": "Engineering"},
            )
        )

        # Projects
        project_x = await kb.insert_node(
            Node(label="Project", properties={"name": "ProjectX", "status": "active"})
        )

        # Relationships
        await kb.insert_edge(
            Edge(
                source_id=alice.node.id,
                target_id=project_x.node.id,
                relationship="works_on",
            )
        )
        await kb.insert_edge(
            Edge(
                source_id=bob.node.id,
                target_id=project_x.node.id,
                relationship="works_on",
            )
        )
        await kb.insert_edge(
            Edge(
                source_id=alice.node.id,
                target_id=charlie.node.id,
                relationship="mentors",
            )
        )

        # Query: Find all people working on ProjectX
        project_workers = await kb.query_connected_nodes(
            start_node_id=project_x.node.id,
            relationship="works_on",
            direction="incoming",
        )
        assert len(project_workers.nodes) == 2
        worker_names = {node.properties["name"] for node in project_workers.nodes}
        assert worker_names == {"Alice", "Bob"}

        # Query: Find all engineers
        engineers = await kb.query_nodes(properties={"department": "Engineering"})
        assert len(engineers.nodes) == 2

        # Query: Find who Alice mentors
        mentees = await kb.query_connected_nodes(
            start_node_id=alice.node.id, relationship="mentors", direction="outgoing"
        )
        assert len(mentees.nodes) == 1
        assert mentees.nodes[0].properties["name"] == "Charlie"

    async def test_performance_and_pruning(self, kb):
        """Test performance characteristics and pruning behavior."""
        # Add substantial amount of data
        nodes = []
        for i in range(100):
            node_diff = await kb.insert_node(
                Node(
                    label="TestNode",
                    properties={"index": i, "category": f"cat_{i % 10}"},
                )
            )
            nodes.append(node_diff.node)

        # Create some edges
        for i in range(0, 90, 10):
            await kb.insert_edge(
                Edge(
                    source_id=nodes[i].id,
                    target_id=nodes[i + 5].id,
                    relationship="connects",
                )
            )

        # Test query performance
        start_time = datetime.utcnow()
        result = await kb.query_nodes(properties={"category": "cat_5"})
        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        assert len(result.nodes) == 10  # Should find 10 nodes in cat_5
        assert query_time < 100  # Should be fast (< 100ms)
        assert result.query_time_ms > 0

        # Test aggressive pruning
        initial_runtime_count = await kb.count_nodes(tier="runtime")
        pruned = await kb.prune(runtime_limit=20, store_limit=50)

        assert pruned > 0
        final_runtime_count = await kb.count_nodes(tier="runtime")
        assert final_runtime_count <= 20

        # Data should still be queryable from store tier
        all_nodes = await kb.query_nodes(label="TestNode")
        assert len(all_nodes.nodes) == 100  # All data still accessible
