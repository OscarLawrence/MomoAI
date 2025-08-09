# Nx Conventions and Standards for MomoAI

**Date:** 2025-08-09  
**Status:** Implementation Standards  
**Purpose:** Reference guide for Nx conventions used in MomoAI monorepo

## Project Organization

### Directory Structure
```
MomoAI-nx/
├── apps/              # User-facing applications
│   ├── web/          # Nuxt.js frontend
│   ├── cli/          # Node.js CLI  
│   └── core/         # Core multi-agent system
├── libs/python/       # Python libraries
│   ├── momo-kb/      # Knowledge base abstraction
│   ├── momo-logger/  # Logging system
│   └── momo-*-store/ # Storage abstractions
├── docs/              # Architectural Decision Records
├── research/          # Strategic research
└── migrations/        # Implementation history
```

### Naming Conventions

#### Python Modules
- **Pattern**: `momo-{domain}` (e.g., `momo-kb`, `momo-logger`)
- **Source Directory**: `{module_name}/` (underscores, e.g., `momo_kb/`)
- **Package Name**: Matches source directory for imports

#### Applications
- **Pattern**: Single word descriptors (`web`, `cli`, `core`)
- **Purpose**: User-facing entry points to the system

### Project Types and Tags
```json
{
  "tags": [
    "python",      // Language
    "library",     // Project type  
    "kb",          // Domain
    "multi-agent"  // System scope
  ]
}
```

## Standardized Targets

### Python Module Targets (All modules implement these)
```json
{
  "targets": {
    "install": {
      "executor": "@nxlv/python:install",
      "description": "Install dependencies with uv sync"
    },
    "format": {
      "executor": "@nxlv/python:ruff-format", 
      "description": "Format code with ruff"
    },
    "lint": {
      "executor": "@nxlv/python:ruff-check",
      "description": "Check code style with ruff"
    },
    "typecheck": {
      "executor": "@nxlv/python:run-commands",
      "options": {
        "command": "uv run python -m pyright {sourceRoot}",
        "cwd": "{projectRoot}"
      },
      "description": "Type checking with pyright"
    },
    "test": {
      "executor": "@nxlv/python:run-commands",
      "options": {
        "command": "uv run python -m pytest tests/",
        "cwd": "{projectRoot}"
      },
      "description": "Run all tests"
    },
    "test-fast": {
      "executor": "@nxlv/python:run-commands",
      "options": {
        "command": "uv run python -m pytest tests/unit/ tests/e2e/",
        "cwd": "{projectRoot}"
      },
      "description": "Run unit and e2e tests (development workflow)"
    },
    "test-all": {
      "executor": "@nxlv/python:run-commands", 
      "options": {
        "command": "uv run python -m pytest tests/ --cov={sourceRoot} --cov-report=term-missing --benchmark-skip",
        "cwd": "{projectRoot}"
      },
      "description": "Complete test suite with coverage"
    },
    "benchmark": {
      "executor": "@nxlv/python:run-commands",
      "options": {
        "command": "uv run python -m pytest benchmarks/ --benchmark-only --benchmark-json=../../../benchmark_results/{projectName}.json",
        "cwd": "{projectRoot}"
      },
      "cache": false,
      "description": "Run performance benchmarks"
    }
  }
}
```

### Target Dependencies and Execution Order
```json
{
  "targetDefaults": {
    "typecheck": {
      "dependsOn": ["format"]
    },
    "test-fast": {
      "dependsOn": ["^test-fast", "typecheck"]  
    },
    "test-all": {
      "dependsOn": ["^test-all", "typecheck"]
    }
  }
}
```

## Testing Standards

### Directory Structure
```
tests/
├── unit/          # Fast isolated tests (< 1s each)
├── e2e/           # End-to-end workflow tests (1-5s)
└── integration/   # Component interaction tests (1-10s)

benchmarks/        # Performance benchmarks (10s+)
```

### Test Configuration
- **Framework**: pytest with async support
- **Coverage**: Required for `test-all` target
- **Benchmarking**: pytest-benchmark with JSON export
- **Execution**: Via `uv run python -m pytest` for proper virtual env access

### Test Commands
```bash
# Development workflow (fast feedback)
nx run {module}:test-fast     # unit/ + e2e/ only

# Complete validation
nx run {module}:test-all      # All tests + coverage + benchmarks

# Performance validation  
nx run {module}:benchmark     # pytest-benchmark only
```

## Documentation Standards

### Required Files Per Module
```
module-name/
├── CLAUDE.md      # AI development context (required)
├── README.md      # Human-readable documentation
├── momo.md        # Brief AI context in src/ directories
└── momo.yaml      # Module configuration (if needed)
```

### Documentation Hierarchy
1. **CLAUDE.md**: Comprehensive development context for AI assistance
2. **README.md**: User-facing documentation and usage examples  
3. **momo.md**: Short AI-friendly context in subdirectories (5-15 lines)
4. **momo.yaml**: Configuration files for backend selection

### Content Guidelines
- **CLAUDE.md**: Development workflow, architecture decisions, performance characteristics
- **README.md**: Installation, usage examples, API documentation
- **momo.md**: Brief context for directory purpose and key files

## Caching Strategy

### Cacheable Targets
```json
{
  "cache": true,
  "inputs": ["pythonSrc"],  // Cache based on Python source changes
  "outputs": []             // Most Python tasks don't generate persistent outputs
}
```

### Non-Cacheable Targets
- **benchmark**: Performance measurements should always run fresh
- **serve**: Development servers need to restart
- **install**: Dependency changes require fresh installation

### Cache Inputs
```json
{
  "namedInputs": {
    "pythonSrc": [
      "{projectRoot}/src/**/*.py",
      "{projectRoot}/pyproject.toml",
      "{projectRoot}/uv.lock"
    ]
  }
}
```

## Development Workflow

### Mandatory Development Order (All Modules)
```bash
# 1. Format code immediately after editing
nx run {module}:format

# 2. Type check before testing (catches issues early)  
nx run {module}:typecheck

# 3. Run fast tests for validation
nx run {module}:test-fast
```

### Batch Operations
```bash
# Format all modules
nx run-many -t format

# Test only affected modules  
nx affected -t test-fast

# Run complete validation before commits
nx run-many -t test-all
```

### Performance Commands
```bash
# Benchmark single module
nx run {module}:benchmark

# Benchmark all modules
nx run-many -t benchmark

# Compare performance over time
nx affected -t benchmark --base=main
```

## Integration Patterns

### Cross-Module Dependencies
```json
{
  "implicitDependencies": [
    "momo-logger",        // All modules depend on logging
    "momo-vector-store",  // KB depends on vector storage
    "momo-graph-store"    // KB depends on graph storage
  ]
}
```

### Affected Command Benefits
- **Only changed modules tested**: Saves CI time
- **Dependency-aware**: Tests dependent modules automatically
- **Incremental validation**: Fast feedback on changes

## uv Integration

### Package Manager Configuration
```json
{
  "plugins": [
    {
      "plugin": "@nxlv/python",
      "options": {
        "packageManager": "uv"
      }
    }
  ]
}
```

### Python Tool Execution Pattern
```bash
# Correct: Use python -m for virtual environment tools
uv run python -m pyright
uv run python -m pytest  

# Incorrect: Direct tool execution (may fail)
uv run pyright
uv run pytest
```

## Quality Standards

### Code Quality Tools
- **Formatting**: ruff format (10-100x faster than black)
- **Linting**: ruff check (comprehensive style checking)
- **Type Checking**: pyright (faster than mypy, better IDE integration)
- **Testing**: pytest with async support and benchmarking

### Performance Requirements
- **Dependency Installation**: < 3s with uv (vs 15-30s with PDM)
- **Type Checking**: < 10s for typical module
- **Unit Tests**: < 1s per test on average
- **E2E Tests**: < 5s per test

### Coverage Standards
- **Unit Tests**: Focus on business logic and edge cases
- **E2E Tests**: Cover complete workflows  
- **Integration Tests**: Test component interactions
- **Benchmarks**: Performance validation and regression detection

## Migration Guidelines

### New Module Creation
1. **Use @nxlv/python generator** for consistent structure
2. **Copy standardized project.json** from existing module
3. **Follow naming conventions** for consistency
4. **Add required documentation** (CLAUDE.md, README.md)
5. **Configure proper dependencies** in implicit dependencies

### Module Updates
1. **Preserve target structure** when modifying project.json
2. **Update documentation** when changing APIs
3. **Run benchmark comparisons** when optimizing
4. **Follow development workflow** for all changes

---

**Last Updated:** 2025-08-09  
**Next Review:** When adding new project types or significant tooling changes