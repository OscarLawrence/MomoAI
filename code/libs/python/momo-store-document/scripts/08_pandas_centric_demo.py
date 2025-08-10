#!/usr/bin/env python3
"""
Pandas-Centric Document Backend Demo

This example demonstrates the new pandas-centric architecture with pluggable persistence:
- Unified pandas DataFrame as the core storage mechanism
- Multiple persistence strategies (memory, CSV, HDF5, DuckDB)
- Hybrid querying capabilities (pandas + backend-specific)
- Advanced analytics with pandas ecosystem

Run with: pdm run script 08_pandas_centric_demo
"""

import asyncio
import tempfile
import os
from datetime import datetime

from momo_kb import KnowledgeBase
from momo_kb.pandas_backend import (
    create_memory_backend,
    create_csv_backend,
    create_hdf5_backend,
    create_duckdb_backend,
)


async def main():
    print("🐼 Pandas-Centric Document Backend Demo")
    print("=" * 50)

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

        # Sample dataset with rich metadata
        sample_docs = [
            (
                "research_paper_1",
                {
                    "content": "Deep learning approaches to natural language processing have revolutionized the field, enabling unprecedented performance across various tasks including machine translation, sentiment analysis, and question answering systems.",
                    "metadata": {
                        "type": "research",
                        "field": "AI",
                        "year": 2023,
                        "citations": 156,
                        "authors": ["Dr. Smith", "Dr. Johnson"],
                        "keywords": ["deep learning", "NLP", "transformers"],
                        "metrics": {
                            "h_index": 45,
                            "impact_factor": 8.2,
                            "downloads": 2500,
                        },
                    },
                },
            ),
            (
                "tutorial_python",
                {
                    "content": "Python programming fundamentals including data structures, control flow, functions, and object-oriented programming concepts essential for software development and data science applications.",
                    "metadata": {
                        "type": "tutorial",
                        "field": "programming",
                        "year": 2024,
                        "views": 15000,
                        "topics": ["basics", "data structures", "OOP"],
                        "difficulty": "beginner",
                        "ratings": {"overall": 4.8, "clarity": 4.9, "examples": 4.7},
                    },
                },
            ),
            (
                "dataset_analysis",
                {
                    "content": "Comprehensive statistical analysis of climate data spanning 50 years, revealing significant trends in temperature variations and precipitation patterns across different geographical regions.",
                    "metadata": {
                        "type": "analysis",
                        "field": "climate",
                        "year": 2024,
                        "data_points": 50000,
                        "regions": ["North America", "Europe", "Asia"],
                        "methods": ["regression", "time-series"],
                        "confidence": {
                            "temperature": 0.95,
                            "precipitation": 0.89,
                            "trends": 0.92,
                        },
                    },
                },
            ),
            (
                "ml_model",
                {
                    "content": "Advanced machine learning model for predictive analytics in healthcare, incorporating ensemble methods and feature engineering techniques to improve diagnostic accuracy and patient outcomes.",
                    "metadata": {
                        "type": "model",
                        "field": "healthcare",
                        "year": 2024,
                        "accuracy": 0.94,
                        "features": ["age", "symptoms", "history"],
                        "algorithms": ["random_forest", "xgboost"],
                        "performance": {
                            "precision": 0.92,
                            "recall": 0.91,
                            "f1_score": 0.93,
                        },
                    },
                },
            ),
            (
                "web_app",
                {
                    "content": "Full-stack web application development using modern frameworks, implementing responsive design principles, API integration, and database management for scalable enterprise solutions.",
                    "metadata": {
                        "type": "application",
                        "field": "web_dev",
                        "year": 2024,
                        "users": 10000,
                        "tech_stack": ["React", "Node.js", "PostgreSQL"],
                        "features": ["responsive", "API", "auth"],
                        "metrics": {
                            "load_time": 1.2,
                            "uptime": 99.9,
                            "satisfaction": 4.6,
                        },
                    },
                },
            ),
        ]

        print(f"\n📊 Creating Backends with Different Persistence Strategies")
        print("-" * 60)

        # Create different backends
        memory_backend = create_memory_backend()
        csv_backend = create_csv_backend(csv_path)
        hdf5_backend = create_hdf5_backend(hdf5_path)
        duckdb_backend = create_duckdb_backend(duckdb_path)

        backends = [
            ("Memory (No Persistence)", memory_backend),
            ("CSV Persistence", csv_backend),
            ("HDF5 Persistence", hdf5_backend),
            ("DuckDB Persistence", duckdb_backend),
        ]

        # Populate all backends with the same data
        print(f"\n📝 Populating All Backends")
        print("-" * 30)

        import time

        for name, backend in backends:
            start_time = time.perf_counter()
            for doc_id, doc_data in sample_docs:
                await backend.put(doc_id, doc_data)
            end_time = time.perf_counter()
            print(f"{name}: {end_time - start_time:.4f} seconds")

            # Close to trigger persistence
            await backend.close()

        print(f"\n🔍 Reading Performance Comparison")
        print("-" * 40)

        # Test read performance from persisted data
        backend_configs = [
            ("Memory", lambda: create_memory_backend()),
            ("CSV", lambda: create_csv_backend(csv_path)),
            ("HDF5", lambda: create_hdf5_backend(hdf5_path)),
            ("DuckDB", lambda: create_duckdb_backend(duckdb_path)),
        ]

        for name, backend_factory in backend_configs:
            # Create fresh backend instances to test loading from persistence
            backend = backend_factory()
            start_time = time.perf_counter()
            docs = await backend.scan()
            end_time = time.perf_counter()
            print(
                f"{name} read: {end_time - start_time:.4f} seconds ({len(docs)} documents)"
            )
            await backend.close()

        print(f"\n💾 File Size Comparison")
        print("-" * 30)

        files = [
            ("CSV", csv_path),
            ("HDF5", hdf5_path),
            ("DuckDB", duckdb_path),
        ]

        for name, file_path in files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"{name} file size: {size:,} bytes ({size/1024:.1f} KB)")

        print(f"\n🔍 Advanced Analytics with Pandas")
        print("-" * 40)

        # Use DuckDB backend for advanced analytics
        analytics_backend = create_duckdb_backend(duckdb_path)
        df = analytics_backend.get_dataframe()
        print(f"Loaded DataFrame: {df.shape[0]} rows, {df.shape[1]} columns")

        # Extract metrics for analysis
        if not df.empty:
            # Extract year from metadata
            df["year"] = df["metadata"].apply(
                lambda x: x.get("year", 0) if isinstance(x, dict) else 0
            )
            df["field"] = df["metadata"].apply(
                lambda x: x.get("field", "unknown")
                if isinstance(x, dict)
                else "unknown"
            )
            df["type"] = df["metadata"].apply(
                lambda x: x.get("type", "unknown") if isinstance(x, dict) else "unknown"
            )

            print(f"\nContent by field:")
            field_counts = df["field"].value_counts()
            for field, count in field_counts.items():
                print(f"  {field}: {count} documents")

            print(f"\nContent by type:")
            type_counts = df["type"].value_counts()
            for doc_type, count in type_counts.items():
                print(f"  {doc_type}: {count} documents")

        print(f"\n🔍 Advanced Search Capabilities")
        print("-" * 40)

        # Test search capabilities
        ai_docs = await analytics_backend.scan(filters={"field": "AI"})
        print(f"AI-related documents: {len(ai_docs)} found")

        recent_docs = await analytics_backend.scan(filters={"year": 2024})
        print(f"Documents from 2024: {len(recent_docs)} found")

        tutorial_docs = await analytics_backend.scan(
            pattern="Python", filters={"type": "tutorial"}
        )
        print(f"Python tutorials: {len(tutorial_docs)} found")

        # Test pandas query expression
        try:
            python_docs = analytics_backend.query(
                "id.str.contains('python', case=False)"
            )
            print(f"Pandas query (python in id): {len(python_docs)} found")
        except Exception as e:
            print(f"Pandas query failed: {e}")

        print(f"\n🦆 DuckDB-Specific Complex Queries")
        print("-" * 40)

        # Test DuckDB-specific complex queries
        try:
            # Execute a complex SQL query using DuckDB's capabilities
            result = analytics_backend.execute_backend_query(
                "SELECT COUNT(*) as doc_count, json_extract_string(metadata, '$.field') as field FROM documents GROUP BY field ORDER BY doc_count DESC"
            )
            print(f"DuckDB aggregation query result:")
            for row in result:
                print(f"  {row[1]}: {row[0]} documents")
        except Exception as e:
            print(f"DuckDB complex query failed: {e}")

        await analytics_backend.close()

        print(f"\n🐼 Pandas-Centric Architecture Benefits")
        print("-" * 50)
        print("✅ Unified pandas DataFrame as core storage")
        print("✅ Pluggable persistence strategies")
        print("✅ Hybrid querying (pandas + backend-specific)")
        print("✅ Advanced analytics with pandas ecosystem")
        print("✅ Consistent API across persistence formats")
        print("✅ Efficient in-memory operations")
        print("✅ Flexible persistence options")

        print(f"\n📊 Performance Characteristics")
        print("-" * 35)
        print("• Fast in-memory operations with pandas")
        print("• Efficient persistence with multiple formats")
        print("• Advanced analytics capabilities")
        print("• Backend-specific optimizations when needed")
        print("• Seamless integration with data science tools")

        print(f"\n✅ Pandas-Centric Backend Demo Complete!")
        print(f"Key advantages:")
        print(f"  • Unified interface for all document operations")
        print(f"  • Choice of persistence strategy for different use cases")
        print(f"  • Access to both pandas and backend-specific features")
        print(f"  • Elimination of redundant InMemoryDocumentBackend")
        print(f"  • Future extensibility for new persistence formats")

    finally:
        # Cleanup
        for path in [csv_path, hdf5_path, duckdb_path]:
            if os.path.exists(path):
                os.unlink(path)


if __name__ == "__main__":
    asyncio.run(main())
