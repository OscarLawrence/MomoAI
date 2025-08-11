# CLAUDE.md

## momo-cmd: Universal Command Interface

### Purpose
Context-aware, universal command interface that intelligently routes any command through a single entry point `mom <anything>`. Provides automatic environment detection, intelligent fallback chains, and seamless integration with existing MomoAI modules.

### Key Features
- **Universal Interface**: Single `mom` command for everything
- **Context Awareness**: Auto-detects current module and environment
- **Intelligent Routing**: File execution, module commands, and passthrough with enhancements
- **Environment Integration**: Uses correct uv/nx environments automatically
- **Fallback Chains**: Multiple execution strategies with graceful degradation

### Usage Patterns

#### File Execution
```bash
mom test.py                    # Execute Python file with environment detection
mom scripts/benchmark.py       # Uses module's uv environment if available
mom build.ts                   # TypeScript execution with npx tsx
```

#### Module Commands (Context-Aware)
```bash
# From within module directory - auto-detects target
mom test-fast                  # Runs for current module
mom format                     # Formats current module
mom lint                       # Lints current module

# Explicit module specification
mom test-fast momo-agent       # Runs test-fast for momo-agent
mom format momo-vector-store   # Formats momo-vector-store
```

#### Passthrough Commands (Enhanced)
```bash
mom git status                 # Enhanced: git status --short --branch
mom git diff                   # Enhanced: git diff --stat
mom find . -name "*.py"        # Enhanced: excludes __pycache__, .venv, etc.
```

### Architecture Overview

```
mom <args...>
      ↓
ContextAwareCommandRouter
      ↓
Command Detection Chain:
1. FileExecutionDetector      # test.py → ContextAwareFileStrategy
2. ModuleCommandDetector      # test-fast → ContextAwareModuleStrategy  
3. ToolchainCommandDetector   # nx, npm → PassthroughCommandStrategy
4. PassthroughDetector        # git, ls → PassthroughCommandStrategy
```

### Context Detection
- **Workspace Root**: Finds nx.json, CLAUDE.md, .git, package.json
- **Current Module**: Detects from directory patterns:
  - `code/libs/python/module-name/...` → module-name
  - `momo-workflow/...` → momo-workflow
- **Module Info**: Auto-discovers available commands from project.json, package.json

### Execution Strategies

#### ContextAwareFileStrategy
- **Python files**: Uses module's `uv run python` if available
- **TypeScript**: Uses `npx tsx`
- **Shell scripts**: Uses `bash`
- **Environment detection**: Automatically uses module environments

#### ContextAwareModuleStrategy  
- **Fallback chain**: nx → uv → common patterns
- **Context-aware**: Uses current module if not specified
- **Common patterns**: test-fast, format, lint, typecheck, install, benchmark

#### PassthroughCommandStrategy
- **Git enhancements**: Adds useful flags (--short --branch, --stat, --oneline)
- **Find enhancements**: Excludes common directories (__pycache__, .venv, node_modules)
- **Directory exclusions**: Automatic filtering for development tools

### Integration Points

#### With momo-agent
```python
from momo_cmd import ContextAwareCommandRouter

# Universal command execution
router = ContextAwareCommandRouter()
success = router.route_and_execute(['test-fast', 'momo-agent'])
```

#### With momo-workflow
```python
from momo_cmd import ContextAwareCommandRouter

def execute_workflow_step(command_args):
    router = ContextAwareCommandRouter()
    return router.route_and_execute(command_args)
```

### Development Commands

```bash
# Development workflow (from module root)
uv run ruff format .           # Format code
uv run ruff check .            # Lint code  
uv run pytest tests/unit tests/e2e -v  # Run tests

# Or using universal interface (from anywhere in workspace)
mom format momo-cmd            # Format this module
mom lint momo-cmd              # Lint this module
mom test-fast momo-cmd         # Test this module
```

### Testing Strategy
- **Unit tests**: Individual component testing with mocking
- **Integration tests**: End-to-end workflow testing  
- **Error handling**: Comprehensive error scenarios
- **Performance**: Command routing overhead < 50ms

### Key Files
- **cli.py**: Universal `mom` command entry point
- **router.py**: Main command routing and execution logic
- **context.py**: Workspace and module context detection
- **detectors.py**: Command classification system
- **strategies/**: Execution strategy implementations
  - **file.py**: File execution with environment detection
  - **module.py**: Module commands with fallback chains
  - **passthrough.py**: Enhanced arbitrary command execution

### Configuration
- **Minimal configuration**: Convention-based approach reduces YAML needs
- **Auto-discovery**: Commands discovered from project.json, package.json
- **Smart defaults**: Intelligent enhancements without explicit configuration

### Performance Characteristics
- **Context detection**: ~10-50ms (cached after first detection)
- **Command classification**: ~1-5ms per command
- **Execution overhead**: Minimal - direct subprocess calls
- **Memory usage**: Lightweight - context caching only

### Error Handling
- **File not found**: Suggests similar files in directory
- **Module not found**: Lists available modules
- **Command not found**: Shows available commands for module
- **Execution timeout**: Configurable with clear messaging
- **Graceful degradation**: Falls back through execution strategies

This module represents the culmination of ADR-009's universal command interface design, providing a single, intelligent entry point for all command execution needs in the MomoAI ecosystem.