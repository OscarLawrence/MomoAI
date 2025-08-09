# MomoAI Documentation Index

This directory contains the structured documentation for the MomoAI multi-agent system monorepo.

## Documentation Structure

### 📊 `/research/` - Strategic Research
Scientific foundation and technology analysis backing architectural decisions.

- **[monorepo_architecture_research.md](../research/monorepo_architecture_research.md)** - Research on monorepo patterns for multi-agent systems
- **[python_package_management_research.md](../research/python_package_management_research.md)** - Technology evaluation: PDM vs Poetry vs uv
- **[performance_benchmarking_research.md](../research/performance_benchmarking_research.md)** - Benchmarking strategies for multi-agent systems
- **[research_driven_monorepo_blueprint.md](../research/research_driven_monorepo_blueprint.md)** - Comprehensive blueprint for research-driven development

### 📋 `/docs/` - Architectural Decision Records (ADRs)
Key architectural decisions with rationale and implementation details.

- **[ADR-001-nx-monorepo-adoption.md](ADR-001-nx-monorepo-adoption.md)** - Decision to adopt Nx for monorepo orchestration
- **[ADR-002-python-package-manager-selection.md](ADR-002-python-package-manager-selection.md)** - Selection of uv as Python package manager
- **[nx-conventions-and-standards.md](nx-conventions-and-standards.md)** - Implementation standards and conventions

### 🔄 `/migrations/` - Implementation History  
Records of actual migrations and their outcomes.

- **[2025-08-09-complete-nx-migration.md](../migrations/2025-08-09-complete-nx-migration.md)** - Complete record of PDM → uv + Nx migration

## Decision Tree Flow

### 1. Research Phase → `/research/`
- Deep technology analysis and scientific validation
- Performance benchmarking and comparison studies
- Multi-agent system specific considerations
- Industry best practices evaluation

### 2. Decision Phase → `/docs/ADR-*.md`
- Architectural Decision Records with clear rationale
- Implementation strategies and trade-off analysis
- Success metrics and risk mitigation
- Structured decision documentation

### 3. Implementation Phase → `/migrations/`
- Step-by-step execution records
- Issues encountered and solutions applied
- Performance validation and lessons learned
- Historical record for future reference

## Current Architecture Status

### ✅ Completed Migrations
- **Nx Monorepo Setup**: Full workspace conversion complete
- **Python Package Management**: All 5 modules migrated from PDM → uv
- **Development Workflow**: Standardized `nx run` commands across all modules
- **Tooling Integration**: pyright, pytest, ruff all working via Nx

### 🏗️ Architecture Components
- **5 Python Modules**: momo-kb, momo-logger, momo-graph-store, momo-vector-store, momo-store-document
- **3 Node.js Applications**: web (Nuxt.js), cli (Node.js), core (Python core system)
- **Development Tooling**: Nx orchestration with uv package management
- **Performance**: 10-35x improvement in dependency management speed

## Development Workflow

### Standard Commands (All Modules)
```bash
# Development workflow
nx run {module}:install      # Install dependencies (uv sync)
nx run {module}:format       # Code formatting (ruff)
nx run {module}:typecheck    # Type checking (pyright)
nx run {module}:test-fast    # Fast tests (unit + e2e)

# Quality assurance
nx run {module}:test-all     # Complete test suite with coverage
nx run {module}:benchmark    # Performance benchmarks
nx run {module}:lint         # Code style checking

# Batch operations
nx run-many -t format        # Format all modules
nx affected -t test-fast     # Test only changed modules
```

### Directory Structure
```
MomoAI-nx/
├── apps/              # Applications (web, cli, core)
├── libs/python/       # Python modules (5 complete modules)
├── docs/              # This directory - ADRs and standards
├── research/          # Strategic research and analysis
├── migrations/        # Implementation history
└── CLAUDE.md          # Root development context
```

## Key Principles

### Scientific Approach
- **Research-Driven**: Every major decision backed by thorough analysis
- **Performance-First**: Benchmarks validate all technology choices
- **Documentation-Complete**: Full decision trail from research to implementation

### Multi-Agent Architecture
- **Protocol-Based Design**: Runtime backend swapping for flexibility
- **Modular Components**: Self-contained modules with clear interfaces
- **Intelligent Coordination**: Nx orchestration mirrors agent coordination patterns

### Development Excellence
- **Consistent Tooling**: Identical commands across all modules
- **Type Safety**: Full pyright integration across Python modules
- **Performance Monitoring**: Automated benchmarking and regression detection
- **AI-Friendly Documentation**: CLAUDE.md files provide development context

## Next Steps

### Immediate Development
- Begin implementing core multi-agent functionality in `apps/core/`
- Integrate Python modules into unified agent system
- Establish inter-agent communication protocols

### Architecture Evolution
- Monitor performance characteristics as system scales
- Evaluate additional storage backends based on usage patterns
- Expand benchmarking to cover multi-agent coordination metrics

---

**Last Updated:** 2025-08-09  
**Architecture Status:** Foundation Complete - Ready for Core Development  
**Next Review:** When core multi-agent system reaches MVP