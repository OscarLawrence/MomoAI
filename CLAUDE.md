# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Codebase Overview

MomoAI is a revolutionary self-extending multi-agent system with modular architecture designed for long-term maintainability and scientific rigor.

## Architecture Structure

```
MomoAI-nx/
├── apps/                    # User-facing applications
│   ├── web/                # Nuxt.js frontend
│   ├── cli/                # Node.js CLI
│   └── core/               # Core Momo functionality
└── libs/python/            # Python libraries (uv + Nx managed)
    ├── momo-kb/           # Knowledge base abstraction - COMPLETE
    ├── momo-logger/       # Structured logging system - COMPLETE
    ├── momo-graph-store/  # Graph database abstraction - COMPLETE
    ├── momo-vector-store/ # Vector store abstraction - COMPLETE
    └── momo-store-document/ # Document store abstraction - COMPLETE
```

## Development Commands

### Python Modules (uv + Nx Integration)

All Python modules use uv with @nxlv/python plugin for seamless Nx integration. Use Nx commands from the root:

```bash
# Development setup - installs uv dependencies via Nx
nx run <module-name>:install

# MANDATORY Development Workflow (REQUIRED ORDER)
nx run <module-name>:format      # Format code immediately after editing
nx run <module-name>:typecheck   # ALWAYS run before testing
nx run <module-name>:test-fast   # Unit + e2e tests on clean code

# Additional commands
nx run <module-name>:test-all    # Complete suite with coverage
nx run <module-name>:benchmark   # Performance benchmarks
nx run <module-name>:lint        # Check code style

# Run commands across all modules
nx run-many -t format            # Format all Python modules
nx affected -t test-fast         # Test only affected modules
```

### Web/CLI Applications (Node.js)

```bash
# Web app (Nuxt.js)
nx run web:serve   # Starts on port 3000

# CLI app 
nx run cli:build

# Core app
nx run core:build
```

## Key Principles

### Development Standards
- **Scientific Approach**: All major decisions backed by research and benchmarks
- **Long-term Focus**: Code written for decades of maintainability
- **Performance First**: All implementations must be performance-tested
- **Protocol-based Design**: Interfaces over implementations for modularity
- **100% Test Coverage**: Comprehensive testing with async support
- **Type Safety**: Full type hints with Python 3.13+ features

### Multi-Agent Architecture
- **Self-extending**: Dynamic agent creation when capabilities are missing
- **Knowledge-driven**: Agent selection via semantic similarity search
- **Async-first**: All I/O operations designed for high concurrency
- **Context-aware**: Rich metadata for agent decision making

## Testing Strategy

Standardized test structure across all modules:

```bash
tests/
├── unit/          # Fast isolated tests (< 1s)
├── e2e/           # End-to-end workflow tests (1-5s)
└── integration/   # Component interaction tests (1-10s)

benchmarks/        # Performance benchmarks (10s+)
```

## Development Workflow

### MANDATORY Development Flow (All Python Modules)

**NOTE: Type checking requires pyright to be available in the environment**

1. **Edit code** with focus on functionality
2. **Format immediately**: `pnpm nx run <module>:format` after editing files
3. **Lint code**: `pnpm nx run <module>:lint` - check code style and common issues
4. **Type check** (if pyright available): `pnpm nx run <module>:typecheck` - prevents confusing test failures
5. **Test functionality**: `pnpm nx run <module>:test-fast` - validate working code

**Alternative workflow when typecheck fails:**
- Skip typecheck temporarily and rely on runtime testing
- Use `--skip-dependencies` to bypass typecheck dependencies: `pnpm nx run <module>:test-fast --skip-dependencies`

### Code Quality Standards
- **Test-driven development** wherever possible
- **Async patterns**: All I/O operations use async/await
- **Full type hints**: Python 3.13+ with Protocol definitions
- **Performance awareness**: Benchmark all implementations
- **Never skip typecheck**: Type errors cause confusing failures

## File Organization

### Documentation Hierarchy
- **CLAUDE.md**: Development context files (root + each module/app)
- **momo.md files**: AI-friendly context in each src subdirectory (5-15 lines max)
- **momo.yaml files**: Module configuration (backends, settings)
- **README.md files**: Human-readable documentation
- **research/ folder**: Strategic analysis and architectural research findings

### Module Status
- **momo-kb**: Knowledge base abstraction - COMPLETE
- **momo-logger**: Structured logging system - COMPLETE  
- **momo-graph-store**: Graph database abstraction - COMPLETE
- **momo-vector-store**: Vector store abstraction - COMPLETE
- **momo-store-document**: Document store abstraction - COMPLETE
- **core**: Core Momo functionality - IN DEVELOPMENT
- **momo-docs**: Revolutionary documentation system - IN DEVELOPMENT

## Standardized Module Structure

All Python modules follow this template:

```
module-name/
├── module_name/         # Source code (direct structure)
├── tests/               # Test suite (unit/, e2e/, integration/)
├── scripts/             # Usage examples (numbered 01-05)
├── benchmarks/          # Performance validation
├── CLAUDE.md            # Module-specific development context
├── README.md            # Human documentation
├── pyproject.toml       # uv configuration
├── uv.lock             # uv lock file
└── project.json        # Nx project configuration
```

### Standardized Scripts (via Nx)
- **install**: `pnpm nx run <module>:install` - `uv sync` - Install dependencies
- **format**: `pnpm nx run <module>:format` - `uv run ruff format` - Code formatting
- **lint**: `pnpm nx run <module>:lint` - `uv run ruff check` - Code linting
- **typecheck**: `pnpm nx run <module>:typecheck` - `uv run pyright` - Type checking (requires pyright)
- **test-fast**: `pnpm nx run <module>:test-fast` - `uv run pytest tests/unit/ tests/e2e/` (development workflow)
- **test-all**: `pnpm nx run <module>:test-all` - Complete suite with coverage
- **benchmark**: `pnpm nx run <module>:benchmark` - Performance validation

### DVC MLOps Commands

```bash
# Core workflow
nx run-many -t dvc-pull          # Pull latest KB artifacts
nx run kb-ingest                 # Process code into KB artifacts  
nx run docs-generate             # Generate fresh documentation
nx run-many -t dvc-push         # Share KB artifacts with team

# Module-specific
nx run momo-kb:dvc-repro        # Rebuild KB module artifacts
nx run momo-vector-store:dvc-repro  # Rebuild vector artifacts
nx run momo-graph-store:dvc-repro   # Rebuild graph artifacts
nx run momo-store-document:dvc-repro # Rebuild document artifacts
nx run momo-logger:dvc-repro    # Rebuild logger artifacts
```

## Repository Conventions

- **Self-contained modules**: Each module/app has own dependencies
- **Performance-driven**: All major decisions backed by benchmarks  
- **Scientific rigor**: Research-backed technology choices
- **Long-term focus**: Code written for decades of maintainability
- **Early development stage**: Do not keep legacy code or configs unless explicitly asked
- **File length limit**: Never create files longer than 500 lines - break into logical pieces
- **Test-driven development**: Use TDD guidelines whenever applicable

## Important Guidelines

- **Never jump to implementations** without confirming implementation details first
- **Module-specific details**: Check individual module CLAUDE.md files for specific guidance
- **Each module is self-contained**: Navigate to specific modules for detailed development workflows