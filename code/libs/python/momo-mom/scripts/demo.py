#!/usr/bin/env python3
"""
Demo script showcasing Mom's shell-first command mapping capabilities.
This script demonstrates how Mom can execute complex shell commands with fallbacks.
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Run demonstration of Mom capabilities."""
    print("🚀 Mom Command Mapping System Demo")
    print("=" * 50)

    # Test basic shell execution
    print("\n1. Testing shell command execution:")
    print("   Command: echo 'Hello from Mom!'")
    result = subprocess.run(["echo", "Hello from Mom!"], capture_output=True, text=True)
    print(f"   Output: {result.stdout.strip()}")

    # Test parameter substitution simulation
    print("\n2. Testing parameter substitution:")
    template = "echo 'Building project: {name} with args: {args}'"
    params = {"name": "momo-mom", "args": "--verbose"}

    # Simple substitution demo
    command = template.format(**params)
    print(f"   Template: {template}")
    print(f"   Resolved: {command}")

    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(f"   Output: {result.stdout.strip()}")

    # Test script discovery
    print("\n3. Testing script discovery:")
    scripts_dir = Path(__file__).parent
    print(f"   Scripts directory: {scripts_dir}")

    for script in scripts_dir.glob("*"):
        if script.is_file() and script != Path(__file__):
            print(f"   Found script: {script.name}")

    # Test language detection
    print("\n4. Testing language entry points:")
    test_files = [
        ("test.py", "Python"),
        ("test.sh", "Bash"),
        ("test.js", "Node.js"),
        ("test.ts", "TypeScript"),
    ]

    for filename, language in test_files:
        print(f"   {filename} -> {language} entry point")

    print("\n✅ Demo completed successfully!")
    print("\nTry these commands:")
    print("  mom run echo 'Hello World'")
    print("  mom list-scripts")
    print("  mom config --show")
    print("  mom script demo")


if __name__ == "__main__":
    main()
