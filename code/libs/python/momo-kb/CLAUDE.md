# CLAUDE.md - Momo Knowledge Base Module

This file provides Claude Code with context and guidance for working on the momo-kb module.

## Module Overview

The momo-kb module is a high-performance, async-first knowledge base abstraction layer designed for multi-agent AI systems. It provides a unified interface to vector, graph, and document storage backends with comprehensive type safety and local embedding support.

## Key Architecture Decisions

### Three-Backend Design with Unified Document Storage
- **Document Backend**: Unified pandas-based storage with pluggable persistence (Memory, CSV, HDF5, DuckDB)
- **Vector Backend**: Semantic similarity with local embeddings (InMemory)  
- **Graph Backend**: Relationship traversal and graph queries (InMemory)

### Document Backend Architecture
All document storage uses pandas DataFrames with different persistence strategies:
- **Memory**: NoPersistence - pure in-memory for development/testing
- **CSV**: CSVPersistence - human-readable files for small datasets
- **HDF5**: HDF5Persistence - compressed binary format for medium datasets  
- **DuckDB**: DuckDBPersistence - ACID transactions and SQL analytics for production

### Performance Characteristics
- **DuckDB**: Production-ready with ACID guarantees and advanced SQL analytics
- **Pandas Integration**: Full access to pandas ecosystem for data analysis
- **Local Embeddings**: < 2ms semantic search with sentence-transformers
- **Async-First**: All operations designed for high concurrency

### Protocol-Based Architecture
Uses Python protocols for clean separation between interface and implementation, enabling runtime backend swapping and easy testing.

## Development Workflow

### Optimal Development Flow (REQUIRED ORDER)

**CRITICAL: Always run type checking before testing functionality**

**During development:**
1. **Edit code** freely with focus on functionality  
2. **Format immediately**: Run `pnpm nx run momo-kb:format` after editing files to ensure formatting compliance
3. **Continue editing** - formatting is now handled transparently

**Before testing/validation (MANDATORY ORDER):**
1. **Type check FIRST**: `pnpm nx run momo-kb:typecheck` - catch type issues before functionality testing
2. **Test functionality**: `pnpm nx run momo-kb:test-fast` - validate working code only after types are clean
3. **Never skip typecheck** - type errors will cause confusing test failures

### Essential Commands
```bash
# Navigate to project root (Poetry + Nx integration)
cd /path/to/MomoAI-nx/

# Development setup
pnpm nx run momo-kb:install

# Fast development cycle (MANDATORY flow)
pnpm nx run momo-kb:format         # Format code immediately after editing - prevents linting issues
pnpm nx run momo-kb:typecheck      # ALWAYS run before testing - prevents confusing failures  
pnpm nx run momo-kb:test-fast      # Unit + e2e tests on clean, typed code

# Full validation before commits  
pnpm nx run momo-kb:test-all       # Complete test suite with coverage
pnpm nx run momo-kb:benchmark      # Performance validation
pnpm nx run momo-kb:lint           # Code style validation
```

### Code Quality Standards
- **100% async operations**: All I/O uses async/await for LangChain compatibility
- **Full type safety**: Python 3.13+ type hints with Protocol definitions
- **Performance awareness**: All implementations must be benchmarked
- **Protocol-first**: Define interfaces before implementations

## Current Implementation Status

### Recent Major Refactoring (January 2025)
Successfully migrated from multiple document backend implementations to a unified pandas-based architecture:
- **Consolidated**: Replaced `InMemoryDocumentStore` and standalone `DuckDBDocumentStore` with single `PandasDocumentBackend`
- **Pluggable Persistence**: Implemented strategy pattern with `NoPersistence`, `CSVPersistence`, `HDF5Persistence`, `DuckDBPersistence`
- **Factory Integration**: Updated backend factory to support persistence strategy configuration
- **Backward Compatibility**: Maintained API compatibility through factory system (`memory`, `csv`, `hdf5`, `duckdb`)
- **Production Default**: Set DuckDB as default persistence strategy for production use

### Completed Features
- Core async KnowledgeBase interface with context manager support
- InMemory backends for vector and graph storage
- Unified pandas-based document backend with pluggable persistence
- DuckDB persistence strategy with ACID transactions and SQL analytics
- CSV and HDF5 persistence strategies for flexible storage options
- Local embedding support with graceful fallbacks
- Rich metadata system with custom fields for agent discovery
- Comprehensive example scripts demonstrating all features

### Development Focus Areas
1. **Performance optimization**: Pandas backend refinement and persistence strategy tuning
2. **Multi-agent integration**: Agent capability storage and discovery
3. **Advanced search**: Complex query composition and ranking with SQL analytics
4. **Configuration management**: Runtime backend selection and persistence strategy configuration

## File Organization

### Source Structure
```
src/momo_kb/
├── core.py           # CoreKnowledgeBase unified implementation
├── factory.py        # Backend creation and configuration
├── embeddings.py     # Local embedding models with fallbacks
├── base.py          # Core Protocol definitions
├── stores/          # Backend implementations
│   ├── document/    # Unified pandas backend with persistence strategies
│   │   ├── PandasDocumentStore.py  # Main pandas-based implementation
│   │   ├── persistence.py          # Pluggable persistence strategies
│   │   └── main.py                 # Protocol definitions
│   ├── vector/      # Vector similarity search  
│   └── graph/       # Graph traversal and relationships
└── types/           # Type definitions and protocols
```

### Configuration Files
- `momo.yaml`: Module-specific configuration (backends, embeddings, performance)
- `pyproject.toml`: Dependencies, scripts, and build configuration
- `momo.md` files: AI-friendly context in each directory

### Examples and Testing
- `scripts/`: Comprehensive usage examples (01-05 numbered progression)
- `tests/unit/`: Fast isolated tests (< 1s each)
- `tests/e2e/`: End-to-end workflow tests (1-5s)
- `tests/integration/`: Backend interaction tests (1-10s)
- `benchmarks/`: Performance validation (10s+)

## Multi-Agent Considerations

### Agent-Friendly Design
- **Rich metadata**: Enables agent discovery through similarity search
- **Custom fields**: Support domain-specific agent capabilities
- **Async operations**: Integrates with LangChain agent workflows
- **Performance profiles**: Help agents choose appropriate backends

### Agent Integration Patterns
- Store agent capabilities as documents with searchable metadata
- Use vector search to match tasks to capable agents
- Graph relationships model agent collaboration patterns
- Custom metadata fields encode agent-specific requirements

## Common Development Tasks

### Adding New Backend
1. Define protocol interface in `types/backend.py`
2. Implement concrete class in appropriate `stores/` subdirectory
3. Add factory method in `factory.py`
4. Create comprehensive test suite
5. Add benchmark comparisons
6. Update configuration options in `momo.yaml`

### Performance Optimization
1. Always benchmark before and after changes
2. Use `pdm run benchmark` for consistent measurement
3. Document performance characteristics in code
4. Consider async/await patterns for I/O operations

### Type Safety
1. Use Protocol definitions for all interfaces
2. Provide full type hints including async return types
3. Run `pdm run typecheck` before testing functionality
4. Use Pydantic for data validation where appropriate

## Dependencies and Installation

### Core Dependencies
- `langchain-core`: Agent framework integration
- `duckdb`: High-performance analytics database
- `sentence-transformers`: Local embedding models
- `torch`: PyTorch backend for embeddings
- `pydantic`: Data validation and serialization

### Development Dependencies  
- `pytest`: Testing framework with async support
- `black`: Code formatting
- `mypy`: Type checking
- `coverage`: Test coverage analysis

### Installation Notes
- PyTorch installation may timeout due to size - this is expected
- Embeddings work with graceful fallback when PyTorch unavailable
- All backends designed to work offline without external APIs

## Integration with MomoAI

### Project Context
This module serves as the knowledge management foundation for the broader MomoAI multi-agent system. Named after Vincent's daughter Momo, it carries deep personal significance and represents the core of knowledge storage and retrieval capabilities.

### Architectural Fit
- Designed for autonomous agent consumption
- Optimized for multi-agent task matching through similarity search  
- Performance characteristics support real-time agent decision making
- Protocol-based design enables runtime adaptation to different workloads

### Future Roadmap
- Integration with other MomoAI modules (momo-core, momo-docs)
- Advanced query composition for complex agent reasoning
- Distributed backend support for scaled deployments
- Agent learning and capability evolution tracking