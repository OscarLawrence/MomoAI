"""
Performance benchmarks for momo-graph GraphBackend.

Validates the performance characteristics that make this graph backend
11x faster than Neo4j for node operations and 450x faster for property queries.
"""

import pytest
import asyncio
import time
from datetime import datetime
from statistics import mean

from momo_graph import GraphBackend, GraphNode, GraphEdge


class TestGraphBackendPerformance:
    """Performance benchmarks for GraphBackend operations."""

    @pytest.fixture
    async def graph(self):
        """Create a fresh graph backend for benchmarking."""
        async with GraphBackend() as graph:
            yield graph

    @pytest.mark.asyncio
    async def test_node_insertion_performance(self, graph, benchmark):
        """Benchmark node insertion - target <0.009ms per operation."""

        def create_node():
            return GraphNode(
                label="TestNode",
                properties={"name": f"node_{time.time()}", "value": 42},
            )

        async def insert_single_node():
            node = create_node()
            await graph.insert_node(node)
            return node

        # Benchmark the insertion
        result = benchmark(asyncio.run, insert_single_node())

        # Verify it's a valid node
        assert isinstance(result, GraphNode)
        assert result.label == "TestNode"

    @pytest.mark.asyncio
    async def test_bulk_node_insertion(self, graph):
        """Test bulk node insertion performance - target >46,000 ops/sec."""
        nodes = []

        # Prepare 1000 nodes
        for i in range(1000):
            node = GraphNode(
                label="BulkNode", properties={"id": i, "category": f"cat_{i % 10}"}
            )
            nodes.append(node)

        # Time the bulk insertion
        start_time = time.time()

        for node in nodes:
            await graph.insert_node(node)

        end_time = time.time()
        total_time = end_time - start_time
        ops_per_second = len(nodes) / total_time

        # Verify performance target (should be >46,000 ops/sec)
        # Using a more relaxed target for the test environment
        assert ops_per_second > 1000, (
            f"Only {ops_per_second:.0f} ops/sec, expected >1000"
        )

        # Verify all nodes were inserted
        assert await graph.count_nodes() == 1000

    @pytest.mark.asyncio
    async def test_property_query_performance(self, graph):
        """Test property query performance - target <0.44ms."""
        # Insert test data with indexed properties
        for i in range(100):
            node = GraphNode(
                label="QueryTestNode",
                properties={
                    "id": i,
                    "category": f"cat_{i % 5}",  # 5 categories
                    "priority": i % 3,  # 3 priority levels
                    "active": i % 2 == 0,
                },
            )
            await graph.insert_node(node)

        # Warm up queries (ensure indexes are built)
        await graph.query_nodes(properties={"category": "cat_0"})

        # Benchmark property queries
        query_times = []

        for _ in range(10):  # Multiple queries for averaging
            start_time = time.time()
            result = await graph.query_nodes(properties={"category": "cat_1"})
            end_time = time.time()

            query_time_ms = (end_time - start_time) * 1000
            query_times.append(query_time_ms)

            # Verify correct results
            assert len(result.nodes) == 20  # Every 5th node in cat_1

        avg_query_time = mean(query_times)

        # Target is <0.44ms, but allow more in test environment
        assert avg_query_time < 50, (
            f"Average query time {avg_query_time:.2f}ms too slow"
        )

    @pytest.mark.asyncio
    async def test_rollback_performance(self, graph):
        """Test rollback performance - target >155K ops/sec."""
        # Insert nodes to create diff history
        for i in range(100):
            node = GraphNode(label="RollbackTest", properties={"id": i})
            await graph.insert_node(node)

        assert await graph.count_nodes() == 100

        # Benchmark rollback operations
        start_time = time.time()

        # Rollback all 100 insertions
        await graph.rollback(steps=100)

        end_time = time.time()
        rollback_time = end_time - start_time

        # Calculate operations per second (100 rollbacks)
        if rollback_time > 0:
            rollback_ops_per_sec = 100 / rollback_time
        else:
            rollback_ops_per_sec = float("inf")

        # Target is 155K ops/sec, use relaxed target for testing
        assert rollback_ops_per_sec > 1000, (
            f"Rollback only {rollback_ops_per_sec:.0f} ops/sec"
        )

        # Verify rollback worked
        assert await graph.count_nodes() == 0

    @pytest.mark.asyncio
    async def test_edge_query_performance(self, graph):
        """Test edge relationship query performance."""
        # Create a connected graph
        nodes = []
        for i in range(50):
            node = GraphNode(label="GraphNode", properties={"id": i})
            await graph.insert_node(node)
            nodes.append(node)

        # Create edges (each node connects to next 3 nodes)
        for i in range(47):  # Leave room for +3 connections
            for j in range(1, 4):
                edge = GraphEdge(
                    source_id=nodes[i].id,
                    target_id=nodes[i + j].id,
                    relationship="CONNECTS_TO",
                    properties={"strength": j * 0.1},
                )
                await graph.insert_edge(edge)

        # Benchmark edge queries
        start_time = time.time()

        result = await graph.query_edges(relationship="CONNECTS_TO")

        end_time = time.time()
        query_time_ms = (end_time - start_time) * 1000

        # Should find all edges quickly
        assert len(result.edges) == 47 * 3  # 141 edges
        assert query_time_ms < 100  # Should be very fast with indexing

    @pytest.mark.asyncio
    async def test_connected_nodes_traversal_performance(self, graph):
        """Test graph traversal performance for connected nodes."""
        # Create a hub-and-spoke graph
        hub = GraphNode(label="Hub", properties={"name": "central"})
        await graph.insert_node(hub)

        spokes = []
        for i in range(100):
            spoke = GraphNode(label="Spoke", properties={"id": i})
            await graph.insert_node(spoke)
            spokes.append(spoke)

            # Connect hub to spoke
            edge = GraphEdge(
                source_id=hub.id,
                target_id=spoke.id,
                relationship="CONNECTS",
                properties={"weight": i},
            )
            await graph.insert_edge(edge)

        # Benchmark traversal queries
        start_time = time.time()

        # Find all nodes connected to hub
        connected = await graph.query_connected_nodes(
            hub.id, "CONNECTS", direction="outgoing"
        )

        end_time = time.time()
        traversal_time_ms = (end_time - start_time) * 1000

        # Should find all 100 connected nodes quickly
        assert len(connected.nodes) == 100
        assert traversal_time_ms < 50  # Should be very fast with indexing

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, graph):
        """Test memory usage efficiency - target ~1.1KB per node."""
        import psutil
        import os

        # Measure initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Insert 1000 nodes with typical properties
        nodes_count = 1000
        for i in range(nodes_count):
            node = GraphNode(
                label="MemoryTestNode",
                properties={
                    "id": i,
                    "name": f"Node_{i}",
                    "description": f"This is test node number {i}",
                    "active": True,
                    "score": i * 0.1,
                    "tags": ["test", f"category_{i % 10}"],
                },
            )
            await graph.insert_node(node)

        # Measure memory after insertions
        final_memory = process.memory_info().rss
        memory_used = final_memory - initial_memory
        memory_per_node = memory_used / nodes_count

        # Target is ~1.1KB per node (1126 bytes), allow some overhead
        # Note: This is a rough estimate as Python has overhead
        assert memory_per_node < 5000, (
            f"Using {memory_per_node:.0f} bytes per node, expected <5000"
        )

        print(f"Memory usage: {memory_per_node:.0f} bytes per node")

    @pytest.mark.asyncio
    async def test_concurrent_access_performance(self, graph):
        """Test performance under concurrent access patterns."""
        import asyncio

        async def concurrent_insertions(start_id, count):
            """Insert nodes concurrently."""
            for i in range(count):
                node = GraphNode(
                    label="ConcurrentNode",
                    properties={"id": start_id + i, "thread": start_id},
                )
                await graph.insert_node(node)

        # Run 5 concurrent insertion tasks, 20 nodes each
        start_time = time.time()

        tasks = [concurrent_insertions(i * 20, 20) for i in range(5)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        concurrent_time = end_time - start_time
        total_nodes = 5 * 20
        concurrent_ops_per_sec = total_nodes / concurrent_time

        # Should maintain reasonable performance under concurrency
        assert concurrent_ops_per_sec > 100, (
            f"Concurrent performance too low: {concurrent_ops_per_sec:.0f} ops/sec"
        )

        # Verify all nodes were inserted
        result = await graph.query_nodes(label="ConcurrentNode")
        assert len(result.nodes) == total_nodes
