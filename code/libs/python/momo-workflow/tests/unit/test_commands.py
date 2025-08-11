"""
Unit tests for command system functionality.
"""

import pytest
from pathlib import Path

from momo_workflow.commands import (
    CommandRegistry,
    FunctionCommand,
    ShellCommand,
    register_command,
    get_command_registry,
)


class TestCommandRegistry:
    """Test cases for CommandRegistry."""
    
    def test_register_and_get_function_command(self):
        """Test registering and retrieving function commands."""
        # Arrange
        registry = CommandRegistry()
        
        def test_function(x: int, y: int) -> int:
            return x + y
        
        # Act
        registry.register_function("add_numbers", test_function, "Add two numbers")
        command = registry.get_command("add_numbers")
        
        # Assert
        assert command is not None
        assert command.name == "add_numbers"
        assert "Add two numbers" in command.description
        
        # Test execution
        result = command.execute(x=5, y=3)
        assert result["success"] is True
        assert result["result"] == 8
    
    def test_command_not_found(self):
        """Test behavior when command is not found."""
        # Arrange
        registry = CommandRegistry()
        
        # Act
        command = registry.get_command("nonexistent")
        
        # Assert
        assert command is None
    
    def test_list_commands(self):
        """Test listing all registered commands."""
        # Arrange
        registry = CommandRegistry()
        
        def func1():
            return "result1"
        
        def func2():
            return "result2"
        
        # Act
        registry.register_function("command1", func1)
        registry.register_function("command2", func2)
        commands = registry.list_commands()
        
        # Assert
        assert "command1" in commands
        assert "command2" in commands
        assert len(commands) >= 2


class TestFunctionCommand:
    """Test cases for FunctionCommand."""
    
    def test_successful_execution(self):
        """Test successful function command execution."""
        # Arrange
        def multiply(x: int, y: int) -> int:
            return x * y
        
        command = FunctionCommand("multiply", multiply, "Multiply two numbers")
        
        # Act
        result = command.execute(x=4, y=7)
        
        # Assert
        assert result["success"] is True
        assert result["result"] == 28
    
    def test_execution_with_exception(self):
        """Test function command execution with exception."""
        # Arrange
        def divide(x: int, y: int) -> int:
            return x / y
        
        command = FunctionCommand("divide", divide, "Divide two numbers")
        
        # Act
        result = command.execute(x=10, y=0)  # Division by zero
        
        # Assert
        assert result["success"] is False
        assert "error" in result
    
    def test_argument_validation(self):
        """Test function command argument validation."""
        # Arrange
        def add_with_types(x: int, y: int) -> int:
            return x + y
        
        command = FunctionCommand("add_typed", add_with_types)
        
        # Act & Assert
        assert command.validate_args(x=1, y=2) is True
        assert command.validate_args(x=1) is False  # Missing y
    
    def test_description_fallback(self):
        """Test description fallback to docstring."""
        # Arrange
        def documented_function(x: int) -> int:
            """This function doubles a number."""
            return x * 2
        
        command = FunctionCommand("double", documented_function)
        
        # Act & Assert
        assert "This function doubles a number." in command.description


class TestShellCommand:
    """Test cases for ShellCommand."""
    
    def test_successful_shell_execution(self):
        """Test successful shell command execution."""
        # Arrange
        command = ShellCommand("echo_test", "echo 'Hello, {name}!'", "Echo greeting")
        
        # Act
        result = command.execute(name="World")
        
        # Assert
        assert result["success"] is True
        assert "Hello, World!" in result["stdout"]
        assert result["returncode"] == 0
    
    def test_failed_shell_execution(self):
        """Test failed shell command execution."""
        # Arrange
        command = ShellCommand("fail_test", "exit 1", "Command that fails")
        
        # Act
        result = command.execute()
        
        # Assert
        assert result["success"] is False
        assert result["returncode"] == 1
    
    def test_shell_command_validation(self):
        """Test shell command argument validation."""
        # Arrange
        command = ShellCommand("template_test", "echo '{message}'", "Echo message")
        
        # Act & Assert
        assert command.validate_args(message="test") is True
        assert command.validate_args() is False  # Missing message
    
    def test_shell_command_timeout(self):
        """Test shell command timeout handling."""
        # Arrange - command that sleeps longer than timeout
        command = ShellCommand("sleep_test", "sleep 2", "Sleep command")
        
        # Act
        result = command.execute(timeout=0.1)  # Very short timeout
        
        # Assert
        assert result["success"] is False
        assert "timed out" in result["error"]


class TestCommandRegistration:
    """Test cases for command registration decorator."""
    
    def test_register_command_decorator(self):
        """Test @register_command decorator functionality."""
        # Arrange & Act
        @register_command("decorated_command", "Test decorated command")
        def test_decorated_function(value: str) -> str:
            return f"Processed: {value}"
        
        # Get from global registry
        registry = get_command_registry()
        command = registry.get_command("decorated_command")
        
        # Assert
        assert command is not None
        assert command.name == "decorated_command"
        
        result = command.execute(value="test_input")
        assert result["success"] is True
        assert result["result"] == "Processed: test_input"
    
    def test_built_in_commands_available(self):
        """Test that built-in commands are available."""
        # Arrange
        registry = get_command_registry()
        
        # Act & Assert
        commands = registry.list_commands()
        
        # Check some built-in commands are available
        assert "create_directory" in commands
        assert "create_file" in commands
        assert "copy_file" in commands
        assert "delete_path" in commands