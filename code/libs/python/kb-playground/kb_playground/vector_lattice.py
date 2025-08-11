"""
Vector Lattice - Core vector operations with relationship awareness.

Implements the hybrid vector-graph structure where documents are vectors
and relationships provide additional context for similarity computation.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Set
import time
from collections import defaultdict

from .models import Document, Relationship, SearchResult


class VectorLattice:
    """
    High-performance vector lattice with relationship-aware similarity.
    
    Combines traditional vector similarity with graph connectivity for
    superior context retrieval. Designed for immutability and fast queries.
    """
    
    def __init__(self, dimension: int = 384):
        """
        Initialize vector lattice.
        
        Args:
            dimension: Vector embedding dimension (default: 384 for efficiency)
        """
        self.dimension = dimension
        self._vectors: Dict[str, np.ndarray] = {}
        self._documents: Dict[str, Document] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)
        
        # Performance optimization: pre-computed similarity matrix for small sets
        self._similarity_cache: Dict[Tuple[str, str], float] = {}
        self._cache_threshold = 1000  # Cache similarities for sets < 1000 docs
        
    def add_document(self, document: Document) -> str:
        """
        Add document to the lattice.
        
        Args:
            document: Document with embedding
            
        Returns:
            Document ID
            
        Raises:
            ValueError: If document has no embedding
        """
        if document.embedding is None:
            raise ValueError(f"Document {document.id} must have embedding")
            
        embedding = np.array(document.embedding, dtype=np.float32)
        if embedding.shape[0] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embedding.shape[0]} != {self.dimension}"
            )
            
        # Normalize for cosine similarity
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        self._vectors[document.id] = embedding
        self._documents[document.id] = document
        
        # Clear similarity cache if it's getting large
        if len(self._vectors) > self._cache_threshold:
            self._similarity_cache.clear()
            
        return document.id
        
    def add_relationship(self, relationship: Relationship) -> str:
        """
        Add relationship to the lattice.
        
        Args:
            relationship: Relationship between documents
            
        Returns:
            Relationship ID
        """
        self._relationships[relationship.id] = relationship
        
        # Update adjacency lists
        self._adjacency[relationship.source_id].add(relationship.target_id)
        self._reverse_adjacency[relationship.target_id].add(relationship.source_id)
        
        if relationship.is_bidirectional:
            self._adjacency[relationship.target_id].add(relationship.source_id)
            self._reverse_adjacency[relationship.source_id].add(relationship.target_id)
            
        return relationship.id
        
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove document and its relationships.
        
        Args:
            doc_id: Document ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if doc_id not in self._documents:
            return False
            
        # Remove from vectors and documents
        del self._vectors[doc_id]
        del self._documents[doc_id]
        
        # Remove relationships
        to_remove = []
        for rel_id, rel in self._relationships.items():
            if rel.source_id == doc_id or rel.target_id == doc_id:
                to_remove.append(rel_id)
                
        for rel_id in to_remove:
            self.remove_relationship(rel_id)
            
        # Clear from adjacency
        if doc_id in self._adjacency:
            del self._adjacency[doc_id]
        if doc_id in self._reverse_adjacency:
            del self._reverse_adjacency[doc_id]
            
        # Clear similarity cache entries
        cache_keys_to_remove = [
            key for key in self._similarity_cache.keys() 
            if doc_id in key
        ]
        for key in cache_keys_to_remove:
            del self._similarity_cache[key]
            
        return True
        
    def remove_relationship(self, rel_id: str) -> bool:
        """
        Remove relationship from lattice.
        
        Args:
            rel_id: Relationship ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if rel_id not in self._relationships:
            return False
            
        rel = self._relationships[rel_id]
        del self._relationships[rel_id]
        
        # Update adjacency lists
        self._adjacency[rel.source_id].discard(rel.target_id)
        self._reverse_adjacency[rel.target_id].discard(rel.source_id)
        
        if rel.is_bidirectional:
            self._adjacency[rel.target_id].discard(rel.source_id)
            self._reverse_adjacency[rel.source_id].discard(rel.target_id)
            
        return True
        
    def search(
        self, 
        query_vector: np.ndarray, 
        top_k: int = 10,
        relationship_boost: float = 0.2,
        min_similarity: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Search for similar documents with relationship awareness.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            relationship_boost: Boost factor for connected documents
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (document_id, score) tuples sorted by relevance
        """
        if len(self._vectors) == 0:
            return []
            
        # Normalize query vector
        query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        
        # Compute base similarities
        similarities = {}
        for doc_id, doc_vector in self._vectors.items():
            similarity = np.dot(query_vector, doc_vector)
            if similarity >= min_similarity:
                similarities[doc_id] = similarity
                
        # Apply relationship boosting
        if relationship_boost > 0:
            similarities = self._apply_relationship_boost(
                similarities, relationship_boost
            )
            
        # Sort and return top-k
        sorted_results = sorted(
            similarities.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return sorted_results[:top_k]
        
    def _apply_relationship_boost(
        self, 
        similarities: Dict[str, float], 
        boost_factor: float
    ) -> Dict[str, float]:
        """
        Apply relationship-based boosting to similarity scores.
        
        Documents connected to high-scoring documents get a boost.
        """
        boosted = similarities.copy()
        
        # Sort by current similarity to prioritize high-scoring docs
        sorted_docs = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        
        # Apply boost based on connections to top documents
        for doc_id, base_score in sorted_docs:
            # Boost connected documents
            for connected_id in self._adjacency.get(doc_id, set()):
                if connected_id in boosted:
                    # Get relationship strength
                    rel_strength = self._get_relationship_strength(doc_id, connected_id)
                    boost = base_score * boost_factor * rel_strength
                    boosted[connected_id] = min(1.0, boosted[connected_id] + boost)
                    
        return boosted
        
    def _get_relationship_strength(self, source_id: str, target_id: str) -> float:
        """Get the strength of relationship between two documents."""
        for rel in self._relationships.values():
            if ((rel.source_id == source_id and rel.target_id == target_id) or
                (rel.is_bidirectional and rel.source_id == target_id and rel.target_id == source_id)):
                return rel.strength
        return 1.0  # Default strength
        
    def get_connected_documents(
        self, 
        doc_id: str, 
        max_depth: int = 2,
        min_strength: float = 0.1
    ) -> List[str]:
        """
        Get documents connected within max_depth hops.
        
        Args:
            doc_id: Starting document ID
            max_depth: Maximum relationship depth to traverse
            min_strength: Minimum relationship strength threshold
            
        Returns:
            List of connected document IDs
        """
        if doc_id not in self._documents:
            return []
            
        visited = set()
        current_level = {doc_id}
        
        for depth in range(max_depth):
            next_level = set()
            
            for current_doc in current_level:
                if current_doc in visited:
                    continue
                    
                visited.add(current_doc)
                
                # Get connected documents with sufficient strength
                for connected_id in self._adjacency.get(current_doc, set()):
                    strength = self._get_relationship_strength(current_doc, connected_id)
                    if strength >= min_strength and connected_id not in visited:
                        next_level.add(connected_id)
                        
            current_level = next_level
            if not current_level:
                break
                
        visited.discard(doc_id)  # Remove starting document
        return list(visited)
        
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self._documents.get(doc_id)
        
    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        """Get relationship by ID."""
        return self._relationships.get(rel_id)
        
    def get_stats(self) -> Dict[str, int]:
        """Get lattice statistics."""
        return {
            "documents": len(self._documents),
            "relationships": len(self._relationships),
            "dimension": self.dimension,
            "cache_size": len(self._similarity_cache),
        }
        
    def create_snapshot(self) -> Dict[str, any]:
        """
        Create immutable snapshot of current state.
        
        Returns:
            Serializable snapshot data
        """
        return {
            "dimension": self.dimension,
            "documents": {doc_id: doc.model_dump() for doc_id, doc in self._documents.items()},
            "relationships": {rel_id: rel.model_dump() for rel_id, rel in self._relationships.items()},
            "vectors": {doc_id: vec.tolist() for doc_id, vec in self._vectors.items()},
        }
        
    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, any]) -> "VectorLattice":
        """
        Restore lattice from snapshot.
        
        Args:
            snapshot: Snapshot data from create_snapshot()
            
        Returns:
            Restored VectorLattice instance
        """
        lattice = cls(dimension=snapshot["dimension"])
        
        # Restore documents and vectors
        for doc_id, doc_data in snapshot["documents"].items():
            doc = Document(**doc_data)
            lattice._documents[doc_id] = doc
            if doc_id in snapshot["vectors"]:
                lattice._vectors[doc_id] = np.array(snapshot["vectors"][doc_id], dtype=np.float32)
                
        # Restore relationships
        for rel_id, rel_data in snapshot["relationships"].items():
            rel = Relationship(**rel_data)
            lattice.add_relationship(rel)
            
        return lattice