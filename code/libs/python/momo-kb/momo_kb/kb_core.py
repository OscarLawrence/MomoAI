"""
Core KnowledgeBase implementation with pluggable backends.

Provides low-level backend management and coordination.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import importlib

from .unified_models import Document, Relationship, SearchResult, KnowledgeBaseStats


class BackendInterface:
    """Abstract interface that all backends must implement."""

    async def initialize(self) -> None:
        """Initialize the backend."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close the backend and cleanup resources."""
        raise NotImplementedError

    async def insert_document(self, doc: Document) -> str:
        """Insert a document and return backend-specific ID."""
        raise NotImplementedError

    async def insert_relationship(self, rel: Relationship) -> str:
        """Insert a relationship and return backend-specific ID."""
        raise NotImplementedError

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by unified ID."""
        raise NotImplementedError

    async def delete_relationship(self, rel_id: str) -> bool:
        """Delete a relationship by unified ID."""
        raise NotImplementedError

    async def search(
        self, query: str, filters: Optional[Dict] = None, top_k: int = 10
    ) -> SearchResult:
        """Search for documents and relationships."""
        raise NotImplementedError

    async def rollback(self, steps: int) -> None:
        """Rollback the last N operations."""
        raise NotImplementedError

    async def get_stats(self) -> Dict[str, Any]:
        """Get backend-specific statistics."""
        raise NotImplementedError


class KnowledgeBaseCore:
    """
    Low-level backend management and coordination.

    Handles backend loading, operation routing, and consistency management.
    """

    def __init__(self, backends: List[str] = None):
        self.backends: Dict[str, BackendInterface] = {}
        self.backend_names = backends or ["graph"]
        self._initialized = False
        self._operation_history: List[Dict[str, Any]] = []
        self._created_at = datetime.utcnow()

    async def initialize(self) -> None:
        """Initialize all configured backends."""
        await self._load_backends()
        self._initialized = True

    async def close(self) -> None:
        """Close all backends and cleanup resources."""
        for backend in self.backends.values():
            await backend.close()
        self._initialized = False

    async def _load_backends(self) -> None:
        """Load and initialize all configured backends."""
        for backend_name in self.backend_names:
            backend = await self._create_backend(backend_name)
            await backend.initialize()
            self.backends[backend_name] = backend

    async def _create_backend(self, backend_name: str) -> BackendInterface:
        """Create a backend instance by name."""
        if backend_name == "graph":
            from .graph_backend_adapter import GraphBackendAdapter

            return GraphBackendAdapter()
        else:
            raise ValueError(f"Unknown backend: {backend_name}")

    async def _route_insert(
        self, item: Union[Document, Relationship]
    ) -> Dict[str, str]:
        """Route insert operation to appropriate backends."""
        backend_ids = {}

        # For now, route to all backends (simple strategy)
        for backend_name, backend in self.backends.items():
            try:
                if isinstance(item, Document):
                    backend_id = await backend.insert_document(item)
                else:  # Relationship
                    backend_id = await backend.insert_relationship(item)
                backend_ids[backend_name] = backend_id
            except Exception as e:
                # Log error but continue with other backends
                print(f"Backend {backend_name} insert failed: {e}")

        return backend_ids

    async def _route_delete(self, item_id: str, item_type: str) -> Dict[str, bool]:
        """Route delete operation to all backends."""
        results = {}

        for backend_name, backend in self.backends.items():
            try:
                if item_type == "document":
                    result = await backend.delete_document(item_id)
                else:  # relationship
                    result = await backend.delete_relationship(item_id)
                results[backend_name] = result
            except Exception as e:
                print(f"Backend {backend_name} delete failed: {e}")
                results[backend_name] = False

        return results

    async def _route_search(
        self, query: str, filters: Optional[Dict] = None, top_k: int = 10
    ) -> SearchResult:
        """Route search to appropriate backends and merge results."""
        all_results = []
        backends_used = []
        total_time = 0.0

        # For now, search all backends and merge results
        for backend_name, backend in self.backends.items():
            try:
                result = await backend.search(query, filters, top_k)
                all_results.append(result)
                backends_used.append(backend_name)
                total_time += result.search_time_ms
            except Exception as e:
                print(f"Backend {backend_name} search failed: {e}")

        # Merge results (simple concatenation for now)
        merged_docs = []
        merged_rels = []
        merged_scores = []

        for result in all_results:
            merged_docs.extend(result.documents)
            merged_rels.extend(result.relationships)
            merged_scores.extend(result.scores)

        return SearchResult(
            documents=merged_docs,
            relationships=merged_rels,
            query=query,
            total_results=len(merged_docs) + len(merged_rels),
            search_time_ms=total_time,
            backends_used=backends_used,
            scores=merged_scores,
        )

    async def _coordinated_rollback(self, steps: int) -> None:
        """Perform coordinated rollback across all backends."""
        # Record rollback operation
        operation = {
            "type": "rollback",
            "steps": steps,
            "timestamp": datetime.utcnow(),
            "backends": list(self.backends.keys()),
        }

        # Execute rollback on all backends
        rollback_results = {}
        for backend_name, backend in self.backends.items():
            try:
                await backend.rollback(steps)
                rollback_results[backend_name] = True
            except Exception as e:
                print(f"Backend {backend_name} rollback failed: {e}")
                rollback_results[backend_name] = False

        operation["results"] = rollback_results
        self._operation_history.append(operation)

        # Remove rolled-back operations from history
        if steps > 0 and len(self._operation_history) > steps:
            self._operation_history = self._operation_history[:-steps]

    def _record_operation(self, operation_type: str, **kwargs) -> None:
        """Record an operation in the history."""
        operation = {"type": operation_type, "timestamp": datetime.utcnow(), **kwargs}
        self._operation_history.append(operation)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
