#!/usr/bin/env python3
"""
AI Output Demo - Showcases Mom's intelligent output formatting capabilities.
Demonstrates structured output, duplicate filtering, head/tail truncation, and format options.
"""

import subprocess
import sys
from pathlib import Path


def run_demo_command(description: str, command: str, format_type: str = "structured"):
    """Run a demo command and show the output."""
    print(f"\n{'='*60}")
    print(f"🎯 {description}")
    print(f"Command: {command}")
    print(f"Format: {format_type}")
    print(f"{'='*60}")
    
    # Build mom command
    mom_cmd = ["uv", "run", "python", "-m", "momo_mom.cli"]
    if format_type != "structured":
        mom_cmd.extend(["--output-format", format_type])
    mom_cmd.extend(["run"] + command.split())
    
    try:
        result = subprocess.run(mom_cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
    except Exception as e:
        print(f"Error running command: {e}")


def main():
    """Run comprehensive AI output demonstration."""
    print("🤖 Mom AI-Tailored Output System Demo")
    print("Showcasing intelligent formatting for AI consumption")
    
    # Demo 1: Simple command with structured output
    run_demo_command(
        "Simple Command - Structured Output",
        "echo 'Hello from Mom AI output system!'"
    )
    
    # Demo 2: JSON format
    run_demo_command(
        "JSON Format Output",
        "echo 'JSON formatted output for API consumption'",
        "json"
    )
    
    # Demo 3: Markdown format
    run_demo_command(
        "Markdown Format Output", 
        "echo 'Markdown formatted output for documentation'",
        "markdown"
    )
    
    # Demo 4: Multi-line output with head/tail truncation
    run_demo_command(
        "Multi-line Output with Truncation",
        "seq 1 25"  # Generate 25 lines
    )
    
    # Demo 5: Simulated test output
    run_demo_command(
        "Simulated Test Output",
        "echo '5 passed, 2 failed, 1 skipped in 0.5s'"
    )
    
    # Demo 6: Error output
    run_demo_command(
        "Error Output Handling",
        "ls /nonexistent/directory"
    )
    
    # Demo 7: Duplicate filtering demo
    print(f"\n{'='*60}")
    print("🔄 Duplicate Filtering Demo")
    print("Command: Repeated output lines")
    print(f"{'='*60}")
    
    # Create a command that produces duplicates
    duplicate_cmd = ["uv", "run", "python", "-m", "momo_mom.cli", "run", 
                    "bash", "-c", "for i in {1..10}; do echo 'Duplicate line'; echo 'Unique line $i'; done"]
    
    try:
        result = subprocess.run(duplicate_cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ AI Output Demo Complete!")
    print(f"{'='*60}")
    print("\nKey Features Demonstrated:")
    print("• 📊 Structured output with status indicators")
    print("• 🎯 Head/tail truncation for long output")
    print("• 🔄 Automatic duplicate filtering")
    print("• 📋 Multiple format options (structured/json/markdown)")
    print("• ❌ Intelligent error handling and formatting")
    print("• 🤖 AI-optimized information density")
    
    print("\nUsage Examples:")
    print("  mom run echo 'test'                    # Structured output")
    print("  mom --output-format json run ls        # JSON format")
    print("  mom --output-format markdown run pwd   # Markdown format")
    print("  mom --expand run long-command          # Full output")
    print("  mom --raw-output run command           # Traditional output")


if __name__ == "__main__":
    main()