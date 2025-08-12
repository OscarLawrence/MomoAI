# Migration Guide: Creating momo-cmd alongside momo-mom

## Migration Overview

This guide covers creating the new `momo-cmd` module alongside existing `momo-mom`, implementing the universal command interface while preserving all existing functionality. This approach provides a safe transition path.

**Migration Duration**: 4 weeks  
**Breaking Changes**: No - momo-mom preserved  
**Backward Compatibility**: Full - both modules coexist

## Pre-Migration Checklist

### **1. Backup Current State**
```bash
# Create migration branch
git checkout -b adr-009-universal-command-interface
git add -A && git commit -m "Backup before momo-cmd creation (preserve momo-mom)"

# Tag current state for easy rollback
git tag pre-momo-cmd-creation
```

### **2. Verify Current momo-mom Dependencies**
```bash
# Find all momo-mom dependencies (these will remain unchanged)
grep -r "momo_mom" . --exclude-dir=.git --exclude-dir=node_modules
grep -r "momo-mom" . --exclude-dir=.git --exclude-dir=node_modules

# Expected locations (to remain as-is):
# - code/libs/python/momo-agent/momo_agent/command_executor.py (optional migration)
# - code/libs/python/momo-workflow/momo_workflow/commands.py (optional migration)
# - Any scripts or configuration files (will continue working)
```

### **3. Test Current Functionality**
```bash
# Test existing momo-mom commands
cd code/libs/python/momo-mom
uv run pytest tests/ -v

# Test agent integration
cd ../momo-agent
uv run pytest tests/unit/test_command_executor.py -v
```

## Phase 1: New Module Creation (Week 1)

### **Step 1: Create New momo-cmd Module**

```bash
# 1.1 Create new module using nx generator (preserves momo-mom)
nx g @nxlv/python:uv-project momo-cmd --directory=code/libs/python/momo-cmd

# 1.2 Create module structure
mkdir -p code/libs/python/momo-cmd/momo_cmd/strategies
mkdir -p code/libs/python/momo-cmd/tests/{unit,e2e}
mkdir -p code/libs/python/momo-cmd/{scripts,benchmarks}

# 1.3 Initialize package files
touch code/libs/python/momo-cmd/momo_cmd/__init__.py
touch code/libs/python/momo-cmd/momo_cmd/strategies/__init__.py
```

### **Step 2: Configure Dependencies**

```bash
# 2.1 Setup independent dependencies
cd code/libs/python/momo-cmd
uv add click pyyaml
uv add --dev pytest pytest-asyncio pytest-cov ruff pyright

# 2.2 No global updates needed - new module is independent
# momo-mom remains completely unchanged
```

### **Step 3: Validation**

```bash
# 3.1 Test new module creation
cd code/libs/python/momo-cmd && uv sync
python -c "import momo_cmd; print('✓ momo-cmd created')"

# 3.2 Verify momo-mom unchanged
cd ../momo-mom && uv run python -c "import momo_mom; print('✓ momo-mom preserved')"

# 3.3 Verify both modules coexist
cd ../.. && python -c "import sys; sys.path.append('python/momo-mom'); sys.path.append('python/momo-cmd'); import momo_mom, momo_cmd; print('✓ Both modules available')"
```

## Phase 2: Architecture Migration (Week 2)

### **Step 4: Create New Architecture Files**

```bash
# 4.1 Create new module structure
mkdir -p code/libs/python/momo-cmd/momo_cmd/strategies
touch code/libs/python/momo-cmd/momo_cmd/context.py
touch code/libs/python/momo-cmd/momo_cmd/router.py
touch code/libs/python/momo-cmd/momo_cmd/detectors.py
touch code/libs/python/momo-cmd/momo_cmd/strategies/__init__.py
touch code/libs/python/momo-cmd/momo_cmd/strategies/base.py
touch code/libs/python/momo-cmd/momo_cmd/strategies/file.py
touch code/libs/python/momo-cmd/momo_cmd/strategies/module.py
touch code/libs/python/momo-cmd/momo_cmd/strategies/passthrough.py
```

### **Step 5: Implement Core Components** 

Follow the detailed implementation from the implementation-plan.md:

1. **WorkspaceContext**: Workspace and module detection
2. **ContextAwareCommandRouter**: Universal command routing  
3. **ExecutionStrategy**: Strategy pattern for command execution
4. **CommandDetector**: Intelligent command classification

### **Step 6: Update CLI Interface**

**Before (momo-mom):**
```python
# Multiple subcommands
@click.group()
def main():
    pass

@main.command()
def test(target, args):
    pass

@main.command() 
def script(script_name, args):
    pass
```

**After (momo-cmd):**
```python
# Single universal command
@click.command()
@click.argument('args', nargs=-1, required=True)
def mom(args, verbose=False, dry_run=False):
    router = ContextAwareCommandRouter(verbose, dry_run)
    success = router.route_and_execute(list(args))
    sys.exit(0 if success else 1)
```

## Phase 3: Integration Updates (Week 3)

### **Step 7: Optional momo-agent Integration**

**Option 1: Keep Existing (Recommended Initially)**
```python
# momo_agent/command_executor.py - No changes
from momo_mom import CommandExecutor

class MomAgentCommandExecutor:
    def __init__(self):
        self.executor = CommandExecutor(config)
        
    def execute_command(self, command, target, args):
        return self.executor.execute_command(command, target, args)

# momo-mom continues to work as before
```

**Option 2: Add momo-cmd Support (Future Enhancement)**
```python
# momo_agent/command_executor.py - Enhanced version
from momo_mom import CommandExecutor
from momo_cmd import ContextAwareCommandRouter

class HybridCommandExecutor:
    def __init__(self, use_universal_interface=False):
        self.use_universal = use_universal_interface
        self.mom_executor = CommandExecutor(config)  # Fallback
        
    async def execute_command(self, command_string, context):
        if self.use_universal:
            # Use new momo-cmd universal interface
            args = shlex.split(command_string)
            router = ContextAwareCommandRouter()
            success = router.route_and_execute(args)
            return CommandResult(success=success, command=command_string)
        else:
            # Use existing momo-mom interface
            return self.mom_executor.execute_command(command, target, args)
```

### **Step 8: Update momo-workflow Integration**

**Before:**
```python
# momo_workflow/commands.py
from momo_mom import CommandExecutor

def execute_workflow_command(command, target):
    executor = CommandExecutor(config)
    return executor.execute_command(command, target, [])
```

**After:**
```python
# momo_workflow/commands.py
from momo_cmd import ContextAwareCommandRouter

def execute_workflow_command(command_args):
    router = ContextAwareCommandRouter()
    return router.route_and_execute(command_args)
```

### **Step 9: Update Configuration Files**

**Before (mom.yaml):**
```yaml
command_name: "mom"
commands:
  test:
    pattern: "nx run {target}:test"
    fallback: "cd {target} && uv run pytest"
  format:
    pattern: "nx run {target}:format"
    fallback: "cd {target} && uv run ruff format ."
```

**After (mom.yaml - simplified):**
```yaml
# Much less configuration needed due to convention-based approach
command_name: "mom"
execution:
  auto_reset_on_cache_failure: true
  retry_count: 2
  timeout: 300
```

## Phase 4: Testing and Validation (Week 4)

### **Step 10: Command Interface Changes**

| **Old Command** | **New Command** | **Notes** |
|----------------|----------------|-----------|
| `mom test module-name` | `mom test-fast module-name` | More explicit |
| `mom script test.py` | `mom test.py` | Direct file execution |
| `mom run git status` | `mom git status` | Simplified passthrough |

### **Step 11: Context-Aware Behavior Testing**

```bash
# Test from repository root
mom test-fast momo-agent                    # Explicit module
mom code/libs/python/momo-agent/test.py     # File with environment detection

# Test from within module (cd code/libs/python/momo-agent)
mom test-fast                              # Auto-detects momo-agent
mom scripts/demo.py                        # Uses momo-agent's uv environment
mom format                                 # Formats current module

# Test from subdirectory (cd code/libs/python/momo-agent/tests)
mom test-fast                              # Still detects momo-agent
mom ../scripts/benchmark.py               # Uses correct environment
```

### **Step 12: Performance Validation**

```bash
# Test command routing overhead
time mom --dry-run test-fast momo-agent    # Should be <50ms

# Test context detection speed  
time mom --context                         # Should be <100ms

# Test file execution
time mom scripts/demo.py                   # Compare to direct python execution
```

## Breaking Changes and Compatibility

### **Breaking Changes**

1. **CLI Interface**: Single `mom` command instead of subcommands
2. **Import Paths**: `momo_mom` → `momo_cmd`
3. **Configuration**: Simplified YAML configuration
4. **API**: New API for programmatic usage

### **Temporary Compatibility**

During migration, create compatibility wrapper:

```python
# momo_cmd/legacy.py
def handle_legacy_subcommand(subcommand, args):
    """Handle old subcommand patterns"""
    legacy_mapping = {
        'test': ['test-fast'] + args,
        'script': [args[0]] + args[1:] if args else [],
        'run': args,
    }
    
    new_args = legacy_mapping.get(subcommand, args)
    router = ContextAwareCommandRouter()
    return router.route_and_execute(new_args)
```

### **Migration Script**

```bash
#!/bin/bash
# migrate-commands.sh - Update scripts using old command patterns

# Find and update script files
find . -name "*.py" -exec grep -l "mom test" {} \; | while read file; do
    sed -i 's/mom test /mom test-fast /g' "$file"
    echo "Updated: $file"
done

find . -name "*.py" -exec grep -l "mom script" {} \; | while read file; do
    sed -i 's/mom script \([^"]*\)/mom \1/g' "$file"
    echo "Updated: $file"
done

find . -name "*.py" -exec grep -l "mom run" {} \; | while read file; do
    sed -i 's/mom run //g' "$file"
    echo "Updated: $file"
done
```

## Rollback Plan

### **Emergency Rollback** 
```bash
# Rollback to pre-migration state
git checkout pre-momo-cmd-migration
git reset --hard
```

### **Selective Rollback**
```bash
# Rollback specific components
git checkout HEAD~N -- code/libs/python/momo-cmd  # Rollback module
git checkout HEAD~N -- code/libs/python/momo-agent/momo_agent/command_executor.py  # Rollback integration
```

### **Partial Migration Rollback**
```bash
# Keep new architecture but restore old naming
mv code/libs/python/momo-cmd code/libs/python/momo-mom
mv code/libs/python/momo-mom/momo_cmd code/libs/python/momo-mom/momo_mom
# Reverse import updates...
```

## Post-Migration Validation

### **Functionality Tests**
```bash
# Test all major functionality
mom test.py                           # File execution
mom test-fast momo-agent              # Module commands
mom git status                        # Passthrough
mom --context                         # Context awareness

# Test from different directories
cd code/libs/python/momo-agent
mom test-fast                         # Context-aware execution
mom scripts/demo.py                   # Environment detection

# Test integration
cd code/libs/python/momo-agent
uv run pytest tests/unit/test_command_executor.py -v
```

### **Performance Tests**  
```bash
# Command routing speed
time mom --dry-run test-fast momo-agent

# Context detection speed
time mom --context

# End-to-end execution time
time mom test-fast momo-agent
```

### **Integration Tests**
```bash
# Test momo-agent integration
cd code/libs/python/momo-agent
uv run python -c "from momo_agent.command_executor import UniversalAgentCommandExecutor; print('✓')"

# Test momo-workflow integration  
cd code/libs/python/momo-workflow
uv run python -c "from momo_workflow.commands import execute_workflow_command; print('✓')"
```

## Success Criteria

- [ ] All tests pass after migration
- [ ] Command routing works correctly (>98% accuracy)
- [ ] Context detection works (>95% accuracy)  
- [ ] Performance overhead <50ms
- [ ] All integrations updated and working
- [ ] Documentation updated
- [ ] Migration validated in test environment

## Troubleshooting

### **Common Issues**

**Import Errors:**
```bash
# If imports fail, check for missed renames
grep -r "momo_mom" . --exclude-dir=.git
# Fix any remaining references
```

**Context Detection Issues:**
```bash
# Test context detection manually
cd problematic/directory
python -c "from momo_cmd.context import WorkspaceContext; ctx = WorkspaceContext(); print(f'Root: {ctx.workspace_root}'); print(f'Module: {ctx.current_module}')"
```

**Command Classification Issues:**
```bash
# Test command classification
python -c "from momo_cmd.router import ContextAwareCommandRouter; router = ContextAwareCommandRouter(); print(router._classify_command(['test.py']).__class__.__name__)"
```

**Performance Issues:**
```bash
# Profile slow operations
python -m cProfile -c "from momo_cmd.router import ContextAwareCommandRouter; router = ContextAwareCommandRouter(); router.route_and_execute(['--context'])"
```

This migration guide provides comprehensive instructions for safely transitioning from momo-mom to momo-cmd with full validation and rollback procedures.