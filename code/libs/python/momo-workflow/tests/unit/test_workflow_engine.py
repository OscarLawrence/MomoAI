"""
Unit tests for WorkflowEngine core functionality.
"""

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


class SimpleTestStep(BaseWorkflowStep):
    """Simple test step for unit testing."""
    
    def __init__(self, step_id: str, should_fail: bool = False):
        super().__init__(step_id, f"Test step: {step_id}", reversible=True)
        self.should_fail = should_fail
        self.executed = False
        self.rolled_back = False
    
    def execute(self, context: WorkflowContext) -> StepResult:
        """Execute test step."""
        start_time = time.time()
        self.executed = True
        
        if self.should_fail:
            return StepResult(
                step_id=self.step_id,
                status=StepStatus.FAILED,
                metrics=ExecutionMetrics(start_time=start_time, end_time=time.time()),
                error=Exception(f"Test failure: {self.step_id}")
            )
        
        return StepResult(
            step_id=self.step_id,
            status=StepStatus.SUCCESS,
            metrics=ExecutionMetrics(start_time=start_time, end_time=time.time()),
            rollback_data={"test_data": "rollback_info"}
        )
    
    def rollback(self, context: WorkflowContext, result: StepResult) -> None:
        """Rollback test step."""
        self.rolled_back = True


class TestWorkflowEngine:
    """Test cases for WorkflowEngine."""
    
    def test_successful_workflow_execution(self):
        """Test successful execution of simple workflow."""
        # Arrange
        engine = WorkflowEngine()
        steps = [
            SimpleTestStep("step_1"),
            SimpleTestStep("step_2"),
            SimpleTestStep("step_3")
        ]
        
        workflow = WorkflowDefinition(
            workflow_id="test_success",
            name="Success Test",
            description="Test successful execution",
            version="1.0.0",
            author="test",
            steps=steps
        )
        
        context = WorkflowContext()
        
        # Act
        result = engine.execute_workflow(workflow, context)
        
        # Assert
        assert result.status == WorkflowStatus.SUCCESS
        assert result.success_rate == 1.0
        assert len(result.step_results) == 3
        assert all(r.success for r in result.step_results)
        assert all(step.executed for step in steps)
    
    def test_workflow_failure_handling(self):
        """Test workflow failure handling without rollback."""
        # Arrange
        engine = WorkflowEngine()
        steps = [
            SimpleTestStep("step_1"),
            SimpleTestStep("step_2", should_fail=True),
            SimpleTestStep("step_3")
        ]
        
        workflow = WorkflowDefinition(
            workflow_id="test_failure",
            name="Failure Test",
            description="Test failure handling",
            version="1.0.0",
            author="test",
            steps=steps
        )
        
        context = WorkflowContext()
        
        # Act
        result = engine.execute_workflow(workflow, context, rollback_on_failure=False)
        
        # Assert
        assert result.status == WorkflowStatus.FAILED
        assert result.success_rate < 1.0
        assert len(result.step_results) == 2  # Only first two steps executed
        assert steps[0].executed
        assert steps[1].executed
        assert not steps[2].executed  # Third step not executed after failure
    
    def test_workflow_validation(self):
        """Test workflow definition validation."""
        # Arrange
        engine = WorkflowEngine()
        
        # Test empty workflow
        empty_workflow = WorkflowDefinition(
            workflow_id="empty_test",
            name="Empty Test",
            description="Empty workflow",
            version="1.0.0",
            author="test",
            steps=[]
        )
        
        context = WorkflowContext()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid workflow"):
            engine.execute_workflow(empty_workflow, context)
    
    def test_duplicate_step_ids_validation(self):
        """Test validation of duplicate step IDs."""
        # Arrange
        engine = WorkflowEngine()
        steps = [
            SimpleTestStep("duplicate_id"),
            SimpleTestStep("duplicate_id")  # Same ID
        ]
        
        workflow = WorkflowDefinition(
            workflow_id="duplicate_test",
            name="Duplicate Test",
            description="Test duplicate step IDs",
            version="1.0.0",
            author="test",
            steps=steps
        )
        
        context = WorkflowContext()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Duplicate step IDs found"):
            engine.execute_workflow(workflow, context)
    
    def test_context_variable_passing(self):
        """Test context variable passing between steps."""
        # Arrange
        class VariableStep(BaseWorkflowStep):
            def __init__(self, step_id: str, set_var: str = None, check_var: str = None):
                super().__init__(step_id, f"Variable step: {step_id}")
                self.set_var = set_var
                self.check_var = check_var
            
            def execute(self, context: WorkflowContext) -> StepResult:
                start_time = time.time()
                
                if self.set_var:
                    context.set_variable("test_var", self.set_var)
                
                if self.check_var:
                    actual_value = context.get_variable("test_var")
                    assert actual_value == self.check_var, f"Expected {self.check_var}, got {actual_value}"
                
                return StepResult(
                    step_id=self.step_id,
                    status=StepStatus.SUCCESS,
                    metrics=ExecutionMetrics(start_time=start_time, end_time=time.time())
                )
        
        engine = WorkflowEngine()
        steps = [
            VariableStep("set_step", set_var="test_value"),
            VariableStep("check_step", check_var="test_value")
        ]
        
        workflow = WorkflowDefinition(
            workflow_id="variable_test",
            name="Variable Test",
            description="Test variable passing",
            version="1.0.0",
            author="test",
            steps=steps
        )
        
        context = WorkflowContext()
        
        # Act
        result = engine.execute_workflow(workflow, context)
        
        # Assert
        assert result.status == WorkflowStatus.SUCCESS
        assert context.get_variable("test_var") == "test_value"
    
    def test_performance_metrics_collection(self):
        """Test that performance metrics are collected."""
        # Arrange
        engine = WorkflowEngine()
        steps = [SimpleTestStep("perf_step")]
        
        workflow = WorkflowDefinition(
            workflow_id="perf_test",
            name="Performance Test",
            description="Test performance metrics",
            version="1.0.0",
            author="test",
            steps=steps
        )
        
        context = WorkflowContext()
        
        # Act
        result = engine.execute_workflow(workflow, context)
        
        # Assert
        assert result.status == WorkflowStatus.SUCCESS
        assert result.overall_metrics.is_complete
        assert result.total_duration >= 0
        
        # Check step metrics
        step_result = result.step_results[0]
        assert step_result.metrics.is_complete
        assert step_result.metrics.duration_seconds >= 0