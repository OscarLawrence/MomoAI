#!/usr/bin/env python3
"""
Knowledge Base Playground Demo

This script demonstrates the hybrid knowledge base and multi-agent RAG system.
Run with: python scripts/demo.py
"""

import sys
from pathlib import Path

# Add the module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kb_playground.hybrid_kb import HybridKB
from kb_playground.multi_agent_rag import MultiAgentRAG


def create_sample_knowledge_base():
    """Create a sample knowledge base with AI/ML content."""
    kb = HybridKB()
    
    # Add nodes about AI/ML concepts
    kb.add_node("ai_def", "Artificial Intelligence is the simulation of human intelligence by machines", 
                {"topic": "AI", "type": "definition"})
    
    kb.add_node("ml_def", "Machine Learning is a subset of AI that learns patterns from data without explicit programming", 
                {"topic": "ML", "type": "definition"})
    
    kb.add_node("dl_def", "Deep Learning uses neural networks with multiple layers to model complex patterns", 
                {"topic": "DL", "type": "definition"})
    
    kb.add_node("supervised", "Supervised learning uses labeled data to train models for prediction tasks", 
                {"topic": "ML", "type": "technique"})
    
    kb.add_node("unsupervised", "Unsupervised learning finds hidden patterns in data without labeled examples", 
                {"topic": "ML", "type": "technique"})
    
    kb.add_node("nn_basics", "Neural networks are computing systems inspired by biological neural networks", 
                {"topic": "DL", "type": "foundation"})
    
    kb.add_node("cnn", "Convolutional Neural Networks excel at processing grid-like data such as images", 
                {"topic": "DL", "type": "architecture"})
    
    kb.add_node("rnn", "Recurrent Neural Networks process sequential data with memory of previous inputs", 
                {"topic": "DL", "type": "architecture"})
    
    # Add relationships
    kb.add_edge("ai_def", "ml_def", "includes", 0.9)
    kb.add_edge("ml_def", "dl_def", "includes", 0.8)
    kb.add_edge("ml_def", "supervised", "encompasses", 0.9)
    kb.add_edge("ml_def", "unsupervised", "encompasses", 0.9)
    kb.add_edge("dl_def", "nn_basics", "builds_on", 0.9)
    kb.add_edge("nn_basics", "cnn", "enables", 0.8)
    kb.add_edge("nn_basics", "rnn", "enables", 0.8)
    kb.add_edge("supervised", "cnn", "can_use", 0.7)
    kb.add_edge("supervised", "rnn", "can_use", 0.7)
    
    return kb


def demo_hybrid_kb():
    """Demonstrate hybrid knowledge base functionality."""
    print("🧠 Hybrid Knowledge Base Demo")
    print("=" * 50)
    
    kb = create_sample_knowledge_base()
    
    print(f"📊 Knowledge Base Stats:")
    stats = kb.stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Vector search demo
    print("🔍 Vector Search Demo:")
    query = "neural networks"
    results = kb.vector_search(query, top_k=3)
    print(f"Query: '{query}'")
    for node_id, similarity in results:
        content = kb.nodes[node_id].content[:60] + "..."
        print(f"  {similarity:.3f} | {node_id}: {content}")
    print()
    
    # Graph traversal demo
    print("🕸️  Graph Traversal Demo:")
    start_node = "ml_def"
    connected = kb.graph_traverse(start_node, max_depth=2)
    print(f"Starting from '{start_node}', connected nodes (depth≤2):")
    for node_id in connected:
        print(f"  • {node_id}")
    print()
    
    # Hybrid search demo
    print("🔄 Hybrid Search Demo:")
    query = "learning from data"
    results = kb.hybrid_search(query, top_k=4)
    print(f"Query: '{query}'")
    for result in results:
        print(f"  {result['similarity']:.3f} | {result['node_id']}: {result['content'][:50]}...")
    print()
    
    return kb


def demo_multi_agent_rag(kb):
    """Demonstrate multi-agent RAG system."""
    print("🤖 Multi-Agent RAG Demo")
    print("=" * 50)
    
    rag = MultiAgentRAG(kb)
    
    # Test different types of queries
    queries = [
        "What is machine learning?",
        "How are neural networks and deep learning related?",
        "Compare supervised and unsupervised learning",
        "Explain the relationship between AI, ML, and DL"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 60)
        
        result = rag.process_query(query)
        
        print(f"📝 Summary:")
        print(result['summary'])
        print()
        
        print(f"⭐ Quality Assessment: {result['quality_assessment']}")
        print(f"🎯 Confidence: {result['confidence']:.2f}")
        print(f"📚 Sources: {', '.join(result['sources'])}")
        
        # Show pipeline trace
        trace = result['pipeline_trace']
        print(f"🔧 Pipeline: {trace['research']['strategies']} → "
              f"{trace['research']['results_count']} results → "
              f"quality_score: {trace['critic']['quality_score']:.2f}")
        
        if i < len(queries):
            input("\nPress Enter for next query...")
    
    # Show conversation context
    print(f"\n💬 Conversation Context:")
    context = rag.get_conversation_context()
    for i, item in enumerate(context, 1):
        print(f"  {i}. {item['query']} (confidence: {item['confidence']:.2f})")


def main():
    """Main demo function."""
    print("🚀 Knowledge Base Playground")
    print("=" * 50)
    print("This demo showcases:")
    print("1. Hybrid Knowledge Base (vector + graph)")
    print("2. Multi-Agent RAG Pipeline")
    print("3. Context-aware query processing")
    print()
    
    # Create and demo knowledge base
    kb = demo_hybrid_kb()
    
    input("Press Enter to continue to Multi-Agent RAG demo...")
    
    # Demo multi-agent RAG
    demo_multi_agent_rag(kb)
    
    print("\n✨ Demo Complete!")
    print("This playground demonstrates the research findings:")
    print("• Hybrid storage eliminates synchronization overhead")
    print("• Multi-agent pipeline creates 'short and rich' context")
    print("• Specialized agents handle planning, research, and quality control")


if __name__ == "__main__":
    main()