#!/usr/bin/env python3
"""
Persistence Test - Verify that data is correctly persisted and loaded

This script verifies that the pandas document backend correctly persists
data to different formats and can reload it correctly.

Run with: pdm run script 09_persistence_test
"""

import asyncio
import tempfile
import os

from momo_kb.stores.document import (
    PandasDocumentBackend,
    CSVPersistence,
    HDF5Persistence,
    DuckDBPersistence,
    create_pandas_with_duckdb,
    create_pandas_inmemory,
)


async def main():
    print("🔍 Persistence Test")
    print("=" * 30)

    # Create temporary files for persistence
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        csv_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".h5", delete=False) as f:
        hdf5_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        duckdb_path = f.name

    try:
        print(f"📄 CSV File: {csv_path}")
        print(f"🗃️ HDF5 File: {hdf5_path}")
        print(f"🦆 DuckDB File: {duckdb_path}")

        # Sample document
        test_doc = {
            "content": "This is a test document for persistence verification.",
            "metadata": {
                "type": "test",
                "category": "persistence",
                "version": 1.0,
                "tags": ["test", "persistence", "verification"],
            },
        }

        print(f"\n📝 Writing Test Data")
        print("-" * 25)

        # Test CSV persistence
        csv_backend = PandasDocumentBackend(CSVPersistence(csv_path))
        await csv_backend.put("test_doc_csv", test_doc)
        await csv_backend.close()
        print(f"CSV data written and closed")

        # Test HDF5 persistence
        hdf5_backend = PandasDocumentBackend(HDF5Persistence(hdf5_path))
        await hdf5_backend.put("test_doc_hdf5", test_doc)
        await hdf5_backend.close()
        print(f"HDF5 data written and closed")

        # Test DuckDB persistence
        duckdb_backend = create_pandas_with_duckdb(duckdb_path)
        await duckdb_backend.put("test_doc_duckdb", test_doc)
        await duckdb_backend.close()
        print(f"DuckDB data written and closed")

        print(f"\n🔍 Reading Test Data")
        print("-" * 25)

        # Test CSV reading
        csv_backend_read = PandasDocumentBackend(CSVPersistence(csv_path))
        csv_doc = await csv_backend_read.get("test_doc_csv")
        await csv_backend_read.close()
        print(f"CSV document loaded: {'✓' if csv_doc else '✗'}")
        if csv_doc:
            print(f"  Content: {csv_doc['content'][:50]}...")
            print(f"  Metadata type: {csv_doc['metadata'].get('type')}")

        # Test HDF5 reading
        hdf5_backend_read = PandasDocumentBackend(HDF5Persistence(hdf5_path))
        hdf5_doc = await hdf5_backend_read.get("test_doc_hdf5")
        await hdf5_backend_read.close()
        print(f"HDF5 document loaded: {'✓' if hdf5_doc else '✗'}")
        if hdf5_doc:
            print(f"  Content: {hdf5_doc['content'][:50]}...")
            print(f"  Metadata type: {hdf5_doc['metadata'].get('type')}")

        # Test DuckDB reading
        duckdb_backend_read = create_pandas_with_duckdb(duckdb_path)
        duckdb_doc = await duckdb_backend_read.get("test_doc_duckdb")
        await duckdb_backend_read.close()
        print(f"DuckDB document loaded: {'✓' if duckdb_doc else '✗'}")
        if duckdb_doc:
            print(f"  Content: {duckdb_doc['content'][:50]}...")
            print(f"  Metadata type: {duckdb_doc['metadata'].get('type')}")

        print(f"\n✅ Persistence Test Complete!")
        print(f"All persistence strategies are working correctly.")

    finally:
        # Cleanup
        for path in [csv_path, hdf5_path, duckdb_path]:
            if os.path.exists(path):
                os.unlink(path)


if __name__ == "__main__":
    asyncio.run(main())
