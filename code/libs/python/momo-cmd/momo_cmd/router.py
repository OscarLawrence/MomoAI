"""
Universal command router with intelligent classification.

Main orchestration component that routes commands to appropriate execution strategies.
"""

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .strategies.base import ExecutionStrategy

from .context import WorkspaceContext
from .detectors import CommandDetectorRegistry


class ContextAwareCommandRouter:
    """Universal command router with intelligent classification."""

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        self.context = WorkspaceContext()
        self.verbose = verbose
        self.dry_run = dry_run
        self.detectors = CommandDetectorRegistry()

    def route_and_execute(self, args: List[str]) -> bool:
        """Main entry point - intelligently route and execute any command."""
        if not args:
            return self._show_help()

        # Classify command type
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

    def _classify_command(self, args: List[str]) -> "ExecutionStrategy":
        """Intelligent command classification using detector chain."""

        # Try each detector in priority order
        for detector in self.detectors.get_detectors():
            if detector.can_handle(args, self.context):
                return detector.create_strategy(args, self.context)

        # Fallback to passthrough (should never reach here due to PassthroughDetector)
        from .strategies.passthrough import PassthroughCommandStrategy

        return PassthroughCommandStrategy(args, self.context)

    def _show_execution_plan(self, strategy: "ExecutionStrategy", args: List[str]):
        """Show detailed execution plan for debugging."""
        print(f"🎯 Strategy: {strategy.__class__.__name__}")
        print(f"📁 Context: {self.context.current_module or 'workspace root'}")
        print(f"📍 Working dir: {self.context.cwd}")
        print(f"⚡ Command preview: {strategy.get_execution_preview()}")

    def _show_help(self) -> bool:
        """Show help information."""
        print("Universal Command Interface - mom <anything>")
        print()
        print("Examples:")
        print("  mom test.py                     # Execute Python file")
        print("  mom test-fast                   # Run test-fast for current module")
        print("  mom test-fast momo-agent        # Run test-fast for specific module")
        print("  mom git status                  # Pass through to git")
        print("  mom scripts/benchmark.py        # Execute with correct environment")
        print()
        print("Options:")
        print("  --verbose    Show execution details")
        print("  --dry-run    Show what would be executed")
        print("  --context    Show current context")
        return True

    def _handle_execution_error(
        self, error: Exception, strategy: "ExecutionStrategy", args: List[str]
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
