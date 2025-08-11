"""
Tests for execution strategies.
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from momo_cmd.context import WorkspaceContext, ModuleInfo
from momo_cmd.strategies.file import ContextAwareFileStrategy
from momo_cmd.strategies.module import ContextAwareModuleStrategy
from momo_cmd.strategies.passthrough import PassthroughCommandStrategy


class TestContextAwareFileStrategy:
    """Test file execution strategy."""

    @pytest.fixture
    def mock_context(self):
        """Mock workspace context."""
        context = MagicMock(spec=WorkspaceContext)
        context.workspace_root = Path("/project")
        context.cwd = Path("/project/current")
        context.current_module = None
        return context

    def test_resolve_file_path_relative(self, mock_context):
        """Test resolving relative file paths."""
        strategy = ContextAwareFileStrategy("test.py", [], mock_context)

        with patch.object(
            Path, "resolve", return_value=Path("/project/current/test.py")
        ):
            resolved = strategy._resolve_file_path()
            assert str(resolved) == "/project/current/test.py"

    def test_resolve_file_path_absolute(self, mock_context):
        """Test resolving absolute file paths."""
        strategy = ContextAwareFileStrategy("/absolute/test.py", [], mock_context)

        with patch.object(Path, "resolve", return_value=Path("/absolute/test.py")):
            resolved = strategy._resolve_file_path()
            assert str(resolved) == "/absolute/test.py"

    def test_determine_target_module_from_path(self, mock_context):
        """Test module detection from file path."""
        strategy = ContextAwareFileStrategy("test.py", [], mock_context)

        # File in module directory
        file_path = Path("/project/code/libs/python/momo-agent/test.py")

        with patch.object(
            file_path,
            "relative_to",
            return_value=Path("code/libs/python/momo-agent/test.py"),
        ):
            module = strategy._determine_target_module(file_path)
            assert module == "momo-agent"

    def test_determine_target_module_fallback_to_context(self, mock_context):
        """Test fallback to current module context."""
        mock_context.current_module = "momo-workflow"
        strategy = ContextAwareFileStrategy("test.py", [], mock_context)

        # Relative file path outside module structure
        file_path = Path("/project/scripts/test.py")

        with patch.object(file_path, "relative_to", side_effect=ValueError):
            module = strategy._determine_target_module(file_path)
            assert module == "momo-workflow"

    def test_execute_file_not_found(self, mock_context):
        """Test execution when file doesn't exist."""
        strategy = ContextAwareFileStrategy("nonexistent.py", [], mock_context)

        with patch.object(Path, "exists", return_value=False):
            with patch.object(strategy, "_suggest_similar_files"):
                with patch("builtins.print") as mock_print:
                    result = strategy.execute()

                    assert result is False
                    mock_print.assert_called_with("❌ File not found: nonexistent.py")

    def test_execute_in_module_environment_python(self, mock_context):
        """Test execution in module environment for Python files."""
        strategy = ContextAwareFileStrategy("test.py", ["arg1"], mock_context)

        # Mock module info
        module_info = MagicMock(spec=ModuleInfo)
        module_info.has_uv = True
        module_info.path = Path("/project/momo-agent")

        mock_context.get_module_info.return_value = module_info

        with patch.object(Path, "exists", return_value=True):
            with patch.object(
                strategy, "_determine_target_module", return_value="momo-agent"
            ):
                with patch.object(
                    strategy, "_execute_shell_command", return_value=True
                ) as mock_exec:
                    with patch("builtins.print") as mock_print:
                        result = strategy.execute()

                        assert result is True
                        mock_print.assert_called_with(
                            "🚀 Executing in momo-agent environment: test.py"
                        )
                        mock_exec.assert_called_once()

                        # Should use uv run
                        call_args = mock_exec.call_args[0][0]
                        assert "uv run python" in call_args

    def test_execute_standard_execution(self, mock_context):
        """Test standard execution without module environment."""
        strategy = ContextAwareFileStrategy("test.py", ["arg1"], mock_context)

        with patch.object(Path, "exists", return_value=True):
            with patch.object(strategy, "_determine_target_module", return_value=None):
                with patch.object(
                    strategy, "_execute_shell_command", return_value=True
                ) as mock_exec:
                    with patch("builtins.print") as mock_print:
                        result = strategy.execute()

                        assert result is True
                        mock_print.assert_called_with("🚀 Executing: test.py")
                        mock_exec.assert_called_once()

    def test_get_file_executor_python(self, mock_context):
        """Test getting Python file executor."""
        strategy = ContextAwareFileStrategy("test.py", [], mock_context)

        executor = strategy._get_file_executor(Path("test.py"))
        command = executor.get_command(Path("test.py"), ["arg1"])

        assert command == "python test.py arg1"

    def test_get_file_executor_typescript(self, mock_context):
        """Test getting TypeScript file executor."""
        strategy = ContextAwareFileStrategy("test.ts", [], mock_context)

        executor = strategy._get_file_executor(Path("test.ts"))
        command = executor.get_command(Path("test.ts"), ["arg1"])

        assert command == "npx tsx test.ts arg1"


class TestContextAwareModuleStrategy:
    """Test module command execution strategy."""

    @pytest.fixture
    def mock_context(self):
        """Mock workspace context."""
        context = MagicMock(spec=WorkspaceContext)
        context.workspace_root = Path("/project")
        context.current_module = None
        return context

    def test_determine_target_module_explicit(self, mock_context):
        """Test explicit module specification."""
        strategy = ContextAwareModuleStrategy("test-fast", ["momo-agent"], mock_context)

        # Mock module exists
        mock_context.get_module_info.return_value = MagicMock()

        module, extra_args = strategy._determine_target_module()
        assert module == "momo-agent"
        assert extra_args == []

    def test_determine_target_module_context_aware(self, mock_context):
        """Test context-aware module detection."""
        mock_context.current_module = "momo-agent"
        strategy = ContextAwareModuleStrategy("test-fast", ["--verbose"], mock_context)

        # First arg is not a module (it's a flag)
        mock_context.get_module_info.return_value = None

        module, extra_args = strategy._determine_target_module()
        assert module == "momo-agent"
        assert extra_args == ["--verbose"]

    def test_determine_target_module_none(self, mock_context):
        """Test when no module can be determined."""
        strategy = ContextAwareModuleStrategy("test-fast", ["--verbose"], mock_context)

        mock_context.get_module_info.return_value = None
        mock_context.current_module = None

        module, extra_args = strategy._determine_target_module()
        assert module is None
        assert extra_args == ["--verbose"]

    def test_try_nx_command_success(self, mock_context):
        """Test successful nx command execution."""
        strategy = ContextAwareModuleStrategy("test-fast", [], mock_context)

        # Mock nx command exists
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value.returncode = 0  # Command exists

            with patch.object(
                strategy, "_execute_shell_command", return_value=True
            ) as mock_exec:
                with patch("builtins.print"):
                    result = strategy._try_nx_command("momo-agent", [])

                    assert result is True
                    mock_exec.assert_called_once()

                    # Should execute nx run command
                    call_args = mock_exec.call_args[0][0]
                    assert call_args == "nx run momo-agent:test-fast"

    def test_try_nx_command_not_available(self, mock_context):
        """Test nx command when not available."""
        strategy = ContextAwareModuleStrategy("test-fast", [], mock_context)

        # Mock nx command doesn't exist
        with patch.object(subprocess, "run") as mock_run:
            mock_run.return_value.returncode = 1  # Command doesn't exist

            result = strategy._try_nx_command("momo-agent", [])
            assert result is False

    def test_try_uv_command_success(self, mock_context):
        """Test successful uv command execution."""
        strategy = ContextAwareModuleStrategy("test-fast", [], mock_context)

        # Mock module info
        module_info = MagicMock(spec=ModuleInfo)
        module_info.has_uv = True
        module_info.path = Path("/project/momo-agent")

        mock_context.get_module_info.return_value = module_info

        with patch.object(
            strategy, "_execute_shell_command", return_value=True
        ) as mock_exec:
            with patch("builtins.print"):
                result = strategy._try_uv_command("momo-agent", [])

                assert result is True
                mock_exec.assert_called_once()

                # Should execute uv run command
                call_args = mock_exec.call_args[0][0]
                assert "uv run test-fast" in call_args

    def test_try_uv_command_no_uv(self, mock_context):
        """Test uv command when module doesn't have uv."""
        strategy = ContextAwareModuleStrategy("test-fast", [], mock_context)

        # Mock module info without uv
        module_info = MagicMock(spec=ModuleInfo)
        module_info.has_uv = False

        mock_context.get_module_info.return_value = module_info

        result = strategy._try_uv_command("momo-agent", [])
        assert result is False

    def test_try_common_patterns_test_fast(self, mock_context):
        """Test common pattern for test-fast command."""
        strategy = ContextAwareModuleStrategy("test-fast", [], mock_context)

        # Mock module info
        module_info = MagicMock(spec=ModuleInfo)
        module_info.has_uv = True
        module_info.path = Path("/project/momo-agent")

        mock_context.get_module_info.return_value = module_info

        with patch.object(
            strategy, "_execute_shell_command", return_value=True
        ) as mock_exec:
            with patch("builtins.print"):
                result = strategy._try_common_patterns("momo-agent", [])

                assert result is True

                # Should execute pytest command
                call_args = mock_exec.call_args[0][0]
                assert "pytest tests/unit tests/e2e" in call_args

    def test_show_context_help(self, mock_context):
        """Test context help display."""
        strategy = ContextAwareModuleStrategy("test-fast", [], mock_context)

        with patch.object(
            strategy,
            "_get_available_modules",
            return_value=["momo-agent", "momo-workflow"],
        ):
            with patch("builtins.print") as mock_print:
                result = strategy._show_context_help()

                assert result is False

                # Should print helpful information
                print_calls = [call.args[0] for call in mock_print.call_args_list]
                help_text = " ".join(print_calls)
                assert "test-fast" in help_text
                assert "momo-agent" in help_text


class TestPassthroughCommandStrategy:
    """Test passthrough command strategy."""

    @pytest.fixture
    def mock_context(self):
        """Mock workspace context."""
        context = MagicMock(spec=WorkspaceContext)
        context.workspace_root = Path("/project")
        return context

    def test_execute_basic_command(self, mock_context):
        """Test executing basic passthrough command."""
        strategy = PassthroughCommandStrategy(["echo", "hello"], mock_context)

        with patch.object(
            strategy, "_execute_shell_command", return_value=True
        ) as mock_exec:
            with patch("builtins.print"):
                result = strategy.execute()

                assert result is True
                call_args = mock_exec.call_args[0][0]
                assert call_args == "echo hello"

    def test_enhance_git_status(self, mock_context):
        """Test git status enhancement."""
        strategy = PassthroughCommandStrategy(["git", "status"], mock_context)

        enhanced = strategy._enhance_command(["git", "status"])
        assert enhanced == ["git", "status", "--short", "--branch"]

    def test_enhance_git_diff(self, mock_context):
        """Test git diff enhancement."""
        strategy = PassthroughCommandStrategy(["git", "diff"], mock_context)

        enhanced = strategy._enhance_command(["git", "diff"])
        assert enhanced == ["git", "diff", "--stat"]

    def test_enhance_ls_command(self, mock_context):
        """Test ls command enhancement."""
        strategy = PassthroughCommandStrategy(["ls"], mock_context)

        enhanced = strategy._enhance_command(["ls"])
        assert enhanced == ["ls", "-la", "--color=auto"]

    def test_enhance_find_python_files(self, mock_context):
        """Test find command enhancement for Python files."""
        strategy = PassthroughCommandStrategy(
            ["find", ".", "-name", "*.py"], mock_context
        )

        enhanced = strategy._enhance_command(["find", ".", "-name", "*.py"])

        # Should add exclusions
        assert "-not" in enhanced
        assert "*/__pycache__/*" in " ".join(enhanced)
        assert "*/.venv/*" in " ".join(enhanced)
        assert "*/node_modules/*" in " ".join(enhanced)

    def test_no_enhancement_for_unknown_commands(self, mock_context):
        """Test that unknown commands are not enhanced."""
        strategy = PassthroughCommandStrategy(["unknown-command", "arg"], mock_context)

        enhanced = strategy._enhance_command(["unknown-command", "arg"])
        assert enhanced == ["unknown-command", "arg"]

    def test_get_execution_preview(self, mock_context):
        """Test execution preview generation."""
        strategy = PassthroughCommandStrategy(["git", "status"], mock_context)

        preview = strategy.get_execution_preview()
        assert preview == "Execute: git status --short --branch"
