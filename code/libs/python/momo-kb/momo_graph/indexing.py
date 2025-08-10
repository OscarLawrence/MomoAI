"""
High-performance indexing system for Momo Graph Backend.

Implements B-tree style indexes for labels, properties, and relationships
to achieve sub-millisecond query performance for graph data.
"""

from collections import defaultdict
from typing import Any, Dict, List, Set, Optional, Union
import bisect

from .models import GraphNode, GraphEdge


class PropertyIndex:
    """
    B-tree style index for node/edge properties.
    Supports exact matches and range queries.
    """
    
    def __init__(self):
        # Property name -> property value -> set of entity IDs
        self._exact_index: Dict[str, Dict[Any, Set[str]]] = defaultdict(lambda: defaultdict(set))
        
        # For numeric properties: property name -> sorted list of (value, entity_id) tuples
        self._range_index: Dict[str, List[tuple]] = defaultdict(list)
        
        # Track which properties are numeric for range queries
        self._numeric_properties: Set[str] = set()
        
    def add_entity(self, entity_id: str, properties: Dict[str, Any]) -> None:
        """Add an entity (node or edge) to the indexes."""
        for prop_name, prop_value in properties.items():
            # Only index hashable values for exact match
            try:
                # Test if value is hashable
                hash(prop_value)
                self._exact_index[prop_name][prop_value].add(entity_id)
            except TypeError:
                # Skip unhashable types (lists, dicts, etc.) for exact indexing
                # They can still be stored and queried via full scan if needed
                pass
            
            # Add to range index if numeric
            if isinstance(prop_value, (int, float)):
                self._numeric_properties.add(prop_name)
                # Insert in sorted order
                bisect.insort(self._range_index[prop_name], (prop_value, entity_id))
                
    def remove_entity(self, entity_id: str, properties: Dict[str, Any]) -> None:
        """Remove an entity from the indexes."""
        for prop_name, prop_value in properties.items():
            # Remove from exact match index (only if hashable)
            try:
                hash(prop_value)
                if prop_name in self._exact_index and prop_value in self._exact_index[prop_name]:
                    self._exact_index[prop_name][prop_value].discard(entity_id)
                    if not self._exact_index[prop_name][prop_value]:
                        del self._exact_index[prop_name][prop_value]
            except TypeError:
                # Skip unhashable types
                pass
                    
            # Remove from range index if numeric
            if isinstance(prop_value, (int, float)) and prop_name in self._range_index:
                try:
                    self._range_index[prop_name].remove((prop_value, entity_id))
                except ValueError:
                    pass  # Already removed
                    
    def find_exact(self, property_name: str, value: Any) -> Set[str]:
        """Find entities with exact property value match."""
        return self._exact_index[property_name].get(value, set()).copy()
        
    def find_range(self, property_name: str, min_value: Any = None, max_value: Any = None) -> Set[str]:
        """Find entities with property values in range [min_value, max_value]."""
        if property_name not in self._numeric_properties:
            return set()
            
        result = set()
        range_data = self._range_index[property_name]
        
        # Find start and end indices
        start_idx = 0
        end_idx = len(range_data)
        
        if min_value is not None:
            start_idx = bisect.bisect_left(range_data, (min_value, ''))
            
        if max_value is not None:
            end_idx = bisect.bisect_right(range_data, (max_value, '\uffff'))
            
        # Collect entity IDs in range
        for i in range(start_idx, end_idx):
            result.add(range_data[i][1])
            
        return result
        
    def find_multiple_properties(self, property_filters: Dict[str, Any]) -> Set[str]:
        """Find entities matching multiple property filters (AND operation)."""
        if not property_filters:
            return set()
            
        # Start with first property filter
        first_prop, first_value = next(iter(property_filters.items()))
        result = self.find_exact(first_prop, first_value)
        
        # Intersect with remaining property filters
        for prop_name, prop_value in list(property_filters.items())[1:]:
            if not result:  # Early termination if no matches
                break
            result &= self.find_exact(prop_name, prop_value)
            
        return result


class LabelIndex:
    """
    Fast label-based index for nodes and edges.
    """
    
    def __init__(self):
        # Label -> set of entity IDs
        self._label_index: Dict[str, Set[str]] = defaultdict(set)
        
    def add_entity(self, entity_id: str, label: str) -> None:
        """Add an entity to the label index."""
        self._label_index[label].add(entity_id)
        
    def remove_entity(self, entity_id: str, label: str) -> None:
        """Remove an entity from the label index."""
        self._label_index[label].discard(entity_id)
        if not self._label_index[label]:
            del self._label_index[label]
            
    def find_by_label(self, label: str) -> Set[str]:
        """Find all entities with the given label."""
        return self._label_index[label].copy()
        
    def get_all_labels(self) -> List[str]:
        """Get all available labels."""
        return list(self._label_index.keys())


class RelationshipIndex:
    """
    Index for edge relationships and connections.
    """
    
    def __init__(self):
        # Relationship type -> set of edge IDs
        self._relationship_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Source node -> set of edge IDs
        self._source_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Target node -> set of edge IDs  
        self._target_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Combined indexes for faster traversal
        # (source_id, relationship) -> set of target_ids
        self._outgoing_index: Dict[tuple, Set[str]] = defaultdict(set)
        
        # (target_id, relationship) -> set of source_ids
        self._incoming_index: Dict[tuple, Set[str]] = defaultdict(set)
        
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to all relationship indexes."""
        # Basic indexes
        self._relationship_index[edge.relationship].add(edge.id)
        self._source_index[edge.source_id].add(edge.id)
        self._target_index[edge.target_id].add(edge.id)
        
        # Traversal indexes
        self._outgoing_index[(edge.source_id, edge.relationship)].add(edge.target_id)
        self._incoming_index[(edge.target_id, edge.relationship)].add(edge.source_id)
        
    def remove_edge(self, edge: GraphEdge) -> None:
        """Remove an edge from all relationship indexes."""
        # Basic indexes
        self._relationship_index[edge.relationship].discard(edge.id)
        self._source_index[edge.source_id].discard(edge.id)
        self._target_index[edge.target_id].discard(edge.id)
        
        # Traversal indexes
        self._outgoing_index[(edge.source_id, edge.relationship)].discard(edge.target_id)
        self._incoming_index[(edge.target_id, edge.relationship)].discard(edge.source_id)
        
        # Cleanup empty sets
        if not self._relationship_index[edge.relationship]:
            del self._relationship_index[edge.relationship]
        if not self._source_index[edge.source_id]:
            del self._source_index[edge.source_id]
        if not self._target_index[edge.target_id]:
            del self._target_index[edge.target_id]
            
    def find_by_relationship(self, relationship: str) -> Set[str]:
        """Find all edges with the given relationship type."""
        return self._relationship_index[relationship].copy()
        
    def find_by_source(self, source_id: str) -> Set[str]:
        """Find all edges from the given source node."""
        return self._source_index[source_id].copy()
        
    def find_by_target(self, target_id: str) -> Set[str]:
        """Find all edges to the given target node."""
        return self._target_index[target_id].copy()
        
    def find_connected_nodes(
        self, 
        node_id: str, 
        relationship: str, 
        direction: str = "outgoing"
    ) -> Set[str]:
        """Find nodes connected via specific relationship and direction."""
        if direction == "outgoing":
            return self._outgoing_index[(node_id, relationship)].copy()
        elif direction == "incoming":
            return self._incoming_index[(node_id, relationship)].copy()
        elif direction == "both":
            outgoing = self._outgoing_index[(node_id, relationship)]
            incoming = self._incoming_index[(node_id, relationship)]
            return outgoing | incoming
        else:
            return set()


class GraphIndexManager:
    """
    Manages all indexes for the knowledge base.
    Provides a unified interface for indexed queries.
    """
    
    def __init__(self):
        self.node_label_index = LabelIndex()
        self.node_property_index = PropertyIndex()
        self.edge_label_index = LabelIndex()
        self.edge_property_index = PropertyIndex()
        self.relationship_index = RelationshipIndex()
        
    def add_node(self, node: GraphNode) -> None:
        """Add a node to all relevant indexes."""
        self.node_label_index.add_entity(node.id, node.label)
        self.node_property_index.add_entity(node.id, node.properties)
        
    def remove_node(self, node: GraphNode) -> None:
        """Remove a node from all relevant indexes."""
        self.node_label_index.remove_entity(node.id, node.label)
        self.node_property_index.remove_entity(node.id, node.properties)
        
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to all relevant indexes."""
        self.edge_label_index.add_entity(edge.id, edge.relationship)
        self.edge_property_index.add_entity(edge.id, edge.properties)
        self.relationship_index.add_edge(edge)
        
    def remove_edge(self, edge: GraphEdge) -> None:
        """Remove an edge from all relevant indexes."""
        self.edge_label_index.remove_entity(edge.id, edge.relationship)
        self.edge_property_index.remove_entity(edge.id, edge.properties)
        self.relationship_index.remove_edge(edge)
        
    def query_nodes_indexed(
        self,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Set[str]:
        """Fast indexed query for nodes."""
        result_sets = []
        
        # Label filter
        if label is not None:
            label_results = self.node_label_index.find_by_label(label)
            result_sets.append(label_results)
            
        # Property filters
        if properties:
            property_results = self.node_property_index.find_multiple_properties(properties)
            result_sets.append(property_results)
            
        # Intersect all result sets
        if result_sets:
            result = result_sets[0]
            for result_set in result_sets[1:]:
                result &= result_set
            return result
        else:
            # If no filters, return empty set to avoid full scan
            return set()
            
    def query_edges_indexed(
        self,
        relationship: Optional[str] = None,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Set[str]:
        """Fast indexed query for edges."""
        result_sets = []
        
        # Relationship filter
        if relationship is not None:
            rel_results = self.relationship_index.find_by_relationship(relationship)
            result_sets.append(rel_results)
            
        # Source filter
        if source_id is not None:
            source_results = self.relationship_index.find_by_source(source_id)
            result_sets.append(source_results)
            
        # Target filter
        if target_id is not None:
            target_results = self.relationship_index.find_by_target(target_id)
            result_sets.append(target_results)
            
        # Property filters
        if properties:
            property_results = self.edge_property_index.find_multiple_properties(properties)
            result_sets.append(property_results)
            
        # Intersect all result sets
        if result_sets:
            result = result_sets[0]
            for result_set in result_sets[1:]:
                result &= result_set
            return result
        else:
            # If no filters, return empty set to avoid full scan
            return set()
            
    def query_connected_nodes_indexed(
        self,
        start_node_id: str,
        relationship: str,
        direction: str = "outgoing"
    ) -> Set[str]:
        """Fast indexed query for connected nodes."""
        return self.relationship_index.find_connected_nodes(
            start_node_id, relationship, direction
        )