# CLAUDE.md - Momo Logger Module

This file provides Claude Code with context and guidance for working on the momo-logger module.

## Module Overview

The momo-logger module provides structured logging capabilities for the Momo AI system. It offers rich, AI-optimized logging with pluggable backends and formatters designed specifically for multi-agent AI systems.

## Key Architecture Decisions

### Multi-Level Logging System
- **Standard Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL for traditional logging
- **AI-Optimized Levels**: AI_SYSTEM, AI_USER, AI_AGENT, AI_DEBUG for AI-specific contexts
- **Role-Specific Levels**: TESTER, DEVELOPER, ARCHITECT, OPERATOR for specialized agent roles

### Protocol-Based Design
Uses Python protocols for clean separation between interface and implementation, enabling runtime backend swapping and easy testing.

### Structured Data First
All log records are structured data using Pydantic models, with multiple formatters for different output needs.

## Development Workflow

### Optimal Development Flow (REQUIRED ORDER)

**CRITICAL: Always run type checking before testing functionality**

**During development:**
1. **Edit code** freely with focus on functionality  
2. **Format immediately**: Run `pnpm nx run momo-logger:format` after editing files to ensure formatting compliance
3. **Continue editing** - formatting is now handled transparently

**Before testing/validation (MANDATORY ORDER):**
1. **Type check FIRST**: `pnpm nx run momo-logger:typecheck` - catch type issues before functionality testing
2. **Test functionality**: `pnpm nx run momo-logger:test-fast` - validate working code only after types are clean
3. **Never skip typecheck** - type errors will cause confusing test failures

### Essential Commands
```bash
# Navigate to project root (Poetry + Nx integration)
cd /path/to/MomoAI-nx/

# Development setup
pnpm nx run momo-logger:install

# Fast development cycle (MANDATORY flow)
pnpm nx run momo-logger:format         # Format code immediately after editing - prevents linting issues
pnpm nx run momo-logger:typecheck      # ALWAYS run before testing - prevents confusing failures  
pnpm nx run momo-logger:test-fast      # Unit + e2e tests on clean, typed code

# Full validation before commits
pnpm nx run momo-logger:test-all       # Complete test suite with coverage
pnpm nx run momo-logger:lint           # Code style validation
```

### Code Quality Standards
- **100% async operations**: All I/O uses async/await
- **Full type safety**: Python 3.13+ type hints with Protocol definitions
- **Structured data**: All logs are structured using Pydantic models
- **Protocol-first**: Define interfaces before implementations
- **Performance awareness**: All implementations must be benchmarked

## Current Implementation Status

### Completed Features
- Core async Logger implementation with context manager support
- Protocol-based backend and formatter interfaces
- Three built-in backends: Console, File, Buffer
- Three built-in formatters: JSON, Text, AI
- Factory system for dynamic backend loading
- Comprehensive log level hierarchy
- Context management for enriched log records

### Development Focus Areas
1. **Performance optimization**: Efficient log record creation and formatting
2. **Backend extensibility**: Easy addition of new backends
3. **Formatter flexibility**: Support for different output formats
4. **AI integration**: Optimization for AI agent consumption

## File Organization

### Source Structure
```
src/momo_logger/
├── main.py           # Public API entry point
├── core.py           # Core Logger implementation
├── base.py           # Protocol and base class definitions
├── types.py          # Pydantic models and enums
├── factory.py        # Backend factory system
├── constants.py      # Default configurations
├── levels.py         # Log level definitions
├── backends/         # Backend implementations
│   ├── console.py    # Console output backend
│   ├── file.py       # File output backend
│   └── buffer.py     # In-memory buffer backend
└── formatters/       # Formatter implementations
    ├── json.py       # JSON structured formatter
    ├── text.py       # Human-readable formatter
    └── ai.py         # AI-optimized formatter
```

### Configuration Files
- `pyproject.toml`: Dependencies, scripts, and build configuration  
- `README.md`: User documentation
- `CLAUDE.md`: AI context (this file)
- `momo.md` files: AI-friendly context in each directory

### Examples and Testing
- `examples/`: Usage examples demonstrating all features
- `tests/unit/`: Fast isolated tests (< 1s each)
- `tests/e2e/`: End-to-end workflow tests (1-5s)

## Multi-Agent Considerations

### Agent-Friendly Design
- **Role-specific logging**: Different log levels for tester, developer, architect agents
- **AI-optimized output**: Structured data that's easy for AI agents to parse
- **Context enrichment**: Add context that helps agents understand system state
- **User-facing logs**: Clear, readable output for CLI/web interfaces

### Agent Integration Patterns
- Use role-specific log levels to filter relevant information
- Include agent identifiers and roles in log records
- Structure data for easy AI parsing and processing
- Provide both detailed debug logs and user-friendly output

## Common Development Tasks

### Adding New Backend
1. Define implementation inheriting from BaseLogBackend
2. Implement write(), flush(), and close() methods
3. Register backend in factory.py
4. Create comprehensive test suite
5. Update documentation

### Adding New Formatter
1. Define implementation inheriting from BaseLogFormatter
2. Implement format() method
3. Register formatter in appropriate location
4. Create test cases
5. Update documentation

### Performance Optimization
1. Minimize object creation in hot paths
2. Use efficient string formatting
3. Avoid blocking I/O operations
4. Consider buffering for high-throughput scenarios

### Type Safety
1. Use Protocol definitions for all interfaces
2. Provide full type hints including async return types
3. Run `pdm run typecheck` before testing functionality
4. Use Pydantic for data validation where appropriate

## Dependencies and Installation

### Core Dependencies
- `pydantic`: Data validation and serialization
- `typing`: Type hints for Python 3.13+

### Development Dependencies  
- `pytest`: Testing framework with async support
- `pytest-asyncio`: Async testing support
- `black`: Code formatting
- `mypy`: Type checking

### Installation Notes
- Uses Poetry for dependency management with Nx integration via @nxlv/python plugin
- Follows same development workflow as momo-kb
- Designed to integrate seamlessly with existing Momo architecture

## Integration with MomoAI

### Project Context
This module provides logging capabilities for the broader MomoAI multi-agent system. It's designed to work with the knowledge base and other modules while providing rich, structured logging optimized for AI agent consumption.

### Architectural Fit
- Designed for autonomous agent consumption
- Optimized for multi-agent system logging needs
- Structured data supports system analysis and debugging
- Protocol-based design enables runtime adaptation