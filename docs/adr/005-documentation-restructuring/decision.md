# ADR-005: Documentation Restructuring

## Status
**ACCEPTED** - Implemented 2025-08-10

## Context
The root directory was becoming cluttered with multiple documentation folders (`docs/`, `research/`, `migrations/`) containing overlapping and disorganized content. This made it difficult to:

- Find relevant documentation quickly
- Understand the relationship between ADRs and their implementation guides
- Maintain a clean project structure
- Follow documentation standards

## Decision
Restructure all documentation under a single `docs/` directory with clear categorization:

### New Structure
```
docs/
├── README.md                    # Documentation overview
├── adr/                        # Architecture Decision Records
│   ├── 001-nx-monorepo/
│   │   ├── decision.md         # ADR document
│   │   ├── migration-guide.md  # Implementation steps
│   │   ├── conventions.md      # Standards and conventions
│   │   └── dvc-integration.md  # Supporting documentation
│   ├── 002-python-package-manager/
│   │   ├── decision.md
│   │   └── scripts/           # Migration scripts
│   └── ...
├── research/                   # Research by topic
│   ├── knowledge-base/
│   ├── monorepo-architecture/
│   ├── performance/
│   ├── python-tooling/
│   └── project-management/
└── api/                       # API documentation
```

### Key Principles
1. **ADRs as folders** - Each ADR gets its own folder containing the decision and all related materials
2. **Topic-based research** - Research organized by subject area rather than chronologically
3. **Single source of truth** - All documentation in one place with clear hierarchy
4. **Migration integration** - Migration guides live with their corresponding ADRs

## Consequences

### Positive
- ✅ Clean root directory structure
- ✅ Logical grouping of related documents
- ✅ Easy to find ADRs and their implementation details
- ✅ Scalable structure for future documentation
- ✅ Clear separation between decisions, research, and API docs

### Negative
- ⚠️ One-time effort to reorganize existing content
- ⚠️ Need to update any hardcoded paths in documentation

## Implementation
- [x] Create new `docs/` structure with `adr/`, `research/`, `api/` subdirectories
- [x] Move existing ADRs into numbered folders with supporting materials
- [x] Organize research files by topic area
- [x] Integrate migration guides with their corresponding ADRs
- [x] Remove old `research/` and `migrations/` directories
- [x] Create documentation README with structure explanation