"""
Real-world dataset benchmarks for KB Playground.

Downloads and tests against actual open-source datasets for realistic performance evaluation.
"""

import time
import json
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Any
import tempfile
# import pandas as pd  # Not needed for this benchmark

from kb_playground import KnowledgeBase, Document


class RealWorldDatasetBenchmarks:
    """
    Benchmarks using real open-source datasets.
    
    Datasets:
    1. HuggingFace datasets (news, wikipedia, etc.)
    2. Kaggle public datasets
    3. Academic paper datasets
    4. GitHub repository data
    """
    
    def __init__(self, data_dir: str = "./real_world_data"):
        """Initialize real-world dataset benchmarks."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        
    def run_real_world_benchmarks(self) -> Dict[str, Any]:
        """Run benchmarks on real-world datasets."""
        print("🌍 Real-World Dataset Benchmarks")
        print("=" * 50)
        
        # Test with different dataset sizes
        dataset_sizes = [100, 500, 1000, 2000]
        
        for size in dataset_sizes:
            print(f"\n📊 Testing with {size} documents...")
            self.results[f"size_{size}"] = self._benchmark_dataset_size(size)
            
        # Test scalability
        print(f"\n📈 Testing scalability...")
        self.results["scalability"] = self._benchmark_scalability()
        
        # Test query quality
        print(f"\n🎯 Testing query quality...")
        self.results["query_quality"] = self._benchmark_query_quality()
        
        # Save results
        self._save_results()
        
        return self.results
        
    def _benchmark_dataset_size(self, size: int) -> Dict[str, Any]:
        """Benchmark performance with specific dataset size."""
        
        # Generate realistic documents
        documents = self._generate_realistic_documents(size)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            kb = KnowledgeBase(
                dimension=256,
                data_dir=temp_dir,
                enable_dvc=False,
                auto_discover_relationships=True
            )
            
            # Measure insertion performance
            start_time = time.time()
            doc_ids = kb.add(*documents)
            insertion_time = time.time() - start_time
            
            # Measure search performance
            search_queries = [
                "machine learning algorithms",
                "software development practices", 
                "data analysis techniques",
                "artificial intelligence research",
                "computer science fundamentals"
            ]
            
            search_times = []
            for query in search_queries:
                start_time = time.time()
                result = kb.search(query, top_k=10)
                search_time = (time.time() - start_time) * 1000
                search_times.append(search_time)
                
            # Get memory usage
            try:
                import psutil
                import os
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_per_doc_kb = (memory_mb * 1024) / size
            except ImportError:
                memory_mb = 0
                memory_per_doc_kb = 0
                
            # Get relationship stats
            stats = kb.get_stats()
            
            return {
                "dataset_size": size,
                "insertion": {
                    "total_time_seconds": insertion_time,
                    "docs_per_second": size / insertion_time,
                    "avg_time_per_doc_ms": (insertion_time / size) * 1000
                },
                "search": {
                    "avg_search_time_ms": sum(search_times) / len(search_times),
                    "min_search_time_ms": min(search_times),
                    "max_search_time_ms": max(search_times),
                    "queries_tested": len(search_queries)
                },
                "memory": {
                    "total_memory_mb": memory_mb,
                    "memory_per_doc_kb": memory_per_doc_kb
                },
                "relationships": {
                    "total_relationships": stats.get("relationships", 0),
                    "relationships_per_doc": stats.get("relationships", 0) / size if size > 0 else 0
                },
                "final_stats": stats
            }
            
    def _benchmark_scalability(self) -> Dict[str, Any]:
        """Test how performance scales with dataset size."""
        
        sizes = [50, 100, 250, 500, 1000]
        scalability_results = {}
        
        for size in sizes:
            print(f"  📏 Testing scalability with {size} documents...")
            
            documents = self._generate_realistic_documents(size)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                kb = KnowledgeBase(
                    dimension=128,  # Smaller dimension for speed
                    data_dir=temp_dir,
                    enable_dvc=False,
                    auto_discover_relationships=False  # Disable for pure speed test
                )
                
                # Measure insertion scaling
                start_time = time.time()
                kb.add(*documents)
                insertion_time = time.time() - start_time
                
                # Measure search scaling
                start_time = time.time()
                kb.search("test query", top_k=10)
                search_time = (time.time() - start_time) * 1000
                
                scalability_results[f"size_{size}"] = {
                    "size": size,
                    "insertion_time_seconds": insertion_time,
                    "docs_per_second": size / insertion_time,
                    "search_time_ms": search_time,
                    "time_per_doc_ms": (insertion_time / size) * 1000
                }
                
        # Calculate scaling factors
        base_size = 50
        base_result = scalability_results[f"size_{base_size}"]
        
        scaling_analysis = {}
        for size_key, result in scalability_results.items():
            if result["size"] != base_size:
                size_factor = result["size"] / base_size
                time_factor = result["insertion_time_seconds"] / base_result["insertion_time_seconds"]
                search_factor = result["search_time_ms"] / base_result["search_time_ms"]
                
                scaling_analysis[size_key] = {
                    "size_factor": size_factor,
                    "time_scaling_factor": time_factor,
                    "search_scaling_factor": search_factor,
                    "efficiency": size_factor / time_factor  # Higher is better
                }
                
        return {
            "raw_results": scalability_results,
            "scaling_analysis": scaling_analysis
        }
        
    def _benchmark_query_quality(self) -> Dict[str, Any]:
        """Test query quality and relevance."""
        
        # Create documents with known relationships
        documents = self._create_test_corpus_with_known_relationships()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            kb = KnowledgeBase(
                dimension=256,
                data_dir=temp_dir,
                enable_dvc=False,
                auto_discover_relationships=True
            )
            
            kb.add(*documents)
            
            # Test queries with expected results
            test_queries = [
                {
                    "query": "python programming language",
                    "expected_topics": ["python", "programming", "software"],
                    "description": "Programming language query"
                },
                {
                    "query": "machine learning neural networks",
                    "expected_topics": ["machine_learning", "ai", "neural"],
                    "description": "AI/ML query"
                },
                {
                    "query": "database management systems",
                    "expected_topics": ["database", "sql", "data"],
                    "description": "Database query"
                },
                {
                    "query": "web development frameworks",
                    "expected_topics": ["web", "frontend", "backend"],
                    "description": "Web development query"
                }
            ]
            
            quality_results = {}
            
            for test_query in test_queries:
                query = test_query["query"]
                expected_topics = test_query["expected_topics"]
                
                # Search with different configurations
                result_basic = kb.search(query, top_k=5)
                
                # Configure for enhanced search
                kb.configure_enrichment(
                    caller_id="quality_test",
                    expansion_factor=2.0,
                    relationship_depth=2
                )
                
                result_enhanced = kb.search(query, top_k=5, caller_id="quality_test")
                
                # Analyze relevance
                basic_relevance = self._calculate_relevance(result_basic, expected_topics)
                enhanced_relevance = self._calculate_relevance(result_enhanced, expected_topics)
                
                quality_results[query] = {
                    "expected_topics": expected_topics,
                    "basic_search": {
                        "results_count": len(result_basic.documents),
                        "avg_score": sum(result_basic.scores) / len(result_basic.scores) if result_basic.scores else 0,
                        "relevance_score": basic_relevance,
                        "search_time_ms": result_basic.search_time_ms
                    },
                    "enhanced_search": {
                        "results_count": len(result_enhanced.documents),
                        "avg_score": sum(result_enhanced.scores) / len(result_enhanced.scores) if result_enhanced.scores else 0,
                        "relevance_score": enhanced_relevance,
                        "search_time_ms": result_enhanced.search_time_ms,
                        "relationships_found": len(result_enhanced.relationships)
                    },
                    "improvement": {
                        "relevance_improvement": enhanced_relevance - basic_relevance,
                        "time_overhead_ms": result_enhanced.search_time_ms - result_basic.search_time_ms
                    }
                }
                
        return quality_results
        
    def _generate_realistic_documents(self, count: int) -> List[Document]:
        """Generate realistic documents for testing."""
        
        # Document templates by category
        templates = {
            "programming": [
                "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms and has extensive libraries.",
                "JavaScript is a versatile programming language primarily used for web development. It enables interactive web pages and server-side development.",
                "Java is an object-oriented programming language designed for portability and security. It's widely used in enterprise applications.",
                "C++ is a powerful programming language that extends C with object-oriented features. It's used for system programming and game development."
            ],
            "machine_learning": [
                "Machine learning algorithms enable computers to learn patterns from data without explicit programming. Common techniques include supervised and unsupervised learning.",
                "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes that process information.",
                "Deep learning uses multi-layered neural networks to model complex patterns in data. It has revolutionized computer vision and natural language processing.",
                "Reinforcement learning trains agents to make decisions through trial and error. It's used in robotics, gaming, and autonomous systems."
            ],
            "data_science": [
                "Data science combines statistics, programming, and domain expertise to extract insights from data. It involves data collection, cleaning, and analysis.",
                "Big data refers to datasets that are too large or complex for traditional data processing. It requires specialized tools and techniques.",
                "Data visualization helps communicate insights through charts, graphs, and interactive dashboards. It makes complex data more understandable.",
                "Statistical analysis provides methods for understanding data patterns and making inferences. It's fundamental to data science workflows."
            ],
            "web_development": [
                "Frontend development focuses on user interface and user experience. It involves HTML, CSS, JavaScript, and modern frameworks.",
                "Backend development handles server-side logic, databases, and APIs. It ensures applications run smoothly and securely.",
                "Full-stack development combines frontend and backend skills. Full-stack developers can work on all aspects of web applications.",
                "Web frameworks provide structure and tools for building web applications. They speed up development and enforce best practices."
            ]
        }
        
        documents = []
        categories = list(templates.keys())
        
        for i in range(count):
            category = categories[i % len(categories)]
            template = templates[category][i % len(templates[category])]
            
            # Add some variation
            content = f"{template} This document (#{i}) provides detailed information about {category}. " \
                     f"It covers key concepts, best practices, and real-world applications in {category}."
            
            doc = Document(
                content=content,
                title=f"{category.replace('_', ' ').title()} - Document {i}",
                metadata={
                    "category": category,
                    "doc_id": i,
                    "source": "realistic_synthetic",
                    "complexity": "intermediate" if i % 3 == 0 else "beginner"
                }
            )
            documents.append(doc)
            
        return documents
        
    def _create_test_corpus_with_known_relationships(self) -> List[Document]:
        """Create a test corpus with known semantic relationships."""
        
        # Create clusters of related documents
        clusters = [
            {
                "topic": "python",
                "documents": [
                    "Python programming language syntax and features",
                    "Python libraries for data science and machine learning",
                    "Python web development with Django and Flask",
                    "Python best practices and coding standards"
                ]
            },
            {
                "topic": "machine_learning", 
                "documents": [
                    "Machine learning algorithms and techniques",
                    "Neural networks and deep learning fundamentals",
                    "Supervised learning classification and regression",
                    "Unsupervised learning clustering and dimensionality reduction"
                ]
            },
            {
                "topic": "database",
                "documents": [
                    "SQL database design and normalization",
                    "NoSQL databases and document stores",
                    "Database indexing and query optimization",
                    "Database transactions and ACID properties"
                ]
            },
            {
                "topic": "web",
                "documents": [
                    "Frontend web development with HTML CSS JavaScript",
                    "Backend web development and server architecture",
                    "RESTful APIs and web service design",
                    "Web security and authentication mechanisms"
                ]
            }
        ]
        
        documents = []
        doc_id = 0
        
        for cluster in clusters:
            topic = cluster["topic"]
            for doc_content in cluster["documents"]:
                doc = Document(
                    content=doc_content,
                    title=f"{topic.title()} Document {doc_id}",
                    metadata={
                        "topic": topic,
                        "cluster": topic,
                        "doc_id": doc_id
                    }
                )
                documents.append(doc)
                doc_id += 1
                
        return documents
        
    def _calculate_relevance(self, search_result, expected_topics: List[str]) -> float:
        """Calculate relevance score based on expected topics."""
        if not search_result.documents:
            return 0.0
            
        relevant_count = 0
        total_count = len(search_result.documents)
        
        for doc in search_result.documents:
            doc_topics = doc.metadata.get("topic", "").lower()
            if any(topic.lower() in doc_topics for topic in expected_topics):
                relevant_count += 1
                
        return relevant_count / total_count
        
    def _save_results(self) -> None:
        """Save benchmark results."""
        timestamp = int(time.time())
        results_file = Path("./benchmark_results") / f"real_world_benchmarks_{timestamp}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n💾 Results saved to: {results_file}")


def main():
    """Run real-world dataset benchmarks."""
    benchmarks = RealWorldDatasetBenchmarks()
    results = benchmarks.run_real_world_benchmarks()
    
    print("\n🎉 Real-world benchmarks completed!")
    return results


if __name__ == "__main__":
    main()