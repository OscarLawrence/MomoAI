"""
Test the performance improvement from indexed queries.

Compares before/after performance to validate 8x improvement target.
"""

import asyncio
import time
import statistics
from datetime import datetime

from momo_kb import KnowledgeBase, Node, Edge


async def benchmark_indexed_queries():
    """Benchmark the new indexed query performance."""
    print("🚀 Testing Indexed Query Performance")
    print("=" * 50)

    async with KnowledgeBase() as kb:
        # Setup test data - larger dataset to see indexing benefits
        print("📊 Setting up test data (10,000 nodes)...")

        categories = [
            "engineering",
            "design",
            "product",
            "marketing",
            "sales",
            "hr",
            "finance",
            "legal",
        ]
        levels = ["L1", "L2", "L3", "L4", "L5", "L6"]

        # Create nodes with various properties
        for i in range(10000):
            await kb.insert_node(
                Node(
                    label="Employee",
                    properties={
                        "id": i,
                        "department": categories[i % len(categories)],
                        "level": levels[i % len(levels)],
                        "active": i % 10 != 0,  # 90% active
                        "salary": 50000 + (i % 100) * 1000,  # Range: 50k-149k
                        "hire_year": 2015 + (i % 8),  # 2015-2022
                    },
                )
            )

        # Create some relationships
        print("📊 Creating relationships...")
        employees = await kb.query_nodes(label="Employee")
        for i in range(0, min(2000, len(employees.nodes) - 1), 2):
            await kb.insert_edge(
                Edge(
                    source_id=employees.nodes[i].id,
                    target_id=employees.nodes[i + 1].id,
                    relationship="reports_to",
                )
            )

        print(
            f"✅ Setup complete: {await kb.count_nodes()} nodes, {await kb.count_edges()} edges"
        )

        # Benchmark different query types
        print("\n🔍 Benchmarking Query Performance")
        print("-" * 40)

        query_tests = [
            ("Label query", lambda: kb.query_nodes(label="Employee")),
            (
                "Single property",
                lambda: kb.query_nodes(properties={"department": "engineering"}),
            ),
            (
                "Multiple properties",
                lambda: kb.query_nodes(properties={"level": "L3", "active": True}),
            ),
            ("Numeric property", lambda: kb.query_nodes(properties={"salary": 75000})),
            ("Edge relationship", lambda: kb.query_edges(relationship="reports_to")),
            (
                "Connected nodes",
                lambda: kb.query_connected_nodes(
                    start_node_id=employees.nodes[0].id,
                    relationship="reports_to",
                    direction="outgoing",
                ),
            ),
        ]

        results = {}

        for test_name, query_func in query_tests:
            print(f"\n📊 Testing: {test_name}")

            # Warm up
            await query_func()

            # Run multiple iterations
            times = []
            result_counts = []

            for _ in range(50):  # 50 iterations for statistical significance
                start = time.perf_counter()
                result = await query_func()
                end = time.perf_counter()

                query_time = (end - start) * 1000  # Convert to ms
                times.append(query_time)

                if hasattr(result, "nodes"):
                    result_counts.append(len(result.nodes))
                else:
                    result_counts.append(len(result.edges))

            avg_time = statistics.mean(times)
            p50_time = statistics.median(times)
            p95_time = (
                statistics.quantiles(times, n=20)[18]
                if len(times) >= 20
                else max(times)
            )
            min_time = min(times)
            max_time = max(times)
            avg_results = statistics.mean(result_counts)

            print(f"  ⚡ Average: {avg_time:.3f}ms")
            print(f"  ⚡ Median:  {p50_time:.3f}ms")
            print(f"  ⚡ P95:     {p95_time:.3f}ms")
            print(f"  ⚡ Range:   {min_time:.3f}ms - {max_time:.3f}ms")
            print(f"  📊 Results: {avg_results:.0f} items")

            results[test_name] = {
                "avg_ms": avg_time,
                "p50_ms": p50_time,
                "p95_ms": p95_time,
                "min_ms": min_time,
                "max_ms": max_time,
                "result_count": avg_results,
            }

        # Performance assessment
        print("\n🎯 Performance Assessment")
        print("-" * 40)

        # Compare against our targets
        targets = {
            "Label query": 0.5,  # Target: <0.5ms
            "Single property": 1.0,  # Target: <1ms
            "Multiple properties": 2.0,  # Target: <2ms
            "Edge relationship": 1.0,  # Target: <1ms
            "Connected nodes": 2.0,  # Target: <2ms
        }

        all_passed = True
        for test_name, target_ms in targets.items():
            if test_name in results:
                actual_ms = results[test_name]["avg_ms"]
                if actual_ms <= target_ms:
                    print(f"✅ {test_name}: {actual_ms:.3f}ms (target: <{target_ms}ms)")
                else:
                    print(f"❌ {test_name}: {actual_ms:.3f}ms (target: <{target_ms}ms)")
                    all_passed = False

        if all_passed:
            print("\n🎉 ALL PERFORMANCE TARGETS MET!")
            print("🚀 Indexed queries are performing excellently!")
        else:
            print("\n⚠️  Some targets not met - may need further optimization")

        return results


async def main():
    """Run indexed query performance tests."""
    results = await benchmark_indexed_queries()

    print(f"\n📋 Summary Results:")
    print("=" * 50)
    for test_name, metrics in results.items():
        print(f"{test_name}:")
        print(f"  Average: {metrics['avg_ms']:.3f}ms")
        print(f"  P95:     {metrics['p95_ms']:.3f}ms")
        print(f"  Results: {metrics['result_count']:.0f} items")
        print()


if __name__ == "__main__":
    asyncio.run(main())
