#!/usr/bin/env python3
"""
Basic usage demonstration of KB Playground.

Shows the core API: search(), get(), add(), roll(), delete()
"""

import asyncio
from kb_playground import KnowledgeBase, Document


def main():
    """Demonstrate basic KB Playground usage."""
    print("🎮 KB Playground - Basic Usage Demo")
    print("=" * 50)
    
    # Initialize knowledge base
    kb = KnowledgeBase(
        dimension=128,
        data_dir="./demo_data",
        auto_discover_relationships=True,
        enable_dvc=False  # Disable for demo
    )
    
    print("\n📚 Adding documents...")
    
    # Add some documents
    documents = [
        "Python is a versatile programming language used for web development, data science, and AI.",
        "Machine learning algorithms can automatically learn patterns from data without explicit programming.",
        "Neural networks are computational models inspired by biological neural networks in animal brains.",
        "Data structures like arrays, lists, and trees organize information efficiently in computer memory.",
        "Algorithms are step-by-step procedures for solving computational problems and processing data.",
        Document(
            content="Software engineering involves designing, developing, and maintaining large-scale software systems.",
            title="Software Engineering",
            metadata={"category": "engineering", "difficulty": "intermediate"}
        )
    ]
    
    # Add documents to KB
    doc_ids = kb.add(*documents)
    print(f"Added {len(doc_ids)} documents")
    
    print("\n🔍 Searching for content...")
    
    # Search for programming-related content
    result = kb.search("programming language python", top_k=3)
    print(f"Found {len(result.documents)} results for 'programming language python':")
    
    for i, (doc, score) in enumerate(zip(result.documents, result.scores)):
        print(f"  {i+1}. Score: {score:.3f}")
        print(f"     Title: {doc.title or 'Untitled'}")
        print(f"     Content: {doc.content[:100]}...")
        print()
    
    print(f"Search took {result.search_time_ms:.2f}ms")
    
    print("\n📖 Retrieving specific documents...")
    
    # Get specific documents
    retrieved = kb.get(doc_ids[0], doc_ids[2])
    print(f"Retrieved {sum(1 for doc in retrieved if doc)} documents")
    
    for doc in retrieved:
        if doc:
            print(f"  - {doc.title or 'Untitled'}: {doc.content[:50]}...")
    
    print("\n🔗 Checking relationships...")
    
    # Search with relationship context
    result_with_context = kb.search("neural networks", top_k=2, caller_id="demo_agent")
    print(f"Found {len(result_with_context.relationships)} relationships")
    
    if result_with_context.relationships:
        for rel in result_with_context.relationships[:3]:
            print(f"  - {rel.relationship_type}: {rel.strength:.2f}")
    
    print("\n⏪ Testing rollback functionality...")
    
    # Add another document
    new_doc = "Quantum computing uses quantum mechanical phenomena to process information."
    new_id = kb.add(new_doc)
    print(f"Added new document: {new_id[0][:8]}...")
    
    # Check current state
    stats_before = kb.get_stats()
    print(f"Documents before rollback: {stats_before['documents']}")
    
    # Roll back the last operation
    success = kb.roll(1)
    if success:
        print("✅ Rollback successful")
        stats_after = kb.get_stats()
        print(f"Documents after rollback: {stats_after['documents']}")
    else:
        print("❌ Rollback failed")
    
    print("\n🗑️ Testing deletion...")
    
    # Delete a document
    delete_results = kb.delete(doc_ids[-1])
    print(f"Deletion results: {delete_results}")
    
    print("\n📊 Final statistics...")
    
    # Get final stats
    final_stats = kb.get_stats()
    print(f"Final document count: {final_stats['documents']}")
    print(f"Total operations: {final_stats['operations']}")
    print(f"Current version: {final_stats['current_version']}")
    print(f"Relationships discovered: {final_stats.get('relationships', 0)}")
    
    if 'relationship_analytics' in final_stats:
        analytics = final_stats['relationship_analytics']
        print(f"Total accesses tracked: {analytics.get('total_accesses', 0)}")
    
    print("\n✨ Demo completed successfully!")


if __name__ == "__main__":
    main()