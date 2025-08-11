# CLAUDE.md - momo-vector-store

This file provides development guidance for the momo-vector-store module.

## Development Commands

### Python Module (PDM-based)

```bash
# Navigate to module
cd Code/modules/momo-vector-store/

# Development setup - via Nx
pnpm nx run momo-vector-store:install              # Install Poetry dependencies

# MANDATORY Development Workflow (REQUIRED ORDER) - via Nx
pnpm nx run momo-vector-store:format           # Format code immediately after editing - prevents issues
pnpm nx run momo-vector-store:typecheck        # ALWAYS run before testing - prevents confusing failures  
pnpm nx run momo-vector-store:test-fast        # Unit + e2e tests on clean, typed code

# Full testing strategies
pnpm nx run momo-vector-store:test             # Run all tests
pnpm nx run momo-vector-store:test-fast        # Unit + e2e (skip integration) - USE DURING DEVELOPMENT
pnpm nx run momo-vector-store:test-all         # Complete suite with coverage
pnpm nx run momo-vector-store:benchmark        # Performance benchmarks

# Code quality
pnpm nx run momo-vector-store:format           # Format code with black
pnpm nx run momo-vector-store:typecheck        # Type checking with mypy
pnpm nx run momo-vector-store:lint             # Check code style
```

## Architecture Overview

### Vector Store Architecture - COMPLETE

The `momo-vector-store` module provides a unified API for vector storage with two main interfaces:

#### 1. Simple VectorStore Class (Recommended)
```python
# Simple usage with sensible defaults
from momo_vector_store import VectorStore

# Default configuration (InMemory + LocalEmbeddings)
store = VectorStore()
await store.add_texts(["Hello world", "Python rocks"])
results = await store.search("greeting")

# Customized usage
store = VectorStore(
    backend_type="memory",
    embeddings=custom_embeddings,
    **config
)
```

#### 2. Factory Pattern (Advanced)
```python
# Direct factory usage for advanced control
from momo_vector_store import create_vectorstore
from langchain_core.documents import Document

# Create backend with factory pattern
vectorstore = create_vectorstore(
    backend_type="memory",  # or "chroma", "weaviate", etc.
    embeddings=embeddings,
    **config
)

# Standard LangChain VectorStore interface
await vectorstore.aadd_texts(["text1", "text2"])
results = await vectorstore.asimilarity_search("query", k=5)
```

**Implemented Features:**
- **Simple Interface**: VectorStore class with sensible defaults (InMemory + LocalEmbeddings)
- **LangChain Integration**: Uses LangChain VectorStore abstractions directly
- **Dual API**: Simple VectorStore class for ease-of-use, factory pattern for advanced control
- **Backend Support**: InMemory (development), extensible to Chroma, Weaviate, etc.
- **Async-first**: Full async support throughout
- **Type Safety**: Python 3.13+ with complete typing
- **Standard Documents**: Uses LangChain Document instead of custom types
- **Local Embeddings**: No external dependencies with LocalEmbeddings by default

**Performance Characteristics:**
- InMemory backend: < 2ms search, ideal for development (< 10K docs)
- Extensible to production backends: Chroma, Weaviate, Pinecone
- Vector search: Semantic similarity with configurable embedding models
- Multi-agent ready: Designed for high-concurrency agent systems

### Backend Architecture

```bash
src/momo_vector_store/
├── main.py             # VectorStore class with sensible defaults
├── manager.py          # VectorStoreManager for advanced operations
├── factory.py          # Backend creation and configuration
├── embeddings.py       # LocalEmbeddings implementation
├── exceptions.py       # Vector store specific exceptions
└── __init__.py         # Public API exports
```

## Logging

- Preferred: momo-logger for structured, async-friendly logging across the codebase
- In this module: we use momo_logger when available; otherwise, a thin stdlib adapter at `momo_vector_store/logger.py` provides compatible methods (ai_user, ai_system, info, warning, error)

## Development Standards

### Code Quality
- **100% test coverage** for production code
- **Type safety**: Full type hints throughout
- **Async patterns**: All operations use async/await
- **LangChain compatibility**: Follow LangChain VectorStore protocols
- **Performance awareness**: Benchmark all implementations

### Testing Architecture

```bash
tests/
├── unit/          # Fast isolated tests (< 1s)
├── e2e/           # End-to-end workflow tests (1-5s)
└── integration/   # Backend integration tests (1-10s)

benchmarks/        # Performance benchmarks (10s+)
```

### Multi-Agent Considerations
- **Async-first design**: All operations designed for high-concurrency
- **Backend swapping**: Runtime backend switching for different use cases
- **Standard interface**: LangChain compatibility for tool integration
- **Embedding management**: Local models with fallback strategies

## Backend Configuration

### Simple Usage (Default)
```python
# Uses InMemory backend with LocalEmbeddings automatically
from momo_vector_store import VectorStore

store = VectorStore()  # Defaults: backend_type="memory", embeddings=LocalEmbeddings()
```

### Advanced Factory Usage
```python
# Direct factory control
from momo_vector_store import create_vectorstore

vectorstore = create_vectorstore(
    backend_type="memory",
    embeddings=embeddings
)
```

### Future Backends
```python
# Chroma (persistent local storage)
vectorstore = create_vectorstore(
    backend_type="chroma",
    embeddings=embeddings,
    persist_directory="./chroma_db"
)

# Weaviate (enterprise scale)
vectorstore = create_vectorstore(
    backend_type="weaviate", 
    embeddings=embeddings,
    url="http://localhost:8080"
)
```

## Key Implementation Details

### Factory Pattern
- **Backend abstraction**: Single `create_vectorstore()` function
- **Configuration flexibility**: Backend-specific options via kwargs
- **Runtime switching**: Easy backend swapping for different environments

### LangChain Integration
- **Document compatibility**: Uses `langchain_core.documents.Document`
- **VectorStore protocol**: Implements LangChain VectorStore interface
- **Ecosystem access**: Compatible with entire LangChain ecosystem

### Error Handling Strategy
- **Custom exceptions**: `VectorStoreError`, `EmbeddingError`, `BackendError`
- **Async error context**: Comprehensive error information in async operations
- **Fallback strategies**: Graceful degradation when backends fail

## Development Workflow

### Optimal Development Flow (REQUIRED ORDER)

**During development:**
1. **Edit code** freely with focus on functionality  
2. **Format immediately**: Run `pdm run format` after editing files
3. **Continue editing** - formatting is now handled transparently

**Before testing/validation (MANDATORY ORDER):**
1. **Type check FIRST**: `pdm run typecheck` - catch type issues before functionality testing
2. **Test functionality**: `pdm run test-fast` - validate working code only after types are clean
3. **Never skip typecheck** - type errors will cause confusing test failures

### When Adding New Features

1. **Start with tests**: Write failing tests first (TDD approach)
2. **Follow LangChain patterns**: Use VectorStore protocols and Document types
3. **Use type hints**: Full type safety with Python 3.13+ features
4. **Apply development flow**: Edit → Format → Typecheck → Test
5. **Validate performance**: Run benchmarks for new implementations

## Repository Conventions

- **Self-contained module** with own dependencies
- **LangChain compatibility**: Follow LangChain patterns and protocols
- **Performance first**: All decisions backed by benchmarks  
- **Modularity over performance**: Design for backend flexibility
- **Scientific approach**: Research-backed technology choices
- **Long-term focus**: Code written for decades of maintainability

The module leverages LangChain's mature VectorStore ecosystem while providing a clean, swappable backend architecture for the MomoAI knowledge base system.