"""
Performance benchmarks for DuckDB document backend.

Comprehensive benchmarks comparing DuckDB against in-memory implementation
and testing scalability across different document set sizes.
"""

import pytest
import asyncio
import time
import statistics
from typing import List
import tempfile
import os

from momo_kb import Document, DocumentMetadata
from momo_kb.stores.document.PandasDocumentStore import PandasDocumentBackend
from momo_kb.stores.document.persistence import DuckDBPersistence, NoPersistence


class BenchmarkTimer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.duration: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        if self.start_time is not None and self.end_time is not None:
            self.duration = self.end_time - self.start_time


def generate_test_documents(count: int, content_size: str = "medium") -> List[Document]:
    """Generate test documents of various sizes."""
    content_templates = {
        "small": "Document {i} with basic content about {topic}.",
        "medium": "Document {i} contains detailed information about {topic}. " * 10,
        "large": "Document {i} provides comprehensive coverage of {topic}. " * 100,
    }

    topics = [
        "python",
        "javascript",
        "machine_learning",
        "data_science",
        "web_development",
        "algorithms",
        "databases",
        "cloud_computing",
        "artificial_intelligence",
        "software_engineering",
    ]

    template = content_templates.get(content_size, content_templates["medium"])
    documents = []

    for i in range(count):
        topic = topics[i % len(topics)]
        content = template.format(i=i, topic=topic)

        doc = Document(
            content=content,
            metadata=DocumentMetadata(
                source=f"source_{i % 20}",
                author=f"author_{i % 10}",
                type=["tutorial", "course", "reference", "guide"][i % 4],
                category=["programming", "ai", "data", "web"][i % 4],
                tags=[f"tag_{j}" for j in range(i % 5 + 1)],
                language="en",
                custom={"difficulty": ["beginner", "intermediate", "advanced"][i % 3]},
            ),
        )
        documents.append(doc)

    return documents


class TestDuckDBPerformanceBenchmarks:
    """Benchmark DuckDB document backend performance."""

    @pytest.fixture(params=[10, 100, 1000])
    def document_count(self, request):
        """Parameterized document counts for scaling tests."""
        return request.param

    @pytest.fixture
    def duckdb_backend(self):
        """DuckDB backend using pandas with DuckDB persistence."""
        return PandasDocumentBackend(DuckDBPersistence(":memory:"))

    @pytest.fixture
    def inmemory_backend(self):
        """In-memory backend using pandas with no persistence."""
        return PandasDocumentBackend(NoPersistence())

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, duckdb_backend, document_count):
        """Benchmark bulk document insertion."""
        documents = generate_test_documents(document_count, "medium")

        # Convert to backend format
        doc_data = []
        for doc in documents:
            doc_dict = {
                "content": doc.content,
                "metadata": doc.metadata.model_dump() if doc.metadata else {},
            }
            doc_data.append((doc.id, doc_dict))

        # Benchmark insertion
        with BenchmarkTimer() as timer:
            for doc_id, data in doc_data:
                await duckdb_backend.put(doc_id, data)

        avg_time_per_doc = timer.duration / document_count
        print(f"\nDuckDB bulk insert ({document_count} docs):")
        print(f"  Total time: {timer.duration:.3f}s")
        print(f"  Avg per document: {avg_time_per_doc * 1000:.2f}ms")
        print(f"  Documents/second: {document_count / timer.duration:.1f}")

        # Verify all documents were stored
        results = await duckdb_backend.scan()
        assert len(results) == document_count

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_search_performance_scaling(self, duckdb_backend):
        """Test search performance across different dataset sizes."""
        results = {}

        for doc_count in [100, 500, 1000, 2000]:
            # Setup data
            documents = generate_test_documents(doc_count, "medium")

            for doc in documents:
                doc_dict = {
                    "content": doc.content,
                    "metadata": doc.metadata.model_dump() if doc.metadata else {},
                }
                await duckdb_backend.put(doc.id, doc_dict)

            # Benchmark search operations
            search_times = []
            for _ in range(10):  # Multiple runs for average
                with BenchmarkTimer() as timer:
                    await duckdb_backend.scan(pattern="python")
                if timer.duration > 0:  # Only add valid durations
                    search_times.append(timer.duration)

            avg_search_time = statistics.mean(search_times)
            results[doc_count] = avg_search_time

            print(f"\nDuckDB search performance ({doc_count} docs):")
            print(f"  Average search time: {avg_search_time * 1000:.2f}ms")
            print(f"  Std dev: {statistics.stdev(search_times) * 1000:.2f}ms")

        # Verify search times don't degrade significantly with scale
        assert (
            results[2000] < results[100] * 20
        )  # Should not be 20x slower (more reasonable)

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_filtered_scan_performance(self, duckdb_backend):
        """Benchmark filtered scanning with complex filters."""
        doc_count = 1000
        documents = generate_test_documents(doc_count, "medium")

        # Insert documents
        for doc in documents:
            doc_dict = {
                "content": doc.content,
                "metadata": doc.metadata.model_dump() if doc.metadata else {},
            }
            await duckdb_backend.put(doc.id, doc_dict)

        # Test different filter complexities
        filter_tests = [
            {"author": "author_1"},
            {"type": "tutorial", "category": "programming"},
            {"difficulty": "advanced", "language": "en", "category": "ai"},
        ]

        for i, filters in enumerate(filter_tests):
            filter_times = []
            results = []
            for _ in range(10):
                with BenchmarkTimer() as timer:
                    results = await duckdb_backend.scan(filters=filters)
                filter_times.append(timer.duration)

            avg_time = statistics.mean(filter_times)
            result_count = len(results)

            print(f"\nDuckDB filtered scan {i + 1} ({len(filters)} filters):")
            print(f"  Average time: {avg_time * 1000:.2f}ms")
            print(f"  Results found: {result_count}")
            print(
                f"  Time per result: {(avg_time / max(result_count, 1)) * 1000:.2f}ms"
            )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_sequential_operation_performance(self, duckdb_backend):
        """Benchmark sequential read/write operations (DuckDB not thread-safe)."""
        # Setup initial data
        setup_docs = generate_test_documents(500, "medium")
        for doc in setup_docs:
            doc_dict = {
                "content": doc.content,
                "metadata": doc.metadata.model_dump() if doc.metadata else {},
            }
            await duckdb_backend.put(doc.id, doc_dict)

        # Sequential read operations
        async def read_operation():
            with BenchmarkTimer() as timer:
                await duckdb_backend.scan(pattern="python")
            return timer.duration

        async def write_operation(doc_id, doc_data):
            with BenchmarkTimer() as timer:
                await duckdb_backend.put(doc_id, doc_data)
            return timer.duration

        # Test sequential reads (avoiding concurrency due to DuckDB thread-safety)
        read_times = []
        with BenchmarkTimer() as total_timer:
            for _ in range(20):
                read_time = await read_operation()
                read_times.append(read_time)

        avg_read_time = statistics.mean(read_times)
        print(f"\nDuckDB sequential reads (20 operations):")
        print(f"  Total time: {total_timer.duration:.3f}s")
        print(f"  Average read time: {avg_read_time * 1000:.2f}ms")
        print(f"  Operations/second: {20 / total_timer.duration:.1f}")

        # Test mixed sequential operations
        new_docs = generate_test_documents(10, "medium")
        write_data = []
        for doc in new_docs:
            doc_dict = {
                "content": doc.content,
                "metadata": doc.metadata.model_dump() if doc.metadata else {},
            }
            write_data.append((doc.id, doc_dict))

        with BenchmarkTimer() as timer:
            # 10 sequential reads
            for _ in range(10):
                await read_operation()
            # 10 sequential writes
            for doc_id, data in write_data:
                await write_operation(doc_id, data)

        print(f"\nDuckDB mixed sequential operations (10 reads + 10 writes):")
        print(f"  Total time: {timer.duration:.3f}s")
        print(f"  Operations/second: {20 / timer.duration:.1f}")


class TestDuckDBVsInMemoryComparison:
    """Compare DuckDB performance against in-memory backend."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_insertion_speed_comparison(self):
        """Compare insertion speed between DuckDB and in-memory."""
        doc_count = 1000
        documents = generate_test_documents(doc_count, "medium")

        # Test DuckDB
        duckdb_backend = PandasDocumentBackend(DuckDBPersistence(":memory:"))
        with BenchmarkTimer() as duckdb_timer:
            for doc in documents:
                doc_dict = {
                    "content": doc.content,
                    "metadata": doc.metadata.model_dump() if doc.metadata else {},
                }
                await duckdb_backend.put(doc.id, doc_dict)

        # Test In-Memory
        inmemory_backend = PandasDocumentBackend(NoPersistence())
        with BenchmarkTimer() as inmemory_timer:
            for doc in documents:
                doc_dict = {
                    "content": doc.content,
                    "metadata": doc.metadata.model_dump() if doc.metadata else {},
                }
                await inmemory_backend.put(doc.id, doc_dict)

        print(f"\nInsertion Speed Comparison ({doc_count} documents):")
        print(
            f"  DuckDB: {duckdb_timer.duration:.3f}s ({doc_count / duckdb_timer.duration:.1f} docs/s)"
        )
        print(
            f"  In-Memory: {inmemory_timer.duration:.3f}s ({doc_count / inmemory_timer.duration:.1f} docs/s)"
        )
        print(f"  Ratio: {duckdb_timer.duration / inmemory_timer.duration:.2f}x")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_search_speed_comparison(self):
        """Compare search speed between backends."""
        doc_count = 1000
        documents = generate_test_documents(doc_count, "medium")

        # Setup both backends
        duckdb_backend = PandasDocumentBackend(DuckDBPersistence(":memory:"))
        inmemory_backend = PandasDocumentBackend(NoPersistence())

        for doc in documents:
            doc_dict = {
                "content": doc.content,
                "metadata": doc.metadata.model_dump() if doc.metadata else {},
            }
            await duckdb_backend.put(doc.id, doc_dict)
            await inmemory_backend.put(doc.id, doc_dict)

        # Benchmark search operations
        search_patterns = ["python", "machine_learning", "tutorial"]

        for pattern in search_patterns:
            # DuckDB search
            duckdb_times = []
            duckdb_results = []
            for _ in range(10):
                with BenchmarkTimer() as timer:
                    duckdb_results = await duckdb_backend.scan(pattern=pattern)
                if timer.duration > 0:
                    duckdb_times.append(timer.duration)

            # In-Memory search
            inmemory_times = []
            inmemory_results = []
            for _ in range(10):
                with BenchmarkTimer() as timer:
                    inmemory_results = await inmemory_backend.scan(pattern=pattern)
                if timer.duration > 0:
                    inmemory_times.append(timer.duration)

            duckdb_avg = statistics.mean(duckdb_times)
            inmemory_avg = statistics.mean(inmemory_times)

            print(f"\nSearch Speed Comparison - Pattern '{pattern}':")
            print(
                f"  DuckDB: {duckdb_avg * 1000:.2f}ms (found {len(duckdb_results)} results)"
            )
            print(
                f"  In-Memory: {inmemory_avg * 1000:.2f}ms (found {len(inmemory_results)} results)"
            )
            print(f"  Ratio: {duckdb_avg / inmemory_avg:.2f}x")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self):
        """Test memory usage as dataset grows."""
        # This test is conceptual - actual memory measurement would require
        # additional tooling like psutil or memory_profiler

        for doc_count in [100, 500, 1000, 2000]:
            documents = generate_test_documents(doc_count, "large")  # Larger documents

            # Test DuckDB memory usage (file-based, should be lower)
            duckdb_backend = PandasDocumentBackend(DuckDBPersistence(":memory:"))

            with BenchmarkTimer() as timer:
                for doc in documents:
                    doc_dict = {
                        "content": doc.content,
                        "metadata": doc.metadata.model_dump() if doc.metadata else {},
                    }
                    await duckdb_backend.put(doc.id, doc_dict)

            # Simulate memory test by checking if operations still perform well
            with BenchmarkTimer() as search_timer:
                results = await duckdb_backend.scan(pattern="machine_learning")

            print(f"\nDuckDB scaling test ({doc_count} large documents):")
            print(f"  Insert time: {timer.duration:.3f}s")
            print(f"  Search time: {search_timer.duration * 1000:.2f}ms")
            print(f"  Results found: {len(results)}")


class TestDuckDBFilePersistencePerformance:
    """Test performance characteristics of file persistence."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_file_vs_memory_performance(self):
        """Compare file-based vs in-memory DuckDB performance."""
        doc_count = 500
        documents = generate_test_documents(doc_count, "medium")

        # Test in-memory DuckDB
        memory_backend = PandasDocumentBackend(DuckDBPersistence(":memory:"))
        with BenchmarkTimer() as memory_timer:
            for doc in documents:
                doc_dict = {
                    "content": doc.content,
                    "metadata": doc.metadata.model_dump() if doc.metadata else {},
                }
                await memory_backend.put(doc.id, doc_dict)

        # Test file-based DuckDB
        with tempfile.NamedTemporaryFile(delete=False, suffix=".duckdb") as tf:
            db_path = tf.name

        try:
            file_backend = PandasDocumentBackend(DuckDBPersistence(db_path))
            with BenchmarkTimer() as file_timer:
                for doc in documents:
                    doc_dict = {
                        "content": doc.content,
                        "metadata": doc.metadata.model_dump() if doc.metadata else {},
                    }
                    await file_backend.put(doc.id, doc_dict)

            await file_backend.close()

            print(f"\nFile vs Memory Performance ({doc_count} documents):")
            print(f"  Memory DuckDB: {memory_timer.duration:.3f}s")
            print(f"  File DuckDB: {file_timer.duration:.3f}s")
            print(
                f"  File overhead: {(file_timer.duration - memory_timer.duration) / memory_timer.duration * 100:.1f}%"
            )

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_startup_time(self):
        """Test time to initialize database with existing data."""
        doc_count = 1000
        documents = generate_test_documents(doc_count, "medium")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".duckdb") as tf:
            db_path = tf.name

        try:
            # Create database with data
            backend = PandasDocumentBackend(DuckDBPersistence(db_path))
            for doc in documents:
                doc_dict = {
                    "content": doc.content,
                    "metadata": doc.metadata.model_dump() if doc.metadata else {},
                }
                await backend.put(doc.id, doc_dict)
            await backend.close()

            # Test startup times
            startup_times = []
            for _ in range(10):
                with BenchmarkTimer() as timer:
                    new_backend = PandasDocumentBackend(DuckDBPersistence(db_path))
                    # Perform a simple operation to ensure initialization
                    await new_backend.get("doc_0")
                    await new_backend.close()
                startup_times.append(timer.duration)

            avg_startup = statistics.mean(startup_times)
            print(f"\nDatabase Startup Performance ({doc_count} existing documents):")
            print(f"  Average startup time: {avg_startup * 1000:.2f}ms")
            print(f"  Std deviation: {statistics.stdev(startup_times) * 1000:.2f}ms")

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
