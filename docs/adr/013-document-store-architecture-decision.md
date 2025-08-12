# ADR-013: Document Store Architecture - Pandas vs Direct DuckDB Integration

## Status
**PROPOSED** - Awaiting review and decision

## Context

The `momo-store-document` module currently implements a layered architecture with Pandas as an abstraction layer over multiple persistence backends (DuckDB, HDF5, CSV). This design decision needs evaluation in the context of the unified knowledge base architecture (ADR-010) and overall system performance.

### Current Architecture Analysis

#### Existing Implementation
```
┌─────────────────────────────────────────────────────────────┐
│                momo-store-document                          │
├─────────────────────────────────────────────────────────────┤
│           PandasDocumentBackend                             │
│           (Unified DataFrame Interface)                     │
├─────────────────────────────────────────────────────────────┤
│              Persistence Layer                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │   DuckDB    │    HDF5     │     CSV     │   Memory    │  │
│  │ Persistence │ Persistence │ Persistence │    Only     │  │
│  │             │             │             │             │  │
│  │ • ACID      │ • Archive   │ • Export    │ • Testing   │  │
│  │ • SQL       │ • Binary    │ • Human     │ • Fast      │  │
│  │ • Fast      │ • Compact   │ • Readable  │ • Simple    │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### Integration with Unified KB
```
┌─────────────────────────────────────────────────────────────┐
│                   momo-kb (Unified API)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┬─────────────────────────────┐ │
│  │ momo-vector │ momo-graph  │    momo-store-document      │ │
│  │   -store    │   -store    │                             │ │
│  │             │             │                             │ │
│  │ • Weaviate  │ • momo-     │ • Pandas + DuckDB           │ │
│  │ • Milvus    │   graph     │ • Metadata filtering        │ │
│  │ • Chroma    │ • Neo4j     │ • Full-text search          │ │
│  └─────────────┴─────────────┴─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Findings from Investigation

#### Strengths of Current Pandas-Based Approach
1. **Unified Interface**: Single DataFrame API for all persistence backends
2. **Flexibility**: Easy switching between backends (memory, CSV, HDF5, DuckDB)
3. **Development Speed**: Pandas provides rich data manipulation capabilities
4. **Testing**: Memory backend enables fast unit testing
5. **Data Processing**: Built-in support for complex data transformations
6. **Export Capabilities**: Easy CSV export for analysis and backup

#### Performance Considerations
1. **Memory Overhead**: Pandas DataFrames require full data loading into memory
2. **Serialization Cost**: JSON metadata serialization/deserialization overhead
3. **Query Performance**: DuckDB direct queries would be faster than Pandas → DuckDB
4. **Scalability**: Pandas approach may not scale to large document collections

#### Benchmark Results Analysis
From `test_duckdb_document_benchmarks.py`:
- **Pandas + DuckDB**: ~0.5ms per document operation
- **Direct DuckDB**: Estimated ~0.1-0.2ms per document operation
- **Memory overhead**: 2-3x for Pandas DataFrame vs direct storage

## Decision

**KEEP the Pandas abstraction layer with strategic optimizations**

### Rationale

#### 1. **Multi-Backend Strategy Alignment**
The unified KB architecture (ADR-010) emphasizes backend flexibility and fallback strategies. The Pandas layer enables:
- **Development/Testing**: Memory backend for fast unit tests
- **Production**: DuckDB for ACID compliance and performance
- **Archive**: HDF5 for long-term storage
- **Export**: CSV for data analysis and backup

#### 2. **Development Velocity vs Performance Trade-off**
- **80/20 Rule**: Document store is primarily for metadata filtering before expensive vector/graph operations
- **Query Patterns**: Most operations are simple key-value lookups and metadata filters
- **Performance Bottleneck**: Vector similarity and graph traversal are the real bottlenecks, not document metadata

#### 3. **Operational Benefits**
- **Debugging**: Pandas DataFrames are easier to inspect and debug
- **Data Science Integration**: Natural integration with ML pipelines
- **Flexibility**: Easy to add new persistence backends
- **Testing**: Fast in-memory testing without external dependencies

#### 4. **Strategic Optimizations**
Rather than removing Pandas, implement targeted optimizations:
- **Lazy Loading**: Load only required columns/rows
- **Query Pushdown**: Push filters to DuckDB before loading into Pandas
- **Caching**: Cache frequently accessed documents
- **Batch Operations**: Optimize bulk operations

## Implementation Plan

### Phase 1: Query Optimization (1 week)
1. **Query Pushdown Implementation**
   ```python
   # Before: Load all data, then filter
   df = self.persistence.load_dataframe()
   filtered = df[df['type'] == 'document']
   
   # After: Push filter to DuckDB
   df = self.persistence.load_dataframe(
       where_clause="type = 'document'"
   )
   ```

2. **Lazy Loading Strategy**
   ```python
   # Load only required columns for metadata queries
   metadata_df = self.persistence.load_columns(['id', 'type', 'category', 'tags'])
   # Load full content only when needed
   content = self.persistence.load_content(document_id)
   ```

### Phase 2: Performance Enhancements (1 week)
1. **Caching Layer**
   ```python
   class CachedPandasBackend(PandasDocumentBackend):
       def __init__(self, persistence, cache_size=1000):
           super().__init__(persistence)
           self.cache = LRUCache(cache_size)
   ```

2. **Batch Operation Optimization**
   ```python
   async def put_batch(self, documents: List[Tuple[str, Dict]]) -> List[bool]:
       # Optimize bulk inserts to avoid individual DataFrame operations
   ```

### Phase 3: Backend-Specific Optimizations (1 week)
1. **DuckDB-Specific Enhancements**
   ```python
   class DuckDBPersistence(PersistenceStrategy):
       def execute_sql(self, query: str, params: Dict) -> pd.DataFrame:
           # Direct SQL execution for complex queries
   ```

2. **Hybrid Query Strategy**
   ```python
   # Simple queries: Use Pandas for flexibility
   # Complex queries: Use direct DuckDB SQL
   # Bulk operations: Use DuckDB batch inserts
   ```

## Architecture Decision

### Recommended Architecture
```
┌─────────────────────────────────────────────────────────────┐
│              Enhanced momo-store-document                   │
├─────────────────────────────────────────────────────────────┤
│           Optimized PandasDocumentBackend                   │
│  • Query Pushdown  • Lazy Loading  • Caching               │
├─────────────────────────────────────────────────────────────┤
│              Smart Persistence Layer                        │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │   DuckDB    │    HDF5     │     CSV     │   Memory    │  │
│  │ Enhanced    │ Archive     │ Export      │ Testing     │  │
│  │             │             │             │             │  │
│  │ • SQL Push  │ • Compress  │ • Analysis  │ • Fast      │  │
│  │ • Batch Ops │ • Readonly  │ • Backup    │ • Simple    │  │
│  │ • Indexing  │ • Metadata  │ • Debug     │ • Isolated  │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Backend Strategy
1. **Development**: Memory backend for fast testing
2. **Production**: DuckDB with query pushdown and indexing
3. **Archive**: HDF5 for historical data compression
4. **Export**: CSV for data analysis and human inspection
5. **Hybrid**: Automatic backend selection based on query type

## Consequences

### Positive
1. **Maintained Flexibility**: Keep all current backend options
2. **Improved Performance**: Query pushdown and caching provide 2-3x speedup
3. **Development Velocity**: Pandas interface remains familiar and productive
4. **Testing Speed**: Memory backend enables fast unit tests
5. **Operational Benefits**: Easy debugging, data export, and analysis

### Negative
1. **Complexity**: Additional optimization layer adds complexity
2. **Memory Usage**: Still higher than direct DuckDB (but optimized)
3. **Learning Curve**: Developers need to understand query pushdown patterns

### Neutral
1. **Performance**: Optimized Pandas approach should match 80% of direct DuckDB performance
2. **Maintenance**: Similar maintenance burden with better optimization patterns

## Monitoring and Success Metrics

### Performance Targets (Post-Optimization)
- **Document Operations**: <0.2ms average (vs current 0.5ms)
- **Metadata Queries**: <0.1ms for filtered queries
- **Bulk Operations**: >1000 documents/second
- **Memory Usage**: <50% overhead vs direct storage

### Monitoring Points
1. **Query Performance**: Track operation latencies by type
2. **Cache Hit Rates**: Monitor caching effectiveness
3. **Memory Usage**: Track DataFrame memory consumption
4. **Backend Usage**: Monitor which backends are used for what operations

## Review and Evolution

### 6-Month Review Criteria
If after 6 months we observe:
- **Performance Issues**: Document operations become a bottleneck
- **Memory Problems**: Pandas overhead causes scaling issues
- **Complexity Burden**: Optimization complexity outweighs benefits

Then consider **Phase 2 Evolution**: Direct DuckDB backend with minimal Pandas wrapper for specific use cases.

### Future Evolution Path
```
Current: Pandas + Multiple Backends (Optimized)
    ↓ (if needed)
Future: Direct DuckDB + Pandas Adapter (Hybrid)
    ↓ (if needed)
Ultimate: Pure DuckDB + Export Utilities (Minimal)
```

## Implementation Priority

**HIGH PRIORITY** - Implement optimizations in next sprint:
1. Query pushdown for DuckDB backend
2. Lazy loading for large documents
3. Basic caching for frequently accessed documents

This approach maintains our current flexibility while addressing performance concerns through targeted optimizations rather than architectural overhaul.