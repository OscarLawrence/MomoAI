"""
Tests for the multi-agent RAG implementation.
"""

import pytest
from kb_playground.hybrid_kb import HybridKB
from kb_playground.multi_agent_rag import (
    Query, AgentResponse, PlannerAgent, ResearchAgent, 
    SummarizerAgent, CriticAgent, MultiAgentRAG
)


class TestQuery:
    def test_query_creation(self):
        query = Query("What is machine learning?")
        
        assert query.text == "What is machine learning?"
        assert query.context == {}
        assert query.metadata == {}


class TestAgentResponse:
    def test_response_creation(self):
        response = AgentResponse("Test response", confidence=0.8)
        
        assert response.content == "Test response"
        assert response.confidence == 0.8
        assert response.metadata == {}
        assert response.sources == []


class TestPlannerAgent:
    def test_planner_what_query(self):
        planner = PlannerAgent()
        query = Query("What is machine learning?")
        
        response = planner.process(query)
        
        assert "vector_search" in response.metadata['plan']['strategies']
        assert response.confidence > 0.0
    
    def test_planner_how_query(self):
        planner = PlannerAgent()
        query = Query("How does machine learning work?")
        
        response = planner.process(query)
        
        assert "graph_traversal" in response.metadata['plan']['strategies']
    
    def test_planner_compare_query(self):
        planner = PlannerAgent()
        query = Query("Compare machine learning and deep learning")
        
        response = planner.process(query)
        
        strategies = response.metadata['plan']['strategies']
        assert "vector_search" in strategies
        assert "graph_traversal" in strategies


class TestResearchAgent:
    def setup_method(self):
        self.kb = HybridKB()
        self.kb.add_node("ml1", "Machine learning is a subset of AI")
        self.kb.add_node("ml2", "Machine learning algorithms learn from data")
        self.kb.add_node("dl1", "Deep learning uses neural networks")
        self.kb.add_node("other", "Cooking is an art")
        
        self.kb.add_edge("ml1", "ml2", "relates_to")
        self.kb.add_edge("ml2", "dl1", "enables")
    
    def test_research_vector_search(self):
        researcher = ResearchAgent(self.kb)
        query = Query("machine learning")
        
        input_data = {
            'query': query,
            'plan': {'strategies': ['vector_search']}
        }
        
        response = researcher.process(input_data)
        
        assert len(response.sources) > 0
        assert 'results' in response.metadata
        assert any('vector' in result.get('method', '') for result in response.metadata['results'])
    
    def test_research_hybrid_search(self):
        researcher = ResearchAgent(self.kb)
        query = Query("learning")
        
        input_data = {
            'query': query,
            'plan': {'strategies': ['hybrid_search']}
        }
        
        response = researcher.process(input_data)
        
        assert len(response.sources) > 0
        assert 'results' in response.metadata


class TestSummarizerAgent:
    def test_summarizer_with_results(self):
        summarizer = SummarizerAgent()
        
        research_data = {
            'results': [
                {'content': 'Machine learning is AI', 'similarity': 0.8},
                {'content': 'Deep learning uses networks', 'similarity': 0.6},
                {'content': 'AI processes data', 'similarity': 0.4}
            ]
        }
        
        response = summarizer.process(research_data)
        
        assert "High relevance" in response.content
        assert response.confidence > 0.5
        assert response.metadata['total_processed'] == 3
    
    def test_summarizer_no_results(self):
        summarizer = SummarizerAgent()
        
        response = summarizer.process({})
        
        assert "No information found" in response.content
        assert response.confidence < 0.5


class TestCriticAgent:
    def test_critic_good_summary(self):
        critic = CriticAgent()
        
        evaluation_data = {
            'summary': """High relevance (2 items):
- Machine learning is a subset of artificial intelligence
- Deep learning uses neural networks for complex patterns""",
            'query': 'machine learning'
        }
        
        response = critic.process(evaluation_data)
        
        assert response.confidence > 0.5
        assert 'quality_score' in response.metadata
    
    def test_critic_poor_summary(self):
        critic = CriticAgent()
        
        evaluation_data = {
            'summary': "Short",
            'query': 'machine learning deep learning comparison'
        }
        
        response = critic.process(evaluation_data)
        
        assert response.confidence < 0.7
        assert len(response.metadata['issues']) > 0


class TestMultiAgentRAG:
    def setup_method(self):
        self.kb = HybridKB()
        self.kb.add_node("ml1", "Machine learning is a subset of AI that learns from data")
        self.kb.add_node("ml2", "Machine learning algorithms include supervised and unsupervised")
        self.kb.add_node("dl1", "Deep learning is a subset of machine learning using neural networks")
        self.kb.add_node("ai1", "Artificial intelligence aims to create intelligent machines")
        
        self.kb.add_edge("ai1", "ml1", "includes")
        self.kb.add_edge("ml1", "dl1", "includes")
        self.kb.add_edge("ml1", "ml2", "encompasses")
        
        self.rag = MultiAgentRAG(self.kb)
    
    def test_process_query_full_pipeline(self):
        result = self.rag.process_query("What is machine learning?")
        
        assert 'query' in result
        assert 'summary' in result
        assert 'quality_assessment' in result
        assert 'confidence' in result
        assert 'sources' in result
        assert 'pipeline_trace' in result
        
        # Check pipeline trace has all stages
        trace = result['pipeline_trace']
        assert 'planner' in trace
        assert 'research' in trace
        assert 'summary' in trace
        assert 'critic' in trace
    
    def test_conversation_context(self):
        # Process multiple queries
        self.rag.process_query("What is machine learning?")
        self.rag.process_query("What is deep learning?")
        
        context = self.rag.get_conversation_context(last_n=2)
        
        assert len(context) == 2
        assert context[0]['query'] == "What is machine learning?"
        assert context[1]['query'] == "What is deep learning?"
    
    def test_process_complex_query(self):
        result = self.rag.process_query("How are machine learning and deep learning related?")
        
        # Should trigger graph traversal due to "how" and "related"
        assert result['confidence'] > 0.0
        assert len(result['sources']) > 0