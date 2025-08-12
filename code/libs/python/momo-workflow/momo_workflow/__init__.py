"""
Scientific Workflow Management System

A flexible, testable, and reversible workflow abstraction for scientific computing
and development automation. Features comprehensive testing, benchmarking, and
documentation capabilities.

Key Components:
- WorkflowEngine: Core execution engine with rollback capabilities
- Command System: Pluggable command registry with type safety
- Testing Framework: Comprehensive testing with performance analysis
- Benchmark Suite: Scientific performance measurement and analysis

Example Usage:
    ```python
    from momo_workflow import WorkflowEngine, WorkflowDefinition
    from momo_workflow.commands import register_command

    # Register custom command
    @register_command("hello_world", "Print hello world")
    def hello_world(name: str = "World") -> str:
        return f"Hello, {name}!"

    # Create and execute workflow
    engine = WorkflowEngine()
    workflow = WorkflowDefinition(
        workflow_id="example",
        name="Example Workflow",
        description="Simple example",
        version="1.0.0",
        author="developer"
    )

    result = engine.execute_workflow(workflow)
    print(f"Success rate: {result.success_rate}")
    ```
"""

# Core workflow components
from .core import WorkflowEngine, BaseWorkflowStep
from .types import (
    WorkflowDefinition,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
    StepResult,
    StepStatus,
    ExecutionMetrics,
)

# Command system
from .commands import (
    CommandRegistry,
    CommandStep,
    FunctionCommand,
    ShellCommand,
    register_command,
    get_command_registry,
)

# Testing framework
from .testing import (
    TestWorkflowStep,
    MockCommand,
    WorkflowTestFixture,
    WorkflowTestCase,
    run_workflow_test_suite,
    create_failure_test_scenario,
    create_performance_test_scenario,
)

# Agent workflows with guardrails
from .agent_workflows import (
    AgentGuardedWorkflow,
    ResearchGuardStep,
    PlanningGuardStep,
    TDDGuardStep,
    ValidationGuardStep,
)

__version__ = "1.0.0"
__author__ = "Vincent (Momo AI Project)"

# Public API
__all__ = [
    # Core workflow
    "WorkflowEngine",
    "BaseWorkflowStep",
    "WorkflowDefinition",
    "WorkflowContext",
    "WorkflowResult",
    "WorkflowStatus",
    "StepResult",
    "StepStatus",
    "ExecutionMetrics",
    # Commands
    "CommandRegistry",
    "CommandStep",
    "FunctionCommand",
    "ShellCommand",
    "register_command",
    "get_command_registry",
    # Testing
    "TestWorkflowStep",
    "MockCommand",
    "WorkflowTestFixture",
    "WorkflowTestCase",
    "run_workflow_test_suite",
    "create_failure_test_scenario",
    "create_performance_test_scenario",
    # Agent workflows
    "AgentGuardedWorkflow",
    "ResearchGuardStep",
    "PlanningGuardStep",
    "TDDGuardStep",
    "ValidationGuardStep",
]
