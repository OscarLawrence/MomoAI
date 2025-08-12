"""
Idea workflow management system.

Implements the stage-based workflow: idea → investigation → decision → implementation → validation
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from .context import WorkspaceContext


class IdeaManager:
    """Manages the complete idea workflow lifecycle."""

    def __init__(self, context: WorkspaceContext):
        self.context = context
        self.ideas_dir = context.workspace_root / "ideas"
        self.ideas_dir.mkdir(exist_ok=True)

        # Ensure template exists
        self._ensure_template_exists()

    def _ensure_template_exists(self):
        """Create template directory if it doesn't exist."""
        template_dir = self.ideas_dir / "template"
        template_dir.mkdir(exist_ok=True)

        # Create template files
        templates = {
            "01-idea.md": self._get_idea_template(),
            "02-investigation.md": self._get_investigation_template(),
            "03-decision.md": self._get_decision_template(),
            "04-implementation-plan.md": self._get_implementation_template(),
            "metadata.json": self._get_metadata_template(),
        }

        for filename, content in templates.items():
            template_file = template_dir / filename
            if not template_file.exists():
                template_file.write_text(content)

    def create_idea(self, topic: str) -> str:
        """Create new idea with folder structure and templates."""
        # Get next idea number
        idea_number = self._get_next_idea_number()
        idea_id = f"{idea_number:03d}-{self._slugify(topic)}"

        idea_path = self.ideas_dir / idea_id
        if idea_path.exists():
            print(f"❌ Idea already exists: {idea_id}")
            return idea_id

        # Create idea directory structure
        idea_path.mkdir()
        (idea_path / "references").mkdir()

        # Copy templates and populate
        self._populate_idea_templates(idea_path, idea_id, topic)

        # Create initial git branch
        self._create_git_branch(f"feature/agent-claude-{idea_id}-creation")

        print(f"✅ Created idea: {idea_id}")
        print(f"📁 Location: {idea_path}")
        print(f"🌿 Git branch: feature/agent-claude-{idea_id}-creation")
        print(f"📝 Edit your research in: {idea_path}/01-idea.md")

        return idea_id

    def investigate_idea(self, idea_id: str) -> bool:
        """Guide agent through investigation process."""
        idea_path = self._get_idea_path(idea_id)
        if not idea_path:
            return False

        print(f"🔍 Starting investigation for: {idea_id}")

        # Check if idea stage is complete
        idea_file = idea_path / "01-idea.md"
        if not self._is_stage_ready(idea_file):
            print(f"❌ Please complete the idea stage first: {idea_file}")
            return False

        # Create investigation branch
        branch_name = f"feature/agent-claude-{idea_id}-investigation"
        self._create_git_branch(branch_name)

        # Show investigation guidance
        self._show_investigation_guidance(idea_path)

        # Mark investigation as started
        self._update_metadata(
            idea_path,
            {"stage": "investigation", "started_at": datetime.now().isoformat()},
        )

        return True

    def create_decision(self, idea_id: str) -> bool:
        """Create decision from investigation."""
        idea_path = self._get_idea_path(idea_id)
        if not idea_path:
            return False

        # Check if investigation is complete
        investigation_file = idea_path / "02-investigation.md"
        if not self._is_stage_ready(investigation_file):
            print(f"❌ Please complete investigation first: {investigation_file}")
            return False

        print(f"🎯 Creating decision for: {idea_id}")

        # Create decision branch
        branch_name = f"feature/agent-claude-{idea_id}-decision"
        self._create_git_branch(branch_name)

        # Show decision guidance
        self._show_decision_guidance(idea_path)

        # Update metadata
        self._update_metadata(idea_path, {"stage": "decision"})

        return True

    def implement_decision(self, idea_id: str) -> bool:
        """Implement decision with ADR creation."""
        idea_path = self._get_idea_path(idea_id)
        if not idea_path:
            return False

        # Check if decision is complete
        decision_file = idea_path / "03-decision.md"
        if not self._is_stage_ready(decision_file):
            print(f"❌ Please complete decision first: {decision_file}")
            return False

        print(f"🚀 Implementing decision for: {idea_id}")

        # Create implementation branch
        branch_name = f"feature/agent-claude-{idea_id}-implementation"
        self._create_git_branch(branch_name)

        # Create ADR from decision
        adr_number = self._create_adr_from_decision(idea_path, idea_id)

        # Show implementation guidance
        self._show_implementation_guidance(idea_path, adr_number)

        # Update metadata
        self._update_metadata(
            idea_path,
            {
                "stage": "implementation",
                "adr_number": adr_number,
                "implementation_started": datetime.now().isoformat(),
            },
        )

        return True

    def _get_next_idea_number(self) -> int:
        """Get the next sequential idea number."""
        existing_ideas = [
            d
            for d in self.ideas_dir.iterdir()
            if d.is_dir() and d.name != "template" and d.name[:3].isdigit()
        ]

        if not existing_ideas:
            return 1

        numbers = [int(d.name[:3]) for d in existing_ideas]
        return max(numbers) + 1

    def _slugify(self, text: str) -> str:
        """Convert text to slug format."""
        return text.lower().replace(" ", "-").replace("_", "-")

    def _get_idea_path(self, idea_id: str) -> Optional[Path]:
        """Get path to idea directory."""
        idea_path = self.ideas_dir / idea_id
        if not idea_path.exists():
            print(f"❌ Idea not found: {idea_id}")
            available_ideas = [
                d.name
                for d in self.ideas_dir.iterdir()
                if d.is_dir() and d.name != "template"
            ]
            if available_ideas:
                print(f"Available ideas: {', '.join(available_ideas)}")
            return None
        return idea_path

    def _populate_idea_templates(self, idea_path: Path, idea_id: str, topic: str):
        """Populate templates with idea-specific information."""
        # Copy and populate templates
        template_dir = self.ideas_dir / "template"

        for template_file in template_dir.iterdir():
            if template_file.is_file():
                target_file = idea_path / template_file.name
                content = template_file.read_text()

                # Replace placeholders
                content = content.replace("{{IDEA_ID}}", idea_id)
                content = content.replace("{{TOPIC}}", topic)
                content = content.replace(
                    "{{DATE}}", datetime.now().strftime("%Y-%m-%d")
                )
                content = content.replace("{{AUTHOR}}", "Human + Claude")

                target_file.write_text(content)

    def _create_git_branch(self, branch_name: str):
        """Create and checkout git branch."""
        try:
            # Check if branch already exists
            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                cwd=self.context.workspace_root,
                capture_output=True,
                text=True,
            )

            if branch_name in result.stdout:
                # Branch exists, just checkout
                subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=self.context.workspace_root,
                    check=True,
                )
            else:
                # Create new branch
                subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=self.context.workspace_root,
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Git branch creation failed: {e}")

    def _is_stage_ready(self, stage_file: Path) -> bool:
        """Check if a stage file has meaningful content."""
        if not stage_file.exists():
            return False

        content = stage_file.read_text()
        # Check if file has more than just template content
        meaningful_content = [
            line
            for line in content.split("\n")
            if line.strip()
            and not line.startswith("#")
            and not line.startswith("<!--")
            and "{{" not in line
        ]

        return len(meaningful_content) > 3  # More than just basic structure

    def _update_metadata(self, idea_path: Path, updates: dict):
        """Update idea metadata."""
        metadata_file = idea_path / "metadata.json"

        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
        else:
            metadata = {}

        metadata.update(updates)
        metadata["last_updated"] = datetime.now().isoformat()

        metadata_file.write_text(json.dumps(metadata, indent=2))

    def _create_adr_from_decision(self, idea_path: Path, idea_id: str) -> str:
        """Create ADR from decision stage."""
        # Get next ADR number
        adr_dir = self.context.workspace_root / "docs" / "adr"
        existing_adrs = [
            d for d in adr_dir.iterdir() if d.is_dir() and d.name[:3].isdigit()
        ]

        if existing_adrs:
            numbers = [int(d.name[:3]) for d in existing_adrs]
            next_number = max(numbers) + 1
        else:
            next_number = 1

        adr_number = f"{next_number:03d}"

        # Read decision content
        decision_file = idea_path / "03-decision.md"
        decision_file.read_text()

        # Create ADR directory and basic structure
        adr_path = adr_dir / f"{adr_number}-{idea_id}"
        adr_path.mkdir(exist_ok=True)

        # Create ADR decision file
        adr_decision = adr_path / "decision.md"
        adr_template = f"""# ADR-{adr_number}: {idea_id.replace("-", " ").title()}

**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Status:** DRAFT
**Decision Makers:** Human + Claude Agent
**Source:** Idea workflow {idea_id}

## Problem Statement

[Extracted from idea investigation]

## Decision

[Extracted from decision stage]

## Implementation Plan

[To be filled during implementation]

## Source Materials

- Idea: {idea_path}/01-idea.md
- Investigation: {idea_path}/02-investigation.md  
- Decision: {idea_path}/03-decision.md

---

*This ADR was created from idea workflow {idea_id}*
"""

        adr_decision.write_text(adr_template)

        print(f"📋 Created ADR-{adr_number} from {idea_id}")
        return adr_number

    def _show_investigation_guidance(self, idea_path: Path):
        """Show guidance for investigation stage."""
        print(f"""
🔍 Investigation Guidance:

1. Read the idea file: {idea_path}/01-idea.md
2. Research the topic thoroughly
3. Update: {idea_path}/02-investigation.md with:
   - Background research
   - Technical options analysis  
   - Pros/cons of different approaches
   - Recommendations
4. Add references to: {idea_path}/references/
5. When ready, run: mo decide {idea_path.name}
""")

    def _show_decision_guidance(self, idea_path: Path):
        """Show guidance for decision stage."""
        print(f"""
🎯 Decision Guidance:

1. Review investigation: {idea_path}/02-investigation.md
2. Update: {idea_path}/03-decision.md with:
   - Clear decision statement
   - Chosen approach and rationale
   - Success criteria
   - Risk assessment
3. When ready, run: mo implement {idea_path.name}
""")

    def _show_implementation_guidance(self, idea_path: Path, adr_number: str):
        """Show guidance for implementation stage."""
        print(f"""
🚀 Implementation Guidance:

1. ADR-{adr_number} has been created from your decision
2. Update: {idea_path}/04-implementation-plan.md with:
   - Detailed implementation steps
   - Testing strategy
   - Rollback plan
3. Follow standard development workflow:
   - Format → Lint → Typecheck → Test-fast
4. Create PR when implementation complete
5. Run: mo validate implementation {idea_path.name}
""")

    # Template methods
    def _get_idea_template(self) -> str:
        return """# Idea: {{TOPIC}}

**ID:** {{IDEA_ID}}
**Date:** {{DATE}}
**Author:** {{AUTHOR}}

## Problem Statement

<!-- What problem are we trying to solve? -->

## Research Question

<!-- What specific question needs investigation? -->

## Context

<!-- Why is this important now? What's the background? -->

## Success Criteria

<!-- How will we know if this idea is worth pursuing? -->

## Initial Thoughts

<!-- Your initial thoughts, concerns, ideas -->

---

*Next stage: Investigation (mo investigate {{IDEA_ID}})*
"""

    def _get_investigation_template(self) -> str:
        return """# Investigation: {{TOPIC}}

**ID:** {{IDEA_ID}}
**Date:** {{DATE}}
**Stage:** Investigation

## Background Research

<!-- What did you discover about this topic? -->

## Technical Options

### Option 1: [Name]
- **Description:**
- **Pros:**
- **Cons:**
- **Complexity:**

### Option 2: [Name]
- **Description:**
- **Pros:**
- **Cons:**
- **Complexity:**

## Analysis

<!-- Your analysis of the options -->

## Recommendations

<!-- What do you recommend and why? -->

## Open Questions

<!-- What still needs to be resolved? -->

---

*Next stage: Decision (mo decide {{IDEA_ID}})*
"""

    def _get_decision_template(self) -> str:
        return """# Decision: {{TOPIC}}

**ID:** {{IDEA_ID}}
**Date:** {{DATE}}
**Stage:** Decision

## Decision

<!-- Clear statement of what we decided to do -->

## Rationale

<!-- Why did we choose this approach? -->

## Implementation Approach

<!-- High-level approach for implementation -->

## Success Criteria

<!-- How will we measure success? -->

## Risks and Mitigations

<!-- What could go wrong and how do we handle it? -->

## Timeline

<!-- Rough timeline for implementation -->

---

*Next stage: Implementation (mo implement {{IDEA_ID}})*
"""

    def _get_implementation_template(self) -> str:
        return """# Implementation Plan: {{TOPIC}}

**ID:** {{IDEA_ID}}
**Date:** {{DATE}}
**Stage:** Implementation

## Implementation Steps

1. [ ] Step 1
2. [ ] Step 2
3. [ ] Step 3

## Testing Strategy

<!-- How will we test this implementation? -->

## Rollback Plan

<!-- If something goes wrong, how do we revert? -->

## Documentation Updates

<!-- What documentation needs to be updated? -->

## Validation Checklist

- [ ] All tests pass
- [ ] Code formatted and linted
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Success criteria met

---

*Next stage: Validation (mo validate implementation {{IDEA_ID}})*
"""

    def _get_metadata_template(self) -> str:
        return """{
  "id": "{{IDEA_ID}}",
  "topic": "{{TOPIC}}",
  "created_at": "{{DATE}}",
  "author": "{{AUTHOR}}",
  "stage": "idea",
  "status": "active"
}"""
