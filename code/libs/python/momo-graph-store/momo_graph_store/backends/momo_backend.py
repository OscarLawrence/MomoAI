"""
Momo Graph backend implementation for graph store.

Adapts momo-graph's GraphBackend to the LangChain GraphStore interface.
"""

from typing import Any, Dict, List, Optional

from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship

from momo_graph import GraphBackend, GraphNode, GraphEdge

from .base import BaseGraphBackend


class MomoGraphBackend(BaseGraphBackend):
    """
    Momo Graph backend implementation.

    Provides high-performance graph operations using momo-graph's
    immutable backend with rollback capabilities.
    """

    def __init__(self, **config: Any):
        """Initialize the momo graph backend."""
        self._backend = GraphBackend()
        self._schema_cache: Optional[str] = None
        self._structured_schema_cache: Optional[Dict[str, Any]] = None

    async def initialize(self) -> None:
        """Initialize the backend."""
        await self._backend.initialize()

    async def close(self) -> None:
        """Close the backend."""
        await self._backend.close()

    def get_schema(self) -> str:
        """Return the schema of the graph database."""
        if self._schema_cache is None:
            # Build schema from current nodes and edges
            node_labels = set()
            relationship_types = set()

            # This is synchronous for now - could be optimized to cache during operations
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context but this method is sync
                    # For now, return a basic schema - this could be enhanced
                    self._schema_cache = (
                        "Graph schema: Dynamic schema based on current data"
                    )
                else:
                    # We can run async operations
                    nodes_result = loop.run_until_complete(self._backend.query_nodes())
                    edges_result = loop.run_until_complete(self._backend.query_edges())

                    for node in nodes_result.nodes:
                        if node.label:
                            node_labels.add(node.label)

                    for edge in edges_result.edges:
                        if edge.relationship:
                            relationship_types.add(edge.relationship)

                    schema_parts = []
                    if node_labels:
                        schema_parts.append(
                            f"Node Labels: {', '.join(sorted(node_labels))}"
                        )
                    if relationship_types:
                        schema_parts.append(
                            f"Relationship Types: {', '.join(sorted(relationship_types))}"
                        )

                    self._schema_cache = "; ".join(schema_parts) or "Empty graph"
            except RuntimeError:
                # No event loop - provide basic schema
                self._schema_cache = (
                    "Graph schema: Dynamic schema based on current data"
                )

        return self._schema_cache

    def get_structured_schema(self) -> Dict[str, Any]:
        """Return the structured schema of the graph database."""
        if self._structured_schema_cache is None:
            self._structured_schema_cache = {
                "node_props": {},
                "rel_props": {},
                "relationships": [],
                "metadata": {
                    "backend": "momo-graph",
                    "supports_rollback": True,
                    "immutable_operations": True,
                },
            }
        return self._structured_schema_cache

    async def query(
        self, query: str, params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Query the graph.

        For now, supports basic patterns. Could be extended to support
        a full query language.
        """
        params = params or {}

        # Basic query pattern matching - can be enhanced
        query_lower = query.lower().strip()

        if query_lower.startswith("match (n)"):
            # Return all nodes
            result = await self._backend.query_nodes()
            return [self._node_to_dict(node) for node in result.nodes]

        elif "return count(n)" in query_lower:
            # Count nodes
            count = await self._backend.count_nodes()
            return [{"count": count}]

        elif "match ()-[r]->()" in query_lower:
            # Return all relationships
            result = await self._backend.query_edges()
            return [self._edge_to_dict(edge) for edge in result.edges]

        else:
            # Default: return empty result
            return []

    async def refresh_schema(self) -> None:
        """Refresh the graph schema information."""
        self._schema_cache = None
        self._structured_schema_cache = None

    async def add_graph_documents(
        self, graph_documents: List[GraphDocument], include_source: bool = False
    ) -> None:
        """Take GraphDocument as input and construct the graph."""
        for doc in graph_documents:
            # Add nodes
            for node in doc.nodes:
                graph_node = self._langchain_node_to_momo(node)
                await self._backend.insert_node(graph_node)

            # Add relationships
            for rel in doc.relationships:
                graph_edge = self._langchain_relationship_to_momo(rel)
                await self._backend.insert_edge(graph_edge)

        # Refresh schema cache since we added new data
        await self.refresh_schema()

    def _langchain_node_to_momo(self, node: Node) -> GraphNode:
        """Convert LangChain Node to momo GraphNode."""
        return GraphNode(
            id=str(node.id), label=node.type, properties=node.properties or {}
        )

    def _langchain_relationship_to_momo(self, rel: Relationship) -> GraphEdge:
        """Convert LangChain Relationship to momo GraphEdge."""
        return GraphEdge(
            id=f"{rel.source.id}-{rel.type}-{rel.target.id}",
            source_id=str(rel.source.id),
            target_id=str(rel.target.id),
            relationship=rel.type,
            properties=rel.properties or {},
        )

    def _node_to_dict(self, node: GraphNode) -> Dict[str, Any]:
        """Convert GraphNode to dictionary for query results."""
        return {
            "id": node.id,
            "type": node.label,
            "properties": node.properties,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "last_accessed": node.last_accessed.isoformat()
            if node.last_accessed
            else None,
        }

    def _edge_to_dict(self, edge: GraphEdge) -> Dict[str, Any]:
        """Convert GraphEdge to dictionary for query results."""
        return {
            "id": edge.id,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "type": edge.relationship,
            "properties": edge.properties,
            "created_at": edge.created_at.isoformat() if edge.created_at else None,
            "last_accessed": edge.last_accessed.isoformat()
            if edge.last_accessed
            else None,
        }

    # Additional momo-graph specific methods
    async def rollback(self, steps: int) -> None:
        """Rollback the last N operations."""
        await self._backend.rollback(steps)
        await self.refresh_schema()

    async def get_rollback_history(self):
        """Get the rollback history."""
        return await self._backend.get_diff_history()

    async def count_nodes(self) -> int:
        """Count total nodes."""
        return await self._backend.count_nodes()

    async def count_edges(self) -> int:
        """Count total edges."""
        return await self._backend.count_edges()

    async def prune(
        self, runtime_limit: Optional[int] = None, store_limit: Optional[int] = None
    ) -> int:
        """Prune storage tiers."""
        return await self._backend.prune(runtime_limit, store_limit)
