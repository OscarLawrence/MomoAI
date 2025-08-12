# ADR-009 Implementation Plan: Universal Command Interface

## Implementation Overview

Create new `momo-cmd` module alongside existing `momo-mom` with a universal, context-aware command interface that intelligently routes any command through a single entry point `mom <anything>`.

**Duration**: 4 weeks  
**Scope**: New module creation, architecture design, agent integration, comprehensive testing  
**Preservation**: Existing `momo-mom` functionality remains unchanged

## Detailed Implementation Plan

### **Phase 1: New Module Creation and Core Architecture (Week 1)**

#### **Day 1: New Module Creation**

**Morning: Create New Module Structure**
```bash
# Step 1.1.1: Backup current state
git checkout -b adr-009-universal-command-interface
git add -A && git commit -m "Backup before momo-cmd creation (preserve momo-mom)"

# Step 1.1.2: Create new momo-cmd module using nx generator
nx g @nxlv/python:uv-project momo-cmd --directory=code/libs/python/momo-cmd

# Step 1.1.3: Create detailed module structure
mkdir -p code/libs/python/momo-cmd/momo_cmd/strategies
mkdir -p code/libs/python/momo-cmd/tests/unit
mkdir -p code/libs/python/momo-cmd/tests/e2e
mkdir -p code/libs/python/momo-cmd/scripts
mkdir -p code/libs/python/momo-cmd/benchmarks

# Step 1.1.4: Initialize package files
touch code/libs/python/momo-cmd/momo_cmd/__init__.py
touch code/libs/python/momo-cmd/momo_cmd/strategies/__init__.py
```

**Afternoon: Configure Module Dependencies**
```bash
# Step 1.1.5: Setup dependencies (similar to momo-mom but independent)
cd code/libs/python/momo-cmd

# Add core dependencies
uv add click
uv add pyyaml
uv add pytest pytest-asyncio pytest-cov
uv add ruff pyright

# Step 1.1.6: Configure pyproject.toml
cat > pyproject.toml << 'EOF'
[project]
name = "momo-cmd"
version = "0.1.0"
description = "Universal command interface for MomoAI"
authors = [{name = "Vincent", email = "vincent@vindao.ai"}]
dependencies = [
    "click",
    "pyyaml",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv.dev-dependencies]
pytest = "*"
pytest-asyncio = "*"
pytest-cov = "*"
ruff = "*"
pyright = "*"
EOF
```

**Evening: Validation**
```bash
# Step 1.1.7: Test module setup
cd code/libs/python/momo-cmd && uv sync

# Step 1.1.8: Verify no impact on momo-mom
cd ../momo-mom && uv run python -c "import momo_mom; print('✓ momo-mom unchanged')"

# Step 1.1.9: Test new module structure
cd ../momo-cmd && python -c "import momo_cmd; print('✓ momo-cmd created successfully')"
```

#### **Day 2: Context Detection System**

**Morning: WorkspaceContext Implementation**
```python
# Step 1.2.1: Create momo_cmd/context.py
"""
Workspace and module context detection system.
Automatically detects:
- Workspace root (nx.json, CLAUDE.md, .git markers)
- Current module when working within module directories
- Module information (uv, nx configuration, available commands)
"""

class WorkspaceContext:
    def __init__(self, cwd: Path = None):
        self.cwd = cwd or Path.cwd()
        self.workspace_root = self._find_workspace_root()
        self.current_module = self._detect_current_module()
        self._module_cache = {}  # Cache for module info
        
    def _find_workspace_root(self) -> Path:
        """Walk up directory tree to find workspace root"""
        current = self.cwd
        markers = ['nx.json', 'CLAUDE.md', '.git', 'package.json']
        
        while current != current.parent:
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
        return self.cwd
    
    def _detect_current_module(self) -> Optional[str]:
        """Detect if currently working within a module directory"""
        try:
            relative = self.cwd.relative_to(self.workspace_root)
            parts = relative.parts
            
            # Pattern: code/libs/python/module-name/...
            if len(parts) >= 4 and parts[0:3] == ('code', 'libs', 'python'):
                return parts[3]
                
            # Pattern: root-level module directories (momo-workflow/)
            if len(parts) >= 1 and parts[0].startswith('momo-'):
                # Verify it's actually a module directory
                potential_module = self.workspace_root / parts[0]
                if self._is_module_directory(potential_module):
                    return parts[0]
                    
        except ValueError:
            pass
            
        return None
    
    def _is_module_directory(self, path: Path) -> bool:
        """Check if directory is a valid module"""
        return any([
            (path / 'pyproject.toml').exists(),
            (path / 'project.json').exists(),
            (path / 'package.json').exists()
        ])
        
    def get_module_info(self, module: str = None) -> Optional['ModuleInfo']:
        """Get comprehensive module information"""
        target_module = module or self.current_module
        if not target_module:
            return None
            
        # Check cache first
        if target_module in self._module_cache:
            return self._module_cache[target_module]
            
        # Find module directory
        module_paths = [
            self.workspace_root / 'code' / 'libs' / 'python' / target_module,
            self.workspace_root / target_module,  # Root level modules
        ]
        
        for path in module_paths:
            if path.exists() and self._is_module_directory(path):
                module_info = ModuleInfo(target_module, path)
                self._module_cache[target_module] = module_info
                return module_info
        
        return None

class ModuleInfo:
    def __init__(self, name: str, path: Path):
        self.name = name
        self.path = path
        self.has_uv = (path / 'pyproject.toml').exists()
        self.has_nx = (path / 'project.json').exists()
        self.has_npm = (path / 'package.json').exists()
        self.available_commands = self._discover_commands()
        
    def _discover_commands(self) -> list[str]:
        """Auto-discover available commands for this module"""
        commands = set()
        
        # Check nx project.json targets
        if self.has_nx:
            try:
                import json
                with open(self.path / 'project.json') as f:
                    project_data = json.load(f)
                    targets = project_data.get('targets', {})
                    commands.update(targets.keys())
            except:
                pass
                
        # Check npm scripts
        if self.has_npm:
            try:
                import json
                with open(self.path / 'package.json') as f:
                    package_data = json.load(f)
                    scripts = package_data.get('scripts', {})
                    commands.update(scripts.keys())
            except:
                pass
                
        # Add common Python module commands
        if self.has_uv:
            common_commands = [
                'test-fast', 'test-all', 'format', 'lint', 
                'typecheck', 'install', 'benchmark'
            ]
            commands.update(common_commands)
            
        return sorted(list(commands))
```

**Afternoon: Module Information Discovery**
```python
# Step 1.2.2: Extend ModuleInfo with comprehensive discovery
def _discover_commands(self) -> list[str]:
    """Enhanced command discovery with validation"""
    commands = set()
    
    # Nx targets (highest priority)
    if self.has_nx:
        commands.update(self._get_nx_targets())
        
    # UV/Python commands  
    if self.has_uv:
        commands.update(self._get_python_commands())
        
    # NPM scripts
    if self.has_npm:
        commands.update(self._get_npm_scripts())
        
    # Validate commands actually work
    return self._validate_commands(list(commands))

def _validate_commands(self, commands: list[str]) -> list[str]:
    """Validate that commands are actually executable"""
    valid_commands = []
    
    for cmd in commands:
        if self._can_execute_command(cmd):
            valid_commands.append(cmd)
            
    return sorted(valid_commands)
```

**Evening: Context Testing**
```python
# Step 1.2.3: Create comprehensive context tests
# tests/unit/test_context.py
def test_workspace_root_detection():
    """Test workspace root detection from various directories"""
    # Test from repository root
    # Test from module directory
    # Test from subdirectory
    # Test fallback behavior
    
def test_module_detection():
    """Test current module detection"""
    # Test code/libs/python/module-name/ detection
    # Test root-level module detection  
    # Test subdirectory detection
    # Test non-module directory handling
    
def test_module_info_discovery():
    """Test module information discovery"""
    # Test nx target discovery
    # Test uv command discovery
    # Test npm script discovery
    # Test command validation
```

#### **Day 3: Universal Command Router**

**Morning: Router Architecture**
```python
# Step 1.3.1: Create momo_cmd/router.py
class ContextAwareCommandRouter:
    """Universal command router with intelligent classification"""
    
    def __init__(self, verbose=False, dry_run=False):
        self.context = WorkspaceContext()
        self.verbose = verbose
        self.dry_run = dry_run
        self.detectors = CommandDetectorRegistry()
        
    def route_and_execute(self, args: list[str]) -> bool:
        """Main entry point - intelligently route and execute any command"""
        if not args:
            return self._show_help()
            
        # Classify command type
        strategy = self._classify_command(args)
        
        if self.verbose:
            self._show_execution_plan(strategy, args)
            
        if self.dry_run:
            print(f"Would execute: {strategy.get_execution_preview()}")
            return True
            
        # Execute with comprehensive error handling
        try:
            return strategy.execute()
        except Exception as e:
            self._handle_execution_error(e, strategy, args)
            return False
    
    def _classify_command(self, args: list[str]) -> 'ExecutionStrategy':
        """Intelligent command classification using detector chain"""
        
        # Try each detector in priority order
        for detector in self.detectors.get_detectors():
            if detector.can_handle(args, self.context):
                return detector.create_strategy(args, self.context)
                
        # Fallback to passthrough
        return PassthroughCommandStrategy(args, self.context)
        
    def _show_execution_plan(self, strategy: 'ExecutionStrategy', args: list[str]):
        """Show detailed execution plan for debugging"""
        print(f"🎯 Strategy: {strategy.__class__.__name__}")
        print(f"📁 Context: {self.context.current_module or 'workspace root'}")
        print(f"📍 Working dir: {self.context.cwd}")
        print(f"⚡ Command preview: {strategy.get_execution_preview()}")
```

**Afternoon: Command Detection System**  
```python
# Step 1.3.2: Create momo_cmd/detectors.py
class CommandDetectorRegistry:
    """Registry of command detectors for intelligent routing"""
    
    def __init__(self):
        self.detectors = [
            FileExecutionDetector(),     # Highest priority
            ModuleCommandDetector(),     # Module-specific commands
            ToolchainCommandDetector(),  # nx, npm, cargo, etc.
            PassthroughDetector(),       # Lowest priority - catch-all
        ]
    
    def get_detectors(self) -> list['CommandDetector']:
        return self.detectors

class FileExecutionDetector(CommandDetector):
    """Detect direct file execution: mom test.py, mom build.ts"""
    
    def can_handle(self, args: list[str], context: WorkspaceContext) -> bool:
        if not args:
            return False
            
        first_arg = args[0]
        
        # Check if it's a file path (has extension)
        if '.' not in first_arg:
            return False
            
        # Check if file exists (resolve relative paths)
        file_path = self._resolve_path(first_arg, context.cwd)
        return file_path.exists() and file_path.is_file()
    
    def create_strategy(self, args: list[str], context: WorkspaceContext):
        return ContextAwareFileStrategy(args[0], args[1:], context)

class ModuleCommandDetector(CommandDetector):
    """Detect module commands: mom test-fast, mom format momo-agent"""
    
    COMMON_MODULE_COMMANDS = {
        'test-fast', 'test-all', 'format', 'lint', 'typecheck', 
        'install', 'benchmark', 'build', 'clean'
    }
    
    def can_handle(self, args: list[str], context: WorkspaceContext) -> bool:
        if not args:
            return False
            
        command = args[0]
        
        # Check if it's a known module command
        if command in self.COMMON_MODULE_COMMANDS:
            return True
            
        # Check if it's available in current module context
        if context.current_module:
            module_info = context.get_module_info()
            if module_info and command in module_info.available_commands:
                return True
                
        return False
    
    def create_strategy(self, args: list[str], context: WorkspaceContext):
        return ContextAwareModuleStrategy(args[0], args[1:], context)
```

**Evening: Strategy Base Classes**
```python
# Step 1.3.3: Create momo_cmd/strategies/base.py
class ExecutionStrategy(ABC):
    """Base class for command execution strategies"""
    
    def __init__(self, context: WorkspaceContext):
        self.context = context
        
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command and return success status"""
        pass
        
    @abstractmethod 
    def get_execution_preview(self) -> str:
        """Get human-readable preview of what will be executed"""
        pass
    
    def _execute_shell_command(
        self, 
        command: str, 
        cwd: Path = None,
        timeout: int = 300
    ) -> bool:
        """Execute shell command with comprehensive error handling"""
        import subprocess
        import shlex
        
        cwd = cwd or self.context.workspace_root
        
        try:
            # Use subprocess with proper shell handling
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                timeout=timeout,
                capture_output=False  # Stream output to console
            )
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"⏰ Command timed out after {timeout} seconds")
            return False
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            return False
```

#### **Day 4: Strategy Implementations - File Execution**

**Morning: File Execution Strategy**
```python
# Step 1.4.1: Create momo_cmd/strategies/file.py
class ContextAwareFileStrategy(ExecutionStrategy):
    """Execute files with automatic environment detection"""
    
    def __init__(self, filename: str, args: list[str], context: WorkspaceContext):
        super().__init__(context)
        self.filename = filename
        self.args = args
        
    def execute(self) -> bool:
        file_path = self._resolve_file_path()
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return False
            
        target_module = self._determine_target_module(file_path)
        
        if target_module:
            return self._execute_in_module_environment(file_path, target_module)
        else:
            return self._execute_standard(file_path)
            
    def get_execution_preview(self) -> str:
        file_path = self._resolve_file_path()
        target_module = self._determine_target_module(file_path)
        
        if target_module:
            return f"Execute {file_path.name} using {target_module} environment"
        else:
            return f"Execute {file_path.name} with standard interpreter"
    
    def _resolve_file_path(self) -> Path:
        """Resolve file path relative to current context"""
        file_path = Path(self.filename)
        if not file_path.is_absolute():
            file_path = self.context.cwd / file_path
        return file_path.resolve()
        
    def _determine_target_module(self, file_path: Path) -> Optional[str]:
        """Determine which module environment should be used"""
        try:
            relative = file_path.relative_to(self.context.workspace_root)
            parts = relative.parts
            
            # Check if file is within a module directory
            if len(parts) >= 4 and parts[0:3] == ('code', 'libs', 'python'):
                return parts[3]
                
        except ValueError:
            pass
            
        # Fallback to current module context if file is relative
        if not Path(self.filename).is_absolute():
            return self.context.current_module
            
        return None
    
    def _execute_in_module_environment(self, file_path: Path, module: str) -> bool:
        """Execute file using specific module's environment"""
        module_info = self.context.get_module_info(module)
        if not module_info:
            print(f"⚠️  Module {module} not found, falling back to standard execution")
            return self._execute_standard(file_path)
            
        # Build execution command with module context
        executor = self._get_file_executor(file_path)
        
        if module_info.has_uv and file_path.suffix == '.py':
            # Use uv environment for Python files
            cmd = f"cd {module_info.path} && uv run {executor.get_command(file_path, self.args)}"
        else:
            # Use standard execution but from module directory
            cmd = f"cd {module_info.path} && {executor.get_command(file_path.resolve(), self.args)}"
            
        print(f"🚀 Executing in {module} environment: {file_path.name}")
        return self._execute_shell_command(cmd)
    
    def _execute_standard(self, file_path: Path) -> bool:
        """Execute file with standard system interpreter"""
        executor = self._get_file_executor(file_path)
        cmd = executor.get_command(file_path, self.args)
        
        print(f"🚀 Executing: {file_path.name}")
        return self._execute_shell_command(cmd, cwd=file_path.parent)
    
    def _get_file_executor(self, file_path: Path) -> 'FileExecutor':
        """Get appropriate executor for file type"""
        executors = {
            '.py': PythonFileExecutor(),
            '.ts': TypeScriptFileExecutor(), 
            '.js': JavaScriptFileExecutor(),
            '.sh': BashFileExecutor(),
        }
        
        executor = executors.get(file_path.suffix)
        if executor:
            return executor
            
        # Try shebang detection
        return self._detect_from_shebang(file_path)
```

**Afternoon: File Executor Classes**
```python
# Step 1.4.2: Create file executor implementations
class FileExecutor(ABC):
    """Base class for file execution"""
    
    @abstractmethod
    def get_command(self, file_path: Path, args: list[str]) -> str:
        """Get shell command to execute this file"""
        pass

class PythonFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        args_str = ' '.join(shlex.quote(arg) for arg in args)
        return f"python {file_path} {args_str}".strip()

class TypeScriptFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        args_str = ' '.join(shlex.quote(arg) for arg in args)
        return f"npx tsx {file_path} {args_str}".strip()

class JavaScriptFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        args_str = ' '.join(shlex.quote(arg) for arg in args)
        return f"node {file_path} {args_str}".strip()

class BashFileExecutor(FileExecutor):
    def get_command(self, file_path: Path, args: list[str]) -> str:
        args_str = ' '.join(shlex.quote(arg) for arg in args)
        return f"bash {file_path} {args_str}".strip()
```

**Evening: File Execution Testing**
```python
# Step 1.4.3: Create comprehensive file execution tests
# tests/unit/test_file_execution.py
def test_python_file_execution():
    """Test Python file execution with environment detection"""
    # Test standard Python execution
    # Test uv environment usage in modules
    # Test relative path resolution
    
def test_typescript_file_execution():
    """Test TypeScript file execution"""
    # Test tsx execution
    # Test path resolution
    
def test_context_aware_environment_selection():
    """Test automatic environment selection based on file location"""
    # Test module environment detection
    # Test fallback to standard execution
```

#### **Day 5: Strategy Implementations - Module Commands**

**Morning: Module Command Strategy**
```python
# Step 1.5.1: Create momo_cmd/strategies/module.py
class ContextAwareModuleStrategy(ExecutionStrategy):
    """Execute module-specific commands with intelligent fallbacks"""
    
    def __init__(self, command: str, args: list[str], context: WorkspaceContext):
        super().__init__(context)
        self.command = command
        self.args = args
        
    def execute(self) -> bool:
        target_module, extra_args = self._determine_target_module()
        
        if not target_module:
            return self._show_context_help()
            
        return self._execute_module_command(target_module, extra_args)
        
    def get_execution_preview(self) -> str:
        target_module, extra_args = self._determine_target_module()
        if target_module:
            return f"Execute {self.command} for {target_module}"
        else:
            return f"Execute {self.command} (context-dependent)"
    
    def _determine_target_module(self) -> tuple[Optional[str], list[str]]:
        """Determine target module and remaining arguments"""
        
        # Case 1: Explicit module specified (mom test-fast momo-agent)
        if self.args:
            potential_module = self.args[0]
            
            # Check if first arg is actually a module name
            if self.context.get_module_info(potential_module):
                return potential_module, self.args[1:]
            else:
                # First arg might be command parameter, not module
                if self.context.current_module:
                    return self.context.current_module, self.args
                    
        # Case 2: Context-aware execution (mom test-fast from within module)
        if self.context.current_module:
            return self.context.current_module, self.args
            
        return None, self.args
    
    def _execute_module_command(self, module: str, extra_args: list[str]) -> bool:
        """Execute command for specific module with fallback chain"""
        
        print(f"🎯 Executing {self.command} for {module}")
        
        # Strategy 1: Try nx command (highest priority)
        if self._try_nx_command(module, extra_args):
            return True
            
        # Strategy 2: Try uv command in module directory
        if self._try_uv_command(module, extra_args):
            return True
            
        # Strategy 3: Try common command patterns
        if self._try_common_patterns(module, extra_args):
            return True
            
        print(f"❌ No execution strategy found for {self.command} in {module}")
        return False
    
    def _try_nx_command(self, module: str, extra_args: list[str]) -> bool:
        """Try executing as nx command"""
        cmd = f"nx run {module}:{self.command}"
        if extra_args:
            cmd += f" {' '.join(shlex.quote(arg) for arg in extra_args)}"
            
        # Quick check if command exists
        check_cmd = f"nx show project {module} | grep -q '{self.command}:'"
        check_result = subprocess.run(
            check_cmd, shell=True, capture_output=True, text=True
        )
        
        if check_result.returncode == 0:
            print(f"📦 Using nx: {cmd}")
            return self._execute_shell_command(cmd)
            
        return False
    
    def _try_uv_command(self, module: str, extra_args: list[str]) -> bool:
        """Try executing as uv command in module directory"""
        module_info = self.context.get_module_info(module)
        if not module_info or not module_info.has_uv:
            return False
            
        cmd = f"cd {module_info.path} && uv run {self.command}"
        if extra_args:
            cmd += f" {' '.join(shlex.quote(arg) for arg in extra_args)}"
            
        print(f"🐍 Using uv: {cmd}")
        return self._execute_shell_command(cmd)
    
    def _try_common_patterns(self, module: str, extra_args: list[str]) -> bool:
        """Try common command patterns as fallbacks"""
        module_info = self.context.get_module_info(module)
        if not module_info:
            return False
            
        patterns = {
            'test-fast': self._build_test_fast_command(module_info),
            'test-all': self._build_test_all_command(module_info),
            'format': self._build_format_command(module_info),
            'lint': self._build_lint_command(module_info),
            'typecheck': self._build_typecheck_command(module_info),
            'install': self._build_install_command(module_info),
            'benchmark': self._build_benchmark_command(module_info),
        }
        
        pattern_cmd = patterns.get(self.command)
        if pattern_cmd:
            if extra_args:
                pattern_cmd += f" {' '.join(shlex.quote(arg) for arg in extra_args)}"
                
            print(f"🔧 Using pattern: {pattern_cmd}")
            return self._execute_shell_command(pattern_cmd)
            
        return False
    
    def _build_test_fast_command(self, module_info: ModuleInfo) -> str:
        """Build test-fast command for module"""
        if module_info.has_uv:
            return f"cd {module_info.path} && uv run pytest tests/unit tests/e2e -v"
        else:
            return f"cd {module_info.path} && pytest tests/unit tests/e2e -v"
    
    def _build_format_command(self, module_info: ModuleInfo) -> str:
        """Build format command for module"""
        if module_info.has_uv:
            return f"cd {module_info.path} && uv run ruff format ."
        else:
            return f"cd {module_info.path} && ruff format ."
            
    # ... similar methods for other common commands
```

**Afternoon: Module Command Testing**
```python
# Step 1.5.2: Create module command tests
def test_context_aware_module_commands():
    """Test module command execution with context awareness"""
    # Test explicit module: mom test-fast momo-agent
    # Test context-aware: mom test-fast (from within module)
    # Test fallback chain: nx → uv → patterns
    
def test_common_command_patterns():
    """Test common command pattern execution"""
    # Test test-fast, format, lint patterns
    # Test with and without extra arguments
    # Test different module types (uv, nx, npm)
```

**Evening: Passthrough Strategy**
```python
# Step 1.5.3: Create momo_cmd/strategies/passthrough.py  
class PassthroughCommandStrategy(ExecutionStrategy):
    """Execute commands with intelligent enhancements"""
    
    def __init__(self, args: list[str], context: WorkspaceContext):
        super().__init__(context)
        self.args = args
        
    def execute(self) -> bool:
        enhanced_args = self._enhance_command(self.args)
        cmd = ' '.join(shlex.quote(arg) for arg in enhanced_args)
        
        print(f"🔗 Passthrough: {cmd}")
        return self._execute_shell_command(cmd, cwd=self.context.workspace_root)
        
    def get_execution_preview(self) -> str:
        enhanced_args = self._enhance_command(self.args)
        return f"Execute: {' '.join(enhanced_args)}"
    
    def _enhance_command(self, args: list[str]) -> list[str]:
        """Add intelligent enhancements to common commands"""
        if not args:
            return args
            
        # Git command enhancements
        if args[0] == 'git':
            return self._enhance_git_command(args)
            
        # Find command enhancements
        if args[0] == 'find':
            return self._enhance_find_command(args)
            
        # Directory listing enhancements
        if args[0] == 'ls' and len(args) == 1:
            return ['ls', '-la', '--color=auto']
            
        return args
    
    def _enhance_git_command(self, args: list[str]) -> list[str]:
        """Enhance git commands with useful flags"""
        if len(args) >= 2:
            subcommand = args[1]
            
            if subcommand == 'status' and len(args) == 2:
                return args + ['--short', '--branch']
            elif subcommand == 'diff' and len(args) == 2:
                return args + ['--stat']
            elif subcommand == 'log' and len(args) == 2:
                return args + ['--oneline', '--graph', '-10']
                
        return args
    
    def _enhance_find_command(self, args: list[str]) -> list[str]:
        """Enhance find commands to exclude common directories"""
        enhanced = args[:]
        
        if any('*.py' in arg for arg in args):
            enhanced.extend([
                '-not', '-path', '*/__pycache__/*',
                '-not', '-path', '*/.venv/*',
                '-not', '-path', '*/node_modules/*'
            ])
            
        return enhanced
```

#### **Day 6-7: Testing and Integration**

**Day 6: Comprehensive Testing Suite**
```python
# Step 1.6.1: Create comprehensive test suite
# tests/unit/test_universal_interface.py
class TestUniversalInterface:
    def test_command_classification(self):
        """Test command classification accuracy"""
        router = ContextAwareCommandRouter()
        
        # File execution
        assert isinstance(
            router._classify_command(['test.py']), 
            ContextAwareFileStrategy
        )
        
        # Module commands
        assert isinstance(
            router._classify_command(['test-fast', 'momo-agent']),
            ContextAwareModuleStrategy
        )
        
        # Passthrough
        assert isinstance(
            router._classify_command(['git', 'status']),
            PassthroughCommandStrategy
        )
    
    def test_context_awareness(self):
        """Test context-aware behavior"""
        # Mock different working directories
        # Test module detection
        # Test command behavior differences
        
    def test_execution_strategies(self):
        """Test all execution strategies work correctly"""
        # File execution with different interpreters
        # Module commands with fallback chains
        # Passthrough with enhancements
        
# Step 1.6.2: Integration tests
class TestMomoAgentIntegration:
    def test_agent_command_execution(self):
        """Test integration with momo-agent"""
        # Mock agent execution context
        # Test universal interface usage
        # Verify command results
```

**Day 7: CLI Integration and Final Testing**
```python
# Step 1.7.1: Create simplified CLI
# momo_cmd/cli.py - Final implementation
@click.command()
@click.argument('args', nargs=-1, required=True)
@click.option('--verbose', '-v', is_flag=True, help='Show execution details')
@click.option('--dry-run', is_flag=True, help='Show what would be executed')
@click.option('--context', is_flag=True, help='Show current context')
def mom(args, verbose, dry_run, context):
    """Universal command interface - execute anything intelligently
    
    Examples:
        mom test.py                     # Execute Python file  
        mom test-fast                   # Run test-fast for current module
        mom test-fast momo-agent        # Run test-fast for specific module
        mom git status                  # Enhanced git status
        mom scripts/benchmark.py        # Execute with module environment
    """
    
    if context:
        _show_context_info()
        return
        
    router = ContextAwareCommandRouter(verbose=verbose, dry_run=dry_run)
    success = router.route_and_execute(list(args))
    sys.exit(0 if success else 1)

def _show_context_info():
    """Show current workspace and module context"""
    ctx = WorkspaceContext()
    print(f"Workspace root: {ctx.workspace_root}")
    print(f"Current directory: {ctx.cwd}")
    print(f"Current module: {ctx.current_module or 'None'}")
    
    if ctx.current_module:
        module_info = ctx.get_module_info()
        if module_info:
            print(f"Module type: {'uv' if module_info.has_uv else 'standard'}")
            print(f"Available commands: {', '.join(module_info.available_commands)}")
```

### **Phase 2-4: Continuation Plan**

The remaining phases follow the same detailed step-by-step approach:

**Phase 2 (Week 2)**: Complete strategy implementations, enhanced error handling, performance optimization

**Phase 3 (Week 3)**: Full integration with momo-agent and momo-workflow, comprehensive testing, performance benchmarking  

**Phase 4 (Week 4)**: Documentation updates, migration guide, rollout and monitoring

## Implementation Checklist

### **Phase 1 Completion Criteria**
- [ ] Module successfully renamed from momo-mom to momo-cmd
- [ ] All imports updated across codebase
- [ ] WorkspaceContext correctly detects workspace root and current module
- [ ] ModuleInfo discovers available commands for modules
- [ ] ContextAwareCommandRouter classifies commands correctly
- [ ] File execution works with environment detection
- [ ] Module commands work with fallback chains
- [ ] Passthrough commands work with enhancements
- [ ] Basic CLI interface functional
- [ ] Comprehensive test suite passes

### **Success Validation Commands**
```bash
# Test basic functionality
mom --context                          # Show context info
mom scripts/demo.py                    # File execution
mom test-fast                          # Context-aware module command
mom git status                         # Enhanced passthrough

# Test from different directories
cd code/libs/python/momo-agent && mom test-fast
cd tests/unit && mom ../../scripts/test.py

# Performance test
time mom test-fast momo-agent          # Should be <50ms overhead
```

This implementation plan provides exhaustive step-by-step instructions for transforming momo-mom into the universal command interface momo-cmd, with detailed daily tasks and validation criteria.