# MomoAI Workflow Quick Start

## 🚀 Prevent Documentation Drift Forever

This system eliminates the need for periodic documentation cleanup by enforcing consistency at every step.

## Daily Workflow Commands

### Before Starting Any Task
```bash
# Always validate first
python scripts/workflow-validate.py
```

### For Structured Tasks  
```bash
# Create a workflow for documentation fixes
python scripts/task-workflow.py create documentation-fix

# Execute a workflow
python scripts/task-workflow.py execute <task_id>

# Check workflow status
python scripts/task-workflow.py status
```

### Quick Validation Checks
```bash
# Full system validation
python scripts/workflow-validate.py

# Test specific module
pnpm nx run momo-kb:test-fast

# Check Nx functionality
pnpm nx show projects
```

## Key Rules (Never Break These)

1. **🚫 Never edit README.md without validation**
2. **🚫 Never claim "COMPLETE" without passing tests**  
3. **🚫 Never create ADRs in modules - use `/docs/adr/` only**
4. **🚫 Never skip validation before committing**
5. **✅ Always run validation after making changes**

## Emergency Fix Protocol

If validation fails:
```bash
1. python scripts/workflow-validate.py  # See what's broken
2. Fix the specific issues reported
3. python scripts/workflow-validate.py  # Validate fixes
4. Repeat until all checks pass
```

## File Locations (Fixed Forever)

- **ADRs**: `/docs/adr/` only (modules reference these)
- **Architecture docs**: Use `code/` prefix for all paths
- **Module status**: Match reality (IN DEVELOPMENT vs COMPLETE)
- **Commands**: Verify they work before documenting

## Success Indicator

When this works correctly:
```
✅ ALL CHECKS PASSED - No documentation drift detected
```

This workflow system saves hours of periodic cleanup by maintaining consistency continuously.