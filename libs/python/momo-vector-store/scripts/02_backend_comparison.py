"""
Backend comparison example for momo-vector-store.

This script demonstrates:
- Creating different backend types
- Comparing their configurations
- Understanding backend-specific features
- Error handling for unavailable backends
"""

import asyncio
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from momo_vector_store import VectorStore
from momo_vector_store.exceptions import BackendError


class ComparisonEmbeddings(Embeddings):
    """Consistent embeddings for backend comparison."""

    def embed_documents(self, texts):
        """Generate consistent embeddings for fair comparison."""
        embeddings = []
        for i, text in enumerate(texts):
            # Create deterministic embeddings based on text content
            words = text.lower().split()

            # Simple bag-of-words style embedding
            embedding = [0.0] * 10
            for j, word in enumerate(words[:10]):
                embedding[j] = hash(word) % 100 / 100.0

            embeddings.append(embedding)

        return embeddings

    def embed_query(self, text):
        """Generate consistent query embedding."""
        return self.embed_documents([text])[0]


async def demonstrate_memory_backend():
    """Demonstrate InMemory backend capabilities."""
    print("\n🧠 InMemory Backend Demonstration")
    print("-" * 40)

    embeddings = ComparisonEmbeddings()

    # Create InMemory backend
    store = VectorStore(backend_type="memory", embeddings=embeddings)
    backend_info = store.get_info()

    print(f"Backend Type: {backend_info['backend']['backend_type']}")
    print(f"Backend Module: {backend_info['backend']['backend_module']}")

    # Add sample documents
    sample_docs = [
        Document(
            page_content="InMemory backends are fast but ephemeral.",
            metadata={"backend": "memory", "persistence": "none"},
        ),
        Document(
            page_content="Memory storage is ideal for development and testing.",
            metadata={"backend": "memory", "use_case": "development"},
        ),
    ]

    doc_ids = await store.add_documents(sample_docs)
    print(f"Added {len(doc_ids)} documents")

    # Test search performance
    import time

    start_time = time.time()
    results = await store.search("memory storage", k=2)
    search_time = (time.time() - start_time) * 1000

    print(f"Search completed in {search_time:.2f}ms")
    print("Characteristics:")
    print("  ✅ Very fast operations")
    print("  ✅ No external dependencies")
    print("  ❌ No persistence (data lost on restart)")
    print("  ❌ Limited by available RAM")

    return store


async def demonstrate_chroma_backend():
    """Demonstrate Chroma backend (if available)."""
    print("\n🔵 Chroma Backend Demonstration")
    print("-" * 40)

    embeddings = ComparisonEmbeddings()

    try:
        # Try to create Chroma backend
        store = VectorStore(
            backend_type="chroma",
            embeddings=embeddings,
            collection_name="momo_demo",
            persist_directory="./chroma_demo_db",
        )

        backend_info = store.get_info()
        print(f"Backend Type: {backend_info['backend']['backend_type']}")

        # Add documents
        chroma_docs = [
            Document(
                page_content="Chroma is an AI-native vector database.",
                metadata={"backend": "chroma", "persistence": "file"},
            ),
            Document(
                page_content="Chroma supports both in-memory and persistent storage.",
                metadata={"backend": "chroma", "feature": "flexible_storage"},
            ),
        ]

        doc_ids = await store.add_documents(chroma_docs)
        print(f"Added {len(doc_ids)} documents")

        # Test search
        results = await store.search("vector database", k=2)
        print(f"Found {len(results)} search results")

        print("Characteristics:")
        print("  ✅ Persistent storage")
        print("  ✅ AI-native design")
        print("  ✅ Good for production workloads")
        print("  ❌ Additional dependency required")

        return store

    except BackendError as e:
        print(f"❌ Chroma backend not available: {e.message}")
        print("To use Chroma backend, install: pip install langchain-chroma")
        print("Characteristics (when available):")
        print("  ✅ Persistent storage")
        print("  ✅ Optimized for embeddings")
        print("  ✅ Apache 2.0 license")
        print("  ❌ Requires additional installation")

        return None


async def demonstrate_weaviate_backend():
    """Demonstrate Weaviate backend (if available)."""
    print("\n🟠 Weaviate Backend Demonstration")
    print("-" * 40)

    embeddings = ComparisonEmbeddings()

    try:
        # Try to create Weaviate backend
        store = VectorStore(
            backend_type="weaviate",
            embeddings=embeddings,
            url="http://localhost:8080",
            index_name="MomoDemo",
        )

        backend_info = store.get_info()
        print(f"Backend Type: {backend_info['backend']['backend_type']}")

        # This would typically fail unless Weaviate server is running
        print("✅ Weaviate backend created successfully")
        print("Characteristics:")
        print("  ✅ Enterprise-scale performance")
        print("  ✅ GraphQL API")
        print("  ✅ Built-in ML model integrations")
        print("  ❌ Requires running Weaviate server")

        return store

    except BackendError as e:
        print(f"❌ Weaviate backend not available: {e.message}")
        print("To use Weaviate:")
        print("  1. Install: pip install langchain-weaviate")
        print("  2. Run Weaviate server (Docker, cloud, or local)")
        print("Characteristics (when available):")
        print("  ✅ Scales to billions of objects")
        print("  ✅ Sub-millisecond search")
        print("  ✅ Distributed architecture")
        print("  ❌ Requires server setup")

        return None


async def compare_backend_performance():
    """Compare performance across available backends."""
    print("\n⚡ Backend Performance Comparison")
    print("-" * 40)

    embeddings = ComparisonEmbeddings()

    # Test documents
    test_docs = []
    for i in range(100):
        doc = Document(
            page_content=f"Performance test document number {i+1}. "
            f"This document contains test content for benchmarking "
            f"vector store operations across different backends.",
            metadata={"test_id": i + 1, "batch": "performance_test"},
        )
        test_docs.append(doc)

    test_queries = [
        "performance test document",
        "benchmarking vector store",
        "test content operations",
    ]

    backends_to_test = ["memory"]

    results = {}

    for backend_name in backends_to_test:
        print(f"\n📊 Testing {backend_name} backend:")

        try:
            if backend_name == "memory":
                store = VectorStore(backend_type="memory", embeddings=embeddings)
            else:
                continue  # Skip unavailable backends

            import time

            # Time document addition
            start_time = time.time()
            await store.add_documents(test_docs)
            add_time = (time.time() - start_time) * 1000

            # Time search operations
            search_times = []
            for query in test_queries:
                start_time = time.time()
                await store.search(query, k=10)
                search_time = (time.time() - start_time) * 1000
                search_times.append(search_time)

            avg_search_time = sum(search_times) / len(search_times)

            results[backend_name] = {
                "add_time_ms": add_time,
                "avg_search_time_ms": avg_search_time,
                "docs_per_second": len(test_docs) / (add_time / 1000),
            }

            print(f"  Document addition: {add_time:.1f}ms")
            print(f"  Average search: {avg_search_time:.2f}ms")
            print(
                f"  Throughput: {results[backend_name]['docs_per_second']:.1f} docs/sec"
            )

        except Exception as e:
            print(f"  ❌ Error testing {backend_name}: {e}")

    return results


async def demonstrate_backend_switching():
    """Demonstrate switching between backends."""
    print("\n🔄 Backend Switching Demonstration")
    print("-" * 40)

    embeddings = ComparisonEmbeddings()

    # Same documents, different backends
    shared_docs = [
        Document(
            page_content="This document exists in multiple backends.",
            metadata={"shared": True, "test": "switching"},
        ),
        Document(
            page_content="Backend switching maintains the same API.",
            metadata={"shared": True, "feature": "compatibility"},
        ),
    ]

    # Create multiple stores with different backends
    stores = {}

    # InMemory backend (always available)
    stores["memory"] = VectorStore(backend_type="memory", embeddings=embeddings)
    await stores["memory"].add_documents(shared_docs)

    print("✅ Created InMemory backend")

    # Test that same query works across backends
    query = "backend switching"

    for backend_name, store in stores.items():
        results = await store.search(query, k=1)
        backend_info = store.get_info()

        print(f"📍 {backend_name} backend ({backend_info['backend']['backend_type']}):")
        if results:
            print(f"   Found: {results[0].page_content[:50]}...")
        else:
            print("   No results found")

    print("\n🎯 Key Insight: Same API works across all backends!")


async def backend_configuration_examples():
    """Show different configuration options."""
    print("\n⚙️  Backend Configuration Examples")
    print("-" * 40)

    embeddings = ComparisonEmbeddings()

    print("Memory backend (with defaults - no configuration needed):")
    print("  store = VectorStore()  # Uses memory + LocalEmbeddings automatically")
    print("  # Or explicit:")
    print("  store = VectorStore(backend_type='memory', embeddings=embeddings)")

    print("\nChroma backend configurations:")
    print("  # In-memory Chroma:")
    print("  store = VectorStore(backend_type='chroma', embeddings=embeddings)")
    print("  # Persistent Chroma:")
    print("  store = VectorStore(")
    print("      backend_type='chroma', embeddings=embeddings,")
    print("      collection_name='my_collection',")
    print("      persist_directory='./chroma_db'")
    print("  )")

    print("\nWeaviate backend configurations:")
    print("  # Local Weaviate:")
    print("  store = VectorStore(")
    print("      backend_type='weaviate', embeddings=embeddings,")
    print("      url='http://localhost:8080',")
    print("      index_name='MyIndex'")
    print("  )")
    print("  # Cloud Weaviate:")
    print("  store = VectorStore(")
    print("      backend_type='weaviate', embeddings=embeddings,")
    print("      url='https://my-cluster.weaviate.network',")
    print("      api_key='your-api-key'")
    print("  )")


async def main():
    """Run the backend comparison demonstration."""
    print("🏢 Vector Store Backend Comparison")
    print("=" * 50)

    # Demonstrate each backend
    memory_store = await demonstrate_memory_backend()
    chroma_store = await demonstrate_chroma_backend()
    weaviate_store = await demonstrate_weaviate_backend()

    # Compare performance
    performance_results = await compare_backend_performance()

    # Demonstrate switching
    await demonstrate_backend_switching()

    # Show configuration examples
    await backend_configuration_examples()

    print("\n✅ Backend comparison completed!")
    print("\nSummary:")
    print("- InMemory: Fast, simple, ephemeral (great for development)")
    print("- Chroma: Persistent, AI-native (good for production)")
    print("- Weaviate: Enterprise-scale, feature-rich (best for large systems)")
    print("- All backends share the same VectorStore API")


if __name__ == "__main__":
    asyncio.run(main())
