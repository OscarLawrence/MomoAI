# Momo KnowledgeBase

A modular, async-first knowledge base abstraction for Momo AI with pluggable backend architecture. Designed for multi-agent systems with performance-optimized storage backends and rich metadata support.

## Key Features

- **Async-First Design**: All operations use async/await for LangChain compatibility
- **Pluggable Architecture**: Vector, graph, and document backends can be mixed and matched
- **Performance Optimized**: DuckDB backend provides 28x faster performance than SQLite
- **Rich Metadata**: Comprehensive document metadata with custom fields for agent discovery
- **Type Safety**: Full Python 3.13+ type hints with protocol-based design
- **Local Embeddings**: Built-in sentence transformers for offline semantic search

## Architecture

The knowledge base uses a three-backend architecture with a unified pandas-based document storage:

- **VectorBackend**: Semantic similarity search with local embeddings
- **GraphBackend**: Relationship traversal and graph queries  
- **DocumentBackend**: Unified pandas-based storage with pluggable persistence strategies

### Available Backends

**Document Backends (All Pandas-Based):**
- `memory`: In-memory pandas backend with no persistence (development/testing)
- `csv`: Pandas backend with CSV file persistence (human-readable storage)
- `hdf5`: Pandas backend with HDF5 persistence (compressed, efficient)
- `duckdb`: Pandas backend with DuckDB persistence (production default, ACID transactions)

**Vector Backends:**
- `InMemoryVectorStore`: CPU-optimized local embeddings

**Graph Backends:**
- `InMemoryGraphStore`: Relationship management and traversal

## Quick Start

```python
import asyncio
from momo_kb import Document, DocumentMetadata, SearchOptions, KnowledgeBase

async def main():
    # Create knowledge base with default backends
    async with KnowledgeBase() as kb:
        # Save documents with rich metadata
        await kb.save(
            Document(
                content="Python is a high-level programming language",
                metadata=DocumentMetadata(
                    source="docs",
                    category="programming",
                    tags=["python", "language"],
                    custom={"difficulty": "beginner"}
                )
            )
        )
        
        # Basic semantic search
        results = await kb.search("What is Python?")
        
        # Advanced search with filters
        options = SearchOptions(
            filters={"category": "programming", "custom.difficulty": "beginner"},
            limit=5,
            threshold=0.7
        )
        results = await kb.search("programming languages", options)
        
        # Document management
        doc_count = await kb.count()
        document = await kb.get(results[0].document.id)

asyncio.run(main())
```

## Installation

```bash
# Install dependencies with PDM
pdm install

# For development (includes testing/linting tools)
pdm install --dev

# Install PyTorch for embeddings (CPU version)
pdm add torch --index-url https://download.pytorch.org/whl/cpu
```

## Example Scripts

Comprehensive examples demonstrating different aspects of the knowledge base:

```bash
# Basic usage patterns
pdm run script 01_basic_usage

# Backend performance comparison
pdm run script 02_backend_comparison

# Advanced search strategies
pdm run script 03_search_strategies

# Document management workflows
pdm run script 04_document_management

# Real-world documentation system
pdm run script 05_real_world_example

# List all available scripts
pdm run list-scripts
```

## Development Workflow

### Testing Strategy
```bash
# Fast development cycle (unit + e2e tests)
pdm run test-fast

# Full test suite with coverage
pdm run test-all

# Performance benchmarks
pdm run benchmark

# Stop on first failure
pdm run test-quick
```

### Code Quality
```bash
# Format code (run after editing)
pdm run format

# Type checking
pdm run typecheck

# Style checking
pdm run lint
```

## Performance Characteristics

- **Memory backend**: < 2ms search latency, ideal for development and testing
- **DuckDB backend**: Production-ready with ACID transactions and SQL analytics
- **CSV/HDF5 backends**: Flexible persistence with pandas ecosystem integration
- **Vector search**: Sub-2ms semantic similarity with local embeddings
- **Async operations**: Designed for high-concurrency multi-agent systems

## Multi-Agent Integration

The knowledge base is optimized for agent consumption:

- **Rich metadata** enables agents to find relevant documents via similarity search
- **Custom fields** support domain-specific agent capabilities  
- **Async-first design** integrates seamlessly with LangChain workflows
- **Protocol-based backends** allow runtime backend selection based on workload
