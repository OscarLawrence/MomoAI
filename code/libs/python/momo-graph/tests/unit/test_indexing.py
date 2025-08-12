"""Unit tests for GraphIndexManager."""

import pytest

from momo_graph.models import GraphNode, GraphEdge
from momo_graph.indexing import GraphIndexManager


class TestGraphIndexManager:
    """Test cases for GraphIndexManager class."""

    @pytest.fixture
    def index_manager(self):
        """Create a fresh index manager for each test."""
        return GraphIndexManager()

    @pytest.fixture
    def sample_nodes(self):
        """Sample nodes for testing."""
        return [
            GraphNode(id="node1", label="Person", properties={"name": "Alice", "age": 30}),
            GraphNode(id="node2", label="Person", properties={"name": "Bob", "age": 25}),
            GraphNode(id="node3", label="Company", properties={"name": "TechCorp", "founded": 2010}),
            GraphNode(id="node4", label="Person", properties={"name": "Charlie", "age": 35}),
        ]

    @pytest.fixture
    def sample_edges(self):
        """Sample edges for testing."""
        return [
            GraphEdge(
                id="edge1",
                source_id="node1",
                target_id="node2", 
                relationship="KNOWS",
                properties={"since": "2020", "strength": "strong"}
            ),
            GraphEdge(
                id="edge2",
                source_id="node1",
                target_id="node3",
                relationship="WORKS_AT",
                properties={"role": "Engineer", "start_date": "2021"}
            ),
            GraphEdge(
                id="edge3",
                source_id="node2",
                target_id="node3",
                relationship="WORKS_AT",
                properties={"role": "Manager", "start_date": "2022"}
            ),
        ]

    def test_index_manager_initialization(self, index_manager):
        """Test index manager is properly initialized."""
        assert isinstance(index_manager, GraphIndexManager)

    def test_add_node_to_index(self, index_manager, sample_nodes):
        """Test adding nodes to indexes."""
        node = sample_nodes[0]
        
        # Add node to index
        index_manager.add_node(node)
        
        # Should be able to query by label
        person_nodes = index_manager.query_nodes_by_label("Person")
        assert len(person_nodes) == 1
        assert person_nodes[0].id == node.id

    def test_add_edge_to_index(self, index_manager, sample_edges):
        """Test adding edges to indexes."""
        edge = sample_edges[0]
        
        # Add edge to index
        index_manager.add_edge(edge)
        
        # Should be able to query by relationship
        knows_edges = index_manager.query_edges_by_relationship("KNOWS")
        assert len(knows_edges) == 1
        assert knows_edges[0].id == edge.id

    def test_remove_node_from_index(self, index_manager, sample_nodes):
        """Test removing nodes from indexes."""
        node = sample_nodes[0]
        
        # Add and then remove node
        index_manager.add_node(node)
        index_manager.remove_node(node.id)
        
        # Should not be found in queries
        person_nodes = index_manager.query_nodes_by_label("Person")
        assert len(person_nodes) == 0

    def test_remove_edge_from_index(self, index_manager, sample_edges):
        """Test removing edges from indexes."""
        edge = sample_edges[0]
        
        # Add and then remove edge
        index_manager.add_edge(edge)
        index_manager.remove_edge(edge.id)
        
        # Should not be found in queries
        knows_edges = index_manager.query_edges_by_relationship("KNOWS")
        assert len(knows_edges) == 0

    def test_query_nodes_by_label(self, index_manager, sample_nodes):
        """Test querying nodes by label."""
        # Add multiple nodes with different labels
        for node in sample_nodes:
            index_manager.add_node(node)
        
        # Query Person nodes
        person_nodes = index_manager.query_nodes_by_label("Person")
        assert len(person_nodes) == 3  # Alice, Bob, Charlie
        
        # Query Company nodes
        company_nodes = index_manager.query_nodes_by_label("Company")
        assert len(company_nodes) == 1  # TechCorp

    def test_query_nodes_by_properties(self, index_manager, sample_nodes):
        """Test querying nodes by properties."""
        # Add nodes with properties
        for node in sample_nodes:
            index_manager.add_node(node)
        
        # Query by single property
        alice_nodes = index_manager.query_nodes_by_properties({"name": "Alice"})
        assert len(alice_nodes) == 1
        assert alice_nodes[0].id == "node1"
        
        # Query by multiple properties
        young_bobs = index_manager.query_nodes_by_properties({"name": "Bob", "age": 25})
        assert len(young_bobs) == 1
        assert young_bobs[0].id == "node2"

    def test_query_edges_by_relationship(self, index_manager, sample_edges):
        """Test querying edges by relationship."""
        # Add edges with different relationships
        for edge in sample_edges:
            index_manager.add_edge(edge)
        
        # Query KNOWS relationships
        knows_edges = index_manager.query_edges_by_relationship("KNOWS")
        assert len(knows_edges) == 1
        assert knows_edges[0].id == "edge1"
        
        # Query WORKS_AT relationships
        works_edges = index_manager.query_edges_by_relationship("WORKS_AT")
        assert len(works_edges) == 2  # edge2 and edge3

    def test_query_edges_by_source(self, index_manager, sample_edges):
        """Test querying edges by source node."""
        # Add edges
        for edge in sample_edges:
            index_manager.add_edge(edge)
        
        # Query edges from node1 (Alice)
        alice_edges = index_manager.query_edges_by_source("node1")
        assert len(alice_edges) == 2  # edge1 and edge2
        
        # Query edges from node2 (Bob)
        bob_edges = index_manager.query_edges_by_source("node2")
        assert len(bob_edges) == 1  # edge3

    def test_query_edges_by_target(self, index_manager, sample_edges):
        """Test querying edges by target node."""
        # Add edges
        for edge in sample_edges:
            index_manager.add_edge(edge)
        
        # Query edges to node3 (TechCorp)
        techcorp_edges = index_manager.query_edges_by_target("node3")
        assert len(techcorp_edges) == 2  # edge2 and edge3
        
        # Query edges to node2 (Bob)
        bob_edges = index_manager.query_edges_by_target("node2")
        assert len(bob_edges) == 1  # edge1

    def test_query_edges_by_properties(self, index_manager, sample_edges):
        """Test querying edges by properties."""
        # Add edges with properties
        for edge in sample_edges:
            index_manager.add_edge(edge)
        
        # Query by single property
        strong_edges = index_manager.query_edges_by_properties({"strength": "strong"})
        assert len(strong_edges) == 1
        assert strong_edges[0].id == "edge1"
        
        # Query by role property
        engineer_edges = index_manager.query_edges_by_properties({"role": "Engineer"})
        assert len(engineer_edges) == 1
        assert engineer_edges[0].id == "edge2"

    def test_find_connected_nodes(self, index_manager, sample_nodes, sample_edges):
        """Test finding connected nodes."""
        # Add nodes and edges
        for node in sample_nodes:
            index_manager.add_node(node)
        for edge in sample_edges:
            index_manager.add_edge(edge)
        
        # Find outgoing connections from Alice
        outgoing = index_manager.find_connected_nodes("node1", "KNOWS", "outgoing")
        assert len(outgoing) == 1
        assert outgoing[0].id == "node2"  # Bob
        
        # Find incoming connections to TechCorp  
        incoming = index_manager.find_connected_nodes("node3", "WORKS_AT", "incoming")
        assert len(incoming) == 2  # Alice and Bob work at TechCorp

    def test_complex_query_combination(self, index_manager, sample_nodes, sample_edges):
        """Test complex queries combining multiple criteria."""
        # Add all data
        for node in sample_nodes:
            index_manager.add_node(node)
        for edge in sample_edges:
            index_manager.add_edge(edge)
        
        # Find all Person nodes older than 30
        older_persons = [
            node for node in index_manager.query_nodes_by_label("Person")
            if node.properties.get("age", 0) >= 30
        ]
        assert len(older_persons) == 2  # Alice (30) and Charlie (35)

    def test_index_performance_simulation(self, index_manager):
        """Test index performance with larger dataset."""
        # Create a larger dataset
        nodes = []
        edges = []
        
        # Create 100 nodes
        for i in range(100):
            node = GraphNode(
                id=f"node_{i}",
                label="Person" if i % 3 == 0 else "Company",
                properties={"index": i, "category": i % 5}
            )
            nodes.append(node)
            index_manager.add_node(node)
        
        # Create 200 edges
        for i in range(200):
            edge = GraphEdge(
                id=f"edge_{i}",
                source_id=f"node_{i % 50}",
                target_id=f"node_{(i + 1) % 50}",
                relationship="CONNECTS" if i % 2 == 0 else "RELATES",
                properties={"weight": i % 10}
            )
            edges.append(edge)
            index_manager.add_edge(edge)
        
        # Test queries on larger dataset
        person_nodes = index_manager.query_nodes_by_label("Person")
        assert len(person_nodes) > 30  # Should find many Person nodes
        
        connects_edges = index_manager.query_edges_by_relationship("CONNECTS")
        assert len(connects_edges) == 100  # Half of edges

    def test_update_node_in_index(self, index_manager, sample_nodes):
        """Test updating nodes in indexes."""
        node = sample_nodes[0]
        
        # Add original node
        index_manager.add_node(node)
        
        # Update node properties
        updated_node = GraphNode(
            id=node.id,
            label=node.label,
            properties={**node.properties, "updated": True, "age": 31}
        )
        
        # Remove old and add updated (simulating update)
        index_manager.remove_node(node.id)
        index_manager.add_node(updated_node)
        
        # Query should find updated version
        updated_nodes = index_manager.query_nodes_by_properties({"updated": True})
        assert len(updated_nodes) == 1
        assert updated_nodes[0].properties["age"] == 31

    def test_index_memory_efficiency(self, index_manager, sample_nodes):
        """Test index memory efficiency."""
        # Add nodes multiple times (simulating updates)
        node = sample_nodes[0]
        
        for i in range(10):
            # Remove if exists, then add
            index_manager.remove_node(node.id)
            index_manager.add_node(node)
        
        # Should only have one instance
        person_nodes = index_manager.query_nodes_by_label("Person")
        assert len(person_nodes) == 1

    def test_empty_query_results(self, index_manager):
        """Test queries on empty indexes."""
        # Query empty indexes
        assert len(index_manager.query_nodes_by_label("NonExistent")) == 0
        assert len(index_manager.query_edges_by_relationship("NoSuchRel")) == 0
        assert len(index_manager.query_nodes_by_properties({"key": "value"})) == 0

    def test_index_edge_cases(self, index_manager):
        """Test edge cases for indexing."""
        # Node with empty properties
        empty_node = GraphNode(id="empty", label="Empty", properties={})
        index_manager.add_node(empty_node)
        
        # Should still be queryable by label
        empty_nodes = index_manager.query_nodes_by_label("Empty")
        assert len(empty_nodes) == 1
        
        # Edge with minimal data
        minimal_edge = GraphEdge(
            id="minimal",
            source_id="source",
            target_id="target",
            relationship="MINIMAL",
            properties={}
        )
        index_manager.add_edge(minimal_edge)
        
        # Should still be queryable
        minimal_edges = index_manager.query_edges_by_relationship("MINIMAL")
        assert len(minimal_edges) == 1