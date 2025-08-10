#!/usr/bin/env python3
"""
Real-World Example - Building a Documentation Knowledge Base

This example demonstrates a practical use case:
- Loading documentation from multiple sources
- Organizing content with hierarchical metadata
- Building a searchable knowledge base
- Implementing a simple Q&A system
"""

import asyncio
from datetime import datetime
from momo_kb import Document, DocumentMetadata, SearchOptions, KnowledgeBase
from momo_logger import get_logger


class DocumentationKB:
    """A documentation knowledge base with Q&A capabilities."""

    def __init__(self):
        self.kb = KnowledgeBase()

    async def __aenter__(self):
        await self.kb.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.kb.__aexit__(exc_type, exc_val, exc_tb)

    async def load_documentation(self):
        """Load sample documentation content."""
        docs = [
            # Python Documentation
            Document(
                content="Python functions are defined using the 'def' keyword followed by the function name and parentheses. Functions can accept parameters and return values.",
                metadata=DocumentMetadata(
                    source="python_docs",
                    author="Python.org",
                    type="documentation",
                    category="python/functions",
                    tags=["python", "functions", "def", "parameters", "return"],
                    language="en",
                    custom={
                        "section": "language_reference",
                        "difficulty": "beginner",
                        "version": "3.11",
                    },
                ),
            ),
            Document(
                content="Python classes are created using the 'class' keyword. Classes define objects with attributes and methods. Use '__init__' method for initialization.",
                metadata=DocumentMetadata(
                    source="python_docs",
                    author="Python.org",
                    type="documentation",
                    category="python/classes",
                    tags=["python", "classes", "objects", "init", "methods"],
                    language="en",
                    custom={
                        "section": "language_reference",
                        "difficulty": "intermediate",
                        "version": "3.11",
                    },
                ),
            ),
            # API Documentation
            Document(
                content="REST API endpoints use HTTP methods: GET for retrieving data, POST for creating resources, PUT for updating, DELETE for removing.",
                metadata=DocumentMetadata(
                    source="api_guide",
                    author="API Team",
                    type="documentation",
                    category="api/rest",
                    tags=["api", "rest", "http", "get", "post", "put", "delete"],
                    language="en",
                    custom={
                        "section": "api_reference",
                        "difficulty": "beginner",
                        "version": "v1",
                    },
                ),
            ),
            Document(
                content="API authentication can use API keys, OAuth tokens, or JWT. Include authentication headers in all requests to protected endpoints.",
                metadata=DocumentMetadata(
                    source="api_guide",
                    author="Security Team",
                    type="documentation",
                    category="api/authentication",
                    tags=[
                        "api",
                        "authentication",
                        "security",
                        "oauth",
                        "jwt",
                        "api-keys",
                    ],
                    language="en",
                    custom={
                        "section": "security",
                        "difficulty": "intermediate",
                        "version": "v1",
                    },
                ),
            ),
            # Database Documentation
            Document(
                content="SQL SELECT statements retrieve data from tables. Use WHERE clauses to filter results, ORDER BY to sort, and LIMIT to control result count.",
                metadata=DocumentMetadata(
                    source="database_guide",
                    author="Database Team",
                    type="documentation",
                    category="database/queries",
                    tags=["sql", "select", "where", "order by", "limit", "queries"],
                    language="en",
                    custom={
                        "section": "query_reference",
                        "difficulty": "beginner",
                        "database": "postgresql",
                    },
                ),
            ),
            Document(
                content="Database indexes improve query performance by creating efficient data structures. Create indexes on frequently queried columns.",
                metadata=DocumentMetadata(
                    source="database_guide",
                    author="Performance Team",
                    type="documentation",
                    category="database/performance",
                    tags=[
                        "database",
                        "indexes",
                        "performance",
                        "optimization",
                        "queries",
                    ],
                    language="en",
                    custom={
                        "section": "performance_guide",
                        "difficulty": "advanced",
                        "database": "postgresql",
                    },
                ),
            ),
            # Troubleshooting Documentation
            Document(
                content="Common Python errors: NameError occurs when using undefined variables, TypeError when using wrong data types, IndexError when accessing invalid list positions.",
                metadata=DocumentMetadata(
                    source="troubleshooting_guide",
                    author="Support Team",
                    type="troubleshooting",
                    category="python/errors",
                    tags=[
                        "python",
                        "errors",
                        "debugging",
                        "nameerror",
                        "typeerror",
                        "indexerror",
                    ],
                    language="en",
                    custom={
                        "section": "common_issues",
                        "difficulty": "beginner",
                        "solution_type": "error_reference",
                    },
                ),
            ),
            Document(
                content="API rate limiting: When you receive 429 status codes, implement exponential backoff. Wait progressively longer between retry attempts.",
                metadata=DocumentMetadata(
                    source="troubleshooting_guide",
                    author="API Team",
                    type="troubleshooting",
                    category="api/errors",
                    tags=[
                        "api",
                        "rate-limiting",
                        "429",
                        "backoff",
                        "retry",
                        "troubleshooting",
                    ],
                    language="en",
                    custom={
                        "section": "api_issues",
                        "difficulty": "intermediate",
                        "solution_type": "implementation_guide",
                    },
                ),
            ),
        ]

        doc_ids = await self.kb.save(*docs)
        return doc_ids

    async def ask_question(self, question: str, context_filters: dict = None) -> dict:
        """Ask a question and get relevant answers from documentation."""
        logger = get_logger("momo.kb.example.real_world_example")
        await logger.ai_user(f"❓ Question: {question}", user_facing=True)

        # Create search options with optional context filters
        options = SearchOptions(limit=3, threshold=0.1)
        if context_filters:
            options.filters = context_filters

        # Search for relevant documentation
        results = await self.kb.search(question, options)

        if not results:
            return {
                "answer": "No relevant documentation found.",
                "sources": [],
                "confidence": 0.0,
            }

        # Format answer from top results
        answer_parts = []
        sources = []
        total_confidence = 0.0

        for i, result in enumerate(results):
            doc = result.document
            score = result.score
            total_confidence += score

            # Add content to answer
            answer_parts.append(f"({score:.2f}) {doc.content}")

            # Track source information
            sources.append(
                {
                    "source": doc.metadata.source,
                    "category": doc.metadata.category,
                    "type": doc.metadata.type,
                    "confidence": score,
                    "tags": doc.metadata.tags,
                }
            )

        return {
            "answer": "\n\n".join(answer_parts),
            "sources": sources,
            "confidence": total_confidence / len(results),
            "result_count": len(results),
        }

    async def browse_categories(self):
        """Browse available documentation categories."""
        all_docs = await self.kb.list_documents()

        categories = {}
        for doc in all_docs:
            if doc:
                category = doc.metadata.category or "uncategorized"
                if category not in categories:
                    categories[category] = []
                categories[category].append(
                    {
                        "id": doc.id,
                        "type": doc.metadata.type,
                        "tags": doc.metadata.tags[:3],  # First 3 tags
                        "difficulty": doc.metadata.custom.get("difficulty", "unknown"),
                    }
                )

        return categories

    async def get_stats(self):
        """Get knowledge base statistics."""
        total_docs = await self.kb.count()
        all_docs = await self.kb.list_documents()

        stats = {
            "total_documents": total_docs,
            "by_type": {},
            "by_difficulty": {},
            "by_source": {},
        }

        for doc in all_docs:
            if doc:
                # Count by type
                doc_type = doc.metadata.type or "unknown"
                stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1

                # Count by difficulty
                difficulty = doc.metadata.custom.get("difficulty", "unknown")
                stats["by_difficulty"][difficulty] = (
                    stats["by_difficulty"].get(difficulty, 0) + 1
                )

                # Count by source
                source = doc.metadata.source or "unknown"
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

        return stats


async def main():
    logger = get_logger("momo.kb.example.real_world_example")
    await logger.ai_user(
        "🧠 Real-World Example - Documentation Knowledge Base", user_facing=True
    )
    await logger.ai_user("=" * 60, user_facing=True)

    # Initialize documentation KB
    async with DocumentationKB() as docs_kb:
        # Load documentation
        await logger.ai_user("📚 Loading documentation...", user_facing=True)
        doc_ids = await docs_kb.load_documentation()
        await logger.ai_user(
            f"✅ Loaded {len(doc_ids)} documentation articles", user_facing=True
        )

        # Show knowledge base statistics
        await logger.ai_user("\n📊 KNOWLEDGE BASE STATS", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)
        stats = await docs_kb.get_stats()

        await logger.ai_user(
            f"Total documents: {stats['total_documents']}", user_facing=True
        )
        await logger.ai_user(
            "By type: " + ", ".join(f"{k}({v})" for k, v in stats["by_type"].items()),
            user_facing=True,
        )
        await logger.ai_user(
            "By difficulty: "
            + ", ".join(f"{k}({v})" for k, v in stats["by_difficulty"].items()),
            user_facing=True,
        )
        await logger.ai_user(
            "By source: "
            + ", ".join(f"{k}({v})" for k, v in stats["by_source"].items()),
            user_facing=True,
        )

        # Browse categories
        await logger.ai_user("\n📁 AVAILABLE CATEGORIES", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)
        categories = await docs_kb.browse_categories()
        for category, docs in categories.items():
            await logger.ai_user(f"📂 {category} ({len(docs)} docs)", user_facing=True)
            for doc in docs[:2]:  # Show first 2 docs per category
                await logger.ai_user(
                    f"   • {doc['type']} | {doc['difficulty']} | {doc['tags']}",
                    user_facing=True,
                )

        # Q&A Examples
        await logger.ai_user("\n💬 DOCUMENTATION Q&A SYSTEM", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)

        questions = [
            "How do I create a Python function?",
            "What HTTP methods are used in REST APIs?",
            "How do I fix a NameError in Python?",
            "How do I handle API rate limiting?",
            "What is a database index?",
        ]

        for question in questions:
            await logger.ai_user("\n" + "=" * 50, user_facing=True)
            response = await docs_kb.ask_question(question)

            await logger.ai_user(
                f"💡 Answer (confidence: {response['confidence']:.2f}):",
                user_facing=True,
            )
            await logger.ai_user(response["answer"], user_facing=True)

            await logger.ai_user(
                f"\n📚 Sources ({response['result_count']} found):", user_facing=True
            )
            for i, source in enumerate(response["sources"], 1):
                await logger.ai_user(
                    f"   {i}. {source['source']} | {source['category']} | {source['confidence']:.2f}",
                    user_facing=True,
                )

        # Context-specific queries
        await logger.ai_user("\n" + "=" * 60, user_facing=True)
        await logger.ai_user("🎯 CONTEXT-SPECIFIC QUERIES", user_facing=True)
        await logger.ai_user("=" * 60, user_facing=True)

        # Query only Python documentation
        await logger.ai_user("\n🐍 Python-specific query:", user_facing=True)
        python_response = await docs_kb.ask_question(
            "How do I handle errors?", context_filters={"category": "python/errors"}
        )
        await logger.ai_user(
            f"Answer: {python_response['answer'][:100]}...", user_facing=True
        )

        # Query only API documentation
        await logger.ai_user("\n🌐 API-specific query:", user_facing=True)
        api_response = await docs_kb.ask_question(
            "How do I authenticate requests?", context_filters={"source": "api_guide"}
        )
        await logger.ai_user(
            f"Answer: {api_response['answer'][:100]}...", user_facing=True
        )

        await logger.ai_user("\n💡 DOCUMENTATION KB FEATURES:", user_facing=True)
        await logger.ai_user("🔹 Multi-source content aggregation", user_facing=True)
        await logger.ai_user("🔹 Hierarchical categorization", user_facing=True)
        await logger.ai_user("🔹 Difficulty-based filtering", user_facing=True)
        await logger.ai_user("🔹 Question-answer capabilities", user_facing=True)
        await logger.ai_user("🔹 Context-aware searches", user_facing=True)
        await logger.ai_user(
            "🔹 Source attribution and confidence scores", user_facing=True
        )

    await logger.ai_user(
        "\n🎉 Real-world documentation KB example completed!", user_facing=True
    )


if __name__ == "__main__":
    asyncio.run(main())
