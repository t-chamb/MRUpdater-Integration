"""
Dependency resolver for MRUpdater integration.

This module helps identify and resolve circular dependencies between modules
during the integration process.
"""

import ast
import os
import sys
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DependencyAnalyzer:
    """Analyzes Python modules for import dependencies."""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.dependencies: Dict[str, Set[str]] = {}
        self.circular_deps: List[List[str]] = []
        
    def analyze_file(self, file_path: Path) -> Set[str]:
        """Analyze a single Python file for its imports."""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
                        
        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"Could not parse {file_path}: {e}")
            
        return imports
    
    def get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        relative_path = file_path.relative_to(self.root_path)
        if relative_path.name == '__init__.py':
            module_parts = relative_path.parent.parts
        else:
            module_parts = relative_path.with_suffix('').parts
            
        return '.'.join(module_parts)
    
    def analyze_directory(self, directory: Optional[Path] = None) -> Dict[str, Set[str]]:
        """Analyze all Python files in a directory for dependencies."""
        if directory is None:
            directory = self.root_path
            
        for py_file in directory.rglob('*.py'):
            if py_file.name.startswith('.'):
                continue
                
            module_name = self.get_module_name(py_file)
            imports = self.analyze_file(py_file)
            
            # Filter to only local imports (within our codebase)
            local_imports = set()
            for imp in imports:
                if self._is_local_import(imp):
                    local_imports.add(imp)
                    
            self.dependencies[module_name] = local_imports
            
        return self.dependencies
    
    def _is_local_import(self, import_name: str) -> bool:
        """Check if an import is local to our codebase."""
        # Check if it's a relative import or starts with our package names
        local_packages = ['cartclinic', 'flashing_tool', 'libpyretro']
        return any(import_name.startswith(pkg) for pkg in local_packages)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
                
            if node in visited:
                return False
                
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.dependencies.get(node, set()):
                if neighbor in self.dependencies:  # Only check modules we know about
                    dfs(neighbor, path.copy())
                    
            rec_stack.remove(node)
            return False
        
        for module in self.dependencies:
            if module not in visited:
                dfs(module, [])
                
        self.circular_deps = cycles
        return cycles
    
    def suggest_fixes(self, circular_deps: List[List[str]]) -> Dict[str, List[str]]:
        """Suggest fixes for circular dependencies."""
        suggestions = {}
        
        for cycle in circular_deps:
            cycle_key = ' -> '.join(cycle)
            fixes = []
            
            # Suggest moving common functionality to a separate module
            fixes.append(f"Create a common module for shared functionality between {cycle[0]} and {cycle[-2]}")
            
            # Suggest using lazy imports
            fixes.append(f"Use lazy imports in {cycle[0]} to break the cycle")
            
            # Suggest dependency injection
            fixes.append(f"Use dependency injection instead of direct imports between {cycle[0]} and {cycle[-2]}")
            
            suggestions[cycle_key] = fixes
            
        return suggestions

class ImportConflictResolver:
    """Resolves import conflicts between different codebases."""
    
    def __init__(self):
        self.conflicts: Dict[str, List[str]] = {}
        self.resolutions: Dict[str, str] = {}
        
    def detect_conflicts(self, original_deps: Dict[str, Set[str]], 
                        decompiled_deps: Dict[str, Set[str]]) -> Dict[str, List[str]]:
        """Detect conflicts between original and decompiled dependencies."""
        conflicts = {}
        
        # Find modules that exist in both codebases
        common_modules = set(original_deps.keys()) & set(decompiled_deps.keys())
        
        for module in common_modules:
            orig_imports = original_deps[module]
            decomp_imports = decompiled_deps[module]
            
            # Find conflicting imports
            conflicting = []
            
            # Check for different import patterns for the same functionality
            for orig_imp in orig_imports:
                for decomp_imp in decomp_imports:
                    if self._are_conflicting_imports(orig_imp, decomp_imp):
                        conflicting.append((orig_imp, decomp_imp))
                        
            if conflicting:
                conflicts[module] = conflicting
                
        self.conflicts = conflicts
        return conflicts
    
    def _are_conflicting_imports(self, import1: str, import2: str) -> bool:
        """Check if two imports are conflicting (same functionality, different modules)."""
        # Define known conflicting patterns
        conflict_patterns = [
            ('PySide6', 'PyQt6'),
            ('PySide6', 'PyQt5'),
            ('PyQt6', 'PyQt5'),
        ]
        
        for pattern1, pattern2 in conflict_patterns:
            if pattern1 in import1 and pattern2 in import2:
                return True
            if pattern2 in import1 and pattern1 in import2:
                return True
                
        return False
    
    def resolve_conflicts(self) -> Dict[str, str]:
        """Provide resolutions for detected conflicts."""
        resolutions = {}
        
        for module, conflicts in self.conflicts.items():
            for orig_imp, decomp_imp in conflicts:
                # Prefer more modern/stable versions
                if 'PySide6' in orig_imp or 'PySide6' in decomp_imp:
                    resolutions[f"{module}:{orig_imp}:{decomp_imp}"] = "Use PySide6 (more modern and stable)"
                elif 'PyQt6' in orig_imp or 'PyQt6' in decomp_imp:
                    resolutions[f"{module}:{orig_imp}:{decomp_imp}"] = "Use PyQt6 (if PySide6 not available)"
                else:
                    resolutions[f"{module}:{orig_imp}:{decomp_imp}"] = "Use compatibility layer to handle both"
                    
        self.resolutions = resolutions
        return resolutions

def analyze_codebase_dependencies(root_path: str) -> Tuple[Dict[str, Set[str]], List[List[str]]]:
    """Analyze a codebase for dependencies and circular imports."""
    analyzer = DependencyAnalyzer(root_path)
    dependencies = analyzer.analyze_directory()
    circular_deps = analyzer.find_circular_dependencies()
    
    return dependencies, circular_deps

def generate_dependency_report(root_path: str, output_file: str = "dependency_report.md"):
    """Generate a comprehensive dependency analysis report."""
    analyzer = DependencyAnalyzer(root_path)
    dependencies = analyzer.analyze_directory()
    circular_deps = analyzer.find_circular_dependencies()
    suggestions = analyzer.suggest_fixes(circular_deps)
    
    with open(output_file, 'w') as f:
        f.write("# Dependency Analysis Report\n\n")
        
        f.write("## Module Dependencies\n\n")
        for module, deps in sorted(dependencies.items()):
            f.write(f"### {module}\n")
            if deps:
                for dep in sorted(deps):
                    f.write(f"- {dep}\n")
            else:
                f.write("- No local dependencies\n")
            f.write("\n")
            
        f.write("## Circular Dependencies\n\n")
        if circular_deps:
            for i, cycle in enumerate(circular_deps, 1):
                f.write(f"### Cycle {i}\n")
                f.write(" -> ".join(cycle) + "\n\n")
                
                cycle_key = ' -> '.join(cycle)
                if cycle_key in suggestions:
                    f.write("**Suggested Fixes:**\n")
                    for fix in suggestions[cycle_key]:
                        f.write(f"- {fix}\n")
                    f.write("\n")
        else:
            f.write("No circular dependencies found.\n\n")
            
    logger.info(f"Dependency report generated: {output_file}")

if __name__ == "__main__":
    # Generate reports for both codebases
    print("Analyzing current codebase...")
    generate_dependency_report(".", "current_dependencies.md")
    
    if os.path.exists("MRUpdater_DECOMPILED"):
        print("Analyzing decompiled codebase...")
        generate_dependency_report("MRUpdater_DECOMPILED", "decompiled_dependencies.md")
        
        # Compare and find conflicts
        current_analyzer = DependencyAnalyzer(".")
        current_deps = current_analyzer.analyze_directory()
        
        decompiled_analyzer = DependencyAnalyzer("MRUpdater_DECOMPILED")
        decompiled_deps = decompiled_analyzer.analyze_directory()
        
        resolver = ImportConflictResolver()
        conflicts = resolver.detect_conflicts(current_deps, decompiled_deps)
        resolutions = resolver.resolve_conflicts()
        
        with open("import_conflicts.md", 'w') as f:
            f.write("# Import Conflict Analysis\n\n")
            
            if conflicts:
                f.write("## Detected Conflicts\n\n")
                for module, conflict_list in conflicts.items():
                    f.write(f"### {module}\n")
                    for orig, decomp in conflict_list:
                        f.write(f"- Original: `{orig}`\n")
                        f.write(f"- Decompiled: `{decomp}`\n")
                    f.write("\n")
                    
                f.write("## Suggested Resolutions\n\n")
                for conflict, resolution in resolutions.items():
                    f.write(f"- **{conflict}**: {resolution}\n")
            else:
                f.write("No import conflicts detected.\n")
                
        print("Import conflict analysis complete: import_conflicts.md")