#!/usr/bin/env python3
"""
Structured Task Workflow System
Ensures consistent task execution and prevents documentation drift
"""

import json
import subprocess
import sys
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


@dataclass
class TaskStep:
    """Individual step in a task workflow"""
    name: str
    description: str
    command: Optional[str] = None
    validation: Optional[str] = None
    completed: bool = False
    timestamp: Optional[str] = None


@dataclass
class TaskWorkflow:
    """Complete task workflow with metadata"""
    task_id: str
    title: str
    description: str
    category: str  # "feature", "bugfix", "documentation", "architecture"
    steps: List[TaskStep]
    created_at: str
    updated_at: str
    status: str = "pending"  # "pending", "in_progress", "completed", "blocked"
    validation_required: bool = True


class WorkflowManager:
    """Manages structured task workflows"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.workflows_dir = project_root / ".workflows"
        self.workflows_dir.mkdir(exist_ok=True)
    
    def create_workflow(self, title: str, description: str, category: str, 
                       steps: List[Dict[str, Any]]) -> TaskWorkflow:
        """Create a new structured workflow"""
        task_id = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()
        
        workflow_steps = [TaskStep(**step) for step in steps]
        
        workflow = TaskWorkflow(
            task_id=task_id,
            title=title,
            description=description,
            category=category,
            steps=workflow_steps,
            created_at=timestamp,
            updated_at=timestamp
        )
        
        self._save_workflow(workflow)
        return workflow
    
    def load_workflow(self, task_id: str) -> Optional[TaskWorkflow]:
        """Load an existing workflow"""
        workflow_file = self.workflows_dir / f"{task_id}.json"
        if not workflow_file.exists():
            return None
        
        with open(workflow_file) as f:
            data = json.load(f)
        
        # Convert steps back to TaskStep objects
        steps = [TaskStep(**step) for step in data['steps']]
        data['steps'] = steps
        
        return TaskWorkflow(**data)
    
    def update_workflow(self, workflow: TaskWorkflow):
        """Update workflow status and timestamp"""
        workflow.updated_at = datetime.now().isoformat()
        self._save_workflow(workflow)
    
    def _save_workflow(self, workflow: TaskWorkflow):
        """Save workflow to disk"""
        workflow_file = self.workflows_dir / f"{workflow.task_id}.json"
        with open(workflow_file, 'w') as f:
            json.dump(asdict(workflow), f, indent=2)
    
    def execute_step(self, workflow: TaskWorkflow, step_index: int) -> bool:
        """Execute a workflow step and validate results"""
        if step_index >= len(workflow.steps):
            return False
        
        step = workflow.steps[step_index]
        print(f"\\n🔄 Executing: {step.name}")
        print(f"   Description: {step.description}")
        
        # Execute command if provided
        if step.command:
            print(f"   Command: {step.command}")
            try:
                result = subprocess.run(
                    step.command.split(),
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    print(f"   ❌ Command failed: {result.stderr}")
                    return False
                print(f"   ✅ Command successful")
            except Exception as e:
                print(f"   ❌ Command error: {e}")
                return False
        
        # Run validation if provided
        if step.validation:
            print(f"   Validation: {step.validation}")
            try:
                result = subprocess.run(
                    step.validation.split(),
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    print(f"   ❌ Validation failed: {result.stderr}")
                    return False
                print(f"   ✅ Validation passed")
            except Exception as e:
                print(f"   ❌ Validation error: {e}")
                return False
        
        # Mark step as completed
        step.completed = True
        step.timestamp = datetime.now().isoformat()
        self.update_workflow(workflow)
        
        print(f"   ✅ Step completed")
        return True
    
    def execute_workflow(self, task_id: str) -> bool:
        """Execute complete workflow"""
        workflow = self.load_workflow(task_id)
        if not workflow:
            print(f"❌ Workflow {task_id} not found")
            return False
        
        print(f"\\n{'='*60}")
        print(f"EXECUTING WORKFLOW: {workflow.title}")
        print(f"{'='*60}")
        
        workflow.status = "in_progress"
        self.update_workflow(workflow)
        
        all_steps_passed = True
        for i, step in enumerate(workflow.steps):
            if step.completed:
                print(f"\\n✅ Skipping completed step: {step.name}")
                continue
            
            if not self.execute_step(workflow, i):
                print(f"\\n❌ Workflow failed at step: {step.name}")
                workflow.status = "blocked"
                self.update_workflow(workflow)
                return False
        
        # Run final validation if required
        if workflow.validation_required:
            print(f"\\n🔍 Running final validation...")
            validation_result = subprocess.run(
                [sys.executable, str(self.project_root / "scripts" / "workflow-validate.py")],
                capture_output=True, text=True
            )
            
            if validation_result.returncode != 0:
                print(f"❌ Final validation failed:")
                print(validation_result.stdout)
                workflow.status = "blocked"
                self.update_workflow(workflow)
                return False
            
            print("✅ Final validation passed")
        
        workflow.status = "completed"
        self.update_workflow(workflow)
        
        print(f"\\n✅ WORKFLOW COMPLETED: {workflow.title}")
        return True
    
    def list_workflows(self) -> List[TaskWorkflow]:
        """List all workflows"""
        workflows = []
        for workflow_file in self.workflows_dir.glob("*.json"):
            task_id = workflow_file.stem
            workflow = self.load_workflow(task_id)
            if workflow:
                workflows.append(workflow)
        
        return sorted(workflows, key=lambda w: w.created_at, reverse=True)
    
    def print_status(self):
        """Print workflow status summary"""
        workflows = self.list_workflows()
        
        print("\\n" + "="*60)
        print("WORKFLOW STATUS SUMMARY")
        print("="*60)
        
        if not workflows:
            print("No workflows found")
            return
        
        status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "blocked": 0}
        
        for workflow in workflows:
            status_counts[workflow.status] += 1
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄", 
                "completed": "✅",
                "blocked": "❌"
            }[workflow.status]
            
            print(f"{status_icon} {workflow.task_id}: {workflow.title}")
            print(f"   Category: {workflow.category} | Status: {workflow.status}")
            if workflow.steps:
                completed_steps = sum(1 for s in workflow.steps if s.completed)
                total_steps = len(workflow.steps)
                print(f"   Progress: {completed_steps}/{total_steps} steps")
            print()
        
        print("Summary:")
        for status, count in status_counts.items():
            if count > 0:
                print(f"  {status.title()}: {count}")


def main():
    """CLI interface for workflow management"""
    if len(sys.argv) < 2:
        print("Usage: python task-workflow.py <command> [args]")
        print("Commands: create, execute, list, status")
        return
    
    project_root = Path(__file__).parent.parent
    manager = WorkflowManager(project_root)
    
    command = sys.argv[1]
    
    if command == "create":
        # Example workflow creation - customize as needed
        if len(sys.argv) < 3:
            print("Usage: python task-workflow.py create <template>")
            print("Templates: documentation-fix, module-development, architecture-change")
            return
        
        template = sys.argv[2]
        workflows = get_workflow_templates()
        
        if template not in workflows:
            print(f"Unknown template: {template}")
            return
        
        workflow = manager.create_workflow(**workflows[template])
        print(f"Created workflow: {workflow.task_id}")
        
    elif command == "execute":
        if len(sys.argv) < 3:
            print("Usage: python task-workflow.py execute <task_id>")
            return
        
        task_id = sys.argv[2]
        success = manager.execute_workflow(task_id)
        sys.exit(0 if success else 1)
        
    elif command == "list":
        workflows = manager.list_workflows()
        for workflow in workflows:
            print(f"{workflow.task_id}: {workflow.title} ({workflow.status})")
        
    elif command == "status":
        manager.print_status()
        
    else:
        print(f"Unknown command: {command}")


def get_workflow_templates() -> Dict[str, Dict[str, Any]]:
    """Predefined workflow templates for common tasks"""
    return {
        "documentation-fix": {
            "title": "Documentation Consistency Fix",
            "description": "Fix documentation inconsistencies and prevent drift",
            "category": "documentation",
            "steps": [
                {
                    "name": "validate_current_state",
                    "description": "Run validation to identify issues",
                    "validation": "python scripts/workflow-validate.py"
                },
                {
                    "name": "fix_architecture_paths", 
                    "description": "Update architecture documentation paths",
                    "command": "echo 'Manual fix required - update README.md and CLAUDE.md'"
                },
                {
                    "name": "resolve_adr_conflicts",
                    "description": "Move and renumber conflicting ADRs",
                    "command": "echo 'Manual fix required - resolve ADR numbering conflicts'"
                },
                {
                    "name": "final_validation",
                    "description": "Validate all fixes",
                    "validation": "python scripts/workflow-validate.py"
                }
            ]
        },
        "module-development": {
            "title": "Module Development Workflow", 
            "description": "Complete development workflow for a Python module",
            "category": "feature",
            "steps": [
                {
                    "name": "setup_environment",
                    "description": "Set up module development environment",
                    "command": "pnpm nx run MODULE:install"
                },
                {
                    "name": "implement_features",
                    "description": "Implement core functionality",
                    "command": "echo 'Manual implementation required'"
                },
                {
                    "name": "format_code",
                    "description": "Format code according to standards",
                    "command": "pnpm nx run MODULE:format"
                },
                {
                    "name": "type_check",
                    "description": "Validate type annotations",
                    "validation": "pnpm nx run MODULE:typecheck"
                },
                {
                    "name": "run_tests",
                    "description": "Execute comprehensive test suite",
                    "validation": "pnpm nx run MODULE:test-fast"
                },
                {
                    "name": "update_documentation",
                    "description": "Update module and system documentation",
                    "command": "echo 'Update README.md, CLAUDE.md, and module docs'"
                }
            ]
        }
    }


if __name__ == "__main__":
    main()