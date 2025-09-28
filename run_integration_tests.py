#!/usr/bin/env python3
"""
Integration Test Runner

This script orchestrates all integration tests for the MRUpdater codebase
integration project, providing comprehensive validation of the integrated system.
"""

import sys
import os
import logging
import time
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('integration_tests.log')
    ]
)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSuite:
    """Represents a test suite with metadata"""
    
    def __init__(self, name: str, module_name: str, description: str, 
                 required: bool = True, timeout: int = 300):
        self.name = name
        self.module_name = module_name
        self.description = description
        self.required = required
        self.timeout = timeout
        self.result = None
        self.execution_time = 0.0
        self.error_message = ""


class IntegrationTestRunner:
    """Main test runner for integration tests"""
    
    def __init__(self):
        self.test_suites: List[TestSuite] = []
        self.results: Dict[str, Any] = {}
        self.start_time = None
        self.end_time = None
        
        # Define test suites
        self._define_test_suites()
        
    def _define_test_suites(self):
        """Define all test suites to run"""
        self.test_suites = [
            TestSuite(
                "Backward Compatibility",
                "test_backward_compatibility",
                "Validates that existing APIs and functionality continue to work",
                required=True,
                timeout=180
            ),
            TestSuite(
                "Data Format Compatibility", 
                "test_data_format_compatibility",
                "Validates compatibility with existing data formats",
                required=True,
                timeout=120
            ),
            TestSuite(
                "Existing Data Compatibility",
                "test_existing_data_compatibility", 
                "Validates compatibility with existing user data",
                required=True,
                timeout=120
            ),
            TestSuite(
                "Import Integration",
                "test_import_integration",
                "Validates that all imports work correctly after integration",
                required=True,
                timeout=180
            ),
            TestSuite(
                "LibPyRetro Integration",
                "test_libpyretro_integration",
                "Validates libpyretro module integration and functionality",
                required=True,
                timeout=240
            ),
            TestSuite(
                "Integration Framework",
                "test_integration_framework",
                "Comprehensive integration testing framework",
                required=True,
                timeout=300
            ),
            TestSuite(
                "Hardware Compatibility",
                "test_hardware_compatibility",
                "Validates device communication and hardware operations",
                required=True,
                timeout=400
            ),
            TestSuite(
                "Compatibility Validation",
                "test_compatibility_validation",
                "Comprehensive compatibility validation for APIs, data formats, and scripts",
                required=True,
                timeout=300
            ),
            TestSuite(
                "Performance Validation",
                "test_performance_validation",
                "Validates performance improvements and identifies regressions",
                required=False,
                timeout=600
            )
        ]
        
    def run_test_suite(self, suite: TestSuite) -> bool:
        """Run a single test suite"""
        logger.info(f"Running test suite: {suite.name}")
        logger.info(f"Description: {suite.description}")
        
        start_time = time.time()
        
        try:
            # Import the test module
            test_module = __import__(suite.module_name)
            
            # Look for main function or run function
            if hasattr(test_module, 'main'):
                result = test_module.main()
            elif hasattr(test_module, f'run_{suite.module_name.replace("test_", "")}'):
                func_name = f'run_{suite.module_name.replace("test_", "")}'
                result = getattr(test_module, func_name)()
            elif hasattr(test_module, 'run_tests'):
                result = test_module.run_tests()
            else:
                # Try to find and run test functions
                test_functions = [
                    attr for attr in dir(test_module) 
                    if attr.startswith('test_') and callable(getattr(test_module, attr))
                ]
                
                if test_functions:
                    results = []
                    for func_name in test_functions:
                        func = getattr(test_module, func_name)
                        try:
                            func_result = func()
                            results.append(func_result)
                        except Exception as e:
                            logger.error(f"Test function {func_name} failed: {e}")
                            results.append(False)
                            
                    result = all(results)
                else:
                    logger.warning(f"No test functions found in {suite.module_name}")
                    result = False
                    
            suite.result = result
            suite.execution_time = time.time() - start_time
            
            if result:
                logger.info(f"✓ {suite.name} PASSED ({suite.execution_time:.2f}s)")
            else:
                logger.error(f"✗ {suite.name} FAILED ({suite.execution_time:.2f}s)")
                
            return result
            
        except ImportError as e:
            suite.result = False
            suite.execution_time = time.time() - start_time
            suite.error_message = f"Import error: {e}"
            logger.error(f"✗ {suite.name} FAILED - Import error: {e}")
            return False
            
        except Exception as e:
            suite.result = False
            suite.execution_time = time.time() - start_time
            suite.error_message = str(e)
            logger.error(f"✗ {suite.name} FAILED - {e}")
            return False
            
    def run_all_tests(self) -> bool:
        """Run all test suites"""
        logger.info("Starting comprehensive integration test run")
        logger.info("=" * 60)
        
        self.start_time = time.time()
        
        passed_required = 0
        total_required = 0
        passed_optional = 0
        total_optional = 0
        
        for suite in self.test_suites:
            success = self.run_test_suite(suite)
            
            if suite.required:
                total_required += 1
                if success:
                    passed_required += 1
            else:
                total_optional += 1
                if success:
                    passed_optional += 1
                    
            logger.info("-" * 40)
            
        self.end_time = time.time()
        
        # Generate summary
        total_time = self.end_time - self.start_time
        
        logger.info("=" * 60)
        logger.info("INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total execution time: {total_time:.2f}s")
        logger.info(f"Required tests: {passed_required}/{total_required} passed")
        logger.info(f"Optional tests: {passed_optional}/{total_optional} passed")
        
        # Detailed results
        for suite in self.test_suites:
            status = "PASSED" if suite.result else "FAILED"
            required_text = "REQUIRED" if suite.required else "OPTIONAL"
            logger.info(f"  {suite.name}: {status} ({required_text}, {suite.execution_time:.2f}s)")
            
            if not suite.result and suite.error_message:
                logger.info(f"    Error: {suite.error_message}")
                
        # Overall result
        all_required_passed = passed_required == total_required
        
        if all_required_passed:
            logger.info("✓ ALL REQUIRED TESTS PASSED")
            if passed_optional < total_optional:
                logger.warning(f"⚠ {total_optional - passed_optional} optional tests failed")
        else:
            logger.error(f"✗ {total_required - passed_required} REQUIRED TESTS FAILED")
            
        return all_required_passed
        
    def generate_detailed_report(self) -> str:
        """Generate detailed test report"""
        if not self.start_time or not self.end_time:
            return "No test results available"
            
        total_time = self.end_time - self.start_time
        
        report = [
            "# Integration Test Report",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Execution Time:** {total_time:.2f}s",
            "",
            "## Summary",
            ""
        ]
        
        # Summary statistics
        required_suites = [s for s in self.test_suites if s.required]
        optional_suites = [s for s in self.test_suites if not s.required]
        
        passed_required = sum(1 for s in required_suites if s.result)
        passed_optional = sum(1 for s in optional_suites if s.result)
        
        report.extend([
            f"- **Required Tests:** {passed_required}/{len(required_suites)} passed",
            f"- **Optional Tests:** {passed_optional}/{len(optional_suites)} passed",
            f"- **Overall Success:** {'✓ PASS' if passed_required == len(required_suites) else '✗ FAIL'}",
            "",
            "## Test Suite Results",
            ""
        ])
        
        # Detailed results for each suite
        for suite in self.test_suites:
            status = "✓ PASS" if suite.result else "✗ FAIL"
            required_text = "Required" if suite.required else "Optional"
            
            report.extend([
                f"### {suite.name}",
                f"**Status:** {status}",
                f"**Type:** {required_text}",
                f"**Execution Time:** {suite.execution_time:.2f}s",
                f"**Description:** {suite.description}",
                ""
            ])
            
            if not suite.result and suite.error_message:
                report.extend([
                    "**Error Details:**",
                    f"```",
                    suite.error_message,
                    f"```",
                    ""
                ])
                
        # Performance summary if available
        if os.path.exists("performance_validation_report.md"):
            report.extend([
                "## Performance Validation",
                "",
                "See `performance_validation_report.md` for detailed performance metrics.",
                ""
            ])
            
        # Integration test framework results if available
        if os.path.exists("integration_test_report.md"):
            report.extend([
                "## Integration Framework Results",
                "",
                "See `integration_test_report.md` for detailed integration test results.",
                ""
            ])
            
        return "\n".join(report)
        
    def save_results(self):
        """Save test results to files"""
        # Save detailed report
        report = self.generate_detailed_report()
        with open("comprehensive_integration_report.md", "w") as f:
            f.write(report)
            
        # Save JSON results for programmatic access
        results_data = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "total_execution_time": self.end_time - self.start_time if self.start_time and self.end_time else 0,
            "test_suites": []
        }
        
        for suite in self.test_suites:
            suite_data = {
                "name": suite.name,
                "module_name": suite.module_name,
                "description": suite.description,
                "required": suite.required,
                "result": suite.result,
                "execution_time": suite.execution_time,
                "error_message": suite.error_message
            }
            results_data["test_suites"].append(suite_data)
            
        with open("integration_test_results.json", "w") as f:
            json.dump(results_data, f, indent=2)
            
        logger.info("Test results saved to:")
        logger.info("  - comprehensive_integration_report.md")
        logger.info("  - integration_test_results.json")


def main():
    """Main entry point"""
    logger.info("MRUpdater Integration Test Runner")
    logger.info("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 7):
        logger.error("Python 3.7 or higher is required")
        sys.exit(1)
        
    # Create test runner
    runner = IntegrationTestRunner()
    
    try:
        # Run all tests
        success = runner.run_all_tests()
        
        # Save results
        runner.save_results()
        
        # Exit with appropriate code
        if success:
            logger.info("Integration tests completed successfully! ✓")
            sys.exit(0)
        else:
            logger.error("Integration tests failed! ✗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Test run interrupted by user")
        runner.save_results()
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()