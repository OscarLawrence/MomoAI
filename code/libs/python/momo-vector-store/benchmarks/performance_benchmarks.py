"""Performance benchmarks for vector store operations."""

import time
import asyncio
import statistics
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from momo_vector_store import VectorStoreManager


class BenchmarkEmbeddings(Embeddings):
    """Fast mock embeddings for benchmarking."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for documents."""
        import random

        return [[random.random() for _ in range(self.dimension)] for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for query."""
        import random

        return [random.random() for _ in range(self.dimension)]


def generate_test_documents(count: int) -> List[Document]:
    """Generate test documents for benchmarking."""
    documents = []
    categories = ["technology", "science", "programming", "ai", "data"]
    authors = ["Alice", "Bob", "Charlie", "Diana", "Eve"]

    for i in range(count):
        content = (
            f"This is test document number {i + 1}. "
            f"It contains information about topic {i % 10}. "
            f"The document discusses various aspects of the subject matter "
            f"and provides detailed insights for researchers and practitioners."
        )

        metadata = {
            "doc_id": f"doc_{i + 1:04d}",
            "category": categories[i % len(categories)],
            "author": authors[i % len(authors)],
            "size": len(content),
            "index": i,
        }

        documents.append(Document(page_content=content, metadata=metadata))

    return documents


async def benchmark_add_documents(
    manager: VectorStoreManager, documents: List[Document], batch_size: int = 100
) -> Dict[str, float]:
    """Benchmark document addition performance."""
    results = {}

    # Benchmark single document addition
    single_doc = documents[0]
    start_time = time.time()
    await manager.add_documents([single_doc])
    single_doc_time = time.time() - start_time
    results["single_document_ms"] = single_doc_time * 1000

    # Benchmark batch addition
    batches = [
        documents[i : i + batch_size] for i in range(0, len(documents), batch_size)
    ]
    batch_times = []

    for batch in batches:
        start_time = time.time()
        await manager.add_documents(batch)
        batch_time = time.time() - start_time
        batch_times.append(batch_time)

    results["batch_add_mean_ms"] = statistics.mean(batch_times) * 1000
    results["batch_add_std_ms"] = (
        statistics.stdev(batch_times) * 1000 if len(batch_times) > 1 else 0
    )
    results["docs_per_second"] = batch_size / statistics.mean(batch_times)

    return results


async def benchmark_similarity_search(
    manager: VectorStoreManager,
    queries: List[str],
    k_values: List[int] = [1, 5, 10, 20],
) -> Dict[str, Any]:
    """Benchmark similarity search performance."""
    results = {}

    for k in k_values:
        search_times = []

        for query in queries:
            start_time = time.time()
            await manager.similarity_search(query, k=k)
            search_time = time.time() - start_time
            search_times.append(search_time)

        results[f"search_k{k}_mean_ms"] = statistics.mean(search_times) * 1000
        results[f"search_k{k}_min_ms"] = min(search_times) * 1000
        results[f"search_k{k}_max_ms"] = max(search_times) * 1000
        results[f"search_k{k}_std_ms"] = (
            statistics.stdev(search_times) * 1000 if len(search_times) > 1 else 0
        )

    return results


async def benchmark_filtered_search(
    manager: VectorStoreManager, queries: List[str], filters: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Benchmark filtered search performance."""
    results = {}

    # Benchmark unfiltered search
    unfiltered_times = []
    for query in queries:
        start_time = time.time()
        await manager.similarity_search(query, k=10)
        search_time = time.time() - start_time
        unfiltered_times.append(search_time)

    results["unfiltered_mean_ms"] = statistics.mean(unfiltered_times) * 1000

    # Benchmark filtered search
    for filter_name, filter_dict in filters:
        filtered_times = []
        for query in queries:
            start_time = time.time()
            await manager.similarity_search(query, k=10, filter=filter_dict)
            search_time = time.time() - start_time
            filtered_times.append(search_time)

        results[f"filtered_{filter_name}_mean_ms"] = (
            statistics.mean(filtered_times) * 1000
        )

    return results


async def benchmark_concurrent_operations(
    manager: VectorStoreManager,
    documents: List[Document],
    queries: List[str],
    concurrency_levels: List[int] = [1, 2, 4, 8],
) -> Dict[str, Any]:
    """Benchmark concurrent operation performance."""
    results = {}

    for concurrency in concurrency_levels:
        # Benchmark concurrent searches
        search_tasks = []
        start_time = time.time()

        for i in range(concurrency):
            query = queries[i % len(queries)]
            task = manager.similarity_search(query, k=5)
            search_tasks.append(task)

        await asyncio.gather(*search_tasks)
        concurrent_search_time = time.time() - start_time

        results[f"concurrent_search_{concurrency}_total_ms"] = (
            concurrent_search_time * 1000
        )
        results[f"concurrent_search_{concurrency}_avg_ms"] = (
            concurrent_search_time / concurrency
        ) * 1000

    return results


async def benchmark_memory_usage():
    """Benchmark memory usage patterns."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    embeddings = BenchmarkEmbeddings()
    manager = VectorStoreManager.create("memory", embeddings)

    memory_usage = {"initial_mb": initial_memory}

    # Memory usage after manager creation
    after_creation = process.memory_info().rss / 1024 / 1024
    memory_usage["after_creation_mb"] = after_creation

    # Memory usage after adding documents
    documents = generate_test_documents(1000)
    await manager.add_documents(documents)

    after_documents = process.memory_info().rss / 1024 / 1024
    memory_usage["after_1k_docs_mb"] = after_documents
    memory_usage["memory_per_doc_kb"] = (
        (after_documents - after_creation) * 1024
    ) / len(documents)

    return memory_usage


async def run_comprehensive_benchmark() -> Dict[str, Any]:
    """Run comprehensive performance benchmark."""
    print("🚀 Starting momo-vector-store performance benchmarks...")

    # Initialize
    embeddings = BenchmarkEmbeddings()
    manager = VectorStoreManager.create("memory", embeddings)

    # Generate test data
    print("📊 Generating test data...")
    small_docs = generate_test_documents(100)
    medium_docs = generate_test_documents(1000)
    large_docs = generate_test_documents(5000)

    test_queries = [
        "artificial intelligence and machine learning",
        "data science programming techniques",
        "vector database similarity search",
        "natural language processing models",
        "software development best practices",
    ]

    filters = [
        ("category_tech", {"category": "technology"}),
        ("author_alice", {"author": "Alice"}),
        ("category_ai", {"category": "ai"}),
    ]

    benchmark_results = {}

    # 1. Document Addition Benchmarks
    print("📥 Benchmarking document addition...")
    manager_small = VectorStoreManager.create("memory", embeddings)
    add_results = await benchmark_add_documents(manager_small, small_docs[:50])
    benchmark_results["document_addition"] = add_results

    # 2. Similarity Search Benchmarks
    print("🔍 Benchmarking similarity search...")
    manager_medium = VectorStoreManager.create("memory", embeddings)
    await manager_medium.add_documents(medium_docs)
    search_results = await benchmark_similarity_search(manager_medium, test_queries)
    benchmark_results["similarity_search"] = search_results

    # 3. Filtered Search Benchmarks
    print("🎯 Benchmarking filtered search...")
    filtered_results = await benchmark_filtered_search(
        manager_medium, test_queries[:3], filters
    )
    benchmark_results["filtered_search"] = filtered_results

    # 4. Concurrent Operations Benchmarks
    print("⚡ Benchmarking concurrent operations...")
    concurrent_results = await benchmark_concurrent_operations(
        manager_medium, medium_docs[:100], test_queries
    )
    benchmark_results["concurrent_operations"] = concurrent_results

    # 5. Memory Usage Benchmarks
    print("💾 Benchmarking memory usage...")
    memory_results = await benchmark_memory_usage()
    benchmark_results["memory_usage"] = memory_results

    # 6. Scalability Test
    print("📈 Testing scalability...")
    scalability_results = {}

    for doc_count in [100, 500, 1000, 2000]:
        manager_scale = VectorStoreManager.create("memory", embeddings)
        test_docs = generate_test_documents(doc_count)

        # Time document addition
        start_time = time.time()
        await manager_scale.add_documents(test_docs)
        add_time = time.time() - start_time

        # Time search operations
        search_times = []
        for query in test_queries[:3]:
            start_time = time.time()
            await manager_scale.similarity_search(query, k=10)
            search_time = time.time() - start_time
            search_times.append(search_time)

        scalability_results[f"docs_{doc_count}"] = {
            "add_time_ms": add_time * 1000,
            "avg_search_ms": statistics.mean(search_times) * 1000,
            "docs_per_second": doc_count / add_time,
        }

    benchmark_results["scalability"] = scalability_results

    return benchmark_results


def print_benchmark_results(results: Dict[str, Any]):
    """Print formatted benchmark results."""
    print("\n" + "=" * 60)
    print("📈 MOMO VECTOR STORE PERFORMANCE BENCHMARK RESULTS")
    print("=" * 60)

    # Document Addition Results
    if "document_addition" in results:
        print(f"\n📥 Document Addition Performance:")
        add_results = results["document_addition"]
        print(f"  Single document: {add_results['single_document_ms']:.2f}ms")
        print(f"  Batch addition (mean): {add_results['batch_add_mean_ms']:.2f}ms")
        print(f"  Documents per second: {add_results['docs_per_second']:.1f}")

    # Similarity Search Results
    if "similarity_search" in results:
        print(f"\n🔍 Similarity Search Performance:")
        search_results = results["similarity_search"]
        for key, value in search_results.items():
            if "mean_ms" in key:
                k_value = key.split("_")[1]
                print(f"  {k_value} results: {value:.2f}ms (avg)")

    # Filtered Search Results
    if "filtered_search" in results:
        print(f"\n🎯 Filtered Search Performance:")
        filter_results = results["filtered_search"]
        print(f"  Unfiltered: {filter_results['unfiltered_mean_ms']:.2f}ms")
        for key, value in filter_results.items():
            if "filtered_" in key and "mean_ms" in key:
                filter_name = key.replace("filtered_", "").replace("_mean_ms", "")
                print(f"  {filter_name}: {value:.2f}ms")

    # Memory Usage Results
    if "memory_usage" in results:
        print(f"\n💾 Memory Usage:")
        mem_results = results["memory_usage"]
        print(f"  Initial: {mem_results['initial_mb']:.1f}MB")
        print(f"  After 1K documents: {mem_results['after_1k_docs_mb']:.1f}MB")
        print(f"  Memory per document: {mem_results['memory_per_doc_kb']:.2f}KB")

    # Scalability Results
    if "scalability" in results:
        print(f"\n📈 Scalability Performance:")
        scale_results = results["scalability"]
        for doc_count, metrics in scale_results.items():
            count = doc_count.replace("docs_", "")
            print(
                f"  {count} docs: {metrics['add_time_ms']:.0f}ms add, "
                f"{metrics['avg_search_ms']:.2f}ms search, "
                f"{metrics['docs_per_second']:.1f} docs/sec"
            )

    print("\n" + "=" * 60)


async def main():
    """Run the benchmark suite."""
    results = await run_comprehensive_benchmark()
    print_benchmark_results(results)

    # Save results to file
    import json

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to benchmark_results.json")
    print("✅ Benchmark complete!")


if __name__ == "__main__":
    asyncio.run(main())
