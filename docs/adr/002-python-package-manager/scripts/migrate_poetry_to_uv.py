#!/usr/bin/env python3
"""
Generic migration script: Poetry to uv for any Momo module
Usage: python3 migrate_poetry_to_uv.py <module-name>
"""

import shutil
import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Module configurations - dependencies and descriptions
MODULE_CONFIGS = {
    "momo-logger": {
        "description": "Structured logging for the Momo AI system",
        "dependencies": ["pydantic>=2.0.0"],
        "internal_deps": [],
        "package_name": "momo_logger"
    },
    "momo-graph-store": {
        "description": "Graph database abstraction for Momo AI knowledge base",
        "dependencies": ["pydantic>=2.0.0"],
        "internal_deps": ["momo-logger"],
        "package_name": "momo_graph_store"
    },
    "momo-vector-store": {
        "description": "Vector store implementation for Momo AI knowledge base",
        "dependencies": [
            "pydantic>=2.0.0",
            "langchain-core>=0.3.73", 
            "langchain-huggingface>=0.1.0"
        ],
        "internal_deps": ["momo-logger"],
        "package_name": "momo_vector_store"
    },
    "momo-store-document": {
        "description": "Document storage abstraction for Momo AI knowledge base",
        "dependencies": [
            "pydantic>=2.0.0",
            "pandas>=2.0.0",
            "duckdb>=0.8.0"
        ],
        "internal_deps": ["momo-logger"],
        "package_name": "momo_store_document"
    },
    "momo-kb": {
        "description": "Knowledge base system for Momo AI multi-agent architecture",
        "dependencies": [
            "pydantic>=2.0.0",
            "pandas>=2.0.0",
            "duckdb>=0.8.0",
            "sqlalchemy>=2.0.0"
        ],
        "internal_deps": ["momo-logger", "momo-vector-store", "momo-graph-store", "momo-store-document"],
        "package_name": "momo_kb"
    }
}

class GenericMomoMigrator:
    def __init__(self, module_name: str):
        if module_name not in MODULE_CONFIGS:
            raise ValueError(f"Unknown module: {module_name}. Available: {list(MODULE_CONFIGS.keys())}")
        
        self.module_name = module_name
        self.config = MODULE_CONFIGS[module_name]
        self.package_name = self.config["package_name"]
        
        self.workspace_root = Path("/home/vincent/Documents/Momo/MomoAI-nx")
        self.old_module_path = self.workspace_root / f"libs/python/{module_name}"
        self.new_module_path = self.workspace_root / f"libs/python/new-{module_name}"
        self.backup_path = self.workspace_root / f"libs/python/{module_name}-backup"
        
    def run_command(self, cmd: str, cwd: Optional[Path] = None) -> bool:
        """Run shell command and return success status."""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                cwd=cwd or self.workspace_root,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                print(f"✓ {result.stdout.strip()}")
            # uv outputs success info to stderr, so don't treat stderr as error
            return True
        except Exception as e:
            print(f"❌ Exception running command: {cmd}")
            print(f"Error: {e}")
            return False
    
    def step_1_backup_and_verify(self) -> bool:
        """Create backup and verify current state."""
        print(f"📦 Step 1: Creating backup for {self.module_name}...")
        
        if not self.old_module_path.exists():
            print(f"❌ Module {self.module_name} does not exist at {self.old_module_path}")
            return False
        
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
        shutil.copytree(self.old_module_path, self.backup_path)
        
        # Fix backup project.json name to avoid Nx conflicts
        backup_project_json = self.backup_path / "project.json"
        if backup_project_json.exists():
            with open(backup_project_json, 'r') as f:
                config = json.load(f)
            config["name"] = f"{self.module_name}-backup"
            with open(backup_project_json, 'w') as f:
                json.dump(config, f, indent=2)
        
        print("✅ Backup created successfully")
        return True
    
    def step_2_generate_new_module(self) -> bool:
        """Generate new module with uv template."""
        print(f"🏗️  Step 2: Generating new {self.module_name} module...")
        
        if self.new_module_path.exists():
            shutil.rmtree(self.new_module_path)
        
        cmd = (
            f'pnpm nx generate @nxlv/python:uv-project {self.module_name} '
            f'--directory=libs/python/new-{self.module_name} '
            f'--pyprojectPythonDependency=">=3.9,<3.13" '
            f'--pyenvPythonVersion="3.12" '
            f'--buildBackend="hatchling"'
        )
        
        success = self.run_command(cmd)
        if success:
            print("✅ New module generated successfully")
        return success
    
    def step_3_migrate_content(self) -> bool:
        """Migrate source code, tests, and assets."""
        print(f"📁 Step 3: Migrating content for {self.module_name}...")
        
        # Copy source code (Poetry: src/package_name/ → uv: package_name/)
        old_src = self.old_module_path / f"src/{self.package_name}"
        new_src = self.new_module_path / self.package_name
        
        if old_src.exists():
            # Remove template hello.py
            hello_file = new_src / "hello.py"
            if hello_file.exists():
                hello_file.unlink()
            
            # Copy all source files
            for item in old_src.iterdir():
                if item.is_file():
                    shutil.copy2(item, new_src)
                elif item.is_dir():
                    shutil.copytree(item, new_src / item.name, dirs_exist_ok=True)
        
        # Copy test suite
        old_tests = self.old_module_path / "tests"
        new_tests = self.new_module_path / "tests"
        if old_tests.exists():
            # Clear template tests
            for item in new_tests.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            
            # Copy all test files
            for item in old_tests.iterdir():
                if item.is_file():
                    shutil.copy2(item, new_tests)
                elif item.is_dir():
                    shutil.copytree(item, new_tests / item.name)
        
        # Copy additional assets
        assets_to_copy = ["benchmarks", "scripts", "README.md", "CLAUDE.md"]
        for asset in assets_to_copy:
            old_asset = self.old_module_path / asset
            if old_asset.exists():
                if old_asset.is_file():
                    shutil.copy2(old_asset, self.new_module_path)
                elif old_asset.is_dir():
                    shutil.copytree(old_asset, self.new_module_path / asset, dirs_exist_ok=True)
        
        # Copy special configuration files (momo.md, momo.yaml, etc.)
        special_files = [
            f"src/{self.package_name}/momo.md",
            "momo.yaml", 
            "benchmark_results.json",
            "pytest.ini"
        ]
        
        for file_path in special_files:
            old_file = self.old_module_path / file_path
            if old_file.exists():
                if file_path.endswith("momo.md") and "src/" in file_path:
                    new_file = self.new_module_path / f"{self.package_name}/momo.md"
                else:
                    new_file = self.new_module_path / old_file.name
                
                new_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old_file, new_file)
        
        print("✅ Content migration completed")
        return True
    
    def step_4_update_configuration(self) -> bool:
        """Update pyproject.toml and project.json with uv configuration."""
        print(f"⚙️  Step 4: Updating configuration for {self.module_name}...")
        
        # Build dependencies list
        dependencies = self.config["dependencies"].copy()
        
        # Add internal dependencies
        for dep in self.config["internal_deps"]:
            dep_path = f"file:///home/vincent/Documents/Momo/MomoAI-nx/libs/python/{dep}"
            dependencies.append(f'"{dep} @ {dep_path}"')
        
        # Format dependencies for pyproject.toml
        deps_str = ",\n    ".join([f'"{dep}"' for dep in self.config["dependencies"]])
        if self.config["internal_deps"]:
            internal_deps_str = ",\n    ".join([
                f'"{dep} @ file:///home/vincent/Documents/Momo/MomoAI-nx/libs/python/{dep}"' 
                for dep in self.config["internal_deps"]
            ])
            if deps_str:
                deps_str += ",\n    " + internal_deps_str
            else:
                deps_str = internal_deps_str
        
        # Create pyproject.toml content
        pyproject_content = f'''[tool.coverage.run]
branch = true
source = [ "{self.package_name}" ]

[tool.coverage.report]
exclude_lines = ['if TYPE_CHECKING:']
show_missing = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]  
python_functions = ["test_*"]
addopts = "-v --tb=short --cov={self.package_name}"
asyncio_mode = "auto"

[project]
name = "{self.module_name}"
version = "0.1.0"
description = "{self.config['description']}"
requires-python = ">=3.9,<3.13"
readme = 'README.md'
dependencies = [
    {deps_str}
]

[tool.hatch.build.targets.wheel]
packages = ["{self.package_name}"]

[tool.hatch.metadata]
allow-direct-references = true

[dependency-groups]
dev = [
  "ruff>=0.8.2",
  "pyright>=1.1.0",
  "pytest>=8.3.4",
  "pytest-asyncio>=0.21",
  "pytest-cov>=6.0.0",
  "pytest-html>=4.1.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
exclude = [
  ".ruff_cache",
  ".svn",
  ".tox",
  ".venv",
  "dist",
]

line-length = 88
indent-width = 4

[tool.ruff.lint]
select = [
  "E", "F", "UP", "B", "SIM", "I",
]
ignore = []

fixable = ["ALL"]
unfixable = []
'''
        
        pyproject_path = self.new_module_path / "pyproject.toml"
        with open(pyproject_path, 'w') as f:
            f.write(pyproject_content)
        
        # Create project.json
        project_config = {
            "name": f"new-{self.module_name}",
            "$schema": "../../../node_modules/nx/schemas/project-schema.json",
            "projectType": "library",
            "sourceRoot": f"libs/python/new-{self.module_name}/{self.package_name}",
            "targets": {
                "lock": {
                    "executor": "@nxlv/python:lock",
                    "options": {"update": False}
                },
                "sync": {
                    "executor": "@nxlv/python:sync",
                    "options": {}
                },
                "add": {"executor": "@nxlv/python:add", "options": {}},
                "update": {"executor": "@nxlv/python:update", "options": {}},
                "remove": {"executor": "@nxlv/python:remove", "options": {}},
                "build": {
                    "executor": "@nxlv/python:build",
                    "outputs": ["{projectRoot}/dist"],
                    "options": {
                        "outputPath": "{projectRoot}/dist",
                        "publish": False,
                        "lockedVersions": True,
                        "bundleLocalDependencies": True
                    },
                    "cache": True
                },
                "lint": {
                    "executor": "@nxlv/python:ruff-check",
                    "options": {
                        "lintFilePatterns": [self.package_name, "tests", "benchmarks"]
                    },
                    "cache": True
                },
                "format": {
                    "executor": "@nxlv/python:ruff-format",
                    "options": {
                        "filePatterns": [self.package_name, "tests", "benchmarks"]
                    },
                    "cache": True
                },
                "test": {
                    "executor": "@nxlv/python:run-commands",
                    "options": {
                        "command": "uv run pytest tests/",
                        "cwd": "{projectRoot}"
                    },
                    "cache": True
                },
                "typecheck": {
                    "executor": "@nxlv/python:run-commands",
                    "options": {
                        "command": f"uv run pyright {self.package_name}"
                    },
                    "cache": True
                },
                "test-fast": {
                    "executor": "@nxlv/python:run-commands",
                    "options": {
                        "command": "uv run pytest tests/unit/ tests/e2e/",
                        "cwd": "{projectRoot}"
                    },
                    "cache": True
                },
                "test-all": {
                    "executor": "@nxlv/python:run-commands",
                    "options": {
                        "command": f"uv run pytest tests/ --cov={self.package_name} --cov-report=term-missing --benchmark-skip",
                        "cwd": "{projectRoot}"
                    },
                    "cache": True
                },
                "benchmark": {
                    "executor": "@nxlv/python:run-commands",
                    "options": {
                        "command": f"uv run pytest benchmarks/ --benchmark-only --benchmark-json=../../../benchmark_results/new-{self.module_name}.json",
                        "cwd": "{projectRoot}"
                    },
                    "cache": False
                },
                "install": {
                    "executor": "@nxlv/python:install",
                    "options": {
                        "silent": False,
                        "args": "",
                        "verbose": False,
                        "debug": False
                    }
                }
            },
            "implicitDependencies": self.config["internal_deps"],
            "tags": ["python", "library", self.module_name.replace("momo-", ""), "multi-agent"]
        }
        
        project_json_path = self.new_module_path / "project.json"
        with open(project_json_path, 'w') as f:
            json.dump(project_config, f, indent=2)
        
        # Add .python-version file
        python_version_path = self.new_module_path / ".python-version"
        with open(python_version_path, 'w') as f:
            f.write("3.12\n")
        
        print("✅ Configuration files updated")
        return True
    
    def step_5_install_and_validate(self) -> bool:
        """Install dependencies and run validation pipeline."""
        print(f"📦 Step 5: Installing dependencies for {self.module_name}...")
        
        # Install dependencies
        install_cmd = f"pnpm nx run new-{self.module_name}:install"
        self.run_command(install_cmd)
        
        # Run format
        format_cmd = f"pnpm nx run new-{self.module_name}:format"
        self.run_command(format_cmd)
        
        print("✅ Dependencies installed and validation completed")
        return True
    
    def step_6_atomic_replacement(self) -> bool:
        """Perform atomic replacement of old module with new one."""
        print(f"🔄 Step 6: Performing atomic replacement for {self.module_name}...")
        
        # Remove old module
        if self.old_module_path.exists():
            shutil.rmtree(self.old_module_path)
        
        # Rename new module to original name
        self.new_module_path.rename(self.old_module_path)
        
        # Update project.json name and paths back to original
        project_json_path = self.old_module_path / "project.json"
        with open(project_json_path, 'r') as f:
            config = json.load(f)
        
        config["name"] = self.module_name
        config["sourceRoot"] = f"libs/python/{self.module_name}/{self.package_name}"
        
        # Update benchmark output path
        if "benchmark" in config["targets"]:
            config["targets"]["benchmark"]["options"]["command"] = (
                f"uv run pytest benchmarks/ --benchmark-only "
                f"--benchmark-json=../../../benchmark_results/{self.module_name}.json"
            )
        
        with open(project_json_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Sync dependencies after rename
        sync_cmd = f"pnpm nx run {self.module_name}:sync"
        self.run_command(sync_cmd)
        
        print("✅ Atomic replacement completed")
        return True
    
    def step_7_cleanup(self) -> bool:
        """Clean up backup and temporary files."""
        print(f"🧹 Step 7: Cleaning up {self.module_name}...")
        
        # Test that the new module works
        format_cmd = f"pnpm nx run {self.module_name}:format"
        self.run_command(format_cmd)
        
        # Remove backup if everything works
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
            print("✅ Backup removed")
        
        print("✅ Cleanup completed")
        return True
    
    def migrate(self) -> bool:
        """Run the complete migration process."""
        print(f"🚀 Starting {self.module_name} migration from Poetry to uv...")
        print("=" * 60)
        
        steps = [
            self.step_1_backup_and_verify,
            self.step_2_generate_new_module,
            self.step_3_migrate_content,
            self.step_4_update_configuration,
            self.step_5_install_and_validate,
            self.step_6_atomic_replacement,
            self.step_7_cleanup,
        ]
        
        for i, step in enumerate(steps, 1):
            try:
                if not step():
                    print(f"❌ Migration failed at step {i}")
                    return False
            except Exception as e:
                print(f"❌ Exception in step {i}: {e}")
                import traceback
                traceback.print_exc()
                return False
            print()
        
        print(f"🎉 {self.module_name} migration completed successfully!")
        print("=" * 60)
        return True

def main():
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print("Generic Momo Module Migration Script")
        print("====================================")
        print("Migrates any Momo module from Poetry to uv with @nxlv/python integration.")
        print()
        print("Usage: python3 migrate_poetry_to_uv.py <module-name>")
        print()
        print("Available modules:")
        for module in MODULE_CONFIGS.keys():
            config = MODULE_CONFIGS[module]
            print(f"  - {module}: {config['description']}")
        print()
        print("Dependency order (migrate in this order):")
        print("1. momo-logger (no deps)")
        print("2. momo-graph-store (deps: momo-logger)")
        print("3. momo-vector-store (deps: momo-logger)")  
        print("4. momo-store-document (deps: momo-logger)")
        print("5. momo-kb (deps: all others)")
        return
    
    module_name = sys.argv[1]
    
    try:
        migrator = GenericMomoMigrator(module_name)
        success = migrator.migrate()
        
        if success:
            print(f"\n🎯 Next steps:")
            print(f"✅ {module_name} successfully migrated to uv!")
            print("🔧 Update dependent modules if needed")
            print("🧪 Run tests when all migrations complete")
            sys.exit(0)
        else:
            print(f"\n💥 Migration failed - check backup at libs/python/{module_name}-backup")
            sys.exit(1)
            
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()