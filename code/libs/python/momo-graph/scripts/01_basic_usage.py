#!/usr/bin/env python3
"""
Basic usage example for momo-graph GraphBackend.

Demonstrates core functionality including:
- Node and edge creation
- Querying
- Rollback operations
"""

import asyncio
from momo_graph import GraphBackend, GraphNode, GraphEdge


async def main():
    """Demonstrate basic GraphBackend usage."""
    print("🔥 Momo Graph Basic Usage Example")
    print("=" * 50)
    
    # Create and initialize graph backend
    async with GraphBackend() as graph:
        print("\n1. Creating nodes...")
        
        # Create some people
        alice = GraphNode(
            label="Person", 
            properties={"name": "Alice", "age": 30, "city": "New York"}
        )
        bob = GraphNode(
            label="Person",
            properties={"name": "Bob", "age": 25, "city": "San Francisco"}
        )
        charlie = GraphNode(
            label="Person", 
            properties={"name": "Charlie", "age": 35, "city": "New York"}
        )
        
        # Insert nodes
        await graph.insert_node(alice)
        await graph.insert_node(bob) 
        await graph.insert_node(charlie)
        
        print(f"   ✅ Inserted {await graph.count_nodes()} nodes")
        
        print("\n2. Creating relationships...")
        
        # Create friendships
        friendship1 = GraphEdge(
            source_id=alice.id,
            target_id=bob.id,
            relationship="FRIEND",
            properties={"since": "2020-01-01", "strength": 0.8}
        )
        friendship2 = GraphEdge(
            source_id=alice.id,
            target_id=charlie.id, 
            relationship="FRIEND",
            properties={"since": "2019-06-15", "strength": 0.9}
        )
        
        await graph.insert_edge(friendship1)
        await graph.insert_edge(friendship2)
        
        print(f"   ✅ Inserted {await graph.count_edges()} edges")
        
        print("\n3. Querying data...")
        
        # Query all people
        all_people = await graph.query_nodes(label="Person")
        print(f"   📊 Found {len(all_people.nodes)} people (query time: {all_people.query_time_ms:.2f}ms)")
        
        # Query people in New York
        ny_people = await graph.query_nodes(
            label="Person",
            properties={"city": "New York"}
        )
        print(f"   🏙️  Found {len(ny_people.nodes)} people in New York:")
        for person in ny_people.nodes:
            print(f"      - {person.properties['name']}")
        
        # Query Alice's friends
        alice_friends = await graph.query_connected_nodes(
            alice.id, "FRIEND", direction="outgoing"
        )
        print(f"   👥 Alice has {len(alice_friends.nodes)} friends:")
        for friend in alice_friends.nodes:
            print(f"      - {friend.properties['name']}")
        
        print("\n4. Demonstrating rollback...")
        
        # Add another person
        diana = GraphNode(
            label="Person",
            properties={"name": "Diana", "age": 28, "city": "Boston"}
        )
        await graph.insert_node(diana)
        print(f"   ➕ Added Diana. Total nodes: {await graph.count_nodes()}")
        
        # Rollback the last operation
        await graph.rollback(steps=1)
        print(f"   ↩️  Rolled back. Total nodes: {await graph.count_nodes()}")
        
        print("\n5. Export data...")
        
        # Export everything to JSON
        export_data = await graph.export_json()
        print(f"   📤 Exported {export_data['metadata']['total_nodes']} nodes and {export_data['metadata']['total_edges']} edges")
        
        print("\n6. Performance characteristics:")
        print(f"   ⚡ Average node query time: {all_people.query_time_ms:.3f}ms")
        print(f"   📈 Operations in diff history: {len(await graph.get_diff_history())}")
        
        print(f"\n✨ Demo completed successfully!")
        print(f"   - Nodes: {await graph.count_nodes()}")
        print(f"   - Edges: {await graph.count_edges()}")


if __name__ == "__main__":
    asyncio.run(main())