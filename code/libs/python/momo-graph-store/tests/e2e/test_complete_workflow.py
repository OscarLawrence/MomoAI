"""End-to-end tests for complete GraphStore workflows."""

import pytest
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.documents import Document

from momo_graph_store import GraphStore


class TestCompleteWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def knowledge_graph_data(self):
        """Sample knowledge graph data for testing."""
        # Create nodes
        nodes = [
            Node(
                id="marie_curie",
                type="Person",
                properties={
                    "name": "Marie Curie",
                    "birth_year": 1867,
                    "nationality": "Polish-French",
                },
            ),
            Node(
                id="pierre_curie",
                type="Person",
                properties={
                    "name": "Pierre Curie",
                    "birth_year": 1859,
                    "nationality": "French",
                },
            ),
            Node(
                id="radium",
                type="Element",
                properties={"name": "Radium", "symbol": "Ra", "atomic_number": 88},
            ),
            Node(
                id="polonium",
                type="Element",
                properties={"name": "Polonium", "symbol": "Po", "atomic_number": 84},
            ),
            Node(
                id="nobel_physics_1903",
                type="Award",
                properties={
                    "name": "Nobel Prize in Physics",
                    "year": 1903,
                    "category": "Physics",
                },
            ),
            Node(
                id="nobel_chemistry_1911",
                type="Award",
                properties={
                    "name": "Nobel Prize in Chemistry",
                    "year": 1911,
                    "category": "Chemistry",
                },
            ),
        ]

        # Create relationships
        relationships = [
            Relationship(
                source=nodes[0],
                target=nodes[1],
                type="MARRIED_TO",
                properties={"year": 1895},
            ),
            Relationship(
                source=nodes[0],
                target=nodes[2],
                type="DISCOVERED",
                properties={"year": 1898},
            ),
            Relationship(
                source=nodes[0],
                target=nodes[3],
                type="DISCOVERED",
                properties={"year": 1898},
            ),
            Relationship(
                source=nodes[1],
                target=nodes[2],
                type="DISCOVERED",
                properties={"year": 1898},
            ),
            Relationship(
                source=nodes[0],
                target=nodes[4],
                type="RECEIVED",
                properties={"shared_with": "Pierre Curie, Henri Becquerel"},
            ),
            Relationship(
                source=nodes[1],
                target=nodes[4],
                type="RECEIVED",
                properties={"shared_with": "Marie Curie, Henri Becquerel"},
            ),
            Relationship(
                source=nodes[0],
                target=nodes[5],
                type="RECEIVED",
                properties={"sole_recipient": True},
            ),
        ]

        return GraphDocument(
            nodes=nodes,
            relationships=relationships,
            source=Document(
                page_content="Marie Curie biography and scientific achievements",
                metadata={"source": "scientific_database", "topic": "chemistry"},
            ),
        )

    @pytest.mark.asyncio
    async def test_full_knowledge_graph_workflow(self, knowledge_graph_data):
        """Test complete knowledge graph creation and querying workflow."""
        # Initialize store
        store = GraphStore()

        # Add data
        await store.add_graph_documents([knowledge_graph_data])

        # Verify data was added
        schema = store.get_structured_schema
        assert schema["nodes"]["total"] == 6
        assert schema["relationships"]["total"] == 7

        # Query all people
        people = await store.query("MATCH (n:Person) RETURN n")
        assert len(people) == 2
        person_names = {p["n"]["properties"]["name"] for p in people}
        assert person_names == {"Marie Curie", "Pierre Curie"}

        # Query all elements
        elements = await store.query("MATCH (n:Element) RETURN n")
        assert len(elements) == 2
        element_symbols = {e["n"]["properties"]["symbol"] for e in elements}
        assert element_symbols == {"Ra", "Po"}

        # Query relationships
        all_rels = await store.query("MATCH (n)-[r]->(m) RETURN n,r,m")
        assert len(all_rels) == 7

        # Verify relationship types
        rel_types = {rel["r"]["type"] for rel in all_rels}
        expected_types = {"MARRIED_TO", "DISCOVERED", "RECEIVED"}
        assert rel_types == expected_types

    @pytest.mark.asyncio
    async def test_multi_document_workflow(self):
        """Test workflow with multiple graph documents."""
        store = GraphStore()

        # First document - Person data
        doc1_nodes = [
            Node(
                id="alice",
                type="Person",
                properties={"name": "Alice", "role": "Engineer"},
            ),
            Node(
                id="bob", type="Person", properties={"name": "Bob", "role": "Designer"}
            ),
        ]
        doc1_rels = [
            Relationship(
                source=doc1_nodes[0], target=doc1_nodes[1], type="COLLABORATES_WITH"
            )
        ]
        doc1 = GraphDocument(
            nodes=doc1_nodes,
            relationships=doc1_rels,
            source=Document(page_content="Team data", metadata={"type": "hr_data"}),
        )

        # Second document - Project data
        doc2_nodes = [
            Node(
                id="project_x",
                type="Project",
                properties={"name": "Project X", "status": "active"},
            ),
        ]
        doc2_rels = [
            Relationship(source=doc1_nodes[0], target=doc2_nodes[0], type="WORKS_ON"),
            Relationship(source=doc1_nodes[1], target=doc2_nodes[0], type="WORKS_ON"),
        ]
        doc2 = GraphDocument(
            nodes=doc2_nodes,
            relationships=doc2_rels,
            source=Document(
                page_content="Project data", metadata={"type": "project_data"}
            ),
        )

        # Add both documents
        await store.add_graph_documents([doc1, doc2])

        # Verify combined data
        schema = store.get_structured_schema
        assert schema["nodes"]["total"] == 3  # alice, bob, project_x
        assert schema["relationships"]["total"] == 3  # COLLABORATES_WITH + 2x WORKS_ON

        # Query cross-document relationships
        project_workers = await store.query("MATCH (n)-[r]->(m) RETURN n,r,m")
        work_relationships = [
            rel for rel in project_workers if rel["r"]["type"] == "WORKS_ON"
        ]
        assert len(work_relationships) == 2

    @pytest.mark.asyncio
    async def test_schema_evolution_workflow(self):
        """Test how schema evolves as data is added."""
        store = GraphStore()

        # Initially empty
        schema = store.get_structured_schema
        assert schema["nodes"]["total"] == 0
        assert schema["relationships"]["total"] == 0

        # Add first set of data
        nodes1 = [Node(id="n1", type="TypeA", properties={})]
        rels1 = []
        doc1 = GraphDocument(
            nodes=nodes1, relationships=rels1, source=Document(page_content="Doc 1")
        )
        await store.add_graph_documents([doc1])

        schema = store.get_structured_schema
        assert schema["nodes"]["total"] == 1
        assert "TypeA" in schema["nodes"]["types"]

        # Add second set with new types
        nodes2 = [
            Node(id="n2", type="TypeB", properties={}),
            Node(id="n3", type="TypeC", properties={}),
        ]
        rels2 = [
            Relationship(source=nodes1[0], target=nodes2[0], type="CONNECTS_TO"),
            Relationship(source=nodes2[0], target=nodes2[1], type="RELATES_TO"),
        ]
        doc2 = GraphDocument(
            nodes=nodes2, relationships=rels2, source=Document(page_content="Doc 2")
        )
        await store.add_graph_documents([doc2])

        # Verify schema evolved
        schema = store.get_structured_schema
        assert schema["nodes"]["total"] == 3
        assert set(schema["nodes"]["types"]) == {"TypeA", "TypeB", "TypeC"}
        assert schema["relationships"]["total"] == 2
        assert set(schema["relationships"]["types"]) == {"CONNECTS_TO", "RELATES_TO"}

    @pytest.mark.asyncio
    async def test_complex_query_workflow(self):
        """Test complex querying scenarios."""
        store = GraphStore()

        # Create a small social network
        people = [
            Node(
                id="alice", type="Person", properties={"name": "Alice", "city": "NYC"}
            ),
            Node(id="bob", type="Person", properties={"name": "Bob", "city": "NYC"}),
            Node(
                id="charlie",
                type="Person",
                properties={"name": "Charlie", "city": "SF"},
            ),
            Node(id="diana", type="Person", properties={"name": "Diana", "city": "SF"}),
        ]

        companies = [
            Node(
                id="techcorp",
                type="Company",
                properties={"name": "TechCorp", "city": "NYC"},
            ),
            Node(
                id="startup_inc",
                type="Company",
                properties={"name": "StartupInc", "city": "SF"},
            ),
        ]

        relationships = [
            # Friendships
            Relationship(source=people[0], target=people[1], type="FRIENDS_WITH"),
            Relationship(source=people[1], target=people[0], type="FRIENDS_WITH"),
            Relationship(source=people[2], target=people[3], type="FRIENDS_WITH"),
            Relationship(source=people[3], target=people[2], type="FRIENDS_WITH"),
            # Employment
            Relationship(source=people[0], target=companies[0], type="WORKS_AT"),
            Relationship(source=people[1], target=companies[0], type="WORKS_AT"),
            Relationship(source=people[2], target=companies[1], type="WORKS_AT"),
            Relationship(source=people[3], target=companies[1], type="WORKS_AT"),
        ]

        doc = GraphDocument(
            nodes=people + companies,
            relationships=relationships,
            source=Document(page_content="Social network data"),
        )

        await store.add_graph_documents([doc])

        # Test various query patterns

        # 1. All people
        all_people = await store.query("MATCH (n:Person) RETURN n")
        assert len(all_people) == 4

        # 2. All companies
        all_companies = await store.query("MATCH (n:Company) RETURN n")
        assert len(all_companies) == 2

        # 3. All relationships
        all_rels = await store.query("MATCH (n)-[r]->(m) RETURN n,r,m")
        assert len(all_rels) == 8  # 4 friendships + 4 employments

        # 4. Specific person query
        alice = await store.query("MATCH (n {id: 'alice'}) RETURN n")
        assert len(alice) == 1
        assert alice[0]["n"]["properties"]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in various scenarios."""
        store = GraphStore()

        # Test invalid query
        with pytest.raises(Exception):  # Should raise QueryError
            await store.query("INVALID SYNTAX HERE")

        # Test querying empty graph (should not error)
        results = await store.query("MATCH (n) RETURN n")
        assert len(results) == 0

        # Test schema operations on empty graph
        schema_str = store.get_schema
        assert "Empty graph" in schema_str

        schema_dict = store.get_structured_schema
        assert schema_dict["nodes"]["total"] == 0
