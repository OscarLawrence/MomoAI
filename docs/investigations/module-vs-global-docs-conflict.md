# Investigation: Module vs Global Documentation Conflict

**Date**: 2025-01-11  
**Priority**: High  
**Status**: Identified

## Issue Description

Found conflicting ADR-008 documentation in two different locations:

1. **Global Location**: `/docs/adr/008-logging-standardization/` (correct location)
2. **Module Location**: `/code/libs/python/momo-kb/research/adr-008-unified-knowledgebase-architecture.md` (unexpected)

## Problem

The existence of ADR-008 documentation in a module-specific location creates confusion about:
- Which is the authoritative source
- How to handle module-specific vs global architectural decisions
- Documentation discovery and maintenance

## Impact

- Developer confusion when looking for ADRs
- Potential for documentation drift between locations
- Unclear governance of architectural decisions

## Questions to Resolve

1. Should module-specific ADRs exist in module directories?
2. How do we distinguish between global vs module-specific architectural decisions?
3. What is the canonical location for ADRs that affect multiple modules?
4. How do we prevent documentation duplication and drift?

## Recommended Actions

1. Establish clear documentation hierarchy and governance
2. Define when ADRs belong in global vs module locations
3. Implement tooling to detect documentation conflicts
4. Create migration plan for existing conflicting documentation

## Next Steps

- Review actual ADR-008 content in correct global location
- Determine if module-specific ADR is outdated or serves different purpose
- Establish documentation governance policy