"""Unit tests for custom exceptions."""

import pytest
from momo_vector_store.exceptions import (
    VectorStoreError,
    EmbeddingError,
    BackendError,
    SearchError,
)


class TestVectorStoreError:
    """Test base VectorStoreError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = VectorStoreError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.backend is None

    def test_error_with_backend(self):
        """Test error with backend information."""
        error = VectorStoreError("Connection failed", backend="chroma")

        assert str(error) == "Connection failed"
        assert error.message == "Connection failed"
        assert error.backend == "chroma"


class TestEmbeddingError:
    """Test EmbeddingError."""

    def test_basic_embedding_error(self):
        """Test basic embedding error."""
        error = EmbeddingError("Embedding failed")

        assert str(error) == "Embedding failed"
        assert error.message == "Embedding failed"
        assert error.model is None
        assert error.backend is None

    def test_embedding_error_with_model(self):
        """Test embedding error with model info."""
        error = EmbeddingError(
            "Model not found",
            model="sentence-transformers/all-MiniLM-L6-v2",
            backend="memory",
        )

        assert str(error) == "Model not found"
        assert error.message == "Model not found"
        assert error.model == "sentence-transformers/all-MiniLM-L6-v2"
        assert error.backend == "memory"

    def test_embedding_error_inheritance(self):
        """Test that EmbeddingError inherits from VectorStoreError."""
        error = EmbeddingError("Test error")

        assert isinstance(error, VectorStoreError)
        assert isinstance(error, Exception)


class TestBackendError:
    """Test BackendError."""

    def test_backend_error_required_backend(self):
        """Test that backend parameter is required."""
        error = BackendError("Backend failed", backend="weaviate")

        assert str(error) == "Backend failed"
        assert error.message == "Backend failed"
        assert error.backend == "weaviate"
        assert error.operation is None

    def test_backend_error_with_operation(self):
        """Test backend error with operation info."""
        error = BackendError(
            "Connection timeout", backend="chroma", operation="connect"
        )

        assert str(error) == "Connection timeout"
        assert error.message == "Connection timeout"
        assert error.backend == "chroma"
        assert error.operation == "connect"

    def test_backend_error_inheritance(self):
        """Test that BackendError inherits from VectorStoreError."""
        error = BackendError("Test error", backend="test")

        assert isinstance(error, VectorStoreError)
        assert isinstance(error, Exception)


class TestSearchError:
    """Test SearchError."""

    def test_basic_search_error(self):
        """Test basic search error."""
        error = SearchError("Search failed")

        assert str(error) == "Search failed"
        assert error.message == "Search failed"
        assert error.query is None
        assert error.backend is None

    def test_search_error_with_query(self):
        """Test search error with query info."""
        error = SearchError(
            "No results found", query="artificial intelligence", backend="memory"
        )

        assert str(error) == "No results found"
        assert error.message == "No results found"
        assert error.query == "artificial intelligence"
        assert error.backend == "memory"

    def test_search_error_inheritance(self):
        """Test that SearchError inherits from VectorStoreError."""
        error = SearchError("Test error")

        assert isinstance(error, VectorStoreError)
        assert isinstance(error, Exception)


class TestExceptionChaining:
    """Test exception chaining and context."""

    def test_exception_chaining(self):
        """Test that exceptions can be chained properly."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise BackendError("Backend failed", backend="test") from e
        except BackendError as error:
            assert str(error) == "Backend failed"
            assert error.backend == "test"
            assert isinstance(error.__cause__, ValueError)
            assert str(error.__cause__) == "Original error"

    def test_exception_context_preserved(self):
        """Test that exception context is preserved."""

        def inner_function():
            raise EmbeddingError("Model load failed", model="test-model")

        def outer_function():
            try:
                inner_function()
            except EmbeddingError:
                raise SearchError("Search initialization failed") from None

        with pytest.raises(SearchError) as exc_info:
            outer_function()

        assert str(exc_info.value) == "Search initialization failed"
        assert exc_info.value.query is None
