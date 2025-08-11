"""
Workflow Command Executor for MomoAI

Integrates momo-mom's command execution capabilities with momo-workflow's
structured workflow system, providing intelligent fallbacks and recovery
for workflow steps.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import subprocess
import time

from .executor import CommandExecutor
from .interactive import MomInteractiveSystem


class WorkflowCommandExecutor(CommandExecutor):
    """
    Enhanced command executor specifically designed for workflow integration.
    
    Provides:
    - Workflow-aware command execution
    - Context-sensitive fallbacks
    - Interactive agent integration
    - Automatic recovery strategies
    """
    
    def __init__(self, config: Dict[str, Any], workflow_context: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.workflow_context = workflow_context or {}
        self.interactive_system = MomInteractiveSystem(config)
        self.command_history = []
        
        # Workflow-specific command mappings
        self.workflow_commands = self._setup_workflow_commands()
    
    def _setup_workflow_commands(self) -> Dict[str, Dict[str, str]]:
        """Setup workflow-specific command mappings with fallbacks"""
        return {
            "research": {
                "grep_pattern": "grep -r '{pattern}' code/libs/python/{module}",
                "find_references": "find code/libs/python -name '*.py' -exec grep -l '{pattern}' {} +",
                "list_tests": "ls code/libs/python/{module}/tests/ 2>/dev/null || echo 'No tests directory'"
            },
            "setup": {
                "install_deps": "nx run {module}:install",
                "install_fallback": "cd code/libs/python/{module} && uv sync",
                "format_code": "nx run {module}:format",
                "format_fallback": "cd code/libs/python/{module} && uv run ruff format .",
                "reset_nx": "nx reset"
            },
            "validation": {
                "format": "nx run {module}:format",
                "lint": "nx run {module}:lint", 
                "typecheck": "nx run {module}:typecheck",
                "test_fast": "nx run {module}:test-fast",
                "test_all": "nx run {module}:test-all",
                "fallback_format": "cd code/libs/python/{module} && uv run ruff format .",
                "fallback_lint": "cd code/libs/python/{module} && uv run ruff check .",
                "fallback_test": "cd code/libs/python/{module} && uv run pytest"
            },
            "integration": {
                "test_affected": "nx affected -t test-fast",
                "test_module_deps": "nx run-many -t test-fast --projects={module},momo-kb",
                "benchmark": "nx run {module}:benchmark"
            }
        }
    
    def execute_workflow_command(self, command: str, step_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute command with workflow-specific context and enhanced error handling.
        
        Args:
            command: Command to execute
            step_context: Context from the workflow step
            
        Returns:
            Dict with execution results including success, output, error, and metadata
        """
        
        # Create rich execution context
        execution_context = self.interactive_system.create_execution_context(
            current_task=step_context.get('step_description', ''),
            command_history=self.command_history,
            session_metadata={
                'workflow_id': step_context.get('workflow_id'),
                'step_id': step_context.get('step_id'),
                'module': step_context.get('module'),
                'feature': step_context.get('feature'),
                'step_type': step_context.get('step_type')
            }
        )
        
        # Format command with context variables
        formatted_command = self._format_command(command, step_context)
        
        # Execute with interactive handling
        start_time = time.time()
        
        try:
            # Try primary command
            result = self._execute_with_fallback(formatted_command, step_context)
            
            # Log command execution
            self.command_history.append({
                'command': formatted_command,
                'timestamp': time.time(),
                'success': result['success'],
                'step_context': step_context
            })
            
            return {
                'success': result['success'],
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'duration': time.time() - start_time,
                'command_used': formatted_command,
                'fallback_used': result.get('fallback_used', False),
                'recovery_applied': result.get('recovery_applied', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'duration': time.time() - start_time,
                'command_used': formatted_command,
                'exception': True
            }
    
    def _format_command(self, command: str, context: Dict[str, Any]) -> str:
        """Format command with context variables"""
        
        # Extract common variables
        module = context.get('module', '')
        feature = context.get('feature', '')
        pattern = context.get('pattern', feature)
        
        # Format command
        try:
            return command.format(
                module=module,
                feature=feature,
                pattern=pattern,
                **context
            )
        except KeyError as e:
            # If formatting fails, return original command
            return command
    
    def _execute_with_fallback(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command with intelligent fallback strategies"""
        
        step_type = context.get('step_type', '')
        module = context.get('module', '')
        
        # Try primary command
        result = self._safe_execute(command)
        
        if result['success']:
            return result
        
        # Apply fallback strategies based on step type and error
        fallback_command = self._get_fallback_command(command, step_type, result['error'])
        
        if fallback_command:
            print(f"    🔄 Primary failed, trying fallback: {fallback_command}")
            fallback_result = self._safe_execute(fallback_command)
            fallback_result['fallback_used'] = True
            
            if fallback_result['success']:
                return fallback_result
        
        # Apply recovery strategies
        recovery_result = self._apply_recovery(command, step_type, module, result['error'])
        if recovery_result:
            recovery_result['recovery_applied'] = True
            return recovery_result
        
        # Return original failure if all strategies fail
        return result
    
    def _safe_execute(self, command: str) -> Dict[str, Any]:
        """Safely execute command with error handling"""
        
        try:
            # Execute command
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': process.returncode == 0,
                'output': process.stdout,
                'error': process.stderr,
                'return_code': process.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Command timed out after 5 minutes',
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }
    
    def _get_fallback_command(self, original_command: str, step_type: str, error: str) -> Optional[str]:
        """Get appropriate fallback command based on step type and error"""
        
        # Nx-specific fallbacks
        if 'nx run' in original_command:
            if 'install' in original_command:
                return original_command.replace('nx run', 'cd code/libs/python').replace(':install', ' && uv sync')
            elif 'format' in original_command:
                return original_command.replace('nx run', 'cd code/libs/python').replace(':format', ' && uv run ruff format .')
            elif 'lint' in original_command:
                return original_command.replace('nx run', 'cd code/libs/python').replace(':lint', ' && uv run ruff check .')
            elif 'test' in original_command:
                return original_command.replace('nx run', 'cd code/libs/python').replace(':test-fast', ' && uv run pytest')
        
        # Step-specific fallbacks
        step_commands = self.workflow_commands.get(step_type, {})
        for key, fallback in step_commands.items():
            if 'fallback' in key and key.replace('_fallback', '') in original_command:
                return fallback
        
        return None
    
    def _apply_recovery(self, command: str, step_type: str, module: str, error: str) -> Optional[Dict[str, Any]]:
        """Apply recovery strategies for common workflow issues"""
        
        # Nx cache issues
        if 'nx' in error.lower() and ('cache' in error.lower() or 'daemon' in error.lower()):
            print("    🔄 Applying nx cache recovery...")
            reset_result = self._safe_execute("nx reset")
            if reset_result['success']:
                # Retry original command
                retry_result = self._safe_execute(command)
                if retry_result['success']:
                    return retry_result
        
        # Dependency issues
        if 'module not found' in error.lower() or 'import error' in error.lower():
            print("    🔄 Applying dependency recovery...")
            if module:
                sync_result = self._safe_execute(f"cd code/libs/python/{module} && uv sync --reinstall")
                if sync_result['success']:
                    retry_result = self._safe_execute(command)
                    if retry_result['success']:
                        return retry_result
        
        # Permission issues
        if 'permission denied' in error.lower():
            print("    🔄 Applying permission recovery...")
            # Try with explicit python path
            if 'python' in command:
                fixed_command = command.replace('python', 'python3')
                retry_result = self._safe_execute(fixed_command)
                if retry_result['success']:
                    return retry_result
        
        return None
    
    def get_available_commands(self, step_type: str) -> List[str]:
        """Get commands available for specific workflow step type"""
        
        step_commands = self.workflow_commands.get(step_type, {})
        return [cmd for cmd in step_commands.values() if not cmd.startswith('fallback')]
    
    def get_command_history(self) -> List[Dict[str, Any]]:
        """Get history of executed commands in this workflow session"""
        return self.command_history.copy()
    
    def clear_command_history(self):
        """Clear command history (useful for new workflow sessions)"""
        self.command_history.clear()
    
    def validate_environment(self, module: str) -> Dict[str, Any]:
        """Validate that the environment is ready for workflow execution"""
        
        validation_results = {}
        
        # Check if module exists
        module_path = Path(f"code/libs/python/{module}")
        validation_results['module_exists'] = module_path.exists()
        
        # Check if nx is available
        nx_result = self._safe_execute("nx --version")
        validation_results['nx_available'] = nx_result['success']
        
        # Check if uv is available
        uv_result = self._safe_execute("uv --version")
        validation_results['uv_available'] = uv_result['success']
        
        # Check if module has proper structure
        if validation_results['module_exists']:
            pyproject_exists = (module_path / "pyproject.toml").exists()
            tests_exist = (module_path / "tests").exists()
            validation_results['proper_structure'] = pyproject_exists and tests_exist
        else:
            validation_results['proper_structure'] = False
        
        # Overall validation
        validation_results['ready'] = all([
            validation_results['module_exists'],
            validation_results['nx_available'] or validation_results['uv_available'],
            validation_results['proper_structure']
        ])
        
        return validation_results


class WorkflowAgentIntegration:
    """
    Integration layer between workflow system and interactive agents.
    
    Provides workflow-aware agent responses and context management.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.interactive_system = MomInteractiveSystem(config)
        self.workflow_executor = WorkflowCommandExecutor(config)
    
    def execute_workflow_step(self, step_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow step with full agent integration"""
        
        # Create execution context
        context = self.interactive_system.create_execution_context(
            current_task=step_info.get('description', ''),
            session_metadata=step_info
        )
        
        # Get step-specific commands
        step_type = step_info.get('step_type', '')
        available_commands = self.workflow_executor.get_available_commands(step_type)
        
        # Execute step commands
        results = []
        for command in available_commands:
            result = self.workflow_executor.execute_workflow_command(command, step_info)
            results.append(result)
        
        # Aggregate results
        success_rate = sum(1 for r in results if r['success']) / len(results) if results else 0
        
        return {
            'step_id': step_info.get('step_id'),
            'success': success_rate > 0.5,
            'success_rate': success_rate,
            'command_results': results,
            'agent_context': context.__dict__
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        
        # This would integrate with workflow state management
        # For now, return basic status
        return {
            'workflow_id': workflow_id,
            'status': 'running',
            'command_history': self.workflow_executor.get_command_history()
        }