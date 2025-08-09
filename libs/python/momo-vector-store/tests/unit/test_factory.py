"""Unit tests for factory pattern."""

import pytest
from unittest.mock import Mock, patch
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from momo_vector_store.factory import create_vectorstore, acreate_vectorstore
from momo_vector_store.exceptions import BackendError


class MockEmbeddings(Embeddings):
    """Mock embeddings for testing."""

    def embed_documents(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, text):
        return [0.1, 0.2, 0.3]


@pytest.fixture
def mock_embeddings():
    """Mock embeddings fixture."""
    return MockEmbeddings()


class TestCreateVectorstore:
    """Test the create_vectorstore factory function."""

    def test_create_memory_backend(self, mock_embeddings):
        """Test creating InMemory backend."""
        vectorstore = create_vectorstore("memory", mock_embeddings)

        assert isinstance(vectorstore, VectorStore)
        assert "InMemoryVectorStore" in str(type(vectorstore))

    def test_unsupported_backend_raises_error(self, mock_embeddings):
        """Test that unsupported backend raises BackendError."""
        with pytest.raises(BackendError) as exc_info:
            create_vectorstore("unsupported", mock_embeddings)

        assert "Unsupported backend type: unsupported" in str(exc_info.value)
        assert exc_info.value.backend == "unsupported"

    def test_backend_creation_failure_wrapped(self, mock_embeddings):
        """Test that backend creation failures are wrapped in BackendError."""
        with patch("momo_vector_store.factory._create_memory_backend") as mock_create:
            mock_create.side_effect = Exception("Connection failed")

            with pytest.raises(BackendError) as exc_info:
                create_vectorstore("memory", mock_embeddings)

            assert "Failed to create memory backend" in str(exc_info.value)
            assert exc_info.value.backend == "memory"
            assert exc_info.value.operation == "create"


class TestAsyncFactory:
    """Test async factory function."""

    @pytest.mark.asyncio
    async def test_acreate_vectorstore(self, mock_embeddings):
        """Test async factory function."""
        vectorstore = await acreate_vectorstore("memory", mock_embeddings)

        assert isinstance(vectorstore, VectorStore)
        assert "InMemoryVectorStore" in str(type(vectorstore))

    @pytest.mark.asyncio
    async def test_acreate_vectorstore_error(self, mock_embeddings):
        """Test async factory function error handling."""
        with pytest.raises(BackendError):
            await acreate_vectorstore("unsupported", mock_embeddings)
