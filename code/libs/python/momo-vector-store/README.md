# Momo Store Vector

Vector store implementation for Momo AI knowledge base.

This module provides semantic search capabilities using vector embeddings and similarity search.

ADR-006 decision: production deployments should use Weaviate (primary) or Milvus (fallback). The InMemory backend is for prototyping only (≤10K vectors) and not suitable for production.

## Features

- Vector embedding storage
- Semantic similarity search
- Integration with LangChain vector stores
- Efficient vector operations
- Pluggable backends: InMemory (dev), Chroma, Weaviate, Milvus
- Async-first API

## Usage

```python
from momo_store_vector import VectorStore

store = VectorStore()
store.add_vectors(documents)
results = store.similarity_search("query text")
```
