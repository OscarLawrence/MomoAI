#!/usr/bin/env python3
"""
ADR Workflow Automation Agent

Automates the complete ADR lifecycle:
1. Create branch & setup folder structure
2. Research & analysis phase
3. Draft ADR with stakeholder input
4. Implementation planning
5. Execute implementation
6. Documentation & wrap-up with PR creation

Usage:
    python scripts/adr-workflow.py start "agent-orchestration" "Design agent orchestration system"
    python scripts/adr-workflow.py continue 007
    python scripts/adr-workflow.py finalize 007
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ADRWorkflowAgent:
    """Manages the complete ADR workflow lifecycle."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.adr_dir = project_root / "docs" / "adr"
        self.scripts_dir = project_root / "scripts"
        
    def get_next_adr_number(self) -> str:
        """Get the next ADR number by examining existing ADRs."""
        if not self.adr_dir.exists():
            return "001"
            
        existing_adrs = [d.name for d in self.adr_dir.iterdir() if d.is_dir() and d.name[:3].isdigit()]
        if not existing_adrs:
            return "001"
            
        numbers = [int(adr[:3]) for adr in existing_adrs]
        return f"{max(numbers) + 1:03d}"
    
    def create_branch_and_setup(self, short_name: str, title: str) -> str:
        """Create ADR branch and folder structure."""
        adr_number = self.get_next_adr_number()
        branch_name = f"adr/{adr_number}-{short_name}"
        adr_folder = f"{adr_number}-{short_name}"
        
        print(f"🔧 Creating ADR {adr_number}: {title}")
        print(f"📁 Branch: {branch_name}")
        
        # Create and switch to ADR branch
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.project_root, check=True)
        
        # Create ADR folder structure
        adr_path = self.adr_dir / adr_folder
        adr_path.mkdir(parents=True, exist_ok=True)
        (adr_path / "scripts").mkdir(exist_ok=True)
        
        # Create initial files from templates
        self._create_from_template(adr_path / "decision.md", "decision", {
            "number": adr_number,
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "DRAFT"
        })
        
        self._create_from_template(adr_path / "research.md", "research", {
            "number": adr_number,
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        self._create_from_template(adr_path / "implementation-plan.md", "implementation_plan", {
            "number": adr_number,
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        # Create workflow state file
        state = {
            "adr_number": adr_number,
            "title": title,
            "branch_name": branch_name,
            "adr_folder": adr_folder,
            "phase": "research",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat()
        }
        
        with open(adr_path / ".workflow-state.json", "w") as f:
            json.dump(state, f, indent=2)
        
        # Initial commit
        subprocess.run(["git", "add", "."], cwd=self.project_root, check=True)
        subprocess.run([
            "git", "commit", "-m", 
            f"feat: start ADR-{adr_number} - {title}\n\n🏗️ Created branch and initial structure\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        ], cwd=self.project_root, check=True)
        
        print(f"✅ ADR {adr_number} setup complete")
        print(f"📝 Next: Research phase - analyze problem and gather requirements")
        print(f"🔗 Continue with: python scripts/adr-workflow.py continue {adr_number}")
        
        return adr_number
    
    def continue_workflow(self, adr_number: str):
        """Continue ADR workflow based on current phase."""
        adr_folders = [d for d in self.adr_dir.iterdir() if d.is_dir() and d.name.startswith(adr_number)]
        
        if not adr_folders:
            print(f"❌ ADR {adr_number} not found")
            return
            
        adr_path = adr_folders[0]
        state_file = adr_path / ".workflow-state.json"
        
        if not state_file.exists():
            print(f"❌ Workflow state not found for ADR {adr_number}")
            return
            
        with open(state_file) as f:
            state = json.load(f)
        
        current_phase = state["phase"]
        
        if current_phase == "research":
            self._research_phase(adr_path, state)
        elif current_phase == "draft":
            self._draft_phase(adr_path, state)
        elif current_phase == "planning":
            self._planning_phase(adr_path, state)
        elif current_phase == "implementation":
            self._implementation_phase(adr_path, state)
        else:
            print(f"📋 ADR {adr_number} is in phase: {current_phase}")
            print("Use 'finalize' command when ready to complete")
    
    def finalize_adr(self, adr_number: str):
        """Finalize ADR and create pull request."""
        adr_folders = [d for d in self.adr_dir.iterdir() if d.is_dir() and d.name.startswith(adr_number)]
        
        if not adr_folders:
            print(f"❌ ADR {adr_number} not found")
            return
            
        adr_path = adr_folders[0]
        state_file = adr_path / ".workflow-state.json"
        
        with open(state_file) as f:
            state = json.load(f)
        
        # Create results document
        self._create_from_template(adr_path / "results.md", "results", {
            "number": adr_number,
            "title": state["title"],
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        # Update decision status
        decision_file = adr_path / "decision.md"
        if decision_file.exists():
            content = decision_file.read_text()
            content = content.replace("**Status:** DRAFT", "**Status:** ✅ **ACCEPTED & IMPLEMENTED**")
            decision_file.write_text(content)
        
        # Final commit
        subprocess.run(["git", "add", "."], cwd=self.project_root, check=True)
        subprocess.run([
            "git", "commit", "-m", 
            f"feat: complete ADR-{adr_number} - {state['title']}\n\n✅ Implementation complete with results documentation\n\n🤖 Generated with [Claude Code](https://claude.ai/code)\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        ], cwd=self.project_root, check=True)
        
        # Create pull request
        try:
            pr_body = f"""## ADR-{adr_number}: {state['title']}

### Summary
• **Decision**: [Brief summary of the architectural decision]
• **Impact**: [Key impacts and benefits]
• **Implementation**: Complete with documentation and results

### Documentation
• 📋 [Decision Document](docs/adr/{adr_path.name}/decision.md)
• 🔬 [Research Analysis](docs/adr/{adr_path.name}/research.md)
• 🗺️ [Implementation Plan](docs/adr/{adr_path.name}/implementation-plan.md)
• 📊 [Results & Lessons](docs/adr/{adr_path.name}/results.md)

### Test Plan
- [ ] Verify all documentation is complete and accurate
- [ ] Review implementation results and lessons learned
- [ ] Confirm architectural decision is properly recorded

🤖 Generated with [Claude Code](https://claude.ai/code)"""
            
            result = subprocess.run([
                "gh", "pr", "create", 
                "--title", f"ADR-{adr_number}: {state['title']}", 
                "--body", pr_body
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Pull request created: {result.stdout.strip()}")
            else:
                print(f"⚠️ PR creation failed: {result.stderr}")
                print("📝 Create PR manually when ready")
                
        except FileNotFoundError:
            print("⚠️ GitHub CLI not found - create PR manually")
        
        print(f"🎉 ADR {adr_number} workflow complete!")
    
    def _research_phase(self, adr_path: Path, state: Dict):
        """Guide through research phase."""
        print(f"🔬 Research Phase - ADR {state['adr_number']}")
        print("📋 Tasks:")
        print("  1. Analyze the problem and current state")
        print("  2. Research potential solutions and alternatives") 
        print("  3. Gather stakeholder requirements")
        print("  4. Document findings in research.md")
        print()
        print("📝 When research is complete:")
        print("  1. Update research.md with findings")
        print("  2. Commit changes")
        print("  3. Run: python scripts/adr-workflow.py continue", state['adr_number'])
        
        # Update phase to draft
        state["phase"] = "draft"
        state["updated"] = datetime.now().isoformat()
        with open(adr_path / ".workflow-state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def _draft_phase(self, adr_path: Path, state: Dict):
        """Guide through drafting phase."""
        print(f"📝 Draft Phase - ADR {state['adr_number']}")
        print("📋 Tasks:")
        print("  1. Draft the decision document based on research")
        print("  2. Include problem statement, options, and recommendation")
        print("  3. Review with stakeholders if needed")
        print("  4. Finalize the architectural decision")
        print()
        print("📝 When draft is complete:")
        print("  1. Update decision.md with final decision")
        print("  2. Commit changes")
        print("  3. Run: python scripts/adr-workflow.py continue", state['adr_number'])
        
        # Update phase to planning
        state["phase"] = "planning"
        state["updated"] = datetime.now().isoformat()
        with open(adr_path / ".workflow-state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def _planning_phase(self, adr_path: Path, state: Dict):
        """Guide through planning phase."""
        print(f"🗺️ Planning Phase - ADR {state['adr_number']}")
        print("📋 Tasks:")
        print("  1. Create detailed implementation plan")
        print("  2. Break down into phases and tasks")
        print("  3. Identify risks and dependencies")
        print("  4. Define success criteria and metrics")
        print()
        print("📝 When planning is complete:")
        print("  1. Update implementation-plan.md")
        print("  2. Commit changes")
        print("  3. Run: python scripts/adr-workflow.py continue", state['adr_number'])
        
        # Update phase to implementation
        state["phase"] = "implementation"
        state["updated"] = datetime.now().isoformat()
        with open(adr_path / ".workflow-state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def _implementation_phase(self, adr_path: Path, state: Dict):
        """Guide through implementation phase."""
        print(f"⚡ Implementation Phase - ADR {state['adr_number']}")
        print("📋 Tasks:")
        print("  1. Execute the implementation plan")
        print("  2. Track progress in implementation-log.md")
        print("  3. Document any changes or discoveries")
        print("  4. Run tests and validate implementation")
        print()
        print("📝 When implementation is complete:")
        print("  1. Document final results and lessons learned")
        print("  2. Commit all changes")
        print("  3. Run: python scripts/adr-workflow.py finalize", state['adr_number'])
        
        # Create implementation log if not exists
        log_file = adr_path / "implementation-log.md"
        if not log_file.exists():
            self._create_from_template(log_file, "implementation_log", {
                "number": state['adr_number'],
                "title": state['title']
            })
        
        # Update phase to ready for finalization
        state["phase"] = "finalizing"
        state["updated"] = datetime.now().isoformat()
        with open(adr_path / ".workflow-state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def _create_from_template(self, file_path: Path, template_name: str, variables: Dict):
        """Create file from template with variable substitution."""
        
        if template_name == "decision":
            template = f"""# ADR-{variables['number']}: {variables['title']}

**Date:** {variables['date']}  
**Status:** {variables['status']}  
**Decision Makers:** Vincent  
**Consulted:** [To be filled during research]

## Table of Contents

- [Problem Statement](#problem-statement)
- [Research Summary](#research-summary)
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

[Describe the architectural challenge that requires a decision]

## Research Summary

### Key Findings

[Research findings from research.md]

### Current State Analysis

[Analysis of existing systems and constraints]

## Decision

[The architectural decision made]

## Implementation Strategy

[High-level implementation approach]

## Success Metrics

[How success will be measured]

## Risks and Mitigations

[Risks identified and how they're addressed]

## Trade-offs Accepted

[What we gain vs what we give up]

## Implementation Results

[Actual results - to be filled during implementation]

## Lessons Learned

[What we learned - to be filled after implementation]

## Next Steps

[Future actions and follow-up work]

## Related Documentation

- **[Research Analysis](research.md)** - Detailed research findings
- **[Implementation Plan](implementation-plan.md)** - Execution details
- **[Implementation Log](implementation-log.md)** - Daily progress tracking  
- **[Results & Lessons](results.md)** - Final outcomes and insights
"""
        
        elif template_name == "research":
            template = f"""# ADR-{variables['number']} Research: {variables['title']}

**Date:** {variables['date']}

## Research Methodology

[Describe how research was conducted]

## Problem Analysis

### Current State

[Detailed analysis of the current situation]

### Pain Points

[Specific issues that need to be addressed]

### Requirements

[Functional and non-functional requirements]

## Solution Research

### Option 1: [Name]

**Description:** [Brief description]

**Pros:**
- [Advantage 1]
- [Advantage 2]

**Cons:**
- [Disadvantage 1]
- [Disadvantage 2]

**Implementation Effort:** [High/Medium/Low]

### Option 2: [Name]

[Similar structure as Option 1]

## Comparative Analysis

[Compare options against key criteria]

## Recommendation

[Which option to pursue and why]

## References

[External sources and documentation consulted]
"""
        
        elif template_name == "implementation_plan":
            template = f"""# ADR-{variables['number']} Implementation Plan: {variables['title']}

## Implementation Overview

[High-level description of implementation approach]

## Phase Breakdown

### Phase 1: [Name]
**Duration:** [Estimated timeframe]  
**Dependencies:** [What must be complete first]

**Tasks:**
- [ ] [Task 1]
- [ ] [Task 2]
- [ ] [Task 3]

**Success Criteria:**
- [Criterion 1]
- [Criterion 2]

### Phase 2: [Name]
[Similar structure]

### Phase 3: [Name]
[Similar structure]

## Risk Management

### Risk 1: [Description]
**Probability:** High/Medium/Low  
**Impact:** High/Medium/Low  
**Mitigation:** [How to address]

## Success Metrics

[How implementation success will be measured]

## Testing Strategy

[How implementation will be validated]

## Rollback Plan

[How to revert if implementation fails]
"""
        
        elif template_name == "implementation_log":
            template = f"""# ADR-{variables['number']} Implementation Log: {variables['title']}

## Progress Tracking

[Daily log of implementation progress]

### {datetime.now().strftime('%Y-%m-%d')}
**Status:** Started  
**Work Done:**
- Created implementation log
- [Other work completed]

**Challenges:**
- [Any issues encountered]

**Next Steps:**
- [What to work on next]

### [Date]
**Status:** [In Progress/Blocked/Complete]  
**Work Done:**
- [Work completed today]

**Decisions Made:**
- [Any architectural or implementation decisions]

**Challenges:**
- [Issues encountered and how resolved]

**Next Steps:**
- [Plans for next session]

## Key Decisions

[Record important implementation decisions made during development]

## Lessons Learned

[Insights gained during implementation]
"""
        
        elif template_name == "results":
            template = f"""# ADR-{variables['number']} Results: {variables['title']}

**Implementation Date:** {variables['date']}  
**Status:** ✅ **COMPLETE**

## Implementation Summary

[High-level summary of what was implemented]

## Success Metrics Achieved

[Results against the success criteria defined in the plan]

## Technical Achievements

[Specific technical accomplishments]

## Performance Impact

[Performance measurements and improvements]

## Quality Improvements  

[Code quality, maintainability, or other quality metrics]

## Challenges Overcome

[Major obstacles encountered and how they were resolved]

## Lessons Learned

### What Worked Well
[Positive outcomes and effective approaches]

### Areas for Improvement
[Things that could be done better next time]

### Key Insights
[Important discoveries or realizations]

## Future Enhancements

[Potential improvements or follow-up work identified]

## Impact Assessment

[How this decision affected the broader system]

## Recommendations

[Advice for similar future decisions or implementations]
"""
        else:
            template = ""
            
        if template:
            file_path.write_text(template)


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/adr-workflow.py start <short-name> <title>")
        print("  python scripts/adr-workflow.py continue <adr-number>")
        print("  python scripts/adr-workflow.py finalize <adr-number>")
        print()
        print("Examples:")
        print("  python scripts/adr-workflow.py start 'agent-orchestration' 'Design agent orchestration system'")
        print("  python scripts/adr-workflow.py continue 007")
        print("  python scripts/adr-workflow.py finalize 007")
        return
    
    project_root = Path(__file__).parent.parent
    agent = ADRWorkflowAgent(project_root)
    
    command = sys.argv[1]
    
    if command == "start":
        if len(sys.argv) < 4:
            print("Usage: python scripts/adr-workflow.py start <short-name> <title>")
            return
        short_name = sys.argv[2]
        title = sys.argv[3]
        agent.create_branch_and_setup(short_name, title)
        
    elif command == "continue":
        if len(sys.argv) < 3:
            print("Usage: python scripts/adr-workflow.py continue <adr-number>")
            return
        adr_number = sys.argv[2]
        agent.continue_workflow(adr_number)
        
    elif command == "finalize":
        if len(sys.argv) < 3:
            print("Usage: python scripts/adr-workflow.py finalize <adr-number>")
            return
        adr_number = sys.argv[2]
        agent.finalize_adr(adr_number)
        
    else:
        print(f"Unknown command: {command}")
        print("Available commands: start, continue, finalize")


if __name__ == "__main__":
    main()