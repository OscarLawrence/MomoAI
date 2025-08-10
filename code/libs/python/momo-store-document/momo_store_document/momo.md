# Document Storage Backends

Unified pandas-based document storage with pluggable persistence strategies. All backends use pandas DataFrames as the core in-memory data structure with different persistence methods.

## Architecture

**Single Implementation**: `PandasDocumentStore.py` - Unified pandas-based backend
**Persistence Strategies**: Pluggable storage methods in `persistence.py`
- `NoPersistence`: Memory-only for development/testing
- `CSVPersistence`: Human-readable CSV files
- `HDF5Persistence`: Compressed binary format with excellent performance
- `DuckDBPersistence`: ACID transactions with SQL analytics (production default)

## Capabilities

- Full-text search across document content with pandas string operations
- Complex metadata filtering with nested fields and custom data types
- Document CRUD operations with automatic timestamp management
- Efficient counting and listing operations with pandas indexing
- Advanced analytics with direct DataFrame access and pandas queries
- SQL analytics capabilities via DuckDB persistence strategy
- Statistical analysis and aggregations through pandas ecosystem

## Performance Characteristics

### Unified Pandas Backend
- Consistent ~1,600 docs/sec insertion across all persistence strategies
- Sub-30ms scan times with pandas vectorized operations
- Memory-efficient columnar storage via pandas DataFrames
- Direct access to full pandas ecosystem for analytics

### Persistence Strategy Performance
- **Memory**: Fastest access, no I/O overhead
- **CSV**: Human-readable, good for small datasets and debugging
- **HDF5**: Compressed storage, excellent for medium-large datasets
- **DuckDB**: ACID guarantees, SQL analytics, production-ready scaling