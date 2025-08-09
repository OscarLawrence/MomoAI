"""
HDF5 vs CSV Performance Benchmarks for PandasDocumentBackend.

Compares read/write performance between CSV and HDF5 persistence formats
to demonstrate the performance benefits of HDF5 for data science workflows.
"""

import asyncio
import pytest
import time
import tempfile
import os
from typing import Dict, Any, List

from momo_kb.stores.document.PandasDocumentStore import PandasDocumentBackend
from momo_kb.stores.document.persistence import CSVPersistence, HDF5Persistence


class TestHDF5Performance:
    """Benchmark HDF5 vs CSV performance for different operations."""

    @pytest.fixture(params=[100, 500, 1000])
    def document_count(self, request):
        """Different document counts for scaling tests."""
        return request.param

    @pytest.fixture
    def sample_documents(self, document_count):
        """Generate sample documents with rich metadata for testing."""
        docs = []
        for i in range(document_count):
            doc = {
                "content": f"Document {i} with comprehensive content for performance testing. "
                * 10,
                "metadata": {
                    "doc_id": i,
                    "category": f"category_{i % 20}",
                    "priority": i % 10,
                    "tags": [
                        f"tag_{i % 5}",
                        f"tag_{(i + 1) % 5}",
                        f"tag_{(i + 2) % 5}",
                    ],
                    "metrics": {
                        "views": i * 10,
                        "rating": 1 + (i % 5) * 0.8,
                        "engagement": i % 100 / 100.0,
                    },
                    "features": {
                        "has_images": i % 3 == 0,
                        "has_code": i % 4 == 0,
                        "word_count": 100 + (i % 200),
                    },
                },
            }
            docs.append((f"doc_{i:04d}", doc))
        return docs

    async def time_operation(self, operation_name: str, operation, *args, **kwargs):
        """Time an async operation and return result with timing."""
        start = time.perf_counter()
        result = await operation(*args, **kwargs)
        end = time.perf_counter()
        return result, end - start, operation_name

    @pytest.mark.asyncio
    async def test_write_performance_comparison(self, sample_documents):
        """Compare write performance between CSV and HDF5 formats."""

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            hdf5_path = f.name

        try:
            # Test CSV write performance
            csv_backend = PandasDocumentBackend(CSVPersistence(csv_path))
            hdf5_backend = PandasDocumentBackend(HDF5Persistence(hdf5_path))

            # Measure CSV write performance
            start_time = time.perf_counter()
            for doc_id, doc_data in sample_documents:
                await csv_backend.put(doc_id, doc_data)
            csv_write_time = time.perf_counter() - start_time
            await csv_backend.close()

            # Measure HDF5 write performance
            start_time = time.perf_counter()
            for doc_id, doc_data in sample_documents:
                await hdf5_backend.put(doc_id, doc_data)
            hdf5_write_time = time.perf_counter() - start_time
            await hdf5_backend.close()

            # Calculate metrics
            doc_count = len(sample_documents)
            csv_docs_per_sec = (
                doc_count / csv_write_time if csv_write_time > 0 else float("inf")
            )
            hdf5_docs_per_sec = (
                doc_count / hdf5_write_time if hdf5_write_time > 0 else float("inf")
            )

            # Print comparison results
            print(f"\n=== Write Performance Comparison ({doc_count} documents) ===")
            print(
                f"CSV  write: {csv_write_time:.4f}s total, {csv_docs_per_sec:.1f} docs/s"
            )
            print(
                f"HDF5 write: {hdf5_write_time:.4f}s total, {hdf5_docs_per_sec:.1f} docs/s"
            )

            if hdf5_write_time > 0 and csv_write_time > 0:
                speedup = csv_write_time / hdf5_write_time
                print(
                    f"HDF5 is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than CSV for writes"
                )

            # Both should complete successfully
            assert csv_write_time > 0
            assert hdf5_write_time > 0

        finally:
            # Cleanup
            for path in [csv_path, hdf5_path]:
                if os.path.exists(path):
                    os.unlink(path)

    @pytest.mark.asyncio
    async def test_read_performance_comparison(self, sample_documents):
        """Compare read performance between CSV and HDF5 formats."""

        # Create temporary files and populate them
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            hdf5_path = f.name

        try:
            # Populate both backends with same data
            csv_backend = PandasDocumentBackend(CSVPersistence(csv_path))
            hdf5_backend = PandasDocumentBackend(HDF5Persistence(hdf5_path))

            for doc_id, doc_data in sample_documents:
                await csv_backend.put(doc_id, doc_data)
                await hdf5_backend.put(doc_id, doc_data)

            await csv_backend.close()
            await hdf5_backend.close()

            # Test CSV read performance (full reload)
            start_time = time.perf_counter()
            csv_backend_read = PandasDocumentBackend(CSVPersistence(csv_path))
            csv_docs = await csv_backend_read.scan()
            csv_read_time = time.perf_counter() - start_time
            await csv_backend_read.close()

            # Test HDF5 read performance (full reload)
            start_time = time.perf_counter()
            hdf5_backend_read = PandasDocumentBackend(HDF5Persistence(hdf5_path))
            hdf5_docs = await hdf5_backend_read.scan()
            hdf5_read_time = time.perf_counter() - start_time
            await hdf5_backend_read.close()

            # Verify same number of documents loaded
            assert len(csv_docs) == len(hdf5_docs) == len(sample_documents)

            # Calculate metrics
            doc_count = len(sample_documents)
            csv_docs_per_sec = (
                doc_count / csv_read_time if csv_read_time > 0 else float("inf")
            )
            hdf5_docs_per_sec = (
                doc_count / hdf5_read_time if hdf5_read_time > 0 else float("inf")
            )

            # Print comparison results
            print(f"\n=== Read Performance Comparison ({doc_count} documents) ===")
            print(
                f"CSV  read:  {csv_read_time:.4f}s total, {csv_docs_per_sec:.1f} docs/s"
            )
            print(
                f"HDF5 read:  {hdf5_read_time:.4f}s total, {hdf5_docs_per_sec:.1f} docs/s"
            )

            if hdf5_read_time > 0 and csv_read_time > 0:
                speedup = csv_read_time / hdf5_read_time
                print(
                    f"HDF5 is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than CSV for reads"
                )

        finally:
            # Cleanup
            for path in [csv_path, hdf5_path]:
                if os.path.exists(path):
                    os.unlink(path)

    @pytest.mark.asyncio
    async def test_file_size_comparison(self, sample_documents):
        """Compare file sizes between CSV and HDF5 formats."""

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            hdf5_path = f.name

        try:
            # Populate both backends
            csv_backend = PandasDocumentBackend(CSVPersistence(csv_path))
            hdf5_backend = PandasDocumentBackend(HDF5Persistence(hdf5_path))

            for doc_id, doc_data in sample_documents:
                await csv_backend.put(doc_id, doc_data)
                await hdf5_backend.put(doc_id, doc_data)

            await csv_backend.close()
            await hdf5_backend.close()

            # Compare file sizes
            csv_size = os.path.getsize(csv_path)
            hdf5_size = os.path.getsize(hdf5_path)

            # Calculate compression ratio
            compression_ratio = csv_size / hdf5_size if hdf5_size > 0 else 1

            doc_count = len(sample_documents)
            print(f"\n=== File Size Comparison ({doc_count} documents) ===")
            print(f"CSV file size:  {csv_size:,} bytes ({csv_size / 1024:.1f} KB)")
            print(f"HDF5 file size: {hdf5_size:,} bytes ({hdf5_size / 1024:.1f} KB)")
            print(
                f"Compression ratio: {compression_ratio:.2f}x (HDF5 is {compression_ratio:.2f}x {'smaller' if compression_ratio > 1 else 'larger'})"
            )

            # Both files should exist and have content
            assert csv_size > 0
            assert hdf5_size > 0

        finally:
            # Cleanup
            for path in [csv_path, hdf5_path]:
                if os.path.exists(path):
                    os.unlink(path)

    @pytest.mark.asyncio
    async def test_random_access_performance(self, sample_documents):
        """Compare random access performance between formats."""

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            hdf5_path = f.name

        try:
            # Populate both backends
            csv_backend = PandasDocumentBackend(CSVPersistence(csv_path))
            hdf5_backend = PandasDocumentBackend(HDF5Persistence(hdf5_path))

            for doc_id, doc_data in sample_documents:
                await csv_backend.put(doc_id, doc_data)
                await hdf5_backend.put(doc_id, doc_data)

            await csv_backend.close()
            await hdf5_backend.close()

            # Load backends for reading
            csv_read_backend = PandasDocumentBackend(CSVPersistence(csv_path))
            hdf5_read_backend = PandasDocumentBackend(HDF5Persistence(hdf5_path))

            # Select random documents to access (every 10th document)
            test_keys = [doc_id for doc_id, _ in sample_documents[::10]]

            # Test CSV random access
            start_time = time.perf_counter()
            csv_retrieved = 0
            for key in test_keys:
                doc = await csv_read_backend.get(key)
                if doc:
                    csv_retrieved += 1
            csv_access_time = time.perf_counter() - start_time

            # Test HDF5 random access
            start_time = time.perf_counter()
            hdf5_retrieved = 0
            for key in test_keys:
                doc = await hdf5_read_backend.get(key)
                if doc:
                    hdf5_retrieved += 1
            hdf5_access_time = time.perf_counter() - start_time

            await csv_read_backend.close()
            await hdf5_read_backend.close()

            # Print results
            print(
                f"\n=== Random Access Performance ({len(test_keys)} gets from {len(sample_documents)} documents) ==="
            )
            print(
                f"CSV  access:  {csv_access_time:.4f}s total, {csv_retrieved} retrieved"
            )
            print(
                f"HDF5 access:  {hdf5_access_time:.4f}s total, {hdf5_retrieved} retrieved"
            )

            if hdf5_access_time > 0 and csv_access_time > 0:
                speedup = csv_access_time / hdf5_access_time
                print(
                    f"HDF5 is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than CSV for random access"
                )

            # Both should retrieve all documents
            assert csv_retrieved == hdf5_retrieved == len(test_keys)

        finally:
            # Cleanup
            for path in [csv_path, hdf5_path]:
                if os.path.exists(path):
                    os.unlink(path)

    @pytest.mark.asyncio
    async def test_scan_performance_comparison(self, sample_documents):
        """Compare scan/filter performance between formats."""

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            hdf5_path = f.name

        try:
            # Populate both backends
            csv_backend = PandasDocumentBackend(CSVPersistence(csv_path))
            hdf5_backend = PandasDocumentBackend(HDF5Persistence(hdf5_path))

            for doc_id, doc_data in sample_documents:
                await csv_backend.put(doc_id, doc_data)
                await hdf5_backend.put(doc_id, doc_data)

            await csv_backend.close()
            await hdf5_backend.close()

            # Load backends for reading
            csv_read_backend = PandasDocumentBackend(CSVPersistence(csv_path))
            hdf5_read_backend = PandasDocumentBackend(HDF5Persistence(hdf5_path))

            # Test different scan operations
            scan_tests = [
                ("full_scan", {}, None),
                ("pattern_search", {"pattern": "Document"}, None),
                ("metadata_filter", {}, {"category": "category_10"}),
                ("combined_filter", {"pattern": "performance"}, {"priority": 5}),
            ]

            results = {}

            for test_name, scan_args, filters in scan_tests:
                if filters:
                    scan_args["filters"] = filters

                # CSV scan performance
                start_time = time.perf_counter()
                csv_results = await csv_read_backend.scan(**scan_args)
                csv_scan_time = time.perf_counter() - start_time

                # HDF5 scan performance
                start_time = time.perf_counter()
                hdf5_results = await hdf5_read_backend.scan(**scan_args)
                hdf5_scan_time = time.perf_counter() - start_time

                results[test_name] = {
                    "csv": {"time": csv_scan_time, "count": len(csv_results)},
                    "hdf5": {"time": hdf5_scan_time, "count": len(hdf5_results)},
                }

            # Print results
            print(
                f"\n=== Scan Performance Comparison ({len(sample_documents)} total documents) ==="
            )
            for test_name, test_results in results.items():
                csv_time = test_results["csv"]["time"]
                hdf5_time = test_results["hdf5"]["time"]
                csv_count = test_results["csv"]["count"]
                hdf5_count = test_results["hdf5"]["count"]

                print(f"\n{test_name}:")
                print(f"  CSV:  {csv_time:.4f}s, {csv_count} results")
                print(f"  HDF5: {hdf5_time:.4f}s, {hdf5_count} results")

                if hdf5_time > 0 and csv_time > 0:
                    speedup = csv_time / hdf5_time
                    print(
                        f"  HDF5 is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'}"
                    )

                # Results should be consistent
                assert csv_count == hdf5_count

            await csv_read_backend.close()
            await hdf5_read_backend.close()

        finally:
            # Cleanup
            for path in [csv_path, hdf5_path]:
                if os.path.exists(path):
                    os.unlink(path)


if __name__ == "__main__":
    # Run specific benchmarks manually
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        pytest.main([__file__, "-v", "-s"])
