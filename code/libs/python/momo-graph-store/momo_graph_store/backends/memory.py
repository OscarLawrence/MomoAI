"""
In-memory graph backend implementation.

Provides a simple in-memory graph store for development and testing.
"""

import re
from collections import defaultdict
from typing import Any, Dict, List, Set

from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship

from ..exceptions import NodeNotFoundError, QueryError
from .base import BaseGraphBackend


class InMemoryGraphBackend(BaseGraphBackend):
    """
    Simple in-memory graph backend for development.

    Stores nodes and relationships in memory using dictionaries.
    Supports basic query operations and schema introspection.
    """

    def __init__(self) -> None:
        """Initialize empty in-memory graph."""
        self.backend_name = "memory"

        # Storage
        self.nodes: Dict[str, Node] = {}
        self.relationships: List[Relationship] = []
        self.node_types: Set[str] = set()
        self.relationship_types: Set[str] = set()

        # Indexes for faster querying
        self._outgoing_rels: Dict[str, List[Relationship]] = defaultdict(list)
        self._incoming_rels: Dict[str, List[Relationship]] = defaultdict(list)

    async def add_graph_documents(
        self, graph_documents: List[GraphDocument], include_source: bool = False
    ) -> None:
        """
        Add graph documents to the in-memory store.

        Args:
            graph_documents: List of GraphDocument objects to add
            include_source: Whether to include source document info (not used in memory backend)
        """
        for graph_doc in graph_documents:
            # Add nodes
            for node in graph_doc.nodes:
                self.nodes[str(node.id)] = node
                self.node_types.add(node.type)

            # Add relationships
            for rel in graph_doc.relationships:
                # Ensure source and target nodes exist
                if str(rel.source.id) not in self.nodes:
                    self.nodes[str(rel.source.id)] = rel.source
                    self.node_types.add(rel.source.type)

                if str(rel.target.id) not in self.nodes:
                    self.nodes[str(rel.target.id)] = rel.target
                    self.node_types.add(rel.target.type)

                self.relationships.append(rel)
                self.relationship_types.add(rel.type)

                # Update indexes
                self._outgoing_rels[str(rel.source.id)].append(rel)
                self._incoming_rels[str(rel.target.id)].append(rel)

    async def query(
        self, query: str, params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a simple query against the graph.

        Supports basic pattern matching queries:
        - "MATCH (n) RETURN n" - return all nodes
        - "MATCH (n:Type) RETURN n" - return nodes of specific type
        - "MATCH (n)-[r]->(m) RETURN n,r,m" - return node relationships
        - "MATCH (n {id: 'value'}) RETURN n" - return nodes with specific property

        Args:
            query: Query string (simplified Cypher-like syntax)
            params: Query parameters (optional)

        Returns:
            List of dictionaries containing query results
        """
        if params is None:
            params = {}

        query = query.strip()
        results = []

        # Simple pattern matching for basic queries
        if "MATCH (n) RETURN n" in query:
            # Return all nodes
            for node in self.nodes.values():
                results.append({"n": self._node_to_dict(node)})

        elif re.search(r"MATCH \(n:(\w+)\) RETURN n", query):
            # Return nodes of specific type
            match = re.search(r"MATCH \(n:(\w+)\) RETURN n", query)
            if match:
                node_type = match.group(1)
                for node in self.nodes.values():
                    if node.type == node_type:
                        results.append({"n": self._node_to_dict(node)})

        elif "MATCH (n)-[r]->(m) RETURN n,r,m" in query:
            # Return relationships
            for rel in self.relationships:
                results.append(
                    {
                        "n": self._node_to_dict(rel.source),
                        "r": self._relationship_to_dict(rel),
                        "m": self._node_to_dict(rel.target),
                    }
                )

        elif re.search(r"MATCH \(n \{id: ['\"]([^'\"]+)['\"]\}\) RETURN n", query):
            # Return node with specific ID
            match = re.search(
                r"MATCH \(n \{id: ['\"]([^'\"]+)['\"]\}\) RETURN n", query
            )
            if match:
                node_id = match.group(1)
                if node_id in self.nodes:
                    results.append({"n": self._node_to_dict(self.nodes[node_id])})

        else:
            raise QueryError(f"Unsupported query pattern: {query}")

        return results

    def get_schema(self) -> str:
        """Return the schema of the Graph database as a string."""
        schema_parts = []

        if self.node_types:
            schema_parts.append("Node types:")
            for node_type in sorted(self.node_types):
                count = sum(1 for node in self.nodes.values() if node.type == node_type)
                schema_parts.append(f"  - {node_type} ({count} nodes)")

        if self.relationship_types:
            schema_parts.append("Relationship types:")
            for rel_type in sorted(self.relationship_types):
                count = sum(1 for rel in self.relationships if rel.type == rel_type)
                schema_parts.append(f"  - {rel_type} ({count} relationships)")

        return "\n".join(schema_parts) if schema_parts else "Empty graph"

    def get_structured_schema(self) -> Dict[str, Any]:
        """Return the schema of the Graph database as a dictionary."""
        node_counts: Dict[str, int] = defaultdict(int)
        for node in self.nodes.values():
            node_counts[node.type] += 1

        rel_counts: Dict[str, int] = defaultdict(int)
        for rel in self.relationships:
            rel_counts[rel.type] += 1

        return {
            "nodes": {
                "types": list(self.node_types),
                "counts": dict(node_counts),
                "total": len(self.nodes),
            },
            "relationships": {
                "types": list(self.relationship_types),
                "counts": dict(rel_counts),
                "total": len(self.relationships),
            },
        }

    async def refresh_schema(self) -> None:
        """Refresh the graph schema information."""
        # For in-memory backend, schema is always up-to-date
        # This method exists for interface compatibility
        pass

    def _node_to_dict(self, node: Node) -> Dict[str, Any]:
        """Convert Node object to dictionary."""
        return {"id": node.id, "type": node.type, "properties": node.properties}

    def _relationship_to_dict(self, rel: Relationship) -> Dict[str, Any]:
        """Convert Relationship object to dictionary."""
        return {
            "type": rel.type,
            "source": rel.source.id,
            "target": rel.target.id,
            "properties": getattr(rel, "properties", {}),
        }

    async def get_node(self, node_id: str) -> Node:
        """Get a specific node by ID."""
        if node_id not in self.nodes:
            raise NodeNotFoundError(f"Node with id '{node_id}' not found")
        return self.nodes[node_id]

    async def get_relationships(
        self, node_id: str, direction: str = "outgoing"
    ) -> List[Relationship]:
        """Get relationships for a node."""
        if node_id not in self.nodes:
            raise NodeNotFoundError(f"Node with id '{node_id}' not found")

        if direction == "outgoing":
            return self._outgoing_rels.get(node_id, [])
        elif direction == "incoming":
            return self._incoming_rels.get(node_id, [])
        else:
            # Both directions
            return self._outgoing_rels.get(node_id, []) + self._incoming_rels.get(
                node_id, []
            )

    async def traverse(
        self,
        start_node_id: str,
        max_depth: int = 2,
        relationship_types: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Traverse the graph from a starting node.

        Args:
            start_node_id: ID of the starting node
            max_depth: Maximum traversal depth
            relationship_types: Optional list of relationship types to follow

        Returns:
            List of dictionaries with traversal results
        """
        if start_node_id not in self.nodes:
            raise NodeNotFoundError(f"Start node '{start_node_id}' not found")

        visited = set()
        result = []

        def _traverse(node_id: str, depth: int) -> None:
            if depth > max_depth or node_id in visited:
                return

            visited.add(node_id)
            node = self.nodes[node_id]

            result.append(
                {"node_id": node_id, "node": self._node_to_dict(node), "depth": depth}
            )

            # Follow outgoing relationships
            for rel in self._outgoing_rels.get(node_id, []):
                if relationship_types is None or rel.type in relationship_types:
                    _traverse(str(rel.target.id), depth + 1)

        _traverse(start_node_id, 0)
        return result
