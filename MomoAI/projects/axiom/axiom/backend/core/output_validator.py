"""
AI Output Contract Validator for Axiom
Validates AI responses for formal contracts and mathematical correctness
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import ast

from .contracts import coherence_contract, ComplexityClass, FormalContract, get_contract_info


@dataclass
class ValidationResult:
    """Result of AI output validation"""
    has_contracts: bool
    contracts_valid: bool
    contracts_verified: bool
    violations: List[str]
    suggestions: List[str]
    confidence: float


class AIOutputValidator:
    """
    Validates AI responses for formal contracts and implementation correctness
    Ensures AI output meets mathematical specifications
    """
    
    def __init__(self):
        self.contract_pattern = r"@coherence_contract\s*\("
        self.complexity_patterns = {
            "O(1)": [r"for\s+\w+\s+in", r"while\s+\w+"],
            "O(n)": [r"for\s+\w+\s+in\s+\w+:", r"while.*len\("],
            "O(n²)": [r"for.*for.*in", r"nested.*loop"]
        }
    
    @coherence_contract(
        input_types={"ai_response": "str"},
        output_type="ValidationResult",
        requires=["len(ai_response.strip()) > 0"],
        complexity_time=ComplexityClass.LINEAR,
        pure=True
    )
    def validate_response(self, ai_response: str) -> ValidationResult:
        """Check if AI response has proper formal contracts"""
        contracts = self.extract_contracts(ai_response)
        has_contracts = len(contracts) > 0
        
        violations = []
        suggestions = []
        
        if not has_contracts:
            violations.append("No formal contracts found in AI response")
            suggestions.append("Add @coherence_contract decorators to all functions")
        
        contracts_valid = True
        contracts_verified = True
        
        for contract_info in contracts:
            # Validate contract structure
            if not self._validate_contract_structure(contract_info):
                contracts_valid = False
                violations.append(f"Invalid contract structure in {contract_info.get('function_name', 'unknown')}")
            
            # Verify implementation matches contract
            if not self._verify_implementation(contract_info, ai_response):
                contracts_verified = False
                violations.append(f"Implementation doesn't match contract in {contract_info.get('function_name', 'unknown')}")
        
        confidence = self._calculate_confidence(ai_response, contracts, violations)
        
        return ValidationResult(
            has_contracts=has_contracts,
            contracts_valid=contracts_valid,
            contracts_verified=contracts_verified,
            violations=violations,
            suggestions=suggestions,
            confidence=confidence
        )
    
    @coherence_contract(
        input_types={"code": "str"},
        output_type="List[Dict[str, Any]]",
        complexity_time=ComplexityClass.LINEAR,
        pure=True
    )
    def extract_contracts(self, code: str) -> List[Dict[str, Any]]:
        """Extract @coherence_contract decorators from code"""
        contracts = []
        
        # Find all contract decorators
        contract_matches = re.finditer(self.contract_pattern, code, re.MULTILINE | re.DOTALL)
        
        for match in contract_matches:
            try:
                # Extract the full decorator and function
                start_pos = match.start()
                
                # Find the matching function
                lines = code[start_pos:].split('\n')
                decorator_lines = []
                function_line = None
                
                in_decorator = True
                paren_count = 0
                
                for i, line in enumerate(lines):
                    if in_decorator:
                        decorator_lines.append(line)
                        paren_count += line.count('(') - line.count(')')
                        if paren_count == 0 and ')' in line:
                            in_decorator = False
                    elif line.strip().startswith('def '):
                        function_line = line
                        break
                
                if function_line:
                    # Parse the decorator parameters
                    decorator_text = '\n'.join(decorator_lines)
                    contract_info = self._parse_decorator(decorator_text, function_line)
                    if contract_info:
                        contracts.append(contract_info)
                        
            except Exception as e:
                # Skip malformed contracts
                continue
        
        return contracts
    
    def _parse_decorator(self, decorator_text: str, function_line: str) -> Optional[Dict[str, Any]]:
        """Parse decorator parameters and function signature"""
        try:
            # Extract function name
            func_match = re.search(r'def\s+(\w+)', function_line)
            if not func_match:
                return None
            
            function_name = func_match.group(1)
            
            # Extract decorator parameters (simplified parsing)
            contract_info = {"function_name": function_name}
            
            # Look for common contract parameters
            if "complexity_time" in decorator_text:
                complexity_match = re.search(r'complexity_time[=:]\s*["\']?([^,\)"\'\s]+)', decorator_text)
                if complexity_match:
                    contract_info["complexity_time"] = complexity_match.group(1)
            
            if "pure" in decorator_text:
                pure_match = re.search(r'pure[=:]\s*(True|False)', decorator_text)
                if pure_match:
                    contract_info["is_pure"] = pure_match.group(1) == "True"
            
            if "requires" in decorator_text:
                requires_match = re.search(r'requires[=:]\s*\[(.*?)\]', decorator_text, re.DOTALL)
                if requires_match:
                    contract_info["preconditions"] = [req.strip().strip('"\'') for req in requires_match.group(1).split(',') if req.strip()]
            
            if "ensures" in decorator_text:
                ensures_match = re.search(r'ensures[=:]\s*\[(.*?)\]', decorator_text, re.DOTALL)
                if ensures_match:
                    contract_info["postconditions"] = [ens.strip().strip('"\'') for ens in ensures_match.group(1).split(',') if ens.strip()]
            
            return contract_info
            
        except Exception:
            return None
    
    def _validate_contract_structure(self, contract_info: Dict[str, Any]) -> bool:
        """Validate that contract has required fields"""
        required_fields = ["function_name"]
        return all(field in contract_info for field in required_fields)
    
    def _verify_implementation(self, contract_info: Dict[str, Any], code: str) -> bool:
        """Verify code satisfies formal contract"""
        function_name = contract_info.get("function_name")
        if not function_name:
            return False
        
        # Extract function implementation
        func_pattern = rf'def\s+{function_name}\s*\([^)]*\):[^:]*?(?=\n\s*def|\n\s*class|\n\s*@|\Z)'
        func_match = re.search(func_pattern, code, re.DOTALL)
        
        if not func_match:
            return False
        
        func_code = func_match.group(0)
        
        # Verify complexity claims
        complexity_time = contract_info.get("complexity_time")
        if complexity_time:
            if not self._verify_complexity(func_code, complexity_time):
                return False
        
        # Verify purity claims
        is_pure = contract_info.get("is_pure", False)
        if is_pure:
            if not self._verify_purity(func_code):
                return False
        
        return True
    
    def _verify_complexity(self, func_code: str, claimed_complexity: str) -> bool:
        """Verify function complexity matches claim"""
        # Simple heuristic-based complexity verification
        
        if claimed_complexity in ["O(1)", "CONSTANT"]:
            # O(1) functions shouldn't have loops
            if re.search(r'\bfor\b|\bwhile\b', func_code):
                return False
        
        elif claimed_complexity in ["O(n)", "LINEAR"]:
            # O(n) functions should have at most one level of loops
            nested_loops = re.findall(r'for.*?for|while.*?while', func_code, re.DOTALL)
            if len(nested_loops) > 0:
                return False
        
        elif claimed_complexity in ["O(n²)", "QUADRATIC"]:
            # O(n²) functions can have nested loops
            pass  # More permissive
        
        return True
    
    def _verify_purity(self, func_code: str) -> bool:
        """Verify function is pure (no side effects)"""
        # Check for common side effect patterns
        side_effect_patterns = [
            r'\bprint\b', r'\bopen\b', r'\.write\b', r'\.append\b',
            r'global\b', r'nonlocal\b', r'\.pop\b', r'\.remove\b'
        ]
        
        for pattern in side_effect_patterns:
            if re.search(pattern, func_code):
                return False
        
        return True
    
    def _calculate_confidence(self, ai_response: str, contracts: List[Dict], violations: List[str]) -> float:
        """Calculate confidence in validation result"""
        base_confidence = 0.8
        
        # Higher confidence with more contracts
        contract_bonus = min(0.2, len(contracts) * 0.05)
        
        # Lower confidence with violations
        violation_penalty = len(violations) * 0.1
        
        # Higher confidence with longer, more detailed code
        code_length_bonus = min(0.1, len(ai_response.split()) * 0.0001)
        
        return max(0.1, min(1.0, base_confidence + contract_bonus + code_length_bonus - violation_penalty))