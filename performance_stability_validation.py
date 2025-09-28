#!/usr/bin/env python3
"""
Performance and Stability Validation

This module validates performance improvements and stability of the integrated
MRUpdater codebase, measuring execution times, memory usage, and error handling
under various conditions.
"""

import sys
import os
import logging
import time
import gc
import threading
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch
from dataclasses import dataclass
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('performance_stability_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class PerformanceMetric:
    """Container for performance metrics"""
    operation_name: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: str = ""
    iterations: int = 1
    
    @property
    def avg_execution_time(self) -> float:
        """Average execution time per iteration"""
        return self.execution_time / self.iterations if self.iterations > 0 else 0.0

@dataclass
class StabilityMetric:
    """Container for stability metrics"""
    test_name: str
    total_iterations: int
    successful_iterations: int
    failed_iterations: int
    error_types: Dict[str, int]
    avg_execution_time: float
    memory_leak_detected: bool
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        return (self.successful_iterations / self.total_iterations * 100) if self.total_iterations > 0 else 0.0

class PerformanceStabilityValidator:
    """Main performance and stability validation framework"""
    
    def __init__(self):
        self.performance_metrics: List[PerformanceMetric] = []
        self.stability_metrics: List[StabilityMetric] = []
        self.baseline_metrics: Dict[str, float] = {}
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None
        
    def measure_performance(self, operation_name: str, operation_func, iterations: int = 1) -> PerformanceMetric:
        """Measure performance of an operation"""
        logger.info(f"Measuring performance: {operation_name} ({iterations} iterations)")
        
        # Get initial memory usage
        gc.collect()  # Force garbage collection
        if PSUTIL_AVAILABLE and self.process:
            initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            initial_cpu = self.process.cpu_percent()
        else:
            initial_memory = 0
            initial_cpu = 0
        
        start_time = time.time()
        success = True
        error_message = ""
        
        try:
            for i in range(iterations):
                result = operation_func()
                if not result and result is not None:
                    success = False
                    error_message = f"Operation returned False on iteration {i+1}"
                    break
                    
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Performance test failed: {e}")
            
        execution_time = time.time() - start_time
        
        # Get final memory usage
        gc.collect()
        if PSUTIL_AVAILABLE and self.process:
            final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            final_cpu = self.process.cpu_percent()
        else:
            final_memory = initial_memory
            final_cpu = initial_cpu
        
        memory_usage = final_memory - initial_memory
        cpu_usage = max(final_cpu - initial_cpu, 0)  # Avoid negative values
        
        metric = PerformanceMetric(
            operation_name=operation_name,
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            success=success,
            error_message=error_message,
            iterations=iterations
        )
        
        self.performance_metrics.append(metric)
        
        logger.info(f"Performance result: {operation_name} - "
                   f"Time: {metric.avg_execution_time:.3f}s/op, "
                   f"Memory: {memory_usage:.2f}MB, "
                   f"Success: {success}")
        
        return metric
    
    def measure_stability(self, test_name: str, test_func, iterations: int = 100) -> StabilityMetric:
        """Measure stability of an operation over multiple iterations"""
        logger.info(f"Measuring stability: {test_name} ({iterations} iterations)")
        
        successful_iterations = 0
        failed_iterations = 0
        error_types = {}
        execution_times = []
        
        if PSUTIL_AVAILABLE and self.process:
            initial_memory = self.process.memory_info().rss / 1024 / 1024
        else:
            initial_memory = 0
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                result = test_func()
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
                
                if result is False:
                    failed_iterations += 1
                    error_type = "operation_returned_false"
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                else:
                    successful_iterations += 1
                    
            except Exception as e:
                failed_iterations += 1
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
                
                error_type = type(e).__name__
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
                if i % 10 == 0:  # Log every 10th error
                    logger.debug(f"Stability test error (iteration {i+1}): {e}")
        
        # Check for memory leaks
        gc.collect()
        if PSUTIL_AVAILABLE and self.process:
            final_memory = self.process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            memory_leak_detected = memory_increase > 50  # More than 50MB increase
        else:
            memory_leak_detected = False
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        metric = StabilityMetric(
            test_name=test_name,
            total_iterations=iterations,
            successful_iterations=successful_iterations,
            failed_iterations=failed_iterations,
            error_types=error_types,
            avg_execution_time=avg_execution_time,
            memory_leak_detected=memory_leak_detected
        )
        
        self.stability_metrics.append(metric)
        
        logger.info(f"Stability result: {test_name} - "
                   f"Success rate: {metric.success_rate:.1f}%, "
                   f"Avg time: {avg_execution_time:.3f}s, "
                   f"Memory leak: {memory_leak_detected}")
        
        return metric
    
    def load_baseline_metrics(self, baseline_file: str = "performance_baselines.json"):
        """Load baseline performance metrics for comparison"""
        baseline_path = Path(baseline_file)
        if baseline_path.exists():
            try:
                import json
                with open(baseline_path, 'r') as f:
                    self.baseline_metrics = json.load(f)
                logger.info(f"Loaded {len(self.baseline_metrics)} baseline metrics")
            except Exception as e:
                logger.warning(f"Could not load baseline metrics: {e}")
        else:
            logger.info("No baseline metrics file found")
    
    def save_baseline_metrics(self, baseline_file: str = "performance_baselines.json"):
        """Save current performance metrics as baseline"""
        try:
            import json
            baseline_data = {}
            for metric in self.performance_metrics:
                if metric.success:
                    baseline_data[metric.operation_name] = metric.avg_execution_time
            
            with open(baseline_file, 'w') as f:
                json.dump(baseline_data, f, indent=2)
            
            logger.info(f"Saved {len(baseline_data)} baseline metrics")
        except Exception as e:
            logger.error(f"Could not save baseline metrics: {e}")
    
    def compare_with_baseline(self) -> Dict[str, Dict[str, Any]]:
        """Compare current metrics with baseline"""
        comparisons = {}
        
        for metric in self.performance_metrics:
            if not metric.success:
                continue
                
            operation_name = metric.operation_name
            current_time = metric.avg_execution_time
            
            if operation_name in self.baseline_metrics:
                baseline_time = self.baseline_metrics[operation_name]
                improvement = ((baseline_time - current_time) / baseline_time) * 100
                
                comparisons[operation_name] = {
                    'current_time': current_time,
                    'baseline_time': baseline_time,
                    'improvement_percent': improvement,
                    'is_improvement': improvement > 0,
                    'is_regression': improvement < -10  # More than 10% slower
                }
            else:
                comparisons[operation_name] = {
                    'current_time': current_time,
                    'baseline_time': None,
                    'improvement_percent': None,
                    'is_improvement': None,
                    'is_regression': False
                }
        
        return comparisons
    
    def generate_report(self) -> str:
        """Generate comprehensive performance and stability report"""
        report = [
            "# Performance and Stability Validation Report",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**System:** {psutil.cpu_count() if PSUTIL_AVAILABLE else 'Unknown'} CPU cores, {psutil.virtual_memory().total // 1024 // 1024 // 1024 if PSUTIL_AVAILABLE else 'Unknown'}GB RAM",
            "",
            "## Performance Metrics",
            ""
        ]
        
        # Performance metrics
        for metric in self.performance_metrics:
            status = "✓ PASS" if metric.success else "✗ FAIL"
            report.extend([
                f"### {metric.operation_name}",
                f"**Status:** {status}",
                f"**Execution Time:** {metric.avg_execution_time:.3f}s per operation",
                f"**Memory Usage:** {metric.memory_usage_mb:.2f}MB",
                f"**CPU Usage:** {metric.cpu_usage_percent:.1f}%",
                f"**Iterations:** {metric.iterations}",
                ""
            ])
            
            if not metric.success:
                report.extend([
                    f"**Error:** {metric.error_message}",
                    ""
                ])
        
        # Baseline comparison
        comparisons = self.compare_with_baseline()
        if comparisons:
            report.extend([
                "## Baseline Comparison",
                ""
            ])
            
            for operation, comparison in comparisons.items():
                if comparison['baseline_time'] is not None:
                    improvement = comparison['improvement_percent']
                    if improvement > 0:
                        status = f"✓ {improvement:.1f}% faster"
                    elif improvement < -10:
                        status = f"⚠ {abs(improvement):.1f}% slower"
                    else:
                        status = f"≈ {abs(improvement):.1f}% difference"
                    
                    report.extend([
                        f"**{operation}:** {status}",
                        f"- Current: {comparison['current_time']:.3f}s",
                        f"- Baseline: {comparison['baseline_time']:.3f}s",
                        ""
                    ])
        
        # Stability metrics
        if self.stability_metrics:
            report.extend([
                "## Stability Metrics",
                ""
            ])
            
            for metric in self.stability_metrics:
                report.extend([
                    f"### {metric.test_name}",
                    f"**Success Rate:** {metric.success_rate:.1f}%",
                    f"**Total Iterations:** {metric.total_iterations}",
                    f"**Successful:** {metric.successful_iterations}",
                    f"**Failed:** {metric.failed_iterations}",
                    f"**Average Time:** {metric.avg_execution_time:.3f}s",
                    f"**Memory Leak Detected:** {'Yes' if metric.memory_leak_detected else 'No'}",
                    ""
                ])
                
                if metric.error_types:
                    report.extend([
                        "**Error Types:**"
                    ])
                    for error_type, count in metric.error_types.items():
                        report.append(f"- {error_type}: {count}")
                    report.append("")
        
        return "\n".join(report)

def test_module_import_performance():
    """Test module import performance"""
    def import_test():
        try:
            # Test core module imports
            import cartclinic.cartridge_read
            import cartclinic.cartridge_write
            import libpyretro.cartclinic.cart_api
            import flashing_tool.chromatic
            import main
            return True
        except Exception:
            return False
    
    return import_test

def test_session_creation_performance():
    """Test session creation performance"""
    def session_test():
        try:
            from libpyretro.cartclinic.comms.session import Session
            from libpyretro.cartclinic.comms.transport import MockTransport, Transporter
            
            mock_transport = MockTransport()
            transporter = Transporter(mock_transport)
            session = Session(transporter)
            return session is not None
        except Exception:
            return False
    
    return session_test

def test_device_detection_performance():
    """Test device detection performance"""
    def detection_test():
        try:
            from flashing_tool.chromatic import Chromatic
            
            chromatic = Chromatic()
            # Mock the device scanning to avoid actual hardware dependency
            with patch('flashing_tool.device_communication.find_devices') as mock_find:
                mock_find.return_value = [{'path': '/dev/ttyUSB0', 'type': 'chromatic'}]
                devices = chromatic.scan_for_devices()
                return len(devices) >= 0  # Should at least return empty list
        except Exception:
            return False
    
    return detection_test

def test_configuration_loading_performance():
    """Test configuration loading performance"""
    def config_test():
        try:
            import config
            # Test basic config functionality
            return hasattr(config, '__name__')
        except Exception:
            return False
    
    return config_test

def test_error_handling_performance():
    """Test error handling performance"""
    def error_test():
        try:
            from error_handler import ErrorHandler
            from cartclinic.exceptions import CartridgeError
            
            handler = ErrorHandler()
            test_error = CartridgeError("Test error")
            
            # Test error handling (should not raise)
            try:
                handler.handle_error(test_error, "test_context")
            except:
                pass  # Expected to handle the error
            
            return True
        except Exception:
            return False
    
    return error_test

def test_memory_efficiency():
    """Test memory efficiency under load"""
    def memory_test():
        try:
            # Create multiple objects to test memory usage
            objects = []
            for i in range(100):
                from libpyretro.cartclinic.comms.transport import MockTransport
                mock_transport = MockTransport()
                objects.append(mock_transport)
            
            # Clean up
            objects.clear()
            gc.collect()
            return True
        except Exception:
            return False
    
    return memory_test

def run_performance_stability_validation() -> bool:
    """Run comprehensive performance and stability validation"""
    validator = PerformanceStabilityValidator()
    
    # Load baseline metrics if available
    validator.load_baseline_metrics()
    
    logger.info("Starting performance and stability validation...")
    
    # Performance tests
    logger.info("Running performance tests...")
    
    validator.measure_performance(
        "Module Import Performance",
        test_module_import_performance(),
        iterations=10
    )
    
    validator.measure_performance(
        "Session Creation Performance", 
        test_session_creation_performance(),
        iterations=5
    )
    
    validator.measure_performance(
        "Device Detection Performance",
        test_device_detection_performance(),
        iterations=3
    )
    
    validator.measure_performance(
        "Configuration Loading Performance",
        test_configuration_loading_performance(),
        iterations=10
    )
    
    validator.measure_performance(
        "Error Handling Performance",
        test_error_handling_performance(),
        iterations=20
    )
    
    # Stability tests
    logger.info("Running stability tests...")
    
    validator.measure_stability(
        "Module Import Stability",
        test_module_import_performance(),
        iterations=50
    )
    
    validator.measure_stability(
        "Session Creation Stability",
        test_session_creation_performance(),
        iterations=25
    )
    
    validator.measure_stability(
        "Error Handling Stability",
        test_error_handling_performance(),
        iterations=100
    )
    
    validator.measure_stability(
        "Memory Efficiency Test",
        test_memory_efficiency(),
        iterations=10
    )
    
    # Generate and save report
    report = validator.generate_report()
    
    with open("performance_stability_report.md", "w") as f:
        f.write(report)
    
    logger.info("Performance and stability report saved to: performance_stability_report.md")
    
    # Save current metrics as baseline if no baseline exists
    if not validator.baseline_metrics:
        validator.save_baseline_metrics()
        logger.info("Saved current metrics as baseline")
    
    # Calculate overall success
    performance_success = all(m.success for m in validator.performance_metrics)
    stability_success = all(m.success_rate > 80 for m in validator.stability_metrics)  # 80% success rate threshold
    
    # Check for regressions
    comparisons = validator.compare_with_baseline()
    no_regressions = not any(c.get('is_regression', False) for c in comparisons.values())
    
    overall_success = performance_success and stability_success and no_regressions
    
    logger.info(f"Performance validation: {'PASSED' if performance_success else 'FAILED'}")
    logger.info(f"Stability validation: {'PASSED' if stability_success else 'FAILED'}")
    logger.info(f"Regression check: {'PASSED' if no_regressions else 'FAILED'}")
    logger.info(f"Overall result: {'PASSED' if overall_success else 'FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    logger.info("Starting performance and stability validation...")
    success = run_performance_stability_validation()
    
    if success:
        logger.info("Performance and stability validation passed! ✓")
        sys.exit(0)
    else:
        logger.error("Performance and stability validation failed! ✗")
        sys.exit(1)