# Type Definitions

Comprehensive type system for momo-kb providing full type safety and IDE support. Includes protocol definitions, data classes, and type aliases.

## Core Types

- `document.py`: Document, DocumentMetadata, SearchResult data classes
- `search.py`: SearchOptions and query parameter types  
- `backend.py`: Protocol definitions for all backend types

## Design Principles

- **Protocol-based**: Use typing.Protocol for interface definitions
- **Pydantic integration**: Rich validation and serialization support
- **Async typing**: Proper typing for async operations
- **Generic types**: Support for parameterized types where appropriate

## Agent Integration

Type definitions designed for multi-agent consumption with rich metadata support enabling agent discovery and task matching through similarity search.