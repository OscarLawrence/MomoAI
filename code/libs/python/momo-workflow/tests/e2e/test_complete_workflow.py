"""
End-to-end tests for complete workflow scenarios.
"""

import tempfile
import time
from pathlib import Path

import pytest

from momo_workflow import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowContext,
    WorkflowStatus,
    BaseWorkflowStep,
    StepResult,
    StepStatus,
    ExecutionMetrics,
)
from momo_workflow.commands import register_command, get_command_registry, CommandStep
from momo_workflow.testing import TestWorkflowStep, WorkflowTestFixture


class TestCompleteWorkflowScenarios:
    """End-to-end tests for complete workflow scenarios."""
    
    def test_file_processing_workflow(self):
        """Test a complete file processing workflow."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            class FileProcessingStep(BaseWorkflowStep):
                def __init__(self, step_id: str, filename: str, content: str):
                    super().__init__(step_id, f"Process file: {filename}", reversible=True)
                    self.filename = filename
                    self.content = content
                
                def execute(self, context: WorkflowContext) -> StepResult:
                    start_time = time.time()
                    
                    # Create file
                    file_path = context.working_directory / self.filename
                    file_path.write_text(self.content)
                    
                    # Process content (example: count lines)
                    line_count = len(self.content.split('\n'))
                    context.set_variable(f"{self.step_id}_lines", line_count)
                    context.add_artifact(file_path)
                    
                    return StepResult(
                        step_id=self.step_id,
                        status=StepStatus.SUCCESS,
                        metrics=ExecutionMetrics(start_time=start_time, end_time=time.time()),
                        artifacts=[file_path],
                        rollback_data={"file_path": str(file_path)}
                    )
                
                def rollback(self, context: WorkflowContext, result: StepResult) -> None:
                    if result.rollback_data and "file_path" in result.rollback_data:
                        file_path = Path(result.rollback_data["file_path"])
                        if file_path.exists():
                            file_path.unlink()
            
            engine = WorkflowEngine()
            steps = [
                FileProcessingStep("process_input", "input.txt", "Line 1\nLine 2\nLine 3"),
                FileProcessingStep("process_config", "config.txt", "Setting 1\nSetting 2"),
            ]
            
            workflow = WorkflowDefinition(
                workflow_id="file_processing",
                name="File Processing Workflow",
                description="Process multiple files",
                version="1.0.0",
                author="test",
                steps=steps
            )
            
            context = WorkflowContext(working_directory=temp_path)
            
            # Act
            result = engine.execute_workflow(workflow, context)
            
            # Assert
            assert result.status == WorkflowStatus.SUCCESS
            assert result.success_rate == 1.0
            assert len(result.artifacts_produced) == 2
            
            # Check that files were created
            assert (temp_path / "input.txt").exists()
            assert (temp_path / "config.txt").exists()
            
            # Check context variables
            assert context.get_variable("process_input_lines") == 3
            assert context.get_variable("process_config_lines") == 2
    
    def test_command_based_workflow(self):
        """Test workflow using command system."""
        # Arrange
        @register_command("process_text", "Process text content")
        def process_text(text: str, operation: str = "upper") -> str:
            if operation == "upper":
                return text.upper()
            elif operation == "lower":
                return text.lower()
            elif operation == "reverse":
                return text[::-1]
            else:
                raise ValueError(f"Unknown operation: {operation}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            registry = get_command_registry()
            engine = WorkflowEngine()
            
            steps = [
                CommandStep(
                    command=registry.get_command("process_text"),
                    step_id="uppercase_step",
                    text="hello world",
                    operation="upper"
                ),
                CommandStep(
                    command=registry.get_command("process_text"),
                    step_id="reverse_step",
                    text="hello world",
                    operation="reverse"
                ),
            ]
            
            workflow = WorkflowDefinition(
                workflow_id="command_workflow",
                name="Command-Based Workflow",
                description="Workflow using command system",
                version="1.0.0",
                author="test",
                steps=steps
            )
            
            context = WorkflowContext(working_directory=temp_path)
            
            # Act
            result = engine.execute_workflow(workflow, context)
            
            # Assert
            assert result.status == WorkflowStatus.SUCCESS
            assert result.success_rate == 1.0
            assert len(result.step_results) == 2
    
    def test_workflow_with_failure_and_partial_rollback(self):
        """Test workflow with failure and partial rollback."""
        # Arrange
        fixture = WorkflowTestFixture()
        
        steps = [
            TestWorkflowStep("step_1", artifacts=["artifact_1.txt"]),
            TestWorkflowStep("step_2", artifacts=["artifact_2.txt"]),
            TestWorkflowStep("step_3", should_fail=True),  # This will fail
            TestWorkflowStep("step_4", artifacts=["artifact_4.txt"]),  # Won't execute
        ]
        
        workflow = fixture.create_simple_workflow(steps, "failure_test")
        context = fixture.create_test_context()
        
        engine = WorkflowEngine()
        
        # Act
        result = engine.execute_workflow(workflow, context, rollback_on_failure=True)
        
        # Assert
        assert result.status in [WorkflowStatus.FAILED, WorkflowStatus.PARTIALLY_ROLLED_BACK]
        assert result.success_rate < 1.0
        assert len(result.step_results) == 3  # Only first 3 steps executed
        
        # Check that successful steps were executed
        assert steps[0].executed
        assert steps[1].executed
        assert steps[2].executed
        assert not steps[3].executed  # Fourth step not executed
        
        fixture.cleanup()
    
    def test_performance_workflow(self):
        """Test workflow performance characteristics."""
        # Arrange
        num_steps = 20
        steps = []
        
        for i in range(num_steps):
            step = TestWorkflowStep(f"perf_step_{i+1}", execution_time=0.01)
            steps.append(step)
        
        fixture = WorkflowTestFixture()
        workflow = fixture.create_simple_workflow(steps, "performance_test")
        context = fixture.create_test_context()
        
        engine = WorkflowEngine()
        
        # Act
        start_time = time.time()
        result = engine.execute_workflow(workflow, context)
        total_time = time.time() - start_time
        
        # Assert
        assert result.status == WorkflowStatus.SUCCESS
        assert result.success_rate == 1.0
        assert len(result.step_results) == num_steps
        
        # Performance assertions
        assert total_time < 5.0  # Should complete within 5 seconds
        assert result.total_duration > 0
        
        # Check that all steps were executed
        assert all(step.executed for step in steps)
        
        fixture.cleanup()
    
    def test_context_data_flow(self):
        """Test data flow through workflow context."""
        # Arrange
        class DataFlowStep(BaseWorkflowStep):
            def __init__(self, step_id: str, input_var: str = None, output_var: str = None, transform_func=None):
                super().__init__(step_id, f"Data flow step: {step_id}")
                self.input_var = input_var
                self.output_var = output_var
                self.transform_func = transform_func
            
            def execute(self, context: WorkflowContext) -> StepResult:
                start_time = time.time()
                
                if self.input_var:
                    input_value = context.get_variable(self.input_var)
                    if self.transform_func and input_value is not None:
                        output_value = self.transform_func(input_value)
                        if self.output_var:
                            context.set_variable(self.output_var, output_value)
                
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.SUCCESS,
                    metrics=ExecutionMetrics(start_time=start_time, end_time=time.time())
                )
        
        engine = WorkflowEngine()
        steps = [
            DataFlowStep("init_step", output_var="initial_data", transform_func=lambda x: 10),
            DataFlowStep("multiply_step", "initial_data", "multiplied_data", lambda x: x * 2),
            DataFlowStep("add_step", "multiplied_data", "final_data", lambda x: x + 5),
        ]
        
        workflow = WorkflowDefinition(
            workflow_id="data_flow",
            name="Data Flow Workflow",
            description="Test data flow through context",
            version="1.0.0",
            author="test",
            steps=steps
        )
        
        context = WorkflowContext()
        
        # Act
        result = engine.execute_workflow(workflow, context)
        
        # Assert
        assert result.status == WorkflowStatus.SUCCESS
        assert context.get_variable("initial_data") == 10
        assert context.get_variable("multiplied_data") == 20
        assert context.get_variable("final_data") == 25