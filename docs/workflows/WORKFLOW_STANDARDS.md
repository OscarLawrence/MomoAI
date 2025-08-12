# MomoAI Workflow Standards

## Overview

This document establishes structured workflow standards to prevent documentation drift and ensure consistency across all MomoAI development tasks.

## Core Principles

### 1. Structured Task Execution
- Every significant task must follow a defined workflow
- All steps must be documented and validated
- Progress must be tracked and verifiable
- Documentation must be updated atomically with code changes

### 2. Automated Validation
- Pre-commit validation prevents inconsistent states
- Post-task validation ensures completeness
- Continuous monitoring detects drift early
- Self-healing where possible

### 3. Documentation Governance
- Single source of truth for architectural decisions (ADRs in `/docs/adr/`)
- Module documentation references global ADRs
- Status claims must match reality (automated verification)
- Path references must be accurate and current

## Workflow Categories

### Documentation Tasks
**Purpose**: Fix documentation inconsistencies, update references, maintain accuracy

**Required Steps**:
1. **Validation**: Run `python scripts/workflow-validate.py`
2. **Analysis**: Identify specific inconsistencies
3. **Fix Implementation**: Make targeted corrections
4. **Cross-Reference Update**: Update all related references
5. **Final Validation**: Ensure no new issues introduced

**Exit Criteria**: All validation checks pass

### Module Development
**Purpose**: Develop new modules or enhance existing ones

**Required Steps**:
1. **Environment Setup**: Initialize development environment
2. **Implementation**: Write core functionality
3. **Code Quality**: Format, lint, type-check
4. **Testing**: Comprehensive test suite execution
5. **Documentation Update**: Update all relevant documentation
6. **Integration Validation**: Ensure system-wide compatibility

**Exit Criteria**: Tests pass, documentation accurate, type-safe code

### Architecture Changes
**Purpose**: Make system-wide architectural decisions

**Required Steps**:
1. **Research**: Comprehensive analysis and benchmarking
2. **ADR Creation**: Document architectural decision
3. **Implementation**: Execute the architectural change
4. **Migration**: Update existing components
5. **Documentation Cascade**: Update all affected documentation
6. **Validation**: Ensure system integrity

**Exit Criteria**: ADR complete, implementation functional, documentation consistent

## Validation Framework

### Pre-Task Validation
```bash
# Always run before starting any task
python scripts/workflow-validate.py
```

### During Task Execution
- Use structured workflows: `python scripts/task-workflow.py execute <task_id>`
- Validate each step before proceeding
- Document all changes and decisions

### Post-Task Validation
```bash
# Always run after completing any task
python scripts/workflow-validate.py
```

## Common Anti-Patterns

### ❌ What NOT to Do

1. **Direct Documentation Editing**: Never edit README.md, CLAUDE.md, or ADRs without workflow validation
2. **Status Claims Without Verification**: Never mark modules as "COMPLETE" without passing all tests
3. **Path References Without Verification**: Never reference paths without confirming they exist
4. **ADR Conflicts**: Never create new ADRs without checking for numbering conflicts
5. **Skipping Validation**: Never commit changes without running validation

### ✅ What TO Do

1. **Use Structured Workflows**: Always use the workflow system for significant changes
2. **Verify Before Claim**: Test and validate before updating status documentation
3. **Global ADR Management**: Keep all ADRs in `/docs/adr/` with module references
4. **Atomic Updates**: Update documentation and code together
5. **Continuous Validation**: Run validation frequently during development

## Workflow Scripts

### `scripts/workflow-validate.py`
**Purpose**: Comprehensive system validation
**Usage**: `python scripts/workflow-validate.py`
**Checks**:
- Architecture documentation consistency
- Module status accuracy
- ADR conflict detection
- Nx functionality
- Project structure integrity

### `scripts/task-workflow.py`
**Purpose**: Structured task execution management
**Usage**: 
```bash
python scripts/task-workflow.py create <template>
python scripts/task-workflow.py execute <task_id>
python scripts/task-workflow.py status
```

## Integration with Development Process

### Pre-Commit Hooks (Recommended)
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
python scripts/workflow-validate.py || {
    echo "❌ Validation failed - commit blocked"
    echo "Run workflow validation and fix issues before committing"
    exit 1
}
```

### CI/CD Integration
- Run validation in all CI pipelines
- Block merges if validation fails
- Generate validation reports for PRs

### Regular Maintenance
- Weekly validation runs to catch drift
- Quarterly workflow standard reviews
- Annual workflow optimization

## Emergency Procedures

### When Validation Fails
1. **Stop Development**: Do not proceed until validation passes
2. **Analyze Issues**: Review validation report carefully
3. **Fix Systematically**: Address issues in order of severity
4. **Re-validate**: Ensure all issues resolved
5. **Document Lessons**: Update workflow standards if needed

### When Workflows Are Broken
1. **Use Manual Checklist**: Follow written procedures
2. **Fix Workflow Scripts**: Repair automation
3. **Validate Manually**: Ensure system consistency
4. **Test Workflow**: Verify automation works
5. **Resume Normal Operation**: Return to automated workflows

## Continuous Improvement

This workflow standard is a living document. When you identify improvements:

1. **Propose Changes**: Create ADR for significant workflow modifications
2. **Test Changes**: Validate new procedures thoroughly  
3. **Update Documentation**: Keep standards current
4. **Train Team**: Ensure everyone understands changes
5. **Monitor Effectiveness**: Track workflow success metrics

---

**Remember**: These workflows exist to prevent the time-consuming periodic cleanups we've experienced. Following them saves time and maintains system quality.