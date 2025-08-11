# Scientific Workflow Management System

A flexible, testable, and reversible workflow abstraction designed for scientific computing and development automation. Built with comprehensive testing, benchmarking, and documentation capabilities following scientific rigor principles.

## 🧬 Core Features

### 🔄 **Reversible Operations**
- Each workflow step can be rolled back
- Automatic rollback on failure
- Safe state management with rollback points

### 🧪 **Scientific Testing**
- Comprehensive test framework
- Performance benchmarking suite  
- Statistical analysis with confidence intervals
- Reproducible test scenarios

### 🔧 **Flexible Command System**
- Pluggable command registry
- Shell command integration
- Function-based commands
- Type-safe execution

### 📊 **Performance Monitoring**
- Execution time tracking
- Memory usage profiling  
- Resource estimation
- Scalability analysis

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
uv sync

# Run basic example
python scripts/01_basic_usage.py
```

### Basic Usage

```python
from momo_workflow import WorkflowEngine, WorkflowDefinition, BaseWorkflowStep
from momo_workflow.commands import register_command

# Register a custom command
@register_command("hello", "Say hello")
def hello_world(name: str = "World") -> str:
    return f"Hello, {name}!"

# Create a simple workflow step
class GreetingStep(BaseWorkflowStep):
    def execute(self, context):
        message = hello_world(name="Vincent")
        print(message)
        return StepResult(
            step_id=self.step_id,
            status=StepStatus.SUCCESS,
            metrics=ExecutionMetrics(start_time=time.time(), end_time=time.time())
        )

# Execute workflow
engine = WorkflowEngine()
workflow = WorkflowDefinition(
    workflow_id="greeting",
    name="Greeting Workflow", 
    description="Simple greeting example",
    version="1.0.0",
    author="Vincent",
    steps=[GreetingStep("greet", "Say hello")]
)

result = engine.execute_workflow(workflow)
print(f"Success rate: {result.success_rate:.2%}")
```

## 📚 Examples

### Script Examples

1. **[Basic Usage](scripts/01_basic_usage.py)** - Core workflow concepts and execution
2. **[Command System](scripts/02_command_system.py)** - Command registry and integration  
3. **[Testing & Benchmarks](scripts/03_testing_and_benchmarks.py)** - Testing framework and performance analysis

### Running Examples

```bash
# Basic workflow demonstration
python scripts/01_basic_usage.py

# Command system features
python scripts/02_command_system.py

# Testing and benchmarking
python scripts/03_testing_and_benchmarks.py
```

## 🏗️ Architecture

### Core Components

```
momo_workflow/
├── types.py          # Type definitions and protocols
├── core.py           # Workflow execution engine  
├── commands.py       # Command registry and execution
├── testing.py        # Testing framework
└── benchmarks/       # Performance benchmarking
    └── performance_benchmarks.py
```

### Key Abstractions

- **WorkflowStep Protocol** - Define executable workflow steps
- **Command Protocol** - Create reusable commands
- **WorkflowEngine** - Execute workflows with rollback support
- **Testing Framework** - Validate workflow behavior

## 🧪 Testing

### Running Tests

```bash
# Unit tests
nx run momo-workflow:test

# Performance benchmarks
python benchmarks/performance_benchmarks.py

# Full test suite via script
python scripts/03_testing_and_benchmarks.py
```

### Test Framework Features

- **Reproducible Scenarios** - Consistent test environments
- **Failure Testing** - Validate error handling
- **Performance Bounds** - Assert execution constraints
- **Rollback Verification** - Test recovery mechanisms

### Benchmark Categories

- **Execution Performance** - Step execution timing
- **Scalability Analysis** - Large workflow handling
- **Memory Efficiency** - Resource usage profiling
- **Rollback Performance** - Recovery operation timing

## 📋 Development Workflow

```bash
# Format code
nx run momo-workflow:format

# Type checking (if pyright available)
nx run momo-workflow:typecheck

# Run tests
nx run momo-workflow:test

# Performance benchmarks
python benchmarks/performance_benchmarks.py
```

## 🔬 Scientific Principles

This workflow system follows scientific computing best practices:

1. **Reproducibility** - Deterministic execution with same inputs
2. **Measurability** - Comprehensive metrics and performance data
3. **Testability** - Extensive test coverage with statistical analysis
4. **Reversibility** - Safe rollback for failed operations
5. **Documentation** - Clear interfaces and usage examples

## 🎯 Use Cases

- **Development Automation** - Build, test, deploy pipelines
- **Data Processing** - ETL workflows with rollback safety  
- **System Administration** - Configuration management
- **Research Computing** - Reproducible analysis pipelines
- **CI/CD Integration** - Reliable deployment workflows

## 🤝 Contributing

This module follows the MomoAI project standards:

- **Test-Driven Development** - Write tests before implementation
- **Scientific Rigor** - Benchmark all performance claims
- **Protocol-Based Design** - Use interfaces over implementations
- **Comprehensive Documentation** - Clear examples and API docs

## 📄 License

Part of the MomoAI project. See project root for license details.

---

**Built with scientific rigor for long-term maintainability** 🧬