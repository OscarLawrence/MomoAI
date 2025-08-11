"""
End-to-end integration tests for momo-cmd.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from momo_cmd.cli import mom
from momo_cmd.router import ContextAwareCommandRouter
from momo_cmd.context import WorkspaceContext
from click.testing import CliRunner


class TestIntegrationScenarios:
    """Test realistic usage scenarios."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create workspace structure
            (workspace / "nx.json").touch()
            (workspace / "CLAUDE.md").touch()

            # Create Python module
            module_dir = workspace / "code" / "libs" / "python" / "test-module"
            module_dir.mkdir(parents=True)

            # Create pyproject.toml
            (module_dir / "pyproject.toml").write_text("""
[project]
name = "test-module"
version = "1.0.0"
            """)

            # Create project.json
            project_json = {
                "targets": {
                    "test-fast": {"command": "pytest tests/unit tests/e2e"},
                    "format": {"command": "ruff format ."},
                    "lint": {"command": "ruff check ."},
                }
            }
            (module_dir / "project.json").write_text(json.dumps(project_json))

            # Create test files
            (module_dir / "test_module").mkdir()
            (module_dir / "tests" / "unit").mkdir(parents=True)
            (module_dir / "scripts").mkdir()

            test_script = module_dir / "scripts" / "demo.py"
            test_script.write_text(
                '#!/usr/bin/env python\nprint("Hello from demo script")'
            )
            test_script.chmod(0o755)

            yield workspace

    def test_context_detection_from_workspace_root(self, temp_workspace):
        """Test context detection from workspace root."""
        with patch("momo_cmd.context.Path.cwd", return_value=temp_workspace):
            context = WorkspaceContext()

            assert context.workspace_root == temp_workspace
            assert context.current_module is None

    def test_context_detection_from_module_directory(self, temp_workspace):
        """Test context detection from within module directory."""
        module_dir = temp_workspace / "code" / "libs" / "python" / "test-module"

        with patch("momo_cmd.context.Path.cwd", return_value=module_dir):
            context = WorkspaceContext()

            assert context.workspace_root == temp_workspace
            assert context.current_module == "test-module"

            # Test module info
            module_info = context.get_module_info()
            assert module_info is not None
            assert module_info.name == "test-module"
            assert module_info.has_uv is True
            assert module_info.has_nx is True
            assert "test-fast" in module_info.available_commands

    def test_module_command_explicit_target(self, temp_workspace):
        """Test module command with explicit target."""
        with patch("momo_cmd.context.Path.cwd", return_value=temp_workspace):
            router = ContextAwareCommandRouter()

            # Test dry run to avoid actual execution
            with patch("builtins.print") as mock_print:
                result = router.route_and_execute(["test-fast", "test-module"])

                # Should classify as module strategy
                strategy = router._classify_command(["test-fast", "test-module"])
                assert strategy.__class__.__name__ == "ContextAwareModuleStrategy"
                assert strategy.command == "test-fast"
                assert strategy.args == ["test-module"]

    def test_module_command_context_aware(self, temp_workspace):
        """Test context-aware module command execution."""
        module_dir = temp_workspace / "code" / "libs" / "python" / "test-module"

        with patch("momo_cmd.context.Path.cwd", return_value=module_dir):
            router = ContextAwareCommandRouter()

            # Test classification
            strategy = router._classify_command(["test-fast"])
            assert strategy.__class__.__name__ == "ContextAwareModuleStrategy"

            # Test target module determination
            target_module, extra_args = strategy._determine_target_module()
            assert target_module == "test-module"
            assert extra_args == []

    def test_file_execution_in_module_environment(self, temp_workspace):
        """Test file execution with module environment detection."""
        module_dir = temp_workspace / "code" / "libs" / "python" / "test-module"
        script_file = module_dir / "scripts" / "demo.py"

        with patch("momo_cmd.context.Path.cwd", return_value=module_dir):
            router = ContextAwareCommandRouter()

            # Test classification
            strategy = router._classify_command(["scripts/demo.py"])
            assert strategy.__class__.__name__ == "ContextAwareFileStrategy"

            # Test target module determination
            target_module = strategy._determine_target_module(script_file)
            assert target_module == "test-module"

    def test_passthrough_command(self, temp_workspace):
        """Test passthrough command execution."""
        with patch("momo_cmd.context.Path.cwd", return_value=temp_workspace):
            router = ContextAwareCommandRouter()

            # Test classification
            strategy = router._classify_command(["git", "status"])
            assert strategy.__class__.__name__ == "PassthroughCommandStrategy"

            # Test enhancement
            enhanced = strategy._enhance_command(["git", "status"])
            assert enhanced == ["git", "status", "--short", "--branch"]


class TestCLIIntegration:
    """Test CLI interface integration."""

    def test_cli_help_display(self):
        """Test CLI help display."""
        runner = CliRunner()
        result = runner.invoke(mom, [])

        assert result.exit_code == 0
        assert "Universal command interface" in result.output
        assert "Examples:" in result.output

    def test_cli_context_display(self):
        """Test CLI context display."""
        runner = CliRunner()

        with patch("momo_cmd.cli.WorkspaceContext") as mock_context_cls:
            mock_context = MagicMock()
            mock_context.workspace_root = Path("/project")
            mock_context.cwd = Path("/project/current")
            mock_context.current_module = "test-module"
            mock_context.get_module_info.return_value = None
            mock_context_cls.return_value = mock_context

            result = runner.invoke(mom, ["--context"])

            assert result.exit_code == 0
            assert "/project" in result.output
            assert "test-module" in result.output

    def test_cli_dry_run_mode(self):
        """Test CLI dry run mode."""
        runner = CliRunner()

        with patch("momo_cmd.router.ContextAwareCommandRouter") as mock_router_cls:
            mock_router = MagicMock()
            mock_router.route_and_execute.return_value = True
            mock_router_cls.return_value = mock_router

            result = runner.invoke(mom, ["--dry-run", "test-command"])

            assert result.exit_code == 0
            # Should create router with dry_run=True
            mock_router_cls.assert_called_with(verbose=False, dry_run=True)

    def test_cli_verbose_mode(self):
        """Test CLI verbose mode."""
        runner = CliRunner()

        with patch("momo_cmd.router.ContextAwareCommandRouter") as mock_router_cls:
            mock_router = MagicMock()
            mock_router.route_and_execute.return_value = True
            mock_router_cls.return_value = mock_router

            result = runner.invoke(mom, ["--verbose", "test-command"])

            assert result.exit_code == 0
            # Should create router with verbose=True
            mock_router_cls.assert_called_with(verbose=True, dry_run=False)

    def test_cli_execution_success(self):
        """Test successful command execution through CLI."""
        runner = CliRunner()

        with patch("momo_cmd.router.ContextAwareCommandRouter") as mock_router_cls:
            mock_router = MagicMock()
            mock_router.route_and_execute.return_value = True
            mock_router_cls.return_value = mock_router

            result = runner.invoke(mom, ["test-command", "arg1"])

            assert result.exit_code == 0
            mock_router.route_and_execute.assert_called_with(["test-command", "arg1"])

    def test_cli_execution_failure(self):
        """Test failed command execution through CLI."""
        runner = CliRunner()

        with patch("momo_cmd.router.ContextAwareCommandRouter") as mock_router_cls:
            mock_router = MagicMock()
            mock_router.route_and_execute.return_value = False
            mock_router_cls.return_value = mock_router

            result = runner.invoke(mom, ["test-command"])

            assert result.exit_code == 1


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_module_specified(self):
        """Test handling of invalid module specification."""
        with patch("momo_cmd.context.Path.cwd", return_value=Path("/project")):
            router = ContextAwareCommandRouter()

            # Mock context with no modules
            router.context.get_module_info = MagicMock(return_value=None)
            router.context.current_module = None

            strategy = router._classify_command(["test-fast", "nonexistent-module"])

            # Should still classify as module strategy
            assert strategy.__class__.__name__ == "ContextAwareModuleStrategy"

            # But execution should show help
            with patch.object(
                strategy, "_show_context_help", return_value=False
            ) as mock_help:
                result = strategy.execute()
                assert result is False
                mock_help.assert_called_once()

    def test_file_not_found_handling(self):
        """Test handling when file doesn't exist."""
        with patch("momo_cmd.context.Path.cwd", return_value=Path("/project")):
            router = ContextAwareCommandRouter()

            strategy = router._classify_command(["nonexistent.py"])

            # Should classify as file strategy
            assert strategy.__class__.__name__ == "ContextAwareFileStrategy"

            # But execution should fail gracefully
            with patch("builtins.print") as mock_print:
                result = strategy.execute()
                assert result is False
                # Should print helpful error message
                error_printed = any(
                    "File not found" in str(call) for call in mock_print.call_args_list
                )
                assert error_printed

    def test_command_execution_timeout(self):
        """Test handling of command execution timeout."""
        with patch("momo_cmd.context.Path.cwd", return_value=Path("/project")):
            router = ContextAwareCommandRouter()

            strategy = router._classify_command(["sleep", "1000"])

            # Mock subprocess timeout
            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired("sleep 1000", 1)
            ):
                with patch("builtins.print") as mock_print:
                    result = strategy.execute()
                    assert result is False

                    # Should print timeout message
                    timeout_printed = any(
                        "timed out" in str(call) for call in mock_print.call_args_list
                    )
                    assert timeout_printed
