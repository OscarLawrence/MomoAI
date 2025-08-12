#!/usr/bin/env python3
"""
Command system demonstration - shows pluggable command architecture.

This script demonstrates the command registry system, custom commands,
shell commands, and integration with workflow steps.
"""

import time
from pathlib import Path
from momo_workflow import WorkflowEngine, WorkflowDefinition, WorkflowContext
from momo_workflow.commands import (
    register_command,
    get_command_registry,
    CommandStep,
    ShellCommand,
    FunctionCommand,
)


# Register custom commands using decorator
@register_command("greet_user", "Greet a user with customizable message")
def greet_user(name: str, greeting: str = "Hello") -> str:
    """Custom greeting command."""
    message = f"{greeting}, {name}! Welcome to the workflow system."
    print(f"👋 {message}")
    return message


@register_command("create_config", "Create a configuration file")
def create_config(filename: str, config_data: dict) -> str:
    """Create configuration file from dictionary."""
    import json

    file_path = Path(filename)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w") as f:
        json.dump(config_data, f, indent=2)

    print(f"📝 Created config file: {file_path}")
    return str(file_path)


@register_command("process_data", "Process data with artificial delay")
def process_data(data: list, processing_time: float = 0.5) -> dict:
    """Simulate data processing with configurable delay."""
    print(f"⚡ Processing {len(data)} items (simulated delay: {processing_time}s)")
    time.sleep(processing_time)

    processed_result = {
        "items_processed": len(data),
        "total_sum": sum(x for x in data if isinstance(x, (int, float))),
        "processing_time": processing_time,
    }

    print(f"✅ Processing complete: {processed_result}")
    return processed_result


def demonstrate_command_registry():
    """Show command registry functionality."""
    print("🗂️  Command Registry Demonstration")
    print("-" * 40)

    registry = get_command_registry()

    # List all registered commands
    commands = registry.list_commands()
    print(f"📋 Registered commands ({len(commands)}):")
    for cmd_name in sorted(commands):
        command = registry.get_command(cmd_name)
        if command:
            print(f"  • {cmd_name}: {command.description}")

    print()

    # Test individual command execution
    print("🧪 Testing individual commands:")

    # Test greet_user command
    greet_cmd = registry.get_command("greet_user")
    if greet_cmd:
        result = greet_cmd.execute(name="Vincent", greeting="Bonjour")
        print(f"Result: {result}")

    # Test create_config command
    config_cmd = registry.get_command("create_config")
    if config_cmd:
        config_data = {
            "version": "1.0.0",
            "environment": "development",
            "features": ["logging", "metrics", "rollback"],
        }
        result = config_cmd.execute(
            filename="workflow_config.json", config_data=config_data
        )
        print(f"Config created: {result}")

    print()


def create_shell_command_examples():
    """Demonstrate shell command integration."""
    print("🖥️  Shell Command Examples")
    print("-" * 40)

    registry = get_command_registry()

    # Register shell commands
    ls_command = ShellCommand(
        name="list_files",
        command_template="ls -la {directory}",
        description="List files in directory",
    )
    registry._commands["list_files"] = ls_command

    echo_command = ShellCommand(
        name="echo_message",
        command_template="echo '{message}' > {output_file}",
        description="Echo message to file",
    )
    registry._commands["echo_message"] = echo_command

    # Test shell commands
    print("📂 Testing shell commands:")

    # List current directory
    ls_result = ls_command.execute(directory=".")
    if ls_result["success"]:
        print("✅ Directory listing successful")
        print(f"Files found: {len(ls_result['stdout'].splitlines())} lines")
    else:
        print(f"❌ Directory listing failed: {ls_result['stderr']}")

    # Echo to file
    echo_result = echo_command.execute(
        message="Hello from shell command!", output_file="shell_output.txt"
    )
    if echo_result["success"]:
        print("✅ Echo command successful")
        if Path("shell_output.txt").exists():
            content = Path("shell_output.txt").read_text().strip()
            print(f"File content: {content}")
    else:
        print(f"❌ Echo command failed: {echo_result['stderr']}")

    print()


def create_command_workflow() -> WorkflowDefinition:
    """Create workflow using command steps."""
    registry = get_command_registry()

    steps = [
        # Step 1: Greet user
        CommandStep(
            command=registry.get_command("greet_user"),
            step_id="welcome_step",
            name="Vincent",
            greeting="Welcome",
        ),
        # Step 2: Create configuration
        CommandStep(
            command=registry.get_command("create_config"),
            step_id="config_step",
            filename="workflow_settings.json",
            config_data={
                "workflow_name": "Command Demo",
                "author": "Vincent",
                "timestamp": time.time(),
                "settings": {
                    "verbose": True,
                    "rollback_enabled": True,
                    "max_retries": 3,
                },
            },
        ),
        # Step 3: Process sample data
        CommandStep(
            command=registry.get_command("process_data"),
            step_id="processing_step",
            data=[1, 2, 3, 4, 5, 10, 20, 30],
            processing_time=0.2,
        ),
    ]

    return WorkflowDefinition(
        workflow_id="command_demo",
        name="Command System Demonstration",
        description="Shows integration of various command types in workflows",
        version="1.0.0",
        author="Vincent",
        steps=steps,
    )


def main():
    """Run command system demonstration."""
    print("🎯 Command System Demonstration")
    print("=" * 40)

    # Demonstrate command registry
    demonstrate_command_registry()

    # Demonstrate shell commands
    create_shell_command_examples()

    # Create and execute command-based workflow
    print("🔄 Command-Based Workflow Execution")
    print("-" * 40)

    engine = WorkflowEngine()
    workflow = create_command_workflow()
    context = WorkflowContext(working_directory=Path.cwd() / "command_demo_output")
    context.working_directory.mkdir(exist_ok=True)

    print(f"📋 Executing: {workflow.name}")
    result = engine.execute_workflow(workflow, context)

    # Display results
    print("\n📊 Command Workflow Results:")
    print(f"Status: {result.status.value}")
    print(f"Success Rate: {result.success_rate:.2%}")
    print(f"Total Duration: {result.total_duration:.3f}s")

    # Show command execution details
    print("\n🔍 Command Execution Details:")
    for step_result in result.step_results:
        status_emoji = "✅" if step_result.success else "❌"
        duration = step_result.metrics.duration_seconds
        print(f"  {status_emoji} {step_result.step_id}: {duration:.3f}s")

    # Show created artifacts
    if result.artifacts_produced:
        print("\n📄 Generated Files:")
        for artifact in result.artifacts_produced:
            if artifact.exists() and artifact.suffix == ".json":
                print(f"  📄 {artifact.name} ({artifact.stat().st_size} bytes)")

    print("\n✨ Command system demonstration completed!")


if __name__ == "__main__":
    main()
