"""
Three-tier storage system for the Momo Graph Backend.

Implements runtime (hot), store (warm), and cold storage tiers with pruning logic
for graph data (nodes and edges).
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .models import GraphNode, GraphEdge
from .indexing import GraphIndexManager


class GraphStorageTier(str, Enum):
    """Storage tiers for the three-tier graph architecture."""

    RUNTIME = "runtime"  # Hot in-memory storage
    STORE = "store"  # Warm indexed storage
    COLD = "cold"  # Cold archival storage


class GraphThreeTierStorage:
    """
    Three-tier storage system with automatic pruning.

    - Runtime: Hot in-memory data for active use
    - Store: Warm data with indexing for queries
    - Cold: Archival storage for historical data
    """

    def __init__(self):
        # Storage tiers - each tier stores nodes and edges separately
        self._nodes: Dict[GraphStorageTier, Dict[str, GraphNode]] = {
            GraphStorageTier.RUNTIME: {},
            GraphStorageTier.STORE: {},
            GraphStorageTier.COLD: {},
        }

        self._edges: Dict[GraphStorageTier, Dict[str, GraphEdge]] = {
            GraphStorageTier.RUNTIME: {},
            GraphStorageTier.STORE: {},
            GraphStorageTier.COLD: {},
        }

        # High-performance indexes for fast queries
        self._indexes: Dict[GraphStorageTier, GraphIndexManager] = {
            GraphStorageTier.RUNTIME: GraphIndexManager(),
            GraphStorageTier.STORE: GraphIndexManager(),
            GraphStorageTier.COLD: GraphIndexManager(),
        }

    def count_nodes(self, tier: GraphStorageTier) -> int:
        """Count nodes in a specific tier."""
        return len(self._nodes[tier])

    def count_edges(self, tier: GraphStorageTier) -> int:
        """Count edges in a specific tier."""
        return len(self._edges[tier])

    def add_node(self, node: GraphNode, tier: GraphStorageTier) -> None:
        """Add a node to a specific tier."""
        self._nodes[tier][node.id] = node
        self._indexes[tier].add_node(node)

    def add_edge(self, edge: GraphEdge, tier: GraphStorageTier) -> None:
        """Add an edge to a specific tier."""
        self._edges[tier][edge.id] = edge
        self._indexes[tier].add_edge(edge)

    def get_node(self, node_id: str, tier: GraphStorageTier) -> Optional[GraphNode]:
        """Get a node from a specific tier."""
        return self._nodes[tier].get(node_id)

    def get_edge(self, edge_id: str, tier: GraphStorageTier) -> Optional[GraphEdge]:
        """Get an edge from a specific tier."""
        return self._edges[tier].get(edge_id)

    def remove_node(self, node_id: str, tier: GraphStorageTier) -> bool:
        """Remove a node from a specific tier. Returns True if found and removed."""
        if node_id in self._nodes[tier]:
            node = self._nodes[tier][node_id]
            self._indexes[tier].remove_node(node)
            del self._nodes[tier][node_id]
            return True
        return False

    def remove_edge(self, edge_id: str, tier: GraphStorageTier) -> bool:
        """Remove an edge from a specific tier. Returns True if found and removed."""
        if edge_id in self._edges[tier]:
            edge = self._edges[tier][edge_id]
            self._indexes[tier].remove_edge(edge)
            del self._edges[tier][edge_id]
            return True
        return False

    def move_node(
        self, node_id: str, from_tier: GraphStorageTier, to_tier: GraphStorageTier
    ) -> bool:
        """Move a node between tiers. Returns True if successful."""
        node = self.get_node(node_id, from_tier)
        if node is None:
            return False

        self.add_node(node, to_tier)
        self.remove_node(node_id, from_tier)
        return True

    def move_edge(
        self, edge_id: str, from_tier: GraphStorageTier, to_tier: GraphStorageTier
    ) -> bool:
        """Move an edge between tiers. Returns True if successful."""
        edge = self.get_edge(edge_id, from_tier)
        if edge is None:
            return False

        self.add_edge(edge, to_tier)
        self.remove_edge(edge_id, from_tier)
        return True

    def find_node(self, node_id: str) -> Optional[GraphNode]:
        """Find a node across all tiers, checking hottest first."""
        for tier in [
            GraphStorageTier.RUNTIME,
            GraphStorageTier.STORE,
            GraphStorageTier.COLD,
        ]:
            node = self.get_node(node_id, tier)
            if node is not None:
                return node
        return None

    def find_edge(self, edge_id: str) -> Optional[GraphEdge]:
        """Find an edge across all tiers, checking hottest first."""
        for tier in [
            GraphStorageTier.RUNTIME,
            GraphStorageTier.STORE,
            GraphStorageTier.COLD,
        ]:
            edge = self.get_edge(edge_id, tier)
            if edge is not None:
                return edge
        return None

    def prune_by_access_count(
        self, tier: GraphStorageTier, threshold: int, target_tier: GraphStorageTier
    ) -> int:
        """
        Prune nodes/edges with access count below threshold.
        Returns number of items moved.
        """
        moved_count = 0

        # Prune nodes
        nodes_to_move = []
        for node_id, node in self._nodes[tier].items():
            if node.access_count < threshold:
                nodes_to_move.append(node_id)

        for node_id in nodes_to_move:
            if self.move_node(node_id, tier, target_tier):
                moved_count += 1

        # Prune edges
        edges_to_move = []
        for edge_id, edge in self._edges[tier].items():
            if edge.access_count < threshold:
                edges_to_move.append(edge_id)

        for edge_id in edges_to_move:
            if self.move_edge(edge_id, tier, target_tier):
                moved_count += 1

        return moved_count

    def prune_by_age(
        self,
        tier: GraphStorageTier,
        max_age_hours: float,
        target_tier: GraphStorageTier,
    ) -> int:
        """
        Prune nodes/edges older than max_age_hours.
        Returns number of items moved.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        moved_count = 0

        # Prune old nodes
        nodes_to_move = []
        for node_id, node in self._nodes[tier].items():
            if node.last_accessed < cutoff_time:
                nodes_to_move.append(node_id)

        for node_id in nodes_to_move:
            if self.move_node(node_id, tier, target_tier):
                moved_count += 1

        # Prune old edges
        edges_to_move = []
        for edge_id, edge in self._edges[tier].items():
            if edge.last_accessed < cutoff_time:
                edges_to_move.append(edge_id)

        for edge_id in edges_to_move:
            if self.move_edge(edge_id, tier, target_tier):
                moved_count += 1

        return moved_count

    def prune_by_size_limit(
        self, tier: GraphStorageTier, max_size: int, target_tier: GraphStorageTier
    ) -> int:
        """
        Prune to keep only max_size items in tier.
        Moves oldest items first. Returns number of items moved.
        """
        current_size = self.count_nodes(tier) + self.count_edges(tier)
        if current_size <= max_size:
            return 0

        items_to_move = current_size - max_size
        moved_count = 0

        # Collect all items with timestamps
        all_items = []

        # Add nodes
        for node_id, node in self._nodes[tier].items():
            all_items.append(("node", node_id, node.last_accessed))

        # Add edges
        for edge_id, edge in self._edges[tier].items():
            all_items.append(("edge", edge_id, edge.last_accessed))

        # Sort by last_accessed (oldest first)
        all_items.sort(key=lambda x: x[2])

        # Move oldest items
        for item_type, item_id, _ in all_items[:items_to_move]:
            if item_type == "node":
                if self.move_node(item_id, tier, target_tier):
                    moved_count += 1
            else:  # edge
                if self.move_edge(item_id, tier, target_tier):
                    moved_count += 1

        return moved_count

    def get_all_nodes(self, tier: GraphStorageTier) -> List[GraphNode]:
        """Get all nodes from a tier."""
        return list(self._nodes[tier].values())

    def get_all_edges(self, tier: GraphStorageTier) -> List[GraphEdge]:
        """Get all edges from a tier."""
        return list(self._edges[tier].values())

    def query_nodes_indexed(
        self,
        tier: GraphStorageTier,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> List[GraphNode]:
        """Fast indexed query for nodes in a specific tier."""
        # If no filters provided, return empty list to avoid full scan
        if label is None and not properties:
            return list(self._nodes[tier].values())

        node_ids = self._indexes[tier].query_nodes_indexed(
            label=label, properties=properties
        )
        return [
            self._nodes[tier][node_id]
            for node_id in node_ids
            if node_id in self._nodes[tier]
        ]

    def query_edges_indexed(
        self,
        tier: GraphStorageTier,
        relationship: Optional[str] = None,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> List[GraphEdge]:
        """Fast indexed query for edges in a specific tier."""
        # If no filters provided, return all edges (but this should be avoided)
        if (
            relationship is None
            and source_id is None
            and target_id is None
            and not properties
        ):
            return list(self._edges[tier].values())

        edge_ids = self._indexes[tier].query_edges_indexed(
            relationship=relationship,
            source_id=source_id,
            target_id=target_id,
            properties=properties,
        )
        return [
            self._edges[tier][edge_id]
            for edge_id in edge_ids
            if edge_id in self._edges[tier]
        ]

    def query_connected_nodes_indexed(
        self,
        tier: GraphStorageTier,
        start_node_id: str,
        relationship: str,
        direction: str = "outgoing",
    ) -> List[GraphNode]:
        """Fast indexed query for connected nodes in a specific tier."""
        connected_node_ids = self._indexes[tier].query_connected_nodes_indexed(
            start_node_id, relationship, direction
        )
        return [
            self._nodes[tier][node_id]
            for node_id in connected_node_ids
            if node_id in self._nodes[tier]
        ]
