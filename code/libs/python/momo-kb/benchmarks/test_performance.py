"""
Performance benchmarks for Momo KnowledgeBase.

Compares against industry standards and identifies bottlenecks.
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any
import statistics

from momo_kb import KnowledgeBase, Node, Edge


class BenchmarkRunner:
    """Runs comprehensive performance benchmarks."""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark suites."""
        print("🚀 Starting Momo KnowledgeBase Benchmarks")
        print("=" * 60)
        
        # Core operation benchmarks
        await self._benchmark_basic_operations()
        await self._benchmark_bulk_operations()
        await self._benchmark_query_performance()
        await self._benchmark_rollback_performance()
        await self._benchmark_storage_tiers()
        await self._benchmark_concurrent_operations()
        
        # Memory and scaling benchmarks
        await self._benchmark_memory_usage()
        await self._benchmark_scaling_characteristics()
        
        return self.results
        
    async def _benchmark_basic_operations(self):
        """Benchmark basic CRUD operations."""
        print("\n📊 Basic Operations Benchmark")
        print("-" * 40)
        
        async with KnowledgeBase() as kb:
            # Node insertion benchmark
            times = []
            for i in range(1000):
                start = time.perf_counter()
                await kb.insert_node(Node(label="TestNode", properties={"id": i}))
                end = time.perf_counter()
                times.append((end - start) * 1000)  # Convert to ms
                
            node_insert_avg = statistics.mean(times)
            node_insert_p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
            
            print(f"✅ Node insertion: {node_insert_avg:.3f}ms avg, {node_insert_p95:.3f}ms p95")
            
            # Edge insertion benchmark
            nodes = await kb.query_nodes(label="TestNode")
            times = []
            for i in range(min(500, len(nodes.nodes) - 1)):
                start = time.perf_counter()
                await kb.insert_edge(Edge(
                    source_id=nodes.nodes[i].id,
                    target_id=nodes.nodes[i + 1].id,
                    relationship="connects"
                ))
                end = time.perf_counter()
                times.append((end - start) * 1000)
                
            edge_insert_avg = statistics.mean(times)
            edge_insert_p95 = statistics.quantiles(times, n=20)[18]
            
            print(f"✅ Edge insertion: {edge_insert_avg:.3f}ms avg, {edge_insert_p95:.3f}ms p95")
            
            self.results["basic_operations"] = {
                "node_insert_avg_ms": node_insert_avg,
                "node_insert_p95_ms": node_insert_p95,
                "edge_insert_avg_ms": edge_insert_avg,
                "edge_insert_p95_ms": edge_insert_p95,
            }
            
    async def _benchmark_bulk_operations(self):
        """Benchmark bulk data operations."""
        print("\n📦 Bulk Operations Benchmark")
        print("-" * 40)
        
        async with KnowledgeBase() as kb:
            # Bulk node insertion
            start = time.perf_counter()
            for i in range(10000):
                await kb.insert_node(Node(
                    label="BulkNode",
                    properties={"batch": "bulk_test", "id": i}
                ))
            end = time.perf_counter()
            
            bulk_insert_time = end - start
            bulk_insert_rate = 10000 / bulk_insert_time
            
            print(f"✅ Bulk insert (10k nodes): {bulk_insert_time:.2f}s ({bulk_insert_rate:.0f} ops/sec)")
            
            # Bulk query
            start = time.perf_counter()
            result = await kb.query_nodes(properties={"batch": "bulk_test"})
            end = time.perf_counter()
            
            bulk_query_time = (end - start) * 1000
            
            print(f"✅ Bulk query (10k results): {bulk_query_time:.2f}ms")
            print(f"✅ Query returned: {len(result.nodes)} nodes")
            
            self.results["bulk_operations"] = {
                "bulk_insert_rate_ops_per_sec": bulk_insert_rate,
                "bulk_query_time_ms": bulk_query_time,
                "bulk_query_result_count": len(result.nodes),
            }
            
    async def _benchmark_query_performance(self):
        """Benchmark different query patterns."""
        print("\n🔍 Query Performance Benchmark")
        print("-" * 40)
        
        async with KnowledgeBase() as kb:
            # Setup test data
            categories = ["engineering", "design", "product", "marketing", "sales"]
            for i in range(5000):
                await kb.insert_node(Node(
                    label="Employee",
                    properties={
                        "id": i,
                        "department": categories[i % len(categories)],
                        "level": f"L{(i % 5) + 1}",
                        "active": i % 10 != 0  # 90% active
                    }
                ))
                
            # Create some relationships
            employees = await kb.query_nodes(label="Employee")
            for i in range(0, min(1000, len(employees.nodes) - 1), 2):
                await kb.insert_edge(Edge(
                    source_id=employees.nodes[i].id,
                    target_id=employees.nodes[i + 1].id,
                    relationship="reports_to"
                ))
                
            # Benchmark different query types
            queries = [
                ("Label query", lambda: kb.query_nodes(label="Employee")),
                ("Property filter", lambda: kb.query_nodes(properties={"department": "engineering"})),
                ("Complex filter", lambda: kb.query_nodes(properties={"level": "L3", "active": True})),
                ("Relationship query", lambda: kb.query_edges(relationship="reports_to")),
            ]
            
            for query_name, query_func in queries:
                times = []
                for _ in range(100):  # Run each query 100 times
                    start = time.perf_counter()
                    result = await query_func()
                    end = time.perf_counter()
                    times.append((end - start) * 1000)
                    
                avg_time = statistics.mean(times)
                p95_time = statistics.quantiles(times, n=20)[18]
                
                print(f"✅ {query_name}: {avg_time:.3f}ms avg, {p95_time:.3f}ms p95")
                
            self.results["query_performance"] = {
                "label_query_avg_ms": statistics.mean([t for t in times]),
                "property_filter_avg_ms": avg_time,  # Last measured
                "query_p95_ms": p95_time,
            }
            
    async def _benchmark_rollback_performance(self):
        """Benchmark rollback operations."""
        print("\n⏪ Rollback Performance Benchmark")
        print("-" * 40)
        
        async with KnowledgeBase() as kb:
            # Create operations to rollback
            operations_count = 1000
            for i in range(operations_count):
                await kb.insert_node(Node(label="RollbackTest", properties={"id": i}))
                
            # Benchmark different rollback scenarios
            rollback_scenarios = [
                ("Single step", 1),
                ("10 steps", 10),
                ("100 steps", 100),
                ("500 steps", 500),
            ]
            
            for scenario_name, steps in rollback_scenarios:
                start = time.perf_counter()
                await kb.rollback(steps=steps)
                end = time.perf_counter()
                
                rollback_time = (end - start) * 1000
                rollback_rate = steps / (rollback_time / 1000) if rollback_time > 0 else float('inf')
                
                print(f"✅ {scenario_name} rollback: {rollback_time:.2f}ms ({rollback_rate:.0f} ops/sec)")
                
                # Restore state for next test
                for i in range(steps):
                    await kb.insert_node(Node(label="RollbackTest", properties={"id": f"restore_{i}"}))
                    
            self.results["rollback_performance"] = {
                "single_rollback_ms": rollback_time,  # Last measured
                "rollback_rate_ops_per_sec": rollback_rate,
            }
            
    async def _benchmark_storage_tiers(self):
        """Benchmark storage tier performance."""
        print("\n🗂️ Storage Tier Performance Benchmark")
        print("-" * 40)
        
        async with KnowledgeBase() as kb:
            # Fill runtime tier
            for i in range(2000):
                await kb.insert_node(Node(label="TierTest", properties={"id": i}))
                
            print(f"✅ Runtime tier: {await kb.count_nodes(tier='runtime')} nodes")
            
            # Benchmark pruning
            start = time.perf_counter()
            pruned = await kb.prune(runtime_limit=500)
            end = time.perf_counter()
            
            prune_time = (end - start) * 1000
            prune_rate = pruned / (prune_time / 1000) if prune_time > 0 else float('inf')
            
            print(f"✅ Pruning: {prune_time:.2f}ms, moved {pruned} items ({prune_rate:.0f} items/sec)")
            print(f"✅ After pruning - Runtime: {await kb.count_nodes(tier='runtime')}, Store: {await kb.count_nodes(tier='store')}")
            
            # Benchmark cross-tier queries
            start = time.perf_counter()
            all_nodes = await kb.query_nodes(label="TierTest")
            end = time.perf_counter()
            
            cross_tier_query_time = (end - start) * 1000
            
            print(f"✅ Cross-tier query: {cross_tier_query_time:.2f}ms for {len(all_nodes.nodes)} nodes")
            
            self.results["storage_tiers"] = {
                "prune_time_ms": prune_time,
                "prune_rate_items_per_sec": prune_rate,
                "cross_tier_query_ms": cross_tier_query_time,
            }
            
    async def _benchmark_concurrent_operations(self):
        """Benchmark concurrent operations."""
        print("\n🔄 Concurrent Operations Benchmark")
        print("-" * 40)
        
        async with KnowledgeBase() as kb:
            # Concurrent node insertions
            async def insert_batch(batch_id: int, size: int):
                for i in range(size):
                    await kb.insert_node(Node(
                        label="ConcurrentTest",
                        properties={"batch": batch_id, "id": i}
                    ))
                    
            start = time.perf_counter()
            await asyncio.gather(*[
                insert_batch(i, 200) for i in range(10)  # 10 concurrent batches of 200
            ])
            end = time.perf_counter()
            
            concurrent_time = end - start
            concurrent_rate = 2000 / concurrent_time
            
            print(f"✅ Concurrent inserts (10 batches × 200): {concurrent_time:.2f}s ({concurrent_rate:.0f} ops/sec)")
            
            # Concurrent queries
            async def query_batch():
                return await kb.query_nodes(properties={"batch": 0})
                
            start = time.perf_counter()
            results = await asyncio.gather(*[query_batch() for _ in range(50)])
            end = time.perf_counter()
            
            concurrent_query_time = (end - start) * 1000
            
            print(f"✅ Concurrent queries (50 parallel): {concurrent_query_time:.2f}ms")
            print(f"✅ Each query returned: {len(results[0].nodes)} nodes")
            
            self.results["concurrent_operations"] = {
                "concurrent_insert_rate_ops_per_sec": concurrent_rate,
                "concurrent_query_time_ms": concurrent_query_time,
            }
            
    async def _benchmark_memory_usage(self):
        """Benchmark memory usage patterns."""
        print("\n💾 Memory Usage Benchmark")
        print("-" * 40)
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        async with KnowledgeBase() as kb:
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Add substantial data
            for i in range(10000):
                await kb.insert_node(Node(
                    label="MemoryTest",
                    properties={
                        "id": i,
                        "data": f"test_data_{i}" * 10,  # Some bulk data
                        "metadata": {"created": datetime.utcnow().isoformat()}
                    }
                ))
                
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Test pruning effect on memory
            await kb.prune(runtime_limit=1000)
            
            post_prune_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"✅ Initial memory: {initial_memory:.1f} MB")
            print(f"✅ Peak memory (10k nodes): {peak_memory:.1f} MB")
            print(f"✅ After pruning: {post_prune_memory:.1f} MB")
            print(f"✅ Memory per node: {(peak_memory - initial_memory) / 10000 * 1024:.1f} KB")
            
            self.results["memory_usage"] = {
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "post_prune_memory_mb": post_prune_memory,
                "memory_per_node_kb": (peak_memory - initial_memory) / 10000 * 1024,
            }
            
    async def _benchmark_scaling_characteristics(self):
        """Benchmark scaling with different data sizes."""
        print("\n📈 Scaling Characteristics Benchmark")
        print("-" * 40)
        
        data_sizes = [100, 500, 1000, 5000, 10000]
        scaling_results = {}
        
        for size in data_sizes:
            async with KnowledgeBase() as kb:
                # Insert data
                start = time.perf_counter()
                for i in range(size):
                    await kb.insert_node(Node(
                        label="ScaleTest",
                        properties={"id": i, "size": size}
                    ))
                insert_time = time.perf_counter() - start
                
                # Query data
                start = time.perf_counter()
                result = await kb.query_nodes(properties={"size": size})
                query_time = time.perf_counter() - start
                
                scaling_results[size] = {
                    "insert_time": insert_time,
                    "query_time": query_time,
                    "insert_rate": size / insert_time,
                    "query_rate": len(result.nodes) / query_time if query_time > 0 else float('inf')
                }
                
                print(f"✅ Size {size:5d}: Insert {insert_time:.3f}s ({size/insert_time:.0f} ops/sec), "
                      f"Query {query_time*1000:.1f}ms ({len(result.nodes)/query_time:.0f} results/sec)")
                
        self.results["scaling"] = scaling_results
        
    def print_industry_comparison(self):
        """Compare results against industry standards."""
        print("\n🏆 Industry Comparison")
        print("=" * 60)
        
        # Industry benchmarks (approximate values from public sources)
        industry_standards = {
            "neo4j_node_insert_ms": 0.1,  # Neo4j typical
            "redis_get_ms": 0.1,          # Redis typical
            "postgresql_insert_ms": 1.0,   # PostgreSQL typical
            "elasticsearch_query_ms": 10,  # Elasticsearch typical
            "sqlite_insert_ms": 0.5,      # SQLite typical
        }
        
        our_results = self.results.get("basic_operations", {})
        
        print("📊 Operation Latency Comparison:")
        print(f"  Momo KB node insert:     {our_results.get('node_insert_avg_ms', 0):.3f}ms")
        print(f"  Neo4j node insert:       {industry_standards['neo4j_node_insert_ms']:.3f}ms")
        print(f"  PostgreSQL insert:       {industry_standards['postgresql_insert_ms']:.3f}ms")
        print(f"  SQLite insert:           {industry_standards['sqlite_insert_ms']:.3f}ms")
        
        print(f"\n📊 Query Performance Comparison:")
        query_results = self.results.get("query_performance", {})
        print(f"  Momo KB query:           {query_results.get('label_query_avg_ms', 0):.3f}ms")
        print(f"  Redis GET:               {industry_standards['redis_get_ms']:.3f}ms")
        print(f"  Elasticsearch query:     {industry_standards['elasticsearch_query_ms']:.3f}ms")
        
        print(f"\n📊 Throughput Comparison:")
        bulk_results = self.results.get("bulk_operations", {})
        print(f"  Momo KB bulk insert:     {bulk_results.get('bulk_insert_rate_ops_per_sec', 0):.0f} ops/sec")
        print(f"  Typical graph DB:        ~1,000-10,000 ops/sec")
        print(f"  Typical document DB:     ~5,000-50,000 ops/sec")
        
        # Performance assessment
        node_insert_ms = our_results.get('node_insert_avg_ms', float('inf'))
        if node_insert_ms < 1.0:
            print("\n✅ EXCELLENT: Sub-millisecond node operations")
        elif node_insert_ms < 5.0:
            print("\n✅ GOOD: Low-latency operations")
        else:
            print("\n⚠️  NEEDS OPTIMIZATION: High operation latency")
            
        bulk_rate = bulk_results.get('bulk_insert_rate_ops_per_sec', 0)
        if bulk_rate > 5000:
            print("✅ EXCELLENT: High throughput bulk operations")
        elif bulk_rate > 1000:
            print("✅ GOOD: Decent bulk throughput")
        else:
            print("⚠️  NEEDS OPTIMIZATION: Low bulk throughput")


async def main():
    """Run comprehensive benchmarks."""
    runner = BenchmarkRunner()
    results = await runner.run_all_benchmarks()
    
    runner.print_industry_comparison()
    
    print(f"\n📋 Complete Results Summary:")
    print("=" * 60)
    for category, data in results.items():
        print(f"\n{category.upper()}:")
        for metric, value in data.items():
            if isinstance(value, float):
                print(f"  {metric}: {value:.3f}")
            else:
                print(f"  {metric}: {value}")


if __name__ == "__main__":
    asyncio.run(main())