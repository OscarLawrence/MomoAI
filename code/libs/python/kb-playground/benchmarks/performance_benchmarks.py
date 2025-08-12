"""
Performance benchmarks for KB Playground.

Comprehensive benchmarking suite to measure and validate performance claims.
"""

import time
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import shutil

from kb_playground import KnowledgeBase, Document


class PerformanceBenchmarks:
    """
    Comprehensive performance benchmarking suite.
    
    Tests various aspects of KB performance:
    - Document insertion speed
    - Search latency and quality
    - Memory efficiency
    - Rollback performance
    - Relationship discovery speed
    """
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        """Initialize benchmark suite."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks."""
        print("🚀 Starting KB Playground Performance Benchmarks")
        print("=" * 60)
        
        # Document insertion benchmarks
        print("\n📝 Document Insertion Benchmarks")
        self.results["insertion"] = self._benchmark_insertion()
        
        # Search performance benchmarks
        print("\n🔍 Search Performance Benchmarks")
        self.results["search"] = self._benchmark_search()
        
        # Memory efficiency benchmarks
        print("\n💾 Memory Efficiency Benchmarks")
        self.results["memory"] = self._benchmark_memory()
        
        # Rollback performance benchmarks
        print("\n⏪ Rollback Performance Benchmarks")
        self.results["rollback"] = self._benchmark_rollback()
        
        # Relationship discovery benchmarks
        print("\n🔗 Relationship Discovery Benchmarks")
        self.results["relationships"] = self._benchmark_relationships()
        
        # Save results
        self._save_results()
        
        # Print summary
        self._print_summary()
        
        return self.results
        
    def _benchmark_insertion(self) -> Dict[str, Any]:
        """Benchmark document insertion performance."""
        results = {}
        
        # Test different batch sizes
        batch_sizes = [1, 10, 100, 500, 1000]
        
        for batch_size in batch_sizes:
            print(f"  Testing batch size: {batch_size}")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                kb = KnowledgeBase(
                    dimension=128,
                    data_dir=temp_dir,
                    enable_dvc=False
                )
                
                # Generate test documents
                documents = self._generate_test_documents(batch_size)
                
                # Measure insertion time
                start_time = time.time()
                kb.add(*documents)
                end_time = time.time()
                
                insertion_time = end_time - start_time
                docs_per_second = batch_size / insertion_time
                
                results[f"batch_{batch_size}"] = {
                    "total_time_ms": insertion_time * 1000,
                    "docs_per_second": docs_per_second,
                    "avg_time_per_doc_ms": (insertion_time / batch_size) * 1000
                }
                
                print(f"    {docs_per_second:.0f} docs/sec, {insertion_time*1000:.2f}ms total")
                
        return results
        
    def _benchmark_search(self) -> Dict[str, Any]:
        """Benchmark search performance and quality."""
        results = {}
        
        # Create KB with test data
        with tempfile.TemporaryDirectory() as temp_dir:
            kb = KnowledgeBase(
                dimension=128,
                data_dir=temp_dir,
                enable_dvc=False
            )
            
            # Add test documents
            test_docs = self._generate_test_documents(1000)
            kb.add(*test_docs)
            
            # Test different search scenarios
            search_queries = [
                "programming language python",
                "machine learning algorithms",
                "data structures and algorithms",
                "neural networks deep learning",
                "software engineering practices"
            ]
            
            # Benchmark search latency
            search_times = []
            for query in search_queries:
                start_time = time.time()
                result = kb.search(query, top_k=10)
                end_time = time.time()
                
                search_time = (end_time - start_time) * 1000
                search_times.append(search_time)
                
            results["search_latency"] = {
                "avg_search_time_ms": np.mean(search_times),
                "min_search_time_ms": np.min(search_times),
                "max_search_time_ms": np.max(search_times),
                "std_search_time_ms": np.std(search_times),
                "queries_tested": len(search_queries)
            }
            
            print(f"  Average search time: {np.mean(search_times):.2f}ms")
            
            # Test search quality with different top_k values
            quality_results = {}
            for top_k in [1, 5, 10, 20, 50]:
                start_time = time.time()
                result = kb.search("python programming", top_k=top_k)
                end_time = time.time()
                
                quality_results[f"top_{top_k}"] = {
                    "search_time_ms": (end_time - start_time) * 1000,
                    "results_returned": len(result.documents),
                    "avg_score": np.mean(result.scores) if result.scores else 0
                }
                
            results["search_quality"] = quality_results
            
        return results
        
    def _benchmark_memory(self) -> Dict[str, Any]:
        """Benchmark memory efficiency."""
        import psutil
        import os
        
        results = {}
        process = psutil.Process(os.getpid())
        
        # Measure memory usage with different dataset sizes
        dataset_sizes = [100, 500, 1000, 2000]
        
        for size in dataset_sizes:
            print(f"  Testing dataset size: {size}")
            
            # Measure initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            with tempfile.TemporaryDirectory() as temp_dir:
                kb = KnowledgeBase(
                    dimension=128,
                    data_dir=temp_dir,
                    enable_dvc=False
                )
                
                # Add documents
                documents = self._generate_test_documents(size)
                kb.add(*documents)
                
                # Measure memory after adding documents
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_used = final_memory - initial_memory
                memory_per_doc = memory_used / size * 1024  # KB per document
                
                results[f"size_{size}"] = {
                    "total_memory_mb": memory_used,
                    "memory_per_doc_kb": memory_per_doc,
                    "documents": size
                }
                
                print(f"    {memory_per_doc:.2f} KB/doc, {memory_used:.2f} MB total")
                
        return results
        
    def _benchmark_rollback(self) -> Dict[str, Any]:
        """Benchmark rollback performance."""
        results = {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            kb = KnowledgeBase(
                dimension=128,
                data_dir=temp_dir,
                enable_dvc=False
            )
            
            # Perform multiple operations to create rollback points
            operations = []
            for i in range(10):
                docs = self._generate_test_documents(100)
                start_time = time.time()
                kb.add(*docs)
                end_time = time.time()
                operations.append(end_time - start_time)
                
            # Test rollback performance
            rollback_times = []
            for steps in [1, 3, 5, 8]:
                if steps < len(operations):
                    start_time = time.time()
                    success = kb.roll(steps)
                    end_time = time.time()
                    
                    if success:
                        rollback_time = (end_time - start_time) * 1000
                        rollback_times.append(rollback_time)
                        
                        results[f"rollback_{steps}_steps"] = {
                            "rollback_time_ms": rollback_time,
                            "operations_per_second": steps / (rollback_time / 1000)
                        }
                        
                        print(f"  Rollback {steps} steps: {rollback_time:.2f}ms")
                        
            if rollback_times:
                results["summary"] = {
                    "avg_rollback_time_ms": np.mean(rollback_times),
                    "min_rollback_time_ms": np.min(rollback_times),
                    "max_rollback_time_ms": np.max(rollback_times)
                }
                
        return results
        
    def _benchmark_relationships(self) -> Dict[str, Any]:
        """Benchmark relationship discovery performance."""
        results = {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            kb = KnowledgeBase(
                dimension=128,
                data_dir=temp_dir,
                enable_dvc=False,
                auto_discover_relationships=True
            )
            
            # Add documents and measure relationship discovery time
            document_counts = [50, 100, 200]
            
            for count in document_counts:
                print(f"  Testing relationship discovery with {count} documents")
                
                # Generate related documents
                documents = self._generate_related_documents(count)
                
                start_time = time.time()
                kb.add(*documents)
                end_time = time.time()
                
                discovery_time = (end_time - start_time) * 1000
                stats = kb.get_stats()
                
                results[f"docs_{count}"] = {
                    "discovery_time_ms": discovery_time,
                    "relationships_found": stats.get("relationships", 0),
                    "time_per_relationship_ms": (
                        discovery_time / max(1, stats.get("relationships", 0))
                    )
                }
                
                print(f"    Found {stats.get('relationships', 0)} relationships in {discovery_time:.2f}ms")
                
        return results
        
    def _generate_test_documents(self, count: int) -> List[Document]:
        """Generate test documents for benchmarking."""
        topics = [
            "programming", "machine learning", "data science", "algorithms",
            "software engineering", "artificial intelligence", "databases",
            "web development", "mobile development", "cloud computing"
        ]
        
        documents = []
        for i in range(count):
            topic = topics[i % len(topics)]
            content = f"This is a test document about {topic}. " \
                     f"Document number {i} contains information about {topic} " \
                     f"and related concepts. It includes various technical details " \
                     f"and examples relevant to {topic} development and implementation."
            
            doc = Document(
                content=content,
                title=f"Document {i}: {topic.title()}",
                metadata={
                    "topic": topic,
                    "doc_id": i,
                    "category": "test"
                }
            )
            documents.append(doc)
            
        return documents
        
    def _generate_related_documents(self, count: int) -> List[Document]:
        """Generate documents with semantic relationships."""
        # Create clusters of related documents
        clusters = [
            {
                "topic": "python programming",
                "terms": ["python", "programming", "code", "syntax", "variables", "functions"]
            },
            {
                "topic": "machine learning",
                "terms": ["machine learning", "algorithms", "models", "training", "data", "prediction"]
            },
            {
                "topic": "web development",
                "terms": ["web", "html", "css", "javascript", "frontend", "backend"]
            }
        ]
        
        documents = []
        for i in range(count):
            cluster = clusters[i % len(clusters)]
            terms = cluster["terms"]
            
            # Use multiple terms from the cluster to create semantic similarity
            selected_terms = np.random.choice(terms, size=min(3, len(terms)), replace=False)
            
            content = f"This document discusses {cluster['topic']}. " \
                     f"Key concepts include {', '.join(selected_terms)}. " \
                     f"The document explores how {selected_terms[0]} relates to " \
                     f"{selected_terms[1] if len(selected_terms) > 1 else 'other concepts'}."
            
            doc = Document(
                content=content,
                title=f"{cluster['topic'].title()} - Document {i}",
                metadata={
                    "cluster": cluster["topic"],
                    "terms": list(selected_terms)
                }
            )
            documents.append(doc)
            
        return documents
        
    def _save_results(self) -> None:
        """Save benchmark results to file."""
        timestamp = int(time.time())
        results_file = self.output_dir / f"kb_playground_benchmark_{timestamp}.json"
        
        # Add metadata
        self.results["metadata"] = {
            "timestamp": timestamp,
            "benchmark_version": "1.0",
            "kb_playground_version": "0.1.0"
        }
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n💾 Results saved to: {results_file}")
        
    def _print_summary(self) -> None:
        """Print benchmark summary."""
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)
        
        # Insertion performance
        if "insertion" in self.results:
            batch_1000 = self.results["insertion"].get("batch_1000", {})
            if batch_1000:
                print(f"📝 Document Insertion: {batch_1000.get('docs_per_second', 0):.0f} docs/sec")
                
        # Search performance
        if "search" in self.results:
            search_latency = self.results["search"].get("search_latency", {})
            if search_latency:
                print(f"🔍 Search Latency: {search_latency.get('avg_search_time_ms', 0):.2f}ms avg")
                
        # Memory efficiency
        if "memory" in self.results:
            size_1000 = self.results["memory"].get("size_1000", {})
            if size_1000:
                print(f"💾 Memory Usage: {size_1000.get('memory_per_doc_kb', 0):.2f} KB/doc")
                
        # Rollback performance
        if "rollback" in self.results:
            rollback_summary = self.results["rollback"].get("summary", {})
            if rollback_summary:
                print(f"⏪ Rollback Speed: {rollback_summary.get('avg_rollback_time_ms', 0):.2f}ms avg")
                
        print("=" * 60)


def main():
    """Run benchmarks from command line."""
    benchmarks = PerformanceBenchmarks()
    benchmarks.run_all_benchmarks()


if __name__ == "__main__":
    main()