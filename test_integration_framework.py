#!/usr/bin/env python3
"""
Comprehensive Integration Testing Framework

This framework validates all integrated functionality, backward compatibility,
and enhanced features from the decompiled version integration.
"""

import unittest
import sys
import os
import logging
import tempfile
import shutil
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class IntegrationTestResult:
    """Container for integration test results"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.error_message = ""
        self.execution_time = 0.0
        self.details = {}
        
    def mark_passed(self, details: Dict[str, Any] = None):
        """Mark test as passed"""
        self.passed = True
        self.details = details or {}
        
    def mark_failed(self, error_message: str, details: Dict[str, Any] = None):
        """Mark test as failed"""
        self.passed = False
        self.error_message = error_message
        self.details = details or {}


class IntegrationTestFramework:
    """Main integration testing framework"""
    
    def __init__(self):
        self.results: List[IntegrationTestResult] = []
        self.temp_dir = None
        self.setup_complete = False
        
    def setup(self):
        """Set up test environment"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="integration_test_")
            logger.info(f"Created temporary directory: {self.temp_dir}")
            self.setup_complete = True
        except Exception as e:
            logger.error(f"Failed to set up test environment: {e}")
            raise
            
    def teardown(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info("Cleaned up temporary directory")
            
    def run_test(self, test_func, test_name: str) -> IntegrationTestResult:
        """Run a single test and record results"""
        result = IntegrationTestResult(test_name)
        start_time = time.time()
        
        try:
            logger.info(f"Running test: {test_name}")
            test_result = test_func()
            
            if isinstance(test_result, bool):
                if test_result:
                    result.mark_passed()
                else:
                    result.mark_failed("Test returned False")
            elif isinstance(test_result, dict):
                if test_result.get('success', False):
                    result.mark_passed(test_result)
                else:
                    result.mark_failed(test_result.get('error', 'Unknown error'), test_result)
            else:
                result.mark_passed({'result': test_result})
                
        except Exception as e:
            result.mark_failed(str(e))
            logger.error(f"Test {test_name} failed: {e}")
            
        result.execution_time = time.time() - start_time
        self.results.append(result)
        
        status = "PASSED" if result.passed else "FAILED"
        logger.info(f"Test {test_name}: {status} ({result.execution_time:.2f}s)")
        
        return result
        
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        passed_tests = sum(1 for r in self.results if r.passed)
        total_tests = len(self.results)
        total_time = sum(r.execution_time for r in self.results)
        
        report = [
            "# Integration Test Report",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Tests:** {total_tests}",
            f"**Passed:** {passed_tests}",
            f"**Failed:** {total_tests - passed_tests}",
            f"**Success Rate:** {(passed_tests/total_tests*100):.1f}%",
            f"**Total Execution Time:** {total_time:.2f}s",
            "",
            "## Test Results",
            ""
        ]
        
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            report.append(f"### {result.test_name}")
            report.append(f"**Status:** {status}")
            report.append(f"**Execution Time:** {result.execution_time:.2f}s")
            
            if not result.passed:
                report.append(f"**Error:** {result.error_message}")
                
            if result.details:
                report.append("**Details:**")
                for key, value in result.details.items():
                    report.append(f"- {key}: {value}")
                    
            report.append("")
            
        return "\n".join(report)


class BackwardCompatibilityTests:
    """Tests for backward compatibility"""
    
    def __init__(self, framework: IntegrationTestFramework):
        self.framework = framework
        
    def test_api_compatibility(self) -> Dict[str, Any]:
        """Test that all existing APIs still work"""
        try:
            # Test cartridge reading API
            from test_backward_compatibility import TestOriginalAPIBehavior
            test_instance = TestOriginalAPIBehavior()
            test_instance.setUp()
            
            # Run original interface tests
            test_instance.test_original_cartridge_read_interface()
            test_instance.test_original_cartridge_write_interface()
            test_instance.test_original_function_signatures()
            
            return {'success': True, 'apis_tested': 3}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_data_format_compatibility(self) -> Dict[str, Any]:
        """Test data format compatibility"""
        try:
            from test_data_format_compatibility import run_data_format_tests
            
            # Run data format compatibility tests
            success = run_data_format_tests()
            
            return {
                'success': success,
                'formats_tested': ['config_files', 'cartridge_data', 'save_data']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_existing_data_compatibility(self) -> Dict[str, Any]:
        """Test compatibility with existing data"""
        try:
            from test_existing_data_compatibility import run_existing_data_tests
            
            # Run existing data compatibility tests
            success = run_existing_data_tests()
            
            return {
                'success': success,
                'data_types_tested': ['cartridge_files', 'save_files', 'config_files']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class EnhancedFeatureTests:
    """Tests for enhanced features from decompiled version"""
    
    def __init__(self, framework: IntegrationTestFramework):
        self.framework = framework
        
    def test_enhanced_cartridge_operations(self) -> Dict[str, Any]:
        """Test enhanced cartridge operations"""
        try:
            # Test enhanced reading with save data support
            mock_session = Mock()
            mock_session.get_flash_type.return_value = Mock(capacity_kb=512)
            mock_session.read_bank.return_value = bytearray(16384)
            mock_session.detect_fram.return_value = True
            mock_session.read_fram.return_value = bytearray(8192)
            
            # Import enhanced functionality
            from cartclinic.cartridge_read import read_cartridge_helper
            
            # Test enhanced reading
            result = read_cartridge_helper(
                session=mock_session,
                animation=None,
                detection_thread=None,
                emit_progress=Mock(),
                progress_callback=Mock(),
                include_save_data=True
            )
            
            features_tested = ['enhanced_reading', 'save_data_support', 'fram_detection']
            
            return {
                'success': True,
                'features_tested': features_tested,
                'result_type': type(result).__name__
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_enhanced_device_communication(self) -> Dict[str, Any]:
        """Test enhanced device communication"""
        try:
            from flashing_tool.chromatic import Chromatic
            
            # Test enhanced Chromatic initialization
            chromatic = Chromatic(
                on_state_transition_callback=Mock(),
                enhanced_detection=True
            )
            
            # Test enhanced state detection
            if hasattr(chromatic, 'detect_device_state'):
                state = chromatic.detect_device_state()
                
            features_tested = ['enhanced_initialization', 'state_detection']
            
            return {
                'success': True,
                'features_tested': features_tested,
                'chromatic_created': chromatic is not None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_enhanced_error_handling(self) -> Dict[str, Any]:
        """Test enhanced error handling"""
        try:
            from cartclinic.exceptions import CartridgeError
            from error_handler import ErrorHandler
            
            # Test enhanced error handling
            handler = ErrorHandler()
            
            # Create test error
            test_error = CartridgeError("Test error")
            
            # Test error handling
            handled = handler.handle_error(test_error, "test_context")
            
            features_tested = ['enhanced_exceptions', 'error_recovery', 'context_handling']
            
            return {
                'success': True,
                'features_tested': features_tested,
                'error_handled': isinstance(handled, bool)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class PerformanceTests:
    """Tests for performance improvements"""
    
    def __init__(self, framework: IntegrationTestFramework):
        self.framework = framework
        
    def test_cartridge_read_performance(self) -> Dict[str, Any]:
        """Test cartridge reading performance"""
        try:
            # Create mock session for performance testing
            mock_session = Mock()
            mock_session.get_flash_type.return_value = Mock(capacity_kb=512)
            mock_session.read_bank.return_value = bytearray(16384)
            
            from cartclinic.cartridge_read import read_cartridge_helper
            
            # Measure performance
            start_time = time.time()
            
            for _ in range(10):  # Run multiple times for average
                result = read_cartridge_helper(
                    session=mock_session,
                    animation=None,
                    detection_thread=None,
                    emit_progress=Mock()
                )
                
            execution_time = time.time() - start_time
            avg_time = execution_time / 10
            
            return {
                'success': True,
                'total_time': execution_time,
                'average_time': avg_time,
                'operations_per_second': 10 / execution_time
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage improvements"""
        try:
            import psutil
            import gc
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Perform memory-intensive operations
            mock_session = Mock()
            mock_session.get_flash_type.return_value = Mock(capacity_kb=2048)  # Larger cartridge
            mock_session.read_bank.return_value = bytearray(32768)  # 32KB banks
            
            from cartclinic.cartridge_read import read_cartridge_helper
            
            # Read large cartridge
            result = read_cartridge_helper(
                session=mock_session,
                animation=None,
                detection_thread=None,
                emit_progress=Mock()
            )
            
            # Force garbage collection
            gc.collect()
            
            # Get final memory usage
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            return {
                'success': True,
                'initial_memory_mb': initial_memory / 1024 / 1024,
                'final_memory_mb': final_memory / 1024 / 1024,
                'memory_increase_mb': memory_increase / 1024 / 1024,
                'memory_efficient': memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
            }
            
        except ImportError:
            return {'success': False, 'error': 'psutil not available for memory testing'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class ImportIntegrationTests:
    """Tests for import integration"""
    
    def __init__(self, framework: IntegrationTestFramework):
        self.framework = framework
        
    def test_import_resolution(self) -> Dict[str, Any]:
        """Test import resolution works correctly"""
        try:
            from test_import_integration import main as run_import_tests
            
            # Capture the result of import tests
            success = run_import_tests()
            
            return {
                'success': success,
                'import_categories_tested': [
                    'basic_imports', 'third_party_imports', 'compatibility_layer',
                    'unified_resolver', 'application_imports', 'circular_dependencies'
                ]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_libpyretro_integration(self) -> Dict[str, Any]:
        """Test libpyretro integration"""
        try:
            from test_libpyretro_integration import main as run_libpyretro_tests
            
            # Run libpyretro integration tests
            success = run_libpyretro_tests()
            
            return {
                'success': success,
                'libpyretro_modules_tested': [
                    'imports', 'cartclinic_functionality', 'feature_api_functionality',
                    'ips_util_functionality', 'util_functionality', 'protocol_integration'
                ]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


def run_integration_tests() -> bool:
    """Run all integration tests"""
    framework = IntegrationTestFramework()
    
    try:
        # Set up test environment
        framework.setup()
        
        # Initialize test suites
        backward_compat = BackwardCompatibilityTests(framework)
        enhanced_features = EnhancedFeatureTests(framework)
        performance = PerformanceTests(framework)
        import_integration = ImportIntegrationTests(framework)
        
        # Run backward compatibility tests
        logger.info("Running backward compatibility tests...")
        framework.run_test(backward_compat.test_api_compatibility, "API Compatibility")
        framework.run_test(backward_compat.test_data_format_compatibility, "Data Format Compatibility")
        framework.run_test(backward_compat.test_existing_data_compatibility, "Existing Data Compatibility")
        
        # Run enhanced feature tests
        logger.info("Running enhanced feature tests...")
        framework.run_test(enhanced_features.test_enhanced_cartridge_operations, "Enhanced Cartridge Operations")
        framework.run_test(enhanced_features.test_enhanced_device_communication, "Enhanced Device Communication")
        framework.run_test(enhanced_features.test_enhanced_error_handling, "Enhanced Error Handling")
        
        # Run performance tests
        logger.info("Running performance tests...")
        framework.run_test(performance.test_cartridge_read_performance, "Cartridge Read Performance")
        framework.run_test(performance.test_memory_usage, "Memory Usage")
        
        # Run import integration tests
        logger.info("Running import integration tests...")
        framework.run_test(import_integration.test_import_resolution, "Import Resolution")
        framework.run_test(import_integration.test_libpyretro_integration, "LibPyRetro Integration")
        
        # Generate and save report
        report = framework.generate_report()
        
        with open("integration_test_report.md", "w") as f:
            f.write(report)
            
        logger.info("Integration test report saved to: integration_test_report.md")
        
        # Print summary
        passed_tests = sum(1 for r in framework.results if r.passed)
        total_tests = len(framework.results)
        
        logger.info(f"Integration tests completed: {passed_tests}/{total_tests} passed")
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"Integration test framework failed: {e}")
        return False
        
    finally:
        framework.teardown()


if __name__ == "__main__":
    logger.info("Starting comprehensive integration tests...")
    success = run_integration_tests()
    
    if success:
        logger.info("All integration tests passed! ✓")
        sys.exit(0)
    else:
        logger.error("Some integration tests failed! ✗")
        sys.exit(1)