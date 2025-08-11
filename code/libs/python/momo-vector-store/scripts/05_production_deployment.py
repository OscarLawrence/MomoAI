"""
Production deployment patterns for momo-vector-store.

This script demonstrates:
- Production-ready configurations
- Error handling and resilience patterns
- Monitoring and observability
- Performance optimization
- Scaling strategies
"""

import asyncio
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from momo_vector_store import VectorStore
from momo_vector_store.exceptions import VectorStoreError, BackendError

# Use momo-logger as intended
try:
    from momo_logger import get_logger
    logger = get_logger("momo.vector_store.production")
except ImportError:
    # Fallback to print statements if momo-logger not available
    class FallbackLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    logger = FallbackLogger()


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""

    operation: str
    duration_ms: float
    success: bool
    document_count: int
    timestamp: str
    backend_type: str
    error_message: Optional[str] = None


class ProductionEmbeddings(Embeddings):
    """Production-ready embeddings with error handling and caching."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.dimension = 384
        self.cache = {}  # Simple in-memory cache
        self.request_count = 0

        logger.info(f"Initialized production embeddings: {model_name}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with error handling and caching."""
        self.request_count += 1
        start_time = time.time()

        try:
            embeddings = []
            cache_hits = 0

            for text in texts:
                # Check cache first
                text_hash = hash(text)
                if text_hash in self.cache:
                    embeddings.append(self.cache[text_hash])
                    cache_hits += 1
                    continue

                # Generate new embedding
                embedding = self._generate_embedding(text)
                self.cache[text_hash] = embedding
                embeddings.append(embedding)

                # Limit cache size in production
                if len(self.cache) > 10000:
                    # Remove oldest entries (simple FIFO)
                    oldest_keys = list(self.cache.keys())[:1000]
                    for key in oldest_keys:
                        del self.cache[key]

            duration = (time.time() - start_time) * 1000
            logger.info(
                f"Generated {len(embeddings)} embeddings in {duration:.2f}ms "
                f"(cache hits: {cache_hits})"
            )

            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            # Return zero vectors as fallback
            return [[0.0] * self.dimension for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        """Generate query embedding."""
        return self.embed_documents([text])[0]

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate single embedding (simulated)."""
        words = text.lower().split()
        embedding = []

        for i in range(self.dimension):
            value = 0.0
            for j, word in enumerate(words[:32]):
                word_value = hash(word + str(i)) % 1000 / 1000.0
                position_weight = 1.0 / (j + 1)
                value += word_value * position_weight

            # Normalize
            embedding.append(value / max(len(words), 1))

        return embedding

    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics."""
        return {
            "request_count": self.request_count,
            "cache_size": len(self.cache),
            "cache_hit_ratio": 0.0,  # Would calculate in real implementation
            "model_name": self.model_name,
        }


class ProductionVectorStore:
    """Production wrapper for VectorStoreManager with monitoring and resilience."""

    def __init__(self, backend_type: str = "memory", **config):
        self.backend_type = backend_type
        self.config = config
        self.metrics: List[PerformanceMetrics] = []
        self.embeddings = ProductionEmbeddings()

        # Initialize with retry logic
        self.manager = self._initialize_with_retry()

        logger.info(f"Production vector store initialized: {backend_type}")

    def _initialize_with_retry(self, max_retries: int = 3) -> VectorStore:
        """Initialize vector store with retry logic."""
        for attempt in range(max_retries):
            try:
                return VectorStore(
                    backend_type=self.backend_type,
                    embeddings=self.embeddings,
                    **self.config,
                )
            except BackendError as e:
                logger.warning(
                    f"Backend initialization attempt {attempt + 1} failed: {e}"
                )
                if attempt == max_retries - 1:
                    logger.error(
                        "All initialization attempts failed, falling back to memory"
                    )
                    return VectorStore(
                        backend_type="memory", embeddings=self.embeddings
                    )
                time.sleep(2**attempt)  # Exponential backoff

        # Should not reach here
        return VectorStore(backend_type="memory", embeddings=self.embeddings)

    async def add_documents_with_monitoring(
        self, documents: List[Document], batch_size: int = 100
    ) -> List[str]:
        """Add documents with performance monitoring and batching."""
        start_time = time.time()
        operation = "add_documents"
        success = True
        error_message = None

        try:
            # Process in batches for better performance
            all_ids = []

            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                batch_start = time.time()

                try:
                    batch_ids = await self.manager.add_documents(batch)
                    all_ids.extend(batch_ids)

                    batch_duration = (time.time() - batch_start) * 1000
                    logger.info(
                        f"Added batch {i//batch_size + 1}: "
                        f"{len(batch)} docs in {batch_duration:.2f}ms"
                    )

                except Exception as e:
                    logger.error(f"Batch {i//batch_size + 1} failed: {str(e)}")
                    success = False
                    error_message = str(e)
                    # Continue with next batch instead of failing completely

            return all_ids

        except Exception as e:
            logger.error(f"Document addition failed: {str(e)}")
            success = False
            error_message = str(e)
            raise VectorStoreError(f"Failed to add documents: {str(e)}")

        finally:
            # Record metrics
            duration = (time.time() - start_time) * 1000
            metric = PerformanceMetrics(
                operation=operation,
                duration_ms=duration,
                success=success,
                document_count=len(documents),
                timestamp=datetime.now().isoformat(),
                backend_type=self.backend_type,
                error_message=error_message,
            )
            self.metrics.append(metric)

            # Log performance
            logger.info(
                f"Operation {operation}: {duration:.2f}ms, "
                f"success: {success}, docs: {len(documents)}"
            )

    async def search_with_monitoring(
        self,
        query: str,
        k: int = 10,
        filter: Optional[Dict] = None,
        timeout: float = 5.0,
    ) -> List[Document]:
        """Search with monitoring and timeout."""
        start_time = time.time()
        operation = "similarity_search"
        success = True
        error_message = None

        try:
            # Add timeout using asyncio
            search_task = self.manager.search(query, k=k, filter=filter)
            results = await asyncio.wait_for(search_task, timeout=timeout)

            logger.info(
                f"Search returned {len(results)} results for query: '{query[:50]}...'"
            )
            return results

        except asyncio.TimeoutError:
            error_message = f"Search timeout after {timeout}s"
            logger.error(error_message)
            success = False
            raise VectorStoreError(error_message)

        except Exception as e:
            error_message = str(e)
            logger.error(f"Search failed: {error_message}")
            success = False
            raise VectorStoreError(f"Search failed: {error_message}")

        finally:
            duration = (time.time() - start_time) * 1000
            metric = PerformanceMetrics(
                operation=operation,
                duration_ms=duration,
                success=success,
                document_count=k,
                timestamp=datetime.now().isoformat(),
                backend_type=self.backend_type,
                error_message=error_message,
            )
            self.metrics.append(metric)

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        recent_metrics = self.metrics[-100:]  # Last 100 operations

        if not recent_metrics:
            return {"status": "unknown", "message": "No metrics available"}

        success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
        avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)

        backend_info = self.manager.get_info()
        embedding_stats = self.embeddings.get_stats()

        return {
            "status": (
                "healthy"
                if success_rate > 0.95
                else "degraded"
                if success_rate > 0.8
                else "unhealthy"
            ),
            "success_rate": success_rate,
            "avg_response_time_ms": avg_duration,
            "total_operations": len(self.metrics),
            "backend_info": backend_info,
            "embedding_stats": embedding_stats,
            "uptime_seconds": time.time()
            - (self.metrics[0].timestamp if self.metrics else time.time()),
        }

    def export_metrics(self, filepath: str = "vector_store_metrics.json"):
        """Export metrics to file for analysis."""
        metrics_data = [asdict(metric) for metric in self.metrics]

        with open(filepath, "w") as f:
            json.dump(
                {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_metrics": len(metrics_data),
                    "metrics": metrics_data,
                },
                f,
                indent=2,
            )

        logger.info(f"Exported {len(metrics_data)} metrics to {filepath}")


class ProductionOrchestrator:
    """Production orchestrator for managing multiple vector stores."""

    def __init__(self):
        self.stores: Dict[str, ProductionVectorStore] = {}
        self.load_balancer_index = 0

    def add_store(self, name: str, store: ProductionVectorStore):
        """Add a vector store to the orchestrator."""
        self.stores[name] = store
        logger.info(f"Added vector store: {name}")

    async def distributed_search(
        self, query: str, k_per_store: int = 5
    ) -> Dict[str, List[Document]]:
        """Perform distributed search across multiple stores."""
        logger.info(f"Distributed search: '{query}' across {len(self.stores)} stores")

        tasks = {}
        for name, store in self.stores.items():
            tasks[name] = store.search_with_monitoring(query, k=k_per_store)

        # Execute searches concurrently
        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
                logger.info(f"Store {name}: {len(results[name])} results")
            except Exception as e:
                logger.error(f"Store {name} search failed: {e}")
                results[name] = []

        return results

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health across all stores."""
        store_healths = {}
        overall_status = "healthy"

        for name, store in self.stores.items():
            health = store.get_health_status()
            store_healths[name] = health

            if health["status"] == "unhealthy":
                overall_status = "unhealthy"
            elif health["status"] == "degraded" and overall_status == "healthy":
                overall_status = "degraded"

        return {
            "overall_status": overall_status,
            "store_count": len(self.stores),
            "store_healths": store_healths,
        }


async def demonstrate_production_config():
    """Demonstrate production configuration patterns."""
    print("\n🏭 Production Configuration Patterns")
    print("-" * 40)

    print("1. Memory Backend (Development/Testing):")
    dev_store = ProductionVectorStore("memory")
    print(f"   ✅ Initialized: {dev_store.backend_type}")

    print("\n2. Production Backend Configurations:")

    # These would work if the backends were installed
    production_configs = {
        "chroma_persistent": {
            "backend_type": "chroma",
            "collection_name": "production_knowledge",
            "persist_directory": "/data/vector_db/chroma",
            # "client_settings": {"host": "chroma.production.com", "port": 8000}
        },
        "weaviate_cluster": {
            "backend_type": "weaviate",
            "url": "https://vector-cluster.company.com",
            "index_name": "ProductionIndex",
            # "api_key": os.getenv("WEAVIATE_API_KEY")
        },
    }

    for name, config in production_configs.items():
        print(f"   🔧 {name}:")
        print(f"      Backend: {config['backend_type']}")
        for key, value in config.items():
            if key != "backend_type":
                print(f"      {key}: {value}")

    return dev_store


async def demonstrate_monitoring_and_metrics():
    """Demonstrate monitoring and metrics collection."""
    print("\n📊 Monitoring and Metrics")
    print("-" * 40)

    store = ProductionVectorStore("memory")

    # Generate sample data and operations
    sample_docs = []
    for i in range(50):
        doc = Document(
            page_content=f"Production document {i+1}. This document contains important "
            f"business information and technical details for monitoring demo.",
            metadata={
                "doc_id": f"prod_{i+1:03d}",
                "category": "business" if i % 2 == 0 else "technical",
                "priority": "high" if i < 10 else "medium",
                "created": datetime.now().isoformat(),
            },
        )
        sample_docs.append(doc)

    print("🔄 Performing monitored operations...")

    # Add documents with monitoring
    await store.add_documents_with_monitoring(sample_docs, batch_size=20)

    # Perform searches with monitoring
    search_queries = [
        "business information analysis",
        "technical documentation details",
        "production system monitoring",
        "performance metrics data",
    ]

    for query in search_queries:
        try:
            results = await store.search_with_monitoring(query, k=5, timeout=2.0)
            print(f"   Search '{query[:30]}...': {len(results)} results")
        except Exception as e:
            print(f"   Search failed: {e}")

    # Get health status
    print("\n📈 Health Status:")
    health = store.get_health_status()
    print(f"   Status: {health['status']}")
    print(f"   Success Rate: {health['success_rate']:.2%}")
    print(f"   Avg Response Time: {health['avg_response_time_ms']:.2f}ms")
    print(f"   Total Operations: {health['total_operations']}")

    # Export metrics
    store.export_metrics("demo_metrics.json")
    print("   ✅ Metrics exported to demo_metrics.json")

    return store


async def demonstrate_error_handling():
    """Demonstrate production error handling patterns."""
    print("\n🛡️  Production Error Handling")
    print("-" * 40)

    store = ProductionVectorStore("memory")

    # Test timeout handling
    print("1. Timeout Handling:")
    try:
        # Simulate slow search with very short timeout
        await store.search_with_monitoring("test query", k=5, timeout=0.001)
    except VectorStoreError as e:
        print(f"   ✅ Timeout handled gracefully: {str(e)[:50]}...")

    # Test invalid document handling
    print("\n2. Invalid Document Handling:")
    invalid_docs = [
        Document(page_content="", metadata={"invalid": True}),  # Empty content
        Document(page_content="Valid document", metadata={"valid": True}),
    ]

    try:
        await store.add_documents_with_monitoring(invalid_docs)
        print("   ✅ Handled invalid documents in batch")
    except Exception as e:
        print(f"   ⚠️  Error handling: {str(e)[:50]}...")

    # Test backend failure simulation
    print("\n3. Backend Resilience:")
    print("   💡 In production:")
    print("      - Use connection pooling")
    print("      - Implement circuit breakers")
    print("      - Add retry logic with exponential backoff")
    print("      - Monitor backend health")
    print("      - Have fallback strategies")


async def demonstrate_scaling_patterns():
    """Demonstrate scaling patterns and load distribution."""
    print("\n⚡ Scaling and Load Distribution")
    print("-" * 40)

    # Create multiple stores to simulate scaling
    orchestrator = ProductionOrchestrator()

    # Add multiple stores (in production, these might be different backends/regions)
    for i in range(3):
        store = ProductionVectorStore("memory")

        # Add different document sets to each store
        docs = []
        for j in range(20):
            doc = Document(
                page_content=f"Store {i+1} document {j+1}. Specialized content for "
                f"distributed search and load balancing demonstration.",
                metadata={
                    "store_id": i + 1,
                    "doc_id": f"store{i+1}_{j+1:02d}",
                    "shard": f"shard_{i+1}",
                },
            )
            docs.append(doc)

        await store.add_documents_with_monitoring(docs, batch_size=10)
        orchestrator.add_store(f"store_{i+1}", store)

    print(f"🏗️  Created distributed system with {len(orchestrator.stores)} stores")

    # Demonstrate distributed search
    print("\n🔍 Distributed Search:")
    distributed_results = await orchestrator.distributed_search(
        "specialized content distribution", k_per_store=3
    )

    total_results = 0
    for store_name, results in distributed_results.items():
        print(f"   {store_name}: {len(results)} results")
        total_results += len(results)

    print(f"   Total results: {total_results}")

    # Get overall health
    print("\n❤️  System Health:")
    overall_health = orchestrator.get_overall_health()
    print(f"   Overall Status: {overall_health['overall_status']}")
    print(f"   Store Count: {overall_health['store_count']}")

    for store_name, health in overall_health["store_healths"].items():
        print(
            f"   {store_name}: {health['status']} "
            f"({health['success_rate']:.1%} success)"
        )


async def demonstrate_production_best_practices():
    """Demonstrate production best practices."""
    print("\n🎯 Production Best Practices")
    print("-" * 40)

    print("1. Configuration Management:")
    print("   ✅ Use environment variables for sensitive config")
    print("   ✅ Separate configs for dev/staging/production")
    print("   ✅ Version your configuration files")

    print("\n2. Security:")
    print("   ✅ Encrypt data at rest and in transit")
    print("   ✅ Use proper authentication and authorization")
    print("   ✅ Regular security audits and updates")
    print("   ✅ Network isolation and firewalls")

    print("\n3. Monitoring and Alerting:")
    print("   ✅ Set up health checks and heartbeats")
    print("   ✅ Monitor key metrics (latency, throughput, errors)")
    print("   ✅ Alert on threshold breaches")
    print("   ✅ Dashboard for real-time visibility")

    print("\n4. Disaster Recovery:")
    print("   ✅ Regular backups and backup validation")
    print("   ✅ Multi-region deployment for high availability")
    print("   ✅ Documented recovery procedures")
    print("   ✅ Regular disaster recovery testing")

    print("\n5. Performance Optimization:")
    print("   ✅ Connection pooling and reuse")
    print("   ✅ Caching strategies at multiple levels")
    print("   ✅ Load balancing and auto-scaling")
    print("   ✅ Performance profiling and optimization")

    print("\n6. Deployment Strategy:")
    print("   ✅ Blue-green deployments for zero downtime")
    print("   ✅ Canary releases for risk mitigation")
    print("   ✅ Automated testing in CI/CD pipeline")
    print("   ✅ Rollback procedures and feature flags")


async def main():
    """Run the production deployment demonstration."""
    print("🏭 Production Deployment Patterns")
    print("=" * 50)

    store = await demonstrate_production_config()
    await demonstrate_monitoring_and_metrics()
    await demonstrate_error_handling()
    await demonstrate_scaling_patterns()
    await demonstrate_production_best_practices()

    print("\n✅ Production deployment demonstration completed!")
    print("\nProduction Readiness Checklist:")
    print("- ✅ Error handling and resilience")
    print("- ✅ Performance monitoring and metrics")
    print("- ✅ Health checks and observability")
    print("- ✅ Scaling and load distribution")
    print("- ✅ Security and configuration management")
    print("- ✅ Disaster recovery planning")

    # Final health check
    final_health = store.get_health_status()
    print(f"\n📊 Final System Health: {final_health['status']}")


if __name__ == "__main__":
    asyncio.run(main())
