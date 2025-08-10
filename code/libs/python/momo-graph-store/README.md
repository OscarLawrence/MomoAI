# momo-graph-store

Graph database abstraction layer following LangChain patterns for the MomoAI ecosystem.

## Features

- **LangChain Compatible**: Full compatibility with LangChain's GraphStore interface
- **Standard Data Models**: Uses LangChain's GraphDocument, Node, and Relationship structures
- **InMemory Backend**: Fast development backend with complete graph operations
- **Async-first**: Complete async/await support throughout
- **Type Safe**: Python 3.13+ with complete type annotations
- **Extensible**: Factory pattern for easy backend addition

## Quick Start

```bash
# Install dependencies
pdm install

# Run tests
pdm run test-fast

# Run example
python scripts/01_basic_usage.py
```

## Basic Usage

```python
from momo_graph_store import GraphStore
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from langchain_core.documents import Document

# Initialize with default InMemory backend
store = GraphStore()

# Create nodes and relationships
nodes = [
    Node(id="alice", type="Person", properties={"name": "Alice"}),
    Node(id="bob", type="Person", properties={"name": "Bob"}),
]
relationships = [
    Relationship(source=nodes[0], target=nodes[1], type="KNOWS")
]

# Add to graph store
graph_doc = GraphDocument(nodes=nodes, relationships=relationships, source=Document(page_content=""))
await store.add_graph_documents([graph_doc])

# Query the graph
results = await store.query("MATCH (n:Person) RETURN n")
```

## Architecture

Follows the proven momo-vector-store pattern:

- **Simple Interface**: GraphStore class with sensible defaults
- **Protocol-based Backends**: Clean abstractions for swappable implementations  
- **Factory Pattern**: Backend creation system for extensibility
- **Standard Testing**: unit/e2e/integration test separation

## Development

```bash
# Format code
pdm run format

# Type check
pdm run typecheck

# Run tests
pdm run test-fast
```

Part of the MomoAI ecosystem - see [CLAUDE.md](CLAUDE.md) for detailed development guidance.
