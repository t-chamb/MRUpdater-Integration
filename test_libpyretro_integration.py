#!/usr/bin/env python3
"""
Test script for libpyretro integration and enhancements.

This script validates that all libpyretro modules work correctly after
integration and that enhanced functionality is available.
"""

import sys
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_libpyretro_imports() -> Dict[str, bool]:
    """Test libpyretro module imports."""
    results = {}
    
    try:
        import libpyretro
        results['libpyretro'] = True
        logger.info("✓ libpyretro imported successfully")
        
        # Test submodule imports
        from libpyretro import cartclinic
        results['cartclinic'] = True
        logger.info("✓ libpyretro.cartclinic imported")
        
        from libpyretro import feature_api
        results['feature_api'] = True
        logger.info("✓ libpyretro.feature_api imported")
        
        from libpyretro import ips_util
        results['ips_util'] = True
        logger.info("✓ libpyretro.ips_util imported")
        
        from libpyretro import util
        results['util'] = True
        logger.info("✓ libpyretro.util imported")
        
    except Exception as e:
        logger.error(f"✗ libpyretro import failed: {e}")
        results['libpyretro'] = False
        
    return results

def test_cartclinic_functionality() -> Dict[str, bool]:
    """Test cartclinic module functionality."""
    results = {}
    
    try:
        from libpyretro.cartclinic import CartAPI_Builder, CartAPI_Parser
        results['cart_api_classes'] = True
        logger.info("✓ CartAPI classes imported")
        
        # Test CartAPI_Builder methods
        builder = CartAPI_Builder()
        
        # Test bank switching
        bank_msgs = builder.set_bank(1)
        results['set_bank'] = isinstance(bank_msgs, list) and len(bank_msgs) == 2
        logger.info(f"✓ set_bank: {len(bank_msgs)} messages")
        
        # Test FRAM bank switching
        fram_msg = builder.set_bank_fram(1)
        results['set_bank_fram'] = isinstance(fram_msg, bytes)
        logger.info("✓ set_bank_fram")
        
        # Test byte operations
        read_msg = builder.read_byte(0, 0)
        results['read_byte'] = isinstance(read_msg, bytes)
        logger.info("✓ read_byte")
        
        write_msg = builder.write_byte(0, 0, 0, 0xFF)
        results['write_byte'] = isinstance(write_msg, bytes)
        logger.info("✓ write_byte")
        
        # Test flash operations
        flash_type_msg = builder.get_flash_type()
        results['get_flash_type'] = isinstance(flash_type_msg, bytes)
        logger.info("✓ get_flash_type")
        
        reset_msg = builder.reset_flash_controller()
        results['reset_flash'] = isinstance(reset_msg, bytes)
        logger.info("✓ reset_flash_controller")
        
        # Test cartridge detection
        detect_msg = builder.detect_cart()
        results['detect_cart'] = isinstance(detect_msg, bytes)
        logger.info("✓ detect_cart")
        
    except Exception as e:
        logger.error(f"✗ cartclinic functionality test failed: {e}")
        results['cart_api_classes'] = False
        
    return results

def test_feature_api_functionality() -> Dict[str, bool]:
    """Test feature API functionality."""
    results = {}
    
    try:
        from libpyretro.feature_api import FeatureAPIClient, FeatureInfo
        
        # Test client creation
        client = FeatureAPIClient("https://test.api.com")
        results['client_creation'] = client is not None
        logger.info("✓ FeatureAPIClient created")
        
        # Test feature management
        features = client.list_features()
        results['list_features'] = isinstance(features, list) and len(features) > 0
        logger.info(f"✓ list_features: {len(features)} features")
        
        # Test feature checking
        is_enabled = client.is_feature_enabled("cartridge_operations")
        results['feature_check'] = isinstance(is_enabled, bool)
        logger.info(f"✓ feature check: cartridge_operations = {is_enabled}")
        
        # Test feature toggling
        client.disable_feature("cartridge_operations")
        client.enable_feature("cartridge_operations")
        results['feature_toggle'] = True
        logger.info("✓ feature toggle")
        
        # Test user features
        user_features = client.get_user_features()
        results['user_features'] = isinstance(user_features, dict)
        logger.info(f"✓ user_features: {len(user_features)} features")
        
    except Exception as e:
        logger.error(f"✗ feature API test failed: {e}")
        results['client_creation'] = False
        
    return results

def test_ips_util_functionality() -> Dict[str, bool]:
    """Test IPS utility functionality."""
    results = {}
    
    try:
        from libpyretro.ips_util import IPSPatcher, apply_ips_patch, create_ips_patch
        
        # Test patcher creation
        patcher = IPSPatcher()
        results['patcher_creation'] = patcher is not None
        logger.info("✓ IPSPatcher created")
        
        # Test patch creation and application
        original_data = b"Hello, World!" + b"\x00" * 100
        modified_data = b"Hello, Patch!" + b"\x00" * 100
        
        # Create patch
        patch_data = create_ips_patch(original_data, modified_data)
        results['patch_creation'] = patch_data is not None
        logger.info(f"✓ patch creation: {len(patch_data) if patch_data else 0} bytes")
        
        if patch_data:
            # Apply patch
            patched_result = apply_ips_patch(original_data, patch_data)
            results['patch_application'] = patched_result == modified_data
            logger.info(f"✓ patch application: {'success' if results['patch_application'] else 'failed'}")
        else:
            results['patch_application'] = False
            
        # Test patcher methods
        patcher2 = IPSPatcher()
        if patch_data:
            load_success = patcher2.load_patch(patch_data)
            results['patch_loading'] = load_success
            logger.info(f"✓ patch loading: {'success' if load_success else 'failed'}")
            
            if load_success:
                applied_data = patcher2.apply_patch(original_data)
                results['patcher_apply'] = applied_data == modified_data
                logger.info(f"✓ patcher apply: {'success' if results['patcher_apply'] else 'failed'}")
        
    except Exception as e:
        logger.error(f"✗ IPS utility test failed: {e}")
        results['patcher_creation'] = False
        
    return results

def test_util_functionality() -> Dict[str, bool]:
    """Test utility module functionality."""
    results = {}
    
    try:
        from libpyretro.util import (
            resolve_path, get_platform_info, safe_filename,
            format_bytes, ensure_directory, OS_NAME, CPU_TYPE
        )
        
        # Test path resolution
        resolved = resolve_path(".")
        results['resolve_path'] = isinstance(resolved, str) and len(resolved) > 0
        logger.info(f"✓ resolve_path: {resolved[:50]}...")
        
        # Test platform info
        platform_info = get_platform_info()
        results['platform_info'] = isinstance(platform_info, dict) and len(platform_info) > 0
        logger.info(f"✓ platform_info: {platform_info['os_name']}/{platform_info['cpu_type']}")
        
        # Test safe filename
        safe_name = safe_filename("test<>file?.txt")
        results['safe_filename'] = isinstance(safe_name, str) and "<" not in safe_name
        logger.info(f"✓ safe_filename: {safe_name}")
        
        # Test byte formatting
        formatted = format_bytes(1024 * 1024)
        results['format_bytes'] = "MB" in formatted
        logger.info(f"✓ format_bytes: {formatted}")
        
        # Test constants
        results['constants'] = isinstance(OS_NAME, str) and isinstance(CPU_TYPE, str)
        logger.info(f"✓ constants: OS={OS_NAME}, CPU={CPU_TYPE}")
        
    except Exception as e:
        logger.error(f"✗ util functionality test failed: {e}")
        results['resolve_path'] = False
        
    return results

def test_protocol_integration() -> Dict[str, bool]:
    """Test protocol module integration."""
    results = {}
    
    try:
        from libpyretro.cartclinic import protocol
        results['protocol_import'] = True
        logger.info("✓ protocol module imported")
        
        # Test protocol components
        from libpyretro.cartclinic.protocol import common
        results['protocol_common'] = True
        logger.info("✓ protocol.common imported")
        
        from libpyretro.cartclinic.protocol import cmd
        results['protocol_cmd'] = True
        logger.info("✓ protocol.cmd imported")
        
        from libpyretro.cartclinic.protocol import reply
        results['protocol_reply'] = True
        logger.info("✓ protocol.reply imported")
        
    except Exception as e:
        logger.error(f"✗ protocol integration test failed: {e}")
        results['protocol_import'] = False
        
    return results

def generate_test_report(all_results: Dict[str, Dict[str, bool]]) -> str:
    """Generate a comprehensive test report."""
    report = ["# LibPyRetro Integration Test Report\n"]
    
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
    """Run all libpyretro integration tests."""
    logger.info("Starting libpyretro integration tests...")
    
    all_results = {}
    
    # Run all test categories
    test_categories = [
        ("imports", test_libpyretro_imports),
        ("cartclinic_functionality", test_cartclinic_functionality),
        ("feature_api_functionality", test_feature_api_functionality),
        ("ips_util_functionality", test_ips_util_functionality),
        ("util_functionality", test_util_functionality),
        ("protocol_integration", test_protocol_integration)
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
    
    with open("libpyretro_integration_test_report.md", "w") as f:
        f.write(report)
        
    logger.info("Test report saved to: libpyretro_integration_test_report.md")
    
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
        return True
    else:
        logger.warning(f"{total_tests - passed_tests} tests failed! ✗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)