# CLAUDE.md - momo-graph-store

This file provides development guidance for the momo-graph-store module.

## Development Commands

### Python Module (PDM-based)

```bash
# Navigate to module
cd Code/modules/momo-graph-store/

# Development setup - via Nx
pnpm nx run momo-graph-store:install              # Install Poetry dependencies

# MANDATORY Development Workflow (REQUIRED ORDER) - via Nx
pnpm nx run momo-graph-store:format           # Format code immediately after editing - prevents issues
pnpm nx run momo-graph-store:typecheck        # ALWAYS run before testing - prevents confusing failures  
pnpm nx run momo-graph-store:test-fast        # Unit + e2e tests on clean, typed code

# Full testing strategies
pnpm nx run momo-graph-store:test             # Run all tests
pnmp nx run momo-graph-store:test-fast        # Unit + e2e (skip integration) - USE DURING DEVELOPMENT
pnpm nx run momo-graph-store:test-all         # Complete suite with coverage
pnpm nx run momo-graph-store:benchmark        # Performance benchmarks

# Code quality
pnpm nx run momo-graph-store:format           # Format code with black
pnpm nx run momo-graph-store:typecheck        # Type checking with mypy
pnpm nx run momo-graph-store:lint             # Check code style
```

## Architecture Overview

### Graph Store Architecture - COMPLETE

The `momo-graph-store` module provides a unified API for graph database operations following LangChain's GraphStore patterns:

#### 1. Simple GraphStore Class (Recommended)
```python
# Simple usage with sensible defaults
from momo_graph_store import GraphStore
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship

# Default configuration (InMemory backend)
store = GraphStore()
await store.add_graph_documents([graph_doc])
results = await store.query("MATCH (n) RETURN n LIMIT 10")

# Customized usage
store = GraphStore(
    backend_type="memory",
    **config
)
```

#### 2. Factory Pattern (Advanced)
```python
# Direct factory usage for advanced control
from momo_graph_store import create_graph_backend

# Create backend with factory pattern
backend = create_graph_backend(
    backend_type="memory",
    **config
)

# Direct backend operations
await backend.add_graph_documents(graph_documents)
results = await backend.query("MATCH (n) RETURN n")
```

**Implemented Features:**
- **LangChain GraphStore Interface**: Full compatibility with `langchain_community.graphs.graph_store.GraphStore`
- **Standard Data Models**: Uses LangChain's `GraphDocument`, `Node`, `Relationship` structures
- **InMemory Backend**: Fast development backend with full graph operations
- **Async-first**: Complete async/await support throughout
- **Type Safety**: Python 3.13+ with complete typing
- **Factory Pattern**: Extensible backend creation system
- **Query Interface**: Support for graph query languages (basic pattern matching for InMemory)

**Performance Characteristics:**
- InMemory backend: < 1ms for most operations, ideal for development (< 10K nodes)
- Data loading: ~0.5ms for 1000 nodes + 1500 relationships
- Query performance: < 0.3ms for complex relationship queries
- Schema operations: < 0.2ms for introspection and refresh
- Multi-agent ready: Designed for high-concurrency agent systems

### Backend Architecture

```bash
src/momo_graph_store/
├── main.py             # GraphStore class with sensible defaults
├── backends/           # Backend implementations
│   ├── __init__.py     # Backend exports
│   ├── memory.py       # InMemoryGraphBackend
│   └── base.py         # Backend protocols and base classes
├── factory.py          # Backend creation and configuration
├── exceptions.py       # Graph store specific exceptions
└── __init__.py         # Public API exports
```

## LangChain Research Findings

### LangChain GraphStore Interface (Required Implementation)

Based on deep research into LangChain's graph architecture, the following interface must be implemented:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_community.graphs.graph_document import GraphDocument

class GraphStore(ABC):
    """Abstract class for graph operations."""
    
    @property
    @abstractmethod
    def get_schema(self) -> str:
        """Return the schema of the Graph database"""
        pass
    
    @property
    @abstractmethod  
    def get_structured_schema(self) -> Dict[str, Any]:
        """Return the schema of the Graph database"""
        pass
    
    @abstractmethod
    def query(self, query: str, params: dict = {}) -> List[Dict[str, Any]]:
        """Query the graph."""
        pass
    
    @abstractmethod
    def refresh_schema(self) -> None:
        """Refresh the graph schema information."""
        pass
    
    @abstractmethod
    def add_graph_documents(
        self, graph_documents: List[GraphDocument], include_source: bool = False
    ) -> None:
        """Take GraphDocument as input as uses it to construct a graph."""
        pass
```

### LangChain Graph Data Models

```python
# Core Data Structures (from langchain_community.graphs.graph_document)
class Node:
    id: str                    # Unique identifier  
    type: str                  # Node category (Person, Organization, etc.)
    properties: Dict[str, Any] # Additional node properties

class Relationship:
    source: Node               # Source node
    target: Node               # Target node  
    type: str                  # Relationship type (KNOWS, WORKS_AT, etc.)
    properties: Dict[str, Any] # Additional relationship properties

class GraphDocument:
    nodes: List[Node]          # Graph nodes
    relationships: List[Relationship] # Graph relationships
    source: Document           # Original document source
```

### Architecture Comparison: GraphStore vs VectorStore

| Aspect | VectorStore | GraphStore |
|--------|-------------|------------|
| **Core Abstraction** | `VectorStore` (langchain_core) | `GraphStore` (langchain_community) |
| **Data Model** | `Document` + embeddings | `GraphDocument` + `Node` + `Relationship` |
| **Primary Operations** | `add_documents()`, `similarity_search()` | `add_graph_documents()`, `query()` |
| **Backend Focus** | Semantic similarity | Structural relationships |
| **Query Language** | Vector similarity | Graph queries (Cypher-like) |

### Integration Benefits

- **Ecosystem Compatibility**: Direct integration with LangChain graph chains and tools
- **Tool Interoperability**: Works with existing LangChain graph retrieval systems
- **Knowledge Graph RAG**: Natural integration with knowledge graph retrieval patterns
- **Future-Proof**: Easy migration to production graph databases (Neo4j, MemGraph)

## Development Standards

### Code Quality
- **100% test coverage** for production code
- **Type safety**: Full type hints throughout
- **Async patterns**: All operations use async/await
- **LangChain compatibility**: Follow LangChain GraphStore protocols exactly
- **Performance awareness**: Benchmark all implementations

### Testing Architecture

```bash
tests/
├── unit/          # Fast isolated tests (< 1s)
├── e2e/           # End-to-end workflow tests (1-5s)
└── integration/   # Backend integration tests (1-10s)

benchmarks/        # Performance benchmarks (< 5s for standard tests)
├── performance_benchmarks.py  # Core benchmark suite
└── run.py                     # Benchmark runner
```

### Multi-Agent Considerations
- **Async-first design**: All operations designed for high-concurrency
- **Backend swapping**: Runtime backend switching for different use cases
- **Standard interface**: LangChain compatibility for tool integration
- **Graph traversal**: Optimized relationship discovery and path finding

## Backend Configuration

### Simple Usage (Default)
```python
# Uses InMemory backend automatically
from momo_graph_store import GraphStore

store = GraphStore()  # Defaults: backend_type="memory"
```

### Advanced Factory Usage
```python
# Direct factory control
from momo_graph_store import create_graph_backend

backend = create_graph_backend(
    backend_type="memory"
)
```

### Future Backends (Planned)
```python
# Neo4j (production graph database)
backend = create_graph_backend(
    backend_type="neo4j",
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# MemGraph (high-performance analytics)
backend = create_graph_backend(
    backend_type="memgraph",
    host="localhost",
    port=7687
)
```

## Key Implementation Details

### Factory Pattern
- **Backend abstraction**: Single `create_graph_backend()` function
- **Configuration flexibility**: Backend-specific options via kwargs
- **Runtime switching**: Easy backend swapping for different environments

### LangChain Integration
- **GraphDocument compatibility**: Uses `langchain_community.graphs.graph_document`
- **GraphStore protocol**: Implements LangChain GraphStore interface exactly
- **Ecosystem access**: Compatible with entire LangChain graph ecosystem

### Error Handling Strategy
- **Custom exceptions**: `GraphStoreError`, `NodeNotFoundError`, `QueryError`
- **Async error context**: Comprehensive error information in async operations
- **Fallback strategies**: Graceful degradation when operations fail

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
2. **Follow LangChain patterns**: Use GraphStore protocols and GraphDocument types
3. **Use type hints**: Full type safety with Python 3.13+ features
4. **Apply development flow**: Edit → Format → Typecheck → Test
5. **Validate performance**: Run benchmarks for new implementations

## Repository Conventions

- **Self-contained module** with own dependencies
- **LangChain compatibility**: Follow LangChain patterns and protocols exactly
- **Performance first**: All decisions backed by benchmarks  
- **Modularity over performance**: Design for backend flexibility
- **Scientific approach**: Research-backed technology choices
- **Long-term focus**: Code written for decades of maintainability

The module leverages LangChain's mature GraphStore ecosystem while providing a clean, swappable backend architecture for the MomoAI knowledge base system.