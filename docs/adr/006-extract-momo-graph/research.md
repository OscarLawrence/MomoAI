# ADR-006 Research: Extract momo-graph module from momo-kb

**Date:** 2025-08-11

## Research Methodology

Analyzed the current `momo-kb` codebase structure, dependencies, and existing documentation (ADR-009) to understand the scope and approach for extracting the `momo_graph/` module into a standalone `momo-graph` module.

## Problem Analysis

### Current State

The `momo_graph/` directory within `momo-kb` contains a complete, high-performance graph implementation:

**Files to Extract:**
- `momo_graph/__init__.py` - Clean module exports
- `momo_graph/core.py` - GraphBackend implementation (333 lines)  
- `momo_graph/models.py` - Graph data models (GraphNode, GraphEdge, GraphDiff, etc.)
- `momo_graph/storage.py` - 3-tier graph storage system
- `momo_graph/indexing.py` - Graph indexing capabilities

**Current Integration:**
- Used by `momo_kb/graph_backend_adapter.py` via: `from momo_graph import GraphBackend, GraphNode, GraphEdge, GraphQueryResult`
- No other internal dependencies found in momo-kb codebase

### Pain Points

1. **Monolithic Structure**: Graph functionality embedded within knowledge base module
2. **Import Issues**: Current imports in core.py have naming conflicts (e.g., `GraphGraphDiff` instead of `GraphDiff`)
3. **Testing Complexity**: Graph-specific tests mixed with KB tests
4. **Reusability**: Graph backend cannot be used independently
5. **Development Overhead**: Changes to graph functionality require full KB testing

### Requirements

**Functional Requirements:**
- Extract complete graph functionality to standalone module
- Maintain all performance characteristics (11x faster than Neo4j)
- Preserve all existing APIs and behavior
- Support rollback, 3-tier storage, and indexing
- Fix import/naming issues during extraction

**Non-Functional Requirements:**
- Zero breaking changes to existing momo-kb functionality
- Maintain test coverage and performance benchmarks
- Follow established Nx monorepo structure
- Use standardized Nx build targets (format, typecheck, test-fast)

## Solution Research

### Option 1: Complete Module Extraction with Cleanup

**Description:** Extract `momo_graph/` to new `momo-graph` module, fix import issues, update momo-kb dependencies

**Pros:**
- Clean separation of concerns
- Independent development and testing
- Reusable graph backend for other projects
- Fixes existing import/naming issues
- Follows existing ADR-009 design pattern

**Cons:**
- Requires coordinated changes across modules
- Need to update import paths in momo-kb
- Testing both modules during transition

**Implementation Effort:** Medium

### Option 2: Gradual Migration with Dual Maintenance

**Description:** Create new module but maintain code in both locations during transition

**Pros:**
- Zero immediate breaking changes
- Gradual migration path
- Lower risk during transition

**Cons:**
- Code duplication and maintenance overhead
- More complex dependency management
- Delayed cleanup of issues

**Implementation Effort:** High

### Option 3: In-Place Refactoring Only

**Description:** Fix import issues within momo-kb without extraction

**Pros:**
- Minimal immediate changes
- Lower implementation effort

**Cons:**
- Doesn't address modularity concerns
- Maintains monolithic structure
- Doesn't enable reusability

**Implementation Effort:** Low

## Comparative Analysis

| Criteria | Option 1 (Complete) | Option 2 (Gradual) | Option 3 (In-place) |
|----------|-------------------|------------------|-------------------|
| Modularity | ✅ Excellent | ⚠️ Delayed | ❌ No improvement |
| Risk | ⚠️ Medium | ✅ Low | ✅ Very Low |
| Reusability | ✅ Full | ⚠️ Delayed | ❌ None |
| Maintenance | ✅ Clean | ❌ Complex | ⚠️ Status quo |
| Performance | ✅ Preserved | ✅ Preserved | ✅ Preserved |
| Development Time | ⚠️ Medium | ❌ High | ✅ Low |

## Recommendation

**Choose Option 1: Complete Module Extraction with Cleanup**

**Rationale:**
1. **Aligns with ADR-009**: The research document already outlines this exact extraction approach
2. **Clean Architecture**: Achieves proper separation of concerns immediately  
3. **Fixes Issues**: Resolves import conflicts and naming issues during extraction
4. **Future-Proof**: Enables independent graph module development
5. **Standardized**: Follows established Nx monorepo patterns used by other modules

**Implementation Approach:**
1. Create new `momo-graph` module following standard Nx structure
2. Extract and clean up `momo_graph/` code with proper imports
3. Update `momo-kb` to depend on new `momo-graph` module
4. Migrate tests and benchmarks appropriately
5. Update documentation and examples

## References

- **ADR-009**: `research/adr-009-graph-backend-extraction.md` - Detailed extraction design
- **Current Implementation**: `momo_graph/` directory with GraphBackend
- **Integration Point**: `momo_kb/graph_backend_adapter.py` 
- **Nx Standards**: Existing module patterns in `momo-logger`, `momo-vector-store`, etc.
