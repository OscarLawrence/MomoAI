# Unified KnowledgeBase API Design Questions

## 🎯 **Proposed Architecture**

```python
class KnowledgeBaseCore:
    """Low-level backend management and core functionality."""
    def __init__(self, backends: List[str] = ["graph"]):
        self.backends = {}  # backend_name -> backend_instance
        self._load_backends(backends)
    
    def _load_backends(self, backend_names): ...
    def _route_operation(self, operation, *args, **kwargs): ...

class KnowledgeBase(KnowledgeBaseCore):
    """High-level unified API for multi-backend knowledge operations."""
    def insert(self, *docs): ...
    def delete(self, *ids): ...
    def query(self, query, filters=None, top_k=10, search_depth='medium', **kwargs): ...
    def roll(self, steps): ...
    def prune(self, mode="auto", threshold=None): ...
    def stats(self): ...
```

## ❓ **Design Questions**

### **1. Document Input Format**
```python
await kb.insert(*docs)
```

**Question**: What format should `docs` accept?

**Options**:
```python
# Option A: Raw dictionaries
await kb.insert(
    {"label": "Person", "properties": {"name": "Alice"}},
    {"label": "Document", "properties": {"title": "AI Paper"}}
)

# Option B: Unified Document class
await kb.insert(
    Document(type="person", content={"name": "Alice"}),
    Document(type="document", content={"title": "AI Paper"})
)

# Option C: Backend-agnostic Node class
await kb.insert(
    Node(label="Person", properties={"name": "Alice"}),
    Node(label="Document", properties={"title": "AI Paper"})
)

# Option D: Mixed formats (auto-detect)
await kb.insert(
    {"label": "Person", "name": "Alice"},  # Dict
    Node(label="Document", properties={"title": "AI Paper"}),  # Node object
    "This is raw text content"  # String
)
```

**Recommendation**: Option D (mixed formats) for maximum flexibility?

### **2. Backend Routing Strategy**
```python
await kb.insert(doc)  # Which backend(s) should receive this?
```

**Question**: How should we route operations to backends?

**Options**:
```python
# Option A: Explicit backend specification
await kb.insert(doc, backends=["graph", "vector"])

# Option B: Content-based auto-routing
await kb.insert(doc)  # Auto-routes based on content type

# Option C: Configuration-based routing
kb.configure_routing({
    "Person": ["graph"],
    "Document": ["graph", "vector", "document"],
    "default": ["graph"]
})

# Option D: All backends by default
await kb.insert(doc)  # Goes to all enabled backends
```

**Recommendation**: Option C (configuration-based) with Option B fallback?

### **3. Query Interface Design**
```python
await kb.query(query, filters=None, top_k=10, search_depth='medium', **kwargs)
```

**Questions**:

**3a. Query Parameter Types**:
```python
# String queries (semantic/fulltext)
await kb.query("machine learning research")

# Structured queries (graph traversal)
await kb.query({"relationship": "knows", "direction": "outgoing"})

# Mixed queries
await kb.query(
    semantic="AI research",
    structural={"label": "Document"},
    fulltext="neural networks"
)
```

**3b. Search Depth Meaning**:
- `shallow`: Single backend, fastest
- `medium`: Multiple backends, balanced
- `deep`: All backends + cross-backend joins, comprehensive

**3c. Response Format**:
```python
# Option A: Unified result format
QueryResult(
    items=[...],  # Backend-agnostic items
    metadata={"backend_sources": ["graph", "vector"], "timing": {...}}
)

# Option B: Backend-specific results
{
    "graph": GraphQueryResult(...),
    "vector": SemanticQueryResult(...),
    "combined": UnifiedResult(...)
}
```

### **4. Rollback Scope**
```python
await kb.roll(steps=3)
```

**Question**: Should rollback affect all backends or be configurable?

**Options**:
```python
# Option A: All backends
await kb.roll(steps=3)  # Rolls back all backends

# Option B: Specific backends
await kb.roll(steps=3, backends=["graph"])

# Option C: Coordinated rollback
await kb.roll(steps=3)  # Ensures consistency across backends
```

### **5. Stats Interface**
```python
stats = await kb.stats()
```

**Question**: What level of detail should stats provide?

**Options**:
```python
# Option A: High-level summary
{
    "total_items": 10000,
    "backends": ["graph", "vector"],
    "performance": {"avg_query_time": "2.5ms"}
}

# Option B: Detailed per-backend
{
    "graph": {"nodes": 5000, "edges": 8000, "query_time": "1.2ms"},
    "vector": {"embeddings": 5000, "index_size": "50MB", "query_time": "3.8ms"},
    "overall": {"total_operations": 15000, "memory_usage": "120MB"}
}

# Option C: Configurable detail level
await kb.stats(detail="summary")  # or "detailed", "performance"
```

## 🎯 **My Recommendations**

### **Proposed Implementation**:
```python
class KnowledgeBase(KnowledgeBaseCore):
    async def insert(self, *docs, backends=None):
        """Insert documents with auto-routing or explicit backend selection."""
        
    async def delete(self, *ids, backends=None):
        """Delete by IDs across specified or all backends."""
        
    async def query(
        self, 
        query: Union[str, dict], 
        filters=None, 
        top_k=10, 
        search_depth: Literal['shallow', 'medium', 'deep'] = 'medium',
        **query_args
    ):
        """Unified query interface with depth-based backend selection."""
        
    async def roll(self, steps: int, backends=None):
        """Coordinated rollback across backends."""
        
    async def prune(self, mode="auto", threshold=None, backends=None):
        """Intelligent pruning across backends."""
        
    async def stats(self, detail="summary"):
        """Comprehensive statistics with configurable detail."""
```

## ❓ **Questions for You**

1. **Document format preference**: Mixed formats (dicts, objects, strings) with auto-detection?

2. **Backend routing**: Configuration-based routing with content-type fallback?

3. **Query interface**: Support both string and structured queries in single method?

4. **Search depth**: Should `deep` include cross-backend joins and fusion?

5. **Rollback coordination**: Should we ensure consistency across backends?

6. **Stats detail**: Prefer detailed per-backend stats by default?

Please let me know your preferences and I'll implement accordingly!