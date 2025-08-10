"""
Unit tests for pandas document backends with different persistence strategies.

Tests the unified pandas-based approach with memory, CSV, HDF5, and DuckDB persistence.
"""

import pytest
import tempfile
import os
from typing import Dict, Any

from momo_store_document import (
    PandasDocumentBackend,
)
from momo_store_document.persistence import (
    NoPersistence,
    CSVPersistence,
    HDF5Persistence,
    DuckDBPersistence,
)


class TestPandasDocumentBackends:
    """Test pandas document backends with different persistence strategies."""

    @pytest.fixture
    def sample_document(self) -> Dict[str, Any]:
        """Create sample document data."""
        return {
            "content": "This is a test document",
            "metadata": {
                "type": "test",
                "category": "unit_test",
                "priority": 1,
                "tags": ["test", "document", "storage"],
            },
        }

    @pytest.mark.asyncio
    async def test_memory_backend(self, sample_document):
        """Test pandas backend with no persistence (memory only)."""
        backend = PandasDocumentBackend(NoPersistence())

        # Test put and get
        result = await backend.put("test_doc", sample_document)
        assert result is True

        retrieved = await backend.get("test_doc")
        assert retrieved is not None
        assert retrieved["content"] == sample_document["content"]
        assert retrieved["metadata"]["type"] == "test"

        # Test scan
        docs = await backend.scan()
        assert len(docs) == 1
        assert docs[0]["id"] == "test_doc"

    @pytest.mark.asyncio
    async def test_duckdb_backend(self, sample_document):
        """Test pandas backend with DuckDB persistence."""
        backend = PandasDocumentBackend(DuckDBPersistence(":memory:"))

        # Test put and get
        result = await backend.put("test_doc", sample_document)
        assert result is True

        retrieved = await backend.get("test_doc")
        assert retrieved is not None
        assert retrieved["content"] == sample_document["content"]
        assert retrieved["metadata"]["type"] == "test"

        # Test scan with filters
        docs = await backend.scan(filters={"type": "test"})
        assert len(docs) == 1

    @pytest.mark.asyncio
    async def test_csv_backend(self, sample_document):
        """Test pandas backend with CSV persistence."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
            csv_path = tmp_file.name

        try:
            backend = PandasDocumentBackend(CSVPersistence(csv_path))

            # Test put and get
            result = await backend.put("test_doc", sample_document)
            assert result is True

            retrieved = await backend.get("test_doc")
            assert retrieved is not None
            assert retrieved["content"] == sample_document["content"]

            # Close and reopen to test persistence
            await backend.close()

            backend2 = PandasDocumentBackend(CSVPersistence(csv_path))
            retrieved2 = await backend2.get("test_doc")
            assert retrieved2 is not None
            assert retrieved2["content"] == sample_document["content"]

        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)

    @pytest.mark.asyncio
    async def test_factory_integration(self):
        """Test that the factory creates the right backends."""
        from momo_kb.factory import create_document_backend

        # Test memory backend
        memory_backend = create_document_backend("memory")
        assert isinstance(memory_backend, PandasDocumentBackend)
        assert isinstance(memory_backend.persistence, NoPersistence)

        # Test DuckDB backend
        duckdb_backend = create_document_backend("duckdb")
        assert isinstance(duckdb_backend, PandasDocumentBackend)
        assert isinstance(duckdb_backend.persistence, DuckDBPersistence)
