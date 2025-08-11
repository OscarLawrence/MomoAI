# momo-cmd

Universal command interface for MomoAI that intelligently routes any command through a single entry point.

## Features

- **Universal Interface**: Single `mom` command for all operations
- **Context Awareness**: Auto-detects current module and environment
- **Intelligent Routing**: Smart classification of commands (files, modules, passthrough)
- **Environment Integration**: Uses correct uv/nx environments automatically
- **Enhanced Commands**: Adds useful flags to common tools (git, find, etc.)

## Quick Start

```bash
# Install
uv sync

# Basic usage
mom --help
mom --context                    # Show current context
mom --dry-run test-fast          # Preview what would be executed

# File execution
mom test.py                      # Execute Python file
mom scripts/demo.py              # Uses module's uv environment

# Module commands  
mom test-fast                    # Context-aware (current module)
mom test-fast momo-agent         # Explicit module
mom format                       # Format current module

# Enhanced passthrough
mom git status                   # Enhanced with --short --branch
mom find . -name "*.py"          # Excludes __pycache__, .venv, etc.
```

## Architecture

The system uses a strategy pattern with intelligent command detection:

1. **FileExecutionDetector**: Detects file execution (`mom test.py`)
2. **ModuleCommandDetector**: Detects module commands (`mom test-fast`)
3. **ToolchainCommandDetector**: Detects toolchain commands (`mom nx`, `mom npm`)
4. **PassthroughDetector**: Handles arbitrary commands with enhancements

Each detector routes to appropriate execution strategies with fallback chains.

## Context Detection

The system automatically detects:
- **Workspace root**: Looks for nx.json, CLAUDE.md, .git markers
- **Current module**: From directory patterns like `code/libs/python/module-name/`
- **Module capabilities**: Available commands from project.json, package.json

## Development

```bash
# Format code
uv run ruff format .

# Run tests
uv run pytest tests/unit tests/e2e -v

# Type check (if pyright available)
uv run pyright

# Using universal interface
mom format momo-cmd     # Format this module
mom test-fast momo-cmd  # Test this module
```

## Integration

```python
from momo_cmd import ContextAwareCommandRouter

# Programmatic usage
router = ContextAwareCommandRouter(verbose=True, dry_run=False)
success = router.route_and_execute(['test-fast', 'momo-agent'])
```

This module implements the universal command interface described in ADR-009, providing a single, intelligent entry point for all command execution needs in the MomoAI ecosystem.
