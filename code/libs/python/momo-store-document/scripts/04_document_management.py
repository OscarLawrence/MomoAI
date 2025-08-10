#!/usr/bin/env python3
"""
Document Management Example - CRUD Operations and Metadata

This example demonstrates:
- Creating documents with rich metadata
- Reading and retrieving documents
- Updating document content and metadata
- Deleting documents
- Batch operations
- Document lifecycle management
"""

import asyncio
from datetime import datetime
from momo_kb import Document, DocumentMetadata, KnowledgeBase, DocumentNotFoundError
from momo_logger import get_logger


async def main():
    logger = get_logger("momo.kb.example.document_management")
    await logger.ai_user("🧠 Momo KnowledgeBase - Document Management", user_facing=True)
    await logger.ai_user("=" * 60, user_facing=True)

    async with KnowledgeBase() as kb:
        # === CREATE OPERATIONS ===
        await logger.ai_user("\n📝 CREATE OPERATIONS", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)

        # Create a document with comprehensive metadata
        doc = Document(
            content="Async programming in Python allows handling multiple operations concurrently.",
            metadata=DocumentMetadata(
                source="python_async_guide",
                author="Python Expert",
                type="tutorial",
                category="programming",
                tags=["python", "async", "concurrency", "programming"],
                language="en",
                created_at=datetime.now(),
                custom={
                    "difficulty": "intermediate",
                    "estimated_read_time": "5 minutes",
                    "prerequisites": ["python_basics", "functions"],
                },
            ),
        )

        # Save single document
        doc_id = (await kb.save(doc))[0]
        await logger.ai_user(f"✅ Created document: {doc_id}", user_facing=True)
        await logger.ai_user(f"   Content: {doc.content[:50]}...", user_facing=True)
        await logger.ai_user(f"   Tags: {doc.metadata.tags}", user_facing=True)

        # Create multiple documents at once
        batch_docs = [
            Document(
                content="FastAPI is a modern web framework for building APIs with Python.",
                metadata=DocumentMetadata(
                    source="fastapi_docs",
                    author="FastAPI Team",
                    type="documentation",
                    category="web_frameworks",
                    tags=["fastapi", "python", "api", "web"],
                    custom={"difficulty": "intermediate"},
                ),
            ),
            Document(
                content="Docker containers provide lightweight virtualization for applications.",
                metadata=DocumentMetadata(
                    source="docker_guide",
                    author="DevOps Team",
                    type="guide",
                    category="devops",
                    tags=["docker", "containers", "devops", "virtualization"],
                    custom={"difficulty": "advanced"},
                ),
            ),
            Document(
                content="Git is a distributed version control system for tracking changes in source code.",
                metadata=DocumentMetadata(
                    source="git_handbook",
                    author="Git Community",
                    type="handbook",
                    category="tools",
                    tags=["git", "version-control", "development", "collaboration"],
                    custom={"difficulty": "beginner"},
                ),
            ),
        ]

        batch_ids = await kb.save(*batch_docs)
        await logger.ai_user(
            f"✅ Created batch of {len(batch_docs)} documents: {batch_ids}",
            user_facing=True,
        )

        # === READ OPERATIONS ===
        await logger.ai_user("\n📖 READ OPERATIONS", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)

        # Get document by ID
        retrieved_doc = await kb.get(doc_id)
        if retrieved_doc:
            await logger.ai_user(f"✅ Retrieved document {doc_id}:", user_facing=True)
            await logger.ai_user(
                f"   Content: {retrieved_doc.content[:60]}...", user_facing=True
            )
            await logger.ai_user(
                f"   Author: {retrieved_doc.metadata.author}", user_facing=True
            )
            await logger.ai_user(
                f"   Created: {retrieved_doc.metadata.created_at}", user_facing=True
            )

        # List all document IDs
        all_ids = await kb.list_documents()
        await logger.ai_user(f"📋 All document IDs: {all_ids}", user_facing=True)

        # Count documents
        total_count = await kb.count()
        await logger.ai_user(f"🔢 Total documents: {total_count}", user_facing=True)

        # === UPDATE OPERATIONS ===
        await logger.ai_user("\n✏️ UPDATE OPERATIONS", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)

        # Update document content and metadata
        if retrieved_doc:
            # Modify the document
            retrieved_doc.content += (
                " This includes asyncio, async/await syntax, and event loops."
            )
            retrieved_doc.metadata.tags.append("asyncio")
            retrieved_doc.metadata.custom["last_updated"] = datetime.now().isoformat()
            retrieved_doc.metadata.updated_at = datetime.now()

            # Save the updated document
            await kb.update(retrieved_doc)
            await logger.ai_user(f"✅ Updated document {doc_id}", user_facing=True)

            # Verify the update
            updated_doc = await kb.get(doc_id)
            if updated_doc:
                await logger.ai_user(
                    f"   New content length: {len(updated_doc.content)} chars",
                    user_facing=True,
                )
                await logger.ai_user(
                    f"   Updated tags: {updated_doc.metadata.tags}", user_facing=True
                )
                await logger.ai_user(
                    f"   Updated at: {updated_doc.metadata.updated_at}",
                    user_facing=True,
                )

        # === SEARCH AND FILTER ===
        await logger.ai_user("\n🔍 SEARCH AND FILTER", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)

        # Search by content
        search_results = await kb.search("python programming")
        await logger.ai_user(
            f"🔍 Found {len(search_results)} results for 'python programming':",
            user_facing=True,
        )
        for i, result in enumerate(search_results, 1):
            await logger.ai_user(
                f"   {i}. {result.document.metadata.type} - Score: {result.score:.3f}",
                user_facing=True,
            )

        # Advanced search - find intermediate difficulty docs
        from momo_kb import SearchOptions

        intermediate_docs = await kb.search(
            "", SearchOptions(filters={"custom.difficulty": "intermediate"})
        )
        await logger.ai_user(
            f"🎯 Found {len(intermediate_docs)} intermediate difficulty documents",
            user_facing=True,
        )

        # === DELETE OPERATIONS ===
        await logger.ai_user("\n🗑️ DELETE OPERATIONS", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)

        # Delete a specific document
        if batch_ids:
            delete_id = batch_ids[0]  # Delete first document from batch
            success = await kb.delete(delete_id)
            if success:
                await logger.ai_user(
                    f"✅ Deleted document: {delete_id}", user_facing=True
                )
            else:
                await logger.ai_user(
                    f"❌ Failed to delete document: {delete_id}", user_facing=True
                )

        # Verify deletion
        try:
            deleted_doc = await kb.get(delete_id)
            await logger.ai_user(
                f"❌ Document {delete_id} still exists after deletion", user_facing=True
            )
        except DocumentNotFoundError:
            await logger.ai_user(
                f"✅ Confirmed: Document {delete_id} no longer exists", user_facing=True
            )

        # Count after deletion
        final_count = await kb.count()
        await logger.ai_user(
            f"🔢 Documents after deletion: {final_count}", user_facing=True
        )

        # === METADATA ANALYSIS ===
        await logger.ai_user("\n📊 METADATA ANALYSIS", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)

        # Analyze all documents
        remaining_ids = await kb.list_documents()
        categories = {}
        difficulty_levels = {}

        for doc in remaining_ids:
            if doc:
                # Count categories
                category = doc.metadata.category or "uncategorized"
                categories[category] = categories.get(category, 0) + 1

                # Count difficulty levels
                difficulty = doc.metadata.custom.get("difficulty", "unknown")
                difficulty_levels[difficulty] = difficulty_levels.get(difficulty, 0) + 1

        await logger.ai_user("📈 Category distribution:", user_facing=True)
        for category, count in categories.items():
            await logger.ai_user(
                f"   • {category}: {count} documents", user_facing=True
            )

        await logger.ai_user("📊 Difficulty distribution:", user_facing=True)
        for difficulty, count in difficulty_levels.items():
            await logger.ai_user(
                f"   • {difficulty}: {count} documents", user_facing=True
            )

        # === LIFECYCLE SUMMARY ===
        await logger.ai_user("\n📋 DOCUMENT LIFECYCLE SUMMARY", user_facing=True)
        await logger.ai_user("-" * 30, user_facing=True)
        await logger.ai_user(
            f"📝 Created: {len(batch_docs) + 1} documents initially", user_facing=True
        )
        await logger.ai_user(
            f"✏️ Updated: 1 document with new content and metadata", user_facing=True
        )
        await logger.ai_user(f"🗑️ Deleted: 1 document", user_facing=True)
        await logger.ai_user(
            f"📊 Final count: {final_count} documents", user_facing=True
        )

        await logger.ai_user(
            "\n💡 DOCUMENT MANAGEMENT BEST PRACTICES:", user_facing=True
        )
        await logger.ai_user(
            "🔹 Use rich metadata for better organization and searching",
            user_facing=True,
        )
        await logger.ai_user(
            "🔹 Include timestamps for tracking document lifecycle", user_facing=True
        )
        await logger.ai_user(
            "🔹 Use custom fields for domain-specific metadata", user_facing=True
        )
        await logger.ai_user(
            "🔹 Batch operations for better performance", user_facing=True
        )
        await logger.ai_user(
            "🔹 Always verify operations with get/count/list", user_facing=True
        )
        await logger.ai_user(
            "🔹 Use consistent categorization and tagging schemes", user_facing=True
        )

    await logger.ai_user("\n🎉 Document management example completed!", user_facing=True)


if __name__ == "__main__":
    asyncio.run(main())
