# Vector Storage Module

Semantic similarity search with simple defaults and advanced backend swapping. Two-tier API for both ease-of-use and power users.

## Core Classes

- `VectorStore`: Simple class with defaults (InMemory + LocalEmbeddings)
- `VectorStoreManager`: Advanced LangChain VectorStore operations
- `LocalEmbeddings`: CPU-optimized local embeddings (no external dependencies)

## Quick Start

```python
from momo_vector_store import VectorStore

# Instant usage - no configuration needed
store = VectorStore()
await store.add_texts(["Document 1", "Document 2"])
results = await store.search("query text")
```

## Features

- Zero-configuration defaults for immediate productivity
- Semantic similarity scoring with configurable thresholds
- Local embedding models (no external API dependencies)
- Async-first design for high-concurrency agent systems
- LangChain compatibility for ecosystem integration
- Backend swapping: InMemory → Chroma → Weaviate (runtime switching)

## Local Embedding Models

LocalEmbeddings provides TF-IDF-like vector generation without external dependencies:
- Deterministic embedding generation (same input = same output)
- Vocabulary building from document corpus
- Configurable dimensionality (default: 384)
- No model downloads or external APIs required