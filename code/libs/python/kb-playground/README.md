# KB Playground

🎮 **Experimental High-Performance Knowledge Base with Vector-Graph Hybrid Architecture**

An immutable, DVC-integrated knowledge base designed for outstanding query quality and agent context building. Features relationship-aware vector search, per-operation versioning, and fast rollback capabilities.

## 🚀 Features

- **Simple API**: `search()`, `get()`, `add()`, `roll()`, `delete()`
- **Immutable Design**: Every operation creates a new version
- **DVC Integration**: Reproducible knowledge management with version control
- **Vector-Graph Hybrid**: Combines semantic similarity with explicit relationships
- **Relationship-Aware Search**: Context enrichment through graph connectivity
- **Per-Caller Enrichment**: Customizable query behavior per agent/collection
- **Fast Rollback**: Explore different knowledge states efficiently
- **Auto-Discovery**: Intelligent relationship detection from usage patterns
- **Performance Optimized**: Designed for speed and memory efficiency

## 🏗️ Architecture

### Vector Lattice
Documents are embedded as vectors in high-dimensional space with explicit relationships providing additional context for similarity computation.

### Relationship Engine
Automatically discovers implicit relationships through:
- Semantic similarity clustering
- Co-access pattern analysis
- Content overlap detection
- Temporal proximity analysis

### Immutable Snapshots
Each operation creates a new snapshot, enabling:
- Perfect rollback capabilities
- Audit trails for all changes
- DVC-tracked reproducibility
- Multi-version exploration

## 🎯 Quick Start

```python
from kb_playground import KnowledgeBase, Document

# Initialize knowledge base
kb = KnowledgeBase(
    dimension=384,
    auto_discover_relationships=True,
    enable_dvc=True
)

# Add documents
doc_ids = kb.add(
    "Python is a versatile programming language.",
    Document(
        content="Machine learning enables computers to learn from data.",
        metadata={"category": "ai", "difficulty": "intermediate"}
    )
)

# Search with relationship awareness
result = kb.search(
    "programming language", 
    top_k=5,
    caller_id="my_agent"
)

print(f"Found {len(result.documents)} documents")
print(f"Related relationships: {len(result.relationships)}")

# Get specific documents
documents = kb.get(*doc_ids)

# Roll back operations
kb.roll(1)  # Undo last operation

# Delete documents
kb.delete(doc_ids[0])
```

## 🔧 Configuration

### Query Enrichment
Configure per-caller or per-collection behavior:

```python
# Global configuration
kb.configure_enrichment(
    expansion_factor=2.0,
    relationship_depth=3,
    semantic_threshold=0.8
)

# Per-agent configuration
kb.configure_enrichment(
    caller_id="research_agent",
    expansion_factor=3.0,
    include_metadata_fields=["category", "difficulty"]
)

# Per-collection configuration
kb.configure_enrichment(
    collection="scientific_papers",
    relationship_depth=4,
    semantic_threshold=0.9
)
```

### Relationship Discovery
Control automatic relationship discovery:

```python
kb = KnowledgeBase(
    auto_discover_relationships=True,
    # Relationship engine parameters
)

# Manual relationship discovery
kb._relationship_engine.similarity_threshold = 0.8
kb._relationship_engine.co_access_threshold = 5
```

## 📊 Performance

Based on initial benchmarks:

| Operation | Performance | Notes |
|-----------|-------------|-------|
| Document Insertion | ~1000+ docs/sec | Batch processing optimized |
| Search Latency | <10ms avg | Relationship-aware search |
| Memory Usage | ~1-2 KB/doc | Efficient vector storage |
| Rollback Speed | <5ms | Snapshot-based rollback |

Run benchmarks:
```bash
uv run python benchmarks/performance_benchmarks.py
```

## 🧪 Testing

Run the test suite:
```bash
# All tests
uv run pytest

# Specific test categories
uv run pytest tests/test_knowledge_base.py
uv run pytest tests/test_vector_lattice.py
uv run pytest tests/test_embedding_engine.py

# With coverage
uv run pytest --cov=kb_playground
```

## 📈 Benchmarking

Comprehensive performance analysis:
```bash
# Run all benchmarks
nx run kb-playground:benchmark

# Or directly
uv run python benchmarks/performance_benchmarks.py
```

## 🎮 Examples

### Basic Usage
```bash
uv run python scripts/basic_usage_demo.py
```

### Advanced Features
```python
# Multi-version exploration
kb.add("Initial knowledge")
version_1 = kb._current_version

kb.add("Additional knowledge") 
version_2 = kb._current_version

# Explore different states
kb.roll(1)  # Back to version_1
# ... do some work ...
kb.roll(-1)  # Forward to version_2
```

### Relationship Analytics
```python
# Get relationship insights
analytics = kb._relationship_engine.get_relationship_analytics()
print(f"Co-access patterns: {analytics['total_co_accesses']}")

# Access tracking for relationship discovery
result = kb.search("machine learning")  # Automatically tracked
```

## 🔬 Design Philosophy

### Query Quality First
- Relationship-aware similarity boosts connected documents
- Context expansion through graph traversal
- Per-caller query transformation pipelines
- Semantic and structural relevance combination

### Immutability & Versioning
- Every operation creates a new state
- Perfect audit trails and reproducibility
- Fast rollback for agent exploration
- DVC integration for knowledge provenance

### Performance & Efficiency
- Optimized vector operations with NumPy
- Efficient relationship storage and traversal
- Memory-conscious design for large knowledge bases
- Designed for future Rust porting

## 🛠️ Development

### Project Structure
```
kb_playground/
├── knowledge_base.py      # Main API interface
├── vector_lattice.py      # Vector-graph hybrid core
├── relationship_engine.py # Relationship discovery
├── embedding_engine.py    # Lightweight embeddings
├── dvc_manager.py         # DVC integration
└── models.py             # Data models
```

### Dependencies
- **Core**: `numpy`, `pydantic`
- **Versioning**: `dvc`
- **Development**: `pytest`, `pytest-benchmark`
- **No heavy ML dependencies** - designed for lightweight deployment

## 🎯 Future Roadmap

### Short-term
- [ ] Query result caching
- [ ] Advanced relationship types
- [ ] Performance optimizations
- [ ] Extended benchmarking

### Medium-term
- [ ] Distributed deployment support
- [ ] Advanced embedding models integration
- [ ] Query planning optimization
- [ ] Compression algorithms

### Long-term
- [ ] Rust implementation for performance
- [ ] GPU acceleration support
- [ ] Federated knowledge base queries
- [ ] ML-based relationship prediction

## 📄 License

This is an experimental project for research and development purposes.

## 🤝 Contributing

This is currently an experimental playground. Feedback and suggestions are welcome!

---

**Built with ❤️ for outstanding query quality and agent context building**