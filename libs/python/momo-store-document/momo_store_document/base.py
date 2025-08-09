"""
Base knowledge base implementation with low-level operations.

This module provides the foundational operations that support the higher-level
KnowledgeBase functionality. Contains private methods and backend management.
"""

from abc import ABC
from typing import List, Dict, Any, Optional, Union
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document as LangChainDocument

from .types import (
    Document,
    DocumentMetadata,
    SearchResult,
    SearchOptions,
    QueryStrategy,
    IndexingPipeline,
    RelationshipSpec,
)
from .exceptions import KnowledgeBaseError, DocumentNotFoundError, SearchError
from .factory import (
    create_document_backend,
    create_vector_backend,
    create_graph_backend,
)


class BaseKnowledgeBase(ABC):
    """
    Base knowledge base with low-level operations.

    Contains private methods for document conversion, backend management,
    and search strategy implementation. This class handles the technical
    details that support the public API.
    """

    def __init__(
        self,
        embeddings: Optional[Embeddings] = None,
        vector_backend: Union[str, Any] = None,
        graph_backend: Union[str, Any] = None,
        document_backend: Union[str, Any] = None,
        indexing_pipeline: Optional[IndexingPipeline] = None,
        default_strategy: QueryStrategy = QueryStrategy.AUTO,
    ):
        """
        Initialize the base knowledge base.

        Args:
            embeddings: Embedding model for vector operations
            vector_backend: Vector storage backend (string or instance, defaults to 'memory')
            graph_backend: Graph storage backend (string or instance, defaults to 'memory')
            document_backend: Document storage backend (string or instance, defaults to 'memory')
            indexing_pipeline: Configuration for document processing
            default_strategy: Default query strategy
        """
        self.embeddings = embeddings
        self.default_strategy = default_strategy

        # Initialize backends using factory system
        if embeddings is not None:
            self.vector_backend = create_vector_backend(
                vector_backend or "memory", embeddings
            )
        else:
            self.vector_backend = None

        self.graph_backend = create_graph_backend(graph_backend or "memory")
        self.document_backend = create_document_backend(document_backend or "memory")

        # Initialize indexing pipeline
        if indexing_pipeline is None:
            indexing_pipeline = IndexingPipeline(
                relationship_specs=[
                    RelationshipSpec(
                        source_field="type",
                        target_field="type",
                        relationship_type="same_type",
                    ),
                    RelationshipSpec(
                        source_field="category",
                        target_field="category",
                        relationship_type="same_category",
                    ),
                    RelationshipSpec(
                        source_field="author",
                        target_field="author",
                        relationship_type="same_author",
                    ),
                    RelationshipSpec(
                        source_field="source",
                        target_field="source",
                        relationship_type="same_source",
                    ),
                ]
            )
        self.indexing_pipeline = indexing_pipeline

        # Document tracking
        self._document_metadata: Dict[str, Document] = {}

    def _document_to_langchain(self, document: Document) -> LangChainDocument:
        """Convert Document to LangChain format."""
        return LangChainDocument(
            id=document.id,
            page_content=document.content,
            metadata=document.metadata.model_dump(exclude_none=True),
        )

    def _langchain_to_document(self, lc_doc: LangChainDocument) -> Document:
        """Convert LangChain document back to Document format."""
        if lc_doc.id and lc_doc.id in self._document_metadata:
            return self._document_metadata[lc_doc.id]

        metadata_dict = dict(lc_doc.metadata) if lc_doc.metadata else {}
        metadata = DocumentMetadata(
            source=metadata_dict.get("source"),
            author=metadata_dict.get("author"),
            type=metadata_dict.get("type"),
            category=metadata_dict.get("category"),
            tags=metadata_dict.get("tags", []),
            language=metadata_dict.get("language", "en"),
            custom={
                k: v
                for k, v in metadata_dict.items()
                if k not in ["source", "author", "type", "category", "tags", "language"]
            },
        )

        return Document(
            id=lc_doc.id or "", content=lc_doc.page_content, metadata=metadata
        )

    async def _extract_relationships(self, document: Document) -> List[tuple]:
        """Extract relationships from document based on pipeline config."""
        if not self.indexing_pipeline.extract_relationships:
            return []

        relationships = []
        metadata_dict = document.metadata.model_dump(exclude_none=True)

        for spec in self.indexing_pipeline.relationship_specs:
            if spec.source_field in metadata_dict:
                source_value = metadata_dict[spec.source_field]
                relationships.append(
                    (
                        document.id,
                        f"{spec.source_field}:{source_value}",
                        spec.relationship_type,
                        {
                            "weight": spec.weight,
                            "field": spec.source_field,
                            "value": source_value,
                        },
                    )
                )

        return relationships

    def _determine_strategy(self, query: str, options: SearchOptions) -> QueryStrategy:
        """Auto-determine optimal query strategy based on query and options."""
        if options.filters and len(options.filters) > 2:
            return QueryStrategy.GRAPH_ONLY
        elif any(
            keyword in query.lower()
            for keyword in ["related", "connected", "similar to"]
        ):
            return QueryStrategy.HYBRID
        else:
            return QueryStrategy.VECTOR_ONLY

    async def _vector_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
        """Perform vector-based search."""
        if not self.vector_backend:
            return []

        lc_results = await self.vector_backend.similarity_search(
            query, k=options.limit + options.offset, filter=options.filters
        )

        results = []
        for i, lc_doc in enumerate(
            lc_results[options.offset : options.offset + options.limit]
        ):
            document = self._langchain_to_document(lc_doc)
            score = 1.0 - (i * 0.1)
            score = max(0.1, score)

            if score >= options.threshold:
                results.append(SearchResult(document=document, score=score, rank=i + 1))

        return results

    async def _graph_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
        """Perform graph-based search."""
        results = []

        if options.filters:
            starting_nodes = []
            for doc_id, doc in self._document_metadata.items():
                metadata_dict = doc.metadata.model_dump(exclude_none=True)
                if all(metadata_dict.get(k) == v for k, v in options.filters.items()):
                    starting_nodes.append(doc_id)

            all_traversed = []
            for start_node in starting_nodes[:3]:
                traversed = await self.graph_backend.traverse(start_node, max_depth=2)
                all_traversed.extend(traversed)

            for i, node_data in enumerate(all_traversed[: options.limit]):
                if node_data["node_id"] in self._document_metadata:
                    document = self._document_metadata[node_data["node_id"]]
                    score = 1.0 / (node_data["depth"] + 1)

                    if score >= options.threshold:
                        results.append(
                            SearchResult(document=document, score=score, rank=i + 1)
                        )

        return results

    async def _hybrid_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
        """Perform hybrid vector + graph search."""
        vector_results = await self._vector_search(query, options)

        graph_results = []
        for result in vector_results[:3]:
            traversed = await self.graph_backend.traverse(
                result.document.id, max_depth=1
            )
            for node_data in traversed[1:]:
                if node_data["node_id"] in self._document_metadata:
                    document = self._document_metadata[node_data["node_id"]]
                    score = result.score * 0.5

                    graph_results.append(
                        SearchResult(document=document, score=score, rank=0)
                    )

        all_results = vector_results + graph_results
        seen_docs = set()
        unique_results: List[SearchResult] = []

        for result in sorted(all_results, key=lambda x: x.score, reverse=True):
            if result.document.id not in seen_docs:
                seen_docs.add(result.document.id)
                result.rank = len(unique_results) + 1
                unique_results.append(result)

        return unique_results[: options.limit]

    async def _document_search(
        self, query: str, options: SearchOptions
    ) -> List[SearchResult]:
        """Perform document backend search (fallback)."""
        scan_results = await self.document_backend.scan(
            pattern=query, filters=options.filters
        )

        results = []
        for i, item in enumerate(scan_results[: options.limit]):
            if item.get("key") in self._document_metadata:
                document = self._document_metadata[item["key"]]
                score = 0.5

                if score >= options.threshold:
                    results.append(
                        SearchResult(document=document, score=score, rank=i + 1)
                    )

        return results

    def set_vector_backend(self, backend):
        """Set or replace vector backend."""
        self.vector_backend = backend

    def set_graph_backend(self, backend):
        """Set or replace graph backend."""
        self.graph_backend = backend

    def set_document_backend(self, backend):
        """Set or replace document backend."""
        self.document_backend = backend

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about configured backends."""
        return {
            "vector_backend": (
                type(self.vector_backend).__name__ if self.vector_backend else None
            ),
            "graph_backend": type(self.graph_backend).__name__,
            "document_backend": type(self.document_backend).__name__,
            "embeddings": type(self.embeddings).__name__ if self.embeddings else None,
            "default_strategy": self.default_strategy.value,
            "indexing_pipeline": {
                "extract_relationships": self.indexing_pipeline.extract_relationships,
                "relationship_specs": len(self.indexing_pipeline.relationship_specs),
            },
        }
