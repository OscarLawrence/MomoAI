"""
Semantic search capabilities for Momo KnowledgeBase.

Provides embedding generation, vector indexing, and semantic similarity search.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .models import Node, SemanticQueryResult, HybridQueryResult


class EmbeddingManager:
    """Manages embedding generation for different models."""
    
    def __init__(self):
        self.models = {}
        self._setup_models()
    
    def _setup_models(self):
        """Setup available embedding models."""
        try:
            import openai
            self.models["openai-ada-002"] = "openai"
        except ImportError:
            pass
        
        # Placeholder for other models
        self.models["sentence-transformers"] = "mock"
    
    async def generate_embedding(
        self, 
        text: str, 
        model: str = "openai-ada-002"
    ) -> List[float]:
        """Generate embedding for text using specified model."""
        if model not in self.models:
            raise ValueError(f"Model {model} not available")
        
        if model == "openai-ada-002":
            return await self._generate_openai_embedding(text)
        else:
            # Mock implementation for testing
            return self._generate_mock_embedding(text)
    
    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding."""
        try:
            import openai
            # This would use actual OpenAI API in production
            # For now, return mock embedding of correct size
            return [0.1] * 1536  # OpenAI ada-002 dimension
        except Exception:
            # Fallback to mock for testing
            return self._generate_mock_embedding(text)
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for testing."""
        # Simple hash-based mock embedding
        hash_val = hash(text)
        np.random.seed(abs(hash_val) % (2**32))
        return np.random.random(384).tolist()  # Smaller dimension for testing
    
    async def embed_node_content(self, node: Node, model: str = "openai-ada-002") -> Node:
        """Generate embedding for node content."""
        content = self._extract_embeddable_content(node)
        embedding = await self.generate_embedding(content, model)
        return node.with_embedding(embedding, model)
    
    def _extract_embeddable_content(self, node: Node) -> str:
        """Extract text content from node for embedding."""
        parts = [node.label]
        
        # Add string properties
        for key, value in node.properties.items():
            if isinstance(value, str):
                parts.append(f"{key}: {value}")
            elif isinstance(value, (int, float, bool)):
                parts.append(f"{key}: {str(value)}")
        
        return " ".join(parts)


class VectorIndex:
    """Vector index for similarity search."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.embeddings = {}  # node_id -> embedding
        self.node_ids = []
        self.embedding_matrix = None
        
    def add_vectors(self, node_ids: List[str], embeddings: List[List[float]]):
        """Add vectors to the index."""
        for node_id, embedding in zip(node_ids, embeddings):
            self.embeddings[node_id] = np.array(embedding)
            if node_id not in self.node_ids:
                self.node_ids.append(node_id)
        
        self._rebuild_matrix()
    
    def _rebuild_matrix(self):
        """Rebuild the embedding matrix for efficient search."""
        if not self.embeddings:
            self.embedding_matrix = None
            return
        
        embeddings_list = [self.embeddings[node_id] for node_id in self.node_ids]
        self.embedding_matrix = np.vstack(embeddings_list)
    
    def similarity_search(
        self, 
        query_embedding: List[float], 
        k: int = 10
    ) -> List[Tuple[str, float]]:
        """Search for similar embeddings using cosine similarity."""
        if self.embedding_matrix is None or len(self.node_ids) == 0:
            return []
        
        query_vec = np.array(query_embedding)
        
        # Compute cosine similarities
        similarities = np.dot(self.embedding_matrix, query_vec) / (
            np.linalg.norm(self.embedding_matrix, axis=1) * np.linalg.norm(query_vec)
        )
        
        # Get top-k results
        top_indices = np.argsort(similarities)[-k:][::-1]
        return [(self.node_ids[i], float(similarities[i])) for i in top_indices]
    
    def remove_vector(self, node_id: str):
        """Remove a vector from the index."""
        if node_id in self.embeddings:
            del self.embeddings[node_id]
            self.node_ids.remove(node_id)
            self._rebuild_matrix()
    
    def size(self) -> int:
        """Get the number of vectors in the index."""
        return len(self.embeddings)
    
    def get_node_ids(self) -> List[str]:
        """Get all node IDs in the index."""
        return self.node_ids.copy()


class SemanticSearch:
    """High-level semantic search interface."""
    
    def __init__(self, kb):
        self.kb = kb
        self.embedding_manager = EmbeddingManager()
        self.vector_index = VectorIndex()
    
    async def search_nodes(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0
    ) -> SemanticQueryResult:
        """Search for nodes semantically similar to query."""
        start_time = time.perf_counter()
        
        # Generate query embedding
        query_embedding = await self.embedding_manager.generate_embedding(query)
        
        # Search for similar embeddings
        similar_results = self.vector_index.similarity_search(query_embedding, k=top_k)
        
        # Filter by threshold
        filtered_results = [
            (node_id, score) for node_id, score in similar_results 
            if score >= threshold
        ]
        
        # Get actual nodes (this would integrate with KB storage)
        nodes = []
        scores = []
        for node_id, score in filtered_results:
            # For now, create mock nodes - would integrate with actual KB
            node = Node(
                id=node_id,
                label="MockNode",
                properties={"semantic_search": True}
            )
            nodes.append(node)
            scores.append(score)
        
        query_time = (time.perf_counter() - start_time) * 1000
        
        return SemanticQueryResult(
            nodes=nodes,
            similarity_scores=scores,
            query_embedding=query_embedding,
            threshold=threshold,
            query_time_ms=query_time
        )
    
    async def hybrid_search(
        self,
        semantic_query: str = None,
        structural_filters: Dict[str, Any] = None,
        alpha: float = 0.5
    ) -> HybridQueryResult:
        """Combine semantic similarity with structural filtering."""
        start_time = time.perf_counter()
        
        # Mock implementation for now
        nodes = [Node(label="HybridResult", properties={"test": True})]
        semantic_scores = [0.85]
        structural_matches = [True]
        combined_scores = [alpha * 0.85 + (1 - alpha) * 1.0]
        
        query_time = (time.perf_counter() - start_time) * 1000
        
        return HybridQueryResult(
            nodes=nodes,
            semantic_scores=semantic_scores,
            structural_matches=structural_matches,
            combined_scores=combined_scores,
            alpha=alpha,
            query_time_ms=query_time
        )
    
    async def find_similar_nodes(
        self,
        reference_node: Node,
        top_k: int = 5,
        exclude_self: bool = True
    ) -> SemanticQueryResult:
        """Find nodes similar to a reference node."""
        if reference_node.embedding is None:
            # Generate embedding if not present
            embedded_node = await self.embedding_manager.embed_node_content(reference_node)
            query_embedding = embedded_node.embedding
        else:
            query_embedding = reference_node.embedding
        
        # Search for similar embeddings
        similar_results = self.vector_index.similarity_search(query_embedding, k=top_k + 1)
        
        # Exclude self if requested
        if exclude_self:
            similar_results = [
                (node_id, score) for node_id, score in similar_results
                if node_id != reference_node.id
            ][:top_k]
        
        # Mock nodes for now
        nodes = []
        scores = []
        for node_id, score in similar_results:
            node = Node(
                id=node_id,
                label="SimilarNode",
                properties={"similar_to": reference_node.id}
            )
            nodes.append(node)
            scores.append(score)
        
        return SemanticQueryResult(
            nodes=nodes,
            similarity_scores=scores,
            query_embedding=query_embedding,
            threshold=0.0,
            query_time_ms=10.0  # Mock timing
        )
    
    async def get_recommendations(
        self,
        interests: List[str],
        top_k: int = 10,
        diversity_threshold: float = 0.8
    ) -> SemanticQueryResult:
        """Get recommendations based on user interests."""
        # Combine interests into single query
        combined_query = " ".join(interests)
        
        result = await self.search_nodes(combined_query, top_k=top_k)
        
        # Add diversity scores (mock for now)
        result.metadata = {"diversity_scores": [0.9] * len(result.nodes)}
        
        return result
    
    async def contextual_search(
        self,
        context: List[str],
        max_results: int = 15
    ) -> SemanticQueryResult:
        """Search based on conversation context."""
        # Combine context into query
        context_query = " ".join(context)
        
        result = await self.search_nodes(context_query, top_k=max_results)
        
        # Add context relevance scores (mock for now)
        result.metadata = {"context_relevance_scores": [0.8] * len(result.nodes)}
        
        return result