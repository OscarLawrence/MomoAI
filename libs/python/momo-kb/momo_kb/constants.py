"""
Constants and default configurations for momo-kb.

This module provides centralized configuration with defaults that can be overridden
via environment variables.
"""

import os
from typing import Optional
from langchain_core.embeddings import Embeddings


def get_default_embeddings() -> Optional[Embeddings]:
    """Get default embeddings, respecting environment variables."""
    embeddings_type = os.getenv("MOMO_KB_EMBEDDINGS", "local").lower()

    if embeddings_type == "none":
        return None
    elif embeddings_type == "local":
        from .embeddings import get_default_embeddings

        return get_default_embeddings()
    else:
        from .embeddings import get_default_embeddings

        return get_default_embeddings()


# Default backend configurations
DEFAULT_VECTOR_BACKEND = os.getenv("MOMO_KB_VECTOR_BACKEND", "memory")
DEFAULT_GRAPH_BACKEND = os.getenv("MOMO_KB_GRAPH_BACKEND", "memory")
# DuckDB as production default, memory for testing
DEFAULT_DOCUMENT_BACKEND = os.getenv("MOMO_KB_DOCUMENT_BACKEND", "duckdb")

# Default embeddings
DEFAULT_EMBEDDINGS = get_default_embeddings()

# Performance settings
DEFAULT_SEARCH_LIMIT = int(os.getenv("MOMO_KB_SEARCH_LIMIT", "10"))
DEFAULT_BATCH_SIZE = int(os.getenv("MOMO_KB_BATCH_SIZE", "100"))

# Database configurations
DATABASE_URL = os.getenv("MOMO_KB_DATABASE_URL", ":memory:")
VECTOR_DIMENSIONS = int(os.getenv("MOMO_KB_VECTOR_DIMENSIONS", "384"))

# Environment variable overrides
ENVIRONMENT_OVERRIDES = {
    "embeddings": "MOMO_KB_EMBEDDINGS",
    "vector_backend": "MOMO_KB_VECTOR_BACKEND",
    "graph_backend": "MOMO_KB_GRAPH_BACKEND",
    "document_backend": "MOMO_KB_DOCUMENT_BACKEND",
    "search_limit": "MOMO_KB_SEARCH_LIMIT",
    "batch_size": "MOMO_KB_BATCH_SIZE",
    "database_url": "MOMO_KB_DATABASE_URL",
    "vector_dimensions": "MOMO_KB_VECTOR_DIMENSIONS",
}
