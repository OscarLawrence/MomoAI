"""
KB Playground - Experimental High-Performance Knowledge Base

A vector-graph hybrid knowledge base with immutable design and DVC integration.
Optimized for outstanding query quality and agent context building.
"""

from .knowledge_base import KnowledgeBase
from .models import Document, Relationship, SearchResult
from .vector_lattice import VectorLattice
from .relationship_engine import RelationshipEngine

__version__ = "0.1.0"
__all__ = [
    "KnowledgeBase",
    "Document", 
    "Relationship",
    "SearchResult",
    "VectorLattice",
    "RelationshipEngine",
]