"""
Universal command router with intelligent classification.

Main orchestration component that routes commands to appropriate execution strategies.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .strategies.base import ExecutionStrategy

from .command_groups import CommandGroupRegistry
from .context import WorkspaceContext
from .detectors import CommandDetectorRegistry


class ContextAwareCommandRouter:
    """Universal command router with intelligent classification."""

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        self.context = WorkspaceContext()
        self.verbose = verbose
        self.dry_run = dry_run
        self.detectors = CommandDetectorRegistry()
        self.command_groups = CommandGroupRegistry()

    def route_and_execute(self, args: list[str]) -> bool:
        """Main entry point - intelligently route and execute any command."""
        if not args:
            return self._show_help()

        # Try grouped commands first (mo create, mo validate, etc.)
        if self._try_grouped_commands(args):
            return True

        # Fallback to original strategy-based routing
        strategy = self._classify_command(args)

        if self.verbose:
            self._show_execution_plan(strategy, args)

        if self.dry_run:
            print(f"Would execute: {strategy.get_execution_preview()}")
            return True

        # Execute with comprehensive error handling
        try:
            return strategy.execute()
        except Exception as e:
            self._handle_execution_error(e, strategy, args)
            return False

    def _classify_command(self, args: list[str]) -> "ExecutionStrategy":
        """Intelligent command classification using detector chain."""

        # Try each detector in priority order
        for detector in self.detectors.get_detectors():
            if detector.can_handle(args, self.context):
                return detector.create_strategy(args, self.context)

        # Fallback to passthrough (should never reach here due to PassthroughDetector)
        from .strategies.passthrough import PassthroughCommandStrategy

        return PassthroughCommandStrategy(args, self.context)

    def _try_grouped_commands(self, args: list[str]) -> bool:
        """Try to handle command using grouped command system."""
        if not args:
            return False

        verb = args[0]
        remaining_args = args[1:]

        # Find appropriate command group handler
        handler = self.command_groups.find_handler(verb, remaining_args)
        if handler:
            if self.verbose:
                print(f"🎯 Using grouped command: {verb}")
                print(f"📁 Context: {self.context.current_module or 'workspace root'}")

            if self.dry_run:
                print(
                    f"Would execute grouped command: {verb} {' '.join(remaining_args)}"
                )
                return True

            try:
                return handler.execute(verb, remaining_args, self.context)
            except Exception as e:
                print(f"❌ Grouped command failed: {e}")
                return False

        return False

    def _show_execution_plan(self, strategy: "ExecutionStrategy", args: list[str]):
        """Show detailed execution plan for debugging."""
        print(f"🎯 Strategy: {strategy.__class__.__name__}")
        print(f"📁 Context: {self.context.current_module or 'workspace root'}")
        print(f"📍 Working dir: {self.context.cwd}")
        print(f"⚡ Command preview: {strategy.get_execution_preview()}")

    def _show_help(self) -> bool:
        """Show help information."""
        print("Universal Command Interface - mo <command>")
        print()
        print("🎯 Idea Workflow (New!):")
        print('  mo create idea "topic"          # Create idea with templates')
        print("  mo investigate idea-001         # Guide agent through research")
        print("  mo decide idea-001              # Create decision from investigation")
        print("  mo implement idea-001           # Implement with ADR creation")
        print()
        print("🎯 Other Grouped Commands:")
        print("  mo validate system              # Full system validation")
        print("  mo status                       # Show current status")
        print()
        print("⚡ Simple Module Commands:")
        print("  mo test module-name             # Test module")
        print("  mo format module-name           # Format module")
        print("  mo build module-name            # Build module")
        print()
        print("🔧 File Execution & Passthrough:")
        print("  mo test.py                      # Execute Python file")
        print("  mo git status                   # Enhanced git commands")
        print()
        print("Options:")
        print("  --verbose    Show execution details")
        print("  --dry-run    Show what would be executed")
        print("  --context    Show current context")
        return True

    def _handle_execution_error(
        self, error: Exception, strategy: "ExecutionStrategy", args: list[str]
    ) -> None:
        """Handle execution errors with helpful feedback."""
        print(f"❌ Execution failed with {strategy.__class__.__name__}")
        print(f"Command: {' '.join(args)}")
        print(f"Error: {error}")

        # Provide context-specific suggestions
        if self.context.current_module:
            module_info = self.context.get_module_info()
            if module_info:
                print(
                    f"💡 Available commands in {self.context.current_module}: {', '.join(module_info.available_commands)}"
                )
        else:
            print("💡 Try specifying a module: mom <command> <module-name>")
            print("💡 Or run from within a module directory")
