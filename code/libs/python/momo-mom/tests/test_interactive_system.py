"""
Comprehensive tests for the interactive agent system.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import os

from momo_mom.interactive import MomInteractiveSystem
from momo_mom.agents.base import ExecutionContext, CommandResult, AgentCallback
from momo_mom.agents.registry import AgentRegistry
from momo_mom.agents.executing import ExecutingAgent
from momo_mom.agents.general import GeneralAgent
from momo_mom.agents.specialized.npm import NpmAgent
from momo_mom.agents.specialized.git import GitAgent


class TestExecutionContext:
    """Test ExecutionContext functionality."""
    
    def test_context_creation(self):
        """Test basic context creation."""
        context = ExecutionContext(
            current_task="test task",
            project_info={"name": "test-project"},
            user_preferences={"author": "Test User"}
        )
        
        assert context.current_task == "test task"
        assert context.project_info["name"] == "test-project"
        assert context.user_preferences["author"] == "Test User"
        assert context.working_directory  # Should have default
    
    def test_context_defaults(self):
        """Test context with defaults."""
        context = ExecutionContext("minimal task")
        
        assert context.current_task == "minimal task"
        assert isinstance(context.project_info, dict)
        assert isinstance(context.command_history, list)
        assert isinstance(context.environment_vars, dict)


class TestAgentRegistry:
    """Test AgentRegistry functionality."""
    
    def setup_method(self):
        """Setup test registry."""
        self.registry = AgentRegistry()
        self.context = ExecutionContext("test")
    
    def test_register_executing_agent(self):
        """Test registering executing agent."""
        callback = Mock(return_value="test")
        agent = ExecutingAgent(AgentCallback(callback))
        
        self.registry.register_executing_agent(agent)
        
        assert self.registry.executing_agent == agent
    
    def test_register_specialized_agent(self):
        """Test registering specialized agents."""
        npm_agent = NpmAgent()
        
        self.registry.register_specialized_agent(r'npm init', npm_agent)
        
        assert len(self.registry.specialized_agents) == 1
    
    def test_agent_selection_priority(self):
        """Test agent selection follows priority order."""
        # Setup agents
        callback = Mock(return_value="test")
        executing_agent = ExecutingAgent(AgentCallback(callback))
        npm_agent = NpmAgent()
        general_agent = GeneralAgent()
        
        self.registry.register_executing_agent(executing_agent)
        self.registry.register_specialized_agent(r'npm init', npm_agent)
        self.registry.register_general_agent(general_agent)
        
        # Test specialized agent is selected for npm command
        agent = self.registry.find_agent("npm init my-project", self.context)
        assert isinstance(agent, NpmAgent)
        
        # Test general agent is selected for unknown command
        agent = self.registry.find_agent("unknown command", self.context)
        assert isinstance(agent, GeneralAgent)
        
        # Test executing agent is ultimate fallback
        # (when general agent can't handle - though it handles everything)
        agent = self.registry.find_agent("any command", self.context)
        assert agent is not None  # Should find some agent


class TestSpecializedAgents:
    """Test specialized agent functionality."""
    
    def setup_method(self):
        """Setup test context."""
        self.context = ExecutionContext(
            "test task",
            project_info={"name": "test-project", "type": "application"},
            user_preferences={"author": "Test User", "license": "MIT"}
        )
    
    def test_npm_agent_responses(self):
        """Test NPM agent prompt responses."""
        agent = NpmAgent()
        
        # Test package name
        response = agent.handle_prompt("package name:", "npm init", self.context)
        assert response == "test-project"
        
        # Test version
        response = agent.handle_prompt("version:", "npm init", self.context)
        assert response == "1.0.0"
        
        # Test author
        response = agent.handle_prompt("author:", "npm init", self.context)
        assert "Test User" in response
        
        # Test license
        response = agent.handle_prompt("license:", "npm init", self.context)
        assert response == "MIT"
    
    def test_git_agent_responses(self):
        """Test Git agent prompt responses."""
        agent = GitAgent()
        
        # Test commit message
        response = agent.handle_prompt("commit message:", "git commit", self.context)
        assert "test task" in response.lower()
        
        # Test username
        response = agent.handle_prompt("user.name:", "git config", self.context)
        assert response  # Should return something
        
        # Test continue prompt
        response = agent.handle_prompt("continue?", "git merge", self.context)
        assert response == "y"
    
    def test_agent_can_handle(self):
        """Test agent command detection."""
        npm_agent = NpmAgent()
        git_agent = GitAgent()
        
        # NPM agent
        assert npm_agent.can_handle("npm init", self.context)
        assert npm_agent.can_handle("yarn create", self.context)
        assert not npm_agent.can_handle("git commit", self.context)
        
        # Git agent
        assert git_agent.can_handle("git commit", self.context)
        assert git_agent.can_handle("git config", self.context)
        assert not git_agent.can_handle("npm init", self.context)


class TestExecutingAgent:
    """Test ExecutingAgent functionality."""
    
    def test_callback_execution(self):
        """Test executing agent callback."""
        callback_mock = Mock(return_value="callback response")
        agent = ExecutingAgent(AgentCallback(callback_mock))
        
        context = ExecutionContext("test")
        response = agent.handle_prompt("test prompt:", "test command", context)
        
        assert response == "callback response"
        callback_mock.assert_called_once()
        
        # Check callback was called with correct structure
        call_args = callback_mock.call_args[0][0]
        assert call_args['type'] == 'interactive_prompt'
        assert call_args['prompt'] == 'test prompt:'
        assert call_args['command'] == 'test command'
    
    def test_safe_defaults(self):
        """Test safe default responses when callback fails."""
        callback_mock = Mock(side_effect=Exception("Callback failed"))
        agent = ExecutingAgent(AgentCallback(callback_mock))
        
        context = ExecutionContext("test")
        
        # Test confirmation prompt
        response = agent.handle_prompt("Continue? (y/n)", "test", context)
        assert response == "y"
        
        # Test version prompt
        response = agent.handle_prompt("Version:", "test", context)
        assert response == "1.0.0"


class TestMomInteractiveSystem:
    """Test the main interactive system."""
    
    def setup_method(self):
        """Setup test system."""
        self.config = {
            'interactive': {
                'enable_executing_agent': True,
                'enable_specialized_agents': True,
                'enable_general_agent': True,
            },
            'user_preferences': {
                'author': 'Test User',
                'license': 'MIT',
            }
        }
        self.system = MomInteractiveSystem(self.config)
    
    def test_system_initialization(self):
        """Test system initializes correctly."""
        assert self.system.registry is not None
        assert self.system.router is not None
        assert len(self.system.registry.get_all_agents()) > 0
    
    def test_context_creation(self):
        """Test execution context creation."""
        context = self.system.create_execution_context("test task")
        
        assert context.current_task == "test task"
        assert context.user_preferences['author'] == 'Test User'
        assert context.working_directory
    
    def test_project_info_extraction(self):
        """Test project info extraction from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a package.json
            package_json = temp_path / "package.json"
            package_json.write_text('{"name": "test-project", "version": "2.0.0"}')
            
            # Test extraction
            info = self.system._extract_project_info(temp_path)
            
            assert info['name'] == 'test-project'
            assert info['version'] == '2.0.0'
            assert info['type'] == 'javascript'
    
    def test_command_execution_real(self):
        """Test command execution with real subprocess."""
        # Set up callback
        callback_mock = Mock(return_value="y")
        self.system.set_executing_agent_callback(callback_mock)
        
        # Execute simple command
        context = self.system.create_execution_context("test")
        result = self.system.execute_command("echo 'test output'", context)
        
        assert isinstance(result, CommandResult)
        assert result.success
        assert "test output" in result.stdout
    
    def test_agent_stats(self):
        """Test agent statistics."""
        stats = self.system.get_agent_stats()
        
        assert 'agents' in stats
        assert 'total_agents' in stats
        assert stats['total_agents'] > 0


class TestGeneralAgent:
    """Test GeneralAgent functionality."""
    
    def test_pattern_responses(self):
        """Test pattern-based responses."""
        agent = GeneralAgent()
        context = ExecutionContext("test", project_info={"name": "test-project"})
        
        # Test confirmation
        response = agent.handle_prompt("Continue? (y/n)", "test", context)
        assert response == "y"
        
        # Test version
        response = agent.handle_prompt("version:", "test", context)
        assert response == "1.0.0"
        
        # Test project name substitution
        response = agent.handle_prompt("project name:", "test", context)
        assert "test-project" in response
    
    def test_safe_defaults(self):
        """Test safe default responses."""
        agent = GeneralAgent()
        context = ExecutionContext("test")
        
        # Test delete prompt (should be conservative)
        response = agent.handle_prompt("Delete files? (y/n)", "test", context)
        assert response == "n"
        
        # Test unknown prompt
        response = agent.handle_prompt("Unknown prompt:", "test", context)
        assert response == ""  # Safe default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])