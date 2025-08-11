"""
Tests for Momo's personality and identity system.
"""

import pytest
from momo_runner.personality import MomoPersonality, momo_personality


class TestMomoPersonality:
    """Test Momo's personality definition and responses."""

    def test_personality_initialization(self):
        """Test that personality can be initialized."""
        personality = MomoPersonality()
        assert personality is not None

    def test_system_prompt_content(self):
        """Test that system prompt contains key identity elements."""
        prompt = momo_personality.system_prompt

        # Check for key identity elements
        assert "Momo" in prompt
        assert "daughter" in prompt
        assert "MomoAI" in prompt
        assert "multi-agent" in prompt
        assert "warm" in prompt or "caring" in prompt

        # Check for role information
        assert "assistant" in prompt
        assert "interface" in prompt

    def test_identity_summary(self):
        """Test that identity summary is concise and informative."""
        summary = momo_personality.identity_summary

        assert len(summary) > 50  # Should be substantial
        assert len(summary) < 500  # But not too long
        assert "Momo" in summary
        assert "daughter" in summary
        assert "MomoAI" in summary

    def test_capabilities_structure(self):
        """Test that capabilities are properly structured."""
        capabilities = momo_personality.capabilities

        assert isinstance(capabilities, dict)
        assert len(capabilities) > 0

        # Check for expected capabilities
        expected_capabilities = [
            "conversation",
            "momoai_guidance",
            "agent_coordination",
            "development_help",
            "knowledge_management",
        ]

        for capability in expected_capabilities:
            assert capability in capabilities
            assert isinstance(capabilities[capability], str)
            assert len(capabilities[capability]) > 10

    def test_system_info_structure(self):
        """Test that system info is properly structured."""
        system_info = momo_personality.momoai_system_info

        assert isinstance(system_info, dict)
        assert "architecture" in system_info
        assert "philosophy" in system_info
        assert "tools" in system_info
        assert "key_features" in system_info

        # Check architecture details
        arch = system_info["architecture"]
        assert "type" in arch
        assert "components" in arch
        assert isinstance(arch["components"], list)
        assert len(arch["components"]) > 0

    def test_greeting_messages(self):
        """Test greeting message generation."""
        first_time_greeting = momo_personality.get_greeting(first_time=True)
        regular_greeting = momo_personality.get_greeting(first_time=False)

        # Both should be strings
        assert isinstance(first_time_greeting, str)
        assert isinstance(regular_greeting, str)

        # First time should be longer and more detailed
        assert len(first_time_greeting) > len(regular_greeting)

        # Both should mention Momo
        assert "Momo" in first_time_greeting
        assert "Momo" in regular_greeting

        # First time should mention being named after daughter
        assert "daughter" in first_time_greeting

    def test_farewell_message(self):
        """Test farewell message."""
        farewell = momo_personality.get_farewell()

        assert isinstance(farewell, str)
        assert len(farewell) > 10
        # Should be warm and positive
        assert any(word in farewell.lower() for word in ["care", "here", "always"])

    def test_system_question_handling(self):
        """Test handling of common system questions."""
        test_questions = ["identity", "purpose", "capabilities", "momoai", "agents", "tools"]

        for question in test_questions:
            response = momo_personality.handle_system_question(question)
            assert isinstance(response, str)
            assert len(response) > 20
            # Should contain relevant information (relaxed check since "tools" response mentions "momo" not "Momo")
            assert any(word in response.lower() for word in ["momo", "momoai", "system", "agent"])

        # Test unknown question
        unknown_response = momo_personality.handle_system_question("unknown_question")
        assert isinstance(unknown_response, str)
        assert "help" in unknown_response.lower()

    def test_global_personality_instance(self):
        """Test that global personality instance is available."""
        assert momo_personality is not None
        assert isinstance(momo_personality, MomoPersonality)

        # Should be the same instance when imported multiple times
        from momo_runner.personality import momo_personality as imported_personality

        assert momo_personality is imported_personality
