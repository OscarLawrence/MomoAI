# Momo KnowledgeBase - Example Scripts

Focused examples showcasing the power and capabilities of the momo-kb module. Each script demonstrates specific features and use cases in a clean, educational format.

## Example Scripts

### 01_basic_usage.py - Getting Started
**Purpose**: Simple introduction to momo-kb API

**Demonstrates**:
- Creating a knowledge base
- Adding documents with metadata
- Basic search operations
- Document retrieval
- Counting and listing operations

**Best for**: First-time users learning the API basics

```bash
python scripts/01_basic_usage.py
```

### 02_backend_comparison.py - Performance Analysis
**Purpose**: Compare different storage backends

**Demonstrates**:
- InMemory vs DuckDB backend performance
- Backend configuration and selection
- Benchmarking insert/search/retrieval speeds
- When to choose which backend

**Best for**: Understanding performance characteristics and backend selection

```bash
python scripts/02_backend_comparison.py
```

### 03_search_strategies.py - Advanced Search
**Purpose**: Explore different search approaches

**Demonstrates**:
- Basic text search
- Metadata filtering (category, tags, author, language)
- Custom field searches (difficulty, type)
- Search options (limits, thresholds)
- Combined content + metadata searches

**Best for**: Learning how to build sophisticated search queries

```bash
python scripts/03_search_strategies.py
```

### 04_document_management.py - CRUD Operations
**Purpose**: Complete document lifecycle management

**Demonstrates**:
- Creating documents with rich metadata
- Reading and retrieving documents
- Updating content and metadata
- Deleting documents
- Batch operations
- Metadata analysis and statistics

**Best for**: Understanding document management patterns

```bash
python scripts/04_document_management.py
```

### 05_real_world_example.py - Documentation KB
**Purpose**: Practical application building a documentation system

**Demonstrates**:
- Multi-source content organization
- Hierarchical categorization
- Q&A system implementation
- Context-aware searches
- Source attribution and confidence scoring
- Knowledge base statistics and browsing

**Best for**: Seeing how to build real applications with momo-kb

```bash
python scripts/05_real_world_example.py
```

## Key Architectural Patterns

### Async-First Design
All examples use proper async/await patterns:
```python
async with KnowledgeBase() as kb:
    results = await kb.search("query")
```

### Rich Metadata Usage
Documents include comprehensive metadata for agent discovery:
```python
metadata=DocumentMetadata(
    category="programming",
    tags=["python", "async"],
    custom={"difficulty": "intermediate"}
)
```

### Context Management
Proper resource management with context managers:
```python
async with KnowledgeBase() as kb:
    # Operations automatically cleaned up
```

### Performance Awareness
Examples include timing and benchmarking:
```python
start_time = time.time()
results = await kb.search(query)
search_time = time.time() - start_time
```

## Running Examples

### Prerequisites
- Python 3.13+
- PDM dependency management
- momo-kb module installed

### Execute Examples
```bash
# Run all examples in sequence
pdm run script 01_basic_usage
pdm run script 02_backend_comparison  
pdm run script 03_search_strategies
pdm run script 04_document_management
pdm run script 05_real_world_example

# Or run directly
python scripts/01_basic_usage.py
```

## Multi-Agent Integration

These examples demonstrate patterns for agent consumption:

- **Rich metadata** enables agents to find relevant documents via similarity search
- **Hierarchical categorization** allows agents to scope searches to relevant domains  
- **Custom fields** support domain-specific agent capabilities
- **Performance characteristics** help agents choose appropriate backends
- **Context managers** ensure proper resource cleanup in agent workflows

## Development Patterns

### Error Handling
Examples include proper error handling and graceful fallbacks

### Resource Management  
Context managers ensure cleanup of backend resources

### Modularity
Each example is self-contained and focused on specific capabilities

### Performance
Benchmarking and timing demonstrate performance awareness

### Real-World Applicability
Examples show practical applications, not just toy demonstrations