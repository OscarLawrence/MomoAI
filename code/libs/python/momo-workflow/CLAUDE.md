# CLAUDE.md - Scientific Workflow Management System

## Module Overview

**momo-workflow** provides a scientific, flexible workflow abstraction with reversible operations, comprehensive testing, and performance benchmarking. Built for long-term maintainability with protocol-based design.

## Architecture Principles

### Core Design
- **Protocol-based**: `WorkflowStep`, `Command` protocols for extensibility
- **Scientific rigor**: Comprehensive metrics, statistical analysis, reproducible tests
- **Reversible operations**: All steps can rollback with state management
- **Performance-first**: Resource tracking, scalability analysis, optimization

### Key Components
```
momo_workflow/
├── types.py          # Core types, protocols, metrics
├── core.py           # WorkflowEngine, BaseWorkflowStep
├── commands.py       # CommandRegistry, execution system
├── testing.py        # Test framework, fixtures, assertions
└── benchmarks/       # Performance measurement suite
```

## Development Workflow

### MANDATORY Process
1. **Format**: `nx run momo-workflow:format` - Format code after changes
2. **Lint**: `nx run momo-workflow:lint` - Check code style 
3. **Type check**: `nx run momo-workflow:typecheck` (if pyright available)
4. **Test**: `nx run momo-workflow:test-fast` - Run unit/e2e tests

### Testing Strategy
- **Unit tests**: Protocol compliance, edge cases (`tests/unit/`)
- **E2E tests**: Full workflow scenarios (`tests/e2e/`)
- **Performance tests**: Benchmark suite validation
- **Example scripts**: Working demonstrations (`scripts/`)

## Usage Patterns

### Creating Workflow Steps
```python
class CustomStep(BaseWorkflowStep):
    def __init__(self, step_id: str):
        super().__init__(step_id, "Description", reversible=True)
    
    def execute(self, context: WorkflowContext) -> StepResult:
        # Implementation with metrics tracking
        start_time = time.time()
        # ... do work ...
        return StepResult(
            step_id=self.step_id,
            status=StepStatus.SUCCESS,
            metrics=ExecutionMetrics(start_time=start_time, end_time=time.time()),
            rollback_data={"cleanup_info": "..."}  # For rollback
        )
    
    def rollback(self, context: WorkflowContext, result: StepResult) -> None:
        # Cleanup using rollback_data
        pass
```

### Command Registration
```python
from momo_workflow.commands import register_command

@register_command("process_data", "Process data with validation")
def process_data(input_data: list, validation: bool = True) -> dict:
    # Command implementation
    return {"processed": len(input_data), "valid": validation}
```

### Testing Workflows
```python
from momo_workflow.testing import WorkflowTestFixture, WorkflowTestCase

fixture = WorkflowTestFixture()
test_case = WorkflowTestCase(fixture)

workflow, context = create_performance_test_scenario(10, 0.1)
result = engine.execute_workflow(workflow, context)

test_case.assert_workflow_success(result)
test_case.assert_performance_bounds(result, max_duration=5.0)
```

## Performance Characteristics

### Benchmarked Operations
- **Execution scaling**: O(n) with step count, <0.005s overhead per step
- **Memory efficiency**: <10MB baseline + step-specific usage
- **Rollback performance**: <2x execution time for full rollback
- **Command overhead**: <0.001s registration, <0.01s execution wrapper

### Resource Management
- **Memory tracking**: Peak usage monitoring per workflow
- **CPU profiling**: Execution time analysis with statistical confidence
- **Artifact management**: File system integration with cleanup

## Integration Points

### With momo-mom Command System
```python
# Register workflow commands in mom.yaml
commands:
  run-workflow:
    pattern: "python -m momo_workflow.scripts.{script_name}"
    fallback: "cd code/libs/python/momo-workflow && python scripts/{script_name}.py"
```

### With Testing Infrastructure
- Uses standard `pytest` framework
- Integrates with nx test execution
- Benchmark results in JSON format for CI/CD

### With Other Modules
- **momo-logger**: Structured logging integration
- **momo-store-***: Artifact persistence backends
- **momo-kb**: Workflow knowledge base integration

## Examples and Scripts

### Available Scripts
1. `01_basic_usage.py` - Core concepts, simple workflow
2. `02_command_system.py` - Command registry, shell integration
3. `03_testing_and_benchmarks.py` - Testing framework, performance analysis

### Running Examples
```bash
# From project root or module directory
python scripts/01_basic_usage.py
nx run momo-workflow:test  # Full test suite
python benchmarks/performance_benchmarks.py  # Performance analysis
```

## Key Design Decisions

### Scientific Approach
- **Reproducibility**: Deterministic execution, seeded random operations
- **Measurability**: Comprehensive metrics collection and analysis
- **Statistical rigor**: Confidence intervals, performance bounds testing

### Error Handling
- **Graceful degradation**: Partial workflow success tracking
- **Rollback safety**: Atomic operations with recovery points
- **Detailed diagnostics**: Error context, execution traces, performance data

### Extensibility
- **Protocol-based**: Easy to add new step types, command formats
- **Plugin architecture**: Command registry supports runtime registration
- **Testing integration**: Custom test scenarios, assertion helpers

## Future Enhancements

### Planned Features
- **Distributed execution**: Multi-node workflow orchestration
- **Visual workflow designer**: Graphical workflow creation
- **Advanced analytics**: ML-based performance optimization
- **Workflow templates**: Common pattern libraries

This module represents a scientific approach to workflow automation with emphasis on reliability, performance, and maintainability.