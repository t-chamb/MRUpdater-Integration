#!/usr/bin/env python3
"""
Test script for import integration and conflict resolution.

This script validates that all imports work correctly after integration
and that conflicts between original and decompiled versions are resolved.
"""

import sys
import logging
from typing import Dict, List, Any
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_basic_imports() -> Dict[str, bool]:
    """Test basic Python standard library imports."""
    results = {}
    
    basic_imports = [
        'os', 'sys', 'logging', 'pathlib', 'typing',
        'configparser', 'hashlib', 'time', 'json'
    ]
    
    for module_name in basic_imports:
        try:
            __import__(module_name)
            results[module_name] = True
            logger.debug(f"✓ {module_name}")
        except ImportError as e:
            results[module_name] = False
            logger.error(f"✗ {module_name}: {e}")
            
    return results

def test_third_party_imports() -> Dict[str, bool]:
    """Test third-party library imports."""
    results = {}
    
    third_party_imports = [
        'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
        'serial', 'usb.core', 'boto3', 'requests',
        'esptool.loader', 'statemachine', 'platformdirs'
    ]
    
    for module_name in third_party_imports:
        try:
            __import__(module_name)
            results[module_name] = True
            logger.debug(f"✓ {module_name}")
        except ImportError as e:
            results[module_name] = False
            logger.warning(f"✗ {module_name}: {e}")
            
    return results

def test_compatibility_layer() -> Dict[str, bool]:
    """Test the import compatibility layer."""
    results = {}
    
    try:
        from import_compatibility import (
            get_compatibility_info, check_required_dependencies,
            resolve_decompiled_imports, log_compatibility_status
        )
        results['import_compatibility'] = True
        logger.info("✓ Import compatibility layer loaded")
        
        # Test compatibility info
        info = get_compatibility_info()
        results['compatibility_info'] = isinstance(info, dict) and len(info) > 0
        logger.info(f"✓ Compatibility info: {len(info)} libraries checked")
        
        # Test dependency checking
        required_deps = ['qt', 'serial', 'usb']
        dep_results = check_required_dependencies(required_deps)
        results['dependency_check'] = isinstance(dep_results, dict)
        logger.info(f"✓ Dependency check: {sum(dep_results.values())}/{len(dep_results)} available")
        
        # Test decompiled import resolution
        resolved = resolve_decompiled_imports()
        results['decompiled_resolution'] = isinstance(resolved, dict)
        available_count = sum(1 for r in resolved.values() if r['available'])
        logger.info(f"✓ Decompiled resolution: {available_count}/{len(resolved)} modules resolved")
        
        # Log compatibility status
        log_compatibility_status()
        
    except Exception as e:
        results['import_compatibility'] = False
        logger.error(f"✗ Import compatibility layer failed: {e}")
        
    return results

def test_unified_resolver() -> Dict[str, bool]:
    """Test the unified import resolver."""
    results = {}
    
    try:
        from unified_import_resolver import (
            get_resolver, resolve_import, 
            register_conflict_resolution, register_import_alias
        )
        results['unified_resolver'] = True
        logger.info("✓ Unified import resolver loaded")
        
        resolver = get_resolver()
        results['resolver_instance'] = resolver is not None
        
        # Test resolving some imports
        test_modules = [
            'cartclinic.gui',
            'flashing_tool.chromatic',
            'libpyretro.cartclinic.comms'
        ]
        
        resolved_count = 0
        for module_name in test_modules:
            result = resolve_import(module_name)
            if result:
                resolved_count += 1
                logger.debug(f"✓ Resolved: {module_name}")
            else:
                logger.debug(f"✗ Failed to resolve: {module_name}")
                
        results['module_resolution'] = resolved_count > 0
        logger.info(f"✓ Module resolution: {resolved_count}/{len(test_modules)} modules")
        
        # Test import map generation
        import_map = resolver.generate_import_map()
        results['import_map'] = isinstance(import_map, dict)
        logger.info(f"✓ Import map: {import_map['total_resolved']} resolved imports")
        
    except Exception as e:
        results['unified_resolver'] = False
        logger.error(f"✗ Unified import resolver failed: {e}")
        
    return results

def test_application_imports() -> Dict[str, bool]:
    """Test application-specific imports."""
    results = {}
    
    app_imports = [
        'cartclinic',
        'cartclinic.gui', 
        'cartclinic.cartridge_read',
        'cartclinic.cartridge_write',
        'cartclinic.consts',
        'cartclinic.exceptions',
        'flashing_tool',
        'flashing_tool.chromatic',
        'flashing_tool.util',
        'flashing_tool.gui',
        'libpyretro',
        'libpyretro.cartclinic',
        'config',
        'error_handler'
    ]
    
    for module_name in app_imports:
        try:
            __import__(module_name)
            results[module_name] = True
            logger.debug(f"✓ {module_name}")
        except ImportError as e:
            results[module_name] = False
            logger.warning(f"✗ {module_name}: {e}")
            
    return results

def test_circular_dependencies() -> Dict[str, bool]:
    """Test for circular dependencies."""
    results = {}
    
    try:
        from dependency_resolver import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer(".")
        dependencies = analyzer.analyze_directory()
        circular_deps = analyzer.find_circular_dependencies()
        
        results['dependency_analysis'] = True
        results['no_circular_deps'] = len(circular_deps) == 0
        
        if circular_deps:
            logger.warning(f"Found {len(circular_deps)} circular dependencies:")
            for i, cycle in enumerate(circular_deps, 1):
                logger.warning(f"  Cycle {i}: {' -> '.join(cycle)}")
        else:
            logger.info("✓ No circular dependencies found")
            
    except Exception as e:
        results['dependency_analysis'] = False
        logger.error(f"✗ Dependency analysis failed: {e}")
        
    return results

def generate_test_report(all_results: Dict[str, Dict[str, bool]]) -> str:
    """Generate a comprehensive test report."""
    report = ["# Import Integration Test Report\n"]
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        report.append(f"## {category.replace('_', ' ').title()}\n")
        
        category_passed = 0
        category_total = len(results)
        
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            report.append(f"- {test_name}: {status}")
            if passed:
                category_passed += 1
                
        report.append(f"\n**Category Summary: {category_passed}/{category_total} tests passed**\n")
        
        total_tests += category_total
        passed_tests += category_passed
        
    # Overall summary
    report.insert(1, f"**Overall Summary: {passed_tests}/{total_tests} tests passed**\n")
    
    return "\n".join(report)

def main():
    """Run all import integration tests."""
    logger.info("Starting import integration tests...")
    
    all_results = {}
    
    # Run all test categories
    test_categories = [
        ("basic_imports", test_basic_imports),
        ("third_party_imports", test_third_party_imports), 
        ("compatibility_layer", test_compatibility_layer),
        ("unified_resolver", test_unified_resolver),
        ("application_imports", test_application_imports),
        ("circular_dependencies", test_circular_dependencies)
    ]
    
    for category_name, test_func in test_categories:
        logger.info(f"Running {category_name}...")
        try:
            results = test_func()
            all_results[category_name] = results
            passed = sum(results.values())
            total = len(results)
            logger.info(f"✓ {category_name}: {passed}/{total} tests passed")
        except Exception as e:
            logger.error(f"✗ {category_name} failed: {e}")
            all_results[category_name] = {"error": False}
            
    # Generate and save report
    report = generate_test_report(all_results)
    
    with open("import_integration_test_report.md", "w") as f:
        f.write(report)
        
    logger.info("Test report saved to: import_integration_test_report.md")
    
    # Print summary
    total_tests = sum(len(results) for results in all_results.values())
    passed_tests = sum(
        sum(results.values()) for results in all_results.values()
        if all(isinstance(v, bool) for v in results.values())
    )
    
    logger.info(f"Overall result: {passed_tests}/{total_tests} tests passed")
    
    # Exit with appropriate code
    if passed_tests == total_tests:
        logger.info("All tests passed! ✓")
        sys.exit(0)
    else:
        logger.warning(f"{total_tests - passed_tests} tests failed! ✗")
        sys.exit(1)

if __name__ == "__main__":
    main()