#!/usr/bin/env python3
"""
Global mo command for MomoAI monorepo.

This script provides universal access to the mo command from anywhere in the workspace.
"""

import os
import sys
from pathlib import Path

def find_workspace_root():
    """Find the workspace root directory."""
    current = Path.cwd()
    markers = ['nx.json', 'CLAUDE.md', '.git', 'package.json']
    
    while current != current.parent:
        if any((current / marker).exists() for marker in markers):
            return current
        current = current.parent
    
    # Fallback: look for mo script location
    return Path(__file__).parent.resolve()

def main():
    """Main entry point for global mo command."""
    # Find workspace root
    workspace_root = find_workspace_root()
    
    # Add momo-cmd to Python path
    momo_cmd_path = workspace_root / "code" / "libs" / "python" / "momo-cmd"
    
    if not momo_cmd_path.exists():
        print(f"❌ momo-cmd not found at: {momo_cmd_path}")
        print("Make sure you're in the MomoAI workspace and momo-cmd is installed")
        sys.exit(1)
    
    # Add to Python path
    sys.path.insert(0, str(momo_cmd_path))
    
    # Change to workspace root for consistent context
    os.chdir(workspace_root)
    
    try:
        # Import and run mo command
        from momo_cmd import mo
        
        # Pass command line arguments (excluding script name)
        mo(sys.argv[1:], standalone_mode=False)
        
    except ImportError as e:
        print(f"❌ Failed to import momo-cmd: {e}")
        print("Try running: cd code/libs/python/momo-cmd && uv sync")
        sys.exit(1)
    except Exception as e:
        print(f"❌ mo command failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()