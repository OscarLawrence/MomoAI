# MomoAI Documentation

This directory contains all project documentation organized by type and topic.

## Structure

### 📋 Architecture Decision Records (ADR)
- `adr/001-nx-monorepo/` - Nx monorepo adoption decision and implementation
- `adr/002-python-package-manager/` - Python package manager selection (uv)
- `adr/003-kb-implementation/` - Knowledge base implementation specifications
- `adr/004-nx-restructuring/` - Nx restructuring and organization

### 🔬 Research
- `research/knowledge-base/` - Knowledge base solutions and multi-agent systems
- `research/monorepo-architecture/` - Monorepo patterns and best practices
- `research/performance/` - Performance benchmarking and optimization
- `research/python-tooling/` - Python tooling, MLOps, and production guides
- `research/project-management/` - Project retrospectives and lessons learned

### 📚 API Documentation
- `api/` - API reference documentation (generated and manual)

## ADR Format

Each ADR follows this structure:
```
adr/XXX-topic-name/
├── decision.md          # Main ADR document
├── migration-guide.md   # Implementation/migration steps
├── conventions.md       # Standards and conventions
├── scripts/            # Related automation scripts
└── supporting-docs/    # Additional context documents
```

## Contributing

- Place new ADRs in numbered folders with descriptive names
- Organize research by primary topic area
- Keep API docs current with code changes
- Follow the established naming conventions