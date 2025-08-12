# CLAUDE.md - Momo Graph Module

This file provides Claude Code with context and guidance for working on the momo-graph module.

## Module Overview

The momo-graph module provides a high-performance, immutable graph database backend with 3-tier storage, diff-based rollback, and advanced indexing capabilities. Extracted from momo-kb for modularity and reusability.

## Key Architecture Decisions

### Immutable Graph Operations
- **INSERT/DELETE Only**: No update operations - use delete + insert pattern
- **Diff-Based Rollback**: Complete rollback system with 155K ops/sec throughput
- **3-Tier Storage**: Runtime → Store → Cold with usage-based pruning
- **Performance Critical**: 11x faster than Neo4j for node operations

### Protocol-Based Design
Clean separation between interface and implementation with GraphBackend as the main entry point.

### High-Performance Indexing
- B-tree indexing for property queries (450x faster than Neo4j)
- Multi-tier query optimization with access tracking
- Semantic embedding support for hybrid queries

## Development Workflow

### Optimal Development Flow (REQUIRED ORDER)

**CRITICAL: Always run type checking before testing functionality**

**During development:**
1. **Edit code** freely with focus on functionality  
2. **Format immediately**: Run `pnpm nx run momo-graph:format` after editing files
3. **Continue editing** - formatting is now handled transparently

**Before testing/validation (MANDATORY ORDER):**
1. **Type check FIRST**: `pnpm nx run momo-graph:typecheck` - catch type issues before functionality testing
2. **Test functionality**: `pnpm nx run momo-graph:test-fast` - validate working code only after types are clean
3. **Never skip typecheck** - type errors will cause confusing test failures

### Essential Commands
```bash
# Navigate to project root (uv + Nx integration)
cd /path/to/MomoAI-nx/

# Development setup
pnpm nx run momo-graph:install

# Fast development cycle (MANDATORY flow)
pnpm nx run momo-graph:format         # Format code immediately after editing
pnpm nx run momo-graph:typecheck      # ALWAYS run before testing - prevents confusing failures  
pnpm nx run momo-graph:test-fast      # Unit + e2e tests on clean, typed code

# Performance validation
pnpm nx run momo-graph:benchmark      # Performance benchmarks validation
pnpm nx run momo-graph:test-all       # Complete test suite with coverage
```

### Code Quality Standards
- **100% async operations**: All I/O uses async/await
- **Full type safety**: Python 3.13+ type hints with Protocol definitions
- **Immutable operations**: All graph modifications create new objects
- **Performance first**: All implementations must maintain benchmark targets
- **Memory efficiency**: ~1.1KB per node target

## Current Implementation Status

### Completed Features
- GraphBackend with complete CRUD operations
- Immutable GraphNode and GraphEdge models with usage tracking
- Diff-based rollback system with timestamp support
- 3-tier storage system (Runtime/Store/Cold)
- High-performance indexing with B-tree structures
- Semantic embedding support for nodes
- Export/import functionality with JSON format

### Performance Targets (MUST MAINTAIN)
- **Node Operations**: <0.009ms (11x faster than Neo4j)
- **Property Queries**: <0.44ms (450x faster than Neo4j)
- **Bulk Loading**: >46,000 ops/sec
- **Memory Usage**: ~1.1KB per node
- **Rollback Operations**: >155K ops/sec

## File Organization

### Source Structure
```
momo_graph/
├── __init__.py       # Clean exports for GraphBackend
├── core.py           # GraphBackend implementation
├── models.py         # GraphNode, GraphEdge, GraphDiff models
├── storage.py        # 3-tier storage system  
├── indexing.py       # High-performance indexing
└── momo.md          # AI-friendly context
```

### Configuration Files
- `pyproject.toml`: Minimal dependencies (pydantic, psutil)
- `project.json`: Nx build targets and configuration
- `README.md`: User documentation
- `CLAUDE.md`: AI context (this file)

### Testing Structure
- `tests/unit/`: Fast isolated tests (< 1s each)
- `tests/e2e/`: End-to-end workflow tests (1-5s)
- `benchmarks/`: Performance validation tests

## Multi-Agent Considerations

### Agent-Optimized Features
- **Immutable Operations**: Safe for concurrent agent access
- **Rollback System**: Agents can safely experiment and rollback
- **Usage Tracking**: Automatic pruning based on agent access patterns
- **Semantic Support**: Embedding integration for agent-friendly queries

### Performance Characteristics
- **High Concurrency**: Async-first design for multi-agent scenarios
- **Memory Efficient**: Minimal memory footprint for large graphs
- **Fast Queries**: Optimized for agent query patterns
- **Incremental Updates**: Diff-based approach supports incremental learning

## Integration Points

### Primary Consumer
- **momo-kb**: Uses GraphBackend through GraphBackendAdapter
- **Import Pattern**: `from momo_graph import GraphBackend, GraphNode, GraphEdge`
- **Adapter Interface**: Translates between unified Document/Relationship and GraphNode/GraphEdge

### Independent Usage
The module can be used standalone for graph database requirements outside of momo-kb.

## Common Development Tasks

### Performance Optimization
1. **Profile Critical Paths**: Focus on node/edge operations and queries
2. **Minimize Object Creation**: Reuse objects where possible
3. **Efficient Indexing**: Optimize B-tree operations
4. **Memory Management**: Monitor memory usage patterns

### Adding New Query Types
1. Add query method to GraphBackend
2. Implement indexed version in storage layer
3. Add corresponding result models if needed
4. Create comprehensive benchmarks
5. Update documentation

### Storage Tier Optimization
1. Monitor tier distribution patterns
2. Optimize pruning algorithms
3. Implement usage-based promotion
4. Benchmark tier performance characteristics

## Dependencies and Installation

### Core Dependencies
- `pydantic>=2.0.0`: Data validation and serialization
- `psutil>=7.0.0`: Memory usage monitoring

### Development Dependencies  
- Standard Python tooling: pytest, ruff, pyright
- Performance testing: pytest-benchmark

### Installation Notes
- Uses uv for dependency management with Nx integration via @nxlv/python plugin
- Minimal dependency footprint for maximum reusability
- Follows same development workflow as other Momo modules

## Integration with MomoAI

### Project Context
This module provides graph database capabilities that were extracted from momo-kb for modularity. It maintains all performance characteristics while enabling independent development and reuse.

### Architectural Fit
- **Backend Module**: Pluggable graph storage for knowledge systems
- **Performance Critical**: Maintains industry-leading performance metrics
- **Multi-Agent Ready**: Designed for concurrent agent access patterns
- **Immutable Design**: Safe for multi-agent experimentation with rollback