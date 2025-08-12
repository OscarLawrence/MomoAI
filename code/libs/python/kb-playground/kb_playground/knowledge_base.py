"""
KnowledgeBase - Main interface for the experimental KB playground.

Provides the simple API: search(), get(), add(), roll(), delete()
with immutable design, DVC integration, and outstanding query quality.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Union
import time
import hashlib
import json
from pathlib import Path

from .models import (
    Document, Relationship, SearchResult, Operation, 
    KnowledgeBaseSnapshot, QueryEnrichmentConfig
)
from .vector_lattice import VectorLattice
from .relationship_engine import RelationshipEngine
from .embedding_engine import SimpleEmbeddingEngine
from .dvc_manager import DVCManager


class KnowledgeBase:
    """
    Experimental high-performance knowledge base with vector-graph hybrid architecture.
    
    Features:
    - Immutable design with per-operation versioning
    - Outstanding query quality through relationship-aware search
    - DVC integration for reproducible knowledge management
    - Per-caller and per-collection query enrichment
    - Fast rollback capabilities for agent exploration
    """
    
    def __init__(
        self,
        dimension: int = 384,
        data_dir: Optional[str] = None,
        auto_discover_relationships: bool = True,
        enable_dvc: bool = True
    ):
        """
        Initialize knowledge base.
        
        Args:
            dimension: Vector embedding dimension
            data_dir: Directory for persistent storage (default: ./data/kb_playground)
            auto_discover_relationships: Enable automatic relationship discovery
            enable_dvc: Enable DVC integration for versioning
        """
        self.dimension = dimension
        self.data_dir = Path(data_dir or "./data/kb_playground")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self._lattice = VectorLattice(dimension=dimension)
        self._relationship_engine = RelationshipEngine() if auto_discover_relationships else None
        self._embedding_engine = SimpleEmbeddingEngine(dimension=dimension)
        self._dvc_manager = DVCManager(self.data_dir) if enable_dvc else None
        
        # State management
        self._operations: List[Operation] = []
        self._snapshots: List[KnowledgeBaseSnapshot] = []
        self._current_version = 0
        self._is_fitted = False
        
        # Query enrichment configurations
        self._global_config = QueryEnrichmentConfig()
        self._caller_configs: Dict[str, QueryEnrichmentConfig] = {}
        self._collection_configs: Dict[str, QueryEnrichmentConfig] = {}
        
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        caller_id: Optional[str] = None,
        collection: Optional[str] = None,
        **kwargs
    ) -> SearchResult:
        """
        Search for documents with relationship-aware context enrichment.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            caller_id: Caller ID for personalized enrichment
            collection: Collection for collection-specific behavior
            **kwargs: Additional search parameters
            
        Returns:
            Rich search result with context and relationships
        """
        start_time = time.time()
        
        # Get enrichment configuration
        config = self._get_enrichment_config(caller_id, collection)
        
        # Generate query embedding
        if not self._is_fitted:
            # Auto-fit on existing documents if not fitted
            self._auto_fit()
            
        query_vector = self._embedding_engine.embed(query)
        
        # Perform vector search with relationship boosting
        vector_results = self._lattice.search(
            query_vector=query_vector,
            top_k=int(top_k * config.expansion_factor),  # Get more for enrichment
            relationship_boost=0.2,
            min_similarity=config.semantic_threshold
        )
        
        # Get documents and relationships
        documents = []
        relationships = []
        scores = []
        
        for doc_id, score in vector_results[:top_k]:
            doc = self._lattice.get_document(doc_id)
            if doc:
                documents.append(doc)
                scores.append(float(score))
                
                # Track access for relationship discovery
                if self._relationship_engine:
                    self._relationship_engine.track_access(doc_id)
        
        # Enrich with relationship context
        if documents and config.relationship_depth > 0:
            relationships = self._get_contextual_relationships(
                documents, config.relationship_depth
            )
            
        # Apply caller-specific enrichment
        context_expansion = self._apply_context_enrichment(
            documents, relationships, config
        )
        
        # Create search result
        search_time_ms = (time.time() - start_time) * 1000
        result = SearchResult(
            documents=documents,
            relationships=relationships,
            scores=scores,
            query=query,
            total_results=len(documents),
            search_time_ms=search_time_ms,
            context_expansion=context_expansion,
            caller_enrichment={
                "caller_id": caller_id,
                "collection": collection,
                "config_used": config.model_dump()
            }
        )
        
        # Record operation
        self._record_operation(
            operation_type="search",
            caller_id=caller_id,
            metadata={
                "query": query,
                "top_k": top_k,
                "results_count": len(documents),
                "search_time_ms": search_time_ms
            }
        )
        
        return result
        
    def get(self, *ids: str) -> List[Optional[Document]]:
        """
        Get documents by their IDs.
        
        Args:
            *ids: Document IDs to retrieve
            
        Returns:
            List of documents (None for missing IDs)
        """
        documents = []
        for doc_id in ids:
            doc = self._lattice.get_document(doc_id)
            documents.append(doc)
            
            # Track access
            if doc and self._relationship_engine:
                self._relationship_engine.track_access(doc_id)
                
        # Record operation
        self._record_operation(
            operation_type="get",
            affected_ids=list(ids),
            metadata={"retrieved_count": sum(1 for doc in documents if doc)}
        )
        
        return documents
        
    def add(self, *documents: Union[Document, str, Dict[str, Any]]) -> List[str]:
        """
        Add documents to the knowledge base.
        
        Args:
            *documents: Documents to add (Document objects, strings, or dicts)
            
        Returns:
            List of document IDs
        """
        added_ids = []
        docs_to_process = []
        
        # Normalize inputs to Document objects
        for doc_input in documents:
            if isinstance(doc_input, Document):
                doc = doc_input
            elif isinstance(doc_input, str):
                doc = Document(content=doc_input, title=doc_input[:50])
            elif isinstance(doc_input, dict):
                doc = Document(**doc_input)
            else:
                raise ValueError(f"Unsupported document type: {type(doc_input)}")
                
            docs_to_process.append(doc)
            
        # Generate embeddings if not present
        texts_to_embed = []
        docs_needing_embeddings = []
        
        for doc in docs_to_process:
            if doc.embedding is None:
                texts_to_embed.append(doc.content)
                docs_needing_embeddings.append(doc)
                
        if texts_to_embed:
            if not self._is_fitted:
                # Fit embedding engine on current content
                all_texts = texts_to_embed.copy()
                for existing_doc in self._lattice._documents.values():
                    all_texts.append(existing_doc.content)
                    
                if all_texts:
                    self._embedding_engine.fit(all_texts)
                    self._is_fitted = True
                    
            # Generate embeddings
            embeddings = self._embedding_engine.embed_batch(texts_to_embed)
            
            for i, doc in enumerate(docs_needing_embeddings):
                docs_to_process[docs_to_process.index(doc)] = doc.with_embedding(embeddings[i])
                
        # Add documents to lattice
        for doc in docs_to_process:
            doc_id = self._lattice.add_document(doc)
            added_ids.append(doc_id)
            
        # Discover relationships if enabled
        if self._relationship_engine and len(added_ids) > 0:
            self._discover_and_add_relationships(added_ids)
            
        # Create snapshot
        self._create_snapshot("add", affected_ids=added_ids)
        
        # Record operation
        self._record_operation(
            operation_type="add",
            affected_ids=added_ids,
            metadata={"documents_added": len(added_ids)}
        )
        
        return added_ids
        
    def delete(self, *ids: str) -> Dict[str, bool]:
        """
        Delete documents by their IDs.
        
        Args:
            *ids: Document IDs to delete
            
        Returns:
            Dict mapping each ID to deletion success status
        """
        results = {}
        deleted_ids = []
        
        for doc_id in ids:
            success = self._lattice.remove_document(doc_id)
            results[doc_id] = success
            if success:
                deleted_ids.append(doc_id)
                
        # Create snapshot if any deletions occurred
        if deleted_ids:
            self._create_snapshot("delete", affected_ids=deleted_ids)
            
        # Record operation
        self._record_operation(
            operation_type="delete",
            affected_ids=list(ids),
            metadata={"deleted_count": len(deleted_ids), "results": results}
        )
        
        return results
        
    def roll(self, n: int) -> bool:
        """
        Rollback the last n operations.
        
        Args:
            n: Number of operations to rollback (negative for forward)
            
        Returns:
            True if rollback successful, False otherwise
        """
        if n == 0:
            return True
            
        target_version = self._current_version - n
        
        if target_version < 0 or target_version >= len(self._snapshots):
            return False
            
        # Find target snapshot
        target_snapshot = None
        for snapshot in self._snapshots:
            if snapshot.version == target_version:
                target_snapshot = snapshot
                break
                
        if target_snapshot is None:
            return False
            
        # Restore from snapshot
        success = self._restore_from_snapshot(target_snapshot)
        
        if success:
            self._current_version = target_version
            
            # Record rollback operation
            self._record_operation(
                operation_type="roll",
                metadata={
                    "rollback_steps": n,
                    "target_version": target_version,
                    "restored_snapshot_id": target_snapshot.id
                }
            )
            
        return success
        
    def _get_enrichment_config(
        self, 
        caller_id: Optional[str], 
        collection: Optional[str]
    ) -> QueryEnrichmentConfig:
        """Get effective enrichment configuration for the request."""
        # Start with global config
        config = self._global_config
        
        # Override with collection config if available
        if collection and collection in self._collection_configs:
            collection_config = self._collection_configs[collection]
            config = QueryEnrichmentConfig(
                **{**config.model_dump(), **collection_config.model_dump()}
            )
            
        # Override with caller config if available
        if caller_id and caller_id in self._caller_configs:
            caller_config = self._caller_configs[caller_id]
            config = QueryEnrichmentConfig(
                **{**config.model_dump(), **caller_config.model_dump()}
            )
            
        return config
        
    def _get_contextual_relationships(
        self, 
        documents: List[Document], 
        max_depth: int
    ) -> List[Relationship]:
        """Get relationships that provide context for the given documents."""
        relationships = []
        doc_ids = {doc.id for doc in documents}
        
        # Get direct relationships
        for rel in self._lattice._relationships.values():
            if rel.source_id in doc_ids or rel.target_id in doc_ids:
                relationships.append(rel)
                
        # Get extended relationships within depth
        if max_depth > 1:
            extended_ids = set()
            for doc in documents:
                connected = self._lattice.get_connected_documents(
                    doc.id, max_depth=max_depth-1
                )
                extended_ids.update(connected)
                
            # Add relationships involving extended documents
            for rel in self._lattice._relationships.values():
                if (rel.source_id in extended_ids or rel.target_id in extended_ids):
                    if rel not in relationships:
                        relationships.append(rel)
                        
        return relationships
        
    def _apply_context_enrichment(
        self,
        documents: List[Document],
        relationships: List[Relationship],
        config: QueryEnrichmentConfig
    ) -> Dict[str, Any]:
        """Apply context enrichment based on configuration."""
        enrichment = {
            "relationship_count": len(relationships),
            "connected_documents": len(set(
                rel.source_id for rel in relationships
            ).union(set(rel.target_id for rel in relationships))),
            "metadata_fields": []
        }
        
        # Extract requested metadata fields
        if config.include_metadata_fields:
            for doc in documents:
                for field in config.include_metadata_fields:
                    if field in doc.metadata:
                        enrichment["metadata_fields"].append({
                            "document_id": doc.id,
                            "field": field,
                            "value": doc.metadata[field]
                        })
                        
        # Apply custom transformations
        if config.custom_transformations:
            enrichment["custom_transformations"] = config.custom_transformations
            
        return enrichment
        
    def _auto_fit(self) -> None:
        """Auto-fit embedding engine on existing documents."""
        if self._lattice._documents:
            texts = [doc.content for doc in self._lattice._documents.values()]
            self._embedding_engine.fit(texts)
            self._is_fitted = True
            
    def _discover_and_add_relationships(self, new_doc_ids: List[str]) -> None:
        """Discover and add relationships for new documents."""
        if not self._relationship_engine:
            return
            
        # Discover semantic relationships
        semantic_rels = self._relationship_engine.discover_semantic_relationships(
            self._lattice._documents,
            self._lattice._vectors
        )
        
        # Add new relationships
        for rel in semantic_rels:
            if (rel.source_id in new_doc_ids or rel.target_id in new_doc_ids):
                self._lattice.add_relationship(rel)
                
    def _create_snapshot(self, operation_type: str, affected_ids: List[str]) -> None:
        """Create a snapshot of the current state."""
        self._current_version += 1
        
        # Create snapshot data
        lattice_snapshot = self._lattice.create_snapshot()
        checksum = self._compute_checksum(lattice_snapshot)
        
        snapshot = KnowledgeBaseSnapshot(
            version=self._current_version,
            operation_count=len(self._operations),
            document_count=len(self._lattice._documents),
            relationship_count=len(self._lattice._relationships),
            checksum=checksum,
            metadata={
                "operation_type": operation_type,
                "affected_ids": affected_ids,
                "lattice_snapshot": lattice_snapshot
            }
        )
        
        self._snapshots.append(snapshot)
        
        # Save to DVC if enabled
        if self._dvc_manager:
            self._dvc_manager.save_snapshot(snapshot)
            
    def _restore_from_snapshot(self, snapshot: KnowledgeBaseSnapshot) -> bool:
        """Restore knowledge base state from snapshot."""
        try:
            lattice_data = snapshot.metadata.get("lattice_snapshot")
            if not lattice_data:
                return False
                
            # Restore lattice
            self._lattice = VectorLattice.from_snapshot(lattice_data)
            
            # Verify checksum
            current_checksum = self._compute_checksum(lattice_data)
            if current_checksum != snapshot.checksum:
                return False
                
            return True
            
        except Exception:
            return False
            
    def _compute_checksum(self, data: Dict[str, Any]) -> str:
        """Compute checksum for data integrity verification."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
        
    def _record_operation(
        self,
        operation_type: str,
        caller_id: Optional[str] = None,
        affected_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an operation for audit trail."""
        operation = Operation(
            operation_type=operation_type,
            caller_id=caller_id,
            affected_ids=affected_ids or [],
            metadata=metadata or {}
        )
        self._operations.append(operation)
        
    def configure_enrichment(
        self,
        caller_id: Optional[str] = None,
        collection: Optional[str] = None,
        **config_kwargs
    ) -> None:
        """
        Configure query enrichment for caller or collection.
        
        Args:
            caller_id: Caller ID to configure (None for global)
            collection: Collection to configure
            **config_kwargs: Configuration parameters
        """
        config = QueryEnrichmentConfig(**config_kwargs)
        
        if caller_id:
            self._caller_configs[caller_id] = config
        elif collection:
            self._collection_configs[collection] = config
        else:
            self._global_config = config
            
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base statistics."""
        lattice_stats = self._lattice.get_stats()
        
        stats = {
            **lattice_stats,
            "operations": len(self._operations),
            "snapshots": len(self._snapshots),
            "current_version": self._current_version,
            "is_fitted": self._is_fitted,
            "caller_configs": len(self._caller_configs),
            "collection_configs": len(self._collection_configs),
        }
        
        if self._relationship_engine:
            stats["relationship_analytics"] = self._relationship_engine.get_relationship_analytics()
            
        if self._embedding_engine:
            stats["embedding_stats"] = self._embedding_engine.get_vocabulary_stats()
            
        return stats