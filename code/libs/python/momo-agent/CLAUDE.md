# CLAUDE.md - Unified AI Agent Framework (momo-agent)

## Module Overview

**momo-agent** provides a unified, scientific framework for AI agent task execution that integrates momo-workflow's scientific rigor with momo-mom's command execution capabilities and ADR system integration. Built for testability with local AI models and comprehensive performance measurement.

## Architecture Principles

### Core Design Philosophy
- **Scientific rigor**: All workflows benchmarked, measured, and reproducible
- **AI-agnostic**: Works with any AI model (local, API-based, or human agents)
- **Integration-focused**: Bridges momo-workflow protocols with momo-mom command execution
- **Rollback-capable**: All operations reversible with state management
- **Performance-first**: Comprehensive metrics, optimization, and benchmarking built-in

### Key Components
```
momo_agent/
├── types.py                # Core protocols and types for agent execution
├── core.py                 # Agent task and workflow execution engines  
├── command_executor.py     # momo-mom integration for command execution
├── main.py                 # Convenience functions and entry points
└── __init__.py            # Public API exports
```

## Development Workflow

### MANDATORY Process (Same as other modules)
1. **Format**: `nx run momo-agent:format` - Format code after changes
2. **Lint**: `nx run momo-agent:lint` - Check code style 
3. **Type check**: `nx run momo-agent:typecheck` (if pyright available)
4. **Test**: `nx run momo-agent:test-fast` - Run unit/e2e tests

### Testing Strategy
- **Unit tests**: Protocol compliance, task/workflow behavior (`tests/unit/`)
- **E2E tests**: Complete workflow scenarios with rollback (`tests/e2e/`)
- **Benchmarks**: Performance validation and optimization (`benchmarks/`)
- **Example scripts**: Working demonstrations (`scripts/`)

## Usage Patterns

### Creating Agent Tasks
```python
class CustomAgentTask(BaseAgentTask):
    def __init__(self, task_id: str, custom_param: str):
        super().__init__(
            task_id=task_id,
            description="Custom agent task",
            task_type=AgentTaskType.SIMPLE,
            priority=TaskPriority.NORMAL,
            is_reversible=True,
        )
        self._custom_param = custom_param
    
    async def execute(self, context: AgentExecutionContext) -> AgentTaskResult:
        start_time = time.time()
        try:
            # Task implementation with comprehensive tracking
            # ... do work ...
            
            return self._create_result(
                status=StepStatus.SUCCESS,
                start_time=start_time,
                outputs={"result": "success"},
                rollback_data={"cleanup_info": "..."},
            )
        except Exception as e:
            return self._create_result(
                status=StepStatus.FAILED,
                start_time=start_time,
                error=e,
            )
    
    async def rollback(self, context: AgentExecutionContext, result: AgentTaskResult) -> None:
        # Cleanup using rollback_data
        if result.rollback_data:
            # Perform rollback operations
            pass
```

### Executing Agent Workflows
```python
# Create workflow with multiple tasks
tasks = [
    CommandTask("setup", "mkdir -p /tmp/test"),
    CustomAgentTask("process", "custom_param_value"),
    CommandTask("cleanup", "rm -rf /tmp/test"),
]

workflow = BaseAgentWorkflow(
    workflow_id="example-workflow",
    name="Example Agent Workflow", 
    tasks=tasks,
)

# Execute with scientific measurement and rollback capability
context = AgentExecutionContext(
    session_id="example-session",
    working_directory=Path("/tmp/workspace"),
)

engine = AgentWorkflowEngine()
result = await engine.execute_workflow(
    workflow, 
    context, 
    rollback_on_failure=True
)

# Analyze results with comprehensive metrics
print(f"Status: {result.status}")
print(f"Tasks: {result.completed_tasks}/{result.total_tasks}")  
print(f"Duration: {result.overall_metrics.duration_seconds:.2f}s")
```

### Command Integration with momo-mom
```python
# Simple command workflow execution
commands = [
    "echo 'Starting workflow'",
    "python scripts/process_data.py", 
    "nx run module:test",
]

result = await execute_command_workflow(
    workflow_name="command_example",
    commands=commands,
    working_directory=Path("/workspace"),
)

# Command executor with advanced features
executor = create_agent_command_executor(verbose=True)
cmd_result = await executor.execute_command(
    "nx run momo-agent:test",
    context,
    timeout_seconds=300
)
```

## Performance Characteristics

### Benchmarked Metrics
- **Framework overhead**: <5% over raw async execution
- **Task throughput**: 50+ tasks/second for simple operations
- **Rollback performance**: <2x execution time for full rollback
- **Command integration**: <10ms overhead per command via momo-mom
- **Memory efficiency**: <10MB baseline + task-specific usage

### Scientific Measurement
- **Execution metrics**: CPU time, memory usage, duration for every task
- **Statistical analysis**: Mean, median, P95, standard deviation
- **Scalability testing**: Performance across 1-50 task workflows
- **Error handling overhead**: Measured failure vs success execution times

## Integration Points

### With momo-workflow
- Uses `WorkflowEngine` for core orchestration capabilities
- Implements scientific measurement protocols and reversible operations
- Integrates benchmarking framework for performance analysis
- Follows same testing patterns and statistical rigor

### With momo-mom 
- `MomAgentCommandExecutor` wraps command execution with fallback strategies
- Automatic retry logic and cache recovery mechanisms
- AI-friendly output formatting and error reporting
- Command duration estimation and performance tracking

### With ADR System
- Framework designed for complex task promotion to ADR workflow
- Decision documentation and architectural impact analysis
- Integration with existing ADR branch management (future)

### With Other Modules
- **momo-logger**: Structured logging with agent context
- **momo-store-***: State persistence and artifact management (future)
- **momo-kb**: Agent workflow knowledge base integration (future)

## Local AI Model Testing

### Framework Features
- **AI-agnostic design**: Works with any model supporting structured workflow execution
- **Local model support**: Tested with Ollama, local OpenAI-compatible servers
- **Reproducibility**: Identical task execution across different AI agents
- **Performance comparison**: Benchmarking between different model types
- **Quality validation**: Task completion validation and success measurement

### Testing Approach  
```python
# Framework designed for validation with local models
async def validate_with_local_model(model_endpoint: str):
    # Standard test battery for any AI model
    test_tasks = create_standard_test_battery()
    
    results = []
    for task_scenario in test_tasks:
        result = await execute_with_model(task_scenario, model_endpoint)
        results.append(result)
    
    # Measure consistency, performance, success rates
    return analyze_model_performance(results)
```

## Examples and Scripts

### Available Scripts
1. `01_basic_usage.py` - Core concepts, task creation, workflow execution
2. `benchmarks/performance_benchmarks.py` - Complete performance analysis suite

### Running Examples
```bash
# From project root
python code/libs/python/momo-agent/scripts/01_basic_usage.py

# Benchmarking  
python code/libs/python/momo-agent/benchmarks/performance_benchmarks.py

# Testing
nx run momo-agent:test-fast         # Unit + e2e tests
nx run momo-agent:test-all          # Complete suite with coverage
```

## Key Design Decisions

### Scientific Integration
- **momo-workflow protocols**: All tasks implement scientific measurement patterns
- **Statistical rigor**: Performance bounds testing, confidence intervals
- **Reproducibility**: Deterministic execution with comprehensive state tracking
- **Benchmarking**: Built-in performance analysis and optimization tools

### AI Agent Abstraction  
- **Protocol-based**: `AgentTask` and `AgentWorkflow` protocols for extensibility
- **Command integration**: Seamless momo-mom command execution with fallbacks
- **State management**: Context tracking, task history, performance metrics
- **Error recovery**: Comprehensive rollback with state restoration

### Performance Optimization
- **Async-first**: All I/O operations designed for high concurrency  
- **Minimal overhead**: <5% framework overhead over raw execution
- **Resource tracking**: Memory, CPU, and execution time monitoring
- **Scalability analysis**: Performance testing across different workflow sizes

## Future Enhancements

### Planned Features
- **ADR integration**: Automatic promotion of complex tasks to structured decision workflows
- **Model comparison**: Systematic benchmarking across different AI model types  
- **Workflow optimization**: ML-based performance improvement recommendations
- **State persistence**: Integration with momo-store modules for workflow resumption

This module represents the unified integration point for AI agent task execution, combining scientific rigor with practical command execution and comprehensive performance measurement.