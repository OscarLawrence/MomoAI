# Momo KnowledgeBase User Guide

## Getting Started

### Installation

```bash
# Install from source
git clone <repository>
cd momo-kb
uv install
```

### Quick Start

```python
import asyncio
from momo_kb import KnowledgeBase, Node, Edge

async def main():
    async with KnowledgeBase() as kb:
        await kb.initialize()
        
        # Create some data
        alice = await kb.insert_node(Node(
            label="Person",
            properties={"name": "Alice", "role": "engineer"}
        ))
        
        bob = await kb.insert_node(Node(
            label="Person", 
            properties={"name": "Bob", "role": "designer"}
        ))
        
        # Create relationship
        await kb.insert_edge(Edge(
            source_id=alice.node.id,
            target_id=bob.node.id,
            relationship="collaborates_with"
        ))
        
        # Query the data
        engineers = await kb.query_nodes(properties={"role": "engineer"})
        print(f"Found {len(engineers.nodes)} engineers")

asyncio.run(main())
```

## Core Concepts

### Immutable Operations

Momo KnowledgeBase uses an immutable data model where you can only INSERT and DELETE - never UPDATE. This provides several benefits:

- **Complete audit trail** of all changes
- **Rollback capability** to any previous state
- **Concurrency safety** without locks
- **Agent debugging** capabilities

```python
# Instead of updating, delete and re-insert
old_alice = await kb.query_nodes(properties={"name": "Alice"})
await kb.delete_node(old_alice.nodes[0].id)

new_alice = await kb.insert_node(Node(
    label="Person",
    properties={"name": "Alice", "role": "senior_engineer"}  # Updated role
))
```

### Three-Tier Storage

Data automatically moves between storage tiers based on usage:

- **Runtime**: Hot data in memory (sub-millisecond access)
- **Store**: Warm data with indexing (millisecond access)  
- **Cold**: Archival data (sub-second access)

```python
# Check storage distribution
runtime_nodes = await kb.count_nodes(tier="runtime")
store_nodes = await kb.count_nodes(tier="store")
cold_nodes = await kb.count_nodes(tier="cold")

print(f"Runtime: {runtime_nodes}, Store: {store_nodes}, Cold: {cold_nodes}")

# Manually trigger pruning if needed
pruned = await kb.prune(runtime_limit=1000, store_limit=10000)
print(f"Moved {pruned} items between tiers")
```

### Diff-Based History

Every operation creates a diff record that can be used for rollback:

```python
# View recent operations
history = await kb.get_diff_history()
for diff in history[-5:]:
    print(f"{diff.timestamp}: {diff.operation} - {diff.id}")

# Rollback last 3 operations
await kb.rollback(steps=3)

# Or rollback to specific time
from datetime import datetime, timedelta
checkpoint = datetime.utcnow() - timedelta(minutes=5)
await kb.rollback_to_timestamp(checkpoint)
```

## Working with Nodes

### Creating Nodes

```python
# Basic node
person = await kb.insert_node(Node(
    label="Person",
    properties={"name": "Alice", "age": 30}
))

# Node with complex properties
project = await kb.insert_node(Node(
    label="Project",
    properties={
        "name": "AI Assistant",
        "status": "active",
        "team_size": 5,
        "technologies": ["Python", "LangChain", "FastAPI"],
        "metadata": {
            "created_by": "alice",
            "priority": "high"
        }
    }
))
```

### Querying Nodes

```python
# Query by label
all_people = await kb.query_nodes(label="Person")

# Query by single property
active_projects = await kb.query_nodes(properties={"status": "active"})

# Query by multiple properties (AND operation)
senior_engineers = await kb.query_nodes(
    label="Person",
    properties={"role": "engineer", "level": "senior"}
)

# Query with no filters (returns all nodes)
all_nodes = await kb.query_nodes()
```

### Property Types and Indexing

Momo KB supports all JSON-serializable types:

```python
node = await kb.insert_node(Node(
    label="Example",
    properties={
        "string_prop": "hello",
        "int_prop": 42,
        "float_prop": 3.14,
        "bool_prop": True,
        "list_prop": [1, 2, 3],
        "dict_prop": {"nested": "value"},
        "null_prop": None  # Note: None values are allowed
    }
))
```

**Performance Note**: Only hashable types (str, int, float, bool, tuple) are indexed for fast queries. Lists and dicts are stored but queries on them use full scans.

## Working with Edges

### Creating Relationships

```python
# Basic relationship
friendship = await kb.insert_edge(Edge(
    source_id=alice.node.id,
    target_id=bob.node.id,
    relationship="friends_with"
))

# Relationship with properties
employment = await kb.insert_edge(Edge(
    source_id=alice.node.id,
    target_id=company.node.id,
    relationship="works_for",
    properties={
        "start_date": "2020-01-15",
        "role": "Senior Engineer",
        "salary": 120000,
        "remote": True
    }
))
```

### Querying Relationships

```python
# All edges of a specific type
friendships = await kb.query_edges(relationship="friends_with")

# Edges from a specific node
alice_edges = await kb.query_edges(source_id=alice.node.id)

# Edges to a specific node
company_employees = await kb.query_edges(target_id=company.node.id)

# Edges with specific properties
recent_hires = await kb.query_edges(
    relationship="works_for",
    properties={"start_date": "2023-01-01"}
)
```

### Graph Traversal

```python
# Find direct connections
alice_friends = await kb.query_connected_nodes(
    start_node_id=alice.node.id,
    relationship="friends_with",
    direction="outgoing"
)

# Find who follows Alice
alice_followers = await kb.query_connected_nodes(
    start_node_id=alice.node.id,
    relationship="follows",
    direction="incoming"
)

# Bidirectional relationships
alice_connections = await kb.query_connected_nodes(
    start_node_id=alice.node.id,
    relationship="connected_to",
    direction="both"
)
```

## Advanced Usage Patterns

### Multi-Hop Traversal

```python
async def find_friends_of_friends(kb, person_id):
    """Find friends of friends (2-hop traversal)."""
    # Get direct friends
    friends = await kb.query_connected_nodes(
        start_node_id=person_id,
        relationship="friends_with",
        direction="both"
    )
    
    # Get friends of each friend
    friends_of_friends = set()
    for friend in friends.nodes:
        fof = await kb.query_connected_nodes(
            start_node_id=friend.id,
            relationship="friends_with", 
            direction="both"
        )
        friends_of_friends.update(node.id for node in fof.nodes)
    
    # Remove original person and direct friends
    friends_of_friends.discard(person_id)
    direct_friend_ids = {friend.id for friend in friends.nodes}
    friends_of_friends -= direct_friend_ids
    
    return friends_of_friends

# Usage
fof_ids = await find_friends_of_friends(kb, alice.node.id)
```

### Batch Operations

```python
async def bulk_insert_people(kb, people_data):
    """Efficiently insert multiple people."""
    people = []
    for person_data in people_data:
        person = await kb.insert_node(Node(
            label="Person",
            properties=person_data
        ))
        people.append(person.node)
    return people

# Usage
people_data = [
    {"name": "Alice", "role": "engineer"},
    {"name": "Bob", "role": "designer"},
    {"name": "Charlie", "role": "manager"}
]
people = await bulk_insert_people(kb, people_data)
```

### Complex Queries

```python
async def find_project_team(kb, project_id):
    """Find all people working on a project."""
    # Find people assigned to project
    team_members = await kb.query_connected_nodes(
        start_node_id=project_id,
        relationship="assigned_to",
        direction="incoming"
    )
    
    # Get additional details for each team member
    team_details = []
    for member in team_members.nodes:
        # Find their role on the project
        assignment = await kb.query_edges(
            source_id=member.id,
            target_id=project_id,
            relationship="assigned_to"
        )
        
        role = assignment.edges[0].properties.get("role", "unknown")
        team_details.append({
            "person": member,
            "role": role
        })
    
    return team_details
```

### Temporal Queries

```python
async def find_recent_activity(kb, hours=24):
    """Find all operations in the last N hours."""
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    history = await kb.get_diff_history()
    
    recent_ops = [
        diff for diff in history 
        if diff.timestamp > cutoff
    ]
    
    return recent_ops

# Usage
recent = await find_recent_activity(kb, hours=1)
print(f"Found {len(recent)} operations in the last hour")
```

## Performance Optimization

### Query Optimization

```python
# Efficient: Use indexed properties
engineers = await kb.query_nodes(properties={"role": "engineer"})

# Less efficient: Complex nested properties
# (Still works, but slower)
special_projects = await kb.query_nodes(
    properties={"metadata": {"priority": "high"}}
)

# Most efficient: Combine label and simple properties
senior_engineers = await kb.query_nodes(
    label="Person",
    properties={"role": "engineer", "level": "senior"}
)
```

### Memory Management

```python
# Monitor memory usage
total_nodes = await kb.count_nodes()
runtime_nodes = await kb.count_nodes(tier="runtime")

memory_usage_pct = (runtime_nodes / total_nodes) * 100
print(f"Runtime tier: {memory_usage_pct:.1f}% of total data")

# Trigger pruning if memory usage is high
if memory_usage_pct > 80:
    pruned = await kb.prune(runtime_limit=int(total_nodes * 0.5))
    print(f"Pruned {pruned} items to reduce memory usage")
```

### Query Performance Monitoring

```python
async def monitored_query(kb, **query_args):
    """Query with performance monitoring."""
    result = await kb.query_nodes(**query_args)
    
    if result.query_time_ms > 100:
        print(f"Slow query detected: {result.query_time_ms:.2f}ms")
        print(f"Query: {query_args}")
        print(f"Results: {len(result.nodes)} nodes")
        print(f"Storage tier: {result.storage_tier}")
    
    return result
```

## Error Handling and Best Practices

### Exception Handling

```python
from pydantic import ValidationError

async def safe_node_creation(kb, label, properties):
    """Safely create a node with error handling."""
    try:
        node = await kb.insert_node(Node(
            label=label,
            properties=properties
        ))
        return node
    except ValidationError as e:
        print(f"Invalid node data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Usage
node = await safe_node_creation(kb, "Person", {"name": "Alice"})
if node:
    print(f"Created node: {node.node.id}")
```

### Rollback Safety

```python
async def safe_operation_with_rollback(kb, operation_func):
    """Execute operation with automatic rollback on error."""
    # Record state before operation
    initial_history_length = len(await kb.get_diff_history())
    
    try:
        result = await operation_func(kb)
        return result
    except Exception as e:
        # Calculate how many operations to rollback
        current_history_length = len(await kb.get_diff_history())
        operations_to_rollback = current_history_length - initial_history_length
        
        if operations_to_rollback > 0:
            await kb.rollback(steps=operations_to_rollback)
            print(f"Rolled back {operations_to_rollback} operations due to error")
        
        raise e

# Usage
async def risky_operation(kb):
    # Some operations that might fail
    await kb.insert_node(Node(label="Test"))
    await kb.insert_node(Node(label="Test2"))
    raise Exception("Something went wrong!")

try:
    await safe_operation_with_rollback(kb, risky_operation)
except Exception:
    print("Operation failed but state was restored")
```

### Resource Management

```python
# Always use async context manager
async with KnowledgeBase() as kb:
    await kb.initialize()
    # Operations here
    # Automatic cleanup on exit

# For long-running applications
class KnowledgeBaseManager:
    def __init__(self):
        self.kb = None
    
    async def start(self):
        self.kb = KnowledgeBase()
        await self.kb.initialize()
    
    async def stop(self):
        if self.kb:
            await self.kb.close()
            self.kb = None
    
    async def __aenter__(self):
        await self.start()
        return self.kb
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

# Usage
async with KnowledgeBaseManager() as kb:
    # Long-running operations
    pass
```

## Integration Examples

### LangChain Integration

```python
from langchain.schema import Document
from momo_kb import KnowledgeBase, Node

async def store_documents_in_kb(kb, documents):
    """Store LangChain documents in knowledge base."""
    for doc in documents:
        await kb.insert_node(Node(
            label="Document",
            properties={
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "unknown")
            }
        ))

async def retrieve_documents_from_kb(kb, source=None):
    """Retrieve documents from knowledge base."""
    if source:
        result = await kb.query_nodes(
            label="Document",
            properties={"source": source}
        )
    else:
        result = await kb.query_nodes(label="Document")
    
    documents = []
    for node in result.nodes:
        doc = Document(
            page_content=node.properties["content"],
            metadata=node.properties["metadata"]
        )
        documents.append(doc)
    
    return documents
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

# Global KB instance
kb_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global kb_manager
    kb_manager = KnowledgeBaseManager()
    await kb_manager.start()
    yield
    await kb_manager.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/nodes/")
async def create_node(label: str, properties: dict):
    try:
        node = await kb_manager.kb.insert_node(Node(
            label=label,
            properties=properties
        ))
        return {"id": node.node.id, "label": label}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/nodes/")
async def query_nodes(label: str = None):
    result = await kb_manager.kb.query_nodes(label=label)
    return {
        "nodes": [
            {"id": node.id, "label": node.label, "properties": node.properties}
            for node in result.nodes
        ],
        "count": len(result.nodes),
        "query_time_ms": result.query_time_ms
    }
```

## Troubleshooting

### Common Issues

**Slow Queries**:
```python
# Check if you're querying unhashable properties
result = await kb.query_nodes(properties={"complex_data": [1, 2, 3]})
# This will be slow - use simpler properties for filtering

# Better approach
result = await kb.query_nodes(properties={"category": "complex"})
# Then filter in application code
```

**Memory Usage**:
```python
# Monitor and manage memory
if await kb.count_nodes(tier="runtime") > 10000:
    await kb.prune(runtime_limit=5000)
```

**Rollback Issues**:
```python
# Always check history before large rollbacks
history = await kb.get_diff_history()
print(f"Total operations: {len(history)}")

# Be careful with rollback steps
if steps_to_rollback <= len(history):
    await kb.rollback(steps=steps_to_rollback)
```

### Performance Debugging

```python
async def debug_query_performance(kb, **query_args):
    """Debug slow queries."""
    import time
    
    start = time.perf_counter()
    result = await kb.query_nodes(**query_args)
    end = time.perf_counter()
    
    print(f"Query: {query_args}")
    print(f"Results: {len(result.nodes)} nodes")
    print(f"Reported time: {result.query_time_ms:.2f}ms")
    print(f"Measured time: {(end - start) * 1000:.2f}ms")
    print(f"Storage tier: {result.storage_tier}")
    
    return result
```