#!/usr/bin/env python3
"""
Script runner utility for the scripts/ folder.
Add new scripts to pyproject.toml [tool.pdm.scripts] section.
"""

import asyncio
import os
import sys
from pathlib import Path
from momo_logger import get_logger


async def list_available_scripts():
    """List all available scripts in the scripts/ folder."""
    logger = get_logger("momo.kb.scripts.run")
    scripts_dir = Path("scripts")
    if not scripts_dir.exists():
        await logger.ai_user("No scripts/ directory found", user_facing=True)
        return

    scripts = [f.stem for f in scripts_dir.glob("*.py")]
    if scripts:
        await logger.ai_user("Available scripts:", user_facing=True)
        for script in sorted(scripts):
            await logger.ai_user(f"  pdm run {script}", user_facing=True)
    else:
        await logger.ai_user("No Python scripts found in scripts/", user_facing=True)


async def main():
    logger = get_logger("momo.kb.scripts.run")
    if len(sys.argv) > 1 and sys.argv[1] in ["--list", "-l"]:
        await list_available_scripts()
    else:
        await logger.ai_user("Usage: python scripts/run.py --list", user_facing=True)
        await logger.ai_user("Or use: pdm run <script_name>", user_facing=True)


if __name__ == "__main__":
    asyncio.run(main())
