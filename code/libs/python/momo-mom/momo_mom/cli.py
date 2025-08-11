#!/usr/bin/env python3
"""
Main CLI entry point for Mom command mapping system.
"""

import sys
import click
from pathlib import Path
from typing import Optional

from .config import ConfigManager
from .executor import CommandExecutor
from .discovery import ScriptDiscovery


@click.group(invoke_without_command=True)
@click.option('--init-config', is_flag=True, help='Initialize configuration in current directory')
@click.option('--config', type=click.Path(), help='Specify config file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--ai-output/--raw-output', default=True, help='Use AI-tailored output formatting')
@click.option('--output-format', type=click.Choice(['structured', 'json', 'markdown']), default='structured', help='Output format for AI consumption')
@click.option('--expand', is_flag=True, help='Show full output (disable truncation)')
@click.pass_context
def main(ctx, init_config: bool, config: Optional[str], verbose: bool, ai_output: bool, output_format: str, expand: bool):
    """Mom - Universal command mapping system for AI-friendly developer tools."""
    
    if init_config:
        _init_config()
        return
    
    # If no subcommand provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return
    
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config_path'] = config
    ctx.obj['ai_output'] = ai_output
    ctx.obj['output_format'] = output_format
    ctx.obj['expand'] = expand


@main.command()
@click.argument('command_type')
@click.argument('args', nargs=-1)
@click.pass_context
def create(ctx, command_type: str, args):
    """Create new projects/modules."""
    _execute_command(ctx, 'create', command_type, args)


@main.command()
@click.argument('target')
@click.argument('args', nargs=-1) 
@click.pass_context
def test(ctx, target: str, args):
    """Run tests for specified target."""
    _execute_command(ctx, 'test', target, args)


@main.command()
@click.argument('target')
@click.argument('args', nargs=-1)
@click.pass_context
def build(ctx, target: str, args):
    """Build specified target."""
    _execute_command(ctx, 'build', target, args)


@main.command()
@click.argument('target')
@click.argument('args', nargs=-1)
@click.pass_context
def format(ctx, target: str, args):
    """Format code for specified target."""
    _execute_command(ctx, 'format', target, args)


@main.command()
@click.argument('script_name')
@click.argument('args', nargs=-1)
@click.pass_context
def script(ctx, script_name: str, args):
    """Execute script by name."""
    config_manager = _get_config_manager(ctx)
    discovery = ScriptDiscovery(config_manager.config)
    
    script_path = discovery.find_script(script_name)
    if not script_path:
        click.echo(f"Script '{script_name}' not found", err=True)
        _suggest_similar_scripts(discovery, script_name)
        sys.exit(1)
    
    # Override config with CLI options
    config = config_manager.config.copy()
    if 'output' not in config:
        config['output'] = {}
    config['output']['format'] = ctx.obj.get('output_format', 'structured')
    if ctx.obj.get('expand'):
        config['output']['head_lines'] = 1000
        config['output']['tail_lines'] = 1000
    
    executor = CommandExecutor(
        config,
        ctx.obj.get('verbose', False),
        ctx.obj.get('ai_output', True)
    )
    success = executor.execute_script(script_path, args)
    
    if not success:
        sys.exit(1)


@main.command('list-scripts')
@click.pass_context
def list_scripts(ctx):
    """List all available scripts."""
    config_manager = _get_config_manager(ctx)
    discovery = ScriptDiscovery(config_manager.config)
    
    scripts = discovery.list_available_scripts()
    
    if not scripts:
        click.echo("No scripts found in configured paths.")
        return
    
    for search_path, script_list in scripts.items():
        click.echo(f"\n📁 {search_path}:")
        for script_path in script_list:
            info = discovery.get_script_info(script_path)
            name = info['name']
            desc = info.get('description', 'No description')
            click.echo(f"  • {name} - {desc}")


@main.command('config')
@click.option('--show', is_flag=True, help='Show current configuration')
@click.option('--validate', is_flag=True, help='Validate configuration')
@click.pass_context
def config_cmd(ctx, show: bool, validate: bool):
    """Manage configuration."""
    config_manager = _get_config_manager(ctx)
    
    if show:
        if config_manager.config_path:
            click.echo(f"Configuration loaded from: {config_manager.config_path}")
            with open(config_manager.config_path, 'r') as f:
                click.echo(f.read())
        else:
            click.echo("Using default configuration (no config file found)")
            import yaml
            click.echo(yaml.dump(config_manager.config, default_flow_style=False))
    
    if validate:
        try:
            # Basic validation
            required_sections = ['commands', 'script_paths']
            for section in required_sections:
                if section not in config_manager.config:
                    click.echo(f"❌ Missing required section: {section}", err=True)
                    sys.exit(1)
            
            click.echo("✅ Configuration is valid")
        except Exception as e:
            click.echo(f"❌ Configuration validation failed: {e}", err=True)
            sys.exit(1)


@main.command('run')
@click.argument('shell_command', nargs=-1, required=True)
@click.pass_context
def run(ctx, shell_command):
    """Execute arbitrary shell command with mom's execution context."""
    config_manager = _get_config_manager(ctx)
    
    # Override config with CLI options
    config = config_manager.config.copy()
    if 'output' not in config:
        config['output'] = {}
    config['output']['format'] = ctx.obj.get('output_format', 'structured')
    if ctx.obj.get('expand'):
        config['output']['head_lines'] = 1000
        config['output']['tail_lines'] = 1000
    
    executor = CommandExecutor(
        config,
        ctx.obj.get('verbose', False),
        ctx.obj.get('ai_output', True)
    )
    
    command = ' '.join(shell_command)
    success = executor._execute_shell_command(command)
    
    if not success:
        sys.exit(1)


def _execute_command(ctx, command: str, target: str, args):
    """Execute a mapped command."""
    config_manager = _get_config_manager(ctx)
    
    # Override config with CLI options
    config = config_manager.config.copy()
    if 'output' not in config:
        config['output'] = {}
    config['output']['format'] = ctx.obj.get('output_format', 'structured')
    if ctx.obj.get('expand'):
        config['output']['head_lines'] = 1000
        config['output']['tail_lines'] = 1000
    
    executor = CommandExecutor(
        config, 
        ctx.obj.get('verbose', False),
        ctx.obj.get('ai_output', True)
    )
    
    success = executor.execute_command(command, target, args)
    if not success:
        sys.exit(1)


def _get_config_manager(ctx) -> ConfigManager:
    """Get configuration manager from context."""
    config_path = ctx.obj.get('config_path')
    return ConfigManager(config_path)


def _suggest_similar_scripts(discovery: ScriptDiscovery, script_name: str):
    """Suggest similar script names when exact match not found."""
    scripts = discovery.list_available_scripts()
    all_scripts = []
    
    for script_list in scripts.values():
        all_scripts.extend([s.stem for s in script_list])
    
    # Simple fuzzy matching
    suggestions = [s for s in all_scripts if script_name.lower() in s.lower() or s.lower() in script_name.lower()]
    
    if suggestions:
        click.echo("Did you mean one of these?")
        for suggestion in suggestions[:5]:  # Show max 5 suggestions
            click.echo(f"  • {suggestion}")
    else:
        click.echo("Run 'mom list-scripts' to see available scripts.")


def _init_config():
    """Initialize mom.yaml configuration in current directory."""
    config_path = Path.cwd() / "mom.yaml"
    
    if config_path.exists():
        click.echo(f"Configuration already exists at {config_path}")
        return
    
    # Create default configuration
    default_config = '''# Mom configuration file
# Configure command mappings for your project

# Command name (what you type after 'mom')
command_name: "mom"

# Command mappings
commands:
  create:
    python: "nx g @nxlv/python:uv-project {name} --directory=code/libs/python/{name}"
    fallback: "mkdir -p {name} && cd {name} && uv init"
    
  test:
    pattern: "nx run {target}:test"
    fallback: "cd {target} && uv run pytest"
    
  build:
    pattern: "nx run {target}:build"
    fallback: "cd {target} && uv build"
    
  format:
    pattern: "nx run {target}:format"
    fallback: "cd {target} && uv run ruff format ."

# Script discovery paths (relative to config file)
script_paths:
  - "scripts"
  - "code/libs/python/*/scripts"

# Execution settings
execution:
  auto_reset_on_cache_failure: true
  retry_count: 2
  timeout: 300

# AI-tailored output configuration
output:
  format: "structured"  # structured, json, markdown
  head_lines: 10        # Lines to show at start
  tail_lines: 10        # Lines to show at end
  max_line_length: 200  # Truncate long lines
  duplicate_threshold: 3 # Filter repeated lines
  
# Recovery commands (run when primary command fails)
recovery:
  nx_cache_reset: "nx reset"
'''
    
    config_path.write_text(default_config)
    click.echo(f"Created configuration at {config_path}")
    click.echo("Edit this file to customize command mappings for your project.")


if __name__ == "__main__":
    main()