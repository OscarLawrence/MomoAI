"""
Core KnowledgeBase implementation with immutable operations and rollback.

Implements the main KB interface with diff-based versioning and 3-tier storage.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .models import Node, Edge, Diff, DiffType, QueryResult
from .storage import StorageTier, ThreeTierStorage


class KnowledgeBase:
    """
    High-performance, multi-agent, immutable knowledge graph.

    Features:
    - Immutable operations (INSERT/DELETE only)
    - Diff-based rollback system
    - 3-tier storage with automatic pruning
    - Agent-optimized query pipeline
    """

    def __init__(self):
        self._storage = ThreeTierStorage()
        self._diff_history: List[Diff] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the knowledge base."""
        self._initialized = True

    async def close(self) -> None:
        """Close the knowledge base and cleanup resources."""
        self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False

    async def count_nodes(self, tier: Optional[str] = None) -> int:
        """Count nodes across all tiers or in a specific tier."""
        if tier is None:
            total = 0
            for storage_tier in [
                StorageTier.RUNTIME,
                StorageTier.STORE,
                StorageTier.COLD,
            ]:
                total += self._storage.count_nodes(storage_tier)
            return total
        else:
            return self._storage.count_nodes(StorageTier(tier))

    async def count_edges(self, tier: Optional[str] = None) -> int:
        """Count edges across all tiers or in a specific tier."""
        if tier is None:
            total = 0
            for storage_tier in [
                StorageTier.RUNTIME,
                StorageTier.STORE,
                StorageTier.COLD,
            ]:
                total += self._storage.count_edges(storage_tier)
            return total
        else:
            return self._storage.count_edges(StorageTier(tier))

    async def insert_node(self, node: Node) -> Diff:
        """Insert a node and create diff record."""
        # Add to runtime tier (hottest)
        self._storage.add_node(node, StorageTier.RUNTIME)

        # Create diff record
        diff = Diff(operation=DiffType.INSERT_NODE, node=node)
        self._diff_history.append(diff)

        return diff

    async def insert_edge(self, edge: Edge) -> Diff:
        """Insert an edge and create diff record."""
        # Add to runtime tier (hottest)
        self._storage.add_edge(edge, StorageTier.RUNTIME)

        # Create diff record
        diff = Diff(operation=DiffType.INSERT_EDGE, edge=edge)
        self._diff_history.append(diff)

        return diff

    async def delete_node(self, node_id: str) -> Diff:
        """Delete a node and create diff record."""
        # Find the node across all tiers
        node = self._storage.find_node(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found")

        # Remove from all tiers
        for tier in [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]:
            self._storage.remove_node(node_id, tier)

        # Create diff record
        diff = Diff(operation=DiffType.DELETE_NODE, node=node)
        self._diff_history.append(diff)

        return diff

    async def delete_edge(self, edge_id: str) -> Diff:
        """Delete an edge and create diff record."""
        # Find the edge across all tiers
        edge = self._storage.find_edge(edge_id)
        if edge is None:
            raise ValueError(f"Edge {edge_id} not found")

        # Remove from all tiers
        for tier in [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]:
            self._storage.remove_edge(edge_id, tier)

        # Create diff record
        diff = Diff(operation=DiffType.DELETE_EDGE, edge=edge)
        self._diff_history.append(diff)

        return diff

    async def get_diff_history(self) -> List[Diff]:
        """Get the complete diff history."""
        return self._diff_history.copy()

    async def rollback(self, steps: int) -> None:
        """Rollback the last N operations by applying reverse diffs."""
        if steps <= 0:
            return

        # Get the last N diffs to reverse
        diffs_to_reverse = self._diff_history[-steps:]

        # Apply reverse diffs in reverse order
        for diff in reversed(diffs_to_reverse):
            reverse_diff = diff.reverse()
            await self._apply_diff(reverse_diff)
            self._diff_history.append(reverse_diff)

    async def rollback_to_timestamp(self, timestamp: datetime) -> None:
        """Rollback to a specific timestamp."""
        # Find diffs after the timestamp
        diffs_to_reverse = []
        for diff in reversed(self._diff_history):
            if diff.timestamp > timestamp:
                diffs_to_reverse.append(diff)
            else:
                break

        # Apply reverse diffs
        for diff in diffs_to_reverse:
            reverse_diff = diff.reverse()
            await self._apply_diff(reverse_diff)
            self._diff_history.append(reverse_diff)

    async def _apply_diff(self, diff: Diff) -> None:
        """Apply a diff operation to the storage."""
        if diff.operation == DiffType.INSERT_NODE and diff.node:
            self._storage.add_node(diff.node, StorageTier.RUNTIME)
        elif diff.operation == DiffType.DELETE_NODE and diff.node:
            for tier in [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]:
                self._storage.remove_node(diff.node.id, tier)
        elif diff.operation == DiffType.INSERT_EDGE and diff.edge:
            self._storage.add_edge(diff.edge, StorageTier.RUNTIME)
        elif diff.operation == DiffType.DELETE_EDGE and diff.edge:
            for tier in [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]:
                self._storage.remove_edge(diff.edge.id, tier)

    async def query_nodes(
        self, label: Optional[str] = None, properties: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Query nodes by label and/or properties using high-performance indexes."""
        start_time = datetime.utcnow()
        matching_nodes = []
        storage_tier = "runtime"

        # Use indexed queries across all tiers (runtime first for performance)
        for tier in [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]:
            # Fast indexed query
            nodes = self._storage.query_nodes_indexed(
                tier, label=label, properties=properties
            )

            # Update access tracking for found nodes
            updated_nodes = []
            for node in nodes:
                updated_node = node.with_access()
                self._storage.add_node(updated_node, tier)
                updated_nodes.append(updated_node)

            matching_nodes.extend(updated_nodes)
            if updated_nodes and tier != StorageTier.RUNTIME:
                storage_tier = tier.value

        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return QueryResult(
            nodes=matching_nodes, query_time_ms=query_time, storage_tier=storage_tier
        )

    async def query_edges(
        self,
        relationship: Optional[str] = None,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """Query edges by relationship type and/or node IDs using high-performance indexes."""
        start_time = datetime.utcnow()
        matching_edges = []
        storage_tier = "runtime"

        # Use indexed queries across all tiers
        for tier in [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]:
            # Fast indexed query
            edges = self._storage.query_edges_indexed(
                tier,
                relationship=relationship,
                source_id=source_id,
                target_id=target_id,
                properties=properties,
            )

            # Update access tracking for found edges
            updated_edges = []
            for edge in edges:
                updated_edge = edge.with_access()
                self._storage.add_edge(updated_edge, tier)
                updated_edges.append(updated_edge)

            matching_edges.extend(updated_edges)
            if updated_edges and tier != StorageTier.RUNTIME:
                storage_tier = tier.value

        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return QueryResult(
            edges=matching_edges, query_time_ms=query_time, storage_tier=storage_tier
        )

    async def query_connected_nodes(
        self,
        start_node_id: str,
        relationship: str,
        direction: str = "outgoing",  # "outgoing", "incoming", "both"
    ) -> QueryResult:
        """Query nodes connected to a start node via specific relationship using indexes."""
        start_time = datetime.utcnow()
        connected_nodes = []
        storage_tier = "runtime"

        # Use fast indexed traversal across all tiers
        for tier in [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]:
            # Fast indexed query for connected nodes
            nodes = self._storage.query_connected_nodes_indexed(
                tier, start_node_id, relationship, direction
            )

            # Update access tracking for found nodes
            updated_nodes = []
            for node in nodes:
                updated_node = node.with_access()
                self._storage.add_node(updated_node, tier)
                updated_nodes.append(updated_node)

            connected_nodes.extend(updated_nodes)
            if updated_nodes and tier != StorageTier.RUNTIME:
                storage_tier = tier.value

        query_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return QueryResult(
            nodes=connected_nodes, query_time_ms=query_time, storage_tier=storage_tier
        )

    async def prune(
        self, runtime_limit: Optional[int] = None, store_limit: Optional[int] = None
    ) -> int:
        """Prune storage tiers to maintain performance."""
        total_pruned = 0

        # Prune runtime to store
        if runtime_limit is not None:
            pruned = self._storage.prune_by_size_limit(
                StorageTier.RUNTIME, runtime_limit, StorageTier.STORE
            )
            total_pruned += pruned

        # Prune store to cold
        if store_limit is not None:
            pruned = self._storage.prune_by_size_limit(
                StorageTier.STORE, store_limit, StorageTier.COLD
            )
            total_pruned += pruned

        return total_pruned

    async def export_json(self) -> Dict[str, Any]:
        """Export the entire knowledge base to JSON format."""
        all_nodes = []
        all_edges = []

        # Collect from all tiers
        for tier in [StorageTier.RUNTIME, StorageTier.STORE, StorageTier.COLD]:
            all_nodes.extend(self._storage.get_all_nodes(tier))
            all_edges.extend(self._storage.get_all_edges(tier))

        return {
            "nodes": [node.model_dump() for node in all_nodes],
            "edges": [edge.model_dump() for edge in all_edges],
            "diffs": [diff.model_dump() for diff in self._diff_history],
            "metadata": {
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_nodes": len(all_nodes),
                "total_edges": len(all_edges),
                "total_diffs": len(self._diff_history),
            },
        }
