"""
Agent registry for managing multiple interactive agents.
"""

import re
from typing import Dict, List, Optional, Pattern, Any
from .base import InteractiveAgent, ExecutionContext


class AgentRegistry:
    """Registry for managing interactive agents with pattern matching."""

    def __init__(self):
        self.executing_agent: Optional[InteractiveAgent] = None
        self.specialized_agents: Dict[Pattern, InteractiveAgent] = {}
        self.general_agent: Optional[InteractiveAgent] = None
        self.custom_agents: List[InteractiveAgent] = []

    def register_executing_agent(self, agent: InteractiveAgent):
        """Register the main executing agent (highest priority)."""
        self.executing_agent = agent

    def register_specialized_agent(self, pattern: str, agent: InteractiveAgent):
        """Register agent for specific command patterns."""
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        self.specialized_agents[compiled_pattern] = agent

    def register_general_agent(self, agent: InteractiveAgent):
        """Register fallback agent for general prompts."""
        self.general_agent = agent

    def register_custom_agent(self, agent: InteractiveAgent):
        """Register custom plugin agent."""
        self.custom_agents.append(agent)
        # Sort by priority
        self.custom_agents.sort(key=lambda a: a.get_priority(), reverse=True)

    def find_agent(
        self, command: str, context: ExecutionContext
    ) -> Optional[InteractiveAgent]:
        """Find the best agent for handling this command."""

        # 1. Try custom agents first (sorted by priority)
        for agent in self.custom_agents:
            if agent.can_handle(command, context):
                return agent

        # 2. Try specialized agents (pattern matching)
        for pattern, agent in self.specialized_agents.items():
            if pattern.search(command) and agent.can_handle(command, context):
                return agent

        # 3. Try general agent
        if self.general_agent and self.general_agent.can_handle(command, context):
            return self.general_agent

        # 4. Fall back to executing agent (ultimate fallback)
        if self.executing_agent and self.executing_agent.can_handle(command, context):
            return self.executing_agent

        return None

    def get_all_agents(self) -> List[InteractiveAgent]:
        """Get all registered agents."""
        agents = []

        if self.executing_agent:
            agents.append(self.executing_agent)

        agents.extend(self.custom_agents)
        agents.extend(self.specialized_agents.values())

        if self.general_agent:
            agents.append(self.general_agent)

        return agents

    def get_agent_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics for all agents."""
        stats = {}

        for agent in self.get_all_agents():
            stats[agent.name] = {
                "priority": agent.priority,
                "usage_count": agent.usage_count,
                "success_count": agent.success_count,
                "success_rate": agent.success_rate,
            }

        return stats
