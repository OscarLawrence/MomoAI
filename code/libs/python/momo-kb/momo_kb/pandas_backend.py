"""Convenience functions for creating pandas document backends with different persistence strategies."""

from typing import Optional
from .stores.document.PandasDocumentStore import PandasDocumentBackend
from .stores.document.persistence import (
    PersistenceStrategy,
    NoPersistence,
    CSVPersistence,
    HDF5Persistence,
    DuckDBPersistence,
)


def create_pandas_backend(
    persistence_type: str = "memory", **persistence_kwargs
) -> PandasDocumentBackend:
    """
    Create a pandas document backend with specified persistence strategy.

    Args:
        persistence_type: Type of persistence ('memory', 'csv', 'hdf5', 'duckdb')
        **persistence_kwargs: Additional arguments for persistence strategy

    Returns:
        PandasDocumentBackend instance

    Examples:
        # In-memory only (no persistence)
        backend = create_pandas_backend()

        # CSV persistence
        backend = create_pandas_backend("csv", file_path="documents.csv")

        # HDF5 persistence
        backend = create_pandas_backend("hdf5", file_path="documents.h5")

        # DuckDB persistence
        backend = create_pandas_backend("duckdb", database_path="documents.db")
    """
    persistence_strategy: Optional[PersistenceStrategy] = None

    if persistence_type == "memory":
        persistence_strategy = NoPersistence()
    elif persistence_type == "csv":
        if "file_path" not in persistence_kwargs:
            raise ValueError("CSV persistence requires 'file_path' argument")
        persistence_strategy = CSVPersistence(persistence_kwargs["file_path"])
    elif persistence_type == "hdf5":
        if "file_path" not in persistence_kwargs:
            raise ValueError("HDF5 persistence requires 'file_path' argument")
        persistence_strategy = HDF5Persistence(persistence_kwargs["file_path"])
    elif persistence_type == "duckdb":
        database_path = persistence_kwargs.get("database_path", ":memory:")
        persistence_strategy = DuckDBPersistence(database_path)
    else:
        raise ValueError(f"Unknown persistence type: {persistence_type}")

    return PandasDocumentBackend(persistence_strategy)


def create_memory_backend() -> PandasDocumentBackend:
    """Create pandas backend with no persistence (in-memory only)."""
    return create_pandas_backend("memory")


def create_csv_backend(file_path: str) -> PandasDocumentBackend:
    """Create pandas backend with CSV persistence."""
    return create_pandas_backend("csv", file_path=file_path)


def create_hdf5_backend(file_path: str) -> PandasDocumentBackend:
    """Create pandas backend with HDF5 persistence."""
    return create_pandas_backend("hdf5", file_path=file_path)


def create_duckdb_backend(database_path: str = ":memory:") -> PandasDocumentBackend:
    """Create pandas backend with DuckDB persistence."""
    return create_pandas_backend("duckdb", database_path=database_path)
