"""
Momo KnowledgeBase - High-performance, multi-agent, immutable knowledge graph.

Core exports for the knowledge base system.
"""

from .models import Node, Edge, Diff, DiffType, QueryResult
from .core import KnowledgeBase
from .storage import StorageTier

__all__ = [
    "KnowledgeBase",
    "Node", 
    "Edge",
    "Diff",
    "DiffType",
    "QueryResult",
    "StorageTier",
]

__version__ = "0.1.0"