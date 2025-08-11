"""
Core data models for the Momo Graph Backend.

Implements immutable graph nodes, edges, and diff-based operations
for the graph storage backend.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class GraphDiffType(str, Enum):
    """Types of operations that can be performed on the graph."""

    INSERT_NODE = "insert_node"
    DELETE_NODE = "delete_node"
    INSERT_EDGE = "insert_edge"
    DELETE_EDGE = "delete_edge"


class GraphNode(BaseModel):
    """Immutable graph node with properties and metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Usage tracking for pruning
    access_count: int = Field(default=0)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)

    # Semantic search capabilities
    embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    embedding_timestamp: Optional[datetime] = None

    class Config:
        frozen = True  # Immutable

    @model_validator(mode="before")
    @classmethod
    def set_embedding_timestamp(cls, values):
        """Set embedding timestamp if embedding is provided but timestamp is not."""
        if isinstance(values, dict):
            if (
                values.get("embedding") is not None
                and values.get("embedding_timestamp") is None
            ):
                values["embedding_timestamp"] = datetime.utcnow()
        return values

    def with_access(self) -> "GraphNode":
        """Return a new node with updated access tracking."""
        return self.model_copy(
            update={
                "access_count": self.access_count + 1,
                "last_accessed": datetime.utcnow(),
            }
        )

    def with_embedding(self, embedding: List[float], model: str) -> "GraphNode":
        """Return a new node with embedding data."""
        return self.model_copy(
            update={
                "embedding": embedding,
                "embedding_model": model,
                "embedding_timestamp": datetime.utcnow(),
            }
        )


class GraphEdge(BaseModel):
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

    def with_access(self) -> "GraphEdge":
        """Return a new edge with updated access tracking."""
        return self.model_copy(
            update={
                "access_count": self.access_count + 1,
                "last_accessed": datetime.utcnow(),
            }
        )


class GraphDiff(BaseModel):
    """Immutable record of a graph operation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    operation: GraphDiffType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Operation data
    node: Optional[GraphNode] = None
    edge: Optional[GraphEdge] = None

    # Metadata
    agent_id: Optional[str] = None
    session_id: Optional[str] = None

    class Config:
        frozen = True  # Immutable

    def reverse(self) -> "GraphDiff":
        """Create the reverse diff for rollback operations."""
        reverse_ops = {
            GraphDiffType.INSERT_NODE: GraphDiffType.DELETE_NODE,
            GraphDiffType.DELETE_NODE: GraphDiffType.INSERT_NODE,
            GraphDiffType.INSERT_EDGE: GraphDiffType.DELETE_EDGE,
            GraphDiffType.DELETE_EDGE: GraphDiffType.INSERT_EDGE,
        }

        return self.model_copy(
            update={
                "id": str(uuid4()),
                "operation": reverse_ops[self.operation],
                "timestamp": datetime.utcnow(),
            }
        )


class GraphQueryResult(BaseModel):
    """Result from a graph query."""

    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Performance metrics
    query_time_ms: float = 0.0
    storage_tier: str = "runtime"


class SemanticQueryResult(BaseModel):
    """Result from a semantic similarity query."""

    nodes: List[GraphNode] = Field(default_factory=list)
    similarity_scores: List[float] = Field(default_factory=list)
    query_embedding: Optional[List[float]] = None
    threshold: float = 0.0
    query_time_ms: float = 0.0
    storage_tier: str = "runtime"

    def __post_init__(self):
        """Validate that nodes and scores have same length."""
        if len(self.nodes) != len(self.similarity_scores):
            raise ValueError("Number of nodes must match number of similarity scores")


class HybridQueryResult(BaseModel):
    """Result from a hybrid semantic + structural query."""

    nodes: List[GraphNode] = Field(default_factory=list)
    semantic_scores: List[float] = Field(default_factory=list)
    structural_matches: List[bool] = Field(default_factory=list)
    combined_scores: List[float] = Field(default_factory=list)
    alpha: float = 0.5  # Balance between semantic (alpha) and structural (1-alpha)
    query_time_ms: float = 0.0
    storage_tier: str = "mixed"

    def __post_init__(self):
        """Validate that all lists have same length."""
        lengths = [
            len(self.nodes),
            len(self.semantic_scores),
            len(self.structural_matches),
            len(self.combined_scores),
        ]
        if not all(l == lengths[0] for l in lengths):
            raise ValueError("All result lists must have the same length")
