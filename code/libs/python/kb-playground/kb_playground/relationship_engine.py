"""
Relationship Engine - Intelligent relationship discovery and management.

Automatically discovers implicit relationships between documents based on
semantic similarity, co-occurrence patterns, and usage analytics.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
import time

from .models import Document, Relationship


class RelationshipEngine:
    """
    Intelligent relationship discovery and strengthening engine.
    
    Discovers implicit relationships through:
    1. Semantic similarity clustering
    2. Co-access pattern analysis  
    3. Content overlap detection
    4. Temporal proximity analysis
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.75,
        co_access_threshold: int = 3,
        temporal_window_minutes: int = 30
    ):
        """
        Initialize relationship engine.
        
        Args:
            similarity_threshold: Minimum cosine similarity for auto-relationships
            co_access_threshold: Minimum co-access count for relationship creation
            temporal_window_minutes: Time window for temporal relationship detection
        """
        self.similarity_threshold = similarity_threshold
        self.co_access_threshold = co_access_threshold
        self.temporal_window_minutes = temporal_window_minutes
        
        # Analytics tracking
        self._access_patterns: Dict[str, List[float]] = defaultdict(list)  # doc_id -> timestamps
        self._co_access_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        self._relationship_strengths: Dict[str, float] = {}
        
    def discover_semantic_relationships(
        self,
        documents: Dict[str, Document],
        vectors: Dict[str, np.ndarray],
        max_relationships_per_doc: int = 10
    ) -> List[Relationship]:
        """
        Discover relationships based on semantic similarity.
        
        Args:
            documents: Document dictionary
            vectors: Vector embeddings dictionary
            max_relationships_per_doc: Maximum relationships per document
            
        Returns:
            List of discovered relationships
        """
        relationships = []
        doc_ids = list(documents.keys())
        
        for i, doc_id_a in enumerate(doc_ids):
            if doc_id_a not in vectors:
                continue
                
            similarities = []
            vector_a = vectors[doc_id_a]
            
            for j, doc_id_b in enumerate(doc_ids):
                if i >= j or doc_id_b not in vectors:  # Avoid duplicates and self
                    continue
                    
                vector_b = vectors[doc_id_b]
                similarity = np.dot(vector_a, vector_b)
                
                if similarity >= self.similarity_threshold:
                    similarities.append((doc_id_b, similarity))
                    
            # Sort by similarity and take top relationships
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarities = similarities[:max_relationships_per_doc]
            
            # Create relationships
            for doc_id_b, similarity in similarities:
                rel = Relationship(
                    source_id=doc_id_a,
                    target_id=doc_id_b,
                    relationship_type="semantic_similarity",
                    strength=min(1.0, float(similarity)),  # Ensure <= 1.0
                    is_bidirectional=True,
                    metadata={
                        "discovery_method": "semantic_similarity",
                        "similarity_score": similarity,
                        "auto_discovered": True
                    }
                )
                relationships.append(rel)
                
        return relationships
        
    def track_access(self, doc_id: str, timestamp: Optional[float] = None) -> None:
        """
        Track document access for co-access pattern analysis.
        
        Args:
            doc_id: Document ID that was accessed
            timestamp: Access timestamp (default: current time)
        """
        if timestamp is None:
            timestamp = time.time()
            
        self._access_patterns[doc_id].append(timestamp)
        
        # Clean old access records (keep last 1000 per document)
        if len(self._access_patterns[doc_id]) > 1000:
            self._access_patterns[doc_id] = self._access_patterns[doc_id][-1000:]
            
    def discover_co_access_relationships(
        self,
        documents: Dict[str, Document]
    ) -> List[Relationship]:
        """
        Discover relationships based on co-access patterns.
        
        Documents accessed within the temporal window are considered related.
        
        Args:
            documents: Document dictionary
            
        Returns:
            List of co-access based relationships
        """
        relationships = []
        current_time = time.time()
        window_seconds = self.temporal_window_minutes * 60
        
        # Find co-access patterns within temporal window
        for doc_id_a, timestamps_a in self._access_patterns.items():
            if doc_id_a not in documents:
                continue
                
            # Get recent accesses
            recent_a = [t for t in timestamps_a if current_time - t <= window_seconds]
            if not recent_a:
                continue
                
            for doc_id_b, timestamps_b in self._access_patterns.items():
                if doc_id_a >= doc_id_b or doc_id_b not in documents:  # Avoid duplicates
                    continue
                    
                recent_b = [t for t in timestamps_b if current_time - t <= window_seconds]
                if not recent_b:
                    continue
                    
                # Count co-accesses within window
                co_access_count = 0
                for t_a in recent_a:
                    for t_b in recent_b:
                        if abs(t_a - t_b) <= window_seconds:
                            co_access_count += 1
                            
                if co_access_count >= self.co_access_threshold:
                    # Update co-access counter
                    key = (doc_id_a, doc_id_b)
                    self._co_access_counts[key] += co_access_count
                    
                    # Calculate relationship strength based on co-access frequency
                    total_accesses = len(recent_a) + len(recent_b)
                    strength = min(1.0, co_access_count / total_accesses)
                    
                    rel = Relationship(
                        source_id=doc_id_a,
                        target_id=doc_id_b,
                        relationship_type="co_access_pattern",
                        strength=strength,
                        is_bidirectional=True,
                        metadata={
                            "discovery_method": "co_access_pattern",
                            "co_access_count": co_access_count,
                            "temporal_window_minutes": self.temporal_window_minutes,
                            "auto_discovered": True
                        }
                    )
                    relationships.append(rel)
                    
        return relationships
        
    def strengthen_relationship(
        self,
        relationship: Relationship,
        boost_factor: float = 0.1
    ) -> Relationship:
        """
        Strengthen an existing relationship based on usage patterns.
        
        Args:
            relationship: Relationship to strengthen
            boost_factor: Strength boost factor
            
        Returns:
            Updated relationship with increased strength
        """
        new_strength = min(1.0, relationship.strength + boost_factor)
        
        return relationship.with_strength(new_strength).model_copy(update={
            "metadata": {
                **relationship.metadata,
                "last_strengthened": time.time(),
                "strength_boosts": relationship.metadata.get("strength_boosts", 0) + 1
            }
        })
        
    def weaken_relationship(
        self,
        relationship: Relationship,
        decay_factor: float = 0.05
    ) -> Relationship:
        """
        Weaken a relationship due to lack of usage.
        
        Args:
            relationship: Relationship to weaken
            decay_factor: Strength decay factor
            
        Returns:
            Updated relationship with decreased strength
        """
        new_strength = max(0.0, relationship.strength - decay_factor)
        
        return relationship.with_strength(new_strength).model_copy(update={
            "metadata": {
                **relationship.metadata,
                "last_weakened": time.time(),
                "strength_decays": relationship.metadata.get("strength_decays", 0) + 1
            }
        })
        
    def discover_content_overlap_relationships(
        self,
        documents: Dict[str, Document],
        min_overlap_ratio: float = 0.3
    ) -> List[Relationship]:
        """
        Discover relationships based on content overlap.
        
        Args:
            documents: Document dictionary
            min_overlap_ratio: Minimum word overlap ratio for relationship
            
        Returns:
            List of content overlap relationships
        """
        relationships = []
        doc_ids = list(documents.keys())
        
        # Simple word-based overlap (can be enhanced with more sophisticated NLP)
        for i, doc_id_a in enumerate(doc_ids):
            doc_a = documents[doc_id_a]
            words_a = set(doc_a.content.lower().split())
            
            for j, doc_id_b in enumerate(doc_ids):
                if i >= j:  # Avoid duplicates and self
                    continue
                    
                doc_b = documents[doc_id_b]
                words_b = set(doc_b.content.lower().split())
                
                # Calculate overlap ratio
                intersection = words_a.intersection(words_b)
                union = words_a.union(words_b)
                
                if len(union) == 0:
                    continue
                    
                overlap_ratio = len(intersection) / len(union)
                
                if overlap_ratio >= min_overlap_ratio:
                    rel = Relationship(
                        source_id=doc_id_a,
                        target_id=doc_id_b,
                        relationship_type="content_overlap",
                        strength=overlap_ratio,
                        is_bidirectional=True,
                        metadata={
                            "discovery_method": "content_overlap",
                            "overlap_ratio": overlap_ratio,
                            "shared_words": len(intersection),
                            "auto_discovered": True
                        }
                    )
                    relationships.append(rel)
                    
        return relationships
        
    def prune_weak_relationships(
        self,
        relationships: List[Relationship],
        min_strength: float = 0.1,
        max_age_days: int = 30
    ) -> List[Relationship]:
        """
        Remove weak or stale relationships.
        
        Args:
            relationships: List of relationships to prune
            min_strength: Minimum strength threshold
            max_age_days: Maximum age in days
            
        Returns:
            Filtered list of relationships
        """
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        pruned = []
        for rel in relationships:
            # Check strength threshold
            if rel.strength < min_strength:
                continue
                
            # Check age
            age_seconds = current_time - rel.created_at.timestamp()
            if age_seconds > max_age_seconds:
                continue
                
            pruned.append(rel)
            
        return pruned
        
    def get_relationship_analytics(self) -> Dict[str, any]:
        """
        Get analytics about relationship discovery and usage.
        
        Returns:
            Dictionary with relationship analytics
        """
        total_accesses = sum(len(timestamps) for timestamps in self._access_patterns.values())
        total_co_accesses = sum(self._co_access_counts.values())
        
        return {
            "tracked_documents": len(self._access_patterns),
            "total_accesses": total_accesses,
            "total_co_accesses": total_co_accesses,
            "unique_co_access_pairs": len(self._co_access_counts),
            "similarity_threshold": self.similarity_threshold,
            "co_access_threshold": self.co_access_threshold,
            "temporal_window_minutes": self.temporal_window_minutes,
        }