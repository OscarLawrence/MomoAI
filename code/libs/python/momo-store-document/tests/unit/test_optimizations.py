"""
Comprehensive tests for the optimization features.

Tests query pushdown, caching, and performance improvements.
"""

import pytest
import tempfile
import os
import asyncio
from typing import Dict, Any
import pandas as pd

from momo_store_document.PandasDocumentStore import PandasDocumentBackend, DocumentCache
from momo_store_document.persistence import DuckDBPersistence, NoPersistence


class TestDocumentCache:
    """Test the DocumentCache implementation."""

    def test_cache_initialization(self):
        """Test cache initialization with different sizes."""
        cache = DocumentCache(max_size=100)
        assert cache.max_size == 100
        assert cache.size() == 0

    def test_cache_put_get(self):
        """Test basic put and get operations."""
        cache = DocumentCache(max_size=3)
        
        # Test put and get
        doc = {"content": "test content", "metadata": {"type": "test"}}
        cache.put("doc1", doc)
        
        retrieved = cache.get("doc1")
        assert retrieved is not None
        assert retrieved["content"] == "test content"
        assert cache.size() == 1

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = DocumentCache(max_size=2)
        
        # Fill cache
        cache.put("doc1", {"content": "content1"})
        cache.put("doc2", {"content": "content2"})
        assert cache.size() == 2
        
        # Access doc1 to make it most recently used
        cache.get("doc1")
        
        # Add doc3, should evict doc2 (least recently used)
        cache.put("doc3", {"content": "content3"})
        assert cache.size() == 2
        assert cache.get("doc1") is not None  # Still in cache
        assert cache.get("doc2") is None      # Evicted
        assert cache.get("doc3") is not None  # Newly added

    def test_cache_update_existing(self):
        """Test updating existing cache entries."""
        cache = DocumentCache(max_size=3)
        
        # Add document
        cache.put("doc1", {"content": "original"})
        
        # Update document
        cache.put("doc1", {"content": "updated"})
        
        retrieved = cache.get("doc1")
        assert retrieved["content"] == "updated"
        assert cache.size() == 1  # Size shouldn't change

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        cache = DocumentCache(max_size=3)
        
        cache.put("doc1", {"content": "test"})
        assert cache.get("doc1") is not None
        
        cache.invalidate("doc1")
        assert cache.get("doc1") is None
        assert cache.size() == 0

    def test_cache_clear(self):
        """Test clearing the entire cache."""
        cache = DocumentCache(max_size=3)
        
        cache.put("doc1", {"content": "test1"})
        cache.put("doc2", {"content": "test2"})
        assert cache.size() == 2
        
        cache.clear()
        assert cache.size() == 0
        assert cache.get("doc1") is None
        assert cache.get("doc2") is None

    def test_cache_isolation(self):
        """Test that cached documents are isolated (deep copy)."""
        cache = DocumentCache(max_size=3)
        
        original = {"content": "test", "metadata": {"tags": ["tag1"]}}
        cache.put("doc1", original)
        
        # Modify original
        original["content"] = "modified"
        original["metadata"]["tags"].append("tag2")
        
        # Cached version should be unchanged
        cached = cache.get("doc1")
        assert cached["content"] == "test"
        assert cached["metadata"]["tags"] == ["tag1"]


class TestDuckDBOptimizations:
    """Test DuckDB query pushdown optimizations."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            yield tmp_file.name
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_query_pushdown_where_clause(self, temp_db_path):
        """Test query pushdown with WHERE clauses."""
        persistence = DuckDBPersistence(temp_db_path)
        
        # Create test data
        test_data = pd.DataFrame([
            {"id": "doc1", "content": "Python tutorial", "created_at": "2024-01-01", "updated_at": "2024-01-01", "metadata": '{"type": "tutorial", "language": "python"}'},
            {"id": "doc2", "content": "JavaScript guide", "created_at": "2024-01-02", "updated_at": "2024-01-02", "metadata": '{"type": "tutorial", "language": "javascript"}'},
            {"id": "doc3", "content": "Database design", "created_at": "2024-01-03", "updated_at": "2024-01-03", "metadata": '{"type": "reference", "topic": "database"}'},
        ])
        
        await persistence.save(test_data)
        
        # Test basic WHERE clause
        filtered = await persistence.load(where_clause="id = 'doc1'")
        assert len(filtered) == 1
        assert filtered.iloc[0]["id"] == "doc1"
        
        # Test JSON metadata filtering
        tutorials = await persistence.load(
            where_clause="JSON_EXTRACT_STRING(metadata, '$.type') = 'tutorial'"
        )
        assert len(tutorials) == 2
        
        # Test pattern matching
        python_docs = await persistence.load(
            where_clause="LOWER(content) LIKE '%python%'"
        )
        assert len(python_docs) == 1
        assert "python" in python_docs.iloc[0]["content"].lower()
        
        persistence.close()

    @pytest.mark.asyncio
    async def test_column_selection(self, temp_db_path):
        """Test lazy loading with column selection."""
        persistence = DuckDBPersistence(temp_db_path)
        
        # Create test data
        test_data = pd.DataFrame([
            {"id": "doc1", "content": "Content 1", "created_at": "2024-01-01", "updated_at": "2024-01-01", "metadata": '{"type": "test"}'},
            {"id": "doc2", "content": "Content 2", "created_at": "2024-01-02", "updated_at": "2024-01-02", "metadata": '{"type": "test"}'},
        ])
        
        await persistence.save(test_data)
        
        # Test loading specific columns
        id_content_only = await persistence.load(columns=["id", "content"])
        assert list(id_content_only.columns) == ["id", "content"]
        assert len(id_content_only) == 2
        
        # Test loading single column
        ids_only = await persistence.load(columns=["id"])
        assert list(ids_only.columns) == ["id"]
        assert len(ids_only) == 2
        
        persistence.close()

    @pytest.mark.asyncio
    async def test_combined_filtering_and_columns(self, temp_db_path):
        """Test combining WHERE clauses with column selection."""
        persistence = DuckDBPersistence(temp_db_path)
        
        # Create test data
        test_data = pd.DataFrame([
            {"id": "doc1", "content": "Python content", "created_at": "2024-01-01", "updated_at": "2024-01-01", "metadata": '{"type": "tutorial"}'},
            {"id": "doc2", "content": "Java content", "created_at": "2024-01-02", "updated_at": "2024-01-02", "metadata": '{"type": "tutorial"}'},
            {"id": "doc3", "content": "Python reference", "created_at": "2024-01-03", "updated_at": "2024-01-03", "metadata": '{"type": "reference"}'},
        ])
        
        await persistence.save(test_data)
        
        # Test combined optimization
        result = await persistence.load(
            where_clause="LOWER(content) LIKE '%python%'",
            columns=["id", "content"]
        )
        
        assert len(result) == 2  # Two Python documents
        assert list(result.columns) == ["id", "content"]
        assert all("python" in content.lower() for content in result["content"])
        
        persistence.close()


class TestPandasBackendOptimizations:
    """Test optimizations in PandasDocumentBackend."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
            yield tmp_file.name
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_caching_integration(self, temp_db_path):
        """Test caching integration in PandasDocumentBackend."""
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(temp_db_path),
            cache_size=10
        )
        
        # Add test document
        test_doc = {
            "content": "Test content",
            "metadata": {"type": "test", "priority": 1}
        }
        
        await backend.put("doc1", test_doc)
        
        # First get should load from persistence and cache
        result1 = await backend.get("doc1")
        assert result1 is not None
        assert result1["content"] == "Test content"
        
        # Second get should hit cache (we can't directly test this without timing)
        result2 = await backend.get("doc1")
        assert result2 is not None
        assert result2["content"] == "Test content"
        
        # Verify cache has the document
        assert backend._cache.size() == 1
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, temp_db_path):
        """Test that cache is invalidated when documents are updated."""
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(temp_db_path),
            cache_size=10
        )
        
        # Add and cache document
        await backend.put("doc1", {"content": "Original content"})
        await backend.get("doc1")  # Cache it
        assert backend._cache.size() == 1
        
        # Update document
        await backend.put("doc1", {"content": "Updated content"})
        
        # Cache should be invalidated, so next get loads fresh data
        result = await backend.get("doc1")
        assert result["content"] == "Updated content"
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_delete(self, temp_db_path):
        """Test that cache is invalidated when documents are deleted."""
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(temp_db_path),
            cache_size=10
        )
        
        # Add and cache document
        await backend.put("doc1", {"content": "Test content"})
        await backend.get("doc1")  # Cache it
        assert backend._cache.size() == 1
        
        # Delete document
        await backend.delete("doc1")
        
        # Document should be gone and cache should be empty
        result = await backend.get("doc1")
        assert result is None
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_optimized_scan_with_duckdb(self, temp_db_path):
        """Test optimized scan using query pushdown."""
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(temp_db_path)
        )
        
        # Add test documents
        test_docs = [
            {"content": "Python tutorial", "metadata": {"type": "tutorial", "language": "python"}},
            {"content": "JavaScript guide", "metadata": {"type": "tutorial", "language": "javascript"}},
            {"content": "Database reference", "metadata": {"type": "reference", "topic": "database"}},
        ]
        
        for i, doc in enumerate(test_docs):
            await backend.put(f"doc{i+1}", doc)
        
        # Test optimized scan with filters (should use query pushdown)
        results = await backend.scan(filters={"type": "tutorial"})
        assert len(results) == 2
        assert all(result["metadata"]["type"] == "tutorial" for result in results)
        
        # Test pattern search with optimization
        python_results = await backend.scan(pattern="Python")
        assert len(python_results) == 1
        assert "Python" in python_results[0]["content"]
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_fallback_to_pandas_filtering(self):
        """Test fallback to pandas filtering for non-DuckDB backends."""
        backend = PandasDocumentBackend(
            persistence_strategy=NoPersistence(),  # Memory backend
            cache_size=10
        )
        
        # Add test documents
        test_docs = [
            {"content": "Python tutorial", "metadata": {"type": "tutorial"}},
            {"content": "JavaScript guide", "metadata": {"type": "guide"}},
        ]
        
        for i, doc in enumerate(test_docs):
            await backend.put(f"doc{i+1}", doc)
        
        # Should fall back to pandas filtering
        results = await backend.scan(filters={"type": "tutorial"})
        assert len(results) == 1
        assert results[0]["metadata"]["type"] == "tutorial"
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_disabled_caching(self, temp_db_path):
        """Test backend with caching disabled."""
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(temp_db_path),
            cache_size=0  # Disable caching
        )
        
        assert backend._cache is None
        
        # Operations should still work without caching
        await backend.put("doc1", {"content": "Test content"})
        result = await backend.get("doc1")
        assert result is not None
        assert result["content"] == "Test content"
        
        await backend.close()


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_query_pushdown_fallback_on_error(self, temp_db_path):
        """Test fallback to pandas filtering when query pushdown fails."""
        backend = PandasDocumentBackend(
            persistence_strategy=DuckDBPersistence(temp_db_path)
        )
        
        # Add test document
        await backend.put("doc1", {"content": "Test", "metadata": {"type": "test"}})
        
        # Test with invalid SQL (should fallback to pandas)
        # This is hard to test directly, but we can test that scan still works
        results = await backend.scan(filters={"type": "test"})
        assert len(results) == 1
        
        await backend.close()

    def test_cache_edge_cases(self):
        """Test cache edge cases."""
        cache = DocumentCache(max_size=1)
        
        # Test getting non-existent key
        assert cache.get("nonexistent") is None
        
        # Test invalidating non-existent key
        cache.invalidate("nonexistent")  # Should not raise error
        
        # Test with zero-size cache
        zero_cache = DocumentCache(max_size=0)
        zero_cache.put("doc1", {"content": "test"})
        assert zero_cache.size() == 0  # Should not store anything

    @pytest.mark.asyncio
    async def test_persistence_error_handling(self):
        """Test error handling in persistence layer."""
        # Test with invalid database path
        persistence = DuckDBPersistence("/invalid/path/database.db")
        
        # Should handle errors gracefully
        try:
            await persistence.load()
        except Exception:
            pass  # Expected to fail, but shouldn't crash
        
        persistence.close()


class TestBackwardCompatibility:
    """Test that optimizations maintain backward compatibility."""

    @pytest.mark.asyncio
    async def test_existing_api_compatibility(self):
        """Test that existing API still works unchanged."""
        backend = PandasDocumentBackend()  # Default configuration
        
        # Test all existing methods work
        await backend.put("doc1", {"content": "Test", "metadata": {"type": "test"}})
        
        result = await backend.get("doc1")
        assert result is not None
        
        results = await backend.scan()
        assert len(results) == 1
        
        results = await backend.scan(pattern="Test")
        assert len(results) == 1
        
        results = await backend.scan(filters={"type": "test"})
        assert len(results) == 1
        
        deleted = await backend.delete("doc1")
        assert deleted is True
        
        await backend.close()

    @pytest.mark.asyncio
    async def test_persistence_backward_compatibility(self):
        """Test that persistence strategies maintain backward compatibility."""
        # Test that old load() method still works
        persistence = NoPersistence()
        
        # Should work without new parameters
        df = await persistence.load()
        assert isinstance(df, pd.DataFrame)
        
        # Should work with new parameters
        df = await persistence.load(where_clause=None, columns=None)
        assert isinstance(df, pd.DataFrame)