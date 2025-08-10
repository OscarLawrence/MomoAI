"""
Multi-Agent RAG Implementation
Implements the specialized agent pipeline for context retrieval and synthesis.
"""

from typing import List, Dict, Any, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
from .hybrid_kb import HybridKB


@dataclass
class Query:
    """A query with context and metadata."""
    text: str
    context: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentResponse:
    """Response from an agent."""
    content: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    sources: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.sources is None:
            self.sources = []


class Agent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def process(self, input_data: Any) -> AgentResponse:
        """Process input and return response."""
        pass


class PlannerAgent(Agent):
    """Agent that decomposes queries into subtasks."""
    
    def __init__(self):
        super().__init__("Planner")
    
    def process(self, query: Query) -> AgentResponse:
        """Break down query into search strategy."""
        text = query.text.lower()
        
        # Simple heuristics for search strategy
        strategy = []
        
        if any(word in text for word in ['what', 'who', 'where', 'when']):
            strategy.append('vector_search')
        
        if any(word in text for word in ['how', 'why', 'explain', 'relationship']):
            strategy.append('graph_traversal')
        
        if any(word in text for word in ['compare', 'difference', 'similar', 'related']):
            strategy.extend(['vector_search', 'graph_traversal'])
        
        # Default to hybrid search
        if not strategy:
            strategy = ['hybrid_search']
        
        plan = {
            'strategies': list(set(strategy)),
            'priority': 'high' if len(strategy) > 1 else 'medium',
            'complexity': 'high' if 'graph_traversal' in strategy else 'low'
        }
        
        return AgentResponse(
            content=f"Query analysis complete. Recommended strategies: {', '.join(strategy)}",
            confidence=0.8,
            metadata={'plan': plan}
        )


class ResearchAgent(Agent):
    """Agent that executes search strategies."""
    
    def __init__(self, knowledge_base: HybridKB):
        super().__init__("Researcher")
        self.kb = knowledge_base
    
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Execute search based on planner's strategy."""
        query = input_data['query']
        plan = input_data.get('plan', {})
        strategies = plan.get('strategies', ['hybrid_search'])
        
        all_results = []
        sources = []
        
        for strategy in strategies:
            if strategy == 'vector_search':
                results = self.kb.vector_search(query.text)
                for node_id, similarity in results:
                    node = self.kb.nodes[node_id]
                    all_results.append({
                        'content': node.content,
                        'similarity': similarity,
                        'source': node_id,
                        'method': 'vector'
                    })
                    sources.append(node_id)
            
            elif strategy == 'graph_traversal':
                # Start from highest similarity nodes
                vector_results = self.kb.vector_search(query.text, top_k=2)
                for start_node, _ in vector_results:
                    connected_nodes = self.kb.graph_traverse(start_node, max_depth=2)
                    for node_id in connected_nodes:
                        node = self.kb.nodes[node_id]
                        all_results.append({
                            'content': node.content,
                            'source': node_id,
                            'method': 'graph',
                            'relationships': self.kb.get_relationships(node_id)
                        })
                        sources.append(node_id)
            
            elif strategy == 'hybrid_search':
                results = self.kb.hybrid_search(query.text)
                for result in results:
                    all_results.append({
                        'content': result['content'],
                        'similarity': result['similarity'],
                        'source': result['node_id'],
                        'method': 'hybrid',
                        'connections': result['connections']
                    })
                    sources.append(result['node_id'])
        
        # Remove duplicates while preserving order
        unique_sources = list(dict.fromkeys(sources))
        
        content = f"Retrieved {len(all_results)} pieces of information using {', '.join(strategies)}"
        
        return AgentResponse(
            content=content,
            confidence=0.7,
            metadata={'results': all_results, 'strategies_used': strategies},
            sources=unique_sources
        )


class SummarizerAgent(Agent):
    """Agent that condenses information into concise context."""
    
    def __init__(self):
        super().__init__("Summarizer")
    
    def process(self, research_data: Dict[str, Any]) -> AgentResponse:
        """Condense research results into concise summary."""
        results = research_data.get('results', [])
        
        if not results:
            return AgentResponse(
                content="No information found to summarize.",
                confidence=0.1
            )
        
        # Group by similarity/relevance
        high_relevance = [r for r in results if r.get('similarity', 0) > 0.3]
        medium_relevance = [r for r in results if 0.1 < r.get('similarity', 0) <= 0.3]
        
        summary_parts = []
        
        if high_relevance:
            summary_parts.append(f"High relevance ({len(high_relevance)} items):")
            for item in high_relevance[:3]:  # Top 3
                summary_parts.append(f"- {item['content'][:100]}...")
        
        if medium_relevance:
            summary_parts.append(f"Medium relevance ({len(medium_relevance)} items):")
            for item in medium_relevance[:2]:  # Top 2
                summary_parts.append(f"- {item['content'][:80]}...")
        
        summary = "\n".join(summary_parts)
        
        return AgentResponse(
            content=summary,
            confidence=0.8 if high_relevance else 0.6,
            metadata={'total_processed': len(results)}
        )


class CriticAgent(Agent):
    """Agent that evaluates response quality."""
    
    def __init__(self):
        super().__init__("Critic")
    
    def process(self, evaluation_data: Dict[str, Any]) -> AgentResponse:
        """Evaluate the quality of summarized content."""
        summary = evaluation_data.get('summary', '')
        original_query = evaluation_data.get('query', '')
        
        # Simple quality metrics
        quality_score = 0.0
        issues = []
        
        # Check length (not too short, not too long)
        if len(summary) < 50:
            issues.append("Summary too short")
        elif len(summary) > 1000:
            issues.append("Summary too long")
            quality_score -= 0.2
        else:
            quality_score += 0.3
        
        # Check if summary addresses query terms
        query_words = set(original_query.lower().split())
        summary_words = set(summary.lower().split())
        overlap = len(query_words.intersection(summary_words))
        
        if overlap >= len(query_words) * 0.5:
            quality_score += 0.4
        else:
            issues.append("Low query term coverage")
        
        # Check information density
        if summary.count('-') >= 2:  # At least 2 bullet points
            quality_score += 0.3
        else:
            issues.append("Low information density")
        
        # Overall assessment
        if quality_score >= 0.7:
            assessment = "Good quality summary"
        elif quality_score >= 0.4:
            assessment = "Acceptable quality with minor issues"
        else:
            assessment = "Poor quality, needs improvement"
        
        return AgentResponse(
            content=assessment,
            confidence=min(quality_score, 1.0),
            metadata={'quality_score': quality_score, 'issues': issues}
        )


class MultiAgentRAG:
    """Orchestrates the multi-agent RAG pipeline."""
    
    def __init__(self, knowledge_base: HybridKB):
        self.kb = knowledge_base
        self.planner = PlannerAgent()
        self.researcher = ResearchAgent(knowledge_base)
        self.summarizer = SummarizerAgent()
        self.critic = CriticAgent()
        self.conversation_history = []
    
    def process_query(self, query_text: str) -> Dict[str, Any]:
        """Process a query through the multi-agent pipeline."""
        query = Query(text=query_text)
        
        # Step 1: Planning
        plan_response = self.planner.process(query)
        
        # Step 2: Research
        research_input = {
            'query': query,
            'plan': plan_response.metadata.get('plan', {})
        }
        research_response = self.researcher.process(research_input)
        
        # Step 3: Summarization
        summary_response = self.summarizer.process(research_response.metadata)
        
        # Step 4: Quality Check
        evaluation_input = {
            'summary': summary_response.content,
            'query': query_text
        }
        critic_response = self.critic.process(evaluation_input)
        
        # Compile final result
        result = {
            'query': query_text,
            'summary': summary_response.content,
            'quality_assessment': critic_response.content,
            'confidence': critic_response.confidence,
            'sources': research_response.sources,
            'pipeline_trace': {
                'planner': plan_response.metadata,
                'research': {
                    'strategies': research_response.metadata.get('strategies_used', []),
                    'results_count': len(research_response.metadata.get('results', []))
                },
                'summary': summary_response.metadata,
                'critic': critic_response.metadata
            }
        }
        
        # Store in conversation history
        self.conversation_history.append(result)
        
        return result
    
    def get_conversation_context(self, last_n: int = 3) -> List[Dict]:
        """Get recent conversation context."""
        return self.conversation_history[-last_n:] if self.conversation_history else []