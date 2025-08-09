"""Unit tests for GraphStore main interface."""

import pytest
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.documents import Document

from momo_graph_store import GraphStore


class TestGraphStore:
    """Test cases for GraphStore class."""

    @pytest.fixture
    def sample_nodes(self):
        """Sample nodes for testing."""
        return [
            Node(id="1", type="Person", properties={"name": "Alice"}),
            Node(id="2", type="Person", properties={"name": "Bob"}),
            Node(id="3", type="Company", properties={"name": "TechCorp"}),
        ]

    @pytest.fixture
    def sample_relationships(self, sample_nodes):
        """Sample relationships for testing."""
        return [
            Relationship(
                source=sample_nodes[0],
                target=sample_nodes[1],
                type="KNOWS",
                properties={"since": "2020"},
            ),
            Relationship(
                source=sample_nodes[0],
                target=sample_nodes[2],
                type="WORKS_AT",
                properties={"role": "Engineer"},
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

    def test_init_default(self):
        """Test GraphStore initialization with defaults."""
        store = GraphStore()
        assert store.backend_type == "memory"
        assert store.backend is not None

    def test_init_custom_backend(self):
        """Test GraphStore initialization with custom backend."""
        store = GraphStore(backend_type="memory")
        assert store.backend_type == "memory"

    @pytest.mark.asyncio
    async def test_add_graph_documents(self, sample_graph_doc):
        """Test adding graph documents."""
        store = GraphStore()

        # Should not raise an exception
        await store.add_graph_documents([sample_graph_doc])

    @pytest.mark.asyncio
    async def test_query_all_nodes(self, sample_graph_doc):
        """Test querying all nodes."""
        store = GraphStore()
        await store.add_graph_documents([sample_graph_doc])

        results = await store.query("MATCH (n) RETURN n")

        assert len(results) == 3  # 3 nodes
        assert all("n" in result for result in results)

    @pytest.mark.asyncio
    async def test_query_nodes_by_type(self, sample_graph_doc):
        """Test querying nodes by type."""
        store = GraphStore()
        await store.add_graph_documents([sample_graph_doc])

        results = await store.query("MATCH (n:Person) RETURN n")

        assert len(results) == 2  # 2 Person nodes
        for result in results:
            assert result["n"]["type"] == "Person"

    @pytest.mark.asyncio
    async def test_query_relationships(self, sample_graph_doc):
        """Test querying relationships."""
        store = GraphStore()
        await store.add_graph_documents([sample_graph_doc])

        results = await store.query("MATCH (n)-[r]->(m) RETURN n,r,m")

        assert len(results) == 2  # 2 relationships
        for result in results:
            assert "n" in result and "r" in result and "m" in result

    def test_get_schema(self, sample_graph_doc):
        """Test getting schema as string."""
        store = GraphStore()
        # Empty schema initially
        schema = store.get_schema
        assert "Empty graph" in schema

    def test_get_structured_schema(self):
        """Test getting structured schema."""
        store = GraphStore()
        schema = store.get_structured_schema

        assert "nodes" in schema
        assert "relationships" in schema
        assert schema["nodes"]["total"] == 0
        assert schema["relationships"]["total"] == 0

    @pytest.mark.asyncio
    async def test_refresh_schema(self):
        """Test refreshing schema."""
        store = GraphStore()
        # Should not raise an exception
        await store.refresh_schema()

    def test_get_info(self):
        """Test getting store information."""
        store = GraphStore()
        info = store.get_info()

        assert "backend" in info
        assert "schema" in info
        assert "default_backend" in info
        assert info["default_backend"] == "memory"

    def test_graph_backend_property(self):
        """Test accessing graph backend."""
        store = GraphStore()
        backend = store.graph_backend
        assert backend is not None

    def test_repr(self):
        """Test string representation."""
        store = GraphStore()
        repr_str = repr(store)
        assert "GraphStore" in repr_str
        assert "memory" in repr_str

    @pytest.mark.asyncio
    async def test_acreate(self):
        """Test async factory method."""
        store = await GraphStore.acreate()
        assert store.backend_type == "memory"
        assert store.backend is not None
