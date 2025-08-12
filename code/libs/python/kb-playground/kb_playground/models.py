"""
Core data models for the KB Playground.

Designed for immutability, efficient serialization, and DVC compatibility.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
import uuid
import numpy as np


class Document(BaseModel):
    """
    Immutable document representation with vector embedding.
    
    Each document becomes a node in the vector lattice with relationships
    to other documents based on both semantic similarity and explicit connections.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    title: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    caller_id: Optional[str] = None  # For per-agent query customization
    collection: Optional[str] = None  # For collection-specific behavior
    
    class Config:
        frozen = True  # Immutable
        
    def with_embedding(self, embedding: np.ndarray) -> "Document":
        """Create new document with embedding (immutable update)."""
        return self.model_copy(update={"embedding": embedding.tolist()})
        
    def with_metadata(self, **metadata) -> "Document":
        """Create new document with additional metadata."""
        new_metadata = {**self.metadata, **metadata}
        return self.model_copy(update={"metadata": new_metadata})
        
    @property
    def embedding_array(self) -> Optional[np.ndarray]:
        """Get embedding as numpy array."""
        if self.embedding is None:
            return None
        return np.array(self.embedding)


class Relationship(BaseModel):
    """
    Immutable relationship between documents in the vector lattice.
    
    Relationships can be explicit (user-defined) or implicit (learned from
    vector proximity and usage patterns).
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    target_id: str
    relationship_type: str
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_bidirectional: bool = False
    
    class Config:
        frozen = True
        
    def with_strength(self, strength: float) -> "Relationship":
        """Create new relationship with updated strength."""
        return self.model_copy(update={"strength": max(0.0, min(1.0, strength))})


class SearchResult(BaseModel):
    """
    Rich search result with context and relationship information.
    
    Designed to provide dense, contextual information for agent decision making.
    """
    
    documents: List[Document]
    relationships: List[Relationship] = Field(default_factory=list)
    scores: List[float] = Field(default_factory=list)
    query: str
    total_results: int
    search_time_ms: float
    context_expansion: Dict[str, Any] = Field(default_factory=dict)
    caller_enrichment: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        frozen = True
        
    @property
    def top_document(self) -> Optional[Document]:
        """Get the highest scoring document."""
        return self.documents[0] if self.documents else None
        
    @property
    def related_documents(self) -> List[Document]:
        """Get documents connected via relationships."""
        if not self.relationships:
            return []
            
        doc_ids = {doc.id for doc in self.documents}
        related_ids = set()
        
        for rel in self.relationships:
            if rel.source_id in doc_ids:
                related_ids.add(rel.target_id)
            if rel.target_id in doc_ids:
                related_ids.add(rel.source_id)
                
        return [doc for doc in self.documents if doc.id in related_ids]


class KnowledgeBaseSnapshot(BaseModel):
    """
    Immutable snapshot of the knowledge base state.
    
    Used for versioning and rollback functionality with DVC integration.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    operation_count: int
    document_count: int
    relationship_count: int
    checksum: str  # For integrity verification
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        frozen = True


class Operation(BaseModel):
    """
    Immutable operation record for audit trail and rollback.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str  # add, delete, search, roll
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    caller_id: Optional[str] = None
    affected_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        frozen = True


class QueryEnrichmentConfig(BaseModel):
    """
    Configuration for per-caller and per-collection query enrichment.
    """
    
    caller_id: Optional[str] = None
    collection: Optional[str] = None
    expansion_factor: float = Field(default=1.5, ge=1.0, le=5.0)
    relationship_depth: int = Field(default=2, ge=1, le=5)
    semantic_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_metadata_fields: List[str] = Field(default_factory=list)
    custom_transformations: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        frozen = True