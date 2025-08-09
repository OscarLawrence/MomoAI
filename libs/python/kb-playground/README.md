# Knowledge Base Playground

A lightweight, dependency-free playground for exploring hybrid knowledge base architectures and multi-agent RAG systems based on research findings.

## Features

### Hybrid Knowledge Base
- **Vector Search**: Semantic similarity using simple character frequency embeddings
- **Graph Traversal**: Relationship-aware navigation through connected concepts
- **Unified Storage**: Single data structure eliminates synchronization overhead

### Multi-Agent RAG Pipeline
- **Planner Agent**: Query analysis and strategy selection
- **Research Agent**: Executes vector, graph, or hybrid search strategies  
- **Summarizer Agent**: Condenses information into concise context
- **Critic Agent**: Quality assessment and validation

## Quick Start

```bash
# Run the interactive demo
python scripts/demo.py

# Run tests
python -m pytest tests/ -v
```

## Architecture

Based on research into multi-agent knowledge bases, this implementation addresses the core challenge of achieving "short and rich" context - information-dense yet concise responses that don't overflow LLM context windows.

### Key Innovations

1. **Unified Hybrid Storage**: Graph database with embedded vectors eliminates sync overhead
2. **Specialized Agent Pipeline**: Role-specific agents for planning, research, synthesis, and critique
3. **Context Engineering**: Self-improving feedback loops with conversation memory

### Research Alignment

This playground validates findings from:
- Hybrid GraphRAG architectures reducing overhead by 40-50%
- Multi-agent RAG systems with specialized roles
- Context engineering flywheels for continuous improvement

## Example Usage

```python
from kb_playground.hybrid_kb import HybridKB
from kb_playground.multi_agent_rag import MultiAgentRAG

# Create knowledge base
kb = HybridKB()
kb.add_node("ml", "Machine learning learns from data")
kb.add_node("dl", "Deep learning uses neural networks") 
kb.add_edge("ml", "dl", "includes")

# Create RAG system
rag = MultiAgentRAG(kb)
result = rag.process_query("What is machine learning?")

print(result['summary'])
print(f"Confidence: {result['confidence']}")
```

## Testing Different Scenarios

The playground supports experimentation with:
- Different query types (factual, relational, comparative)
- Various search strategies (vector, graph, hybrid)
- Agent pipeline configurations
- Quality assessment metrics

Perfect for prototyping before implementing with production dependencies.