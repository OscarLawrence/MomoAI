"""
TDD Tests for nx command routing fix.

These tests should FAIL initially, then pass after implementation.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from momo_cmd.strategies.module import ContextAwareModuleStrategy


class TestNxCommandRoutingFix:
    """Test that nx commands are properly detected and routed."""

    @pytest.fixture
    def mock_context_with_nx(self):
        """Mock context with nx project."""
        mock_ctx = MagicMock()
        mock_ctx.workspace_root = Path("/project")
        mock_ctx.current_module = "momo-cmd"

        # Mock module info that should have nx
        mock_module_info = MagicMock()
        mock_module_info.name = "momo-cmd"
        mock_module_info.has_nx = True
        mock_module_info.has_uv = True
        mock_module_info.path = Path("/project/code/libs/python/momo-cmd")
        mock_module_info.available_commands = ["test", "format", "lint", "typecheck"]

        mock_ctx.get_module_info.return_value = mock_module_info

        return mock_ctx

    def test_nx_command_should_be_tried_first(self, mock_context_with_nx):
        """TEST: nx commands should be tried before uv commands."""
        strategy = ContextAwareModuleStrategy(
            "test", ["momo-cmd"], mock_context_with_nx
        )

        with patch("subprocess.run") as mock_run:
            # Mock successful nx show command (project exists) with JSON response
            mock_run.side_effect = [
                MagicMock(
                    returncode=0, stdout='{"targets": {"test": {"command": "pytest"}}}'
                ),  # nx show project check succeeds
                MagicMock(returncode=0),  # nx run command succeeds
            ]

            with patch("builtins.print") as mock_print:
                result = strategy.execute()

                assert result is True

                # Should print nx usage message
                print_calls = [str(call) for call in mock_print.call_args_list]
                nx_usage_found = any("📦 Using nx:" in call for call in print_calls)
                assert nx_usage_found, f"Expected nx usage message, got: {print_calls}"

    def test_nx_command_detection_uses_correct_syntax(self, mock_context_with_nx):
        """TEST: nx command detection should use simple nx run syntax."""
        strategy = ContextAwareModuleStrategy(
            "test", ["momo-cmd"], mock_context_with_nx
        )

        with patch("subprocess.run") as mock_run:
            # Mock nx project check with JSON response
            mock_run.side_effect = [
                MagicMock(
                    returncode=0, stdout='{"targets": {"test": {"command": "pytest"}}}'
                ),  # nx show succeeds with test target
                MagicMock(returncode=0),  # nx run succeeds
            ]

            strategy.execute()

            # Check that the correct commands were called
            calls = [call[0][0] for call in mock_run.call_args_list]

            # Should use simple nx run syntax
            nx_run_call = None
            for call in calls:
                if "run" in call and "momo-cmd:test" in call:
                    nx_run_call = call
                    break

            assert nx_run_call is not None, f"No nx run call found in: {calls}"
            assert nx_run_call == "nx run momo-cmd:test", (
                f"Expected 'nx run momo-cmd:test', got: {nx_run_call}"
            )

    def test_fallback_to_uv_when_nx_fails(self, mock_context_with_nx):
        """TEST: Should fallback to uv when nx command fails."""
        strategy = ContextAwareModuleStrategy(
            "test", ["momo-cmd"], mock_context_with_nx
        )

        with patch("subprocess.run") as mock_run:
            # Mock nx check fails, but uv succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1),  # nx show fails
                MagicMock(returncode=0),  # uv command succeeds
            ]

            with patch("builtins.print") as mock_print:
                result = strategy.execute()

                assert result is True

                # Should print uv usage message since nx failed
                print_calls = [str(call) for call in mock_print.call_args_list]
                uv_usage_found = any("🐍 Using uv:" in call for call in print_calls)
                assert uv_usage_found, f"Expected uv usage message, got: {print_calls}"
