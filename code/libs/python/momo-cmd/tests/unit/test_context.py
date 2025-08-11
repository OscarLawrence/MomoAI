"""
Tests for workspace context detection.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from momo_cmd.context import WorkspaceContext, ModuleInfo


class TestWorkspaceContext:
    """Test workspace context detection functionality."""

    def test_workspace_root_detection_with_nx_json(self):
        """Test workspace root detection using nx.json marker."""
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = lambda: str(self).endswith("nx.json")

            context = WorkspaceContext(Path("/project/subdir"))
            # Would find workspace root by walking up
            assert context.workspace_root is not None

    def test_current_module_detection_python_libs(self):
        """Test current module detection in code/libs/python structure."""
        workspace_root = Path("/project")
        current_dir = (
            workspace_root / "code" / "libs" / "python" / "momo-agent" / "tests"
        )

        with patch.object(
            WorkspaceContext, "_find_workspace_root", return_value=workspace_root
        ):
            context = WorkspaceContext(current_dir)
            assert context.current_module == "momo-agent"

    def test_current_module_detection_root_level(self):
        """Test current module detection for root-level modules."""
        workspace_root = Path("/project")
        current_dir = workspace_root / "momo-workflow" / "src"

        with patch.object(
            WorkspaceContext, "_find_workspace_root", return_value=workspace_root
        ):
            with patch.object(
                WorkspaceContext, "_is_module_directory", return_value=True
            ):
                context = WorkspaceContext(current_dir)
                assert context.current_module == "momo-workflow"

    def test_no_module_detection_outside_modules(self):
        """Test no module detected when outside module directories."""
        workspace_root = Path("/project")
        current_dir = workspace_root / "docs"

        with patch.object(
            WorkspaceContext, "_find_workspace_root", return_value=workspace_root
        ):
            context = WorkspaceContext(current_dir)
            assert context.current_module is None

    def test_is_module_directory(self):
        """Test module directory detection."""
        context = WorkspaceContext()

        # Mock directory with pyproject.toml
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            assert context._is_module_directory(Path("/fake/module")) is True

    def test_get_module_info_caching(self):
        """Test module info caching."""
        workspace_root = Path("/project")
        module_path = workspace_root / "code" / "libs" / "python" / "momo-agent"

        with patch.object(
            WorkspaceContext, "_find_workspace_root", return_value=workspace_root
        ):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(
                    WorkspaceContext, "_is_module_directory", return_value=True
                ):
                    context = WorkspaceContext()

                    # First call
                    info1 = context.get_module_info("momo-agent")
                    # Second call should use cache
                    info2 = context.get_module_info("momo-agent")

                    assert info1 is info2  # Same object from cache


class TestModuleInfo:
    """Test module information discovery."""

    def test_module_info_basic_properties(self):
        """Test basic module info properties."""
        module_path = Path("/project/momo-agent")

        with patch.object(Path, "exists") as mock_exists:
            # Mock pyproject.toml exists, project.json doesn't
            mock_exists.side_effect = lambda: str(self).endswith("pyproject.toml")

            info = ModuleInfo("momo-agent", module_path)

            assert info.name == "momo-agent"
            assert info.path == module_path
            assert info.has_uv is True
            assert info.has_nx is False

    def test_command_discovery_from_nx_project_json(self):
        """Test command discovery from nx project.json."""
        module_path = Path("/project/momo-agent")

        project_data = {
            "targets": {
                "test-fast": {"command": "pytest tests/unit"},
                "format": {"command": "ruff format ."},
                "build": {"command": "python -m build"},
            }
        }

        mock_open = MagicMock()
        mock_open.return_value.__enter__.return_value.read.return_value = "json_data"

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = lambda: str(self).endswith("project.json")
            with patch("builtins.open", mock_open):
                with patch("json.load", return_value=project_data):
                    info = ModuleInfo("momo-agent", module_path)

                    expected_commands = ["build", "format", "test-fast"]
                    assert sorted(info.available_commands) == expected_commands

    def test_command_discovery_with_uv_common_commands(self):
        """Test that common uv commands are included."""
        module_path = Path("/project/momo-agent")

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = lambda: str(self).endswith("pyproject.toml")

            info = ModuleInfo("momo-agent", module_path)

            # Should include common uv commands
            common_commands = [
                "test-fast",
                "test-all",
                "format",
                "lint",
                "typecheck",
                "install",
                "benchmark",
            ]
            for cmd in common_commands:
                assert cmd in info.available_commands

    def test_command_discovery_npm_scripts(self):
        """Test command discovery from npm package.json scripts."""
        module_path = Path("/project/web-app")

        package_data = {
            "scripts": {"start": "npm run dev", "build": "nuxt build", "test": "vitest"}
        }

        mock_open = MagicMock()
        mock_open.return_value.__enter__.return_value.read.return_value = "json_data"

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = lambda: str(self).endswith("package.json")
            with patch("builtins.open", mock_open):
                with patch("json.load", return_value=package_data):
                    info = ModuleInfo("web-app", module_path)

                    assert "start" in info.available_commands
                    assert "build" in info.available_commands
                    assert "test" in info.available_commands
