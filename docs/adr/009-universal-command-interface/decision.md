# ADR-009: Universal Command Interface (New momo-cmd Module)

**Date:** 2025-01-11  
**Status:** APPROVED  
**Decision Makers:** Vincent  
**Consulted:** Current momo-mom analysis, workflow reflection findings, agent integration requirements

## Table of Contents

- [Problem Statement](#problem-statement)
- [Current State Analysis](#current-state-analysis)
- [Decision](#decision)
- [Implementation Strategy](#implementation-strategy)
- [Success Metrics](#success-metrics)
- [Risks and Mitigations](#risks-and-mitigations)
- [Trade-offs Accepted](#trade-offs-accepted)
- [Implementation Results](#implementation-results)
- [Lessons Learned](#lessons-learned)
- [Next Steps](#next-steps)
- [Related Documentation](#related-documentation)

## Problem Statement

**Challenge**: Current `momo-mom` module provides some command mapping functionality but lacks a truly universal command interface for AI agents. While `momo-mom` serves important existing use cases, we need a more powerful interface for agent workflows.

**Core Issues**:
1. **Configuration-heavy architecture** - momo-mom requires explicit YAML mapping for each command type
2. **Limited file execution** - Cannot directly execute files like `mom test.py`
3. **Missing context awareness** - No understanding of module-specific environments
4. **Agent-unfriendly interface** - Multiple subcommands instead of universal pattern
5. **Incomplete coverage** - Many command types not supported by current system

**Impact**:
- Agents struggle with inconsistent command patterns
- Manual configuration required for new command types
- Workflow execution inefficiency in momo-agent integration
- Poor developer experience when working within module contexts
- Need to preserve existing momo-mom functionality while adding new capabilities

## Current State Analysis

### **Existing momo-mom Architecture Analysis**

**1. Current Strengths (To Preserve)**
- Working command mapping system with fallback strategies
- Configuration-based approach for specific use cases
- Integration with momo-agent for basic command execution
- Established patterns for nx command orchestration

**2. Current Limitations (To Address)**
```yaml
# Current: Requires explicit configuration for each command
commands:
  test:
    pattern: "nx run {target}:test"
    fallback: "cd code/libs/python/{target} && uv run pytest"
```

**2. Fixed Subcommand Structure**
```bash
# Current: Multiple specific subcommands
mom test target
mom build target  
mom script script-name
mom run "arbitrary command"
```

**3. No Context Awareness**
- Must specify module names even when working within module
- No automatic environment detection for file execution
- Scripts in module directories don't use module's uv environment

**4. Agent Integration Limitations**
- `momo-agent` cannot predict command execution patterns
- Complex fallback logic not transparent to agents
- Multiple command interfaces create confusion

### **Integration Pain Points**

**momo-workflow Integration**:
- Workflow steps must know which command interface to use
- No universal execution pattern for workflow tasks
- Command validation difficult with multiple interfaces

**momo-agent Integration**:
- CommandExecutor has complex routing logic
- Agents must learn multiple command patterns
- Error handling inconsistent across command types

## Decision

**DECISION: Create New momo-cmd Module with Universal Command Interface**

**Core Decision**: Create a new `momo-cmd` module alongside existing `momo-mom` to provide a context-aware, universal command interface that intelligently routes any command through a single entry point, while preserving existing momo-mom functionality.

**Key Changes**:
1. **New Module**: Create `momo-cmd` as separate module (preserve momo-mom)
2. **Universal Interface**: Single `mom <anything>` command entry point
3. **Context Awareness**: Auto-detect module environments and working contexts
4. **Intelligent Routing**: Convention-based command classification and execution
5. **Agent Optimization**: Predictable, discoverable command patterns
6. **Coexistence**: Both modules available during transition period

## Implementation Strategy

### **Phase 1: New Module Creation and Core Architecture (Week 1)**

#### **Step 1.1: Create New momo-cmd Module**
```bash
# Create new module structure (preserve existing momo-mom)
nx g @nxlv/python:uv-project momo-cmd --directory=code/libs/python/momo-cmd

# Create module package structure
mkdir -p code/libs/python/momo-cmd/momo_cmd
mkdir -p code/libs/python/momo-cmd/momo_cmd/strategies
mkdir -p code/libs/python/momo-cmd/tests/unit
mkdir -p code/libs/python/momo-cmd/tests/e2e
mkdir -p code/libs/python/momo-cmd/scripts
mkdir -p code/libs/python/momo-cmd/benchmarks
```

#### **Step 1.2: Setup Module Dependencies**
```bash
# Configure momo-cmd dependencies (initially similar to momo-mom)
cd code/libs/python/momo-cmd

# Add dependencies to pyproject.toml
uv add click
uv add pyyaml
uv add pytest pytest-asyncio pytest-cov
uv add ruff pyright

# No global imports to update - this is a new module
# Existing momo-mom remains unchanged
```

#### **Step 1.3: Create New Architecture Files**
```python
# New module structure
momo_cmd/
├── __init__.py          # Public API exports
├── cli.py               # Simplified single-command CLI
├── context.py           # WorkspaceContext, ModuleInfo classes  
├── router.py            # ContextAwareCommandRouter
├── strategies/          # Execution strategy implementations
│   ├── __init__.py
│   ├── base.py         # Strategy base classes
│   ├── file.py         # FileExecutionStrategy  
│   ├── module.py       # ModuleCommandStrategy
│   └── passthrough.py  # PassthroughCommandStrategy
└── detectors.py        # Smart command classification
```

#### **Step 1.4: Implement Context Detection System**
```python
# momo_cmd/context.py
class WorkspaceContext:
    def __init__(self, cwd: Path = None):
        self.cwd = cwd or Path.cwd()
        self.workspace_root = self._find_workspace_root()
        self.current_module = self._detect_current_module()
        
    def _find_workspace_root(self) -> Path:
        """Walk up to find workspace root (nx.json, CLAUDE.md, .git)"""
        current = self.cwd
        while current != current.parent:
            markers = ['nx.json', 'CLAUDE.md', '.git', 'package.json']
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        return self.cwd
    
    def _detect_current_module(self) -> Optional[str]:
        """Detect if working within a specific module"""
        try:
            relative = self.cwd.relative_to(self.workspace_root)
            parts = relative.parts
            
            # Pattern: code/libs/python/module-name/...
            if len(parts) >= 4 and parts[0:3] == ('code', 'libs', 'python'):
                return parts[3]
                
            # Pattern: root-level module (momo-workflow/)
            if len(parts) >= 1 and parts[0].startswith('momo-'):
                return parts[0]
                
        except ValueError:
            pass
            
        return None

class ModuleInfo:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.has_uv = (path / 'pyproject.toml').exists()
        self.has_nx = (path / 'project.json').exists()
        self.available_commands = self._discover_commands()
        
    def _discover_commands(self) -> list[str]:
        """Auto-discover available commands for module"""
        commands = []
        
        # Check nx project.json
        if self.has_nx:
            try:
                import json
                with open(self.path / 'project.json') as f:
                    project_data = json.load(f)
                    targets = project_data.get('targets', {})
                    commands.extend(targets.keys())
            except:
                pass
                
        # Add common commands
        common_commands = ['test-fast', 'format', 'lint', 'typecheck', 'install']
        commands.extend(common_commands)
        
        return list(set(commands))
```

### **Step 1.5: Implement Universal Command Router**
```python
# momo_cmd/router.py
class ContextAwareCommandRouter:
    def __init__(self, verbose=False, dry_run=False):
        self.context = WorkspaceContext()
        self.verbose = verbose
        self.dry_run = dry_run
        
    def route_and_execute(self, args: list[str]) -> bool:
        """Main entry point - route and execute any command"""
        strategy = self._classify_command(args)
        
        if self.verbose:
            print(f"Strategy: {strategy.__class__.__name__}")
            print(f"Context: {self.context.current_module or 'workspace root'}")
            
        if self.dry_run:
            print(f"Would execute: {strategy.get_execution_preview()}")
            return True
            
        return strategy.execute()
    
    def _classify_command(self, args: list[str]) -> ExecutionStrategy:
        """Intelligently classify and route command"""
        if not args:
            return ShowHelpStrategy(self.context)
            
        first_arg = args[0]
        
        # Strategy 1: Direct file execution (test.py, build.ts)
        if self._is_file_execution(first_arg):
            return ContextAwareFileStrategy(first_arg, args[1:], self.context)
        
        # Strategy 2: Module commands (test-fast, format, lint)
        if self._is_module_command(first_arg, args[1:]):
            return ContextAwareModuleStrategy(first_arg, args[1:], self.context)
        
        # Strategy 3: Direct passthrough (git, ls, echo)
        return PassthroughCommandStrategy(args, self.context)
```

### **Phase 2: Execution Strategies Implementation (Week 2)**

#### **Step 2.1: File Execution Strategy**
```python
# momo_cmd/strategies/file.py
class ContextAwareFileStrategy(ExecutionStrategy):
    def __init__(self, filename: str, args: list[str], context: WorkspaceContext):
        self.filename = filename
        self.args = args
        self.context = context
        
    def execute(self) -> bool:
        file_path = self._resolve_file_path()
        target_module = self._determine_target_module(file_path)
        
        if target_module:
            return self._execute_in_module_environment(file_path, target_module)
        else:
            return self._execute_standard(file_path)
            
    def _resolve_file_path(self) -> Path:
        """Resolve file path relative to current context"""
        file_path = Path(self.filename)
        if not file_path.is_absolute():
            file_path = self.context.cwd / file_path
        return file_path.resolve()
        
    def _determine_target_module(self, file_path: Path) -> Optional[str]:
        """Determine which module environment to use"""
        try:
            relative = file_path.relative_to(self.context.workspace_root)
            parts = relative.parts
            
            # Check if file is within module directory
            if len(parts) >= 4 and parts[0:3] == ('code', 'libs', 'python'):
                return parts[3]
                
        except ValueError:
            pass
            
        # Fallback to current module context
        return self.context.current_module
    
    def _execute_in_module_environment(self, file_path: Path, module: str) -> bool:
        """Execute file using module's environment (uv)"""
        module_info = self.context.get_module_info(module)
        if not module_info or not module_info.has_uv:
            return self._execute_standard(file_path)
            
        # Use uv environment for Python files
        if file_path.suffix == '.py':
            cmd = f"cd {module_info.path} && uv run python {file_path} {' '.join(self.args)}"
        else:
            cmd = f"cd {module_info.path} && {self._get_execution_command(file_path)}"
            
        return self._execute_shell_command(cmd)
```

#### **Step 2.2: Module Command Strategy**
```python
# momo_cmd/strategies/module.py
class ContextAwareModuleStrategy(ExecutionStrategy):
    def __init__(self, command: str, args: list[str], context: WorkspaceContext):
        self.command = command
        self.args = args
        self.context = context
        
    def execute(self) -> bool:
        # Determine target module
        if self.args:
            target_module = self.args[0]
            extra_args = self.args[1:]
        elif self.context.current_module:
            target_module = self.context.current_module
            extra_args = []
        else:
            return self._show_context_help()
            
        return self._execute_module_command(target_module, extra_args)
        
    def _execute_module_command(self, module: str, extra_args: list[str]) -> bool:
        """Execute command for specific module with fallback chain"""
        
        # Strategy 1: Try nx command
        nx_cmd = f"nx run {module}:{self.command}"
        if self._command_exists(nx_cmd):
            return self._execute_with_args(nx_cmd, extra_args)
            
        # Strategy 2: Try uv command in module directory
        module_info = self.context.get_module_info(module)
        if module_info and module_info.has_uv:
            uv_cmd = f"cd {module_info.path} && uv run {self.command}"
            if self._try_command(uv_cmd):
                return self._execute_with_args(uv_cmd, extra_args)
                
        # Strategy 3: Common command patterns
        return self._try_common_patterns(module, extra_args)
        
    def _try_common_patterns(self, module: str, extra_args: list[str]) -> bool:
        """Try common command patterns as fallbacks"""
        patterns = {
            'test-fast': f"cd {module} && uv run pytest tests/unit tests/e2e",
            'format': f"cd {module} && uv run ruff format .",
            'lint': f"cd {module} && uv run ruff check .",
            'typecheck': f"cd {module} && uv run pyright",
            'install': f"cd {module} && uv sync"
        }
        
        if self.command in patterns:
            cmd = patterns[self.command]
            return self._execute_with_args(cmd, extra_args)
            
        return False
```

#### **Step 2.3: Passthrough Strategy**
```python
# momo_cmd/strategies/passthrough.py  
class PassthroughCommandStrategy(ExecutionStrategy):
    def __init__(self, args: list[str], context: WorkspaceContext):
        self.args = args
        self.context = context
        
    def execute(self) -> bool:
        """Execute command with intelligent enhancements"""
        enhanced_args = self._enhance_command(self.args)
        cmd = ' '.join(enhanced_args)
        
        # Execute in workspace root for consistency
        return self._execute_shell_command(cmd, cwd=self.context.workspace_root)
        
    def _enhance_command(self, args: list[str]) -> list[str]:
        """Add intelligent enhancements to common commands"""
        
        if not args:
            return args
            
        # Git command enhancements
        if args[0] == 'git':
            if len(args) == 2 and args[1] == 'status':
                return args + ['--short', '--branch']
            if len(args) == 2 and args[1] == 'diff':
                return args + ['--stat']
                
        # Find command enhancements  
        if args[0] == 'find' and any('*.py' in arg for arg in args):
            return args + ['-not', '-path', '*/__pycache__/*', '-not', '-path', '*/.venv/*']
            
        return args
```

### **Phase 3: CLI Integration and Testing (Week 3)**

#### **Step 3.1: Simplified CLI Interface**
```python
# momo_cmd/cli.py
@click.command()
@click.argument('args', nargs=-1, required=True)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--dry-run', is_flag=True, help='Show what would be executed')
@click.option('--help-context', is_flag=True, help='Show context information')
def mom(args, verbose, dry_run, help_context):
    """Universal command interface - intelligently execute anything
    
    Examples:
        mom test.py                     # Execute Python file
        mom test-fast                   # Run test-fast for current module
        mom test-fast momo-agent        # Run test-fast for specific module  
        mom git status                  # Pass through to git
        mom scripts/benchmark.py        # Execute with correct environment
    """
    
    if help_context:
        context = WorkspaceContext()
        print(f"Workspace: {context.workspace_root}")
        print(f"Current module: {context.current_module or 'None'}")
        if context.current_module:
            module_info = context.get_module_info()
            print(f"Available commands: {', '.join(module_info.available_commands)}")
        return
        
    router = ContextAwareCommandRouter(verbose=verbose, dry_run=dry_run)
    success = router.route_and_execute(list(args))
    sys.exit(0 if success else 1)
```

#### **Step 3.2: Integration with momo-agent**
```python
# Update momo_agent/command_executor.py
from momo_cmd import ContextAwareCommandRouter

class UniversalAgentCommandExecutor:
    """Enhanced command executor using universal interface"""
    
    def __init__(self, working_directory: Path = None):
        self.working_directory = working_directory
        
    async def execute_command(
        self, 
        command: str, 
        context: AgentExecutionContext
    ) -> CommandResult:
        """Execute command through universal interface"""
        
        # Parse command into arguments
        args = shlex.split(command)
        
        # Create router with agent context
        original_cwd = Path.cwd()
        if self.working_directory:
            os.chdir(self.working_directory)
            
        try:
            router = ContextAwareCommandRouter(verbose=False)
            success = router.route_and_execute(args)
            
            return CommandResult(
                command=command,
                success=success,
                execution_time=time.time() - start_time,
                context=context
            )
        finally:
            os.chdir(original_cwd)
```

#### **Step 3.3: Comprehensive Testing Suite**
```python
# tests/test_universal_interface.py
class TestUniversalInterface:
    def test_file_execution_routing(self):
        """Test file execution detection and routing"""
        router = ContextAwareCommandRouter()
        
        # Python file execution
        strategy = router._classify_command(['test.py'])
        assert isinstance(strategy, ContextAwareFileStrategy)
        
        # TypeScript file execution
        strategy = router._classify_command(['build.ts'])
        assert isinstance(strategy, ContextAwareFileStrategy)
        
    def test_module_command_routing(self):
        """Test module command detection and routing"""
        router = ContextAwareCommandRouter()
        
        # Explicit module command
        strategy = router._classify_command(['test-fast', 'momo-agent'])
        assert isinstance(strategy, ContextAwareModuleStrategy)
        
        # Context-aware module command (mock context)
        with mock_context(current_module='momo-agent'):
            strategy = router._classify_command(['test-fast'])
            assert isinstance(strategy, ContextAwareModuleStrategy)
            
    def test_passthrough_routing(self):
        """Test passthrough command detection"""
        router = ContextAwareCommandRouter()
        
        strategy = router._classify_command(['git', 'status'])
        assert isinstance(strategy, PassthroughCommandStrategy)
        
    def test_context_awareness(self):
        """Test context detection and module environment usage"""
        # Test workspace root detection
        # Test module detection from various directories
        # Test file execution with correct environments
```

### **Phase 4: Integration and Documentation (Week 4)**

#### **Step 4.1: Update Module Integrations (Optional Transition)**
```bash
# Option 1: Update momo-agent to use new momo-cmd (recommended)
# Update momo_agent/command_executor.py to import from momo_cmd
# Keep momo-mom as fallback during transition

# Option 2: Keep existing momo-mom integrations
# Add momo-cmd as additional option for new agent workflows
# Gradual migration over time

# Update documentation to show both options
```

#### **Step 4.2: Update CLAUDE.md Files**
```markdown
# Update code/libs/python/momo-cmd/CLAUDE.md
# momo-cmd: Universal Command Interface

## Purpose
Context-aware, universal command interface that intelligently routes any command through a single entry point.

## Usage Patterns
- Direct file execution: `mom test.py`
- Module commands: `mom test-fast` (context-aware) or `mom test-fast module-name`
- Passthrough commands: `mom git status`
- Environment-aware: Automatically uses correct uv/nx environments

## Integration
- momo-agent: Uses UniversalAgentCommandExecutor
- momo-workflow: Universal command execution for workflow steps
```

#### **Step 4.3: Create Migration Documentation**
```markdown
# Migration Guide: momo-mom → momo-cmd

## Breaking Changes
- Module renamed: `momo-mom` → `momo-cmd`
- CLI interface simplified: Single `mom` command instead of subcommands
- Configuration changes: Less configuration required due to convention-based approach

## Migration Steps
1. Update imports: `from momo_mom` → `from momo_cmd`
2. Update command usage: Use universal interface patterns
3. Test context-aware behavior in module directories
```

## Success Metrics

### **Quantitative Metrics**
- **Universal Interface Adoption**: 100% of agent commands use `mom <pattern>`
- **Context Detection Accuracy**: >95% correct module/environment detection
- **Command Routing Success**: >98% successful command classification
- **Performance**: <50ms overhead for command routing and classification
- **Backward Compatibility**: 100% existing functionality preserved during transition

### **Qualitative Metrics**  
- **Agent Integration**: momo-agent successfully uses universal interface for all operations
- **Developer Experience**: Natural command patterns work intuitively from any directory
- **Environment Intelligence**: Files execute in correct Python/Node environments automatically
- **Documentation Quality**: Clear examples and migration guides available

### **Validation Tests**
- **Context Awareness**: Commands work correctly from workspace root and module directories
- **File Execution**: Python/TypeScript/Bash files execute with appropriate interpreters
- **Module Commands**: `test-fast`, `format`, `lint` work with and without module specification
- **Fallback Behavior**: Graceful degradation when nx commands unavailable

## Risks and Mitigations

### **Risk 1: Context Detection Failures**
**Probability**: Medium **Impact**: High  
**Mitigation**: Extensive testing across different directory structures. Clear error messages when context cannot be determined. Fallback to explicit module specification.

### **Risk 2: Performance Regression**
**Probability**: Low **Impact**: Medium  
**Mitigation**: Benchmark context detection and command classification. Cache context information. Optimize path resolution algorithms.

### **Risk 3: Agent Integration Complexity**
**Probability**: Medium **Impact**: High  
**Mitigation**: Comprehensive integration testing with momo-agent. Clear API documentation. Backward compatibility during transition period.

### **Risk 4: Module Dependency Issues**
**Probability**: Medium **Impact**: Medium  
**Mitigation**: Thorough testing of import updates. Automated search/replace validation. Staged rollout with rollback capability.

## Trade-offs Accepted

### **What We Gain**
- **Universal Interface**: Single command pattern for all operations
- **Context Awareness**: Automatic environment and module detection
- **Agent Optimization**: Predictable, discoverable command patterns
- **Developer Experience**: Natural workflows from any directory location
- **Reduced Configuration**: Convention-based execution reduces YAML configuration needs

### **What We Give Up**  
- **Module Creation Overhead**: Additional module to maintain alongside momo-mom
- **Potential Confusion**: Two command interfaces available during transition
- **Development Complexity**: Need to decide which module to enhance for new features
- **Testing Complexity**: More sophisticated testing required for context-aware behavior

**Rationale**: Creating a new module preserves existing functionality while enabling innovation. The benefits of a universal, context-aware command interface justify the additional maintenance overhead. This approach provides a safe migration path and preserves critical momo-mom functionality.

## Implementation Results

[To be filled during implementation]

## Lessons Learned

[To be filled after implementation]

## Next Steps

### **Immediate Actions (Phase 1)**
1. **Module Rename**: Execute momo-mom → momo-cmd rename across codebase
2. **Context System**: Implement WorkspaceContext and ModuleInfo classes
3. **Universal Router**: Create ContextAwareCommandRouter with strategy pattern
4. **Basic Integration**: Update momo-agent command executor integration

### **Short Term (Phase 2-3)**
1. **Strategy Implementation**: Complete all execution strategy classes
2. **CLI Simplification**: Replace complex subcommand structure with universal interface
3. **Testing Suite**: Comprehensive testing of context detection and command routing
4. **Documentation**: Update all module documentation and examples

### **Medium Term (Phase 4)**
1. **Migration Completion**: Full transition from momo-mom to momo-cmd
2. **Performance Optimization**: Optimize context detection and command classification
3. **Agent Integration**: Complete momo-agent and momo-workflow integration
4. **Monitoring**: Implement success metrics tracking and performance monitoring

## Related Documentation

- **[Implementation Plan](implementation-plan.md)** - Detailed step-by-step execution plan
- **[Migration Guide](migration-guide.md)** - Complete migration instructions
- **[Architecture Design](architecture.md)** - Technical architecture documentation
- **[Testing Strategy](testing-strategy.md)** - Comprehensive testing approach