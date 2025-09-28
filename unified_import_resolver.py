"""
Unified import resolver for MRUpdater integration.

This module provides a centralized way to resolve import conflicts between
the original codebase and decompiled enhancements, ensuring compatibility
and proper dependency management.
"""

import sys
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import importlib.util

logger = logging.getLogger(__name__)

class ImportResolver:
    """Resolves import conflicts and manages unified imports."""
    
    def __init__(self):
        self.resolved_imports: Dict[str, Any] = {}
        self.conflict_resolutions: Dict[str, str] = {}
        self.import_aliases: Dict[str, str] = {}
        
    def register_conflict_resolution(self, original_module: str, 
                                   decompiled_module: str, 
                                   resolution: str):
        """Register a resolution strategy for conflicting imports."""
        conflict_key = f"{original_module}:{decompiled_module}"
        self.conflict_resolutions[conflict_key] = resolution
        logger.info(f"Registered conflict resolution: {conflict_key} -> {resolution}")
        
    def register_import_alias(self, original_name: str, alias_name: str):
        """Register an alias for an import to avoid conflicts."""
        self.import_aliases[original_name] = alias_name
        logger.info(f"Registered import alias: {original_name} -> {alias_name}")
        
    def resolve_import(self, module_name: str, 
                      prefer_original: bool = True) -> Optional[Any]:
        """
        Resolve an import, handling conflicts between original and decompiled versions.
        
        Args:
            module_name: Name of the module to import
            prefer_original: Whether to prefer original over decompiled version
            
        Returns:
            The resolved module or None if not found
        """
        # Check if we already resolved this import
        if module_name in self.resolved_imports:
            return self.resolved_imports[module_name]
            
        # Check for aliases
        if module_name in self.import_aliases:
            actual_name = self.import_aliases[module_name]
            logger.debug(f"Using alias {actual_name} for {module_name}")
            module_name = actual_name
            
        # Try to import the module
        try:
            module = importlib.import_module(module_name)
            self.resolved_imports[module_name] = module
            logger.debug(f"Successfully imported {module_name}")
            return module
        except ImportError as e:
            logger.warning(f"Failed to import {module_name}: {e}")
            
            # Try alternative import strategies
            alternative = self._try_alternative_imports(module_name)
            if alternative:
                self.resolved_imports[module_name] = alternative
                return alternative
                
        return None
        
    def _try_alternative_imports(self, module_name: str) -> Optional[Any]:
        """Try alternative import strategies for failed imports."""
        
        # Strategy 1: Try importing from different locations
        alternative_paths = [
            f"decompiled.{module_name}",
            f"MRUpdater_DECOMPILED.{module_name}",
            f"libpyretro.{module_name}",
            f"cartclinic.{module_name}",
            f"flashing_tool.{module_name}"
        ]
        
        for alt_path in alternative_paths:
            try:
                module = importlib.import_module(alt_path)
                logger.info(f"Found alternative import: {alt_path} for {module_name}")
                return module
            except ImportError:
                continue
                
        # Strategy 2: Try partial imports
        if '.' in module_name:
            parent_module = module_name.rsplit('.', 1)[0]
            child_name = module_name.rsplit('.', 1)[1]
            
            try:
                parent = importlib.import_module(parent_module)
                if hasattr(parent, child_name):
                    child = getattr(parent, child_name)
                    logger.info(f"Found {child_name} in {parent_module}")
                    return child
            except ImportError:
                pass
                
        return None
        
    def create_unified_module(self, module_name: str, 
                            original_module: Any, 
                            decompiled_module: Any) -> Any:
        """
        Create a unified module that combines functionality from both versions.
        
        Args:
            module_name: Name of the unified module
            original_module: Original module implementation
            decompiled_module: Decompiled module implementation
            
        Returns:
            Unified module with combined functionality
        """
        class UnifiedModule:
            def __init__(self, name: str, original: Any, decompiled: Any):
                self.__name__ = name
                self._original = original
                self._decompiled = decompiled
                
                # Copy attributes from both modules, preferring original
                if original:
                    for attr_name in dir(original):
                        if not attr_name.startswith('_'):
                            setattr(self, attr_name, getattr(original, attr_name))
                            
                # Add enhanced attributes from decompiled version
                if decompiled:
                    for attr_name in dir(decompiled):
                        if not attr_name.startswith('_'):
                            # Only add if not already present or if it's an enhancement
                            if not hasattr(self, attr_name) or self._is_enhancement(attr_name, decompiled):
                                enhanced_attr = getattr(decompiled, attr_name)
                                setattr(self, f"enhanced_{attr_name}", enhanced_attr)
                                
            def _is_enhancement(self, attr_name: str, decompiled_module: Any) -> bool:
                """Check if an attribute from decompiled version is an enhancement."""
                # Simple heuristic: if the decompiled version has more functionality
                try:
                    original_attr = getattr(self._original, attr_name, None)
                    decompiled_attr = getattr(decompiled_module, attr_name, None)
                    
                    if original_attr and decompiled_attr:
                        # If both are functions, check if decompiled has more parameters
                        if callable(original_attr) and callable(decompiled_attr):
                            try:
                                import inspect
                                orig_params = len(inspect.signature(original_attr).parameters)
                                decomp_params = len(inspect.signature(decompiled_attr).parameters)
                                return decomp_params > orig_params
                            except:
                                pass
                                
                    return False
                except:
                    return False
                    
        unified = UnifiedModule(module_name, original_module, decompiled_module)
        self.resolved_imports[module_name] = unified
        logger.info(f"Created unified module: {module_name}")
        return unified
        
    def resolve_circular_dependency(self, cycle: List[str]) -> Dict[str, str]:
        """
        Resolve circular dependencies by suggesting import restructuring.
        
        Args:
            cycle: List of modules in the circular dependency
            
        Returns:
            Dictionary of suggested fixes
        """
        suggestions = {}
        
        if len(cycle) < 2:
            return suggestions
            
        # Identify the weakest link in the cycle
        weakest_link = self._find_weakest_link(cycle)
        
        suggestions[f"break_cycle_{weakest_link}"] = (
            f"Use lazy import in {weakest_link} to break circular dependency"
        )
        
        # Suggest creating a common module
        common_functionality = self._identify_common_functionality(cycle)
        if common_functionality:
            suggestions["create_common_module"] = (
                f"Create common module for shared functionality: {common_functionality}"
            )
            
        return suggestions
        
    def _find_weakest_link(self, cycle: List[str]) -> str:
        """Find the weakest link in a circular dependency cycle."""
        # Simple heuristic: the module with the fewest dependencies
        dependency_counts = {}
        
        for module in cycle:
            try:
                imported_module = importlib.import_module(module)
                # Count the number of imports (rough estimate)
                dependency_counts[module] = len([
                    attr for attr in dir(imported_module) 
                    if not attr.startswith('_')
                ])
            except ImportError:
                dependency_counts[module] = 0
                
        return min(dependency_counts, key=dependency_counts.get)
        
    def _identify_common_functionality(self, cycle: List[str]) -> List[str]:
        """Identify common functionality that could be extracted."""
        common_functions = []
        
        # This is a simplified implementation
        # In practice, you'd analyze the actual code to find common patterns
        common_patterns = [
            "validate_", "parse_", "format_", "convert_", 
            "handle_error", "log_", "check_"
        ]
        
        for pattern in common_patterns:
            if any(pattern in module for module in cycle):
                common_functions.append(pattern)
                
        return common_functions
        
    def generate_import_map(self) -> Dict[str, Any]:
        """Generate a map of all resolved imports for debugging."""
        return {
            "resolved_imports": list(self.resolved_imports.keys()),
            "conflict_resolutions": self.conflict_resolutions,
            "import_aliases": self.import_aliases,
            "total_resolved": len(self.resolved_imports)
        }

# Global import resolver instance
_resolver = ImportResolver()

def get_resolver() -> ImportResolver:
    """Get the global import resolver instance."""
    return _resolver

def resolve_import(module_name: str, prefer_original: bool = True) -> Optional[Any]:
    """Convenience function to resolve an import."""
    return _resolver.resolve_import(module_name, prefer_original)

def register_conflict_resolution(original: str, decompiled: str, resolution: str):
    """Convenience function to register conflict resolution."""
    _resolver.register_conflict_resolution(original, decompiled, resolution)

def register_import_alias(original: str, alias: str):
    """Convenience function to register import alias."""
    _resolver.register_import_alias(original, alias)

# Pre-register known conflict resolutions
def setup_known_resolutions():
    """Set up known conflict resolutions."""
    
    # Qt framework conflicts
    register_conflict_resolution(
        "PySide6", "PyQt6", 
        "Use PySide6 (preferred) with PyQt6 fallback via import_compatibility"
    )
    
    # USB library conflicts
    register_conflict_resolution(
        "usb.core", "pyusb", 
        "Use pyusb with compatibility layer"
    )
    
    # Serial communication conflicts
    register_conflict_resolution(
        "serial", "pyserial", 
        "Use pyserial as standard serial implementation"
    )
    
    # State machine conflicts
    register_conflict_resolution(
        "statemachine", "python-statemachine", 
        "Use python-statemachine as standard implementation"
    )
    
    # Register common aliases
    register_import_alias("cartclinic.enhanced_gui", "cartclinic.gui")
    register_import_alias("flashing_tool.enhanced_chromatic", "flashing_tool.chromatic")
    register_import_alias("libpyretro.enhanced_comms", "libpyretro.cartclinic.comms")

# Set up known resolutions on import
setup_known_resolutions()

if __name__ == "__main__":
    # Test the import resolver
    resolver = get_resolver()
    
    # Test resolving some common imports
    test_imports = [
        "cartclinic.gui",
        "flashing_tool.chromatic", 
        "libpyretro.cartclinic.comms",
        "PySide6.QtCore",
        "serial"
    ]
    
    print("Testing import resolution:")
    for module_name in test_imports:
        result = resolver.resolve_import(module_name)
        status = "✓" if result else "✗"
        print(f"{status} {module_name}")
        
    # Print import map
    import_map = resolver.generate_import_map()
    print(f"\nResolved {import_map['total_resolved']} imports")
    print(f"Conflict resolutions: {len(import_map['conflict_resolutions'])}")
    print(f"Import aliases: {len(import_map['import_aliases'])}")