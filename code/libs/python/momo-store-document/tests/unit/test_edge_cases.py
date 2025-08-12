"""
Edge case tests for comprehensive coverage.

Tests error conditions, boundary cases, and unusual scenarios.
"""

import pytest
import tempfile
import os
import asyncio
import json
from unittest.mock import Mock, patch
import pandas as pd

from momo_store_document.PandasDocumentStore import PandasDocumentBackend, DocumentCache
from momo_store_document.persistence import (
    DuckDBPersistence, NoPersistence, CSVPersistence, HDF5Persistence
)
from momo_store_document.exceptions import KnowledgeBaseError


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_document_handling(self):
        """Test handling of empty and minimal documents."""
        backend = PandasDocumentBackend()
        
        # Test empty content
        await backend.put("empty", {"content": "", "metadata": {}})
        result = await backend.get("empty")
        assert result is not None
        assert result["content"] == ""
        
        # Test None content
        await backend.put("none_content", {"content": None, "metadata": {}})
        result = await backend.get("none_content")
        assert result is not None
        assert result["content"] == ""  # Should be converted to empty string
        
        # Test missing content
        await backend.put("no_content", {"metadata": {"type": "test"}})
        result = await backend.get("no_content")
        assert result is not None
        assert result["content"] == ""
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_large_document_handling(self):
        """Test handling of very large documents."""
        backend = PandasDocumentBackend()
        
        # Create a large document (1MB of text)
        large_content = "A" * (1024 * 1024)
        large_doc = {
            "content": large_content,
            "metadata": {"type": "large", "size": len(large_content)}
        }
        
        await backend.put("large_doc", large_doc)
        result = await backend.get("large_doc")
        
        assert result is not None
        assert len(result["content"]) == 1024 * 1024
        assert result["metadata"]["type"] == "large"
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_special_characters_in_content(self):
        """Test handling of special characters and unicode."""
        backend = PandasDocumentBackend()
        
        special_docs = [
            ("unicode", {"content": "Hello 世界 🌍 émojis", "metadata": {}}),
            ("quotes", {"content": "Text with 'single' and \"double\" quotes", "metadata": {}}),
            ("newlines", {"content": "Line 1\nLine 2\r\nLine 3", "metadata": {}}),
            ("json_like", {"content": '{"key": "value", "array": [1,2,3]}', "metadata": {}}),
            ("sql_injection", {"content": "'; DROP TABLE documents; --", "metadata": {}}),
        ]
        
        for doc_id, doc in special_docs:
            await backend.put(doc_id, doc)
            result = await backend.get(doc_id)
            assert result is not None
            assert result["content"] == doc["content"]
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_complex_metadata_structures(self):
        """Test handling of complex nested metadata."""
        backend = PandasDocumentBackend()
        
        complex_metadata = {
            "nested": {
                "level1": {
                    "level2": {
                        "value": "deep_value"
                    }
                }
            },
            "arrays": [1, 2, 3, {"nested_in_array": True}],
            "mixed_types": {
                "string": "text",
                "number": 42,
                "float": 3.14,
                "boolean": True,
                "null": None,
                "empty_list": [],
                "empty_dict": {}
            }
        }
        
        await backend.put("complex", {"content": "test", "metadata": complex_metadata})
        result = await backend.get("complex")
        
        assert result is not None
        assert result["metadata"]["nested"]["level1"]["level2"]["value"] == "deep_value"
        assert result["metadata"]["arrays"][3]["nested_in_array"] is True
        assert result["metadata"]["mixed_types"]["number"] == 42
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent document operations."""
        backend = PandasDocumentBackend()
        
        # Create multiple concurrent put operations
        async def put_doc(i):
            await backend.put(f"doc_{i}", {"content": f"Content {i}", "metadata": {"id": i}})
        
        # Run 10 concurrent puts
        await asyncio.gather(*[put_doc(i) for i in range(10)])
        
        # Verify all documents were stored
        for i in range(10):
            result = await backend.get(f"doc_{i}")
            assert result is not None
            assert result["content"] == f"Content {i}"
        
        # Test concurrent gets
        async def get_doc(i):
            return await backend.get(f"doc_{i}")
        
        results = await asyncio.gather(*[get_doc(i) for i in range(10)])
        assert all(result is not None for result in results)
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_persistence_error_recovery(self):
        """Test error recovery in persistence layer."""
        # Test with invalid database path
        with pytest.raises(Exception):
            persistence = DuckDBPersistence("/invalid/readonly/path/test.db")
            backend = PandasDocumentBackend(persistence)
            await backend.put("test", {"content": "test"})

    def test_cache_with_invalid_operations(self):
        """Test cache behavior with invalid operations."""
        cache = DocumentCache(max_size=5)
        
        # Test with None values
        cache.put("test", None)
        result = cache.get("test")
        assert result is None  # Should handle None gracefully
        
        # Test with very large cache size
        large_cache = DocumentCache(max_size=1000000)
        for i in range(100):
            large_cache.put(f"doc_{i}", {"content": f"test {i}"})
        assert large_cache.size() == 100

    @pytest.mark.asyncio
    async def test_scan_with_invalid_filters(self):
        """Test scan operations with invalid or edge case filters."""
        backend = PandasDocumentBackend()
        
        # Add test documents
        await backend.put("doc1", {"content": "test", "metadata": {"type": "valid"}})
        
        # Test with None filters
        results = await backend.scan(filters=None)
        assert len(results) >= 1
        
        # Test with empty filters
        results = await backend.scan(filters={})
        assert len(results) >= 1
        
        # Test with non-existent filter keys
        results = await backend.scan(filters={"nonexistent_key": "value"})
        assert len(results) == 0
        
        # Test with None pattern
        results = await backend.scan(pattern=None)
        assert len(results) >= 1
        
        # Test with empty pattern
        results = await backend.scan(pattern="")
        assert len(results) >= 1
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_timestamp_edge_cases(self):
        """Test timestamp handling edge cases."""
        backend = PandasDocumentBackend()
        
        # Test with various timestamp formats
        timestamp_docs = [
            ("iso_format", {"content": "test", "created_at": "2024-01-01T12:00:00Z"}),
            ("date_only", {"content": "test", "created_at": "2024-01-01"}),
            ("invalid_date", {"content": "test", "created_at": "not-a-date"}),
            ("numeric_timestamp", {"content": "test", "created_at": 1704110400}),
        ]
        
        for doc_id, doc in timestamp_docs:
            await backend.put(doc_id, doc)
            result = await backend.get(doc_id)
            assert result is not None
            # Should have some created_at value (either parsed or auto-generated)
            assert "created_at" in result
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_memory_pressure_scenarios(self):
        """Test behavior under memory pressure."""
        # Test with very small cache
        backend = PandasDocumentBackend(cache_size=1)
        
        # Add more documents than cache can hold
        for i in range(10):
            await backend.put(f"doc_{i}", {"content": f"Content {i}"})
        
        # Cache should only hold 1 document
        assert backend._cache.size() <= 1
        
        # All documents should still be retrievable
        for i in range(10):
            result = await backend.get(f"doc_{i}")
            assert result is not None
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_database_corruption_recovery(self):
        """Test recovery from database corruption scenarios."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            # Create a valid database
            backend = PandasDocumentBackend(DuckDBPersistence(db_path))
            await backend.put("test", {"content": "test"})
            await backend.close()
            
            # Corrupt the database file
            with open(db_path, "w") as f:
                f.write("corrupted data")
            
            # Try to use the corrupted database
            backend2 = PandasDocumentBackend(DuckDBPersistence(db_path))
            # Should handle corruption gracefully and create new database
            await backend2.put("new_test", {"content": "new test"})
            result = await backend2.get("new_test")
            assert result is not None
            await backend2.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_persistence_strategy_edge_cases(self):
        """Test edge cases in different persistence strategies."""
        # Test CSV with special characters
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
            csv_path = tmp_file.name
        
        try:
            backend = PandasDocumentBackend(CSVPersistence(csv_path))
            
            # Test document with commas and quotes (CSV edge case)
            special_doc = {
                "content": 'Text with, commas and "quotes"',
                "metadata": {"description": "CSV, test with \"special\" chars"}
            }
            
            await backend.put("csv_test", special_doc)
            await backend.close()
            
            # Reload and verify
            backend2 = PandasDocumentBackend(CSVPersistence(csv_path))
            result = await backend2.get("csv_test")
            assert result is not None
            assert "commas" in result["content"]
            await backend2.close()
            
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)

    def test_document_cache_stress_test(self):
        """Stress test the document cache."""
        cache = DocumentCache(max_size=100)
        
        # Add many documents rapidly
        for i in range(1000):
            cache.put(f"doc_{i}", {"content": f"Content {i}", "id": i})
        
        # Cache should not exceed max size
        assert cache.size() <= 100
        
        # Most recent documents should still be in cache
        recent_doc = cache.get("doc_999")
        assert recent_doc is not None
        
        # Very old documents should be evicted
        old_doc = cache.get("doc_0")
        assert old_doc is None

    @pytest.mark.asyncio
    async def test_query_pushdown_sql_injection_protection(self):
        """Test that query pushdown protects against SQL injection."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            backend = PandasDocumentBackend(DuckDBPersistence(db_path))
            
            # Add test document
            await backend.put("test", {"content": "safe content", "metadata": {"type": "test"}})
            
            # Try SQL injection in pattern search
            malicious_pattern = "'; DROP TABLE documents; --"
            results = await backend.scan(pattern=malicious_pattern)
            
            # Should not crash and should return empty results (no match)
            assert isinstance(results, list)
            
            # Verify database is still intact
            normal_results = await backend.scan(filters={"type": "test"})
            assert len(normal_results) == 1
            
            await backend.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_backend_factory_functions(self):
        """Test the convenience factory functions."""
        from momo_store_document.PandasDocumentStore import (
            create_pandas_with_duckdb, create_pandas_inmemory
        )
        
        # Test in-memory factory
        memory_backend = create_pandas_inmemory()
        assert isinstance(memory_backend, PandasDocumentBackend)
        assert isinstance(memory_backend.persistence, NoPersistence)
        
        await memory_backend.put("test", {"content": "test"})
        result = await memory_backend.get("test")
        assert result is not None
        await memory_backend.close()
        
        # Test DuckDB factory
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            duckdb_backend = create_pandas_with_duckdb(db_path)
            assert isinstance(duckdb_backend, PandasDocumentBackend)
            assert isinstance(duckdb_backend.persistence, DuckDBPersistence)
            
            await duckdb_backend.put("test", {"content": "test"})
            result = await duckdb_backend.get("test")
            assert result is not None
            await duckdb_backend.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)