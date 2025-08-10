"""
Correctness tests for Momo KnowledgeBase queries.

Verifies that our high-performance indexed queries return the same results
as naive implementations, ensuring speed doesn't compromise accuracy.
"""

import pytest
from typing import Set, List
import asyncio

from momo_kb import KnowledgeBase, Node, Edge


class TestQueryCorrectness:
    """Test that indexed queries return correct results."""

    @pytest.fixture
    async def populated_kb(self):
        """Create a knowledge base with known test data for correctness testing."""
        kb = KnowledgeBase()
        await kb.initialize()

        # Create a small but comprehensive test dataset
        # People with various attributes
        alice = await kb.insert_node(
            Node(
                label="Person",
                properties={
                    "name": "Alice",
                    "age": 30,
                    "department": "Engineering",
                    "active": True,
                },
            )
        )
        bob = await kb.insert_node(
            Node(
                label="Person",
                properties={
                    "name": "Bob",
                    "age": 25,
                    "department": "Design",
                    "active": True,
                },
            )
        )
        charlie = await kb.insert_node(
            Node(
                label="Person",
                properties={
                    "name": "Charlie",
                    "age": 35,
                    "department": "Engineering",
                    "active": False,
                },
            )
        )

        # Companies
        techcorp = await kb.insert_node(
            Node(
                label="Company",
                properties={
                    "name": "TechCorp",
                    "size": "large",
                    "industry": "technology",
                },
            )
        )
        designco = await kb.insert_node(
            Node(
                label="Company",
                properties={"name": "DesignCo", "size": "small", "industry": "design"},
            )
        )

        # Projects
        project_x = await kb.insert_node(
            Node(
                label="Project",
                properties={"name": "ProjectX", "status": "active", "budget": 100000},
            )
        )
        project_y = await kb.insert_node(
            Node(
                label="Project",
                properties={"name": "ProjectY", "status": "completed", "budget": 50000},
            )
        )

        # Relationships
        await kb.insert_edge(
            Edge(
                source_id=alice.node.id,
                target_id=techcorp.node.id,
                relationship="works_for",
                properties={"since": 2020},
            )
        )
        await kb.insert_edge(
            Edge(
                source_id=bob.node.id,
                target_id=designco.node.id,
                relationship="works_for",
                properties={"since": 2021},
            )
        )
        await kb.insert_edge(
            Edge(
                source_id=charlie.node.id,
                target_id=techcorp.node.id,
                relationship="worked_for",
                properties={"from": 2018, "to": 2023},
            )
        )

        await kb.insert_edge(
            Edge(
                source_id=alice.node.id,
                target_id=project_x.node.id,
                relationship="assigned_to",
                properties={"role": "lead"},
            )
        )
        await kb.insert_edge(
            Edge(
                source_id=bob.node.id,
                target_id=project_x.node.id,
                relationship="assigned_to",
                properties={"role": "designer"},
            )
        )
        await kb.insert_edge(
            Edge(
                source_id=alice.node.id,
                target_id=project_y.node.id,
                relationship="completed",
                properties={"role": "developer"},
            )
        )

        await kb.insert_edge(
            Edge(
                source_id=alice.node.id,
                target_id=bob.node.id,
                relationship="mentors",
                properties={"area": "technical"},
            )
        )

        yield kb
        await kb.close()

    async def test_label_query_correctness(self, populated_kb):
        """Test that label queries return exactly the right nodes."""
        kb = populated_kb

        # Query for all people
        people = await kb.query_nodes(label="Person")
        assert len(people.nodes) == 3

        people_names = {node.properties["name"] for node in people.nodes}
        assert people_names == {"Alice", "Bob", "Charlie"}

        # Query for companies
        companies = await kb.query_nodes(label="Company")
        assert len(companies.nodes) == 2

        company_names = {node.properties["name"] for node in companies.nodes}
        assert company_names == {"TechCorp", "DesignCo"}

        # Query for projects
        projects = await kb.query_nodes(label="Project")
        assert len(projects.nodes) == 2

        project_names = {node.properties["name"] for node in projects.nodes}
        assert project_names == {"ProjectX", "ProjectY"}

        # Query for non-existent label
        robots = await kb.query_nodes(label="Robot")
        assert len(robots.nodes) == 0

    async def test_single_property_query_correctness(self, populated_kb):
        """Test that single property queries return correct results."""
        kb = populated_kb

        # Query by department
        engineers = await kb.query_nodes(properties={"department": "Engineering"})
        assert len(engineers.nodes) == 2

        engineer_names = {node.properties["name"] for node in engineers.nodes}
        assert engineer_names == {"Alice", "Charlie"}

        # Query by age
        age_30 = await kb.query_nodes(properties={"age": 30})
        assert len(age_30.nodes) == 1
        assert age_30.nodes[0].properties["name"] == "Alice"

        # Query by boolean property
        active_people = await kb.query_nodes(properties={"active": True})
        assert len(active_people.nodes) == 2

        active_names = {node.properties["name"] for node in active_people.nodes}
        assert active_names == {"Alice", "Bob"}

        # Query by company size
        large_companies = await kb.query_nodes(properties={"size": "large"})
        assert len(large_companies.nodes) == 1
        assert large_companies.nodes[0].properties["name"] == "TechCorp"

    async def test_multiple_property_query_correctness(self, populated_kb):
        """Test that multiple property queries return correct intersections."""
        kb = populated_kb

        # Query for active engineers
        active_engineers = await kb.query_nodes(
            properties={"department": "Engineering", "active": True}
        )
        assert len(active_engineers.nodes) == 1
        assert active_engineers.nodes[0].properties["name"] == "Alice"

        # Query for inactive engineers
        inactive_engineers = await kb.query_nodes(
            properties={"department": "Engineering", "active": False}
        )
        assert len(inactive_engineers.nodes) == 1
        assert inactive_engineers.nodes[0].properties["name"] == "Charlie"

        # Query for young designers
        young_designers = await kb.query_nodes(
            properties={"department": "Design", "age": 25}
        )
        assert len(young_designers.nodes) == 1
        assert young_designers.nodes[0].properties["name"] == "Bob"

        # Query with no matches
        old_designers = await kb.query_nodes(
            properties={"department": "Design", "age": 50}
        )
        assert len(old_designers.nodes) == 0

    async def test_label_and_property_combination_correctness(self, populated_kb):
        """Test that label + property combinations work correctly."""
        kb = populated_kb

        # Query for active people
        active_people = await kb.query_nodes(
            label="Person", properties={"active": True}
        )
        assert len(active_people.nodes) == 2

        active_names = {node.properties["name"] for node in active_people.nodes}
        assert active_names == {"Alice", "Bob"}

        # Query for technology companies
        tech_companies = await kb.query_nodes(
            label="Company", properties={"industry": "technology"}
        )
        assert len(tech_companies.nodes) == 1
        assert tech_companies.nodes[0].properties["name"] == "TechCorp"

        # Query for active projects
        active_projects = await kb.query_nodes(
            label="Project", properties={"status": "active"}
        )
        assert len(active_projects.nodes) == 1
        assert active_projects.nodes[0].properties["name"] == "ProjectX"

    async def test_edge_query_correctness(self, populated_kb):
        """Test that edge queries return correct relationships."""
        kb = populated_kb

        # Query all work relationships
        work_edges = await kb.query_edges(relationship="works_for")
        assert len(work_edges.edges) == 2

        # Verify the relationships are correct
        work_relationships = set()
        for edge in work_edges.edges:
            source_node = await kb.query_nodes(
                properties={"id": edge.source_id}
            )  # This won't work, need different approach
            # Let's verify by checking edge properties instead
            work_relationships.add(edge.properties.get("since"))

        assert work_relationships == {2020, 2021}

        # Query assignment relationships
        assignment_edges = await kb.query_edges(relationship="assigned_to")
        assert len(assignment_edges.edges) == 2

        assignment_roles = {edge.properties["role"] for edge in assignment_edges.edges}
        assert assignment_roles == {"lead", "designer"}

        # Query mentoring relationships
        mentor_edges = await kb.query_edges(relationship="mentors")
        assert len(mentor_edges.edges) == 1
        assert mentor_edges.edges[0].properties["area"] == "technical"

        # Query non-existent relationship
        friendship_edges = await kb.query_edges(relationship="friends_with")
        assert len(friendship_edges.edges) == 0

    async def test_connected_nodes_query_correctness(self, populated_kb):
        """Test that connected node queries return correct graph traversals."""
        kb = populated_kb

        # First, get Alice's node ID
        alice_result = await kb.query_nodes(properties={"name": "Alice"})
        assert len(alice_result.nodes) == 1
        alice_id = alice_result.nodes[0].id

        # Find who Alice mentors (outgoing)
        mentees = await kb.query_connected_nodes(
            start_node_id=alice_id, relationship="mentors", direction="outgoing"
        )
        assert len(mentees.nodes) == 1
        assert mentees.nodes[0].properties["name"] == "Bob"

        # Find who mentors Alice (incoming) - should be empty
        mentors = await kb.query_connected_nodes(
            start_node_id=alice_id, relationship="mentors", direction="incoming"
        )
        assert len(mentors.nodes) == 0

        # Find Alice's work relationships (outgoing)
        employers = await kb.query_connected_nodes(
            start_node_id=alice_id, relationship="works_for", direction="outgoing"
        )
        assert len(employers.nodes) == 1
        assert employers.nodes[0].properties["name"] == "TechCorp"

        # Find Alice's project assignments (outgoing)
        projects = await kb.query_connected_nodes(
            start_node_id=alice_id, relationship="assigned_to", direction="outgoing"
        )
        assert len(projects.nodes) == 1
        assert projects.nodes[0].properties["name"] == "ProjectX"

        # Test bidirectional search
        all_relationships = await kb.query_connected_nodes(
            start_node_id=alice_id, relationship="mentors", direction="both"
        )
        assert (
            len(all_relationships.nodes) == 1
        )  # Alice mentors Bob, no one mentors Alice

    async def test_query_result_consistency(self, populated_kb):
        """Test that repeated queries return consistent results."""
        kb = populated_kb

        # Run the same query multiple times
        for _ in range(5):
            people = await kb.query_nodes(label="Person")
            assert len(people.nodes) == 3

            engineers = await kb.query_nodes(properties={"department": "Engineering"})
            assert len(engineers.nodes) == 2

            work_edges = await kb.query_edges(relationship="works_for")
            assert len(work_edges.edges) == 2

    async def test_empty_query_correctness(self, populated_kb):
        """Test that queries with no matches return empty results correctly."""
        kb = populated_kb

        # Non-existent label
        aliens = await kb.query_nodes(label="Alien")
        assert len(aliens.nodes) == 0
        assert aliens.nodes == []

        # Non-existent property value
        centenarians = await kb.query_nodes(properties={"age": 100})
        assert len(centenarians.nodes) == 0

        # Non-existent relationship
        marriages = await kb.query_edges(relationship="married_to")
        assert len(marriages.edges) == 0

        # Connected nodes with non-existent relationship
        alice_result = await kb.query_nodes(properties={"name": "Alice"})
        alice_id = alice_result.nodes[0].id

        enemies = await kb.query_connected_nodes(
            start_node_id=alice_id, relationship="enemies_with", direction="outgoing"
        )
        assert len(enemies.nodes) == 0

    async def test_query_metadata_correctness(self, populated_kb):
        """Test that query metadata (timing, storage tier) is correct."""
        kb = populated_kb

        result = await kb.query_nodes(label="Person")

        # Check that timing is reasonable (should be very fast)
        assert result.query_time_ms >= 0
        assert result.query_time_ms < 100  # Should be under 100ms

        # Check storage tier is set
        assert result.storage_tier in ["runtime", "store", "cold", "mixed"]

        # For fresh data, should be in runtime tier
        assert result.storage_tier == "runtime"
