# ADR-006: Extract momo-graph module from momo-kb

**Date:** 2025-08-11  
**Status:** ✅ **ACCEPTED**  
**Decision Makers:** Vincent  
**Consulted:** ADR-009 extraction design, existing Nx module patterns

## Table of Contents

- [Problem Statement](#problem-statement)
- [Research Summary](#research-summary)
- [Decision](#decision)
- [Implementation Strategy](#implementation-strategy)
- [Success Metrics](#success-metrics)
- [Risks and Mitigations](#risks-and-mitigations)
- [Trade-offs Accepted](#trade-offs-accepted)
- [Implementation Results](#implementation-results)
- [Lessons Learned](#lessons-learned)
- [Next Steps](#next-steps)
- [Related Documentation](#related-documentation)

## Problem Statement

The `momo_graph/` directory within `momo-kb` contains a complete, high-performance graph implementation that should be extracted into a standalone module for:

- **Modularity**: Enable independent development and testing of graph functionality
- **Reusability**: Allow other projects to use the graph backend independently  
- **Code Quality**: Fix existing import/naming conflicts (e.g., `GraphGraphDiff` issues)
- **Architecture**: Align with established Nx monorepo patterns and ADR-009 design

The current monolithic structure limits reusability and creates maintenance overhead.

## Research Summary

### Key Findings

1. **Complete Implementation**: `momo_graph/` contains fully functional GraphBackend with 5 core files
2. **Clean Integration**: Only one import point in `momo_kb/graph_backend_adapter.py`
3. **Import Issues**: Current core.py has naming conflicts requiring cleanup
4. **Proven Pattern**: ADR-009 already documents this exact extraction approach
5. **Performance Critical**: Must maintain 11x Neo4j performance advantage

### Current State Analysis

**Files to Extract:**
- `core.py` (333 lines) - GraphBackend implementation
- `models.py` (176 lines) - GraphNode, GraphEdge, GraphDiff models
- `storage.py` - 3-tier storage system
- `indexing.py` - Graph indexing capabilities  
- `__init__.py` - Clean module exports

**Integration Point:**
```python
# momo_kb/graph_backend_adapter.py
from momo_graph import GraphBackend, GraphNode, GraphEdge, GraphQueryResult
```

## Decision

**Extract `momo_graph/` into a standalone `momo-graph` module with complete cleanup and proper Nx integration.**

### Architecture Chosen

**New Module Structure:**
```
code/libs/python/momo-graph/
├── momo_graph/           # Source code
│   ├── __init__.py      # Clean exports
│   ├── core.py          # GraphBackend (fixed imports)
│   ├── models.py        # Graph data models
│   ├── storage.py       # 3-tier storage
│   └── indexing.py      # Graph indexing
├── tests/               # Complete test suite
│   ├── unit/           # Unit tests
│   └── e2e/            # End-to-end tests
├── benchmarks/         # Performance validation
├── scripts/            # Usage examples
├── pyproject.toml      # uv configuration
├── project.json        # Nx configuration
├── CLAUDE.md           # Module documentation
└── README.md           # User guide
```

**Updated Dependencies:**
- `momo-kb` will depend on `momo-graph` module
- Import path: `from momo_graph import GraphBackend, GraphNode, GraphEdge`
- Nx project dependency: `"momo-kb"` → `["momo-graph"]`

## Implementation Strategy

### Phase 1: Module Creation ✅
- Create new `momo-graph` module following Nx standards
- Set up pyproject.toml, project.json, and build targets
- Establish clean folder structure with proper separation

### Phase 2: Code Extraction & Cleanup
- Extract all `momo_graph/` files to new module
- Fix import issues in core.py (GraphGraphDiff → GraphDiff)
- Clean up any other naming conflicts discovered
- Update __init__.py exports for clean API

### Phase 3: Testing Migration
- Extract graph-specific tests to new module
- Update test imports and dependencies
- Migrate relevant benchmarks for performance validation
- Ensure 100% test coverage maintained

### Phase 4: Integration Update
- Update `momo-kb` pyproject.toml to depend on `momo-graph`
- Update Nx project.json dependencies
- Modify `graph_backend_adapter.py` import paths
- Validate all existing functionality works

### Phase 5: Validation & Cleanup
- Run complete test suites for both modules
- Execute performance benchmarks to ensure no regression
- Remove extracted code from `momo-kb`
- Update documentation and examples

## Success Metrics

### Functionality Metrics
- ✅ All graph operations work through new module
- ✅ GraphBackend maintains all existing APIs
- ✅ Rollback, 3-tier storage, and indexing preserved
- ✅ All existing tests pass in both modules

### Performance Metrics  
- ✅ Graph operations maintain 11x Neo4j performance advantage
- ✅ Memory efficiency characteristics preserved (1.1KB vs 3KB per node)
- ✅ Rollback operations maintain 155K ops/sec throughput
- ✅ Zero performance regression in momo-kb integration

### Code Quality Metrics
- ✅ Import/naming conflicts resolved (no more GraphGraphDiff)
- ✅ Clean module boundaries and exports
- ✅ 100% test coverage maintained across both modules
- ✅ Nx build targets work correctly (format, typecheck, test-fast)

## Risks and Mitigations

### Risk 1: Breaking Changes During Extraction
**Probability:** Medium **Impact:** High  
**Mitigation:** Careful import path management and comprehensive testing at each step

### Risk 2: Performance Regression
**Probability:** Low **Impact:** High  
**Mitigation:** Run benchmarks before and after extraction, maintain identical algorithms

### Risk 3: Import/Dependency Issues
**Probability:** Medium **Impact:** Medium  
**Mitigation:** Fix known issues first, systematic testing of import paths

### Risk 4: Test Coverage Gaps
**Probability:** Low **Impact:** Medium  
**Mitigation:** Extract tests systematically, validate coverage metrics

## Trade-offs Accepted

### Advantages Gained
- ✅ **Modularity**: Independent development and testing of graph functionality
- ✅ **Reusability**: Graph backend can be used by other projects
- ✅ **Code Quality**: Fixes import conflicts and naming issues
- ✅ **Architecture**: Aligns with Nx monorepo standards
- ✅ **Maintenance**: Cleaner boundaries and focused responsibilities

### Complexity Added
- ⚠️ **Dependency Management**: momo-kb now depends on momo-graph
- ⚠️ **Coordination**: Changes affecting both modules need coordination
- ⚠️ **Build Complexity**: Additional module in build pipeline

**Mitigation**: Nx handles cross-module dependencies and build orchestration automatically

## Implementation Results

[To be filled during implementation]

## Lessons Learned

[To be filled after implementation]

## Next Steps

### Immediate Actions
1. Create momo-graph module structure with Nx configuration
2. Extract and clean up momo_graph/ code with import fixes
3. Migrate tests and benchmarks to new module
4. Update momo-kb dependencies and imports
5. Validate functionality and performance

### Future Enhancements
- Consider extracting other backends (vector, document) using same pattern
- Explore graph module optimization opportunities
- Investigate graph backend extensions for multi-agent scenarios

## Related Documentation

- **[Research Analysis](research.md)** - Detailed research findings and option comparison
- **[Implementation Plan](implementation-plan.md)** - Step-by-step execution plan
- **[Implementation Log](implementation-log.md)** - Daily progress tracking  
- **[Results & Lessons](results.md)** - Final outcomes and insights
- **[ADR-009](../../momo-kb/research/adr-009-graph-backend-extraction.md)** - Original extraction design
