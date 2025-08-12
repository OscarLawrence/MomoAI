# Momo Graph

High-performance, immutable graph database backend with 3-tier storage, diff-based rollback, and advanced indexing capabilities.

## Features

- **11x faster** than Neo4j for node operations (0.009ms vs 0.1ms)
- **450x faster** than Neo4j for property queries (0.44ms vs 200ms) 
- **155K ops/sec** rollback performance with complete version history
- **3-tier storage** with automatic usage-based pruning
- **Memory efficient**: ~1.1KB per node vs 3KB in Neo4j
- **Async-first** design for high concurrency
- **Immutable operations** with INSERT/DELETE only pattern

## Quick Start

```python
from momo_graph import GraphBackend, GraphNode, GraphEdge

async def main():
    async with GraphBackend() as graph:
        # Create a node
        node = GraphNode(label="Person", properties={"name": "Alice"})
        diff = await graph.insert_node(node)
        
        # Query nodes
        result = await graph.query_nodes(label="Person")
        print(f"Found {len(result.nodes)} people")
        
        # Rollback if needed
        await graph.rollback(steps=1)

asyncio.run(main())
```

## Architecture

### 3-Tier Storage System
- **Runtime Tier**: Hot data for immediate access
- **Store Tier**: Frequently accessed data  
- **Cold Tier**: Archived data with compression

### Rollback System
Complete diff-based rollback with operation history and timestamp support.

### Performance Characteristics
- Node operations: <0.009ms
- Property queries: <0.44ms  
- Bulk loading: >46,000 ops/sec
- Memory usage: ~1.1KB per node
- Rollback ops: >155K ops/sec

## Development

```bash
# Setup
pnpm nx run momo-graph:install

# Development workflow
pnpm nx run momo-graph:format
pnpm nx run momo-graph:typecheck  
pnpm nx run momo-graph:test-fast

# Performance validation
pnpm nx run momo-graph:benchmark
```

## Integration

Originally extracted from momo-kb for modularity. Can be used independently or as a backend for knowledge base systems.

```python
# Standalone usage
from momo_graph import GraphBackend

# Via knowledge base integration  
from momo_kb import KnowledgeBase  # Uses GraphBackend internally
```