"""Unit tests for InMemoryGraphBackend."""

import pytest
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.documents import Document

from momo_graph_store.backends.memory import InMemoryGraphBackend
from momo_graph_store.exceptions import NodeNotFoundError, QueryError


class TestInMemoryGraphBackend:
    """Test cases for InMemoryGraphBackend."""

    @pytest.fixture
    def backend(self):
        """Create a fresh backend for each test."""
        return InMemoryGraphBackend()

    @pytest.fixture
    def sample_nodes(self):
        """Sample nodes for testing."""
        return [
            Node(id="alice", type="Person", properties={"name": "Alice", "age": 30}),
            Node(id="bob", type="Person", properties={"name": "Bob", "age": 25}),
            Node(
                id="techcorp",
                type="Company",
                properties={"name": "TechCorp", "founded": 2010},
            ),
        ]

    @pytest.fixture
    def sample_relationships(self, sample_nodes):
        """Sample relationships for testing."""
        return [
            Relationship(
                source=sample_nodes[0],  # alice
                target=sample_nodes[1],  # bob
                type="KNOWS",
                properties={"since": "2020"},
            ),
            Relationship(
                source=sample_nodes[0],  # alice
                target=sample_nodes[2],  # techcorp
                type="WORKS_AT",
                properties={"role": "Engineer", "salary": 100000},
            ),
        ]

    @pytest.fixture
    def sample_graph_doc(self, sample_nodes, sample_relationships):
        """Sample GraphDocument for testing."""
        return GraphDocument(
            nodes=sample_nodes,
            relationships=sample_relationships,
            source=Document(page_content="Test document", metadata={}),
        )

    def test_init(self, backend):
        """Test backend initialization."""
        assert backend.backend_name == "memory"
        assert len(backend.nodes) == 0
        assert len(backend.relationships) == 0
        assert len(backend.node_types) == 0
        assert len(backend.relationship_types) == 0

    @pytest.mark.asyncio
    async def test_add_graph_documents(self, backend, sample_graph_doc):
        """Test adding graph documents."""
        await backend.add_graph_documents([sample_graph_doc])

        # Check nodes were added
        assert len(backend.nodes) == 3
        assert "alice" in backend.nodes
        assert "bob" in backend.nodes
        assert "techcorp" in backend.nodes

        # Check relationships were added
        assert len(backend.relationships) == 2

        # Check types were tracked
        assert "Person" in backend.node_types
        assert "Company" in backend.node_types
        assert "KNOWS" in backend.relationship_types
        assert "WORKS_AT" in backend.relationship_types

    @pytest.mark.asyncio
    async def test_query_all_nodes(self, backend, sample_graph_doc):
        """Test querying all nodes."""
        await backend.add_graph_documents([sample_graph_doc])

        results = await backend.query("MATCH (n) RETURN n")

        assert len(results) == 3
        node_ids = {result["n"]["id"] for result in results}
        assert node_ids == {"alice", "bob", "techcorp"}

    @pytest.mark.asyncio
    async def test_query_nodes_by_type(self, backend, sample_graph_doc):
        """Test querying nodes by specific type."""
        await backend.add_graph_documents([sample_graph_doc])

        results = await backend.query("MATCH (n:Person) RETURN n")

        assert len(results) == 2
        for result in results:
            assert result["n"]["type"] == "Person"
            assert result["n"]["id"] in ["alice", "bob"]

    @pytest.mark.asyncio
    async def test_query_node_by_id(self, backend, sample_graph_doc):
        """Test querying specific node by ID."""
        await backend.add_graph_documents([sample_graph_doc])

        results = await backend.query("MATCH (n {id: 'alice'}) RETURN n")

        assert len(results) == 1
        assert results[0]["n"]["id"] == "alice"
        assert results[0]["n"]["properties"]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_query_relationships(self, backend, sample_graph_doc):
        """Test querying relationships."""
        await backend.add_graph_documents([sample_graph_doc])

        results = await backend.query("MATCH (n)-[r]->(m) RETURN n,r,m")

        assert len(results) == 2

        # Check relationship types
        rel_types = {result["r"]["type"] for result in results}
        assert rel_types == {"KNOWS", "WORKS_AT"}

    @pytest.mark.asyncio
    async def test_query_unsupported_pattern(self, backend):
        """Test unsupported query pattern raises error."""
        with pytest.raises(QueryError):
            await backend.query("INVALID QUERY PATTERN")

    def test_get_schema_empty(self, backend):
        """Test schema for empty graph."""
        schema = backend.get_schema()
        assert schema == "Empty graph"

    def test_get_schema_with_data(self, backend, sample_graph_doc):
        """Test schema with data."""
        # Need to add data synchronously for this test
        import asyncio

        asyncio.run(backend.add_graph_documents([sample_graph_doc]))

        schema = backend.get_schema()

        assert "Node types:" in schema
        assert "Person (2 nodes)" in schema
        assert "Company (1 nodes)" in schema
        assert "Relationship types:" in schema
        assert "KNOWS (1 relationships)" in schema
        assert "WORKS_AT (1 relationships)" in schema

    def test_get_structured_schema_empty(self, backend):
        """Test structured schema for empty graph."""
        schema = backend.get_structured_schema()

        assert schema["nodes"]["total"] == 0
        assert schema["relationships"]["total"] == 0
        assert len(schema["nodes"]["types"]) == 0
        assert len(schema["relationships"]["types"]) == 0

    def test_get_structured_schema_with_data(self, backend, sample_graph_doc):
        """Test structured schema with data."""
        import asyncio

        asyncio.run(backend.add_graph_documents([sample_graph_doc]))

        schema = backend.get_structured_schema()

        assert schema["nodes"]["total"] == 3
        assert schema["relationships"]["total"] == 2
        assert schema["nodes"]["counts"]["Person"] == 2
        assert schema["nodes"]["counts"]["Company"] == 1
        assert schema["relationships"]["counts"]["KNOWS"] == 1
        assert schema["relationships"]["counts"]["WORKS_AT"] == 1

    @pytest.mark.asyncio
    async def test_refresh_schema(self, backend):
        """Test schema refresh (no-op for memory backend)."""
        # Should not raise any exception
        await backend.refresh_schema()

    @pytest.mark.asyncio
    async def test_get_node(self, backend, sample_graph_doc):
        """Test getting specific node."""
        await backend.add_graph_documents([sample_graph_doc])

        node = await backend.get_node("alice")
        assert node.id == "alice"
        assert node.type == "Person"
        assert node.properties["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_get_node_not_found(self, backend):
        """Test getting non-existent node raises error."""
        with pytest.raises(NodeNotFoundError):
            await backend.get_node("nonexistent")

    @pytest.mark.asyncio
    async def test_get_relationships_outgoing(self, backend, sample_graph_doc):
        """Test getting outgoing relationships."""
        await backend.add_graph_documents([sample_graph_doc])

        rels = await backend.get_relationships("alice", "outgoing")
        assert len(rels) == 2

        targets = {rel.target.id for rel in rels}
        assert targets == {"bob", "techcorp"}

    @pytest.mark.asyncio
    async def test_get_relationships_incoming(self, backend, sample_graph_doc):
        """Test getting incoming relationships."""
        await backend.add_graph_documents([sample_graph_doc])

        rels = await backend.get_relationships("bob", "incoming")
        assert len(rels) == 1
        assert rels[0].source.id == "alice"
        assert rels[0].type == "KNOWS"

    @pytest.mark.asyncio
    async def test_traverse(self, backend, sample_graph_doc):
        """Test graph traversal."""
        await backend.add_graph_documents([sample_graph_doc])

        result = await backend.traverse("alice", max_depth=2)

        # Should include alice + connected nodes
        assert len(result) == 3

        node_ids = {item["node_id"] for item in result}
        assert node_ids == {"alice", "bob", "techcorp"}

        # Check depths
        alice_item = next(item for item in result if item["node_id"] == "alice")
        assert alice_item["depth"] == 0

    @pytest.mark.asyncio
    async def test_traverse_with_relationship_filter(self, backend, sample_graph_doc):
        """Test graph traversal with relationship type filter."""
        await backend.add_graph_documents([sample_graph_doc])

        result = await backend.traverse(
            "alice", max_depth=1, relationship_types=["KNOWS"]
        )

        # Should include alice + only KNOWS connections
        assert len(result) == 2
        node_ids = {item["node_id"] for item in result}
        assert node_ids == {"alice", "bob"}

    @pytest.mark.asyncio
    async def test_traverse_nonexistent_node(self, backend):
        """Test traversal from non-existent node raises error."""
        with pytest.raises(NodeNotFoundError):
            await backend.traverse("nonexistent")
