"""Persistence strategy implementations for pandas document backend."""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from typing import Optional, Any, List
import pandas as pd

try:
    import duckdb
except ImportError:
    duckdb = None

from .exceptions import KnowledgeBaseError


class PersistenceStrategy(ABC):
    """Abstract base class for persistence strategies."""

    def __init__(self):
        self.enabled = True

    @abstractmethod
    async def load(self) -> pd.DataFrame:
        """Load data into pandas DataFrame."""
        pass

    @abstractmethod
    async def save(self, df: pd.DataFrame):
        """Save pandas DataFrame to persistence."""
        pass

    @abstractmethod
    def execute_query(self, query: str, query_type: str = "sql") -> Any:
        """Execute backend-specific queries. Returns query results or raises exception."""
        pass


class NoPersistence(PersistenceStrategy):
    """No persistence - data exists only in memory."""

    def __init__(self):
        super().__init__()
        self.enabled = False

    async def load(self) -> pd.DataFrame:
        """Return empty DataFrame."""
        return pd.DataFrame(
            columns=["id", "content", "created_at", "updated_at", "metadata"]
        )

    async def save(self, df: pd.DataFrame):
        """No-op."""
        pass

    def execute_query(self, query: str, query_type: str = "sql") -> Any:
        """Not supported."""
        raise KnowledgeBaseError(
            "No persistence backend configured for query execution"
        )


class CSVPersistence(PersistenceStrategy):
    """CSV persistence strategy."""

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    async def load(self) -> pd.DataFrame:
        """Load DataFrame from CSV file."""
        try:
            df = await asyncio.get_event_loop().run_in_executor(None, self._load_sync)
            return df
        except Exception:
            # Return empty DataFrame if file doesn't exist or is corrupted
            return pd.DataFrame(
                columns=["id", "content", "created_at", "updated_at", "metadata"]
            )

    def _load_sync(self) -> pd.DataFrame:
        """Synchronous CSV loading."""
        try:
            df = pd.read_csv(self.file_path)
            # Parse metadata JSON column
            if "metadata" in df.columns:
                df["metadata"] = df["metadata"].apply(
                    lambda x: json.loads(x) if pd.notnull(x) and x else {}
                )
            return df
        except FileNotFoundError:
            return pd.DataFrame(
                columns=["id", "content", "created_at", "updated_at", "metadata"]
            )

    async def save(self, df: pd.DataFrame):
        """Save DataFrame to CSV file."""
        try:
            await asyncio.get_event_loop().run_in_executor(None, self._save_sync, df)
        except Exception as e:
            raise KnowledgeBaseError(
                f"Failed to save to CSV {self.file_path}: {e}"
            ) from e

    def _save_sync(self, df: pd.DataFrame):
        """Synchronous CSV saving."""
        # Prepare DataFrame for CSV export
        export_df = df.copy()

        # Convert metadata dict to JSON string for CSV storage
        export_df["metadata"] = export_df["metadata"].apply(
            lambda x: json.dumps(x) if x else ""
        )

        # Reset index to include id as column
        export_df.reset_index(drop=True, inplace=True)
        export_df.to_csv(self.file_path, index=False)

    def execute_query(self, query: str, query_type: str = "sql") -> Any:
        """CSV doesn't support complex queries."""
        raise KnowledgeBaseError("CSV persistence does not support complex queries")


class HDF5Persistence(PersistenceStrategy):
    """HDF5 persistence strategy with compression."""

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    async def load(self) -> pd.DataFrame:
        """Load DataFrame from HDF5 file."""
        try:
            df = await asyncio.get_event_loop().run_in_executor(None, self._load_sync)
            return df
        except Exception:
            # Return empty DataFrame if file doesn't exist or is corrupted
            return pd.DataFrame(
                columns=["id", "content", "created_at", "updated_at", "metadata"]
            )

    def _load_sync(self) -> pd.DataFrame:
        """Synchronous HDF5 loading."""
        try:
            with pd.HDFStore(self.file_path, mode="r") as store:
                if "/documents" in store:
                    df_result = store["/documents"]
                    # Parse metadata JSON column
                    if "metadata" in df_result.columns:
                        df_result["metadata"] = df_result["metadata"].apply(
                            lambda x: json.loads(x) if pd.notnull(x) and x else {}
                        )
                    return df_result
                else:
                    return pd.DataFrame(
                        columns=[
                            "id",
                            "content",
                            "created_at",
                            "updated_at",
                            "metadata",
                        ]
                    )
        except FileNotFoundError:
            return pd.DataFrame(
                columns=["id", "content", "created_at", "updated_at", "metadata"]
            )

    async def save(self, df: pd.DataFrame):
        """Save DataFrame to HDF5 file."""
        try:
            await asyncio.get_event_loop().run_in_executor(None, self._save_sync, df)
        except Exception as e:
            raise KnowledgeBaseError(
                f"Failed to save to HDF5 {self.file_path}: {e}"
            ) from e

    def _save_sync(self, df: pd.DataFrame):
        """Synchronous HDF5 saving."""
        export_df = df.copy()

        # For HDF5 table format, serialize metadata to JSON
        export_df["metadata"] = export_df["metadata"].apply(
            lambda x: json.dumps(x) if x else ""
        )

        # Reset index to include id as column
        export_df.reset_index(drop=True, inplace=True)

        # Use pandas HDFStore for efficient storage with compression
        with pd.HDFStore(
            self.file_path, mode="w", complevel=9, complib="blosc"
        ) as store:
            store.put("/documents", export_df, format="table", data_columns=True)

    def execute_query(self, query: str, query_type: str = "sql") -> Any:
        """HDF5 doesn't support complex queries."""
        raise KnowledgeBaseError("HDF5 persistence does not support complex queries")


class DuckDBPersistence(PersistenceStrategy):
    """DuckDB persistence strategy with complex query support."""

    def __init__(self, database_path: str = ":memory:"):
        super().__init__()
        self.database_path = database_path
        self._connection = None

    def _get_connection(self):
        """Get or create DuckDB connection."""
        if self._connection is None:
            if duckdb is None:
                raise KnowledgeBaseError(
                    "DuckDB is not installed. Please install with: pip install duckdb"
                )

            # If file exists but is not a valid DuckDB database, remove it
            if self.database_path != ":memory:" and os.path.exists(self.database_path):
                try:
                    # Try to connect to see if it's a valid DuckDB database
                    temp_conn = duckdb.connect(self.database_path)
                    temp_conn.close()
                except Exception:
                    # Not a valid DuckDB database, remove it
                    os.remove(self.database_path)

            self._connection = duckdb.connect(self.database_path)
            # Initialize the documents table
            self._initialize_table()
        return self._connection

    def _initialize_table(self):
        """Initialize the documents table."""
        if self._connection is None:
            raise KnowledgeBaseError("DuckDB connection not established")

        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR PRIMARY KEY,
                content TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                metadata JSON
            )
        """
        )

    async def load(self) -> pd.DataFrame:
        """Load DataFrame from DuckDB."""
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, self._load_sync)
            return df
        except Exception:
            return pd.DataFrame(
                columns=["id", "content", "created_at", "updated_at", "metadata"]
            )

    def _load_sync(self) -> pd.DataFrame:
        """Synchronous DuckDB loading."""
        try:
            conn = self._get_connection()
            result = conn.execute("SELECT * FROM documents").fetchdf()

            if not result.empty:
                # Parse metadata JSON column
                if "metadata" in result.columns:
                    result["metadata"] = result["metadata"].apply(
                        lambda x: json.loads(x)
                        if pd.notnull(x) and x and x != "{}"
                        else {}
                    )
                return result
            else:
                return pd.DataFrame(
                    columns=["id", "content", "created_at", "updated_at", "metadata"]
                )
        except Exception:
            return pd.DataFrame(
                columns=["id", "content", "created_at", "updated_at", "metadata"]
            )

    async def save(self, df: pd.DataFrame):
        """Save DataFrame to DuckDB."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._save_sync, df)
        except Exception as e:
            raise KnowledgeBaseError(
                f"Failed to save to DuckDB {self.database_path}: {e}"
            ) from e

    def _save_sync(self, df: pd.DataFrame):
        """Synchronous DuckDB saving."""
        # Convert metadata to JSON strings for storage
        export_df = df.copy()

        # Handle the case where df might have id as index
        if "id" not in export_df.columns and export_df.index.name == "id":
            export_df = export_df.reset_index()

        export_df["metadata"] = export_df["metadata"].apply(
            lambda x: json.dumps(x) if x else "{}"
        )

        conn = self._get_connection()

        # Clear existing data and insert new data
        conn.execute("DELETE FROM documents")

        # Use DuckDB's register to insert the dataframe
        conn.register("temp_df", export_df)
        conn.execute(
            """
            INSERT INTO documents (id, content, created_at, updated_at, metadata)
            SELECT id, content, created_at, updated_at, metadata FROM temp_df
        """
        )
        conn.unregister("temp_df")

    def execute_query(self, query: str, query_type: str = "sql") -> List[Any]:
        """Execute complex SQL queries."""
        if query_type != "sql":
            raise KnowledgeBaseError(f"Unsupported query type: {query_type}")

        try:
            conn = self._get_connection()
            result = conn.execute(query).fetchall()
            return result
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to execute query: {e}") from e

    def close(self):
        """Close the DuckDB connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
