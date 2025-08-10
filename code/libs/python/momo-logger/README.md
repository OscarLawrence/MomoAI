# Momo Logger

Structured logging module for the Momo AI system. Provides rich, AI-optimized logging capabilities with pluggable backends and formatters.

## Features

- **Structured Logging**: All logs are structured data optimized for both human and AI consumption
- **Multiple Log Levels**: Standard levels plus AI-optimized and role-specific levels
- **Pluggable Backends**: Console, file, and buffer backends with easy extensibility
- **Multiple Formatters**: JSON, text, and AI-optimized formatters
- **Async-First Design**: Built for modern async Python applications
- **Context Management**: Add context to log records with async context managers
- **Type Safety**: Full type hints and Pydantic validation

## Installation

```bash
cd Code/modules/momo-logger
pdm install
```

## Usage

### Basic Logging

```python
from momo_logger import get_logger

logger = get_logger("momo.example")
await logger.info("Application started")
await logger.warning("This is a warning", user_id=123)
await logger.error("An error occurred", error_code="E001")
```

### AI-Optimized Logging

```python
# AI system logs
await logger.ai_system("Agent selection completed", 
                      agent="momo_agent", 
                      selected_agent="developer_agent")

# User-facing logs
await logger.ai_user("I've found the information you requested", 
                    user_facing=True)

# Agent communication logs
await logger.ai_agent("Task dispatched to worker agent")
```

### Role-Specific Logging

```python
# Tester logs
await logger.tester("Test case passed", test_name="document_save_test")

# Developer logs
await logger.developer("Implemented new feature", feature="graph_traversal")

# Architect logs
await logger.architect("Refactored module structure")
```

### Context Management

```python
async with logger.context(user_id="123", session_id="abc"):
    await logger.info("Processing user request")
    await logger.debug("Detailed operation info")
```

## Backends

- **Console**: Standard output for development
- **File**: Persistent logging to files
- **Buffer**: In-memory buffer for testing

## Formatters

- **JSON**: Structured JSON output for analysis tools
- **Text**: Human-readable text output
- **AI**: AI-optimized structured output

## Development

```bash
# Install dependencies
pdm install

# Run tests
pdm run test

# Format code
pdm run format

# Type checking
pdm run typecheck
```