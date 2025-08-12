# ADR-006 Implementation Plan: Extract momo-graph module from momo-kb

## Implementation Overview

Extract the complete `momo_graph/` functionality from `momo-kb` into a standalone `momo-graph` module following established Nx patterns. The implementation follows a 5-phase approach with systematic testing and validation at each step to ensure zero breaking changes and maintained performance.

## Phase Breakdown

### Phase 1: Module Foundation Setup
**Duration:** 30 minutes  
**Dependencies:** ADR approval, Nx workspace setup

**Tasks:**
- [ ] Create `code/libs/python/momo-graph/` directory structure
- [ ] Set up pyproject.toml with uv configuration and dependencies
- [ ] Create project.json with Nx build targets (install, format, typecheck, test-fast)
- [ ] Establish folder structure: `momo_graph/`, `tests/`, `benchmarks/`, `scripts/`
- [ ] Create initial CLAUDE.md and README.md files

**Success Criteria:**
- ✅ Directory structure matches established Nx patterns
- ✅ `nx run momo-graph:install` works correctly
- ✅ Basic Nx targets execute without errors

**Validation:**
```bash
nx run momo-graph:install
nx show project momo-graph
```

### Phase 2: Code Extraction & Import Fixes
**Duration:** 45 minutes  
**Dependencies:** Phase 1 complete

**Tasks:**
- [ ] Copy all files from `momo_graph/` to new module
- [ ] Fix import issues in core.py (GraphGraphDiff → GraphDiff, etc.)
- [ ] Clean up any duplicate imports or naming conflicts
- [ ] Update `__init__.py` exports for clean API surface
- [ ] Validate all internal imports work correctly

**Success Criteria:**
- ✅ All 5 core files copied with clean imports
- ✅ No import errors when loading module
- ✅ GraphBackend can be imported cleanly
- ✅ All model classes accessible via exports

**Validation:**
```bash
python -c "from momo_graph import GraphBackend, GraphNode, GraphEdge"
nx run momo-graph:format
```

### Phase 3: Test & Benchmark Migration
**Duration:** 45 minutes  
**Dependencies:** Phase 2 complete

**Tasks:**
- [ ] Identify graph-specific tests in momo-kb test suite
- [ ] Extract relevant test files to new module test structure
- [ ] Update test imports to use new module paths
- [ ] Migrate performance benchmarks for graph operations
- [ ] Create test runner scripts (01-05) for usage examples

**Success Criteria:**
- ✅ Graph-specific tests run independently in new module
- ✅ Test coverage maintained (aim for 100%)
- ✅ Performance benchmarks execute successfully
- ✅ All tests pass in isolated environment

**Validation:**
```bash
nx run momo-graph:test-fast
nx run momo-graph:benchmark
```

### Phase 4: Dependency Integration
**Duration:** 30 minutes  
**Dependencies:** Phase 3 complete

**Tasks:**
- [ ] Add momo-graph dependency to momo-kb pyproject.toml
- [ ] Update momo-kb project.json to depend on momo-graph
- [ ] Modify imports in `graph_backend_adapter.py`
- [ ] Validate momo-kb can import from new module
- [ ] Test full integration through adapter layer

**Success Criteria:**
- ✅ momo-kb successfully imports GraphBackend from momo-graph
- ✅ No circular dependencies created
- ✅ Nx dependency graph correctly represents relationship
- ✅ All momo-kb tests still pass

**Validation:**
```bash
nx graph  # Verify dependency structure
nx run momo-kb:test-fast
```

### Phase 5: Cleanup & Validation
**Duration:** 30 minutes  
**Dependencies:** Phase 4 complete

**Tasks:**
- [ ] Remove extracted `momo_graph/` directory from momo-kb
- [ ] Clean up any leftover imports or references
- [ ] Run complete test suites for both modules
- [ ] Execute performance benchmarks to verify no regression
- [ ] Update documentation and examples

**Success Criteria:**
- ✅ No duplicate code between modules
- ✅ All tests pass in both modules
- ✅ Performance metrics maintained
- ✅ Clean module boundaries established

**Validation:**
```bash
nx run-many -t test-fast -p momo-graph momo-kb
nx run momo-graph:benchmark
```

## Risk Management

### Risk 1: Import Path Conflicts
**Probability:** Medium  
**Impact:** Medium  
**Mitigation:** 
- Fix known import issues (GraphGraphDiff) first
- Test imports systematically at each phase
- Use absolute imports throughout

### Risk 2: Missing Dependencies
**Probability:** Low  
**Impact:** Medium  
**Mitigation:**
- Copy pyproject.toml dependencies from momo-kb
- Test module isolation before integration
- Validate all imports work independently

### Risk 3: Test Coverage Gaps
**Probability:** Low  
**Impact:** Medium  
**Mitigation:**
- Systematically identify graph-specific tests
- Maintain coverage metrics during migration
- Create additional tests if gaps identified

### Risk 4: Performance Regression
**Probability:** Very Low  
**Impact:** High  
**Mitigation:**
- Run benchmarks before and after extraction
- Use identical algorithms and data structures
- Measure specific operations (node ops, queries, rollback)

### Risk 5: Breaking momo-kb Integration
**Probability:** Medium  
**Impact:** High  
**Mitigation:**
- Keep adapter interface identical
- Test momo-kb functionality continuously
- Have rollback plan ready

## Success Metrics

### Functional Success
- ✅ GraphBackend operations work identically
- ✅ All rollback functionality preserved
- ✅ 3-tier storage system functional
- ✅ Indexing and query performance maintained

### Performance Success  
- ✅ Node operations: <0.009ms (maintain 11x Neo4j advantage)
- ✅ Property queries: <0.44ms (maintain 450x Neo4j advantage)
- ✅ Bulk operations: >46,000 ops/sec
- ✅ Memory efficiency: ~1.1KB per node
- ✅ Rollback operations: >155K ops/sec

### Integration Success
- ✅ momo-kb adapter layer works unchanged
- ✅ All momo-kb tests pass with new dependency
- ✅ Nx build system handles dependencies correctly
- ✅ No circular dependencies created

### Code Quality Success
- ✅ Import conflicts resolved (no more GraphGraphDiff)
- ✅ Clean module exports and API surface
- ✅ 100% test coverage maintained
- ✅ All Nx targets work (format, typecheck, test-fast)

## Testing Strategy

### Unit Testing
- Extract graph-specific unit tests to new module
- Test all GraphBackend operations independently
- Validate model classes and their methods
- Test import/export functionality

### Integration Testing
- Test momo-kb → momo-graph integration
- Validate adapter layer functionality
- Test cross-module dependencies through Nx

### Performance Testing
- Run existing benchmarks on extracted module
- Compare performance before/after extraction
- Validate no regression in critical operations

### End-to-End Testing
- Test complete workflows through both modules
- Validate semantic query functionality
- Test rollback operations end-to-end

## Rollback Plan

If critical issues arise during implementation:

### Immediate Rollback (during phases 1-3)
1. Delete `momo-graph` directory
2. Revert to ADR branch state
3. No impact to momo-kb functionality

### Integration Rollback (during phases 4-5)
1. Revert momo-kb pyproject.toml changes
2. Revert momo-kb project.json dependencies  
3. Restore original import paths in adapter
4. Keep extracted module for future retry

### Emergency Rollback
1. Use git to revert all changes to known-good state
2. Restore original momo_graph/ directory in momo-kb
3. Document issues encountered for future resolution

## Pre-Implementation Checklist

- [ ] Backup current momo-kb performance benchmark results
- [ ] Verify all momo-kb tests pass in current state  
- [ ] Confirm no other modules depend on momo_graph directly
- [ ] Review ADR-009 extraction patterns for consistency
- [ ] Ensure development environment has all required tools (uv, nx, python3)

## Post-Implementation Verification

- [ ] Compare benchmark results before/after extraction
- [ ] Verify nx graph shows correct dependency structure
- [ ] Test momo-graph module can be used independently
- [ ] Confirm momo-kb functionality unchanged
- [ ] Validate all documentation is updated
