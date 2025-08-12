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

try:
    from momo_logger import get_logger
    from momo_logger.types import LogLevel

    MOMO_LOGGER_AVAILABLE = True
except ImportError:
    MOMO_LOGGER_AVAILABLE = False

# Initialize logger for user-facing messages
if MOMO_LOGGER_AVAILABLE:
    logger = get_logger("momo-graph.examples", level=LogLevel.AI_USER)
else:
    logger = None


def log_user(message: str):
    """Log user-facing message with momo-logger or fallback to print."""
    if MOMO_LOGGER_AVAILABLE and logger:
        logger._sync_log(LogLevel.AI_USER, message, user_facing=True)
    else:
        print(message)


async def main():
    """Demonstrate basic GraphBackend usage."""
    log_user("🔥 Momo Graph Basic Usage Example")
    log_user("=" * 50)

    # Create and initialize graph backend
    async with GraphBackend() as graph:
        log_user("\n1. Creating nodes...")

        # Create some people
        alice = GraphNode(
            label="Person", properties={"name": "Alice", "age": 30, "city": "New York"}
        )
        bob = GraphNode(
            label="Person",
            properties={"name": "Bob", "age": 25, "city": "San Francisco"},
        )
        charlie = GraphNode(
            label="Person",
            properties={"name": "Charlie", "age": 35, "city": "New York"},
        )

        # Insert nodes
        await graph.insert_node(alice)
        await graph.insert_node(bob)
        await graph.insert_node(charlie)

        log_user(f"   ✅ Inserted {await graph.count_nodes()} nodes")

        log_user("\n2. Creating relationships...")

        # Create friendships
        friendship1 = GraphEdge(
            source_id=alice.id,
            target_id=bob.id,
            relationship="FRIEND",
            properties={"since": "2020-01-01", "strength": 0.8},
        )
        friendship2 = GraphEdge(
            source_id=alice.id,
            target_id=charlie.id,
            relationship="FRIEND",
            properties={"since": "2019-06-15", "strength": 0.9},
        )

        await graph.insert_edge(friendship1)
        await graph.insert_edge(friendship2)

        log_user(f"   ✅ Inserted {await graph.count_edges()} edges")

        log_user("\n3. Querying data...")

        # Query all people
        all_people = await graph.query_nodes(label="Person")
        log_user(
            f"   📊 Found {len(all_people.nodes)} people (query time: {all_people.query_time_ms:.2f}ms)"
        )

        # Query people in New York
        ny_people = await graph.query_nodes(
            label="Person", properties={"city": "New York"}
        )
        log_user(f"   🏙️  Found {len(ny_people.nodes)} people in New York:")
        for person in ny_people.nodes:
            log_user(f"      - {person.properties['name']}")

        # Query Alice's friends
        alice_friends = await graph.query_connected_nodes(
            alice.id, "FRIEND", direction="outgoing"
        )
        log_user(f"   👥 Alice has {len(alice_friends.nodes)} friends:")
        for friend in alice_friends.nodes:
            log_user(f"      - {friend.properties['name']}")

        log_user("\n4. Demonstrating rollback...")

        # Add another person
        diana = GraphNode(
            label="Person", properties={"name": "Diana", "age": 28, "city": "Boston"}
        )
        await graph.insert_node(diana)
        log_user(f"   ➕ Added Diana. Total nodes: {await graph.count_nodes()}")

        # Rollback the last operation
        await graph.rollback(steps=1)
        log_user(f"   ↩️  Rolled back. Total nodes: {await graph.count_nodes()}")

        log_user("\n5. Export data...")

        # Export everything to JSON
        export_data = await graph.export_json()
        log_user(
            f"   📤 Exported {export_data['metadata']['total_nodes']} nodes and {export_data['metadata']['total_edges']} edges"
        )

        log_user("\n6. Performance characteristics:")
        log_user(f"   ⚡ Average node query time: {all_people.query_time_ms:.3f}ms")
        log_user(
            f"   📈 Operations in diff history: {len(await graph.get_diff_history())}"
        )

        log_user(f"\n✨ Demo completed successfully!")
        log_user(f"   - Nodes: {await graph.count_nodes()}")
        log_user(f"   - Edges: {await graph.count_edges()}")


if __name__ == "__main__":
    asyncio.run(main())
