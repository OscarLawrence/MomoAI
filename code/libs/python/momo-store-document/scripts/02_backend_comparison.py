#!/usr/bin/env python3
"""
Backend Comparison Example - InMemory vs DuckDB

This example demonstrates:
- How to use different storage backends
- Performance differences between backends
- When to choose which backend
"""

import asyncio
import time
from momo_kb import Document, DocumentMetadata, KnowledgeBase, CoreKnowledgeBase
from momo_logger import get_logger


def create_sample_documents(count: int = 100):
    """Create sample documents for testing."""
    documents = []
    topics = [
        "python",
        "javascript",
        "machine learning",
        "data science",
        "web development",
    ]

    for i in range(count):
        topic = topics[i % len(topics)]
        doc = Document(
            content=f"Document {i}: This is about {topic}. "
            * 10,  # Make it substantial
            metadata=DocumentMetadata(
                source=f"source_{i % 5}",
                category=topic.replace(" ", "_"),
                tags=[topic, f"tag_{i % 3}"],
                custom={
                    "priority": i % 3,
                    "level": ["beginner", "intermediate", "advanced"][i % 3],
                },
            ),
        )
        documents.append(doc)

    return documents


async def benchmark_backend(backend_name: str, kb, documents, logger):
    """Benchmark a specific backend."""
    await logger.ai_user(f"\n🔧 Testing {backend_name} Backend", user_facing=True)
    await logger.ai_user("-" * 40, user_facing=True)

    # Test insertion speed
    start_time = time.time()
    doc_ids = await kb.save(*documents)
    insert_time = time.time() - start_time

    await logger.info(
        f"Inserted {len(documents)} documents in {insert_time:.3f}s using {backend_name} backend"
    )
    await logger.ai_user(
        f"📝 Inserted {len(documents)} documents in {insert_time:.3f}s",
        user_facing=True,
    )
    await logger.ai_user(
        f"⚡ Speed: {len(documents)/insert_time:.1f} docs/second", user_facing=True
    )

    # Test search speed
    search_times = []
    search_queries = ["python", "machine learning", "javascript", "data science"]

    for query in search_queries:
        start_time = time.time()
        results = await kb.search(query)
        search_time = time.time() - start_time
        search_times.append(search_time)
        await logger.debug(
            f"Search '{query}' completed in {search_time*1000:.1f}ms with {len(results)} results"
        )
        await logger.ai_user(
            f"🔍 Search '{query}': {search_time*1000:.1f}ms ({len(results)} results)",
            user_facing=True,
        )

    avg_search_time = sum(search_times) / len(search_times)
    await logger.info(
        f"Average search time for {backend_name}: {avg_search_time*1000:.1f}ms"
    )
    await logger.ai_user(
        f"📊 Average search time: {avg_search_time*1000:.1f}ms", user_facing=True
    )

    # Test retrieval speed
    start_time = time.time()
    doc = await kb.get(doc_ids[0])
    retrieval_time = time.time() - start_time
    await logger.debug(f"Document retrieval took {retrieval_time*1000:.1f}ms")
    await logger.ai_user(
        f"📖 Document retrieval: {retrieval_time*1000:.1f}ms", user_facing=True
    )

    # Test count operation
    start_time = time.time()
    total = await kb.count()
    count_time = time.time() - start_time
    await logger.debug(
        f"Count operation took {count_time*1000:.1f}ms, found {total} documents"
    )
    await logger.ai_user(
        f"🔢 Count operation: {count_time*1000:.1f}ms (found {total} docs)",
        user_facing=True,
    )

    return {
        "insert_time": insert_time,
        "avg_search_time": avg_search_time,
        "retrieval_time": retrieval_time,
        "count_time": count_time,
    }


async def main():
    logger = get_logger("momo.kb.example.comparison")

    await logger.ai_user("🧠 Momo KnowledgeBase - Backend Comparison", user_facing=True)
    await logger.ai_user("=" * 50, user_facing=True)

    # Create sample documents
    await logger.ai_user("📄 Creating sample documents...", user_facing=True)
    documents = create_sample_documents(100)
    await logger.info(f"Created {len(documents)} sample documents for benchmarking")
    await logger.ai_user(
        f"✅ Created {len(documents)} sample documents", user_facing=True
    )

    # Test InMemory Backend
    await logger.ai_user("\n" + "=" * 50, user_facing=True)
    inmemory_kb = KnowledgeBase()  # Default is all in-memory

    async with inmemory_kb:
        inmemory_stats = await benchmark_backend(
            "InMemory", inmemory_kb, documents, logger
        )

    # Test DuckDB Backend
    await logger.ai_user("\n" + "=" * 50, user_facing=True)
    duckdb_kb = CoreKnowledgeBase(
        document_backend="duckdb"  # String-based configuration
    )

    async with duckdb_kb:
        duckdb_stats = await benchmark_backend("DuckDB", duckdb_kb, documents, logger)

    # Compare results
    await logger.ai_user("\n" + "=" * 50, user_facing=True)
    await logger.ai_user("📊 PERFORMANCE COMPARISON", user_facing=True)
    await logger.ai_user("=" * 50, user_facing=True)

    await logger.ai_user(
        f"{'Metric':<20} {'InMemory':<15} {'DuckDB':<15} {'Winner'}", user_facing=True
    )
    await logger.ai_user("-" * 65, user_facing=True)

    # Insert speed comparison
    inmem_insert_rate = len(documents) / inmemory_stats["insert_time"]
    duckdb_insert_rate = len(documents) / duckdb_stats["insert_time"]
    insert_winner = "InMemory" if inmem_insert_rate > duckdb_insert_rate else "DuckDB"
    await logger.info(
        f"Insert speed comparison: InMemory {inmem_insert_rate:.1f} docs/s vs DuckDB {duckdb_insert_rate:.1f} docs/s, winner: {insert_winner}"
    )
    await logger.ai_user(
        f"{'Insert Speed':<20} {inmem_insert_rate:<10.1f} docs/s {duckdb_insert_rate:<10.1f} docs/s {insert_winner}",
        user_facing=True,
    )

    # Search speed comparison
    inmem_search = inmemory_stats["avg_search_time"] * 1000
    duckdb_search = duckdb_stats["avg_search_time"] * 1000
    search_winner = "InMemory" if inmem_search < duckdb_search else "DuckDB"
    await logger.info(
        f"Search speed comparison: InMemory {inmem_search:.1f}ms vs DuckDB {duckdb_search:.1f}ms, winner: {search_winner}"
    )
    await logger.ai_user(
        f"{'Search Speed':<20} {inmem_search:<10.1f} ms    {duckdb_search:<10.1f} ms    {search_winner}",
        user_facing=True,
    )

    # Retrieval speed comparison
    inmem_retrieval = inmemory_stats["retrieval_time"] * 1000
    duckdb_retrieval = duckdb_stats["retrieval_time"] * 1000
    retrieval_winner = "InMemory" if inmem_retrieval < duckdb_retrieval else "DuckDB"
    await logger.info(
        f"Retrieval speed comparison: InMemory {inmem_retrieval:.1f}ms vs DuckDB {duckdb_retrieval:.1f}ms, winner: {retrieval_winner}"
    )
    await logger.ai_user(
        f"{'Retrieval Speed':<20} {inmem_retrieval:<10.1f} ms    {duckdb_retrieval:<10.1f} ms    {retrieval_winner}",
        user_facing=True,
    )

    await logger.ai_user("\n💡 RECOMMENDATIONS:", user_facing=True)
    await logger.ai_user("🔹 InMemory Backend:", user_facing=True)
    await logger.ai_user(
        "   • Best for: Small datasets (< 10K documents)", user_facing=True
    )
    await logger.ai_user(
        "   • Pros: Fastest search and retrieval, simple setup", user_facing=True
    )
    await logger.ai_user("   • Cons: No persistence, memory limited", user_facing=True)

    await logger.ai_user("\n🔹 DuckDB Backend:", user_facing=True)
    await logger.ai_user(
        "   • Best for: Large datasets (> 10K documents)", user_facing=True
    )
    await logger.ai_user(
        "   • Pros: Persistent storage, handles large datasets, SQL analytics",
        user_facing=True,
    )
    await logger.ai_user(
        "   • Cons: Slightly slower for small operations", user_facing=True
    )

    await logger.ai_user("\n🎉 Backend comparison completed!", user_facing=True)


if __name__ == "__main__":
    asyncio.run(main())
