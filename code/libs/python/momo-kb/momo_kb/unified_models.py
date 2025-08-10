"""
Unified data models for the KnowledgeBase system.

Provides consistent, filterable data structures that work across all backends.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Standard document types for consistent categorization."""

    PERSON = "person"
    DOCUMENT = "document"
    ORGANIZATION = "organization"
    CONCEPT = "concept"
    EVENT = "event"
    LOCATION = "location"
    CUSTOM = "custom"


class Document(BaseModel):
    """
    Unified document format for consistent structure across all backends.

    Designed for maximum filterability and consistent querying.
    """

    # Core identification
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: DocumentType = DocumentType.CUSTOM

    # Content structure
    title: Optional[str] = None
    content: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # Backend tracking
    backend_ids: Dict[str, str] = Field(
        default_factory=dict
    )  # backend_name -> backend_specific_id

    class Config:
        frozen = True  # Immutable

    def with_backend_id(self, backend_name: str, backend_id: str) -> "Document":
        """Return new document with backend ID mapping."""
        new_backend_ids = self.backend_ids.copy()
        new_backend_ids[backend_name] = backend_id
        return self.model_copy(
            update={"backend_ids": new_backend_ids, "updated_at": datetime.utcnow()}
        )

    def get_backend_id(self, backend_name: str) -> Optional[str]:
        """Get backend-specific ID for this document."""
        return self.backend_ids.get(backend_name)


class Relationship(BaseModel):
    """
    Unified relationship format for connecting documents.

    Represents connections between documents across backends.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str  # Document ID
    target_id: str  # Document ID
    relationship_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = None

    # Backend tracking
    backend_ids: Dict[str, str] = Field(default_factory=dict)

    class Config:
        frozen = True  # Immutable

    def with_backend_id(self, backend_name: str, backend_id: str) -> "Relationship":
        """Return new relationship with backend ID mapping."""
        new_backend_ids = self.backend_ids.copy()
        new_backend_ids[backend_name] = backend_id
        return self.model_copy(update={"backend_ids": new_backend_ids})


class SearchResult(BaseModel):
    """Unified search result format."""

    documents: List[Document] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)

    # Search metadata
    query: str = ""
    total_results: int = 0
    search_time_ms: float = 0.0
    backends_used: List[str] = Field(default_factory=list)

    # Scoring (for ranked results)
    scores: List[float] = Field(default_factory=list)

    class Config:
        frozen = True


class KnowledgeBaseStats(BaseModel):
    """Statistics about the knowledge base state."""

    # Content counts
    total_documents: int = 0
    total_relationships: int = 0
    document_types: Dict[str, int] = Field(default_factory=dict)

    # Backend information
    active_backends: List[str] = Field(default_factory=list)
    backend_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # System information
    created_at: datetime
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_operations: int = 0
    memory_usage_mb: Optional[float] = None

    class Config:
        frozen = True
