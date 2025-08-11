"""Unit tests for VectorStoreManager."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from momo_vector_store.main import VectorStoreManager
from momo_vector_store.exceptions import VectorStoreError


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


@pytest.fixture
def mock_vectorstore():
    """Mock vectorstore fixture."""
    mock = Mock(spec=VectorStore)
    # Properly set the mock's class name and module
    type(mock).__name__ = "MockVectorStore"
    type(mock).__module__ = "test.mock"

    # Set up async methods
    mock.aadd_texts = AsyncMock(return_value=["id1", "id2"])
    mock.aadd_documents = AsyncMock(return_value=["doc1", "doc2"])
    mock.asimilarity_search = AsyncMock(
        return_value=[
            Document(page_content="Test content", metadata={"source": "test"})
        ]
    )
    mock.asimilarity_search_with_score = AsyncMock(
        return_value=[
            (Document(page_content="Test content", metadata={"source": "test"}), 0.95)
        ]
    )

    return mock


@pytest.fixture
def manager(mock_vectorstore):
    """VectorStoreManager fixture."""
    return VectorStoreManager(mock_vectorstore)


class TestVectorStoreManagerInit:
    """Test VectorStoreManager initialization."""

    def test_init_with_vectorstore(self, mock_vectorstore):
        """Test initialization with vectorstore."""
        manager = VectorStoreManager(mock_vectorstore)

        assert manager.vectorstore == mock_vectorstore

    def test_create_classmethod(self, mock_embeddings):
        """Test create classmethod."""
        with patch("momo_vector_store.manager.create_vectorstore") as mock_create:
            mock_vectorstore = Mock(spec=VectorStore)
            mock_create.return_value = mock_vectorstore

            manager = VectorStoreManager.create(
                "memory", mock_embeddings, test_config="value"
            )

            mock_create.assert_called_once_with(
                "memory", mock_embeddings, test_config="value"
            )
            assert isinstance(manager, VectorStoreManager)
            assert manager.vectorstore == mock_vectorstore

    @pytest.mark.asyncio
    async def test_acreate_classmethod(self, mock_embeddings):
        """Test async create classmethod."""
        with patch("momo_vector_store.manager.acreate_vectorstore") as mock_acreate:
            mock_vectorstore = Mock(spec=VectorStore)
            mock_acreate.return_value = mock_vectorstore

            manager = await VectorStoreManager.acreate(
                "memory", mock_embeddings, persist_directory="/tmp"
            )

            mock_acreate.assert_called_once_with(
                "memory", mock_embeddings, persist_directory="/tmp"
            )
            assert isinstance(manager, VectorStoreManager)
            assert manager.vectorstore == mock_vectorstore


class TestVectorStoreManagerAddTexts:
    """Test add_texts functionality."""

    @pytest.mark.asyncio
    async def test_add_texts_success(self, manager, mock_vectorstore):
        """Test successful text addition."""
        texts = ["Hello world", "Python is great"]
        metadatas = [{"source": "test1"}, {"source": "test2"}]
        ids = ["id1", "id2"]

        result = await manager.add_texts(texts, metadatas, ids)

        mock_vectorstore.aadd_texts.assert_called_once_with(
            texts=texts, metadatas=metadatas, ids=ids
        )
        assert result == ["id1", "id2"]

    @pytest.mark.asyncio
    async def test_add_texts_without_metadata(self, manager, mock_vectorstore):
        """Test text addition without metadata."""
        texts = ["Simple text"]

        result = await manager.add_texts(texts)

        mock_vectorstore.aadd_texts.assert_called_once_with(
            texts=texts, metadatas=None, ids=None
        )
        assert result == ["id1", "id2"]

    @pytest.mark.asyncio
    async def test_add_texts_error_wrapped(self, manager, mock_vectorstore):
        """Test that add_texts errors are wrapped in VectorStoreError."""
        mock_vectorstore.aadd_texts.side_effect = Exception("Connection failed")

        with pytest.raises(VectorStoreError) as exc_info:
            await manager.add_texts(["test"])

        assert "Failed to add texts" in str(exc_info.value)
        assert exc_info.value.backend == "MockVectorStore"


class TestVectorStoreManagerAddDocuments:
    """Test add_documents functionality."""

    @pytest.mark.asyncio
    async def test_add_documents_success(self, manager, mock_vectorstore):
        """Test successful document addition."""
        documents = [
            Document(page_content="Doc 1", metadata={"source": "test1"}),
            Document(page_content="Doc 2", metadata={"source": "test2"}),
        ]

        result = await manager.add_documents(documents)

        mock_vectorstore.aadd_documents.assert_called_once_with(documents)
        assert result == ["doc1", "doc2"]

    @pytest.mark.asyncio
    async def test_add_documents_error_wrapped(self, manager, mock_vectorstore):
        """Test that add_documents errors are wrapped in VectorStoreError."""
        mock_vectorstore.aadd_documents.side_effect = Exception("Storage full")

        with pytest.raises(VectorStoreError) as exc_info:
            await manager.add_documents([])

        assert "Failed to add documents" in str(exc_info.value)
        assert exc_info.value.backend == "MockVectorStore"


class TestVectorStoreManagerSimilaritySearch:
    """Test similarity search functionality."""

    @pytest.mark.asyncio
    async def test_similarity_search_success(self, manager, mock_vectorstore):
        """Test successful similarity search."""
        query = "test query"
        k = 5
        filter_dict = {"source": "test"}

        result = await manager.similarity_search(
            query, k, filter_dict, extra_param="value"
        )

        # Verify the call was made with correct parameters
        call_args = mock_vectorstore.asimilarity_search.call_args
        assert call_args.kwargs["query"] == query
        assert call_args.kwargs["k"] == k
        assert call_args.kwargs["extra_param"] == "value"
        # For non-InMemory backends, filter dict should be passed through; for InMemory, it's converted to callable
        passed_filter = call_args.kwargs["filter"]
        assert callable(passed_filter) or passed_filter == filter_dict

        assert len(result) == 1
        assert isinstance(result[0], Document)
        assert result[0].page_content == "Test content"

    @pytest.mark.asyncio
    async def test_similarity_search_defaults(self, manager, mock_vectorstore):
        """Test similarity search with default parameters."""
        result = await manager.similarity_search("test query")

        mock_vectorstore.asimilarity_search.assert_called_once_with(
            query="test query", k=4, filter=None
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_similarity_search_error_wrapped(self, manager, mock_vectorstore):
        """Test that search errors are wrapped in VectorStoreError."""
        mock_vectorstore.asimilarity_search.side_effect = Exception("Search failed")

        with pytest.raises(VectorStoreError) as exc_info:
            await manager.similarity_search("test")

        assert "Search failed" in str(exc_info.value)
        assert exc_info.value.backend == "MockVectorStore"


class TestVectorStoreManagerSimilaritySearchWithScore:
    """Test similarity search with score functionality."""

    @pytest.mark.asyncio
    async def test_similarity_search_with_score_success(
        self, manager, mock_vectorstore
    ):
        """Test successful similarity search with scores."""
        result = await manager.similarity_search_with_score("test query", k=3)

        mock_vectorstore.asimilarity_search_with_score.assert_called_once_with(
            query="test query", k=3, filter=None
        )
        assert len(result) == 1
        doc, score = result[0]
        assert isinstance(doc, Document)
        assert doc.page_content == "Test content"
        assert score == 0.95

    @pytest.mark.asyncio
    async def test_similarity_search_with_score_error_wrapped(
        self, manager, mock_vectorstore
    ):
        """Test that search with score errors are wrapped in VectorStoreError."""
        mock_vectorstore.asimilarity_search_with_score.side_effect = Exception(
            "Score calculation failed"
        )

        with pytest.raises(VectorStoreError) as exc_info:
            await manager.similarity_search_with_score("test")

        assert "Search with score failed" in str(exc_info.value)
        assert exc_info.value.backend == "MockVectorStore"


class TestVectorStoreManagerBackendInfo:
    """Test backend info functionality."""

    def test_get_backend_info(self, manager, mock_vectorstore):
        """Test getting backend information."""
        info = manager.get_backend_info()

        expected = {"backend_type": "MockVectorStore", "backend_module": "test.mock"}
        assert info == expected

    def test_get_backend_info_with_real_vectorstore(self, mock_embeddings):
        """Test backend info with real InMemory vectorstore."""
        from momo_vector_store import create_vectorstore

        vectorstore = create_vectorstore("memory", mock_embeddings)
        manager = VectorStoreManager(vectorstore)

        info = manager.get_backend_info()

        assert info["backend_type"] == "InMemoryVectorStore"
        assert "langchain" in info["backend_module"]
