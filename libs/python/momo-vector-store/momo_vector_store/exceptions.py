"""Vector store specific exceptions."""

from typing import Optional


class VectorStoreError(Exception):
    """Base exception for vector store operations."""

    def __init__(self, message: str, backend: Optional[str] = None):
        self.message = message
        self.backend = backend
        super().__init__(self.message)


class EmbeddingError(VectorStoreError):
    """Raised when embedding operations fail."""

    def __init__(
        self, message: str, model: Optional[str] = None, backend: Optional[str] = None
    ):
        self.model = model
        super().__init__(message, backend)


class BackendError(VectorStoreError):
    """Raised when backend-specific operations fail."""

    def __init__(self, message: str, backend: str, operation: Optional[str] = None):
        self.operation = operation
        super().__init__(message, backend)


class SearchError(VectorStoreError):
    """Raised when search operations fail."""

    def __init__(
        self, message: str, query: Optional[str] = None, backend: Optional[str] = None
    ):
        self.query = query
        super().__init__(message, backend)
