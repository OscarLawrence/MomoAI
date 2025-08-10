"""
Hybrid Knowledge Base Implementation
Combines vector similarity search with graph-based relationship traversal.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
import json
import math
from dataclasses import dataclass, field


@dataclass
class Node:
    """A node in the hybrid knowledge base."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    vector: Optional[List[float]] = None
    connections: Set[str] = field(default_factory=set)


@dataclass
class Edge:
    """An edge connecting two nodes."""
    from_node: str
    to_node: str
    relationship: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleEmbedder:
    """Simple text embedder using character frequency."""
    
    def embed(self, text: str) -> List[float]:
        """Create a simple embedding based on character frequency."""
        # Create 26-dimensional vector for a-z frequency
        vector = [0.0] * 26
        text_lower = text.lower()
        total_chars = 0
        
        for char in text_lower:
            if 'a' <= char <= 'z':
                vector[ord(char) - ord('a')] += 1
                total_chars += 1
        
        # Normalize to frequencies
        if total_chars > 0:
            vector = [count / total_chars for count in vector]
        
        return vector


class HybridKB:
    """Hybrid Knowledge Base combining vector search with graph traversal."""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.embedder = SimpleEmbedder()
    
    def add_node(self, node_id: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a node to the knowledge base."""
        vector = self.embedder.embed(content)
        self.nodes[node_id] = Node(
            id=node_id,
            content=content,
            metadata=metadata or {},
            vector=vector
        )
    
    def add_edge(self, from_node: str, to_node: str, relationship: str, 
                 weight: float = 1.0, metadata: Optional[Dict] = None) -> None:
        """Add an edge between two nodes."""
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist before creating edge")
        
        edge = Edge(from_node, to_node, relationship, weight, metadata or {})
        self.edges.append(edge)
        
        # Update node connections
        self.nodes[from_node].connections.add(to_node)
        self.nodes[to_node].connections.add(from_node)
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def vector_search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search nodes by vector similarity."""
        query_vector = self.embedder.embed(query)
        similarities = []
        
        for node_id, node in self.nodes.items():
            if node.vector:
                similarity = self.cosine_similarity(query_vector, node.vector)
                similarities.append((node_id, similarity))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def graph_traverse(self, start_node: str, max_depth: int = 2) -> Set[str]:
        """Traverse the graph from a starting node."""
        if start_node not in self.nodes:
            return set()
        
        visited = set()
        queue = [(start_node, 0)]
        
        while queue:
            current_node, depth = queue.pop(0)
            
            if current_node in visited or depth > max_depth:
                continue
            
            visited.add(current_node)
            
            # Add connected nodes to queue
            for connected_node in self.nodes[current_node].connections:
                if connected_node not in visited:
                    queue.append((connected_node, depth + 1))
        
        return visited
    
    def hybrid_search(self, query: str, top_k: int = 5, expand_graph: bool = True) -> List[Dict]:
        """Perform hybrid search combining vector similarity and graph traversal."""
        # First, get vector similarity results
        vector_results = self.vector_search(query, top_k)
        
        result_nodes = set()
        for node_id, similarity in vector_results:
            result_nodes.add(node_id)
            
            # Optionally expand using graph traversal
            if expand_graph:
                connected_nodes = self.graph_traverse(node_id, max_depth=1)
                result_nodes.update(connected_nodes)
        
        # Build enriched results
        results = []
        for node_id in result_nodes:
            node = self.nodes[node_id]
            
            # Calculate similarity score
            similarity = 0.0
            if node.vector:
                query_vector = self.embedder.embed(query)
                similarity = self.cosine_similarity(query_vector, node.vector)
            
            results.append({
                'node_id': node_id,
                'content': node.content,
                'similarity': similarity,
                'metadata': node.metadata,
                'connections': list(node.connections)
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k * 2]  # Return more results due to graph expansion
    
    def get_relationships(self, node_id: str) -> List[Dict]:
        """Get all relationships for a node."""
        relationships = []
        for edge in self.edges:
            if edge.from_node == node_id:
                relationships.append({
                    'to': edge.to_node,
                    'relationship': edge.relationship,
                    'weight': edge.weight,
                    'metadata': edge.metadata
                })
            elif edge.to_node == node_id:
                relationships.append({
                    'from': edge.from_node,
                    'relationship': edge.relationship,
                    'weight': edge.weight,
                    'metadata': edge.metadata
                })
        return relationships
    
    def export_data(self) -> Dict:
        """Export knowledge base data."""
        return {
            'nodes': {
                node_id: {
                    'content': node.content,
                    'metadata': node.metadata,
                    'vector': node.vector
                }
                for node_id, node in self.nodes.items()
            },
            'edges': [
                {
                    'from_node': edge.from_node,
                    'to_node': edge.to_node,
                    'relationship': edge.relationship,
                    'weight': edge.weight,
                    'metadata': edge.metadata
                }
                for edge in self.edges
            ]
        }
    
    def stats(self) -> Dict:
        """Get knowledge base statistics."""
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'avg_connections_per_node': (
                sum(len(node.connections) for node in self.nodes.values()) / 
                len(self.nodes) if self.nodes else 0
            )
        }