"""
Basic setup tests for the Document Store architecture.
"""

import pytest
from momo_store_document import (
    PandasDocumentBackend,
    CSVPersistence,
    HDF5Persistence,
    DuckDBPersistence,
    NoPersistence,
)
from momo_store_document.main import BaseDocumentBackend
from momo_store_document.persistence import PersistenceStrategy
from momo_store_document.exceptions import KnowledgeBaseError


def test_imports():
    """Test that all expected imports work correctly."""
    assert PandasDocumentBackend is not None
    assert CSVPersistence is not None
    assert HDF5Persistence is not None
    assert DuckDBPersistence is not None
    assert NoPersistence is not None
    assert BaseDocumentBackend is not None
    assert PersistenceStrategy is not None
    assert KnowledgeBaseError is not None


def test_pandas_backend_instantiation():
    """Test that PandasDocumentBackend can be instantiated."""
    # With default (NoPersistence)
    backend = PandasDocumentBackend()
    assert backend is not None
    assert isinstance(backend.persistence, NoPersistence)

    # With CSV
    backend = PandasDocumentBackend(persistence_strategy=CSVPersistence("test.csv"))
    assert isinstance(backend.persistence, CSVPersistence)

    # With HDF5
    backend = PandasDocumentBackend(persistence_strategy=HDF5Persistence("test.h5"))
    assert isinstance(backend.persistence, HDF5Persistence)

    # With DuckDB
    backend = PandasDocumentBackend(persistence_strategy=DuckDBPersistence(":memory:"))
    assert isinstance(backend.persistence, DuckDBPersistence)


@pytest.mark.asyncio
async def test_async_methods_exist():
    """Test that all expected async methods exist on the backend."""
    backend = PandasDocumentBackend()

    methods = ["put", "get", "delete", "update", "list", "count", "search", "close"]
    for method in methods:
        assert hasattr(backend, method)
        assert callable(getattr(backend, method))


def test_sync_methods_exist():
    """Test that all expected sync wrapper methods exist on KnowledgeBase."""
    from momo_kb import KnowledgeBase

    kb = KnowledgeBase()

    # Sync wrapper methods
    assert hasattr(kb, "save_sync")
    assert hasattr(kb, "search_sync")
    assert hasattr(kb, "get_sync")
    assert hasattr(kb, "delete_sync")
    assert hasattr(kb, "update_sync")
    assert hasattr(kb, "list_documents_sync")
    assert hasattr(kb, "count_sync")

    # Check they are callable
    assert callable(getattr(kb, "save_sync"))
    assert callable(getattr(kb, "search_sync"))
    assert callable(getattr(kb, "get_sync"))
    assert callable(getattr(kb, "delete_sync"))
    assert callable(getattr(kb, "update_sync"))
    assert callable(getattr(kb, "list_documents_sync"))
    assert callable(getattr(kb, "count_sync"))


def test_context_manager_support():
    """Test that KnowledgeBase supports both sync and async context managers."""
    from momo_kb import KnowledgeBase

    kb = KnowledgeBase()

    # Async context manager methods
    assert hasattr(kb, "__aenter__")
    assert hasattr(kb, "__aexit__")

    # Sync context manager methods
    assert hasattr(kb, "__enter__")
    assert hasattr(kb, "__exit__")

    # Check they are callable
    assert callable(getattr(kb, "__aenter__"))
    assert callable(getattr(kb, "__aexit__"))
    assert callable(getattr(kb, "__enter__"))
    assert callable(getattr(kb, "__exit__"))


def test_backend_management_methods():
    """Test that backend management methods exist and are accessible."""
    from momo_kb import KnowledgeBase

    kb = KnowledgeBase()

    # Backend management methods (inherited from BaseKnowledgeBase)
    assert hasattr(kb, "set_vector_backend")
    assert hasattr(kb, "set_graph_backend")
    assert hasattr(kb, "set_document_backend")
    assert hasattr(kb, "get_backend_info")

    # Check they are callable
    assert callable(getattr(kb, "set_vector_backend"))
    assert callable(getattr(kb, "set_graph_backend"))
    assert callable(getattr(kb, "set_document_backend"))
    assert callable(getattr(kb, "get_backend_info"))


def test_inheritance_structure():
    """Test that the inheritance structure is as expected."""
    from momo_kb import KnowledgeBase, BaseKnowledgeBase, CoreKnowledgeBase

    kb = KnowledgeBase()

    # Should be instance of BaseKnowledgeBase
    assert isinstance(kb, BaseKnowledgeBase)
    assert isinstance(kb, CoreKnowledgeBase)

    # Should have the expected method resolution order on the actual class
    mro = CoreKnowledgeBase.__mro__
    assert BaseKnowledgeBase in mro
    assert len(mro) >= 2  # At least CoreKnowledgeBase and BaseKnowledgeBase


def test_document_creation():
    """Test that Document objects can be created as expected."""
    from momo_kb import Document, DocumentMetadata

    # Create a simple document
    metadata = DocumentMetadata(source="test", type="example", tags=["test", "basic"])

    doc = Document(content="This is a test document", metadata=metadata)

    assert doc.content == "This is a test document"
    assert doc.metadata.source == "test"
    assert doc.metadata.type == "example"
    assert "test" in doc.metadata.tags
    assert doc.id is not None  # Should auto-generate ID


def test_search_options_creation():
    """Test that SearchOptions can be created with various configurations."""
    from momo_kb import SearchOptions, QueryStrategy

    # Default options
    options1 = SearchOptions()
    assert options1.limit > 0
    assert options1.offset >= 0
    assert options1.threshold >= 0

    # Custom options
    options2 = SearchOptions(
        limit=50, offset=10, threshold=0.8, filters={"type": "example"}
    )
    assert options2.limit == 50
    assert options2.offset == 10
    assert options2.threshold == 0.8
    assert options2.filters["type"] == "example"
