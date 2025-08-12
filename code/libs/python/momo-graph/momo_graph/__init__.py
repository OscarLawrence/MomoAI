"""
Momo Graph - High-performance immutable graph database backend.

Provides graph-specific storage, indexing, and query capabilities
as a pluggable backend for the Momo KnowledgeBase system.
"""

from .models import GraphNode, GraphEdge, GraphDiff, GraphDiffType, GraphQueryResult
from .storage import GraphStorageTier, GraphThreeTierStorage
from .indexing import GraphIndexManager
from .core import GraphBackend

__all__ = [
    "GraphBackend",
    "GraphNode",
    "GraphEdge",
    "GraphDiff",
    "GraphDiffType",
    "GraphQueryResult",
    "GraphStorageTier",
    "GraphThreeTierStorage",
    "GraphIndexManager",
]

__version__ = "0.1.0"
