"""Test module for Mom command mapping system."""

import pytest
from pathlib import Path
import tempfile
import os

from momo_mom import ConfigManager, CommandExecutor, ScriptDiscovery


def test_config_manager_default():
    """Test configuration manager with default config."""
    config_manager = ConfigManager()
    assert config_manager.config is not None
    assert 'commands' in config_manager.config
    assert 'script_paths' in config_manager.config


def test_config_manager_with_file():
    """Test configuration manager with custom config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
command_name: "test"
commands:
  test:
    pattern: "echo {target}"
script_paths:
  - "test_scripts"
""")
        config_path = f.name
    
    try:
        config_manager = ConfigManager(config_path)
        assert config_manager.config['command_name'] == 'test'
        assert 'test' in config_manager.config['commands']
    finally:
        os.unlink(config_path)


def test_command_executor_shell_execution():
    """Test command executor with shell commands."""
    config = {
        'commands': {
            'test': {
                'pattern': 'echo "Hello {target}"'
            }
        },
        'execution': {
            'retry_count': 1,
            'timeout': 30
        },
        'recovery': {}
    }
    
    executor = CommandExecutor(config, verbose=False)
    
    # Test parameter substitution
    template = "echo 'Hello {target}'"
    context = {'target': 'world'}
    result = executor._substitute_parameters(template, context)
    assert result == "echo 'Hello world'"


def test_script_discovery():
    """Test script discovery functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        scripts_dir = temp_path / "scripts"
        scripts_dir.mkdir()
        
        # Create test scripts
        (scripts_dir / "test.py").write_text("#!/usr/bin/env python3\nprint('test')")
        (scripts_dir / "build.sh").write_text("#!/bin/bash\necho 'build'")
        
        config = {
            'script_paths': [str(scripts_dir)]
        }
        
        discovery = ScriptDiscovery(config)
        discovery.search_paths = [scripts_dir]  # Override for test
        
        # Test finding scripts
        python_script = discovery.find_script("test")
        assert python_script is not None
        assert python_script.name == "test.py"
        
        bash_script = discovery.find_script("build")
        assert bash_script is not None
        assert bash_script.name == "build.sh"
        
        # Test listing scripts
        scripts = discovery.list_available_scripts()
        assert len(scripts) > 0


def test_language_entry_points():
    """Test language entry point detection."""
    from momo_mom.executor import PythonEntryPoint, BashEntryPoint, NodeEntryPoint
    
    python_ep = PythonEntryPoint()
    assert python_ep.can_handle(Path("test.py"))
    assert not python_ep.can_handle(Path("test.sh"))
    
    bash_ep = BashEntryPoint()
    assert bash_ep.can_handle(Path("test.sh"))
    assert not bash_ep.can_handle(Path("test.py"))
    
    node_ep = NodeEntryPoint()
    assert node_ep.can_handle(Path("test.js"))
    assert node_ep.can_handle(Path("test.mjs"))
    assert not node_ep.can_handle(Path("test.py"))
