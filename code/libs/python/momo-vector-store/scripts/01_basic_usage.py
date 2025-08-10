"""
Basic usage example for momo-vector-store.

This script demonstrates the fundamental operations of the vector store:
- Creating a VectorStore with defaults
- Adding documents and texts
- Performing similarity searches
- Using metadata filters
"""

import asyncio
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from momo_vector_store import VectorStore


class DemoEmbeddings(Embeddings):
    """Demo embeddings that create simple numerical vectors."""

    def embed_documents(self, texts):
        """Create embeddings for documents based on text length and content."""
        embeddings = []
        for text in texts:
            # Simple embedding based on text characteristics
            length_factor = len(text) / 100
            word_count = len(text.split())
            char_sum = sum(ord(c) for c in text[:10]) / 1000

            embedding = [length_factor, word_count / 10, char_sum]
            embeddings.append(embedding)

        return embeddings

    def embed_query(self, text):
        """Create embedding for a single query."""
        return self.embed_documents([text])[0]


async def basic_usage_example():
    """Demonstrate basic vector store usage."""
    print("🚀 Basic Vector Store Usage Example")
    print("=" * 40)

    # 1. Initialize the vector store
    print("\n1. Creating VectorStore with defaults...")
    embeddings = DemoEmbeddings()
    store = VectorStore(backend_type="memory", embeddings=embeddings)

    # Check backend info
    backend_info = store.get_info()
    print(f"   Backend: {backend_info['backend']['backend_type']}")

    # 2. Create sample documents
    print("\n2. Preparing sample documents...")
    documents = [
        Document(
            page_content="Python is a versatile programming language used for web development, data science, and automation.",
            metadata={
                "topic": "programming",
                "language": "python",
                "difficulty": "beginner",
            },
        ),
        Document(
            page_content="Machine learning algorithms can analyze large datasets to discover patterns and make predictions.",
            metadata={
                "topic": "ai",
                "difficulty": "intermediate",
                "field": "data_science",
            },
        ),
        Document(
            page_content="Vector databases enable semantic search by storing and querying high-dimensional embeddings.",
            metadata={"topic": "databases", "type": "vector", "difficulty": "advanced"},
        ),
        Document(
            page_content="Natural language processing helps computers understand and generate human language.",
            metadata={"topic": "ai", "subtopic": "nlp", "difficulty": "intermediate"},
        ),
        Document(
            page_content="Web scraping techniques allow extraction of data from websites using Python libraries.",
            metadata={
                "topic": "programming",
                "language": "python",
                "difficulty": "intermediate",
            },
        ),
    ]

    print(f"   Created {len(documents)} sample documents")

    # 3. Add documents to the vector store
    print("\n3. Adding documents to vector store...")
    doc_ids = await store.add_documents(documents)
    print(f"   Added documents with IDs: {doc_ids}")

    # 4. Perform similarity searches
    print("\n4. Performing similarity searches...")

    # Basic similarity search
    print("\n   🔍 Search: 'python programming'")
    results = await store.search("python programming", k=3)

    for i, doc in enumerate(results, 1):
        print(f"   Result {i}:")
        print(f"     Content: {doc.page_content[:80]}...")
        print(f"     Metadata: {doc.metadata}")

    # Search with different query
    print("\n   🔍 Search: 'artificial intelligence machine learning'")
    ai_results = await store.search("artificial intelligence machine learning", k=2)

    for i, doc in enumerate(ai_results, 1):
        print(f"   Result {i}: {doc.page_content[:60]}...")

    # 5. Similarity search with scores
    print("\n5. Similarity search with relevance scores...")
    print("\n   🎯 Search with scores: 'database vector search'")

    scored_results = await store.search_with_score("database vector search", k=3)

    for i, (doc, score) in enumerate(scored_results, 1):
        print(f"   Result {i} (score: {score:.3f}):")
        print(f"     {doc.page_content[:70]}...")

    # 6. Filtered searches
    print("\n6. Filtered searches...")

    # Filter by topic
    print("\n   🎯 Filter by topic='ai':")
    ai_docs = await store.search("learning algorithms", k=5, filter={"topic": "ai"})

    for doc in ai_docs:
        print(f"     Topic: {doc.metadata.get('topic')} - {doc.page_content[:50]}...")

    # Filter by difficulty
    print("\n   🎯 Filter by difficulty='intermediate':")
    intermediate_docs = await store.search(
        "programming techniques", k=5, filter={"difficulty": "intermediate"}
    )

    for doc in intermediate_docs:
        difficulty = doc.metadata.get("difficulty", "unknown")
        print(f"     Difficulty: {difficulty} - {doc.page_content[:50]}...")

    # 7. Adding individual texts
    print("\n7. Adding individual texts...")

    new_texts = [
        "Deep learning uses neural networks with multiple layers to process data.",
        "React is a popular JavaScript library for building user interfaces.",
        "Docker containers provide lightweight virtualization for applications.",
    ]

    new_metadata = [
        {"topic": "ai", "subtopic": "deep_learning", "difficulty": "advanced"},
        {"topic": "programming", "language": "javascript", "difficulty": "beginner"},
        {"topic": "devops", "tool": "docker", "difficulty": "intermediate"},
    ]

    text_ids = await store.add_texts(new_texts, new_metadata)
    print(f"   Added texts with IDs: {text_ids}")

    # Search the expanded dataset
    print("\n   🔍 Search in expanded dataset: 'javascript frontend'")
    frontend_results = await store.search("javascript frontend", k=2)

    for doc in frontend_results:
        print(f"     {doc.page_content}")

    print("\n✅ Basic usage example completed!")
    print("\nKey takeaways:")
    print("- VectorStore provides a simple interface with sensible defaults")
    print("- Documents can be added individually or in batches")
    print("- Similarity search finds semantically related content")
    print("- Metadata filters enable precise content targeting")
    print("- Both documents and raw texts can be added to the store")


if __name__ == "__main__":
    asyncio.run(basic_usage_example())
