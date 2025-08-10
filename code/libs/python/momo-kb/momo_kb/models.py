"""
Core data models for the Momo KnowledgeBase.

Implements immutable nodes, edges, and diff-based operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class DiffType(str, Enum):
    """Types of operations that can be performed on the knowledge graph."""
    INSERT_NODE = "insert_node"
    DELETE_NODE = "delete_node"
    INSERT_EDGE = "insert_edge"
    DELETE_EDGE = "delete_edge"


class Node(BaseModel):
    """Immutable graph node with properties and metadata."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Usage tracking for pruning
    access_count: int = Field(default=0)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True  # Immutable
        
    def with_access(self) -> "Node":
        """Return a new node with updated access tracking."""
        return self.model_copy(update={
            "access_count": self.access_count + 1,
            "last_accessed": datetime.utcnow()
        })


class Edge(BaseModel):
    """Immutable graph edge connecting two nodes."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    relationship: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Usage tracking for pruning
    access_count: int = Field(default=0)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        frozen = True  # Immutable
        
    def with_access(self) -> "Edge":
        """Return a new edge with updated access tracking."""
        return self.model_copy(update={
            "access_count": self.access_count + 1,
            "last_accessed": datetime.utcnow()
        })


class Diff(BaseModel):
    """Immutable record of a knowledge graph operation."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    operation: DiffType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Operation data
    node: Optional[Node] = None
    edge: Optional[Edge] = None
    
    # Metadata
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    
    class Config:
        frozen = True  # Immutable
        
    def reverse(self) -> "Diff":
        """Create the reverse diff for rollback operations."""
        reverse_ops = {
            DiffType.INSERT_NODE: DiffType.DELETE_NODE,
            DiffType.DELETE_NODE: DiffType.INSERT_NODE,
            DiffType.INSERT_EDGE: DiffType.DELETE_EDGE,
            DiffType.DELETE_EDGE: DiffType.INSERT_EDGE,
        }
        
        return self.model_copy(update={
            "id": str(uuid4()),
            "operation": reverse_ops[self.operation],
            "timestamp": datetime.utcnow()
        })


class QueryResult(BaseModel):
    """Result from a knowledge graph query."""
    
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance metrics
    query_time_ms: float = 0.0
    storage_tier: str = "runtime"