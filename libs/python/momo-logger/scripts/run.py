#!/usr/bin/env python3
"""
Script Runner for Momo Logger Module

This script provides a convenient way to discover and run example scripts
in the momo-logger module. It follows the same pattern as the momo-kb module.

Usage:
    pdm run script basic_usage          # Run basic usage example
    pdm run script backend_demonstration # Run backend demonstration
    pdm run list-scripts                # List all available scripts
"""

import os
import sys
import argparse
import importlib.util
from pathlib import Path


def list_scripts():
    """List all available scripts in the scripts directory."""
    scripts_dir = Path(__file__).parent
    scripts = []

    for file in scripts_dir.glob("*.py"):
        if file.name != "run.py":
            # Get the description from the docstring
            description = get_script_description(file)
            scripts.append((file.stem, description))

    if scripts:
        print("Available scripts:")
        print("-" * 50)
        for name, description in sorted(scripts):
            print(f"  {name:<20} {description}")
        print("-" * 50)
        print(f"\nRun with: pdm run script <script_name>")
    else:
        print("No scripts found in the scripts directory.")


def get_script_description(script_path):
    """Extract description from script docstring."""
    try:
        with open(script_path, "r") as f:
            # Read first few lines to find docstring
            content = f.read(1000)  # Read first 1000 chars

            # Look for module docstring (first triple-quoted string)
            if '"""' in content:
                start = content.find('"""') + 3
                end = content.find('"""', start)
                if end != -1:
                    docstring = content[start:end].strip()
                    # Return first line as description
                    lines = docstring.split("\n")
                    return lines[0] if lines else "No description"

            return "No description"
    except Exception:
        return "No description"


def run_script(script_name):
    """Run a specific script by name."""
    scripts_dir = Path(__file__).parent
    script_path = scripts_dir / f"{script_name}.py"

    if not script_path.exists():
        print(f"Error: Script '{script_name}' not found.")
        print(f"Available scripts:")
        list_scripts()
        sys.exit(1)

    # Import and run the script
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # If the script has a main function, call it
    if hasattr(module, "main"):
        import asyncio

        if asyncio.iscoroutinefunction(module.main):
            asyncio.run(module.main())
        else:
            module.main()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Momo Logger Script Runner")
    parser.add_argument("script", nargs="?", help="Script to run")
    parser.add_argument(
        "--list", action="store_true", help="List all available scripts"
    )

    args = parser.parse_args()

    if args.list:
        list_scripts()
    elif args.script:
        run_script(args.script)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
