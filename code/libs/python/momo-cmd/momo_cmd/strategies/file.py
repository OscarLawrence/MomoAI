"""
File execution strategy with automatic environment detection.

Executes files using appropriate interpreters and module environments.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..context import WorkspaceContext, ModuleInfo

from .base import (
    ExecutionStrategy,
    FileExecutor,
    PythonFileExecutor,
    TypeScriptFileExecutor,
    JavaScriptFileExecutor,
    BashFileExecutor,
)


class ContextAwareFileStrategy(ExecutionStrategy):
    """Execute files with automatic environment detection."""

    def __init__(self, filename: str, args: list[str], context: "WorkspaceContext"):
        super().__init__(context)
        self.filename = filename
        self.args = args

    def execute(self) -> bool:
        file_path = self._resolve_file_path()
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            self._suggest_similar_files(file_path)
            return False

        target_module = self._determine_target_module(file_path)

        if target_module:
            return self._execute_in_module_environment(file_path, target_module)
        else:
            return self._execute_standard(file_path)

    def get_execution_preview(self) -> str:
        file_path = self._resolve_file_path()
        target_module = self._determine_target_module(file_path)

        if target_module:
            return f"Execute {file_path.name} using {target_module} environment"
        else:
            return f"Execute {file_path.name} with standard interpreter"

    def _resolve_file_path(self) -> Path:
        """Resolve file path relative to current context."""
        file_path = Path(self.filename)
        if not file_path.is_absolute():
            file_path = self.context.cwd / file_path
        return file_path.resolve()

    def _determine_target_module(self, file_path: Path) -> Optional[str]:
        """Determine which module environment should be used."""
        try:
            relative = file_path.relative_to(self.context.workspace_root)
            parts = relative.parts

            # Check if file is within a module directory
            if len(parts) >= 4 and parts[0:3] == ("code", "libs", "python"):
                return parts[3]

        except ValueError:
            pass

        # Fallback to current module context if file is relative
        if not Path(self.filename).is_absolute():
            return self.context.current_module

        return None

    def _execute_in_module_environment(self, file_path: Path, module: str) -> bool:
        """Execute file using specific module's environment."""
        module_info = self.context.get_module_info(module)
        if not module_info:
            print(f"⚠️  Module {module} not found, falling back to standard execution")
            return self._execute_standard(file_path)

        # Build execution command with module context
        executor = self._get_file_executor(file_path)

        if module_info.has_uv and file_path.suffix == ".py":
            # Use uv environment for Python files
            base_cmd = executor.get_command(file_path, self.args)
            # Replace 'python' with 'uv run python' if it starts with python
            if base_cmd.startswith("python "):
                base_cmd = base_cmd.replace("python ", "uv run python ", 1)
            cmd = f"cd {module_info.path} && {base_cmd}"
        else:
            # Use standard execution but from module directory
            cmd = f"cd {module_info.path} && {executor.get_command(file_path.resolve(), self.args)}"

        print(f"🚀 Executing in {module} environment: {file_path.name}")
        return self._execute_shell_command(cmd)

    def _execute_standard(self, file_path: Path) -> bool:
        """Execute file with standard system interpreter."""
        executor = self._get_file_executor(file_path)
        cmd = executor.get_command(file_path, self.args)

        print(f"🚀 Executing: {file_path.name}")
        return self._execute_shell_command(cmd, cwd=file_path.parent)

    def _get_file_executor(self, file_path: Path) -> FileExecutor:
        """Get appropriate executor for file type."""
        executors = {
            ".py": PythonFileExecutor(),
            ".ts": TypeScriptFileExecutor(),
            ".js": JavaScriptFileExecutor(),
            ".sh": BashFileExecutor(),
        }

        executor = executors.get(file_path.suffix)
        if executor:
            return executor

        # Try shebang detection
        return self._detect_from_shebang(file_path)

    def _detect_from_shebang(self, file_path: Path) -> FileExecutor:
        """Detect executor from shebang line."""
        try:
            with open(file_path, "r") as f:
                first_line = f.readline().strip()
                if first_line.startswith("#!"):
                    if "python" in first_line:
                        return PythonFileExecutor()
                    elif "node" in first_line:
                        return JavaScriptFileExecutor()
                    elif "bash" in first_line or "sh" in first_line:
                        return BashFileExecutor()
        except:
            pass

        # Fallback to generic executor
        return GenericFileExecutor()

    def _suggest_similar_files(self, file_path: Path) -> None:
        """Suggest similar files if the target file doesn't exist."""
        parent = file_path.parent
        if parent.exists():
            similar_files = []
            for file in parent.iterdir():
                if file.is_file() and file.stem.lower() == file_path.stem.lower():
                    similar_files.append(
                        str(file.relative_to(self.context.workspace_root))
                    )

            if similar_files:
                print(f"💡 Similar files found:")
                for similar_file in similar_files[:3]:  # Show max 3 suggestions
                    print(f"   {similar_file}")


class GenericFileExecutor(FileExecutor):
    """Generic file executor that tries to execute the file directly."""

    def get_command(self, file_path: Path, args: list[str]) -> str:
        import shlex

        args_str = " ".join(shlex.quote(arg) for arg in args)
        return f"{file_path} {args_str}".strip()
