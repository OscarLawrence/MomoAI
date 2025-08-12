"""Pandas document backend implementation with pluggable persistence."""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from functools import lru_cache
import pandas as pd

from .main import BaseDocumentBackend
from .persistence import PersistenceStrategy, NoPersistence
from .exceptions import KnowledgeBaseError
from momo_logger import get_logger


class DocumentCache:
    """Simple LRU cache for frequently accessed documents."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: List[str] = []
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get document from cache."""
        if key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key].copy()
        return None
    
    def put(self, key: str, value: Dict[str, Any]) -> None:
        """Put document in cache."""
        if key in self._cache:
            # Update existing
            self._cache[key] = value.copy()
            self._access_order.remove(key)
            self._access_order.append(key)
        else:
            # Add new
            if len(self._cache) >= self.max_size:
                # Remove least recently used
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
            
            self._cache[key] = value.copy()
            self._access_order.append(key)
    
    def invalidate(self, key: str) -> None:
        """Remove document from cache."""
        if key in self._cache:
            del self._cache[key]
            self._access_order.remove(key)
    
    def clear(self) -> None:
        """Clear all cached documents."""
        self._cache.clear()
        self._access_order.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class PandasDocumentBackend(BaseDocumentBackend):
    """
    Unified pandas-based document storage backend with pluggable persistence.

    Uses pandas DataFrame as the central in-memory representation for all
    document operations, with optional pluggable persistence strategies.

    Excels at:
    - Complex data analysis and aggregations
    - Statistical operations across document collections
    - Time-series analysis of document metadata
    - Advanced filtering with pandas query syntax
    - Integration with data science workflows
    - High-performance columnar operations

    Features:
    - Always in-memory pandas DataFrame for fast operations
    - Pluggable persistence strategies (CSV, HDF5, DuckDB, etc.)
    - Hybrid querying (pandas filtering + backend-specific queries)
    - Rich metadata support with nested structures
    - Statistical analysis functions
    - Integration with pandas ecosystem
    - Memory-efficient columnar storage
    """

    def __init__(self, persistence_strategy: Optional[PersistenceStrategy] = None, cache_size: int = 1000):
        """
        Initialize pandas document backend.

        Args:
            persistence_strategy: Optional persistence strategy implementation
            cache_size: Maximum number of documents to cache (0 to disable caching)
        """
        self.persistence = persistence_strategy or NoPersistence()
        self._df: pd.DataFrame = pd.DataFrame()
        # Initialize in async context
        self._initialized = False
        # Initialize cache
        self._cache = DocumentCache(cache_size) if cache_size > 0 else None

    async def _initialize_dataframe(self):
        """Initialize the pandas DataFrame."""
        if self._initialized:
            return

        try:
            # Load existing data if persistence is enabled
            if self.persistence.enabled:
                self._df = await self.persistence.load()
            else:
                # Create empty DataFrame with required schema
                self._df = self._create_empty_dataframe()
        except Exception:
            # If there's any issue loading, just create empty DataFrame
            self._df = self._create_empty_dataframe()

        # Ensure proper data types
        if not self._df.empty:
            self._df["created_at"] = pd.to_datetime(
                self._df["created_at"], errors="coerce"
            )
            self._df["updated_at"] = pd.to_datetime(
                self._df["updated_at"], errors="coerce"
            )

        # Set id as index for efficient lookups
        if not self._df.empty and "id" in self._df.columns:
            self._df.set_index("id", inplace=True, drop=False)

        self._initialized = True

    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create an empty DataFrame with the required schema."""
        return pd.DataFrame(
            columns=["id", "content", "created_at", "updated_at", "metadata"]
        )

    async def put(self, key: str, value: Dict[str, Any]) -> bool:
        """Store document data."""
        await self._initialize_dataframe()
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._put_sync, key, value)
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to store document {key}: {e}") from e

    def _put_sync(self, key: str, value: Dict[str, Any]) -> bool:
        """Synchronous put operation."""
        content = value.get("content", "")
        metadata = value.get("metadata", {})
        created_at = value.get("created_at")
        updated_at = datetime.now()

        # Parse created_at if it's a string
        if created_at and isinstance(created_at, str):
            try:
                created_at = pd.to_datetime(created_at)
            except:
                created_at = None

        # If created_at not provided and document exists, preserve original
        if created_at is None and key in self._df.index:
            created_at = self._df.loc[key, "created_at"]
        elif created_at is None:
            created_at = updated_at

        # Create new row data
        new_row = {
            "id": key,
            "content": content,
            "created_at": created_at,
            "updated_at": updated_at,
            "metadata": metadata,
        }

        # Update existing document or add new one
        if key in self._df.index:
            # Update existing row - need to handle each column carefully
            self._df.at[key, "content"] = new_row["content"]
            self._df.at[key, "created_at"] = new_row["created_at"]
            self._df.at[key, "updated_at"] = new_row["updated_at"]
            self._df.at[key, "metadata"] = new_row["metadata"]
        else:
            # Add new row - use pd.concat for better performance
            # Handle empty DataFrame case to avoid deprecation warning
            if self._df.empty:
                self._df = pd.DataFrame([new_row])
                self._df.set_index("id", inplace=True, drop=False)
            else:
                new_df = pd.DataFrame([new_row])
                new_df.set_index("id", inplace=True, drop=False)
                self._df = pd.concat([self._df, new_df])

        # Persist if strategy is enabled
        if self.persistence.enabled:
            import asyncio

            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we can't await, so we'll do it synchronously
                    loop.run_until_complete(self.persistence.save(self._df))
                else:
                    # No event loop running, create a new one
                    asyncio.run(self.persistence.save(self._df))
            except RuntimeError:
                # No event loop in current thread, create a new one
                asyncio.run(self.persistence.save(self._df))

        # Invalidate cache for this document
        if self._cache:
            self._cache.invalidate(key)

        return True

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve document data by key with caching."""
        # Check cache first
        if self._cache:
            cached_result = self._cache.get(key)
            if cached_result is not None:
                return cached_result
        
        await self._initialize_dataframe()
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_sync, key)
            
            # Cache the result if caching is enabled
            if result is not None and self._cache:
                self._cache.put(key, result)
            
            return result
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to retrieve document {key}: {e}") from e

    def _get_sync(self, key: str) -> Optional[Dict[str, Any]]:
        """Synchronous get operation."""
        if key not in self._df.index:
            return None

        row = self._df.loc[key]
        if isinstance(row, pd.Series):
            return self._row_to_dict(key, row)
        else:
            # This shouldn't happen with single key lookup, but handle it
            return self._row_to_dict(key, row.iloc[0])

    async def delete(self, key: str) -> bool:
        """Delete document data."""
        await self._initialize_dataframe()
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._delete_sync, key)
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to delete document {key}: {e}") from e

    def _delete_sync(self, key: str) -> bool:
        """Synchronous delete operation."""
        if key not in self._df.index:
            return False

        self._df.drop(key, inplace=True)

        # Persist if strategy is enabled
        if self.persistence.enabled:
            import asyncio

            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we can't await, so we'll do it synchronously
                    loop.run_until_complete(self.persistence.save(self._df))
                else:
                    # No event loop running, create a new one
                    asyncio.run(self.persistence.save(self._df))
            except RuntimeError:
                # No event loop in current thread, create a new one
                asyncio.run(self.persistence.save(self._df))

        # Invalidate cache for this document
        if self._cache:
            self._cache.invalidate(key)

        return True

    async def scan(
        self, pattern: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Scan for matching documents using optimized query pushdown when possible."""
        await self._initialize_dataframe()
        try:
            # Try optimized query pushdown for DuckDB backend
            if hasattr(self.persistence, '_get_connection') and filters:
                return await self._scan_optimized(pattern, filters)
            else:
                # Fall back to pandas filtering
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self._scan_sync, pattern, filters)
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to scan documents: {e}") from e

    async def _scan_optimized(
        self, pattern: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Optimized scan using query pushdown to DuckDB."""
        try:
            # Build WHERE clause for DuckDB
            where_conditions = []
            
            # Add pattern matching to WHERE clause
            if pattern:
                pattern_escaped = pattern.replace("'", "''")  # Escape single quotes
                where_conditions.append(
                    f"(LOWER(id) LIKE LOWER('%{pattern_escaped}%') OR LOWER(content) LIKE LOWER('%{pattern_escaped}%'))"
                )
            
            # Add metadata filters to WHERE clause
            if filters:
                for key, value in filters.items():
                    if key in ["created_at", "updated_at"]:
                        # Handle timestamp filters
                        if isinstance(value, str):
                            where_conditions.append(f"{key} = '{value}'")
                        else:
                            where_conditions.append(f"{key} = '{value.isoformat()}'")
                    else:
                        # Handle metadata filters using JSON extraction
                        if isinstance(value, str):
                            value_escaped = value.replace("'", "''")
                            where_conditions.append(f"JSON_EXTRACT_STRING(metadata, '$.{key}') = '{value_escaped}'")
                        else:
                            where_conditions.append(f"JSON_EXTRACT_STRING(metadata, '$.{key}') = '{value}'")
            
            # Build complete WHERE clause
            where_clause = " AND ".join(where_conditions) if where_conditions else None
            
            # Load filtered data directly from DuckDB
            filtered_df = await self.persistence.load(where_clause=where_clause)
            
            # Sort by created_at descending (newest first)
            if not filtered_df.empty and "created_at" in filtered_df.columns:
                filtered_df = filtered_df.sort_values("created_at", ascending=False)
            
            # Convert to list of dictionaries
            results = []
            for idx, row in filtered_df.iterrows():
                results.append(self._row_to_dict(str(row["id"]), row))
            
            return results
            
        except Exception as e:
            # Fall back to pandas filtering if query pushdown fails
            get_logger("momo.store.document").warning(f"Query pushdown failed, falling back to pandas: {e}")
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._scan_sync, pattern, filters)

    def _scan_sync(
        self, pattern: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Synchronous scan operation using pandas filtering."""
        if self._df.empty:
            return []

        # Start with all documents
        mask = pd.Series([True] * len(self._df), index=self._df.index)

        # Apply pattern matching
        if pattern:
            pattern_lower = pattern.lower()
            # Search in both id and content columns
            id_matches = (
                self._df["id"].str.lower().str.contains(pattern_lower, na=False)
            )
            content_matches = (
                self._df["content"].str.lower().str.contains(pattern_lower, na=False)
            )
            pattern_mask = id_matches | content_matches
            mask = mask & pattern_mask

        # Apply metadata filters
        if filters:
            for key, value in filters.items():
                if key in ["created_at", "updated_at"]:
                    # Handle timestamp filters
                    if isinstance(value, str):
                        try:
                            value = pd.to_datetime(value)
                        except:
                            continue
                    filter_mask = self._df[key] == value
                else:
                    # Handle metadata filters
                    filter_mask = self._df["metadata"].apply(
                        lambda x: x.get(key) == value if isinstance(x, dict) else False
                    )
                mask = mask & filter_mask

        # Apply mask and convert to results
        filtered_df = self._df[mask]

        # Sort by created_at descending (newest first)
        if not filtered_df.empty:
            filtered_df = filtered_df.sort_values("created_at", ascending=False)

        # Convert to list of dictionaries
        results = []
        for idx, row in filtered_df.iterrows():
            results.append(self._row_to_dict(str(idx), row))

        return results

    def _row_to_dict(self, key: str, row: pd.Series) -> Dict[str, Any]:
        """Convert pandas row to dictionary."""
        metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}

        created_at = row["created_at"]
        updated_at = row["updated_at"]

        # Convert timestamps to ISO format strings
        if pd.notnull(created_at):
            created_at = created_at.isoformat()
        else:
            created_at = None

        if pd.notnull(updated_at):
            updated_at = updated_at.isoformat()
        else:
            updated_at = None

        return {
            "key": key,
            "id": key,
            "content": row["content"] if pd.notnull(row["content"]) else "",
            "created_at": created_at,
            "updated_at": updated_at,
            "metadata": metadata,
        }

    async def close(self):
        """Close backend and save if persistence is enabled."""
        if self.persistence.enabled:
            try:
                await self.persistence.save(self._df)
            except KnowledgeBaseError:
                # If save fails, just ignore on close
                pass

    # Additional pandas-specific methods for advanced analytics

    def get_dataframe(self) -> pd.DataFrame:
        """Get direct access to underlying DataFrame for advanced operations."""
        return self._df.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistical summary of the document collection."""
        if self._df.empty:
            return {"total_documents": 0}

        stats = {
            "total_documents": len(self._df),
            "content_length_stats": self._df["content"].str.len().describe().to_dict(),
            "creation_date_range": {
                "earliest": (
                    self._df["created_at"].min().isoformat()
                    if pd.notnull(self._df["created_at"].min())
                    else None
                ),
                "latest": (
                    self._df["created_at"].max().isoformat()
                    if pd.notnull(self._df["created_at"].max())
                    else None
                ),
            },
            "memory_usage_mb": self._df.memory_usage(deep=True).sum() / 1024 / 1024,
        }

        return stats

    def query(self, query_expr: str) -> List[Dict[str, Any]]:
        """Execute pandas query expression and return matching documents."""
        try:
            filtered_df = self._df.query(query_expr)
            results = []
            for idx, row in filtered_df.iterrows():
                results.append(self._row_to_dict(str(idx), row))
            return results
        except Exception as e:
            raise KnowledgeBaseError(
                f"Failed to execute query '{query_expr}': {e}"
            ) from e

    def execute_backend_query(self, query: str, query_type: str = "sql"):
        """Execute backend-specific complex queries."""
        return self.persistence.execute_query(query, query_type)


# Convenience factory functions


def create_pandas_with_duckdb(
    database_path: str = "documents.db",
) -> PandasDocumentBackend:
    """
    Create a PandasDocumentBackend with DuckDB persistence.

    This is the recommended production configuration.

    Args:
        database_path: Path to the DuckDB database file

    Returns:
        PandasDocumentBackend configured with DuckDB persistence
    """
    from .persistence import DuckDBPersistence

    return PandasDocumentBackend(persistence_strategy=DuckDBPersistence(database_path))


def create_pandas_inmemory() -> PandasDocumentBackend:
    """
    Create a PandasDocumentBackend with no persistence (in-memory only).

    This is suitable for development and testing.

    Returns:
        PandasDocumentBackend with no persistence
    """
    from .persistence import NoPersistence

    return PandasDocumentBackend(persistence_strategy=NoPersistence())
