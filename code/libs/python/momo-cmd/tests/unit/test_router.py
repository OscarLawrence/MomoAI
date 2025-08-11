"""
Tests for command router and classification.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from momo_cmd.router import ContextAwareCommandRouter
from momo_cmd.context import WorkspaceContext
from momo_cmd.strategies.file import ContextAwareFileStrategy
from momo_cmd.strategies.module import ContextAwareModuleStrategy
from momo_cmd.strategies.passthrough import PassthroughCommandStrategy


class TestContextAwareCommandRouter:
    """Test command router functionality."""

    def test_command_classification_file_execution(self):
        """Test classification of file execution commands."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter()
            router.context = MagicMock()
            router.context.cwd = Path("/project")

            # Mock file exists
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "is_file", return_value=True):
                    strategy = router._classify_command(["test.py", "arg1"])

                    assert isinstance(strategy, ContextAwareFileStrategy)
                    assert strategy.filename == "test.py"
                    assert strategy.args == ["arg1"]

    def test_command_classification_module_command(self):
        """Test classification of module commands."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter()
            router.context = MagicMock()

            strategy = router._classify_command(["test-fast", "momo-agent"])

            assert isinstance(strategy, ContextAwareModuleStrategy)
            assert strategy.command == "test-fast"
            assert strategy.args == ["momo-agent"]

    def test_command_classification_passthrough(self):
        """Test classification of passthrough commands."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter()
            router.context = MagicMock()

            strategy = router._classify_command(["git", "status"])

            assert isinstance(strategy, PassthroughCommandStrategy)
            assert strategy.args == ["git", "status"]

    def test_route_and_execute_success(self):
        """Test successful command routing and execution."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter()
            router.context = MagicMock()

            # Mock strategy that returns True
            mock_strategy = MagicMock()
            mock_strategy.execute.return_value = True
            mock_strategy.get_execution_preview.return_value = "test preview"

            with patch.object(router, "_classify_command", return_value=mock_strategy):
                result = router.route_and_execute(["test-command"])

                assert result is True
                mock_strategy.execute.assert_called_once()

    def test_route_and_execute_failure(self):
        """Test command routing with execution failure."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter()
            router.context = MagicMock()

            # Mock strategy that returns False
            mock_strategy = MagicMock()
            mock_strategy.execute.return_value = False

            with patch.object(router, "_classify_command", return_value=mock_strategy):
                result = router.route_and_execute(["test-command"])

                assert result is False

    def test_route_and_execute_dry_run(self):
        """Test dry run mode."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter(dry_run=True)
            router.context = MagicMock()

            mock_strategy = MagicMock()
            mock_strategy.get_execution_preview.return_value = "test preview"

            with patch.object(router, "_classify_command", return_value=mock_strategy):
                with patch("builtins.print") as mock_print:
                    result = router.route_and_execute(["test-command"])

                    assert result is True
                    mock_strategy.execute.assert_not_called()  # Should not execute in dry run
                    mock_print.assert_called_with("Would execute: test preview")

    def test_verbose_mode(self):
        """Test verbose output mode."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter(verbose=True)
            router.context = MagicMock()
            router.context.current_module = "momo-agent"
            router.context.cwd = Path("/project/momo-agent")

            mock_strategy = MagicMock()
            mock_strategy.execute.return_value = True
            mock_strategy.get_execution_preview.return_value = "test preview"

            with patch.object(router, "_classify_command", return_value=mock_strategy):
                with patch.object(router, "_show_execution_plan") as mock_show_plan:
                    router.route_and_execute(["test-command"])

                    mock_show_plan.assert_called_once()

    def test_show_help_empty_args(self):
        """Test help display for empty arguments."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter()
            router.context = MagicMock()

            with patch("builtins.print") as mock_print:
                result = router.route_and_execute([])

                assert result is True
                # Should have printed help
                mock_print.assert_called()

    def test_handle_execution_error(self):
        """Test error handling during execution."""
        with patch.object(WorkspaceContext, "__init__", return_value=None):
            router = ContextAwareCommandRouter()
            router.context = MagicMock()
            router.context.current_module = "momo-agent"

            # Mock strategy that raises exception
            mock_strategy = MagicMock()
            mock_strategy.execute.side_effect = Exception("Test error")

            with patch.object(router, "_classify_command", return_value=mock_strategy):
                with patch.object(
                    router, "_handle_execution_error"
                ) as mock_handle_error:
                    result = router.route_and_execute(["test-command"])

                    assert result is False
                    mock_handle_error.assert_called_once()


class TestCommandRouterIntegration:
    """Integration tests for command router."""

    @pytest.fixture
    def mock_workspace_context(self):
        """Mock workspace context for testing."""
        with patch.object(WorkspaceContext, "__init__", return_value=None) as mock_init:
            mock_context = MagicMock()
            mock_context.workspace_root = Path("/project")
            mock_context.current_module = None
            mock_context.cwd = Path("/project")

            with patch.object(WorkspaceContext, "__new__", return_value=mock_context):
                yield mock_context

    def test_file_execution_integration(self, mock_workspace_context):
        """Test file execution end-to-end."""
        router = ContextAwareCommandRouter()

        # Mock file exists
        test_file = Path("/project/test.py")
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "is_file", return_value=True):
                with patch.object(Path, "resolve", return_value=test_file):
                    strategy = router._classify_command(["test.py"])

                    assert isinstance(strategy, ContextAwareFileStrategy)
                    preview = strategy.get_execution_preview()
                    assert "test.py" in preview

    def test_module_command_integration(self, mock_workspace_context):
        """Test module command end-to-end."""
        router = ContextAwareCommandRouter()

        strategy = router._classify_command(["test-fast"])

        assert isinstance(strategy, ContextAwareModuleStrategy)
        assert strategy.command == "test-fast"
