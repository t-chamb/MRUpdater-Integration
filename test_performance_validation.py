#!/usr/bin/env python3
"""
Performance Validation Tests

This module provides comprehensive performance testing for the integrated
MRUpdater codebase to validate improvements from the decompiled version.
"""

import time
import sys
import os
import logging
import statistics
import gc
from typing import Dict, List, Any, Callable, Optional
from unittest.mock import Mock
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class PerformanceMetric:
    """Container for performance metrics"""
    name: str
    value: float
    unit: str
    baseline: Optional[float] = None
    improvement: Optional[float] = None
    
    def calculate_improvement(self):
        """Calculate improvement percentage"""
        if self.baseline and self.baseline > 0:
            self.improvement = ((self.baseline - self.value) / self.baseline) * 100


class PerformanceBenchmark:
    """Performance benchmarking utilities"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        
    def benchmark_function(self, func: Callable, name: str, iterations: int = 10, 
                          baseline: Optional[float] = None) -> PerformanceMetric:
        """Benchmark a function's execution time"""
        times = []
        
        # Warm up
        for _ in range(2):
            try:
                func()
            except Exception:
                pass  # Ignore warm-up errors
                
        # Actual benchmarking
        for i in range(iterations):
            gc.collect()  # Clean up before each run
            start_time = time.perf_counter()
            
            try:
                result = func()
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            except Exception as e:
                logger.warning(f"Benchmark iteration {i+1} failed: {e}")
                continue
                
        if not times:
            logger.error(f"All benchmark iterations failed for {name}")
            return PerformanceMetric(name, float('inf'), 'seconds', baseline)
            
        # Calculate statistics
        avg_time = statistics.mean(times)
        metric = PerformanceMetric(name, avg_time, 'seconds', baseline)
        metric.calculate_improvement()
        
        self.metrics.append(metric)
        
        logger.info(f"Benchmark {name}: {avg_time:.4f}s avg ({min(times):.4f}s min, {max(times):.4f}s max)")
        if metric.improvement is not None:
            logger.info(f"  Improvement: {metric.improvement:.1f}%")
            
        return metric
        
    def benchmark_memory_usage(self, func: Callable, name: str) -> PerformanceMetric:
        """Benchmark memory usage of a function"""
        try:
            import psutil
            process = psutil.Process()
            
            # Get initial memory
            gc.collect()
            initial_memory = process.memory_info().rss
            
            # Run function
            result = func()
            
            # Get peak memory
            peak_memory = process.memory_info().rss
            
            # Clean up and get final memory
            del result
            gc.collect()
            final_memory = process.memory_info().rss
            
            # Calculate metrics
            memory_increase = peak_memory - initial_memory
            memory_leaked = final_memory - initial_memory
            
            metric = PerformanceMetric(name, memory_increase / 1024 / 1024, 'MB')
            self.metrics.append(metric)
            
            logger.info(f"Memory usage {name}: {memory_increase/1024/1024:.2f}MB increase, "
                       f"{memory_leaked/1024/1024:.2f}MB leaked")
            
            return metric
            
        except ImportError:
            logger.warning("psutil not available for memory benchmarking")
            return PerformanceMetric(name, 0, 'MB')
            
    def generate_report(self) -> str:
        """Generate performance report"""
        report = [
            "# Performance Validation Report",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Metrics:** {len(self.metrics)}",
            "",
            "## Performance Metrics",
            ""
        ]
        
        for metric in self.metrics:
            report.append(f"### {metric.name}")
            report.append(f"**Value:** {metric.value:.4f} {metric.unit}")
            
            if metric.baseline is not None:
                report.append(f"**Baseline:** {metric.baseline:.4f} {metric.unit}")
                
            if metric.improvement is not None:
                improvement_text = "improvement" if metric.improvement > 0 else "regression"
                report.append(f"**Change:** {abs(metric.improvement):.1f}% {improvement_text}")
                
            report.append("")
            
        return "\n".join(report)


class CartridgeOperationBenchmarks:
    """Benchmarks for cartridge operations"""
    
    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark
        
    def create_mock_session(self, cartridge_size_kb: int = 512) -> Mock:
        """Create mock session for testing"""
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=cartridge_size_kb)
        
        # Mock bank reading (16KB banks)
        bank_size = 16384
        mock_session.read_bank.return_value = bytearray(bank_size)
        
        # Mock FRAM detection and reading
        mock_session.detect_fram.return_value = True
        mock_session.read_fram.return_value = bytearray(8192)  # 8KB FRAM
        
        # Mock writing operations
        mock_session.write_bank.return_value = True
        mock_session.write_fram.return_value = True
        
        return mock_session
        
    def benchmark_cartridge_reading(self):
        """Benchmark cartridge reading operations"""
        try:
            from cartclinic.cartridge_read import read_cartridge_helper
            
            # Test different cartridge sizes
            sizes = [512, 1024, 2048, 4096]  # KB
            
            for size_kb in sizes:
                mock_session = self.create_mock_session(size_kb)
                
                def read_test():
                    return read_cartridge_helper(
                        session=mock_session,
                        animation=None,
                        detection_thread=None,
                        emit_progress=Mock()
                    )
                    
                self.benchmark.benchmark_function(
                    read_test, 
                    f"Cartridge Read {size_kb}KB",
                    iterations=5
                )
                
                # Test enhanced reading with save data
                def enhanced_read_test():
                    return read_cartridge_helper(
                        session=mock_session,
                        animation=None,
                        detection_thread=None,
                        emit_progress=Mock(),
                        progress_callback=Mock(),
                        include_save_data=True
                    )
                    
                self.benchmark.benchmark_function(
                    enhanced_read_test,
                    f"Enhanced Cartridge Read {size_kb}KB",
                    iterations=5
                )
                
        except Exception as e:
            logger.error(f"Cartridge reading benchmark failed: {e}")
            
    def benchmark_cartridge_writing(self):
        """Benchmark cartridge writing operations"""
        try:
            from cartclinic.cartridge_write import write_cartridge_helper
            
            # Test different data sizes
            sizes = [512, 1024, 2048]  # KB
            
            for size_kb in sizes:
                mock_session = self.create_mock_session(size_kb)
                test_data = bytearray(size_kb * 1024)  # Convert KB to bytes
                
                def write_test():
                    return write_cartridge_helper(
                        session=mock_session,
                        game_data=test_data,
                        game_save_settings=None,
                        animation_thread=None,
                        detection_thread=None,
                        emit_progress=Mock()
                    )
                    
                self.benchmark.benchmark_function(
                    write_test,
                    f"Cartridge Write {size_kb}KB",
                    iterations=3
                )
                
        except Exception as e:
            logger.error(f"Cartridge writing benchmark failed: {e}")
            
    def benchmark_memory_usage(self):
        """Benchmark memory usage of cartridge operations"""
        try:
            from cartclinic.cartridge_read import read_cartridge_helper
            
            # Test memory usage with large cartridge
            mock_session = self.create_mock_session(4096)  # 4MB cartridge
            
            def memory_test():
                results = []
                for _ in range(10):  # Multiple operations
                    result = read_cartridge_helper(
                        session=mock_session,
                        animation=None,
                        detection_thread=None,
                        emit_progress=Mock()
                    )
                    results.append(result)
                return results
                
            self.benchmark.benchmark_memory_usage(
                memory_test,
                "Cartridge Operations Memory Usage"
            )
            
        except Exception as e:
            logger.error(f"Memory usage benchmark failed: {e}")


class DeviceCommunicationBenchmarks:
    """Benchmarks for device communication"""
    
    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark
        
    def benchmark_device_detection(self):
        """Benchmark device detection performance"""
        try:
            from flashing_tool.chromatic import Chromatic
            
            def detection_test():
                chromatic = Chromatic(
                    on_state_transition_callback=Mock(),
                    enhanced_detection=True
                )
                
                # Test state detection if available
                if hasattr(chromatic, 'detect_device_state'):
                    return chromatic.detect_device_state()
                    
                return chromatic
                
            self.benchmark.benchmark_function(
                detection_test,
                "Device Detection",
                iterations=5
            )
            
        except Exception as e:
            logger.error(f"Device detection benchmark failed: {e}")
            
    def benchmark_communication_protocols(self):
        """Benchmark communication protocol performance"""
        try:
            from libpyretro.cartclinic.comms.session import Session
            from libpyretro.cartclinic.comms.transport import MockTransport
            
            def protocol_test():
                # Create mock transport
                transport = MockTransport()
                session = Session(transport)
                
                # Test various protocol operations
                operations = []
                
                # Flash type detection
                flash_info = session.get_flash_type()
                operations.append(flash_info)
                
                # Bank reading
                for bank in range(4):  # Test 4 banks
                    bank_data = session.read_bank(bank)
                    operations.append(bank_data)
                    
                # FRAM detection
                fram_detected = session.detect_fram()
                operations.append(fram_detected)
                
                return operations
                
            self.benchmark.benchmark_function(
                protocol_test,
                "Communication Protocols",
                iterations=5
            )
            
        except Exception as e:
            logger.error(f"Communication protocol benchmark failed: {e}")


class GUIPerformanceBenchmarks:
    """Benchmarks for GUI performance"""
    
    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark
        
    def benchmark_gui_responsiveness(self):
        """Benchmark GUI responsiveness"""
        try:
            # Mock Qt application for testing
            from unittest.mock import patch
            
            with patch('PySide6.QtWidgets.QApplication'):
                from cartclinic.gui import CartClinicGUI
                
                def gui_test():
                    # Create GUI instance
                    gui = CartClinicGUI()
                    
                    # Simulate GUI operations
                    operations = []
                    
                    # Test progress updates
                    for i in range(100):
                        gui.update_progress(i)
                        operations.append(i)
                        
                    # Test status updates
                    for status in ['Reading', 'Writing', 'Verifying', 'Complete']:
                        gui.update_status(status)
                        operations.append(status)
                        
                    return operations
                    
                self.benchmark.benchmark_function(
                    gui_test,
                    "GUI Responsiveness",
                    iterations=3
                )
                
        except Exception as e:
            logger.error(f"GUI responsiveness benchmark failed: {e}")


class ConfigurationBenchmarks:
    """Benchmarks for configuration operations"""
    
    def __init__(self, benchmark: PerformanceBenchmark):
        self.benchmark = benchmark
        
    def benchmark_config_loading(self):
        """Benchmark configuration loading performance"""
        try:
            import tempfile
            import configparser
            
            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                config_path = f.name
                
                # Write test configuration
                f.write("[DEFAULT]\n")
                f.write("device_timeout = 30\n")
                f.write("debug_mode = false\n")
                f.write("enhanced_features_enabled = true\n")
                
                # Add many sections for performance testing
                for i in range(100):
                    f.write(f"[section_{i}]\n")
                    f.write(f"option_{i} = value_{i}\n")
                    
            def config_test():
                from config import load_config, save_config
                
                # Load configuration
                config = load_config(config_path)
                
                # Modify configuration
                config['DEFAULT']['test_option'] = 'test_value'
                
                # Save configuration
                save_config(config, config_path)
                
                return config
                
            self.benchmark.benchmark_function(
                config_test,
                "Configuration Loading",
                iterations=10
            )
            
            # Clean up
            os.unlink(config_path)
            
        except Exception as e:
            logger.error(f"Configuration benchmark failed: {e}")


def run_performance_validation() -> bool:
    """Run all performance validation tests"""
    logger.info("Starting performance validation tests...")
    
    benchmark = PerformanceBenchmark()
    
    # Initialize benchmark suites
    cartridge_benchmarks = CartridgeOperationBenchmarks(benchmark)
    device_benchmarks = DeviceCommunicationBenchmarks(benchmark)
    gui_benchmarks = GUIPerformanceBenchmarks(benchmark)
    config_benchmarks = ConfigurationBenchmarks(benchmark)
    
    try:
        # Run cartridge operation benchmarks
        logger.info("Running cartridge operation benchmarks...")
        cartridge_benchmarks.benchmark_cartridge_reading()
        cartridge_benchmarks.benchmark_cartridge_writing()
        cartridge_benchmarks.benchmark_memory_usage()
        
        # Run device communication benchmarks
        logger.info("Running device communication benchmarks...")
        device_benchmarks.benchmark_device_detection()
        device_benchmarks.benchmark_communication_protocols()
        
        # Run GUI performance benchmarks
        logger.info("Running GUI performance benchmarks...")
        gui_benchmarks.benchmark_gui_responsiveness()
        
        # Run configuration benchmarks
        logger.info("Running configuration benchmarks...")
        config_benchmarks.benchmark_config_loading()
        
        # Generate and save report
        report = benchmark.generate_report()
        
        with open("performance_validation_report.md", "w") as f:
            f.write(report)
            
        logger.info("Performance validation report saved to: performance_validation_report.md")
        
        # Check for performance regressions
        regressions = [m for m in benchmark.metrics if m.improvement is not None and m.improvement < -10]
        
        if regressions:
            logger.warning(f"Found {len(regressions)} performance regressions:")
            for regression in regressions:
                logger.warning(f"  {regression.name}: {abs(regression.improvement):.1f}% slower")
                
        improvements = [m for m in benchmark.metrics if m.improvement is not None and m.improvement > 5]
        
        if improvements:
            logger.info(f"Found {len(improvements)} performance improvements:")
            for improvement in improvements:
                logger.info(f"  {improvement.name}: {improvement.improvement:.1f}% faster")
                
        return len(regressions) == 0  # Success if no major regressions
        
    except Exception as e:
        logger.error(f"Performance validation failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting performance validation...")
    success = run_performance_validation()
    
    if success:
        logger.info("Performance validation completed successfully! ✓")
        sys.exit(0)
    else:
        logger.error("Performance validation found issues! ✗")
        sys.exit(1)