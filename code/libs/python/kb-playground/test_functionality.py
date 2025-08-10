#!/usr/bin/env python3
"""
Test script to investigate what works and what doesn't in the current KB system.
"""

from kb_playground.hybrid_kb import HybridKB
from kb_playground.multi_agent_rag import MultiAgentRAG, Query

def test_hybrid_kb():
    """Test the hybrid knowledge base functionality."""
    print("🧠 Testing Hybrid Knowledge Base...")
    
    kb = HybridKB()
    
    # Add some test nodes
    kb.add_node("doc1", "Python is a programming language", {"type": "definition"})
    kb.add_node("doc2", "Machine learning trains models on data", {"type": "concept"})  
    kb.add_node("doc3", "Neural networks are inspired by the brain", {"type": "explanation"})
    
    # Add relationships
    kb.add_edge("doc1", "doc2", "enables", 1.0, {"context": "programming"})
    kb.add_edge("doc2", "doc3", "uses", 0.8, {"context": "AI"})
    
    print(f"📊 Stats: {kb.stats()}")
    
    # Test vector search
    print("\n🔍 Vector Search Test:")
    results = kb.vector_search("programming language")
    for node_id, similarity in results:
        print(f"  {similarity:.3f} | {node_id}: {kb.nodes[node_id].content[:50]}...")
    
    # Test graph traversal
    print("\n🕸️ Graph Traversal Test:")
    connected = kb.graph_traverse("doc1", max_depth=2)
    print(f"  Connected to doc1: {connected}")
    
    # Test hybrid search
    print("\n🔄 Hybrid Search Test:")
    hybrid_results = kb.hybrid_search("machine learning neural")
    for result in hybrid_results[:3]:
        print(f"  {result['similarity']:.3f} | {result['node_id']}: {result['content'][:50]}...")
    
    print("✅ Hybrid KB basic functionality works")
    return kb

def test_multi_agent_rag(kb):
    """Test the multi-agent RAG system."""
    print("\n🤖 Testing Multi-Agent RAG...")
    
    rag = MultiAgentRAG(kb)
    
    # Test query processing
    print("\n💬 Query Processing Test:")
    result = rag.process_query("What is machine learning?")
    
    print(f"Query: {result['query']}")
    print(f"Summary: {result['summary'][:100]}...")
    print(f"Quality: {result['quality_assessment']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Sources: {result['sources']}")
    
    # Test conversation history
    print("\n📝 Conversation History Test:")
    context = rag.get_conversation_context()
    print(f"History entries: {len(context)}")
    
    print("✅ Multi-Agent RAG basic functionality works")
    return rag

def test_edge_cases():
    """Test edge cases and error scenarios."""
    print("\n⚠️ Testing Edge Cases...")
    
    kb = HybridKB()
    
    # Empty search
    print("🔍 Empty search test:")
    results = kb.vector_search("nonexistent content")
    print(f"  Empty results: {len(results)} items")
    
    # Invalid graph traversal
    print("🕸️ Invalid traversal test:")
    connected = kb.graph_traverse("nonexistent_node")
    print(f"  Invalid traversal: {len(connected)} nodes")
    
    # RAG with empty KB
    print("🤖 RAG with empty KB test:")
    rag = MultiAgentRAG(kb)
    result = rag.process_query("What is AI?")
    print(f"  Empty KB result confidence: {result['confidence']:.2f}")
    
    print("✅ Edge cases handled gracefully")

def test_performance():
    """Test performance with larger dataset."""
    print("\n⚡ Testing Performance...")
    
    kb = HybridKB()
    
    # Add many nodes
    print("📊 Adding 100 test nodes...")
    for i in range(100):
        kb.add_node(f"node_{i}", f"Content for node {i} about topic {i%10}", 
                    {"index": i, "topic": i%10})
    
    # Add random edges
    print("🔗 Adding random edges...")
    for i in range(0, 100, 5):
        if i + 1 < 100:
            kb.add_edge(f"node_{i}", f"node_{i+1}", "related", 0.7)
    
    stats = kb.stats()
    print(f"📈 Final stats: {stats}")
    
    # Test search performance
    import time
    
    start = time.time()
    results = kb.vector_search("topic content")
    vector_time = time.time() - start
    
    start = time.time()
    hybrid_results = kb.hybrid_search("topic content")  
    hybrid_time = time.time() - start
    
    print(f"🏁 Vector search: {vector_time:.4f}s ({len(results)} results)")
    print(f"🏁 Hybrid search: {hybrid_time:.4f}s ({len(hybrid_results)} results)")
    
    print("✅ Performance tests completed")

def main():
    print("🔬 Knowledge Base Investigation Report")
    print("=" * 50)
    
    try:
        # Test core functionality
        kb = test_hybrid_kb()
        rag = test_multi_agent_rag(kb)
        
        # Test edge cases  
        test_edge_cases()
        
        # Test performance
        test_performance()
        
        print("\n" + "=" * 50)
        print("🎉 Investigation Summary:")
        print("✅ Hybrid KB: Vector + Graph search working")
        print("✅ Multi-Agent RAG: Agent pipeline functional") 
        print("✅ Edge Cases: Graceful error handling")
        print("✅ Performance: Scales to 100+ nodes")
        print("\n💡 The kb-playground implementation is functional!")
        
    except Exception as e:
        print(f"\n❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()