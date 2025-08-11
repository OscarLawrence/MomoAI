"""
Script discovery system for finding and executing scripts across the project.
"""

from pathlib import Path
from typing import List, Optional, Dict
import os


class ScriptDiscovery:
    """Discovers scripts across configured search paths."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.search_paths = self._get_search_paths()
    
    def _get_search_paths(self) -> List[Path]:
        """Get all script search paths from configuration."""
        from .config import ConfigManager
        
        config_manager = ConfigManager()
        return config_manager.get_script_paths()
    
    def find_script(self, script_name: str) -> Optional[Path]:
        """Find a script by name across all search paths."""
        # Try exact matches first
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
                
            # Try with various extensions
            candidates = [
                search_path / script_name,
                search_path / f"{script_name}.py",
                search_path / f"{script_name}.sh",
                search_path / f"{script_name}.js",
                search_path / f"{script_name}.ts",
            ]
            
            for candidate in candidates:
                if candidate.exists() and candidate.is_file():
                    return candidate
        
        # Try fuzzy matching (partial name matches)
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
                
            for file_path in search_path.iterdir():
                if file_path.is_file() and script_name in file_path.stem:
                    return file_path
        
        return None
    
    def list_available_scripts(self) -> Dict[str, List[Path]]:
        """List all available scripts organized by search path."""
        scripts = {}
        
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
                
            path_scripts = []
            for file_path in search_path.iterdir():
                if file_path.is_file() and self._is_executable_script(file_path):
                    path_scripts.append(file_path)
            
            if path_scripts:
                scripts[str(search_path)] = sorted(path_scripts)
        
        return scripts
    
    def _is_executable_script(self, file_path: Path) -> bool:
        """Check if a file appears to be an executable script."""
        # Check by extension
        if file_path.suffix in ['.py', '.sh', '.js', '.ts', '.mjs']:
            return True
        
        # Check if executable
        if os.access(file_path, os.X_OK):
            return True
        
        # Check for shebang
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                return first_line.startswith('#!')
        except:
            return False
    
    def find_scripts_by_pattern(self, pattern: str) -> List[Path]:
        """Find scripts matching a pattern."""
        matching_scripts = []
        
        for search_path in self.search_paths:
            if not search_path.exists():
                continue
                
            # Use glob pattern matching
            for script_path in search_path.glob(pattern):
                if script_path.is_file() and self._is_executable_script(script_path):
                    matching_scripts.append(script_path)
        
        return sorted(matching_scripts)
    
    def get_script_info(self, script_path: Path) -> Dict[str, str]:
        """Get information about a script."""
        info = {
            'name': script_path.stem,
            'path': str(script_path),
            'extension': script_path.suffix,
            'size': str(script_path.stat().st_size),
            'executable': str(os.access(script_path, os.X_OK)),
        }
        
        # Try to extract description from script
        try:
            with open(script_path, 'r') as f:
                lines = f.readlines()
                
                # Look for docstring or comment description
                description = None
                if script_path.suffix == '.py':
                    # Look for module docstring
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if line.startswith('"""') or line.startswith("'''"):
                            if line.count('"""') == 2 or line.count("'''") == 2:
                                # Single line docstring
                                description = line.strip('"""').strip("'''").strip()
                            else:
                                # Multi-line docstring
                                for j in range(i + 1, min(i + 5, len(lines))):
                                    if '"""' in lines[j] or "'''" in lines[j]:
                                        description = lines[i + 1].strip() if i + 1 < len(lines) else ""
                                        break
                            break
                else:
                    # Look for comment description
                    for line in lines[:10]:  # Check first 10 lines
                        line = line.strip()
                        if line.startswith('#') and len(line) > 2:
                            potential_desc = line[1:].strip()
                            if not potential_desc.startswith('!') and len(potential_desc) > 10:
                                description = potential_desc
                                break
                
                if description:
                    info['description'] = description
                    
        except:
            pass  # Ignore errors reading file
        
        return info