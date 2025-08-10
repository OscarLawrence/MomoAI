#!/usr/bin/env python3
"""
Basic usage example for momo-graph-store.

This script demonstrates the core functionality of the GraphStore module,
showing how to create nodes, relationships, and query the graph.
"""

import asyncio
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.documents import Document

from momo_graph_store import GraphStore


async def main():
    """Demonstrate basic GraphStore functionality."""
    print("🚀 momo-graph-store Basic Usage Example")
    print("=" * 50)

    # Initialize GraphStore with default InMemory backend
    store = GraphStore()
    print(f"✅ Initialized GraphStore: {store}")

    # Create some sample nodes
    print("\n📝 Creating sample nodes...")
    nodes = [
        Node(
            id="alice",
            type="Person",
            properties={"name": "Alice Johnson", "age": 30, "city": "San Francisco"},
        ),
        Node(
            id="bob",
            type="Person",
            properties={"name": "Bob Smith", "age": 28, "city": "San Francisco"},
        ),
        Node(
            id="techcorp",
            type="Company",
            properties={"name": "TechCorp", "founded": 2010, "industry": "Technology"},
        ),
        Node(
            id="python",
            type="Technology",
            properties={
                "name": "Python",
                "type": "Programming Language",
                "created": 1991,
            },
        ),
    ]

    # Create relationships between nodes
    print("🔗 Creating relationships...")
    relationships = [
        Relationship(
            source=nodes[0],  # alice
            target=nodes[1],  # bob
            type="KNOWS",
            properties={"since": "2020", "relationship": "colleague"},
        ),
        Relationship(
            source=nodes[0],  # alice
            target=nodes[2],  # techcorp
            type="WORKS_AT",
            properties={"role": "Senior Engineer", "start_date": "2022-01-01"},
        ),
        Relationship(
            source=nodes[1],  # bob
            target=nodes[2],  # techcorp
            type="WORKS_AT",
            properties={"role": "Product Designer", "start_date": "2021-06-15"},
        ),
        Relationship(
            source=nodes[0],  # alice
            target=nodes[3],  # python
            type="USES",
            properties={"proficiency": "expert", "years_experience": 8},
        ),
        Relationship(
            source=nodes[1],  # bob
            target=nodes[3],  # python
            type="USES",
            properties={"proficiency": "intermediate", "years_experience": 3},
        ),
    ]

    # Create a GraphDocument
    graph_doc = GraphDocument(
        nodes=nodes,
        relationships=relationships,
        source=Document(
            page_content="Employee and technology data from TechCorp",
            metadata={"source": "hr_database", "date": "2025-01-01"},
        ),
    )

    # Add the graph document to the store
    print("💾 Adding graph document to store...")
    await store.add_graph_documents([graph_doc])

    # Display schema information
    print("\n📊 Graph Schema:")
    print(store.get_schema)

    print("\n📋 Structured Schema:")
    schema = store.get_structured_schema
    print(f"  • Total nodes: {schema['nodes']['total']}")
    print(f"  • Node types: {', '.join(schema['nodes']['types'])}")
    print(f"  • Total relationships: {schema['relationships']['total']}")
    print(f"  • Relationship types: {', '.join(schema['relationships']['types'])}")

    # Query examples
    print("\n🔍 Query Examples:")

    # 1. Get all nodes
    print("\n1. All nodes:")
    results = await store.query("MATCH (n) RETURN n")
    for i, result in enumerate(results, 1):
        node = result["n"]
        print(
            f"   {i}. {node['type']} '{node['id']}': {node['properties'].get('name', node['id'])}"
        )

    # 2. Get all people
    print("\n2. All people:")
    results = await store.query("MATCH (n:Person) RETURN n")
    for result in results:
        person = result["n"]
        props = person["properties"]
        print(f"   • {props['name']} (age {props['age']}, lives in {props['city']})")

    # 3. Get all companies
    print("\n3. All companies:")
    results = await store.query("MATCH (n:Company) RETURN n")
    for result in results:
        company = result["n"]
        props = company["properties"]
        print(
            f"   • {props['name']} (founded {props['founded']}, industry: {props['industry']})"
        )

    # 4. Get all relationships
    print("\n4. All relationships:")
    results = await store.query("MATCH (n)-[r]->(m) RETURN n,r,m")
    for result in results:
        source = result["n"]["properties"]["name"]
        rel_type = result["r"]["type"]
        target = result["m"]["properties"]["name"]
        print(f"   • {source} —{rel_type}→ {target}")

    # 5. Get specific person
    print("\n5. Specific person (Alice):")
    results = await store.query("MATCH (n {id: 'alice'}) RETURN n")
    if results:
        alice = results[0]["n"]
        props = alice["properties"]
        print(f"   • Name: {props['name']}")
        print(f"   • Age: {props['age']}")
        print(f"   • City: {props['city']}")

    # Get backend information
    print("\n🔧 Backend Information:")
    info = store.get_info()
    backend_info = info["backend"]
    print(f"  • Backend type: {backend_info['type']}")
    print(f"  • Backend name: {backend_info['backend_name']}")

    print("\n✨ Basic usage demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
