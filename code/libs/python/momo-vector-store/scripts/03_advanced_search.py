"""
Advanced search techniques with momo-vector-store.

This script demonstrates:
- Complex metadata filtering
- Search result ranking and scoring
- Advanced query strategies
- Custom search parameters
"""

import asyncio
from typing import List, Tuple
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from momo_vector_store import VectorStore


class AdvancedEmbeddings(Embeddings):
    """Advanced embeddings that capture more semantic information."""

    def __init__(self):
        # Keyword weights for semantic understanding
        self.keyword_weights = {
            "python": [0.8, 0.2, 0.1, 0.3, 0.6],
            "javascript": [0.1, 0.8, 0.2, 0.4, 0.5],
            "ai": [0.9, 0.7, 0.8, 0.2, 0.1],
            "machine": [0.9, 0.6, 0.8, 0.3, 0.2],
            "learning": [0.8, 0.7, 0.9, 0.2, 0.1],
            "database": [0.3, 0.4, 0.2, 0.9, 0.8],
            "vector": [0.4, 0.3, 0.5, 0.8, 0.9],
            "search": [0.2, 0.5, 0.3, 0.7, 0.8],
            "web": [0.2, 0.6, 0.1, 0.5, 0.4],
            "data": [0.5, 0.4, 0.6, 0.8, 0.7],
        }

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate semantic embeddings based on content analysis."""
        embeddings = []

        for text in texts:
            words = text.lower().split()

            # Base embedding
            embedding = [0.1, 0.1, 0.1, 0.1, 0.1]

            # Apply keyword weights
            for word in words:
                if word in self.keyword_weights:
                    weights = self.keyword_weights[word]
                    for i in range(len(embedding)):
                        embedding[i] += weights[i] * 0.2

            # Normalize
            max_val = max(embedding)
            if max_val > 0:
                embedding = [x / max_val for x in embedding]

            embeddings.append(embedding)

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Generate query embedding."""
        return self.embed_documents([text])[0]


async def setup_advanced_dataset():
    """Create a comprehensive dataset for advanced search demos."""
    documents = [
        # Programming languages
        Document(
            page_content="Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, artificial intelligence, and automation.",
            metadata={
                "category": "programming",
                "language": "python",
                "difficulty": "beginner",
                "topics": ["web", "data", "ai", "automation"],
                "popularity": 9.5,
                "year_created": 1991,
                "paradigm": "multi-paradigm",
            },
        ),
        Document(
            page_content="JavaScript is a dynamic programming language that enables interactive web pages and is essential for web development. It runs in browsers and servers through Node.js.",
            metadata={
                "category": "programming",
                "language": "javascript",
                "difficulty": "intermediate",
                "topics": ["web", "frontend", "backend"],
                "popularity": 9.2,
                "year_created": 1995,
                "paradigm": "multi-paradigm",
            },
        ),
        # AI and Machine Learning
        Document(
            page_content="Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to find patterns in data.",
            metadata={
                "category": "ai",
                "subcategory": "machine_learning",
                "difficulty": "intermediate",
                "topics": ["algorithms", "data", "patterns"],
                "applications": ["prediction", "classification", "clustering"],
                "maturity": "established",
            },
        ),
        Document(
            page_content="Deep learning uses artificial neural networks with multiple layers to model and understand complex patterns in large amounts of data. It's particularly effective for image recognition and natural language processing.",
            metadata={
                "category": "ai",
                "subcategory": "deep_learning",
                "difficulty": "advanced",
                "topics": ["neural_networks", "images", "nlp"],
                "applications": ["computer_vision", "speech", "translation"],
                "maturity": "cutting_edge",
            },
        ),
        # Database technologies
        Document(
            page_content="Vector databases store high-dimensional vectors and enable fast similarity search. They're essential for AI applications like semantic search, recommendation systems, and retrieval-augmented generation.",
            metadata={
                "category": "database",
                "type": "vector",
                "difficulty": "advanced",
                "topics": ["vectors", "similarity", "search"],
                "use_cases": ["semantic_search", "recommendations", "rag"],
                "performance": "high",
            },
        ),
        Document(
            page_content="PostgreSQL is a powerful, open-source relational database management system known for its reliability, feature robustness, and performance. It supports both SQL and JSON querying.",
            metadata={
                "category": "database",
                "type": "relational",
                "difficulty": "intermediate",
                "topics": ["sql", "json", "transactions"],
                "use_cases": ["web_apps", "analytics", "enterprise"],
                "performance": "high",
            },
        ),
        # Web technologies
        Document(
            page_content="React is a JavaScript library for building user interfaces, particularly web applications. It uses a component-based architecture and virtual DOM for efficient updates.",
            metadata={
                "category": "web",
                "type": "frontend",
                "difficulty": "intermediate",
                "topics": ["components", "dom", "ui"],
                "framework_type": "library",
                "backed_by": "Meta",
            },
        ),
        Document(
            page_content="REST APIs provide a standardized way for applications to communicate over HTTP. They use standard HTTP methods and are stateless, making them scalable and easy to understand.",
            metadata={
                "category": "web",
                "type": "api",
                "difficulty": "intermediate",
                "topics": ["http", "stateless", "scalable"],
                "architecture": "stateless",
                "protocol": "http",
            },
        ),
        # Data Science
        Document(
            page_content="Data visualization transforms complex datasets into clear, intuitive visual representations. It helps identify patterns, trends, and insights that might be missed in raw data.",
            metadata={
                "category": "data_science",
                "subcategory": "visualization",
                "difficulty": "beginner",
                "topics": ["patterns", "trends", "insights"],
                "tools": ["matplotlib", "d3", "tableau"],
                "importance": "critical",
            },
        ),
        Document(
            page_content="Statistical analysis involves collecting, organizing, analyzing, and interpreting data to discover patterns and trends. It forms the foundation of data-driven decision making.",
            metadata={
                "category": "data_science",
                "subcategory": "statistics",
                "difficulty": "intermediate",
                "topics": ["patterns", "trends", "analysis"],
                "methods": ["descriptive", "inferential"],
                "applications": "universal",
            },
        ),
    ]

    return documents


async def demonstrate_basic_filtering():
    """Demonstrate basic metadata filtering."""
    print("\n🎯 Basic Metadata Filtering")
    print("-" * 40)

    embeddings = AdvancedEmbeddings()
    store = VectorStore(backend_type="memory", embeddings=embeddings)

    documents = await setup_advanced_dataset()
    await store.add_documents(documents)

    # Filter by category
    print("1. Filter by category='programming':")
    programming_docs = await store.search(
        "language development", k=5, filter={"category": "programming"}
    )

    for doc in programming_docs:
        lang = doc.metadata.get("language", "unknown")
        print(f"   - {lang}: {doc.page_content[:60]}...")

    # Filter by difficulty level
    print("\n2. Filter by difficulty='advanced':")
    advanced_docs = await store.search(
        "complex technology", k=5, filter={"difficulty": "advanced"}
    )

    for doc in advanced_docs:
        category = doc.metadata.get("category", "unknown")
        print(f"   - {category}: {doc.page_content[:60]}...")


async def demonstrate_complex_filtering():
    """Demonstrate complex multi-field filtering."""
    print("\n🔍 Complex Multi-field Filtering")
    print("-" * 40)

    embeddings = AdvancedEmbeddings()
    store = VectorStore(backend_type="memory", embeddings=embeddings)

    documents = await setup_advanced_dataset()
    await store.add_documents(documents)

    # Multiple field filters
    print("1. Filter: category='ai' AND difficulty='intermediate':")
    ai_intermediate = await store.search(
        "artificial intelligence learning",
        k=5,
        filter={"category": "ai", "difficulty": "intermediate"},
    )

    for doc in ai_intermediate:
        subcat = doc.metadata.get("subcategory", "general")
        print(f"   - AI/{subcat}: {doc.page_content[:60]}...")

    # Note: LangChain's InMemoryVectorStore supports exact match filters
    # For more complex filtering (ranges, lists), you'd need specialized backends

    print("\n2. Simulated range filtering (popularity >= 9.0):")
    # We'll simulate this by searching and post-filtering
    all_results = await store.search("popular programming", k=10)

    high_popularity = [
        doc for doc in all_results if doc.metadata.get("popularity", 0) >= 9.0
    ]

    for doc in high_popularity:
        pop = doc.metadata.get("popularity", "N/A")
        lang = doc.metadata.get("language", doc.metadata.get("category", "unknown"))
        print(f"   - {lang} (popularity: {pop}): {doc.page_content[:50]}...")


async def demonstrate_scored_search():
    """Demonstrate search with relevance scoring."""
    print("\n⭐ Relevance Scoring and Ranking")
    print("-" * 40)

    embeddings = AdvancedEmbeddings()
    store = VectorStore(backend_type="memory", embeddings=embeddings)

    documents = await setup_advanced_dataset()
    await store.add_documents(documents)

    # Search with scores
    print("1. Search with relevance scores: 'python programming'")
    scored_results = await store.search_with_score("python programming language", k=5)

    for i, (doc, score) in enumerate(scored_results, 1):
        category = doc.metadata.get("category", "unknown")
        language = doc.metadata.get("language", category)
        print(f"   {i}. [{language}] Score: {score:.3f}")
        print(f"      {doc.page_content[:70]}...")

    # Compare different query terms
    print("\n2. Score comparison for different queries:")
    queries = [
        "machine learning algorithms",
        "database vector search",
        "web development javascript",
    ]

    for query in queries:
        print(f"\n   Query: '{query}'")
        results = await store.search_with_score(query, k=3)

        for doc, score in results:
            category = doc.metadata.get("category", "unknown")
            print(f"     {category} ({score:.3f}): {doc.page_content[:50]}...")


async def demonstrate_search_strategies():
    """Demonstrate different search strategies."""
    print("\n🎪 Advanced Search Strategies")
    print("-" * 40)

    embeddings = AdvancedEmbeddings()
    store = VectorStore(backend_type="memory", embeddings=embeddings)

    documents = await setup_advanced_dataset()
    await store.add_documents(documents)

    # 1. Broad exploratory search
    print("1. Broad exploratory search (high k value):")
    broad_results = await store.search("technology programming", k=8)

    categories = {}
    for doc in broad_results:
        cat = doc.metadata.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1

    print("   Categories found:", dict(categories))

    # 2. Focused precision search
    print("\n2. Focused precision search (low k, specific query):")
    focused_results = await store.search(
        "vector database similarity search high dimensional", k=2
    )

    for doc in focused_results:
        db_type = doc.metadata.get("type", "unknown")
        print(f"   - {db_type}: {doc.page_content[:60]}...")

    # 3. Category-constrained search
    print("\n3. Category-constrained exploration:")
    for category in ["programming", "ai", "database"]:
        print(f"\n   Within {category}:")
        cat_results = await store.search(
            "modern advanced techniques", k=3, filter={"category": category}
        )

        for doc in cat_results:
            subcat = (
                doc.metadata.get("subcategory") or doc.metadata.get("type") or "general"
            )
            difficulty = doc.metadata.get("difficulty", "unknown")
            print(f"     - {subcat} ({difficulty}): {doc.page_content[:45]}...")


async def demonstrate_query_expansion():
    """Demonstrate query expansion techniques."""
    print("\n📈 Query Expansion Techniques")
    print("-" * 40)

    embeddings = AdvancedEmbeddings()
    store = VectorStore(backend_type="memory", embeddings=embeddings)

    documents = await setup_advanced_dataset()
    await store.add_documents(documents)

    # Original specific query
    original_query = "ML"
    print(f"1. Original query: '{original_query}'")
    original_results = await store.search(original_query, k=3)

    print("   Results:")
    for doc in original_results:
        category = doc.metadata.get("category", "unknown")
        print(f"     - {category}: {doc.page_content[:50]}...")

    # Expanded query with synonyms and context
    expanded_query = "machine learning artificial intelligence algorithms data patterns"
    print(f"\n2. Expanded query: '{expanded_query}'")
    expanded_results = await store.search(expanded_query, k=3)

    print("   Results:")
    for doc in expanded_results:
        category = doc.metadata.get("category", "unknown")
        subcat = doc.metadata.get("subcategory", "general")
        print(f"     - {category}/{subcat}: {doc.page_content[:50]}...")

    # Domain-specific expansion
    domain_query = "database storage retrieval indexing search optimization"
    print(f"\n3. Domain-focused expansion: 'database...'")
    domain_results = await store.search(domain_query, k=3)

    print("   Results:")
    for doc in domain_results:
        db_type = doc.metadata.get("type", "unknown")
        performance = doc.metadata.get("performance", "unknown")
        print(f"     - {db_type} ({performance}): {doc.page_content[:50]}...")


async def demonstrate_result_analysis():
    """Demonstrate analyzing and understanding search results."""
    print("\n🔬 Search Result Analysis")
    print("-" * 40)

    embeddings = AdvancedEmbeddings()
    store = VectorStore(backend_type="memory", embeddings=embeddings)

    documents = await setup_advanced_dataset()
    await store.add_documents(documents)

    # Analyze result diversity
    query = "programming development software"
    results = await store.search_with_score(query, k=8)

    print(f"Query: '{query}' - Analyzing {len(results)} results\n")

    # Group by metadata fields
    analysis = {
        "categories": {},
        "difficulties": {},
        "score_ranges": {"high": 0, "medium": 0, "low": 0},
    }

    print("Detailed Results:")
    for i, (doc, score) in enumerate(results, 1):
        category = doc.metadata.get("category", "other")
        difficulty = doc.metadata.get("difficulty", "unknown")

        # Count categories and difficulties
        analysis["categories"][category] = analysis["categories"].get(category, 0) + 1
        analysis["difficulties"][difficulty] = (
            analysis["difficulties"].get(difficulty, 0) + 1
        )

        # Score ranges
        if score > 0.8:
            analysis["score_ranges"]["high"] += 1
        elif score > 0.5:
            analysis["score_ranges"]["medium"] += 1
        else:
            analysis["score_ranges"]["low"] += 1

        print(f"   {i}. [{category}/{difficulty}] Score: {score:.3f}")
        print(f"      {doc.page_content[:65]}...")

    print(f"\n📊 Analysis Summary:")
    print(f"   Categories: {dict(analysis['categories'])}")
    print(f"   Difficulties: {dict(analysis['difficulties'])}")
    print(f"   Score distribution: {dict(analysis['score_ranges'])}")

    # Coverage analysis
    total_categories = len(set(doc.metadata.get("category") for doc in documents))
    found_categories = len(analysis["categories"])
    coverage = (found_categories / total_categories) * 100

    print(
        f"   Category coverage: {coverage:.1f}% ({found_categories}/{total_categories})"
    )


async def main():
    """Run the advanced search demonstration."""
    print("🎯 Advanced Search Techniques Demo")
    print("=" * 50)

    await demonstrate_basic_filtering()
    await demonstrate_complex_filtering()
    await demonstrate_scored_search()
    await demonstrate_search_strategies()
    await demonstrate_query_expansion()
    await demonstrate_result_analysis()

    print("\n✅ Advanced search demonstration completed!")
    print("\nKey Insights:")
    print("- Metadata filtering enables precise content targeting")
    print("- Relevance scores help identify the best matches")
    print("- Query expansion improves result coverage")
    print("- Different search strategies suit different use cases")
    print("- Result analysis reveals search effectiveness and bias")


if __name__ == "__main__":
    asyncio.run(main())
