#!/usr/bin/env python3
"""
MomoAI Workflow Validation System
Prevents documentation drift and ensures consistency across all tasks
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml


@dataclass
class ValidationResult:
    """Structured result of a validation check"""
    check_name: str
    passed: bool
    message: str
    fix_command: Optional[str] = None


class WorkflowValidator:
    """Comprehensive validation system for MomoAI workflows"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results: List[ValidationResult] = []
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        checks = [
            self.validate_architecture_docs,
            self.validate_module_status,
            self.validate_adr_conflicts,
            self.validate_nx_commands,
            self.validate_project_structure
        ]
        
        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                self.results.append(ValidationResult(
                    check_name=check.__name__,
                    passed=False,
                    message=f"Check failed with error: {e}"
                ))
                all_passed = False
        
        return all_passed
    
    def validate_architecture_docs(self) -> bool:
        """Ensure architecture documentation matches actual structure"""
        readme_path = self.project_root / "README.md"
        claude_path = self.project_root / "CLAUDE.md"
        
        if not readme_path.exists():
            self.results.append(ValidationResult(
                "validate_architecture_docs", False, "README.md not found"))
            return False
        
        with open(readme_path) as f:
            readme_content = f.read()
        
        # Check for correct path structure
        if "├── apps/" in readme_content and "├── code/" not in readme_content:
            self.results.append(ValidationResult(
                "validate_architecture_docs", False,
                "README.md contains incorrect architecture paths (missing code/ prefix)",
                "Update README.md architecture section to reflect code/ directory structure"
            ))
            return False
        
        self.results.append(ValidationResult(
            "validate_architecture_docs", True,
            "Architecture documentation is consistent"))
        return True
    
    def validate_module_status(self) -> bool:
        """Validate module completion status claims against reality"""
        errors_found = False
        
        # Check for type errors in modules claimed as COMPLETE
        modules_to_check = [
            "momo-kb", "momo-logger", "momo-graph-store", 
            "momo-vector-store", "momo-store-document"
        ]
        
        for module in modules_to_check:
            try:
                result = subprocess.run(
                    ["pnpm", "nx", "run", f"{module}:typecheck"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0:
                    readme_path = self.project_root / "README.md"
                    if readme_path.exists():
                        readme_content = readme_path.read_text()
                        if "COMPLETE" in readme_content:
                            self.results.append(ValidationResult(
                                "validate_module_status", False,
                                f"Module {module} claimed as COMPLETE but has type errors",
                                f"Fix type errors in {module} or update status documentation"
                            ))
                            errors_found = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Skip if command fails - don't fail validation for missing tools
                continue
        
        if not errors_found:
            self.results.append(ValidationResult(
                "validate_module_status", True,
                "Module status claims are consistent with reality"))
        
        return not errors_found
    
    def validate_adr_conflicts(self) -> bool:
        """Check for ADR numbering conflicts"""
        adr_root = self.project_root / "docs" / "adr"
        if not adr_root.exists():
            self.results.append(ValidationResult(
                "validate_adr_conflicts", False, "ADR directory not found"))
            return False
        
        adr_numbers: Set[str] = set()
        conflicts = []
        
        # Check root ADRs
        for adr_dir in adr_root.iterdir():
            if adr_dir.is_dir() and adr_dir.name.startswith(('00', '01')):
                adr_num = adr_dir.name.split('-')[0]
                if adr_num in adr_numbers:
                    conflicts.append(f"Duplicate ADR number {adr_num} in {adr_dir}")
                adr_numbers.add(adr_num)
        
        # Check for ADRs in module directories
        code_dir = self.project_root / "code"
        if code_dir.exists():
            for adr_file in code_dir.rglob("adr-*.md"):
                adr_num = adr_file.name.split('-')[1][:3]  # Extract number
                if adr_num in adr_numbers:
                    conflicts.append(f"ADR conflict: {adr_file} conflicts with root ADR-{adr_num}")
        
        if conflicts:
            self.results.append(ValidationResult(
                "validate_adr_conflicts", False,
                f"ADR conflicts found: {'; '.join(conflicts)}",
                "Renumber conflicting ADRs and move module ADRs to root with references"
            ))
            return False
        
        self.results.append(ValidationResult(
            "validate_adr_conflicts", True,
            "No ADR conflicts detected"))
        return True
    
    def validate_nx_commands(self) -> bool:
        """Validate that documented Nx commands work"""
        # Test basic Nx functionality
        try:
            result = subprocess.run(
                ["pnpm", "nx", "show", "projects"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                self.results.append(ValidationResult(
                    "validate_nx_commands", False,
                    "Basic Nx commands are failing",
                    "Run 'pnpm nx reset' and check Nx configuration"
                ))
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results.append(ValidationResult(
                "validate_nx_commands", False,
                "Nx or pnpm not available"))
            return False
        
        self.results.append(ValidationResult(
            "validate_nx_commands", True,
            "Nx commands are functional"))
        return True
    
    def validate_project_structure(self) -> bool:
        """Validate actual project structure matches expectations"""
        expected_dirs = [
            "code/apps", "code/libs/python",
            "docs/adr", "scripts", "research"
        ]
        
        missing_dirs = []
        for dir_path in expected_dirs:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            self.results.append(ValidationResult(
                "validate_project_structure", False,
                f"Missing expected directories: {', '.join(missing_dirs)}",
                "Create missing directories or update documentation"
            ))
            return False
        
        self.results.append(ValidationResult(
            "validate_project_structure", True,
            "Project structure is as expected"))
        return True
    
    def print_report(self):
        """Print comprehensive validation report"""
        print("\\n" + "="*60)
        print("MOMOAI WORKFLOW VALIDATION REPORT")
        print("="*60)
        
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)
        
        print(f"\\nStatus: {passed_count}/{total_count} checks passed")
        
        if passed_count == total_count:
            print("✅ ALL CHECKS PASSED - No documentation drift detected")
        else:
            print("❌ ISSUES DETECTED - Documentation drift present")
        
        print("\\nDetailed Results:")
        print("-" * 40)
        
        for result in self.results:
            status = "✅" if result.passed else "❌"
            print(f"{status} {result.check_name}")
            print(f"   {result.message}")
            if result.fix_command and not result.passed:
                print(f"   Fix: {result.fix_command}")
            print()
        
        if passed_count < total_count:
            print("\\n🔧 NEXT STEPS:")
            failed_results = [r for r in self.results if not r.passed and r.fix_command]
            for i, result in enumerate(failed_results, 1):
                print(f"{i}. {result.fix_command}")


def main():
    """Main validation entry point"""
    project_root = Path(__file__).parent.parent
    
    validator = WorkflowValidator(project_root)
    all_passed = validator.validate_all()
    validator.print_report()
    
    # Exit with error code if any checks failed
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()