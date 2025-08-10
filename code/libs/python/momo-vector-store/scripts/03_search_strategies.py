#!/usr/bin/env python3
"""
Search Strategies Example - Different Ways to Find Information

This example demonstrates:
- Basic text search
- Metadata filtering
- Advanced search options
- Search result analysis
"""

import asyncio
from momo_kb import Document, DocumentMetadata, SearchOptions, KnowledgeBase
from momo_logger import get_logger


async def create_knowledge_base():
    """Create a knowledge base with diverse content."""
    kb = KnowledgeBase()

    # Create documents with rich metadata
    documents = [
        Document(
            content="Python is an interpreted, high-level programming language with dynamic semantics.",
            metadata=DocumentMetadata(
                source="python.org",
                author="Python Foundation",
                type="documentation",
                category="programming",
                tags=["python", "programming", "interpreted", "high-level"],
                language="en",
                custom={"difficulty": "beginner", "year": 2023},
            ),
        ),
        Document(
            content="Machine learning algorithms can automatically improve through experience and data.",
            metadata=DocumentMetadata(
                source="ml_handbook",
                author="AI Research Team",
                type="article",
                category="artificial_intelligence",
                tags=["machine-learning", "algorithms", "data", "AI"],
                language="en",
                custom={"difficulty": "intermediate", "year": 2023},
            ),
        ),
        Document(
            content="React is a JavaScript library for building user interfaces, maintained by Meta.",
            metadata=DocumentMetadata(
                source="react.dev",
                author="Meta Team",
                type="documentation",
                category="web_development",
                tags=["react", "javascript", "ui", "frontend", "library"],
                language="en",
                custom={"difficulty": "intermediate", "year": 2023},
            ),
        ),
        Document(
            content="Data science combines statistics, programming, and domain expertise to extract insights.",
            metadata=DocumentMetadata(
                source="data_science_guide",
                author="Analytics Team",
                type="guide",
                category="data_science",
                tags=["data-science", "statistics", "programming", "analytics"],
                language="en",
                custom={"difficulty": "advanced", "year": 2022},
            ),
        ),
        Document(
            content="Deep learning uses neural networks with multiple layers to model complex patterns.",
            metadata=DocumentMetadata(
                source="deep_learning_book",
                author="Neural Net Experts",
                type="textbook",
                category="artificial_intelligence",
                tags=["deep-learning", "neural-networks", "AI", "patterns"],
                language="en",
                custom={"difficulty": "advanced", "year": 2023},
            ),
        ),
        Document(
            content="L'intelligence artificielle révolutionne notre façon de travailler et de vivre.",
            metadata=DocumentMetadata(
                source="tech_fr",
                author="Équipe IA",
                type="article",
                category="artificial_intelligence",
                tags=["intelligence-artificielle", "technologie", "innovation"],
                language="fr",
                custom={"difficulty": "beginner", "year": 2023},
            ),
        ),
    ]

    await kb.save(*documents)
    return kb


async def demonstrate_search_strategy(kb, title: str, description: str, search_func):
    """Demonstrate a specific search strategy."""
    logger = get_logger("momo.kb.example.search_strategies")
    await logger.ai_user(f"\n{'='*60}", user_facing=True)
    await logger.ai_user(f"🔍 {title}", user_facing=True)
    await logger.ai_user(f"💡 {description}", user_facing=True)
    await logger.ai_user("=" * 60, user_facing=True)

    results = await search_func(kb)

    await logger.ai_user(f"📊 Found {len(results)} results", user_facing=True)

    for i, result in enumerate(results, 1):
        await logger.ai_user(f"\n{i}. Score: {result.score:.3f}", user_facing=True)
        await logger.ai_user(
            f"   Content: {result.document.content[:80]}...", user_facing=True
        )
        await logger.ai_user(
            f"   Category: {result.document.metadata.category}", user_facing=True
        )
        await logger.ai_user(
            f"   Tags: {result.document.metadata.tags}", user_facing=True
        )
        if result.document.metadata.custom:
            await logger.ai_user(
                f"   Difficulty: {result.document.metadata.custom.get('difficulty', 'N/A')}",
                user_facing=True,
            )


async def basic_text_search(kb):
    """Basic text search - finds documents containing keywords."""
    return await kb.search("programming language")


async def category_search(kb):
    """Search within specific category using metadata filters."""
    options = SearchOptions(filters={"category": "artificial_intelligence"})
    return await kb.search("algorithms", options)


async def tag_based_search(kb):
    """Search documents with specific tags."""
    options = SearchOptions(filters={"tags": ["python"]})
    return await kb.search("", options)  # Empty query, just filter by tags


async def difficulty_search(kb):
    """Search by custom metadata - difficulty level."""
    options = SearchOptions(filters={"custom.difficulty": "advanced"})
    return await kb.search("", options)


async def language_search(kb):
    """Search documents in specific language."""
    options = SearchOptions(filters={"language": "fr"})
    return await kb.search("", options)


async def author_search(kb):
    """Search documents by specific author."""
    options = SearchOptions(filters={"author": "Meta Team"})
    return await kb.search("", options)


async def limited_results_search(kb):
    """Search with result limits."""
    options = SearchOptions(limit=2, threshold=0.1)  # Max 2 results, min 0.1 relevance
    return await kb.search("AI machine learning", options)


async def type_and_content_search(kb):
    """Combined content and metadata search."""
    options = SearchOptions(filters={"type": "documentation"})
    return await kb.search("programming", options)


async def main():
    logger = get_logger("momo.kb.example.search_strategies")
    await logger.ai_user("🧠 Momo KnowledgeBase - Search Strategies", user_facing=True)
    await logger.ai_user("=" * 60, user_facing=True)

    # Create knowledge base with sample data
    await logger.ai_user(
        "📄 Setting up knowledge base with diverse content...", user_facing=True
    )
    kb = await create_knowledge_base()

    total_docs = await kb.count()
    await logger.ai_user(
        f"✅ Knowledge base created with {total_docs} documents", user_facing=True
    )

    # Demonstrate different search strategies
    search_strategies = [
        (
            "Basic Text Search",
            "Find documents containing specific keywords",
            basic_text_search,
        ),
        ("Category Filter", "Search within a specific category", category_search),
        ("Tag-Based Search", "Find documents with specific tags", tag_based_search),
        ("Difficulty Filter", "Search by custom difficulty level", difficulty_search),
        ("Language Filter", "Find documents in specific language", language_search),
        ("Author Search", "Find documents by specific author", author_search),
        (
            "Limited Results",
            "Control number and quality of results",
            limited_results_search,
        ),
        (
            "Combined Search",
            "Mix content search with metadata filters",
            type_and_content_search,
        ),
    ]

    async with kb:
        for title, description, search_func in search_strategies:
            await demonstrate_search_strategy(kb, title, description, search_func)

    await logger.ai_user(f"\n{'='*60}", user_facing=True)
    await logger.ai_user("💡 SEARCH STRATEGY TIPS:", user_facing=True)
    await logger.ai_user("=" * 60, user_facing=True)
    await logger.ai_user(
        "🔹 Use basic text search for content discovery", user_facing=True
    )
    await logger.ai_user(
        "🔹 Add metadata filters to narrow down results", user_facing=True
    )
    await logger.ai_user(
        "🔹 Combine multiple filters for precise searches", user_facing=True
    )
    await logger.ai_user(
        "🔹 Adjust threshold to control result quality", user_facing=True
    )
    await logger.ai_user(
        "🔹 Use limits for performance with large datasets", user_facing=True
    )
    await logger.ai_user(
        "🔹 Custom metadata enables domain-specific searches", user_facing=True
    )

    await logger.ai_user("\n🎉 Search strategies example completed!", user_facing=True)


if __name__ == "__main__":
    asyncio.run(main())
