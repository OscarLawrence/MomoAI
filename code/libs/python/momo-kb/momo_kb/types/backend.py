"""Backend configuration types using Pydantic."""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class StorageBackend(str, Enum):
    """Supported storage backend types."""

    VECTOR = "vector"
    GRAPH = "graph"
    DOCUMENT = "document"
    HYBRID = "hybrid"


class QueryStrategy(str, Enum):
    """Available query strategies."""

    VECTOR_ONLY = "vector_only"
    GRAPH_ONLY = "graph_only"
    HYBRID = "hybrid"
    AUTO = "auto"


class BackendConfig(BaseModel):
    """Configuration for storage backends."""

    backend_type: StorageBackend
    config: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    priority: int = Field(
        default=1, ge=1, description="Higher priority = preferred for queries"
    )

    model_config = ConfigDict(extra="allow")


class RelationshipSpec(BaseModel):
    """Specification for document relationships in graph storage."""

    source_field: str = Field(description="Source metadata field")
    target_field: str = Field(description="Target metadata field")
    relationship_type: str = Field(
        default="related_to", description="Type of relationship"
    )
    bidirectional: bool = Field(
        default=True, description="Create bidirectional relationships"
    )
    weight: float = Field(default=1.0, ge=0.0, description="Relationship weight")

    model_config = ConfigDict(validate_assignment=True)


class IndexingPipeline(BaseModel):
    """Configuration for document indexing pipeline."""

    extract_relationships: bool = Field(
        default=True, description="Extract document relationships"
    )
    relationship_specs: List[RelationshipSpec] = Field(
        default_factory=lambda: [
            RelationshipSpec(
                source_field="type", target_field="type", relationship_type="same_type"
            ),
            RelationshipSpec(
                source_field="category",
                target_field="category",
                relationship_type="same_category",
            ),
            RelationshipSpec(
                source_field="author",
                target_field="author",
                relationship_type="same_author",
            ),
            RelationshipSpec(
                source_field="source",
                target_field="source",
                relationship_type="same_source",
            ),
        ],
        description="Relationship extraction specifications",
    )
    index_metadata: bool = Field(default=True, description="Index document metadata")
    chunk_size: Optional[int] = Field(
        default=None, ge=1, description="Document chunking size"
    )
    overlap_size: int = Field(default=0, ge=0, description="Chunk overlap size")

    model_config = ConfigDict(validate_assignment=True)
