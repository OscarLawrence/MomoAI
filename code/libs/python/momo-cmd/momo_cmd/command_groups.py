"""
Logical command grouping for agent-optimized workflows.

Implements mo <verb> <type> <target> pattern for consistency and simplicity.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .context import WorkspaceContext
from .idea_workflow import IdeaManager


class CommandGroup(ABC):
    """Base class for command groups."""

    @abstractmethod
    def can_handle(self, verb: str, args: list[str]) -> bool:
        """Check if this group can handle the command."""
        pass

    @abstractmethod
    def execute(self, verb: str, args: list[str], context: WorkspaceContext) -> bool:
        """Execute the command."""
        pass

    @abstractmethod
    def get_help(self) -> dict[str, str]:
        """Get help information for this group."""
        pass


class ModuleCommandGroup(CommandGroup):
    """Handle simple module operations: mo test, mo format, mo build"""

    SIMPLE_MODULE_COMMANDS = {
        "test": "test-fast",
        "test-all": "test-all",
        "format": "format",
        "lint": "lint",
        "typecheck": "typecheck",
        "build": "build",
        "install": "install",
        "benchmark": "benchmark",
    }

    def can_handle(self, verb: str, args: list[str]) -> bool:
        return verb in self.SIMPLE_MODULE_COMMANDS

    def execute(self, verb: str, args: list[str], context: WorkspaceContext) -> bool:
        from .strategies.module import ContextAwareModuleStrategy

        # Map simple command to actual command
        actual_command = self.SIMPLE_MODULE_COMMANDS[verb]

        strategy = ContextAwareModuleStrategy(actual_command, args, context)
        return strategy.execute()

    def get_help(self) -> dict[str, str]:
        return {
            "test": "Run tests for module",
            "format": "Format code in module",
            "build": "Build module",
            "lint": "Lint module code",
        }


class CreateCommandGroup(CommandGroup):
    """Handle creation commands: mo create task, mo create adr, mo create module"""

    def can_handle(self, verb: str, args: list[str]) -> bool:
        return verb == "create" and len(args) >= 2

    def execute(self, verb: str, args: list[str], context: WorkspaceContext) -> bool:
        create_type = args[0]

        if create_type == "idea":
            return self._create_idea(args[1:], context)
        elif create_type == "task":
            return self._create_task(args[1:], context)
        elif create_type == "adr":
            return self._create_adr(args[1:], context)
        elif create_type == "module":
            return self._create_module(args[1:], context)
        else:
            print(f"❌ Unknown creation type: {create_type}")
            print("Available: idea, task, adr, module")
            return False

    def _create_task(self, args: list[str], context: WorkspaceContext) -> bool:
        """Create a new structured task."""
        if not args:
            print('❌ Task description required: mo create task "description"')
            return False

        task_description = args[0]
        print(f"🎯 Creating task: {task_description}")

        # TODO: Integrate with task management system
        # For now, just show what would be created
        print(f"   - Task ID: task-{hash(task_description) % 10000:04d}")
        print(f"   - Description: {task_description}")
        print("   - Status: pending")
        print(f"   - Created in context: {context.current_module or 'workspace'}")

        return True

    def _create_idea(self, args: list[str], context: WorkspaceContext) -> bool:
        """Create a new idea with research templates."""
        if not args:
            print('❌ Idea topic required: mo create idea "topic"')
            return False

        topic = args[0]
        idea_manager = IdeaManager(context)
        idea_manager.create_idea(topic)

        return True

    def _create_adr(self, args: list[str], context: WorkspaceContext) -> bool:
        """Create new ADR workflow."""
        if not args:
            print('❌ ADR topic required: mo create adr "topic"')
            return False

        adr_topic = args[0]
        print(f"📋 Creating ADR: {adr_topic}")

        # TODO: Integrate with ADR workflow system
        print(f"   - Starting ADR workflow for: {adr_topic}")
        print("   - Investigation phase initiated")

        return True

    def _create_module(self, args: list[str], context: WorkspaceContext) -> bool:
        """Create new module."""
        if len(args) < 2:
            print(
                "❌ Module type and name required: mo create module python module-name"
            )
            return False

        module_type = args[0]
        module_name = args[1]

        if module_type == "python":
            return self._create_python_module(module_name, context)
        else:
            print(f"❌ Unknown module type: {module_type}")
            return False

    def _create_python_module(
        self, module_name: str, context: WorkspaceContext
    ) -> bool:
        """Create Python module using nx generator."""
        from .strategies.base import ExecutionStrategy

        class CreateModuleStrategy(ExecutionStrategy):
            def __init__(self, module_name: str, context: WorkspaceContext):
                super().__init__(context)
                self.module_name = module_name

            def execute(self) -> bool:
                cmd = f"nx g @nxlv/python:uv-project {self.module_name} --directory=code/libs/python/{self.module_name}"
                return self._execute_shell_command(cmd)

            def get_execution_preview(self) -> str:
                return f"Create Python module: {self.module_name}"

        strategy = CreateModuleStrategy(module_name, context)
        return strategy.execute()

    def get_help(self) -> dict[str, str]:
        return {
            "create idea": "Create idea with research templates",
            "create task": "Create structured task with validation",
            "create adr": "Start ADR workflow",
            "create module": "Create new module (python, node, etc.)",
        }


class ValidateCommandGroup(CommandGroup):
    """Handle validation commands: mo validate task, mo validate system"""

    def can_handle(self, verb: str, args: list[str]) -> bool:
        return verb == "validate"

    def execute(self, verb: str, args: list[str], context: WorkspaceContext) -> bool:
        if not args:
            return self._validate_current_context(context)

        validate_type = args[0]

        if validate_type == "system":
            return self._validate_system(context)
        elif validate_type == "module":
            module_name = args[1] if len(args) > 1 else context.current_module
            return self._validate_module(module_name, context)
        else:
            print(f"❌ Unknown validation type: {validate_type}")
            return False

    def _validate_current_context(self, context: WorkspaceContext) -> bool:
        """Validate current context (module or system)."""
        if context.current_module:
            return self._validate_module(context.current_module, context)
        else:
            return self._validate_system(context)

    def _validate_system(self, context: WorkspaceContext) -> bool:
        """Run full system validation."""
        print("🔍 Running system validation...")

        # Use the existing workflow validation script
        validation_script = context.workspace_root / "scripts" / "workflow-validate.py"
        if validation_script.exists():
            cmd = f"python3 {validation_script}"
            from .strategies.base import ExecutionStrategy

            class ValidationStrategy(ExecutionStrategy):
                def __init__(self, context: WorkspaceContext):
                    super().__init__(context)

                def execute(self) -> bool:
                    return self._execute_shell_command(cmd)

                def get_execution_preview(self) -> str:
                    return "Run system validation checks"

            strategy = ValidationStrategy(context)
            return strategy.execute()
        else:
            print("⚠️  System validation script not found")
            return False

    def _validate_module(self, module_name: str, context: WorkspaceContext) -> bool:
        """Validate specific module."""
        if not module_name:
            print("❌ Module name required")
            return False

        print(f"🔍 Validating module: {module_name}")

        # Run module validation sequence
        from .strategies.module import ContextAwareModuleStrategy

        checks = ["typecheck", "test-fast", "lint"]
        all_passed = True

        for check in checks:
            strategy = ContextAwareModuleStrategy(check, [], context)
            strategy.context = context  # Ensure context is set

            print(f"   Running {check}...")
            success = strategy.execute()
            if not success:
                all_passed = False
                print(f"   ❌ {check} failed")
            else:
                print(f"   ✅ {check} passed")

        return all_passed

    def get_help(self) -> dict[str, str]:
        return {
            "validate": "Validate current context",
            "validate system": "Full system validation",
            "validate module": "Validate specific module",
        }


class StatusCommandGroup(CommandGroup):
    """Handle status commands: mo status, mo status system"""

    def can_handle(self, verb: str, args: list[str]) -> bool:
        return verb == "status"

    def execute(self, verb: str, args: list[str], context: WorkspaceContext) -> bool:
        if not args:
            return self._show_current_status(context)

        status_type = args[0]

        if status_type == "system":
            return self._show_system_status(context)
        else:
            print(f"❌ Unknown status type: {status_type}")
            return False

    def _show_current_status(self, context: WorkspaceContext) -> bool:
        """Show current context status."""
        print("📊 Current Status")
        print(f"   Workspace: {context.workspace_root.name}")
        print(f"   Directory: {context.cwd.relative_to(context.workspace_root)}")
        print(f"   Module: {context.current_module or 'None'}")

        if context.current_module:
            module_info = context.get_module_info()
            if module_info:
                print(
                    f"   Available commands: {', '.join(module_info.available_commands[:5])}..."
                )

        return True

    def _show_system_status(self, context: WorkspaceContext) -> bool:
        """Show overall system status."""
        print("🏗️ System Status")

        # Count modules
        python_modules = context.workspace_root / "code" / "libs" / "python"
        if python_modules.exists():
            modules = [d for d in python_modules.iterdir() if d.is_dir()]
            print(f"   Python modules: {len(modules)}")

        # Check key files
        key_files = ["nx.json", "CLAUDE.md", ".git"]
        for file in key_files:
            exists = (context.workspace_root / file).exists()
            status = "✅" if exists else "❌"
            print(f"   {file}: {status}")

        return True

    def get_help(self) -> dict[str, str]:
        return {
            "status": "Show current context status",
            "status system": "Show overall system status",
        }


class IdeaWorkflowCommandGroup(CommandGroup):
    """Handle idea workflow commands: mo investigate, mo decide, mo implement"""

    def can_handle(self, verb: str, args: list[str]) -> bool:
        return verb in ["investigate", "decide", "implement"] and len(args) >= 1

    def execute(self, verb: str, args: list[str], context: WorkspaceContext) -> bool:
        idea_id = args[0]
        idea_manager = IdeaManager(context)

        if verb == "investigate":
            return idea_manager.investigate_idea(idea_id)
        elif verb == "decide":
            return idea_manager.create_decision(idea_id)
        elif verb == "implement":
            return idea_manager.implement_decision(idea_id)
        else:
            return False

    def get_help(self) -> dict[str, str]:
        return {
            "investigate": "Guide agent through idea investigation",
            "decide": "Create decision from investigation",
            "implement": "Implement decision with ADR creation",
        }


class CommandGroupRegistry:
    """Registry for all command groups."""

    def __init__(self):
        self.groups = [
            ModuleCommandGroup(),
            CreateCommandGroup(),
            ValidateCommandGroup(),
            StatusCommandGroup(),
            IdeaWorkflowCommandGroup(),
        ]

    def find_handler(self, verb: str, args: list[str]) -> Optional[CommandGroup]:
        """Find appropriate handler for command."""
        for group in self.groups:
            if group.can_handle(verb, args):
                return group
        return None

    def get_all_help(self) -> dict[str, dict[str, str]]:
        """Get help for all command groups."""
        help_info = {}
        for group in self.groups:
            group_name = group.__class__.__name__.replace("CommandGroup", "").lower()
            help_info[group_name] = group.get_help()
        return help_info
