"""
Adapter to connect the graph backend to the unified KnowledgeBase interface.

Translates between unified Document/Relationship models and graph-specific models.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .kb_core import BackendInterface
from .unified_models import Document, Relationship, SearchResult, DocumentType
from momo_graph import GraphBackend, GraphNode, GraphEdge, GraphQueryResult


class GraphBackendAdapter(BackendInterface):
    """
    Adapter that connects the graph backend to the unified KB interface.

    Handles translation between unified models and graph-specific models.
    """

    def __init__(self):
        self.graph_backend = GraphBackend()
        self._doc_id_mapping: Dict[str, str] = {}  # unified_id -> graph_node_id
        self._rel_id_mapping: Dict[str, str] = {}  # unified_id -> graph_edge_id

    async def initialize(self) -> None:
        """Initialize the graph backend."""
        await self.graph_backend.initialize()

    async def close(self) -> None:
        """Close the graph backend."""
        await self.graph_backend.close()

    async def insert_document(self, doc: Document) -> str:
        """Insert a document as a graph node."""
        # Convert Document to GraphNode
        graph_node = self._document_to_graph_node(doc)

        # Insert into graph backend
        diff = await self.graph_backend.insert_node(graph_node)
        graph_node_id = diff.node.id

        # Track ID mapping
        self._doc_id_mapping[doc.id] = graph_node_id

        return graph_node_id

    async def insert_relationship(self, rel: Relationship) -> str:
        """Insert a relationship as a graph edge."""
        # Get graph node IDs for source and target
        source_graph_id = self._doc_id_mapping.get(rel.source_id)
        target_graph_id = self._doc_id_mapping.get(rel.target_id)

        if not source_graph_id or not target_graph_id:
            raise ValueError(f"Source or target document not found in graph backend")

        # Convert Relationship to GraphEdge
        graph_edge = GraphEdge(
            source_id=source_graph_id,
            target_id=target_graph_id,
            relationship=rel.relationship_type,
            properties={
                **rel.properties,
                "unified_id": rel.id,
                "created_at": rel.created_at.isoformat(),
                "source": rel.source,
            },
        )

        # Insert into graph backend
        diff = await self.graph_backend.insert_edge(graph_edge)
        graph_edge_id = diff.edge.id

        # Track ID mapping
        self._rel_id_mapping[rel.id] = graph_edge_id

        return graph_edge_id

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by unified ID."""
        graph_node_id = self._doc_id_mapping.get(doc_id)
        if not graph_node_id:
            return False

        try:
            await self.graph_backend.delete_node(graph_node_id)
            del self._doc_id_mapping[doc_id]
            return True
        except Exception:
            return False

    async def delete_relationship(self, rel_id: str) -> bool:
        """Delete a relationship by unified ID."""
        graph_edge_id = self._rel_id_mapping.get(rel_id)
        if not graph_edge_id:
            return False

        try:
            await self.graph_backend.delete_edge(graph_edge_id)
            del self._rel_id_mapping[rel_id]
            return True
        except Exception:
            return False

    async def search(
        self, query: str, filters: Optional[Dict] = None, top_k: int = 10
    ) -> SearchResult:
        """Search using graph backend capabilities."""
        start_time = datetime.utcnow()

        # For now, implement simple text-based search using graph queries
        # This is a basic implementation - will be enhanced later

        documents = []
        relationships = []
        scores = []

        try:
            # Search nodes by properties (simple text matching)
            if query:
                # Try to find nodes with query text in properties
                node_result = await self.graph_backend.query_nodes()

                for node in node_result.nodes:
                    # Simple text matching in properties
                    if self._matches_query(node, query):
                        doc = self._graph_node_to_document(node)
                        documents.append(doc)
                        scores.append(0.8)  # Mock score for now

                        if len(documents) >= top_k:
                            break

            # Apply filters if provided
            if filters:
                documents = self._apply_filters(documents, filters)

        except Exception as e:
            print(f"Graph search error: {e}")

        search_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return SearchResult(
            documents=documents,
            relationships=relationships,
            query=query,
            total_results=len(documents) + len(relationships),
            search_time_ms=search_time,
            backends_used=["graph"],
            scores=scores,
        )

    async def rollback(self, steps: int) -> None:
        """Rollback operations in the graph backend."""
        await self.graph_backend.rollback(steps)

    async def get_stats(self) -> Dict[str, Any]:
        """Get graph backend statistics."""
        node_count = await self.graph_backend.count_nodes()
        edge_count = await self.graph_backend.count_edges()

        return {
            "nodes": node_count,
            "edges": edge_count,
            "documents_mapped": len(self._doc_id_mapping),
            "relationships_mapped": len(self._rel_id_mapping),
            "backend_type": "graph",
        }

    def _document_to_graph_node(self, doc: Document) -> GraphNode:
        """Convert unified Document to GraphNode."""
        # Combine title and content for graph node properties
        properties = {
            **doc.properties,
            "unified_id": doc.id,
            "document_type": doc.type.value,
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat(),
        }

        if doc.title:
            properties["title"] = doc.title
        if doc.content:
            properties["content"] = doc.content
        if doc.source:
            properties["source"] = doc.source
        if doc.tags:
            properties["tags"] = doc.tags

        return GraphNode(
            label=doc.type.value.title(),  # "person" -> "Person"
            properties=properties,
        )

    def _graph_node_to_document(self, node: GraphNode) -> Document:
        """Convert GraphNode to unified Document."""
        props = node.properties.copy()

        # Extract standard fields
        unified_id = props.pop("unified_id", node.id)
        doc_type = props.pop("document_type", "custom")
        title = props.pop("title", None)
        content = props.pop("content", None)
        source = props.pop("source", None)
        tags = props.pop("tags", [])

        # Parse timestamps
        created_at = datetime.fromisoformat(
            props.pop("created_at", datetime.utcnow().isoformat())
        )
        updated_at = datetime.fromisoformat(
            props.pop("updated_at", datetime.utcnow().isoformat())
        )

        return Document(
            id=unified_id,
            type=DocumentType(doc_type),
            title=title,
            content=content,
            properties=props,  # Remaining properties
            created_at=created_at,
            updated_at=updated_at,
            source=source,
            tags=tags,
            backend_ids={"graph": node.id},
        )

    def _matches_query(self, node: GraphNode, query: str) -> bool:
        """Simple text matching for search queries."""
        query_lower = query.lower()

        # Check in node label
        if query_lower in node.label.lower():
            return True

        # Check in properties
        for key, value in node.properties.items():
            if isinstance(value, str) and query_lower in value.lower():
                return True

        return False

    def _apply_filters(
        self, documents: List[Document], filters: Dict
    ) -> List[Document]:
        """Apply filters to search results."""
        filtered = []

        for doc in documents:
            matches = True

            for filter_key, filter_value in filters.items():
                if filter_key == "type" and doc.type.value != filter_value:
                    matches = False
                    break
                elif filter_key == "tags" and filter_value not in doc.tags:
                    matches = False
                    break
                elif (
                    filter_key in doc.properties
                    and doc.properties[filter_key] != filter_value
                ):
                    matches = False
                    break

            if matches:
                filtered.append(doc)

        return filtered
