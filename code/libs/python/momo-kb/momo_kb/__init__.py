"""
Momo KnowledgeBase - High-performance, multi-agent, immutable knowledge graph.

Core exports for the knowledge base system.
"""

from .knowledge_base import KnowledgeBase
from .unified_models import Document, Relationship, SearchResult, KnowledgeBaseStats, DocumentType

# Legacy exports for backward compatibility
from .models import Node, Edge, Diff, DiffType, QueryResult

__all__ = [
    # New unified interface
    "KnowledgeBase",
    "Document",
    "Relationship", 
    "SearchResult",
    "KnowledgeBaseStats",
    "DocumentType",
    
    # Legacy exports (for backward compatibility)
    "Node",
    "Edge", 
    "Diff",
    "DiffType",
    "QueryResult",
]

__version__ = "0.1.0"