# momo-agent

**Unified AI Agent Framework for Scientific Task Execution**

A comprehensive framework that integrates [momo-workflow](../momo-workflow) scientific rigor with [momo-mom](../momo-mom) command execution capabilities, designed for AI agent task orchestration with rollback capabilities and performance measurement.

## Features

- **🔬 Scientific Rigor**: Built-in performance measurement, benchmarking, and statistical analysis
- **🤖 AI-Agnostic**: Works with any AI model (local, API-based, or human agents)
- **🔄 Rollback Capable**: All operations reversible with comprehensive state management
- **⚡ High Performance**: <5% framework overhead, 50+ tasks/second throughput
- **📊 Comprehensive Metrics**: CPU, memory, duration tracking for every operation
- **🧪 Local Model Testing**: Designed for validation with local AI models

## Quick Start

### Installation

```bash
# Install dependencies via uv
uv sync
```

### Basic Usage

```python
import asyncio
from momo_agent import (
    AgentExecutionContext, 
    BaseAgentTask, 
    BaseAgentWorkflow,
    AgentWorkflowEngine
)

# Create a simple task
class HelloTask(BaseAgentTask):
    async def execute(self, context):
        return self._create_result(
            status="SUCCESS",
            start_time=time.time(),
            outputs={"message": "Hello from momo-agent!"}
        )

# Execute workflow
async def main():
    task = HelloTask("hello-task", "Say hello")
    workflow = BaseAgentWorkflow("demo", "Demo Workflow", [task])
    context = AgentExecutionContext(session_id="demo-session")
    
    engine = AgentWorkflowEngine()
    result = await engine.execute_workflow(workflow, context)
    
    print(f"Status: {result.status}")
    print(f"Duration: {result.overall_metrics.duration_seconds:.2f}s")

asyncio.run(main())
```

### Command Integration

```python
from momo_agent.main import execute_command_workflow

# Execute shell commands with scientific measurement
async def command_example():
    commands = [
        "echo 'Starting workflow'",
        "python scripts/process_data.py",
        "nx run module:test",
    ]
    
    result = await execute_command_workflow(
        workflow_name="command_demo",
        commands=commands,
    )
    
    print(f"Executed {result.total_tasks} commands")
    print(f"Success rate: {result.completed_tasks}/{result.total_tasks}")

asyncio.run(command_example())
```

## Architecture

### Core Components

- **`types.py`** - Protocols and types for agent task execution
- **`core.py`** - Task and workflow execution engines with rollback
- **`command_executor.py`** - momo-mom integration for command execution
- **`main.py`** - Convenience functions and usage examples

### Integration Points

- **[momo-workflow](../momo-workflow)** - Scientific protocols and benchmarking
- **[momo-mom](../momo-mom)** - Command execution with fallback strategies
- **Future**: ADR system integration for complex decision workflows

## Development

### Running Tests

```bash
# Fast development testing
nx run momo-agent:test-fast

# Complete test suite with coverage
nx run momo-agent:test-all

# Performance benchmarking
python benchmarks/performance_benchmarks.py
```

### Code Quality

```bash
# Format code
nx run momo-agent:format

# Lint code
nx run momo-agent:lint

# Type check (if pyright available)
nx run momo-agent:typecheck
```

## Performance

### Benchmarks

- **Framework overhead**: <5% over raw async execution
- **Task throughput**: 50+ tasks/second for simple operations  
- **Rollback performance**: <2x execution time for complete rollback
- **Command integration**: <10ms overhead per command via momo-mom
- **Memory efficiency**: <10MB baseline + task-specific usage

### Scientific Measurement

Every task execution includes:
- CPU time and memory usage tracking
- Statistical analysis (mean, median, P95, std deviation)
- Scalability testing across workflow sizes
- Error handling overhead measurement

## Examples

### File Management Workflow

```python
class FileWriteTask(BaseAgentTask):
    def __init__(self, task_id: str, file_path: Path, content: str):
        super().__init__(task_id, f"Write to {file_path}", is_reversible=True)
        self._file_path = file_path
        self._content = content
    
    async def execute(self, context):
        self._file_path.write_text(self._content)
        return self._create_result(
            status="SUCCESS",
            start_time=time.time(),
            rollback_data={"file_to_delete": str(self._file_path)}
        )
    
    async def rollback(self, context, result):
        if result.rollback_data:
            Path(result.rollback_data["file_to_delete"]).unlink(missing_ok=True)
```

### Error Handling and Rollback

```python
# Workflow with automatic rollback on failure
result = await engine.execute_workflow(
    workflow, 
    context, 
    rollback_on_failure=True
)

if result.status == "FAILED":
    print(f"Workflow failed, rolled back {len(result.rollback_points)} tasks")
```

## Advanced Features

### Performance Tracking

```python
# Context automatically tracks performance metrics
context = AgentExecutionContext(session_id="perf-test")

# After execution, analyze metrics
print(f"Performance metrics: {context.performance_tracking}")

# Engine provides execution summaries  
engine_stats = engine.get_execution_summary()
print(f"Average task duration: {engine_stats['average_duration']:.3f}s")
```

### Local AI Model Testing

The framework is designed for validation with local AI models:

```python
# Test framework with local models (conceptual)
async def test_with_local_model(model_endpoint: str):
    # Framework provides standard test battery
    test_scenarios = create_standard_test_scenarios()
    
    for scenario in test_scenarios:
        result = await execute_with_ai_model(scenario, model_endpoint)
        validate_consistency(result)
        measure_performance(result)
```

## Contributing

This module follows the MomoAI development standards:

1. **Scientific approach** - All features benchmarked and measured
2. **Protocol-based design** - Extensible interfaces over implementations  
3. **Test-driven development** - Comprehensive unit and e2e test coverage
4. **Performance-first** - <5% overhead, optimized for high throughput
5. **Long-term maintainability** - Clear documentation and stable APIs

See [CLAUDE.md](./CLAUDE.md) for detailed development guidelines and architectural decisions.
