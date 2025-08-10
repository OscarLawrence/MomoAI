"""
Performance benchmarks for momo-graph-store.

Tests the performance characteristics of different operations
and provides baseline measurements for optimization.
"""

import asyncio
import time
from typing import List

from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.documents import Document

from momo_graph_store import GraphStore


class GraphStoreBenchmark:
    """Performance benchmark suite for GraphStore operations."""

    def __init__(self, backend_type: str = "memory"):
        """Initialize benchmark with specified backend."""
        self.backend_type = backend_type
        self.store = GraphStore(backend_type=backend_type)
        self.results = {}

    async def benchmark_add_documents(
        self, num_nodes: int, num_relationships: int
    ) -> float:
        """Benchmark adding graph documents."""
        # Generate test data
        nodes = [
            Node(
                id=f"node_{i}",
                type="TestNode",
                properties={"index": i, "name": f"Node {i}"},
            )
            for i in range(num_nodes)
        ]

        relationships = []
        for i in range(num_relationships):
            source_idx = i % num_nodes
            target_idx = (i + 1) % num_nodes
            relationships.append(
                Relationship(
                    source=nodes[source_idx],
                    target=nodes[target_idx],
                    type="TEST_RELATION",
                    properties={"index": i},
                )
            )

        graph_doc = GraphDocument(
            nodes=nodes,
            relationships=relationships,
            source=Document(
                page_content=f"Benchmark data {num_nodes}x{num_relationships}"
            ),
        )

        # Benchmark the operation
        start_time = time.perf_counter()
        await self.store.add_graph_documents([graph_doc])
        end_time = time.perf_counter()

        return end_time - start_time

    async def benchmark_query_all_nodes(self) -> float:
        """Benchmark querying all nodes."""
        start_time = time.perf_counter()
        results = await self.store.query("MATCH (n) RETURN n")
        end_time = time.perf_counter()

        print(f"  → Retrieved {len(results)} nodes")
        return end_time - start_time

    async def benchmark_query_by_type(self) -> float:
        """Benchmark querying nodes by type."""
        start_time = time.perf_counter()
        results = await self.store.query("MATCH (n:TestNode) RETURN n")
        end_time = time.perf_counter()

        print(f"  → Retrieved {len(results)} TestNode nodes")
        return end_time - start_time

    async def benchmark_query_relationships(self) -> float:
        """Benchmark querying relationships."""
        start_time = time.perf_counter()
        results = await self.store.query("MATCH (n)-[r]->(m) RETURN n,r,m")
        end_time = time.perf_counter()

        print(f"  → Retrieved {len(results)} relationships")
        return end_time - start_time

    async def benchmark_specific_node_query(self) -> float:
        """Benchmark querying specific node."""
        start_time = time.perf_counter()
        results = await self.store.query("MATCH (n {id: 'node_0'}) RETURN n")
        end_time = time.perf_counter()

        print(f"  → Retrieved {len(results)} specific nodes")
        return end_time - start_time

    async def benchmark_schema_operations(self) -> float:
        """Benchmark schema operations."""
        start_time = time.perf_counter()

        # Get schema (string)
        schema_str = self.store.get_schema

        # Get structured schema
        schema_dict = self.store.get_structured_schema

        # Refresh schema
        await self.store.refresh_schema()

        end_time = time.perf_counter()

        print(
            f"  → Schema has {schema_dict['nodes']['total']} nodes, {schema_dict['relationships']['total']} relationships"
        )
        return end_time - start_time

    async def run_benchmark_suite(self, test_sizes: List[tuple] = None) -> dict:
        """Run complete benchmark suite."""
        if test_sizes is None:
            test_sizes = [(100, 150), (500, 750), (1000, 1500)]

        print(f"🚀 GraphStore Performance Benchmark ({self.backend_type} backend)")
        print("=" * 60)

        results = {"backend": self.backend_type, "tests": {}}

        for num_nodes, num_relationships in test_sizes:
            print(
                f"\n📊 Testing with {num_nodes} nodes, {num_relationships} relationships"
            )

            # Fresh store for each test
            self.store = GraphStore(backend_type=self.backend_type)

            # Test data loading
            print("  📝 Adding documents...")
            add_time = await self.benchmark_add_documents(num_nodes, num_relationships)

            # Test queries
            print("  🔍 Query all nodes...")
            query_all_time = await self.benchmark_query_all_nodes()

            print("  🔍 Query by type...")
            query_type_time = await self.benchmark_query_by_type()

            print("  🔍 Query relationships...")
            query_rel_time = await self.benchmark_query_relationships()

            print("  🔍 Query specific node...")
            query_specific_time = await self.benchmark_specific_node_query()

            print("  📋 Schema operations...")
            schema_time = await self.benchmark_schema_operations()

            # Store results
            test_key = f"{num_nodes}n_{num_relationships}r"
            results["tests"][test_key] = {
                "nodes": num_nodes,
                "relationships": num_relationships,
                "add_documents_ms": round(add_time * 1000, 2),
                "query_all_nodes_ms": round(query_all_time * 1000, 2),
                "query_by_type_ms": round(query_type_time * 1000, 2),
                "query_relationships_ms": round(query_rel_time * 1000, 2),
                "query_specific_ms": round(query_specific_time * 1000, 2),
                "schema_operations_ms": round(schema_time * 1000, 2),
            }

            # Summary
            print(f"  ⏱️  Add documents: {add_time * 1000:.2f}ms")
            print(f"  ⏱️  Query all: {query_all_time * 1000:.2f}ms")
            print(f"  ⏱️  Query by type: {query_type_time * 1000:.2f}ms")
            print(f"  ⏱️  Query relationships: {query_rel_time * 1000:.2f}ms")
            print(f"  ⏱️  Query specific: {query_specific_time * 1000:.2f}ms")
            print(f"  ⏱️  Schema ops: {schema_time * 1000:.2f}ms")

        return results

    def print_summary(self, results: dict):
        """Print benchmark summary."""
        print(f"\n📈 Performance Summary ({results['backend']} backend)")
        print("-" * 60)

        for test_key, data in results["tests"].items():
            print(f"\n{data['nodes']} nodes, {data['relationships']} relationships:")
            print(f"  • Add documents:     {data['add_documents_ms']:>8.2f} ms")
            print(f"  • Query all nodes:   {data['query_all_nodes_ms']:>8.2f} ms")
            print(f"  • Query by type:     {data['query_by_type_ms']:>8.2f} ms")
            print(f"  • Query relationships: {data['query_relationships_ms']:>6.2f} ms")
            print(f"  • Query specific:    {data['query_specific_ms']:>8.2f} ms")
            print(f"  • Schema operations: {data['schema_operations_ms']:>8.2f} ms")

        # Performance insights
        print(f"\n💡 Performance Insights:")
        largest_test = list(results["tests"].values())[-1]
        print(
            f"  • Largest test: {largest_test['nodes']} nodes, {largest_test['relationships']} relationships"
        )
        print(f"  • Data loading: {largest_test['add_documents_ms']:.2f}ms")
        print(
            f"  • Average query time: {(largest_test['query_all_nodes_ms'] + largest_test['query_by_type_ms'] + largest_test['query_specific_ms']) / 3:.2f}ms"
        )
        print(f"  • Memory backend suitable for: < 10K nodes (development/testing)")


async def main():
    """Run benchmark suite."""
    # Test InMemory backend
    benchmark = GraphStoreBenchmark("memory")
    results = await benchmark.run_benchmark_suite()
    benchmark.print_summary(results)

    print(f"\n✨ Benchmark complete!")
    print(f"💾 Results available in benchmark object for further analysis")


if __name__ == "__main__":
    asyncio.run(main())
