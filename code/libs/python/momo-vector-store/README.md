# Momo Store Vector

Vector store implementation for Momo AI knowledge base.

This module provides semantic search capabilities using vector embeddings and similarity search.

## Features

- Vector embedding storage
- Semantic similarity search
- Integration with langchain vector stores
- Efficient vector operations

## Usage

```python
from momo_store_vector import VectorStore

store = VectorStore()
store.add_vectors(documents)
results = store.similarity_search("query text")
```
