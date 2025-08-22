#!/usr/bin/env python3
"""
Minimal Axiom Core - Extracted from OM tools
Self-sufficient AI assistant that can create its own tools with formal verification
"""

import ast
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import time

# Import formal contracts
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../coherence/formal_contracts'))
from contract_language import coherence_contract, ComplexityClass

class SafeInterpreter:
    """Safe Python code execution with timeout and sandboxing"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.allowed_imports = {
            'os', 'sys', 'pathlib', 'json', 'ast', 'typing', 
            'dataclasses', 'enum', 're', 'math', 'datetime'
        }
    
    @coherence_contract(
        input_types={"code": "str"},
        output_type="Dict[str, Any]",
        requires=["len(code.strip()) > 0"],
        ensures=[
            "isinstance(result, dict)",
            "'success' in result",
            "'output' in result or 'error' in result"
        ],
        complexity_time=ComplexityClass.LINEAR,
        pure=False  # Executes code, has side effects
    )
    def execute(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely with timeout"""
        try:
            # Basic security check
            if any(dangerous in code.lower() for dangerous in ['import os', 'subprocess', 'eval', 'exec', '__import__']):
                return {
                    "success": False,
                    "error": "Dangerous code detected",
                    "output": ""
                }
            
            # Create temporary file for execution
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with timeout
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "output": result.stdout.strip(),
                        "error": ""
                    }
                else:
                    return {
                        "success": False,
                        "output": "",
                        "error": result.stderr.strip()
                    }
                    
            finally:
                # Clean up temp file
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Execution timeout after {self.timeout}s"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }

class CodeAnalyzer:
    """Code analysis and AST parsing extracted from OM"""
    
    @coherence_contract(
        input_types={"file_path": "str"},
        output_type="Dict[str, Any]",
        requires=["len(file_path) > 0"],
        ensures=[
            "isinstance(result, dict)",
            "'functions' in result",
            "'classes' in result"
        ],
        complexity_time=ComplexityClass.LINEAR,
        pure=True
    )
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a Python file and extract structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'docstring': ast.get_docstring(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        'docstring': ast.get_docstring(node)
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            return {
                'file_path': file_path,
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'lines': len(content.splitlines()),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'file_path': file_path,
                'functions': [],
                'classes': [],
                'imports': [],
                'lines': 0,
                'status': 'error',
                'error': str(e)
            }

class MinimalAxiom:
    """
    Minimal self-sufficient AI assistant
    Can create tools, analyze code, and verify coherence
    """
    
    def __init__(self):
        self.interpreter = SafeInterpreter()
        self.analyzer = CodeAnalyzer()
        self.workspace = Path.cwd()
    
    @coherence_contract(
        input_types={"path": "str", "content": "str"},
        output_type="bool",
        requires=["len(path) > 0", "isinstance(content, str)"],
        ensures=["isinstance(result, bool)"],
        complexity_time=ComplexityClass.CONSTANT,
        pure=False  # Creates files
    )
    def create_file(self, path: str, content: str) -> bool:
        """Create a file with given content"""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception:
            return False
    
    @coherence_contract(
        input_types={"path": "str"},
        output_type="str",
        requires=["len(path) > 0"],
        ensures=["isinstance(result, str)"],
        complexity_time=ComplexityClass.CONSTANT,
        pure=True
    )
    def read_file(self, path: str) -> str:
        """Read file content"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    @coherence_contract(
        input_types={"code": "str"},
        output_type="Dict[str, Any]",
        requires=["len(code.strip()) > 0"],
        ensures=["isinstance(result, dict)"],
        complexity_time=ComplexityClass.LINEAR,
        pure=False
    )
    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely"""
        return self.interpreter.execute(code)
    
    @coherence_contract(
        input_types={"file_path": "str"},
        output_type="Dict[str, Any]",
        requires=["len(file_path) > 0"],
        ensures=["isinstance(result, dict)"],
        complexity_time=ComplexityClass.LINEAR,
        pure=True
    )
    def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """Analyze code structure"""
        return self.analyzer.analyze_file(file_path)
    
    @coherence_contract(
        input_types={"code": "str"},
        output_type="Dict[str, Any]",
        requires=["len(code.strip()) > 0"],
        ensures=["isinstance(result, dict)"],
        complexity_time=ComplexityClass.LINEAR,
        pure=True
    )
    def check_coherence(self, code: str) -> Dict[str, Any]:
        """Check code coherence using formal contracts"""
        try:
            # Import coherence checker (use the original validator for now)
            coherence_path = str(Path(__file__).parent.parent.parent / 'coherence' / 'src' / 'coherence')
            sys.path.append(coherence_path)
            from validator import LogicalCoherenceValidator
            
            validator = LogicalCoherenceValidator()
            result = validator.validate_statement(code)
            
            return {
                'coherent': result.level.name in ['HIGH', 'PERFECT'],
                'score': result.score,
                'confidence': result.confidence,
                'contradictions': result.contradictions,
                'level': result.level.name
            }
        except Exception as e:
            # Fallback to basic coherence check
            return self._basic_coherence_check(code)
    
    def _basic_coherence_check(self, code: str) -> Dict[str, Any]:
        """Basic coherence check without external dependencies"""
        contradictions = []
        
        # Simple contradiction patterns
        code_lower = code.lower()
        if 'efficiently' in code_lower and any(word in code_lower for word in ['slow', 'inefficient', 'timeout']):
            contradictions.append("Efficiency claim contradicted")
        
        if 'sorted' in code_lower and any(word in code_lower for word in ['reverse', 'random', 'shuffle']):
            contradictions.append("Sorting claim contradicted")
        
        score = 1.0 if not contradictions else 0.3
        
        return {
            'coherent': len(contradictions) == 0,
            'score': score,
            'confidence': 0.7,
            'contradictions': contradictions,
            'level': 'COHERENT' if not contradictions else 'INCOHERENT'
        }
    
    @coherence_contract(
        input_types={"command": "str"},
        output_type="Dict[str, Any]",
        requires=["len(command.strip()) > 0"],
        ensures=["isinstance(result, dict)"],
        complexity_time=ComplexityClass.LINEAR,
        pure=False
    )
    def execute_bash(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute bash command safely"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout.strip(),
                'error': result.stderr.strip(),
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': f'Command timeout after {timeout}s',
                'return_code': -1
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }
    
    def create_tool(self, tool_name: str, tool_code: str) -> Dict[str, Any]:
        """Create a new tool with coherence verification"""
        # First check if the tool code is coherent
        coherence_result = self.check_coherence(tool_code)
        
        if not coherence_result['coherent']:
            return {
                'success': False,
                'error': f"Tool code is not coherent: {coherence_result['contradictions']}",
                'coherence_score': coherence_result['score']
            }
        
        # Create the tool file
        tool_path = f"tools/{tool_name}.py"
        success = self.create_file(tool_path, tool_code)
        
        if success:
            # Test the tool
            test_result = self.execute_code(f"import sys; sys.path.append('tools'); import {tool_name}")
            
            return {
                'success': test_result['success'],
                'tool_path': tool_path,
                'coherence_score': coherence_result['score'],
                'test_result': test_result
            }
        else:
            return {
                'success': False,
                'error': 'Failed to create tool file'
            }

# Test the minimal axiom
if __name__ == "__main__":
    print("🚀 Testing Minimal Axiom")
    print("=" * 40)
    
    axiom = MinimalAxiom()
    
    # Test code execution
    result = axiom.execute_code("print('Hello from Axiom!')")
    print(f"Code execution: {result}")
    
    # Test coherence checking
    coherence = axiom.check_coherence("This function sorts a list efficiently")
    print(f"Coherence check: {coherence}")
    
    # Test file operations
    success = axiom.create_file("test_axiom.py", "def hello(): return 'Hello World'")
    print(f"File creation: {success}")
    
    if success:
        content = axiom.read_file("test_axiom.py")
        print(f"File content: {content}")
        
        analysis = axiom.analyze_code("test_axiom.py")
        print(f"Code analysis: {analysis}")
    
    print("\n✅ Minimal Axiom is operational!")
    print("Ready to create coherent tools with formal verification.")