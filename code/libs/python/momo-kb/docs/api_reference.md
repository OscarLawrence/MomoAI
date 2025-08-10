# Momo KnowledgeBase API Reference

## Overview

The Momo KnowledgeBase provides a high-performance, immutable graph database optimized for multi-agent AI systems. All operations are async and maintain complete audit trails with rollback capability.

## Core Classes

### KnowledgeBase

The main interface for all knowledge base operations.

```python
from momo_kb import KnowledgeBase

async with KnowledgeBase() as kb:
    await kb.initialize()
    # Use kb for operations
```

#### Methods

##### `async initialize() -> None`
Initialize the knowledge base. Must be called before any operations.

##### `async close() -> None`
Close the knowledge base and cleanup resources.

##### `async insert_node(node: Node) -> Diff`
Insert a new node into the knowledge base.

**Parameters:**
- `node`: Node object to insert

**Returns:**
- `Diff`: Operation record for audit trail

**Example:**
```python
from momo_kb import Node

node = Node(
    label="Person",
    properties={"name": "Alice", "age": 30}
)
diff = await kb.insert_node(node)
```

##### `async insert_edge(edge: Edge) -> Diff`
Insert a new edge into the knowledge base.

**Parameters:**
- `edge`: Edge object to insert

**Returns:**
- `Diff`: Operation record for audit trail

**Example:**
```python
from momo_kb import Edge

edge = Edge(
    source_id=alice.id,
    target_id=bob.id,
    relationship="knows",
    properties={"since": 2020}
)
diff = await kb.insert_edge(edge)
```

##### `async delete_node(node_id: str) -> Diff`
Delete a node from the knowledge base.

**Parameters:**
- `node_id`: ID of the node to delete

**Returns:**
- `Diff`: Operation record for audit trail

**Raises:**
- `ValueError`: If node not found

##### `async delete_edge(edge_id: str) -> Diff`
Delete an edge from the knowledge base.

**Parameters:**
- `edge_id`: ID of the edge to delete

**Returns:**
- `Diff`: Operation record for audit trail

**Raises:**
- `ValueError`: If edge not found

##### `async query_nodes(label: str = None, properties: Dict[str, Any] = None) -> QueryResult`
Query nodes by label and/or properties.

**Parameters:**
- `label`: Optional label filter
- `properties`: Optional property filters (AND operation)

**Returns:**
- `QueryResult`: Contains matching nodes and metadata

**Example:**
```python
# Query by label
people = await kb.query_nodes(label="Person")

# Query by properties
engineers = await kb.query_nodes(properties={"department": "Engineering"})

# Combined query
active_engineers = await kb.query_nodes(
    label="Person",
    properties={"department": "Engineering", "active": True}
)
```

##### `async query_edges(relationship: str = None, source_id: str = None, target_id: str = None, properties: Dict[str, Any] = None) -> QueryResult`
Query edges by relationship type and/or node connections.

**Parameters:**
- `relationship`: Optional relationship type filter
- `source_id`: Optional source node filter
- `target_id`: Optional target node filter
- `properties`: Optional property filters

**Returns:**
- `QueryResult`: Contains matching edges and metadata

**Example:**
```python
# Query by relationship
friendships = await kb.query_edges(relationship="friends_with")

# Query by source node
alice_edges = await kb.query_edges(source_id=alice.id)

# Combined query
work_relationships = await kb.query_edges(
    relationship="works_for",
    properties={"since": 2020}
)
```

##### `async query_connected_nodes(start_node_id: str, relationship: str, direction: str = "outgoing") -> QueryResult`
Query nodes connected via specific relationships.

**Parameters:**
- `start_node_id`: Starting node for traversal
- `relationship`: Relationship type to follow
- `direction`: "outgoing", "incoming", or "both"

**Returns:**
- `QueryResult`: Contains connected nodes and metadata

**Example:**
```python
# Find who Alice manages
managed = await kb.query_connected_nodes(
    start_node_id=alice.id,
    relationship="manages",
    direction="outgoing"
)

# Find Alice's manager
manager = await kb.query_connected_nodes(
    start_node_id=alice.id,
    relationship="manages",
    direction="incoming"
)
```

##### `async rollback(steps: int) -> None`
Rollback the last N operations.

**Parameters:**
- `steps`: Number of operations to rollback

**Example:**
```python
# Rollback last 3 operations
await kb.rollback(steps=3)
```

##### `async rollback_to_timestamp(timestamp: datetime) -> None`
Rollback to a specific timestamp.

**Parameters:**
- `timestamp`: Target timestamp to rollback to

##### `async get_diff_history() -> List[Diff]`
Get the complete operation history.

**Returns:**
- `List[Diff]`: All operations in chronological order

##### `async count_nodes(tier: str = None) -> int`
Count nodes in all tiers or a specific tier.

**Parameters:**
- `tier`: Optional tier filter ("runtime", "store", "cold")

**Returns:**
- `int`: Number of nodes

##### `async count_edges(tier: str = None) -> int`
Count edges in all tiers or a specific tier.

**Parameters:**
- `tier`: Optional tier filter ("runtime", "store", "cold")

**Returns:**
- `int`: Number of edges

##### `async prune(runtime_limit: int = None, store_limit: int = None) -> int`
Prune storage tiers to manage memory usage.

**Parameters:**
- `runtime_limit`: Maximum nodes in runtime tier
- `store_limit`: Maximum nodes in store tier

**Returns:**
- `int`: Number of items moved between tiers

##### `async export_json() -> Dict[str, Any]`
Export the entire knowledge base to JSON format.

**Returns:**
- `Dict`: Complete knowledge base data and metadata

### Data Models

#### Node

Immutable graph node with properties and metadata.

```python
from momo_kb import Node

node = Node(
    label="Person",
    properties={"name": "Alice", "age": 30, "active": True}
)
```

**Fields:**
- `id: str` - Unique identifier (auto-generated UUID)
- `label: str` - Node type/category
- `properties: Dict[str, Any]` - Key-value properties
- `created_at: datetime` - Creation timestamp
- `access_count: int` - Usage tracking for pruning
- `last_accessed: datetime` - Last access time

**Methods:**
- `with_access() -> Node` - Return new node with updated access tracking

#### Edge

Immutable graph edge connecting two nodes.

```python
from momo_kb import Edge

edge = Edge(
    source_id=alice.id,
    target_id=bob.id,
    relationship="knows",
    properties={"since": 2020, "strength": 0.8}
)
```

**Fields:**
- `id: str` - Unique identifier (auto-generated UUID)
- `source_id: str` - Source node ID
- `target_id: str` - Target node ID
- `relationship: str` - Relationship type
- `properties: Dict[str, Any]` - Key-value properties
- `created_at: datetime` - Creation timestamp
- `access_count: int` - Usage tracking for pruning
- `last_accessed: datetime` - Last access time

**Methods:**
- `with_access() -> Edge` - Return new edge with updated access tracking

#### Diff

Immutable record of a knowledge graph operation.

```python
from momo_kb import Diff, DiffType

diff = Diff(
    operation=DiffType.INSERT_NODE,
    node=node,
    agent_id="agent_1",
    session_id="session_123"
)
```

**Fields:**
- `id: str` - Unique identifier
- `operation: DiffType` - Type of operation
- `timestamp: datetime` - When operation occurred
- `node: Node` - Node data (for node operations)
- `edge: Edge` - Edge data (for edge operations)
- `agent_id: str` - Optional agent identifier
- `session_id: str` - Optional session identifier

**Methods:**
- `reverse() -> Diff` - Create reverse diff for rollback

#### DiffType

Enumeration of possible operations.

```python
from momo_kb import DiffType

# Available operations
DiffType.INSERT_NODE
DiffType.DELETE_NODE
DiffType.INSERT_EDGE
DiffType.DELETE_EDGE
```

#### QueryResult

Result from a knowledge graph query.

```python
result = await kb.query_nodes(label="Person")

print(f"Found {len(result.nodes)} nodes")
print(f"Query took {result.query_time_ms:.2f}ms")
print(f"Data from {result.storage_tier} tier")
```

**Fields:**
- `nodes: List[Node]` - Matching nodes
- `edges: List[Edge]` - Matching edges
- `metadata: Dict[str, Any]` - Additional query metadata
- `query_time_ms: float` - Query execution time
- `storage_tier: str` - Primary storage tier accessed

## Usage Patterns

### Basic CRUD Operations

```python
async with KnowledgeBase() as kb:
    # Create nodes
    alice = await kb.insert_node(Node(
        label="Person", 
        properties={"name": "Alice", "role": "engineer"}
    ))
    
    # Create relationships
    await kb.insert_edge(Edge(
        source_id=alice.node.id,
        target_id=company.node.id,
        relationship="works_for"
    ))
    
    # Query data
    engineers = await kb.query_nodes(properties={"role": "engineer"})
    
    # Delete if needed
    await kb.delete_node(alice.node.id)
```

### Graph Traversal

```python
# Find all employees of a company
employees = await kb.query_connected_nodes(
    start_node_id=company.id,
    relationship="works_for",
    direction="incoming"
)

# Find Alice's colleagues (2-hop traversal)
alice_company = await kb.query_connected_nodes(
    start_node_id=alice.id,
    relationship="works_for",
    direction="outgoing"
)

if alice_company.nodes:
    colleagues = await kb.query_connected_nodes(
        start_node_id=alice_company.nodes[0].id,
        relationship="works_for",
        direction="incoming"
    )
```

### Rollback and Audit

```python
# Record checkpoint
checkpoint = datetime.utcnow()

# Make some changes
await kb.insert_node(Node(label="Test"))
await kb.insert_node(Node(label="Test2"))

# Rollback if needed
await kb.rollback_to_timestamp(checkpoint)

# Or rollback specific number of operations
await kb.rollback(steps=2)

# View operation history
history = await kb.get_diff_history()
for diff in history[-10:]:  # Last 10 operations
    print(f"{diff.timestamp}: {diff.operation}")
```

### Performance Optimization

```python
# Monitor storage tiers
runtime_count = await kb.count_nodes(tier="runtime")
store_count = await kb.count_nodes(tier="store")

# Prune if needed
if runtime_count > 1000:
    pruned = await kb.prune(runtime_limit=500)
    print(f"Moved {pruned} items to store tier")

# Export for analysis
data = await kb.export_json()
print(f"Total operations: {data['metadata']['total_diffs']}")
```

## Performance Characteristics

### Query Performance
- **Label queries**: ~0.5ms for 1000+ nodes
- **Property queries**: ~0.4ms for specific values
- **Graph traversal**: ~2ms for connected nodes
- **Complex filters**: ~2ms for multi-property queries

### Throughput
- **Node insertion**: 99,000+ ops/sec
- **Bulk loading**: 46,000+ ops/sec
- **Concurrent queries**: 85,000+ ops/sec
- **Rollback operations**: 155,000+ ops/sec

### Memory Usage
- **Per node**: ~1.1KB including metadata and indexes
- **Per edge**: ~0.8KB including metadata and indexes
- **Index overhead**: ~5% of total memory usage

### Storage Tiers
- **Runtime**: Sub-millisecond access
- **Store**: <10ms access with automatic promotion
- **Cold**: <100ms access for archival data

## Error Handling

### Common Exceptions

```python
try:
    await kb.delete_node("nonexistent_id")
except ValueError as e:
    print(f"Node not found: {e}")

try:
    # Invalid node data
    await kb.insert_node(Node(label="", properties={}))
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Best Practices

1. **Always use async context manager**:
   ```python
   async with KnowledgeBase() as kb:
       # Operations here
   ```

2. **Handle rollback carefully**:
   ```python
   # Save checkpoint before risky operations
   checkpoint = datetime.utcnow()
   try:
       # Risky operations
       pass
   except Exception:
       await kb.rollback_to_timestamp(checkpoint)
   ```

3. **Monitor performance**:
   ```python
   result = await kb.query_nodes(label="Person")
   if result.query_time_ms > 100:
       print("Slow query detected, consider optimization")
   ```

4. **Use appropriate query patterns**:
   ```python
   # Efficient: Use indexed properties
   result = await kb.query_nodes(properties={"status": "active"})
   
   # Less efficient: Complex nested properties
   # (Will work but may be slower)
   result = await kb.query_nodes(properties={"metadata": {"nested": "value"}})
   ```