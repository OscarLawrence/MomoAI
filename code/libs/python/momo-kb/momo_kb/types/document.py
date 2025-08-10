"""Document types and metadata using Pydantic."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
import uuid


class DocumentMetadata(BaseModel):
    """
    Document metadata with flexible custom fields.

    Uses Pydantic for validation and serialization.
    """

    source: Optional[str] = None
    author: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    language: str = "en"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    custom: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class Document(BaseModel):
    """
    Core document model with content and metadata.

    Uses Pydantic for validation and automatic ID generation.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)

    model_config = ConfigDict(validate_assignment=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary."""
        metadata_data = data.get("metadata", {})
        return cls(
            id=data["id"],
            content=data["content"],
            metadata=DocumentMetadata(**metadata_data),
        )
