"""
Workspace and module context detection system.

Automatically detects:
- Workspace root (nx.json, CLAUDE.md, .git markers)
- Current module when working within module directories
- Module information (uv, nx configuration, available commands)
"""

import json
from pathlib import Path
from typing import Optional


class WorkspaceContext:
    """Context detection for workspace and module information."""

    def __init__(self, cwd: Path = None):
        self.cwd = cwd or Path.cwd()
        self.workspace_root = self._find_workspace_root()
        self.current_module = self._detect_current_module()
        self._module_cache = {}  # Cache for module info

    def _find_workspace_root(self) -> Path:
        """Walk up directory tree to find workspace root."""
        current = self.cwd
        markers = ["nx.json", "CLAUDE.md", ".git", "package.json"]

        while current != current.parent:
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        return self.cwd

    def _detect_current_module(self) -> Optional[str]:
        """Detect if currently working within a module directory."""
        try:
            relative = self.cwd.relative_to(self.workspace_root)
            parts = relative.parts

            # Pattern: code/libs/python/module-name/...
            if len(parts) >= 4 and parts[0:3] == ("code", "libs", "python"):
                return parts[3]

            # Pattern: root-level module directories (momo-workflow/)
            if len(parts) >= 1 and parts[0].startswith("momo-"):
                # Verify it's actually a module directory
                potential_module = self.workspace_root / parts[0]
                if self._is_module_directory(potential_module):
                    return parts[0]

        except ValueError:
            pass

        return None

    def _is_module_directory(self, path: Path) -> bool:
        """Check if directory is a valid module."""
        return any(
            [
                (path / "pyproject.toml").exists(),
                (path / "project.json").exists(),
                (path / "package.json").exists(),
            ]
        )

    def get_module_info(self, module: str = None) -> Optional["ModuleInfo"]:
        """Get comprehensive module information."""
        target_module = module or self.current_module
        if not target_module:
            return None

        # Check cache first
        if target_module in self._module_cache:
            return self._module_cache[target_module]

        # Find module directory
        module_paths = [
            self.workspace_root / "code" / "libs" / "python" / target_module,
            self.workspace_root / target_module,  # Root level modules
        ]

        for path in module_paths:
            if path.exists() and self._is_module_directory(path):
                module_info = ModuleInfo(target_module, path)
                self._module_cache[target_module] = module_info
                return module_info

        return None


class ModuleInfo:
    """Information about a specific module."""

    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.has_uv = (path / "pyproject.toml").exists()
        self.has_nx = (path / "project.json").exists()
        self.has_npm = (path / "package.json").exists()
        self.available_commands = self._discover_commands()

    def _discover_commands(self) -> list[str]:
        """Auto-discover available commands for this module."""
        commands = set()

        # Check nx project.json targets
        if self.has_nx:
            try:
                with open(self.path / "project.json") as f:
                    project_data = json.load(f)
                    targets = project_data.get("targets", {})
                    commands.update(targets.keys())
            except:
                pass

        # Check npm scripts
        if self.has_npm:
            try:
                with open(self.path / "package.json") as f:
                    package_data = json.load(f)
                    scripts = package_data.get("scripts", {})
                    commands.update(scripts.keys())
            except:
                pass

        # Add common Python module commands
        if self.has_uv:
            common_commands = [
                "test-fast",
                "test-all",
                "format",
                "lint",
                "typecheck",
                "install",
                "benchmark",
            ]
            commands.update(common_commands)

        return sorted(list(commands))

    def _validate_commands(self, commands: list[str]) -> list[str]:
        """Validate that commands are actually executable."""
        # For now, return all discovered commands
        # In the future, we could add actual validation
        return sorted(commands)
