# Repository Restructuring Migration Guide

**Date:** 2025-08-09  
**Type:** Organizational Restructuring  
**Impact:** Low Risk - Automated Nx Migration  
**Execution Time:** ~15 minutes

## Overview

This migration implements a **Code Directory Pattern** to separate source code from other repository concerns, improving navigation and organization clarity.

## Current Structure Issues

- `apps/` and `libs/` mixed with other concerns at root level
- Creates visual noise and navigation friction
- Inconsistent with enterprise patterns identified in research

## Target Structure

```
MomoAI-nx/
├── code/                   # All source code (NEW)
│   ├── apps/              # Applications (MOVED)
│   │   ├── cli/
│   │   ├── core/
│   │   └── web/
│   └── libs/              # Libraries (MOVED)
│       └── python/
│           ├── momo-kb/
│           ├── momo-logger/
│           ├── momo-graph-store/
│           ├── momo-vector-store/
│           ├── momo-store-document/
│           └── kb-playground/
├── research/              # Strategic analysis (UNCHANGED)
├── docs/                  # Documentation (UNCHANGED)
├── migrations/            # Migration guides (UNCHANGED)
├── data/                  # Data artifacts (UNCHANGED)
├── scripts/               # Automation scripts (UNCHANGED)
└── tools/                 # Development tools (UNCHANGED)
```

## Pre-Migration Checklist

- [ ] Verify all projects build successfully: `pnpm nx run-many -t build`
- [ ] Verify all tests pass: `pnpm nx run-many -t test-fast --skip-nx-cache`
- [ ] Check git status is clean or acceptable
- [ ] Create backup branch: `git checkout -b backup/before-restructuring`

## Migration Steps

### Step 1: Create code directory structure
```bash
mkdir -p code
```

### Step 2: Move applications using Nx generators
```bash
# Move each application - Nx handles all dependency updates
nx g @nx/workspace:move --project web --destination code/apps/web
nx g @nx/workspace:move --project cli --destination code/apps/cli  
nx g @nx/workspace:move --project core --destination code/apps/core
```

### Step 3: Move libraries using Nx generators
```bash
# Move Python libraries
nx g @nx/workspace:move --project momo-kb --destination code/libs/python/momo-kb
nx g @nx/workspace:move --project momo-logger --destination code/libs/python/momo-logger
nx g @nx/workspace:move --project momo-graph-store --destination code/libs/python/momo-graph-store
nx g @nx/workspace:move --project momo-vector-store --destination code/libs/python/momo-vector-store
nx g @nx/workspace:move --project momo-store-document --destination code/libs/python/momo-store-document
nx g @nx/workspace:move --project kb-playground --destination code/libs/python/kb-playground
```

### Step 4: Update workspace configuration
Nx automatically updates:
- `nx.json` project paths
- `tsconfig.base.json` path mappings
- All import statements and project references
- `project.json` files in each moved project

### Step 5: Clean up empty directories
```bash
# Remove empty original directories
rmdir apps/ libs/ 2>/dev/null || true
```

## Validation Steps

### Build Verification
```bash
# Test all projects build
pnpm nx run-many -t build

# Test Python modules specifically
pnpm nx run-many -t format --projects="momo-*,kb-playground"
pnpm nx run-many -t test-fast --projects="momo-*,kb-playground"
```

### Dependency Graph Check
```bash
# Visualize new structure
nx graph

# Check for any broken dependencies
nx affected:graph --base=HEAD~1
```

### Import Path Verification
Nx automatically updates all import paths, but verify key integrations work:
```bash
# Run integration tests
pnpm nx run-many -t test-fast
```

## Configuration Updates

### nx.json
No manual updates needed - Nx move generator handles automatically.

### tsconfig.base.json
Path mappings updated automatically by move generator.

### package.json scripts
No changes needed - all Nx commands work with new paths.

## Rollback Plan

If issues arise:
```bash
# Return to backup branch
git checkout backup/before-restructuring

# Or manually reverse moves
nx g @nx/workspace:move --project web --destination apps/web
# ... repeat for all projects
```

## Benefits After Migration

1. **Clear Separation of Concerns**
   - Source code isolated in `code/` directory
   - Documentation, research, migrations clearly separated
   
2. **Improved Navigation** 
   - Less visual noise at root level
   - Logical grouping of related concerns

3. **Enterprise Pattern Alignment**
   - Matches patterns from Nx research
   - Scalable for future growth

4. **Maintained Tooling**
   - All Nx commands work unchanged
   - Build cache and dependency graph preserved
   - No performance impact

## Expected Changes

### Files Modified by Nx Generators:
- `nx.json` - Updated project paths
- `tsconfig.base.json` - Updated path mappings  
- All `project.json` files - Updated references
- Any files with imports - Updated import paths

### Files Created:
- `code/` directory structure
- Updated project files in new locations

### Files Removed:
- Empty `apps/` and `libs/` directories

## Timeline

- **Planning:** 5 minutes (reading this guide)
- **Execution:** 10 minutes (running migration commands)
- **Validation:** 5 minutes (testing builds)
- **Documentation Update:** 5 minutes (updating CLAUDE.md)

**Total: ~25 minutes**

## Success Criteria

- [ ] All Nx projects moved to `code/` structure
- [ ] All builds pass: `pnpm nx run-many -t build`
- [ ] All tests pass: `pnpm nx run-many -t test-fast`
- [ ] Dependency graph shows no broken references
- [ ] CLAUDE.md updated with new structure
- [ ] Repository root is cleaner and more navigable

## Notes

- This migration uses Nx's official `@nx/workspace:move` generator
- All dependency updates are handled automatically
- No code changes required - only organizational
- Migration is fully reversible if needed
- Zero impact on build performance or caching