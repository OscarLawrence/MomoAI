"""
Correctness tests comparing indexed queries vs naive implementations.

Ensures that our high-performance indexed queries return exactly the same
results as brute-force naive implementations.
"""

import pytest
import asyncio
from typing import List, Dict, Any, Set

from momo_kb import KnowledgeBase, Node, Edge, QueryResult


class NaiveQueryEngine:
    """
    Naive (brute-force) query implementation for correctness comparison.
    
    This implementation does full scans and manual filtering to ensure
    we get the "ground truth" results to compare against our indexes.
    """
    
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        
    async def naive_query_nodes(
        self, 
        label: str = None, 
        properties: Dict[str, Any] = None
    ) -> List[Node]:
        """Naive node query using full scan."""
        all_nodes = []
        
        # Get all nodes from all tiers (brute force)
        for tier_name in ["runtime", "store", "cold"]:
            tier_count = await self.kb.count_nodes(tier=tier_name)
            if tier_count > 0:
                # We need to access storage directly for naive implementation
                # This is a test-only approach
                from momo_kb.storage import StorageTier
                tier = StorageTier(tier_name)
                tier_nodes = self.kb._storage.get_all_nodes(tier)
                all_nodes.extend(tier_nodes)
                
        # Manual filtering
        result_nodes = []
        for node in all_nodes:
            # Label filter
            if label is not None and node.label != label:
                continue
                
            # Property filters
            if properties is not None:
                match = True
                for key, value in properties.items():
                    if key not in node.properties or node.properties[key] != value:
                        match = False
                        break
                if not match:
                    continue
                    
            result_nodes.append(node)
            
        return result_nodes
        
    async def naive_query_edges(
        self,
        relationship: str = None,
        source_id: str = None,
        target_id: str = None,
        properties: Dict[str, Any] = None
    ) -> List[Edge]:
        """Naive edge query using full scan."""
        all_edges = []
        
        # Get all edges from all tiers (brute force)
        for tier_name in ["runtime", "store", "cold"]:
            tier_count = await self.kb.count_edges(tier=tier_name)
            if tier_count > 0:
                from momo_kb.storage import StorageTier
                tier = StorageTier(tier_name)
                tier_edges = self.kb._storage.get_all_edges(tier)
                all_edges.extend(tier_edges)
                
        # Manual filtering
        result_edges = []
        for edge in all_edges:
            # Relationship filter
            if relationship is not None and edge.relationship != relationship:
                continue
                
            # Source filter
            if source_id is not None and edge.source_id != source_id:
                continue
                
            # Target filter
            if target_id is not None and edge.target_id != target_id:
                continue
                
            # Property filters
            if properties is not None:
                match = True
                for key, value in properties.items():
                    if key not in edge.properties or edge.properties[key] != value:
                        match = False
                        break
                if not match:
                    continue
                    
            result_edges.append(edge)
            
        return result_edges
        
    async def naive_query_connected_nodes(
        self,
        start_node_id: str,
        relationship: str,
        direction: str = "outgoing"
    ) -> List[Node]:
        """Naive connected nodes query using full scan."""
        # First find relevant edges
        all_edges = await self.naive_query_edges()
        
        connected_node_ids = set()
        
        for edge in all_edges:
            if edge.relationship != relationship:
                continue
                
            if direction == "outgoing" and edge.source_id == start_node_id:
                connected_node_ids.add(edge.target_id)
            elif direction == "incoming" and edge.target_id == start_node_id:
                connected_node_ids.add(edge.source_id)
            elif direction == "both":
                if edge.source_id == start_node_id:
                    connected_node_ids.add(edge.target_id)
                elif edge.target_id == start_node_id:
                    connected_node_ids.add(edge.source_id)
                    
        # Find the actual nodes
        all_nodes = await self.naive_query_nodes()
        connected_nodes = [node for node in all_nodes if node.id in connected_node_ids]
        
        return connected_nodes


class TestIndexedVsNaive:
    """Compare indexed queries against naive implementations."""
    
    @pytest.fixture
    async def large_test_kb(self):
        """Create a larger knowledge base for comprehensive testing."""
        kb = KnowledgeBase()
        await kb.initialize()
        
        # Create a more complex dataset
        departments = ["Engineering", "Design", "Product", "Marketing", "Sales"]
        levels = ["Junior", "Mid", "Senior", "Staff", "Principal"]
        companies = ["TechCorp", "StartupInc", "BigCorp"]
        
        # Create 50 people with various attributes
        people_nodes = []
        for i in range(50):
            person = await kb.insert_node(Node(
                label="Person",
                properties={
                    "name": f"Person{i}",
                    "employee_id": i,
                    "department": departments[i % len(departments)],
                    "level": levels[i % len(levels)],
                    "salary": 50000 + (i * 2000),
                    "active": i % 7 != 0,  # ~85% active
                    "hire_year": 2015 + (i % 8)
                }
            ))
            people_nodes.append(person.node)
            
        # Create companies
        company_nodes = []
        for i, company_name in enumerate(companies):
            company = await kb.insert_node(Node(
                label="Company",
                properties={
                    "name": company_name,
                    "size": ["small", "medium", "large"][i],
                    "industry": "technology",
                    "founded": 2000 + i * 5
                }
            ))
            company_nodes.append(company.node)
            
        # Create projects
        project_nodes = []
        for i in range(10):
            project = await kb.insert_node(Node(
                label="Project",
                properties={
                    "name": f"Project{i}",
                    "status": ["active", "completed", "on_hold"][i % 3],
                    "budget": 10000 + (i * 15000),
                    "priority": ["low", "medium", "high"][i % 3]
                }
            ))
            project_nodes.append(project.node)
            
        # Create relationships
        # Employment relationships
        for i, person in enumerate(people_nodes):
            company = company_nodes[i % len(company_nodes)]
            await kb.insert_edge(Edge(
                source_id=person.id,
                target_id=company.id,
                relationship="works_for",
                properties={"since": 2018 + (i % 5), "role": f"role_{i % 10}"}
            ))
            
        # Project assignments
        for i, person in enumerate(people_nodes[:30]):  # Only first 30 people
            project = project_nodes[i % len(project_nodes)]
            await kb.insert_edge(Edge(
                source_id=person.id,
                target_id=project.id,
                relationship="assigned_to",
                properties={"role": ["developer", "designer", "manager"][i % 3]}
            ))
            
        # Mentoring relationships
        for i in range(0, len(people_nodes) - 1, 3):  # Every 3rd person mentors the next
            await kb.insert_edge(Edge(
                source_id=people_nodes[i].id,
                target_id=people_nodes[i + 1].id,
                relationship="mentors",
                properties={"area": ["technical", "leadership", "design"][i % 3]}
            ))
            
        yield kb
        await kb.close()
        
    async def test_node_queries_match_naive(self, large_test_kb):
        """Test that indexed node queries match naive implementations."""
        kb = large_test_kb
        naive = NaiveQueryEngine(kb)
        
        test_cases = [
            # Label only queries
            {"label": "Person"},
            {"label": "Company"},
            {"label": "Project"},
            {"label": "NonExistent"},
            
            # Property only queries
            {"properties": {"department": "Engineering"}},
            {"properties": {"active": True}},
            {"properties": {"salary": 60000}},
            {"properties": {"status": "active"}},
            {"properties": {"nonexistent": "value"}},
            
            # Combined queries
            {"label": "Person", "properties": {"department": "Engineering"}},
            {"label": "Person", "properties": {"active": True, "level": "Senior"}},
            {"label": "Company", "properties": {"size": "large"}},
            {"label": "Project", "properties": {"status": "completed", "priority": "high"}},
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"Testing node query case {i + 1}: {test_case}")
            
            # Get results from both implementations
            indexed_result = await kb.query_nodes(**test_case)
            naive_result = await naive.naive_query_nodes(**test_case)
            
            # Compare results
            indexed_ids = {node.id for node in indexed_result.nodes}
            naive_ids = {node.id for node in naive_result}
            
            assert indexed_ids == naive_ids, f"Mismatch in test case {i + 1}: {test_case}"
            assert len(indexed_result.nodes) == len(naive_result), f"Count mismatch in test case {i + 1}"
            
    async def test_edge_queries_match_naive(self, large_test_kb):
        """Test that indexed edge queries match naive implementations."""
        kb = large_test_kb
        naive = NaiveQueryEngine(kb)
        
        test_cases = [
            # Relationship only
            {"relationship": "works_for"},
            {"relationship": "assigned_to"},
            {"relationship": "mentors"},
            {"relationship": "nonexistent"},
            
            # Property only
            {"properties": {"role": "developer"}},
            {"properties": {"since": 2020}},
            {"properties": {"area": "technical"}},
            
            # Combined
            {"relationship": "works_for", "properties": {"since": 2020}},
            {"relationship": "assigned_to", "properties": {"role": "manager"}},
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"Testing edge query case {i + 1}: {test_case}")
            
            # Get results from both implementations
            indexed_result = await kb.query_edges(**test_case)
            naive_result = await naive.naive_query_edges(**test_case)
            
            # Compare results
            indexed_ids = {edge.id for edge in indexed_result.edges}
            naive_ids = {edge.id for edge in naive_result}
            
            assert indexed_ids == naive_ids, f"Mismatch in test case {i + 1}: {test_case}"
            assert len(indexed_result.edges) == len(naive_result), f"Count mismatch in test case {i + 1}"
            
    async def test_connected_queries_match_naive(self, large_test_kb):
        """Test that connected node queries match naive implementations."""
        kb = large_test_kb
        naive = NaiveQueryEngine(kb)
        
        # Get some test node IDs
        people = await kb.query_nodes(label="Person")
        test_node_ids = [people.nodes[i].id for i in [0, 5, 10, 15] if i < len(people.nodes)]
        
        test_cases = [
            # Different relationships and directions
            {"relationship": "works_for", "direction": "outgoing"},
            {"relationship": "works_for", "direction": "incoming"},
            {"relationship": "assigned_to", "direction": "outgoing"},
            {"relationship": "assigned_to", "direction": "incoming"},
            {"relationship": "mentors", "direction": "outgoing"},
            {"relationship": "mentors", "direction": "incoming"},
            {"relationship": "mentors", "direction": "both"},
            {"relationship": "nonexistent", "direction": "outgoing"},
        ]
        
        for node_id in test_node_ids:
            for i, test_case in enumerate(test_cases):
                print(f"Testing connected query for node {node_id[:8]}..., case {i + 1}: {test_case}")
                
                # Get results from both implementations
                indexed_result = await kb.query_connected_nodes(
                    start_node_id=node_id, **test_case
                )
                naive_result = await naive.naive_query_connected_nodes(
                    start_node_id=node_id, **test_case
                )
                
                # Compare results
                indexed_ids = {node.id for node in indexed_result.nodes}
                naive_ids = {node.id for node in naive_result}
                
                assert indexed_ids == naive_ids, f"Mismatch for node {node_id}, case {i + 1}: {test_case}"
                
    async def test_performance_vs_correctness_tradeoff(self, large_test_kb):
        """Verify that performance optimizations don't compromise correctness."""
        kb = large_test_kb
        naive = NaiveQueryEngine(kb)
        
        import time
        
        # Test a complex query that exercises the indexes
        test_query = {
            "label": "Person",
            "properties": {"department": "Engineering", "active": True}
        }
        
        # Time the indexed version
        start = time.perf_counter()
        indexed_result = await kb.query_nodes(**test_query)
        indexed_time = time.perf_counter() - start
        
        # Time the naive version
        start = time.perf_counter()
        naive_result = await naive.naive_query_nodes(**test_query)
        naive_time = time.perf_counter() - start
        
        # Verify correctness
        indexed_ids = {node.id for node in indexed_result.nodes}
        naive_ids = {node.id for node in naive_result}
        assert indexed_ids == naive_ids, "Performance optimization broke correctness!"
        
        # Verify performance improvement
        speedup = naive_time / indexed_time if indexed_time > 0 else float('inf')
        print(f"Indexed query: {indexed_time*1000:.2f}ms")
        print(f"Naive query: {naive_time*1000:.2f}ms") 
        print(f"Speedup: {speedup:.1f}x")
        
        # Should be at least 2x faster (usually much more)
        assert speedup >= 2.0, f"Expected speedup >= 2x, got {speedup:.1f}x"