"""
Performance benchmarks for PandasDocumentBackend.

Compares performance against existing backends (InMemory, DuckDB)
focusing on different use cases and data sizes.
"""

import asyncio
import pytest
import time
import tempfile
from typing import Dict, Any, List
import tempfile
import os

from momo_kb.stores.document.PandasDocumentStore import PandasDocumentBackend
from momo_kb.stores.document.persistence import (
    DuckDBPersistence,
    NoPersistence,
    CSVPersistence,
)


class TestDocumentBackendBenchmarks:
    """Benchmark comparison between document backends."""

    @pytest.fixture(params=[10, 100, 1000])
    def document_count(self, request):
        """Different document counts for scaling tests."""
        return request.param

    @pytest.fixture
    def sample_documents(self, document_count):
        """Generate sample documents for testing."""
        docs = []
        for i in range(document_count):
            doc = {
                "content": f"This is test document {i} with some content for benchmarking purposes. "
                * 5,
                "metadata": {
                    "id": i,
                    "category": f"category_{i % 10}",
                    "priority": i % 5,
                    "tags": [f"tag_{i % 3}", f"tag_{(i + 1) % 3}"],
                    "size": (
                        "large" if i % 4 == 0 else "medium" if i % 2 == 0 else "small"
                    ),
                },
            }
            docs.append((f"doc_{i:04d}", doc))
        return docs

    @pytest.fixture
    async def inmemory_backend(self):
        """InMemory backend for comparison."""
        backend = PandasDocumentBackend(NoPersistence())
        yield backend
        # No cleanup needed

    @pytest.fixture
    async def duckdb_backend(self):
        """DuckDB backend for comparison."""
        backend = PandasDocumentBackend(DuckDBPersistence(":memory:"))
        yield backend
        await backend.close()

    @pytest.fixture
    async def pandas_backend(self):
        """Pandas backend for comparison."""
        backend = PandasDocumentBackend(NoPersistence())
        yield backend
        await backend.close()

    @pytest.fixture
    async def pandas_backend_csv(self):
        """Pandas backend with CSV persistence for comparison."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            backend = PandasDocumentBackend(CSVPersistence(temp_path))
            yield backend
            await backend.close()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def time_operation(self, operation, *args, **kwargs):
        """Time an async operation."""
        start = time.perf_counter()
        result = await operation(*args, **kwargs)
        end = time.perf_counter()
        return result, end - start

    def time_sync_operation(self, operation, *args, **kwargs):
        """Time a synchronous operation."""
        start = time.perf_counter()
        result = operation(*args, **kwargs)
        end = time.perf_counter()
        return result, end - start

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(
        self, sample_documents, inmemory_backend, duckdb_backend, pandas_backend
    ):
        """Compare bulk insert performance across backends."""
        backends = {
            "inmemory": inmemory_backend,
            "duckdb": duckdb_backend,
            "pandas": pandas_backend,
        }

        results = {}

        for name, backend in backends.items():
            # Time bulk insert
            start = time.perf_counter()
            for doc_id, doc_data in sample_documents:
                await backend.put(doc_id, doc_data)
            end = time.perf_counter()

            insert_time = end - start
            results[name] = {
                "insert_time": insert_time,
                "docs_per_second": (
                    len(sample_documents) / insert_time
                    if insert_time > 0
                    else float("inf")
                ),
                "avg_time_per_doc": (
                    insert_time / len(sample_documents)
                    if len(sample_documents) > 0
                    else 0
                ),
            }

        # Print results for analysis
        print(f"\n=== Bulk Insert Performance ({len(sample_documents)} documents) ===")
        for name, metrics in results.items():
            print(
                f"{name:12}: {metrics['insert_time']:.4f}s total, {metrics['docs_per_second']:.1f} docs/s, {metrics['avg_time_per_doc'] * 1000:.2f}ms/doc"
            )

        # All backends should complete successfully
        for name in backends:
            assert results[name]["insert_time"] > 0

    @pytest.mark.asyncio
    async def test_scan_performance(
        self, sample_documents, inmemory_backend, duckdb_backend, pandas_backend
    ):
        """Compare scan performance across backends."""
        backends = {
            "inmemory": inmemory_backend,
            "duckdb": duckdb_backend,
            "pandas": pandas_backend,
        }

        # First, populate all backends
        for name, backend in backends.items():
            for doc_id, doc_data in sample_documents:
                await backend.put(doc_id, doc_data)

        results = {}

        # Test different scan scenarios
        scan_tests = [
            ("full_scan", {}, None),
            ("pattern_search", {"pattern": "test"}, None),
            ("metadata_filter", {}, {"category": "category_5"}),
            ("combined_filter", {"pattern": "document"}, {"priority": 3}),
        ]

        for test_name, scan_kwargs, filters in scan_tests:
            test_results = {}

            for name, backend in backends.items():
                if filters:
                    scan_kwargs["filters"] = filters

                result, scan_time = await self.time_operation(
                    backend.scan, **scan_kwargs
                )

                test_results[name] = {
                    "scan_time": scan_time,
                    "results_count": len(result),
                    "ms_per_result": (scan_time * 1000) / max(len(result), 1),
                }

            results[test_name] = test_results

        # Print results for analysis
        print(f"\n=== Scan Performance ({len(sample_documents)} documents) ===")
        for test_name, test_results in results.items():
            print(f"\n{test_name}:")
            for name, metrics in test_results.items():
                print(
                    f"  {name:12}: {metrics['scan_time'] * 1000:.2f}ms, {metrics['results_count']} results, {metrics['ms_per_result']:.2f}ms/result"
                )

        # All backends should return results for full scan
        for name in backends:
            assert results["full_scan"][name]["results_count"] > 0

    @pytest.mark.asyncio
    async def test_random_access_performance(
        self, sample_documents, inmemory_backend, duckdb_backend, pandas_backend
    ):
        """Compare random access (get by key) performance."""
        backends = {
            "inmemory": inmemory_backend,
            "duckdb": duckdb_backend,
            "pandas": pandas_backend,
        }

        # Populate backends
        for name, backend in backends.items():
            for doc_id, doc_data in sample_documents:
                await backend.put(doc_id, doc_data)

        # Test random access on subset of keys
        test_keys = [
            doc_id
            for doc_id, _ in sample_documents[:: max(1, len(sample_documents) // 20)]
        ]  # Every ~20th document

        results = {}

        for name, backend in backends.items():
            start = time.perf_counter()
            retrieved = 0

            for key in test_keys:
                doc = await backend.get(key)
                if doc:
                    retrieved += 1

            end = time.perf_counter()
            access_time = end - start

            results[name] = {
                "total_time": access_time,
                "keys_accessed": len(test_keys),
                "retrieved_count": retrieved,
                "avg_time_per_get": (
                    access_time / len(test_keys) if len(test_keys) > 0 else 0
                ),
                "gets_per_second": (
                    len(test_keys) / access_time if access_time > 0 else float("inf")
                ),
            }

        # Print results
        print(
            f"\n=== Random Access Performance ({len(test_keys)} gets from {len(sample_documents)} documents) ==="
        )
        for name, metrics in results.items():
            print(
                f"{name:12}: {metrics['total_time'] * 1000:.2f}ms total, {metrics['avg_time_per_get'] * 1000:.3f}ms/get, {metrics['gets_per_second']:.1f} gets/s"
            )

        # All backends should retrieve all requested documents
        for name, metrics in results.items():
            assert metrics["retrieved_count"] == len(test_keys)

    @pytest.mark.asyncio
    async def test_pandas_specific_features(self, sample_documents, pandas_backend):
        """Test pandas-specific analytics features performance."""
        # Populate backend
        for doc_id, doc_data in sample_documents:
            await pandas_backend.put(doc_id, doc_data)

        # Test analytics features
        analytics_tests = []

        # DataFrame access
        start = time.perf_counter()
        df = pandas_backend.get_dataframe()
        end = time.perf_counter()
        analytics_tests.append(("dataframe_access", end - start, len(df)))

        # Statistics
        start = time.perf_counter()
        stats = pandas_backend.get_stats()
        end = time.perf_counter()
        analytics_tests.append(("get_stats", end - start, stats["total_documents"]))

        # Query operation (if DataFrame not empty)
        if not df.empty:
            start = time.perf_counter()
            try:
                query_results = pandas_backend.query("content.str.len() > 10")
                end = time.perf_counter()
                analytics_tests.append(
                    ("pandas_query", end - start, len(query_results))
                )
            except Exception as e:
                # Query might fail on empty or incompatible data
                analytics_tests.append(("pandas_query", 0, 0))

        # Print results
        print(f"\n=== Pandas Analytics Features Performance ===")
        for test_name, exec_time, result_count in analytics_tests:
            print(f"{test_name:20}: {exec_time * 1000:.3f}ms, {result_count} items")

        # Verify basic functionality
        assert df is not None
        assert stats["total_documents"] == len(sample_documents)

    @pytest.mark.asyncio
    async def test_memory_usage_comparison(self, sample_documents):
        """Compare memory usage between backends."""

        def get_memory_mb():
            import os

            try:
                import psutil

                process = psutil.Process(os.getpid())
                return process.memory_info().rss / 1024 / 1024
            except ImportError:
                # Fallback if psutil not available - rough estimate using memory info
                return 0.0

        # Baseline memory
        baseline_memory = get_memory_mb()

        backends_memory = {}

        # Test each backend
        backend_configs = [
            ("inmemory", lambda: PandasDocumentBackend(NoPersistence())),
            (
                "pandas_csv",
                lambda: PandasDocumentBackend(
                    CSVPersistence(tempfile.mktemp(suffix=".csv"))
                ),
            ),
            (
                "pandas_duckdb",
                lambda: PandasDocumentBackend(DuckDBPersistence(":memory:")),
            ),
        ]

        for name, backend_factory in backend_configs:
            # Create backend
            backend = backend_factory()

            memory_before = get_memory_mb()

            # Populate with documents
            for doc_id, doc_data in sample_documents:
                await backend.put(doc_id, doc_data)

            memory_after = get_memory_mb()
            memory_used = memory_after - memory_before

            backends_memory[name] = {
                "memory_mb": memory_used,
                "memory_per_doc": (
                    memory_used / len(sample_documents)
                    if len(sample_documents) > 0
                    else 0
                ),
            }

            # Cleanup
            if hasattr(backend, "close"):
                await backend.close()

        # Print results
        print(f"\n=== Memory Usage Comparison ({len(sample_documents)} documents) ===")
        print(f"Baseline memory: {baseline_memory:.2f} MB")
        for name, metrics in backends_memory.items():
            print(
                f"{name:12}: {metrics['memory_mb']:.2f} MB total, {metrics['memory_per_doc'] * 1000:.3f} KB/doc"
            )

        # All backends should use some memory
        for name, metrics in backends_memory.items():
            # Memory measurement can be noisy, just check it's reasonable
            assert metrics["memory_mb"] >= 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("backend_name", ["inmemory", "duckdb", "pandas"])
    async def test_concurrent_operations_performance(
        self, backend_name, sample_documents
    ):
        """Test concurrent operation performance."""
        # Create backend
        if backend_name == "inmemory":
            backend = PandasDocumentBackend(NoPersistence())
        elif backend_name == "duckdb":
            backend = PandasDocumentBackend(DuckDBPersistence(":memory:"))
        elif backend_name == "pandas":
            backend = PandasDocumentBackend(NoPersistence())
        else:
            pytest.skip(f"Unknown backend: {backend_name}")

        try:
            # Test concurrent writes
            async def write_batch(docs_batch):
                for doc_id, doc_data in docs_batch:
                    await backend.put(doc_id, doc_data)

            # Split documents into batches for concurrent writing
            batch_size = max(1, len(sample_documents) // 4)
            batches = [
                sample_documents[i : i + batch_size]
                for i in range(0, len(sample_documents), batch_size)
            ]

            start = time.perf_counter()
            await asyncio.gather(*[write_batch(batch) for batch in batches])
            end = time.perf_counter()

            concurrent_write_time = end - start

            # Test concurrent reads
            test_keys = [
                doc_id for doc_id, _ in sample_documents[::5]
            ]  # Every 5th document

            start = time.perf_counter()
            results = await asyncio.gather(*[backend.get(key) for key in test_keys])
            end = time.perf_counter()

            concurrent_read_time = end - start
            successful_reads = sum(1 for result in results if result is not None)

            print(f"\n=== Concurrent Operations Performance ({backend_name}) ===")
            print(
                f"Concurrent writes: {concurrent_write_time:.4f}s for {len(sample_documents)} docs"
            )
            print(
                f"Concurrent reads:  {concurrent_read_time:.4f}s for {len(test_keys)} gets ({successful_reads} successful)"
            )

            # Verify operations succeeded
            assert concurrent_write_time > 0
            assert concurrent_read_time > 0
            assert successful_reads == len(test_keys)

        finally:
            if hasattr(backend, "close"):
                await backend.close()


if __name__ == "__main__":
    # Run specific benchmarks manually
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        pytest.main([__file__, "-v", "-s"])
