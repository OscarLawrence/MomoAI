"""
Simplified CLI interface with universal mom command.

Provides a single entry point for all command execution needs.
"""

import sys
import click
from .router import ContextAwareCommandRouter
from .context import WorkspaceContext


@click.command()
@click.argument("args", nargs=-1, required=False)
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--dry-run", is_flag=True, help="Show what would be executed")
@click.option("--context", is_flag=True, help="Show current context")
def mom(args, verbose, dry_run, context):
    """Universal command interface - execute anything intelligently

    Examples:
        mom test.py                     # Execute Python file
        mom test-fast                   # Run test-fast for current module
        mom test-fast momo-agent        # Run test-fast for specific module
        mom git status                  # Enhanced git status
        mom scripts/benchmark.py        # Execute with module environment
    """

    if context:
        _show_context_info()
        return

    if not args:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return

    router = ContextAwareCommandRouter(verbose=verbose, dry_run=dry_run)
    success = router.route_and_execute(list(args))
    sys.exit(0 if success else 1)


def _show_context_info():
    """Show current workspace and module context."""
    ctx = WorkspaceContext()
    print(f"🏠 Workspace root: {ctx.workspace_root}")
    print(f"📁 Current directory: {ctx.cwd}")
    print(f"📦 Current module: {ctx.current_module or 'None'}")

    if ctx.current_module:
        module_info = ctx.get_module_info()
        if module_info:
            print(f"🔧 Module type: {_get_module_type(module_info)}")
            print(f"⚡ Available commands: {', '.join(module_info.available_commands)}")
            print(f"📍 Module path: {module_info.path}")


def _get_module_type(module_info) -> str:
    """Get human-readable module type."""
    types = []
    if module_info.has_uv:
        types.append("uv")
    if module_info.has_nx:
        types.append("nx")
    if module_info.has_npm:
        types.append("npm")

    return " + ".join(types) if types else "standard"


if __name__ == "__main__":
    mom()
