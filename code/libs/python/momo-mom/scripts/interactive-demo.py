#!/usr/bin/env python3
"""
Interactive Agent System Demo - Shows how Mom handles interactive commands.
"""

import subprocess
import sys
from pathlib import Path


def run_demo(description: str, command: str):
    """Run a demo command and show the results."""
    print(f"\n{'=' * 60}")
    print(f"🤖 {description}")
    print(f"Command: {command}")
    print(f"{'=' * 60}")

    mom_cmd = ["uv", "run", "python", "-m", "momo_mom.cli", "run"] + command.split()

    try:
        result = subprocess.run(
            mom_cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run interactive system demonstration."""
    print("🤖 Mom Interactive Agent System Demo")
    print("Showcasing multi-agent handling of interactive commands")

    # Demo 1: Simple command (no interaction needed)
    run_demo("Simple Command - No Interaction", "echo 'Hello from Mom!'")

    # Demo 2: Show agent statistics
    print(f"\n{'=' * 60}")
    print("📊 Agent System Status")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-c",
                """
from momo_mom.interactive import MomInteractiveSystem
config = {'interactive': {'enable_executing_agent': True}}
system = MomInteractiveSystem(config)
print(f'Total agents registered: {len(system.registry.get_all_agents())}')
print('\\nAgent details:')
for agent in system.registry.get_all_agents():
    print(f'  • {agent.name} (priority: {agent.priority})')
            """,
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")

    # Demo 3: Test specialized agent detection
    print(f"\n{'=' * 60}")
    print("🎯 Specialized Agent Detection")
    print(f"{'=' * 60}")

    test_commands = [
        ("npm init", "NpmAgent should handle this"),
        ("git commit", "GitAgent should handle this"),
        ("docker run", "DockerAgent should handle this"),
        ("pip install", "PythonAgent should handle this"),
        ("unknown command", "GeneralAgent should handle this"),
    ]

    for cmd, expected in test_commands:
        try:
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "-c",
                    f"""
from momo_mom.interactive import MomInteractiveSystem
from momo_mom.agents.base import ExecutionContext

config = {{'interactive': {{'enable_executing_agent': True}}}}
system = MomInteractiveSystem(config)
context = system.create_execution_context('test')
agent = system.registry.find_agent('{cmd}', context)
print(f'{cmd} -> {{agent.name if agent else "No agent"}}')
                """,
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )

            print(f"  {result.stdout.strip()}")
        except Exception as e:
            print(f"  Error testing {cmd}: {e}")

    print(f"\n{'=' * 60}")
    print("✅ Interactive Demo Complete!")
    print(f"{'=' * 60}")
    print("\nKey Features Demonstrated:")
    print("• 🤖 Multi-agent system with 11 registered agents")
    print("• 🎯 Specialized agents for npm, git, docker, python")
    print("• 🔄 ExecutingAgent for routing back to main agent")
    print("• 🛡️ GeneralAgent as intelligent fallback")
    print("• 📊 Agent priority system and statistics")
    print("• 🔌 Pluggable architecture for custom agents")

    print("\nAgent Hierarchy:")
    print("  1. ExecutingAgent (priority: 100) - Routes to main agent")
    print("  2. Specialized Agents (priority: 70) - Domain experts")
    print("  3. GeneralAgent (priority: 10) - Smart fallback")

    print("\nNext Steps:")
    print("  • Set executing agent callback for real interactive handling")
    print("  • Test with actual interactive commands (npm init, git commit)")
    print("  • Add custom agents via plugin system")
    print("  • Configure user preferences for better responses")


if __name__ == "__main__":
    main()
