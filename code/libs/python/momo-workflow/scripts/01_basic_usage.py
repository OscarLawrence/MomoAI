#!/usr/bin/env python3
"""
Basic workflow usage example - demonstrates core workflow concepts.

This script shows how to create and execute simple workflows with
the scientific workflow system, including error handling and metrics.
"""

from pathlib import Path
from momo_workflow import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowContext,
    BaseWorkflowStep,
    StepResult,
    StepStatus,
    ExecutionMetrics
)
from momo_workflow.commands import register_command
import time


class HelloWorldStep(BaseWorkflowStep):
    """Simple step that greets the user."""
    
    def __init__(self, name: str = "World"):
        super().__init__(
            step_id="hello_world",
            description=f"Say hello to {name}",
            reversible=False
        )
        self.name = name
    
    def execute(self, context: WorkflowContext) -> StepResult:
        """Execute greeting step."""
        start_time = time.time()
        
        message = f"Hello, {self.name}!"
        print(f"🌟 {message}")
        
        # Store result in context
        context.set_variable("greeting_message", message)
        
        return StepResult(
            step_id=self.step_id,
            status=StepStatus.SUCCESS,
            metrics=ExecutionMetrics(start_time=start_time, end_time=time.time())
        )


class FileCreationStep(BaseWorkflowStep):
    """Step that creates a file - demonstrates reversible operations."""
    
    def __init__(self, filename: str, content: str):
        super().__init__(
            step_id=f"create_{filename}",
            description=f"Create file: {filename}",
            reversible=True
        )
        self.filename = filename
        self.content = content
    
    def execute(self, context: WorkflowContext) -> StepResult:
        """Create file and track for rollback."""
        start_time = time.time()
        
        file_path = context.working_directory / self.filename
        file_path.write_text(self.content)
        
        print(f"📄 Created file: {file_path}")
        context.add_artifact(file_path)
        
        return StepResult(
            step_id=self.step_id,
            status=StepStatus.SUCCESS,
            metrics=ExecutionMetrics(start_time=start_time, end_time=time.time()),
            artifacts=[file_path],
            rollback_data={"file_path": str(file_path)}
        )
    
    def rollback(self, context: WorkflowContext, result: StepResult) -> None:
        """Remove created file during rollback."""
        if result.rollback_data and "file_path" in result.rollback_data:
            file_path = Path(result.rollback_data["file_path"])
            if file_path.exists():
                file_path.unlink()
                print(f"🗑️  Removed file during rollback: {file_path}")


@register_command("calculate_sum", "Calculate sum of two numbers")
def calculate_sum(a: int, b: int) -> int:
    """Example command for mathematical operations."""
    result = a + b
    print(f"🧮 Calculating: {a} + {b} = {result}")
    return result


def create_basic_workflow() -> WorkflowDefinition:
    """Create a basic workflow demonstration."""
    
    steps = [
        HelloWorldStep("Workflow User"),
        FileCreationStep("workflow_output.txt", "This file was created by the workflow!"),
        HelloWorldStep("Vincent (Workflow Creator)")
    ]
    
    # Fix step IDs to be unique
    steps[0]._step_id = "hello_user"
    steps[2]._step_id = "hello_creator"
    
    return WorkflowDefinition(
        workflow_id="basic_example",
        name="Basic Workflow Example",
        description="Demonstrates fundamental workflow concepts",
        version="1.0.0",
        author="Vincent",
        steps=steps,
        variables={"example_var": "Hello from variables!"}
    )


def main():
    """Run the basic workflow example."""
    print("🚀 Basic Workflow Usage Example")
    print("=" * 40)
    
    # Create workflow engine
    engine = WorkflowEngine()
    
    # Create workflow definition
    workflow = create_basic_workflow()
    
    # Create execution context
    context = WorkflowContext(
        working_directory=Path.cwd() / "workflow_output",
        variables={"user_name": "Vincent"}
    )
    
    # Ensure output directory exists
    context.working_directory.mkdir(exist_ok=True)
    
    print(f"📋 Executing workflow: {workflow.name}")
    print(f"📁 Working directory: {context.working_directory}")
    print()
    
    # Execute workflow
    result = engine.execute_workflow(workflow, context)
    
    # Display results
    print("\n📊 Workflow Results:")
    print(f"Status: {result.status.value}")
    print(f"Success Rate: {result.success_rate:.2%}")
    print(f"Total Duration: {result.total_duration:.3f}s")
    print(f"Steps Executed: {len(result.step_results)}")
    print(f"Artifacts Created: {len(result.artifacts_produced)}")
    
    # Show step details
    print("\n📋 Step Details:")
    for step_result in result.step_results:
        status_emoji = "✅" if step_result.success else "❌"
        print(f"  {status_emoji} {step_result.step_id}: {step_result.metrics.duration_seconds:.3f}s")
    
    # Show context variables
    print(f"\n🔤 Context Variables:")
    for key, value in context.variables.items():
        print(f"  {key}: {value}")
    
    # Show artifacts
    if result.artifacts_produced:
        print(f"\n📄 Artifacts Produced:")
        for artifact in result.artifacts_produced:
            if artifact.exists():
                content_preview = artifact.read_text()[:50] + "..." if len(artifact.read_text()) > 50 else artifact.read_text()
                print(f"  📄 {artifact.name}: {content_preview}")
    
    print("\n✨ Basic workflow example completed!")


if __name__ == "__main__":
    main()