# Momo Store Document

Document store implementation for Momo AI knowledge base.

This module provides a unified interface for storing and retrieving documents using various backends including Pandas and DuckDB.

## Features

- Pandas-based document storage
- DuckDB integration for performance
- HDF5 persistence support
- Unified document interface

## Usage

```python
from momo_store_document import DocumentStore

store = DocumentStore()
store.add_document({"content": "Hello world", "metadata": {}})
documents = store.search("Hello")
```
