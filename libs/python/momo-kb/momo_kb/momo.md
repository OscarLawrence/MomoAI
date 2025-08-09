# MomoKB Core Package

Main implementation of the momo-kb abstraction layer. Provides unified interface to vector, graph, and document backends with async-first design.

## Core Components

- `core.py`: CoreKnowledgeBase - main implementation that orchestrates backends
- `factory.py`: Backend creation and configuration management with persistence strategies
- `base.py`: Protocol definitions for KnowledgeBase interface
- `embeddings.py`: Local embedding models with graceful fallbacks
- `main.py`: High-level convenience functions and default instances

## Backend Integration

The package follows a three-backend architecture with unified document storage:
- **Vector backends** (stores/vector/): Semantic similarity search
- **Graph backends** (stores/graph/): Relationship traversal
- **Document backends** (stores/document/): Unified pandas-based storage with pluggable persistence

## Unified Document Architecture

All document storage uses pandas DataFrames with pluggable persistence strategies:
- `memory`: In-memory only (NoPersistence)
- `csv`: CSV file persistence (CSVPersistence)
- `hdf5`: HDF5 binary format (HDF5Persistence)
- `duckdb`: ACID database with SQL analytics (DuckDBPersistence) - production default

## Type System

Type definitions in `types/` provide comprehensive typing for documents, search options, and backend protocols. Enables full type safety and IDE support.