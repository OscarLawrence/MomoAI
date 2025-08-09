#!/usr/bin/env python3
"""
Basic Usage Example - Getting Started with Momo KnowledgeBase

This example shows the simplest way to use momo-kb:
- Create a knowledge base
- Add documents
- Search for information
- Retrieve documents
"""

import asyncio
from momo_kb import Document, DocumentMetadata, KnowledgeBase
from momo_logger import get_logger


async def main():
    logger = get_logger("momo.kb.example.basic")

    await logger.ai_user("🧠 Momo KnowledgeBase - Basic Usage Example", user_facing=True)
    await logger.ai_user("=" * 50, user_facing=True)

    # Create a knowledge base (uses in-memory storage by default)
    async with KnowledgeBase() as kb:
        await logger.info("Created knowledge base with default in-memory storage")

        # Create some documents about programming
        documents = [
            Document(
                content="Python is a high-level programming language known for its simplicity and readability.",
                metadata=DocumentMetadata(
                    source="programming_guide",
                    category="programming",
                    tags=["python", "programming", "beginner"],
                ),
            ),
            Document(
                content="JavaScript is a versatile programming language primarily used for web development.",
                metadata=DocumentMetadata(
                    source="web_guide",
                    category="programming",
                    tags=["javascript", "web", "frontend"],
                ),
            ),
            Document(
                content="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                metadata=DocumentMetadata(
                    source="ai_guide",
                    category="ai",
                    tags=["machine-learning", "ai", "algorithms"],
                ),
            ),
        ]

        # Save documents to the knowledge base
        await logger.ai_user(
            f"\n📝 Saving {len(documents)} documents...", user_facing=True
        )
        doc_ids = await kb.save(*documents)
        await logger.info(f"Saved documents with IDs: {doc_ids}")
        await logger.ai_user(f"✅ Saved documents with IDs: {doc_ids}", user_facing=True)

        # Search for information
        await logger.ai_user(
            "\n🔍 Searching for 'python programming'...", user_facing=True
        )
        results = await kb.search("python programming")
        await logger.info(f"Search completed, found {len(results)} results")
        await logger.ai_user(f"📊 Found {len(results)} results", user_facing=True)

        for i, result in enumerate(results, 1):
            await logger.ai_user(f"\n{i}. Score: {result.score:.3f}", user_facing=True)
            await logger.ai_user(
                f"   Content: {result.document.content[:80]}...", user_facing=True
            )
            await logger.ai_user(
                f"   Tags: {result.document.metadata.tags}", user_facing=True
            )

        # Get a specific document by ID
        await logger.ai_user(
            f"\n📖 Retrieving document {doc_ids[0]}...", user_facing=True
        )
        doc = await kb.get(doc_ids[0])
        if doc:
            await logger.info(f"Retrieved document {doc_ids[0]} successfully")
            await logger.ai_user(
                f"✅ Retrieved: {doc.content[:50]}...", user_facing=True
            )

        # Count total documents
        total = await kb.count()
        await logger.info(f"Knowledge base contains {total} documents")
        await logger.ai_user(
            f"\n📊 Total documents in knowledge base: {total}", user_facing=True
        )

        # List all document IDs
        all_ids = await kb.list_documents()
        await logger.debug(f"All document IDs: {all_ids}")
        await logger.ai_user(f"📋 All document IDs: {all_ids}", user_facing=True)

    await logger.ai_user("\n🎉 Basic usage example completed!", user_facing=True)


if __name__ == "__main__":
    asyncio.run(main())
