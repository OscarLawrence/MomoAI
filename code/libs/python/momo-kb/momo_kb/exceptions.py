"""
Custom exceptions for the knowledge base system.
"""


class KnowledgeBaseError(Exception):
    """Base exception for all knowledge base related errors."""

    pass


class DocumentNotFoundError(KnowledgeBaseError):
    """Raised when a requested document cannot be found."""

    def __init__(self, document_id: str):
        self.document_id = document_id
        super().__init__(f"Document with ID '{document_id}' not found")


class SearchError(KnowledgeBaseError):
    """Raised when a search operation fails."""

    pass


class ValidationError(KnowledgeBaseError):
    """Raised when document or query validation fails."""

    pass


class ConnectionError(KnowledgeBaseError):
    """Raised when connection to the knowledge base backend fails."""

    pass
