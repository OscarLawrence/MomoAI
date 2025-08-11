# ADR-009 Architecture: Universal Command Interface

## Architecture Overview

The Universal Command Interface (`momo-cmd`) provides a single, intelligent entry point for all command execution needs in the MomoAI system. It operates alongside the existing `momo-mom` module, offering a convention-based, context-aware system that can execute any command through `mom <anything>` while preserving all existing functionality.

## Core Design Principles

### **1. Convention Over Configuration**
- Minimal YAML configuration required
- Intelligent detection based on file extensions, command patterns, and context
- Fallback chains provide robustness without explicit configuration

### **2. Context Awareness**
- Automatic detection of current module when working within module directories
- Environment-aware execution (uses correct uv/nx environments)
- Working directory sensitive behavior

### **3. Universal Interface**
- Single command pattern: `mom <anything>`
- Intelligent routing based on command classification
- Agent-optimized predictable behavior

### **4. Strategy Pattern Architecture**
- Pluggable execution strategies for different command types
- Clean separation of command detection from execution
- Extensible for future command types

### **5. Coexistence with momo-mom**
- Independent module that doesn't affect existing momo-mom functionality
- Optional migration path for integrations
- Both interfaces available during transition period

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Command Entry Point                      │
│                         mom <args...>                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                ContextAwareCommandRouter                        │
│  • Parse arguments                                              │
│  • Detect workspace context                                    │
│  • Classify command type                                       │
│  • Route to appropriate strategy                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
┌───────────▼─────────────┐    ┌────────▼──────────┐
│   Command Detectors     │    │ Workspace Context │
│                         │    │                   │
│ • FileExecutionDetector │    │ • Workspace root  │
│ • ModuleCommandDetector │    │ • Current module  │
│ • ToolchainDetector     │    │ • Module info     │
│ • PassthroughDetector   │    │ • Available cmds  │
└───────────┬─────────────┘    └───────────────────┘
            │
┌───────────▼─────────────┐
│   Execution Strategies  │
│                         │
│ ┌─────────────────────┐ │
│ │ ContextAwareFile    │ │  Execute files with environment detection
│ │ Strategy            │ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ ContextAwareModule  │ │  Execute module commands with fallbacks
│ │ Strategy            │ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ PassthroughCommand  │ │  Execute arbitrary commands with enhancements
│ │ Strategy            │ │
│ └─────────────────────┘ │
└─────────────────────────┘
            │
┌───────────▼─────────────┐
│     Command Execution   │
│                         │
│ • Shell command exec   │
│ • Environment handling │
│ • Error management     │
│ • Output formatting    │
└─────────────────────────┘
```

## Core Components

### **1. ContextAwareCommandRouter**

**Purpose**: Main orchestration component that routes commands to appropriate execution strategies.

**Key Responsibilities**:
- Parse command arguments
- Detect current workspace and module context  
- Classify command type using detector chain
- Route to appropriate execution strategy
- Handle execution errors and provide feedback

**Interface**:
```python
class ContextAwareCommandRouter:
    def __init__(self, verbose=False, dry_run=False):
        self.context = WorkspaceContext()
        self.detectors = CommandDetectorRegistry()
        
    def route_and_execute(self, args: list[str]) -> bool:
        """Main entry point for command execution"""
        
    def _classify_command(self, args: list[str]) -> ExecutionStrategy:
        """Classify command and return appropriate strategy"""
```

### **2. WorkspaceContext**

**Purpose**: Detect and provide workspace and module context information.

**Key Responsibilities**:
- Find workspace root directory
- Detect current module when working within module directories
- Provide module information (uv, nx configuration, available commands)
- Cache module information for performance

**Context Detection Algorithm**:
```python
def _find_workspace_root(self) -> Path:
    """Walk up directory tree looking for workspace markers"""
    markers = ['nx.json', 'CLAUDE.md', '.git', 'package.json']
    # Walk up from current directory until marker found

def _detect_current_module(self) -> Optional[str]:
    """Detect if working within a module directory"""
    # Pattern 1: code/libs/python/module-name/...
    # Pattern 2: root-level module (momo-workflow/)
    # Verify directory is actually a module
```

**Module Information Discovery**:
```python
class ModuleInfo:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path  
        self.has_uv = (path / 'pyproject.toml').exists()
        self.has_nx = (path / 'project.json').exists()
        self.available_commands = self._discover_commands()
        
    def _discover_commands(self) -> list[str]:
        """Auto-discover available commands"""
        # Check nx project.json targets
        # Check npm package.json scripts  
        # Add common Python module commands
        # Return sorted, deduplicated list
```

### **3. Command Detection System**

**Purpose**: Intelligent classification of commands into execution strategies.

**Detector Chain** (Priority Order):
1. **FileExecutionDetector**: Detects direct file execution (`mom test.py`)
2. **ModuleCommandDetector**: Detects module-specific commands (`mom test-fast`)
3. **ToolchainCommandDetector**: Detects toolchain commands (`mom nx run`)
4. **PassthroughDetector**: Catch-all for arbitrary commands (`mom git status`)

**Detection Interface**:
```python
class CommandDetector(ABC):
    @abstractmethod
    def can_handle(self, args: list[str], context: WorkspaceContext) -> bool:
        """Check if this detector can handle the command"""
        
    @abstractmethod
    def create_strategy(self, args: list[str], context: WorkspaceContext) -> ExecutionStrategy:
        """Create appropriate execution strategy"""
```

**FileExecutionDetector Logic**:
```python
def can_handle(self, args: list[str], context: WorkspaceContext) -> bool:
    if not args or '.' not in args[0]:
        return False
        
    file_path = self._resolve_path(args[0], context.cwd)
    return file_path.exists() and file_path.is_file()
```

**ModuleCommandDetector Logic**:
```python
def can_handle(self, args: list[str], context: WorkspaceContext) -> bool:
    if not args:
        return False
        
    command = args[0]
    
    # Check against known module commands
    if command in COMMON_MODULE_COMMANDS:
        return True
        
    # Check if available in current module
    if context.current_module:
        module_info = context.get_module_info()
        return module_info and command in module_info.available_commands
        
    return False
```

### **4. Execution Strategies**

**Purpose**: Execute commands using different approaches based on command type.

**Strategy Hierarchy**:
```python
class ExecutionStrategy(ABC):
    """Base class for all execution strategies"""
    
    def __init__(self, context: WorkspaceContext):
        self.context = context
        
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command and return success status"""
        
    @abstractmethod
    def get_execution_preview(self) -> str:
        """Get preview of what will be executed"""
```

#### **ContextAwareFileStrategy**

**Purpose**: Execute files with automatic environment detection and interpreter selection.

**Key Features**:
- Automatic interpreter detection based on file extension
- Module environment usage for files within modules
- Shebang detection for custom interpreters
- Relative path resolution

**Execution Flow**:
```python
def execute(self) -> bool:
    file_path = self._resolve_file_path()
    target_module = self._determine_target_module(file_path)
    
    if target_module:
        return self._execute_in_module_environment(file_path, target_module)
    else:
        return self._execute_standard(file_path)
```

**Environment Detection**:
```python
def _determine_target_module(self, file_path: Path) -> Optional[str]:
    """Determine which module environment to use"""
    
    # Check if file is within a module directory
    try:
        relative = file_path.relative_to(self.context.workspace_root)
        if relative.parts[0:3] == ('code', 'libs', 'python'):
            return relative.parts[3]  # module name
    except ValueError:
        pass
        
    # Fallback to current module context
    return self.context.current_module
```

**Module Environment Execution**:
```python
def _execute_in_module_environment(self, file_path: Path, module: str) -> bool:
    """Execute file using module's uv environment"""
    module_info = self.context.get_module_info(module)
    
    if module_info.has_uv and file_path.suffix == '.py':
        cmd = f"cd {module_info.path} && uv run python {file_path} {args}"
    else:
        cmd = f"cd {module_info.path} && {standard_execution_command}"
        
    return self._execute_shell_command(cmd)
```

#### **ContextAwareModuleStrategy**

**Purpose**: Execute module-specific commands with intelligent fallback chains.

**Key Features**:
- Context-aware module detection (explicit or current module)
- Multi-tier fallback chain (nx → uv → common patterns)
- Command validation and existence checking
- Argument forwarding

**Module Resolution**:
```python
def _determine_target_module(self) -> tuple[Optional[str], list[str]]:
    """Determine target module and remaining arguments"""
    
    # Case 1: Explicit module (mom test-fast momo-agent)
    if self.args and self.context.get_module_info(self.args[0]):
        return self.args[0], self.args[1:]
        
    # Case 2: Context-aware (mom test-fast from within module)
    if self.context.current_module:
        return self.context.current_module, self.args
        
    return None, self.args
```

**Fallback Chain Execution**:
```python
def _execute_module_command(self, module: str, extra_args: list[str]) -> bool:
    """Execute with comprehensive fallback chain"""
    
    # Strategy 1: Try nx command (highest priority)
    if self._try_nx_command(module, extra_args):
        return True
        
    # Strategy 2: Try uv command in module directory
    if self._try_uv_command(module, extra_args):
        return True
        
    # Strategy 3: Try common command patterns
    if self._try_common_patterns(module, extra_args):
        return True
        
    return False
```

**Common Pattern Examples**:
```python
COMMON_PATTERNS = {
    'test-fast': 'uv run pytest tests/unit tests/e2e -v',
    'format': 'uv run ruff format .',
    'lint': 'uv run ruff check .',
    'typecheck': 'uv run pyright',
    'install': 'uv sync',
    'benchmark': 'uv run python benchmarks/performance_benchmarks.py'
}
```

#### **PassthroughCommandStrategy**

**Purpose**: Execute arbitrary commands with intelligent enhancements.

**Key Features**:
- Direct command execution with minimal modification
- Intelligent enhancements for common commands
- Working directory management
- Command validation and safety checks

**Command Enhancement Examples**:
```python
def _enhance_command(self, args: list[str]) -> list[str]:
    """Add intelligent enhancements"""
    
    if args[0] == 'git':
        return self._enhance_git_command(args)
    elif args[0] == 'find':
        return self._enhance_find_command(args)
    elif args[0] == 'ls' and len(args) == 1:
        return ['ls', '-la', '--color=auto']
        
    return args

def _enhance_git_command(self, args: list[str]) -> list[str]:
    """Add useful flags to git commands"""
    if len(args) == 2:
        enhancements = {
            'status': ['--short', '--branch'],
            'diff': ['--stat'],
            'log': ['--oneline', '--graph', '-10']
        }
        return args + enhancements.get(args[1], [])
    return args
```

## Data Flow

### **1. Command Entry Flow**

```
User Input: mom test.py arg1 arg2
    ↓
CLI Parser: ['test.py', 'arg1', 'arg2']
    ↓
ContextAwareCommandRouter:
    ↓
WorkspaceContext Detection:
    • workspace_root: /path/to/MomoAI-nx
    • current_module: momo-agent (if in module dir)
    • cwd: /path/to/current/directory
    ↓
Command Classification:
    • FileExecutionDetector.can_handle(['test.py', 'arg1', 'arg2']) → True
    ↓
Strategy Creation:
    • ContextAwareFileStrategy('test.py', ['arg1', 'arg2'], context)
    ↓
Execution:
    • file_path: /resolved/path/to/test.py
    • target_module: momo-agent (detected from path)
    • execution: cd momo-agent && uv run python test.py arg1 arg2
```

### **2. Context-Aware Module Command Flow**

```
User Input: mom test-fast (from within momo-agent directory)
    ↓
Context Detection:
    • current_module: momo-agent
    • module_info: ModuleInfo(has_uv=True, available_commands=[...])
    ↓
Command Classification:
    • ModuleCommandDetector.can_handle(['test-fast']) → True
    ↓
Strategy Execution:
    • target_module: momo-agent (from context)
    • fallback_chain: nx → uv → patterns
    • execution: nx run momo-agent:test-fast || cd momo-agent && uv run pytest tests/unit tests/e2e
```

## Performance Considerations

### **1. Context Detection Optimization**

**Caching Strategy**:
```python
class WorkspaceContext:
    def __init__(self):
        self._module_cache = {}  # Cache module info
        self._workspace_root_cache = None
        
    def get_module_info(self, module: str) -> ModuleInfo:
        if module in self._module_cache:
            return self._module_cache[module]
        # ... compute and cache
```

**Path Resolution**:
- Cache workspace root after first detection
- Minimize filesystem operations through intelligent path handling
- Use relative path calculations instead of repeated directory traversal

### **2. Command Classification Performance**

**Detector Ordering**:
- Most specific detectors first (FileExecution)
- Most common detectors prioritized (ModuleCommand)
- Expensive detectors last (PassthroughCommand)

**Early Termination**:
```python
def _classify_command(self, args: list[str]) -> ExecutionStrategy:
    for detector in self.detectors.get_detectors():
        if detector.can_handle(args, self.context):
            return detector.create_strategy(args, self.context)
    # First match wins - no need to check remaining detectors
```

### **3. Execution Optimization**

**Command Existence Checking**:
```python
def _command_exists(self, command: str) -> bool:
    """Fast command existence check"""
    try:
        subprocess.run(command.split()[0], capture_output=True, timeout=1)
        return True
    except:
        return False
```

**Subprocess Optimization**:
- Stream output instead of capturing for large outputs
- Use appropriate shell settings for command type
- Implement timeout protection for all executions

## Error Handling

### **1. Context Detection Errors**

**Workspace Root Not Found**:
- Fallback to current working directory
- Log warning but continue execution
- Provide clear error message to user

**Module Detection Ambiguity**:
- Prefer explicit module specification over context
- Provide suggestion when module ambiguous
- Show available modules for user guidance

### **2. Command Execution Errors**

**File Not Found**:
```python
def execute(self) -> bool:
    file_path = self._resolve_file_path()
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        self._suggest_similar_files()
        return False
```

**Command Execution Failure**:
```python
def _execute_shell_command(self, command: str) -> bool:
    try:
        result = subprocess.run(command, shell=True, timeout=300)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        return False
```

**Fallback Chain Exhaustion**:
```python
def _execute_module_command(self, module: str, args: list[str]) -> bool:
    for strategy in [self._try_nx, self._try_uv, self._try_patterns]:
        if strategy(module, args):
            return True
            
    print(f"❌ No execution strategy found for {self.command} in {module}")
    self._show_available_commands(module)
    return False
```

## Extension Points

### **1. New Command Detectors**

```python
class CustomDetector(CommandDetector):
    def can_handle(self, args: list[str], context: WorkspaceContext) -> bool:
        # Custom detection logic
        
    def create_strategy(self, args: list[str], context: WorkspaceContext):
        return CustomStrategy(args, context)

# Register with detection system
detectors.register(CustomDetector())
```

### **2. New Execution Strategies**

```python
class CustomStrategy(ExecutionStrategy):
    def execute(self) -> bool:
        # Custom execution logic
        
    def get_execution_preview(self) -> str:
        # Preview description
```

### **3. New File Executors**

```python
class RustFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        return f"cargo run --bin {file_path.stem} -- {' '.join(args)}"

# Register in file strategy
file_executors['.rs'] = RustFileExecutor()
```

This architecture provides a robust, extensible foundation for the universal command interface while maintaining high performance and clear separation of concerns.