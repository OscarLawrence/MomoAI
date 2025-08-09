"""Search-related types using Pydantic."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

from .document import Document


class SearchOptions(BaseModel):
    """
    Options for customizing search behavior using Pydantic validation.

    Provides fine-grained control over search operations while maintaining
    simplicity for basic use cases.
    """

    # Result limits
    limit: int = Field(
        default=10, ge=1, le=1000, description="Maximum number of results"
    )
    offset: int = Field(default=0, ge=0, description="Number of results to skip")

    # Relevance filtering
    threshold: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum relevance score"
    )

    # Metadata filtering
    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata filters"
    )

    # Search behavior
    semantic: bool = Field(default=True, description="Use semantic search")
    exact_match: bool = Field(default=False, description="Require exact text matching")

    # Result formatting
    include_content: bool = Field(
        default=True, description="Include document content in results"
    )
    include_metadata: bool = Field(
        default=True, description="Include document metadata"
    )
    include_scores: bool = Field(default=True, description="Include relevance scores")

    # Advanced options (implementation-specific)
    advanced: Dict[str, Any] = Field(
        default_factory=dict, description="Advanced search options"
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,  # Strict validation
    )


class SearchResult(BaseModel):
    """
    A single search result with document and relevance information.
    """

    document: Document
    score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    rank: int = Field(ge=1, description="Result ranking")

    # Optional context (e.g., highlighted passages)
    context: Optional[str] = Field(default=None, description="Search context")
    highlights: List[str] = Field(
        default_factory=list, description="Highlighted text snippets"
    )

    model_config = ConfigDict(validate_assignment=True)
