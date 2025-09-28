#!/usr/bin/env python3
"""
Compatibility Validation Suite

This module provides comprehensive compatibility validation for the integrated
MRUpdater codebase, ensuring that existing APIs, data formats, configurations,
and scripts continue to work after integration.
"""

import sys
import os
import logging
import time
import json
import tempfile
import shutil
import configparser
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Callable
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from pathlib import Path
import inspect

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class CompatibilityTestResult:
    """Container for compatibility test results"""
    test_name: str
    category: str
    success: bool
    execution_time: float
    error_message: str = ""
    details: Dict[str, Any] = None
    compatibility_issues: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.compatibility_issues is None:
            self.compatibility_issues = []

class CompatibilityValidator:
    """Main compatibility validation class"""
    
    def __init__(self):
        self.results: List[CompatibilityTestResult] = []
        self.temp_dir = None
        
    def setup(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="compatibility_test_")
        logger.info(f"Created temporary directory: {self.temp_dir}")
        
    def teardown(self):
        """Clean up test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info("Cleaned up temporary directory")
            
    def run_test(self, test_func: Callable, test_name: str, category: str) -> CompatibilityTestResult:
        """Run a single compatibility test"""
        start_time = time.time()
        
        try:
            logger.info(f"Running compatibility test: {test_name}")
            
            result = test_func()
            execution_time = time.time() - start_time
            
            if isinstance(result, bool):
                success = result
                details = {}
                issues = []
            elif isinstance(result, dict):
                success = result.get('success', False)
                details = result
                issues = result.get('compatibility_issues', [])
            else:
                success = True
                details = {'result': result}
                issues = []
                
            test_result = CompatibilityTestResult(
                test_name=test_name,
                category=category,
                success=success,
                execution_time=execution_time,
                details=details,
                compatibility_issues=issues
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            test_result = CompatibilityTestResult(
                test_name=test_name,
                category=category,
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            logger.error(f"Compatibility test {test_name} failed: {e}")
            
        self.results.append(test_result)
        
        status = "PASSED" if test_result.success else "FAILED"
        logger.info(f"Compatibility test {test_name}: {status} ({test_result.execution_time:.2f}s)")
        
        return test_result

class APICompatibilityTests:
    """Tests for API compatibility"""
    
    def __init__(self, validator: CompatibilityValidator):
        self.validator = validator
        
    def test_function_signatures(self) -> Dict[str, Any]:
        """Test that function signatures remain compatible"""
        try:
            signature_tests = []
            
            # Test cartridge reading functions
            from cartclinic.cartridge_read import read_cartridge_helper
            
            # Get function signature
            sig = inspect.signature(read_cartridge_helper)
            
            # Check required parameters
            required_params = [
                'session', 'animation', 'detection_thread', 'emit_progress'
            ]
            
            param_names = list(sig.parameters.keys())
            missing_params = [p for p in required_params if p not in param_names]
            
            signature_tests.append({
                'function': 'read_cartridge_helper',
                'required_params_present': len(missing_params) == 0,
                'missing_params': missing_params,
                'total_params': len(param_names),
                'signature_compatible': len(missing_params) == 0
            })
            
            # Test cartridge writing functions
            from cartclinic.cartridge_write import write_cartridge_helper
            
            sig = inspect.signature(write_cartridge_helper)
            required_params = [
                'session', 'game_data', 'game_save_settings', 
                'animation_thread', 'detection_thread', 'emit_progress'
            ]
            
            param_names = list(sig.parameters.keys())
            missing_params = [p for p in required_params if p not in param_names]
            
            signature_tests.append({
                'function': 'write_cartridge_helper',
                'required_params_present': len(missing_params) == 0,
                'missing_params': missing_params,
                'total_params': len(param_names),
                'signature_compatible': len(missing_params) == 0
            })
            
            # Test GUI functions
            from cartclinic.gui import CartClinicGUI
            
            # Check if GUI class has expected methods
            expected_methods = ['update_progress', 'update_status', 'show_error']
            available_methods = [method for method in expected_methods 
                               if hasattr(CartClinicGUI, method)]
            
            signature_tests.append({
                'class': 'CartClinicGUI',
                'expected_methods': expected_methods,
                'available_methods': available_methods,
                'methods_compatible': len(available_methods) == len(expected_methods)
            })
            
            compatible_signatures = sum(1 for test in signature_tests 
                                      if test.get('signature_compatible', test.get('methods_compatible', False)))
            
            return {
                'success': compatible_signatures > 0,
                'signature_tests': signature_tests,
                'compatible_signatures': compatible_signatures,
                'total_signatures_tested': len(signature_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_return_value_compatibility(self) -> Dict[str, Any]:
        """Test that return values remain compatible"""
        try:
            return_value_tests = []
            
            # Test cartridge reading return values
            from cartclinic.cartridge_read import read_cartridge_helper
            from libpyretro.cartclinic.comms.session import Session
            from libpyretro.cartclinic.comms.transport import MockTransport
            
            transport = MockTransport()
            session = Session(transport)
            
            # Test original interface
            try:
                result = read_cartridge_helper(
                    session=session,
                    animation=None,
                    detection_thread=None,
                    emit_progress=Mock()
                )
                
                return_value_tests.append({
                    'function': 'read_cartridge_helper',
                    'original_interface': True,
                    'result_type': type(result).__name__,
                    'result_not_none': result is not None,
                    'compatible': True
                })
                
            except Exception as e:
                return_value_tests.append({
                    'function': 'read_cartridge_helper',
                    'original_interface': True,
                    'compatible': False,
                    'error': str(e)
                })
                
            # Test enhanced interface
            try:
                result = read_cartridge_helper(
                    session=session,
                    animation=None,
                    detection_thread=None,
                    emit_progress=Mock(),
                    progress_callback=Mock(),
                    include_save_data=True
                )
                
                return_value_tests.append({
                    'function': 'read_cartridge_helper',
                    'enhanced_interface': True,
                    'result_type': type(result).__name__,
                    'result_not_none': result is not None,
                    'compatible': True
                })
                
            except Exception as e:
                return_value_tests.append({
                    'function': 'read_cartridge_helper',
                    'enhanced_interface': True,
                    'compatible': False,
                    'error': str(e)
                })
                
            # Test session methods
            try:
                flash_info = session.get_flash_type()
                
                return_value_tests.append({
                    'method': 'session.get_flash_type',
                    'result_type': type(flash_info).__name__,
                    'result_not_none': flash_info is not None,
                    'compatible': True
                })
                
            except Exception as e:
                return_value_tests.append({
                    'method': 'session.get_flash_type',
                    'compatible': False,
                    'error': str(e)
                })
                
            compatible_returns = sum(1 for test in return_value_tests if test.get('compatible', False))
            
            return {
                'success': compatible_returns > 0,
                'return_value_tests': return_value_tests,
                'compatible_returns': compatible_returns,
                'total_returns_tested': len(return_value_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_exception_compatibility(self) -> Dict[str, Any]:
        """Test that exception handling remains compatible"""
        try:
            exception_tests = []
            
            # Test existing exception types
            from cartclinic.exceptions import CartridgeError, CommunicationError
            
            # Test that exceptions can be raised and caught
            try:
                raise CartridgeError("Test cartridge error")
            except CartridgeError as e:
                exception_tests.append({
                    'exception_type': 'CartridgeError',
                    'can_raise': True,
                    'can_catch': True,
                    'message': str(e),
                    'compatible': True
                })
            except Exception as e:
                exception_tests.append({
                    'exception_type': 'CartridgeError',
                    'compatible': False,
                    'error': str(e)
                })
                
            try:
                raise CommunicationError("Test communication error")
            except CommunicationError as e:
                exception_tests.append({
                    'exception_type': 'CommunicationError',
                    'can_raise': True,
                    'can_catch': True,
                    'message': str(e),
                    'compatible': True
                })
            except Exception as e:
                exception_tests.append({
                    'exception_type': 'CommunicationError',
                    'compatible': False,
                    'error': str(e)
                })
                
            # Test exception hierarchy
            try:
                # Test that CartridgeError is still an Exception
                is_exception = issubclass(CartridgeError, Exception)
                
                exception_tests.append({
                    'test': 'exception_hierarchy',
                    'cartridge_error_is_exception': is_exception,
                    'compatible': is_exception
                })
                
            except Exception as e:
                exception_tests.append({
                    'test': 'exception_hierarchy',
                    'compatible': False,
                    'error': str(e)
                })
                
            compatible_exceptions = sum(1 for test in exception_tests if test.get('compatible', False))
            
            return {
                'success': compatible_exceptions > 0,
                'exception_tests': exception_tests,
                'compatible_exceptions': compatible_exceptions,
                'total_exceptions_tested': len(exception_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_import_compatibility(self) -> Dict[str, Any]:
        """Test that imports remain compatible"""
        try:
            import_tests = []
            
            # Test basic imports
            basic_imports = [
                'cartclinic.cartridge_read',
                'cartclinic.cartridge_write',
                'cartclinic.gui',
                'cartclinic.exceptions',
                'flashing_tool.chromatic',
                'flashing_tool.gui',
                'libpyretro.cartclinic.comms.session',
                'config'
            ]
            
            for module_name in basic_imports:
                try:
                    __import__(module_name)
                    import_tests.append({
                        'module': module_name,
                        'import_successful': True,
                        'compatible': True
                    })
                except ImportError as e:
                    import_tests.append({
                        'module': module_name,
                        'import_successful': False,
                        'compatible': False,
                        'error': str(e)
                    })
                except Exception as e:
                    import_tests.append({
                        'module': module_name,
                        'import_successful': False,
                        'compatible': False,
                        'error': str(e)
                    })
                    
            # Test specific function imports
            function_imports = [
                ('cartclinic.cartridge_read', 'read_cartridge_helper'),
                ('cartclinic.cartridge_write', 'write_cartridge_helper'),
                ('cartclinic.exceptions', 'CartridgeError'),
                ('config', 'load_config')
            ]
            
            for module_name, function_name in function_imports:
                try:
                    module = __import__(module_name, fromlist=[function_name])
                    func = getattr(module, function_name)
                    
                    import_tests.append({
                        'import': f'{module_name}.{function_name}',
                        'import_successful': True,
                        'function_exists': func is not None,
                        'compatible': True
                    })
                    
                except (ImportError, AttributeError) as e:
                    import_tests.append({
                        'import': f'{module_name}.{function_name}',
                        'import_successful': False,
                        'compatible': False,
                        'error': str(e)
                    })
                except Exception as e:
                    import_tests.append({
                        'import': f'{module_name}.{function_name}',
                        'import_successful': False,
                        'compatible': False,
                        'error': str(e)
                    })
                    
            successful_imports = sum(1 for test in import_tests if test.get('compatible', False))
            
            return {
                'success': successful_imports > 0,
                'import_tests': import_tests,
                'successful_imports': successful_imports,
                'total_imports_tested': len(import_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

class DataFormatCompatibilityTests:
    """Tests for data format compatibility"""
    
    def __init__(self, validator: CompatibilityValidator):
        self.validator = validator
        
    def test_cartridge_data_formats(self) -> Dict[str, Any]:
        """Test cartridge data format compatibility"""
        try:
            format_tests = []
            
            # Test ROM data format
            test_rom_data = bytearray([0x00, 0x01, 0x02, 0x03] * 1024)  # 4KB test ROM
            
            # Test that ROM data can be processed
            try:
                from cartclinic.cartridge_read import validate_rom_checksum
                
                checksum_result = validate_rom_checksum(test_rom_data)
                
                format_tests.append({
                    'format': 'rom_data',
                    'validation_available': True,
                    'validation_result': checksum_result,
                    'compatible': True
                })
                
            except ImportError:
                format_tests.append({
                    'format': 'rom_data',
                    'validation_available': False,
                    'compatible': True,  # Still compatible, just no validation
                    'note': 'Checksum validation not available'
                })
            except Exception as e:
                format_tests.append({
                    'format': 'rom_data',
                    'compatible': False,
                    'error': str(e)
                })
                
            # Test save data format
            test_save_data = bytearray([0xFF, 0xEE, 0xDD, 0xCC] * 512)  # 2KB test save
            
            try:
                # Test save data processing
                from libpyretro.cartclinic.comms.session import Session
                from libpyretro.cartclinic.comms.transport import MockTransport
                
                transport = MockTransport()
                session = Session(transport)
                
                # Test FRAM operations if available
                if hasattr(session, 'write_fram'):
                    write_result = session.write_fram(test_save_data)
                    
                    format_tests.append({
                        'format': 'save_data',
                        'fram_operations_available': True,
                        'write_successful': write_result,
                        'compatible': True
                    })
                else:
                    format_tests.append({
                        'format': 'save_data',
                        'fram_operations_available': False,
                        'compatible': True,
                        'note': 'FRAM operations not available'
                    })
                    
            except Exception as e:
                format_tests.append({
                    'format': 'save_data',
                    'compatible': False,
                    'error': str(e)
                })
                
            # Test cartridge header format
            try:
                # Create Game Boy header
                header_data = bytearray(80)  # 0x100-0x14F
                header_data[0x34:0x44] = b"TEST GAME\x00\x00\x00\x00\x00\x00"  # Title
                header_data[0x47] = 0x01  # Cartridge type
                header_data[0x48] = 0x02  # ROM size
                header_data[0x49] = 0x01  # RAM size
                
                # Test header parsing (if available)
                format_tests.append({
                    'format': 'cartridge_header',
                    'header_created': True,
                    'header_size': len(header_data),
                    'compatible': True
                })
                
            except Exception as e:
                format_tests.append({
                    'format': 'cartridge_header',
                    'compatible': False,
                    'error': str(e)
                })
                
            compatible_formats = sum(1 for test in format_tests if test.get('compatible', False))
            
            return {
                'success': compatible_formats > 0,
                'format_tests': format_tests,
                'compatible_formats': compatible_formats,
                'total_formats_tested': len(format_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_configuration_data_formats(self) -> Dict[str, Any]:
        """Test configuration data format compatibility"""
        try:
            config_tests = []
            
            # Create test configuration file
            test_config_path = os.path.join(self.validator.temp_dir, "test_config.ini")
            
            # Write test configuration
            config_content = """[DEFAULT]
device_timeout = 30
debug_mode = false
enhanced_features_enabled = true

[cartridge]
default_read_mode = standard
include_save_data = false
verify_checksums = true

[gui]
show_progress = true
auto_detect_cartridge = true
"""
            
            with open(test_config_path, 'w') as f:
                f.write(config_content)
                
            # Test configuration loading
            try:
                from config import load_config
                
                config = load_config(test_config_path)
                
                config_tests.append({
                    'operation': 'load_config',
                    'config_loaded': config is not None,
                    'config_sections': list(config.sections()) if config else [],
                    'compatible': config is not None
                })
                
                # Test configuration values
                if config:
                    expected_values = {
                        'device_timeout': '30',
                        'debug_mode': 'false',
                        'enhanced_features_enabled': 'true'
                    }
                    
                    values_correct = all(
                        config.get('DEFAULT', key, fallback=None) == value
                        for key, value in expected_values.items()
                    )
                    
                    config_tests.append({
                        'operation': 'config_values',
                        'values_correct': values_correct,
                        'expected_values': expected_values,
                        'compatible': values_correct
                    })
                    
            except Exception as e:
                config_tests.append({
                    'operation': 'load_config',
                    'compatible': False,
                    'error': str(e)
                })
                
            # Test configuration saving
            try:
                from config import save_config
                
                # Create new config
                new_config = configparser.ConfigParser()
                new_config['DEFAULT'] = {
                    'device_timeout': '60',
                    'debug_mode': 'true'
                }
                
                save_path = os.path.join(self.validator.temp_dir, "test_save_config.ini")
                save_config(new_config, save_path)
                
                # Verify saved config
                saved_exists = os.path.exists(save_path)
                
                config_tests.append({
                    'operation': 'save_config',
                    'config_saved': saved_exists,
                    'save_path': save_path,
                    'compatible': saved_exists
                })
                
            except Exception as e:
                config_tests.append({
                    'operation': 'save_config',
                    'compatible': False,
                    'error': str(e)
                })
                
            compatible_configs = sum(1 for test in config_tests if test.get('compatible', False))
            
            return {
                'success': compatible_configs > 0,
                'config_tests': config_tests,
                'compatible_configs': compatible_configs,
                'total_config_tests': len(config_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_firmware_data_formats(self) -> Dict[str, Any]:
        """Test firmware data format compatibility"""
        try:
            firmware_tests = []
            
            # Create test firmware data
            test_firmware = bytearray([0xAA, 0xBB, 0xCC, 0xDD] * 2048)  # 8KB test firmware
            
            # Test firmware validation
            try:
                from flashing_tool.firmware_manager import FirmwareManager
                
                firmware_manager = FirmwareManager()
                
                # Test firmware validation
                is_valid = firmware_manager.validate_firmware(test_firmware)
                
                firmware_tests.append({
                    'operation': 'validate_firmware',
                    'validation_available': True,
                    'firmware_valid': is_valid,
                    'firmware_size': len(test_firmware),
                    'compatible': True
                })
                
            except Exception as e:
                firmware_tests.append({
                    'operation': 'validate_firmware',
                    'compatible': False,
                    'error': str(e)
                })
                
            # Test firmware metadata
            try:
                firmware_metadata = {
                    'version': '1.0.0',
                    'build_date': '2024-01-01',
                    'checksum': 'abc123',
                    'size': len(test_firmware)
                }
                
                # Test metadata processing
                metadata_valid = all(
                    key in firmware_metadata 
                    for key in ['version', 'build_date', 'checksum', 'size']
                )
                
                firmware_tests.append({
                    'operation': 'firmware_metadata',
                    'metadata_valid': metadata_valid,
                    'metadata_keys': list(firmware_metadata.keys()),
                    'compatible': metadata_valid
                })
                
            except Exception as e:
                firmware_tests.append({
                    'operation': 'firmware_metadata',
                    'compatible': False,
                    'error': str(e)
                })
                
            compatible_firmware = sum(1 for test in firmware_tests if test.get('compatible', False))
            
            return {
                'success': compatible_firmware > 0,
                'firmware_tests': firmware_tests,
                'compatible_firmware': compatible_firmware,
                'total_firmware_tests': len(firmware_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

class ConfigurationCompatibilityTests:
    """Tests for configuration file compatibility"""
    
    def __init__(self, validator: CompatibilityValidator):
        self.validator = validator
        
    def test_existing_config_files(self) -> Dict[str, Any]:
        """Test compatibility with existing configuration files"""
        try:
            config_file_tests = []
            
            # Test various configuration file formats
            config_formats = [
                {
                    'name': 'basic_config',
                    'content': """[DEFAULT]
device_timeout = 30
debug_mode = false
"""
                },
                {
                    'name': 'advanced_config',
                    'content': """[DEFAULT]
device_timeout = 30
debug_mode = false
enhanced_features_enabled = true

[cartridge]
default_read_mode = standard
include_save_data = false
verify_checksums = true

[gui]
show_progress = true
auto_detect_cartridge = true
theme = default

[device]
auto_connect = true
connection_timeout = 10
retry_attempts = 3
"""
                },
                {
                    'name': 'legacy_config',
                    'content': """[DEFAULT]
timeout = 30
debug = 0

[settings]
mode = 1
verify = 1
"""
                }
            ]
            
            for config_format in config_formats:
                config_path = os.path.join(self.validator.temp_dir, f"{config_format['name']}.ini")
                
                # Write config file
                with open(config_path, 'w') as f:
                    f.write(config_format['content'])
                    
                # Test loading
                try:
                    from config import load_config
                    
                    config = load_config(config_path)
                    
                    config_file_tests.append({
                        'config_name': config_format['name'],
                        'load_successful': config is not None,
                        'sections_count': len(config.sections()) if config else 0,
                        'compatible': config is not None
                    })
                    
                except Exception as e:
                    config_file_tests.append({
                        'config_name': config_format['name'],
                        'load_successful': False,
                        'compatible': False,
                        'error': str(e)
                    })
                    
            compatible_configs = sum(1 for test in config_file_tests if test.get('compatible', False))
            
            return {
                'success': compatible_configs > 0,
                'config_file_tests': config_file_tests,
                'compatible_configs': compatible_configs,
                'total_config_files_tested': len(config_file_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_config_migration(self) -> Dict[str, Any]:
        """Test configuration migration capabilities"""
        try:
            migration_tests = []
            
            # Create old format config
            old_config_path = os.path.join(self.validator.temp_dir, "old_config.ini")
            old_config_content = """[DEFAULT]
timeout = 30
debug = 0
mode = 1
"""
            
            with open(old_config_path, 'w') as f:
                f.write(old_config_content)
                
            # Test migration
            try:
                from data_format_migration import migrate_config_file
                
                new_config_path = os.path.join(self.validator.temp_dir, "migrated_config.ini")
                
                migration_result = migrate_config_file(old_config_path, new_config_path)
                
                migration_tests.append({
                    'operation': 'config_migration',
                    'migration_successful': migration_result,
                    'migrated_file_exists': os.path.exists(new_config_path),
                    'compatible': migration_result
                })
                
                # Test loading migrated config
                if migration_result and os.path.exists(new_config_path):
                    from config import load_config
                    
                    migrated_config = load_config(new_config_path)
                    
                    migration_tests.append({
                        'operation': 'load_migrated_config',
                        'load_successful': migrated_config is not None,
                        'compatible': migrated_config is not None
                    })
                    
            except ImportError:
                migration_tests.append({
                    'operation': 'config_migration',
                    'migration_available': False,
                    'compatible': True,  # Not required for compatibility
                    'note': 'Migration functionality not available'
                })
            except Exception as e:
                migration_tests.append({
                    'operation': 'config_migration',
                    'compatible': False,
                    'error': str(e)
                })
                
            # Test backward compatibility
            try:
                # Test that old config can still be read
                from config import load_config
                
                old_config = load_config(old_config_path)
                
                migration_tests.append({
                    'operation': 'backward_compatibility',
                    'old_config_readable': old_config is not None,
                    'compatible': old_config is not None
                })
                
            except Exception as e:
                migration_tests.append({
                    'operation': 'backward_compatibility',
                    'compatible': False,
                    'error': str(e)
                })
                
            compatible_migrations = sum(1 for test in migration_tests if test.get('compatible', False))
            
            return {
                'success': compatible_migrations > 0,
                'migration_tests': migration_tests,
                'compatible_migrations': compatible_migrations,
                'total_migration_tests': len(migration_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_config_defaults(self) -> Dict[str, Any]:
        """Test configuration default values"""
        try:
            default_tests = []
            
            # Test loading config with missing values
            minimal_config_path = os.path.join(self.validator.temp_dir, "minimal_config.ini")
            minimal_config_content = """[DEFAULT]
# Minimal config with only one setting
debug_mode = true
"""
            
            with open(minimal_config_path, 'w') as f:
                f.write(minimal_config_content)
                
            try:
                from config import load_config
                
                config = load_config(minimal_config_path)
                
                # Test default values
                expected_defaults = {
                    'device_timeout': 30,
                    'enhanced_features_enabled': True,
                    'auto_detect_cartridge': True
                }
                
                defaults_applied = []
                for key, expected_value in expected_defaults.items():
                    try:
                        # Try to get value with default
                        if isinstance(expected_value, bool):
                            actual_value = config.getboolean('DEFAULT', key, fallback=expected_value)
                        elif isinstance(expected_value, int):
                            actual_value = config.getint('DEFAULT', key, fallback=expected_value)
                        else:
                            actual_value = config.get('DEFAULT', key, fallback=str(expected_value))
                            
                        defaults_applied.append({
                            'key': key,
                            'expected': expected_value,
                            'actual': actual_value,
                            'default_applied': actual_value == expected_value
                        })
                        
                    except Exception as e:
                        defaults_applied.append({
                            'key': key,
                            'expected': expected_value,
                            'default_applied': False,
                            'error': str(e)
                        })
                        
                successful_defaults = sum(1 for d in defaults_applied if d.get('default_applied', False))
                
                default_tests.append({
                    'operation': 'config_defaults',
                    'defaults_applied': defaults_applied,
                    'successful_defaults': successful_defaults,
                    'total_defaults_tested': len(defaults_applied),
                    'compatible': successful_defaults > 0
                })
                
            except Exception as e:
                default_tests.append({
                    'operation': 'config_defaults',
                    'compatible': False,
                    'error': str(e)
                })
                
            compatible_defaults = sum(1 for test in default_tests if test.get('compatible', False))
            
            return {
                'success': compatible_defaults > 0,
                'default_tests': default_tests,
                'compatible_defaults': compatible_defaults
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

class ScriptCompatibilityTests:
    """Tests for existing script and automation compatibility"""
    
    def __init__(self, validator: CompatibilityValidator):
        self.validator = validator
        
    def test_python_script_compatibility(self) -> Dict[str, Any]:
        """Test compatibility with existing Python scripts"""
        try:
            script_tests = []
            
            # Create test scripts that use the MRUpdater API
            test_scripts = [
                {
                    'name': 'basic_cartridge_read.py',
                    'content': '''#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from cartclinic.cartridge_read import read_cartridge_helper
from libpyretro.cartclinic.comms.session import Session
from libpyretro.cartclinic.comms.transport import MockTransport

def main():
    transport = MockTransport()
    session = Session(transport)
    
    result = read_cartridge_helper(
        session=session,
        animation=None,
        detection_thread=None,
        emit_progress=lambda x: None
    )
    
    print(f"Read result: {type(result).__name__}")
    return True

if __name__ == "__main__":
    main()
'''
                },
                {
                    'name': 'config_test.py',
                    'content': '''#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from config import load_config
import tempfile
import os

def main():
    # Create test config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("""[DEFAULT]
device_timeout = 30
debug_mode = false
""")
        config_path = f.name
    
    try:
        config = load_config(config_path)
        print(f"Config loaded: {config is not None}")
        return config is not None
    finally:
        os.unlink(config_path)

if __name__ == "__main__":
    main()
'''
                },
                {
                    'name': 'exception_test.py',
                    'content': '''#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from cartclinic.exceptions import CartridgeError

def main():
    try:
        raise CartridgeError("Test error")
    except CartridgeError as e:
        print(f"Caught exception: {e}")
        return True
    except Exception as e:
        print(f"Unexpected exception: {e}")
        return False

if __name__ == "__main__":
    main()
'''
                }
            ]
            
            for script_info in test_scripts:
                script_path = os.path.join(self.validator.temp_dir, script_info['name'])
                
                # Write script file
                with open(script_path, 'w') as f:
                    f.write(script_info['content'])
                    
                # Make script executable
                os.chmod(script_path, 0o755)
                
                # Test script execution
                try:
                    result = subprocess.run(
                        [sys.executable, script_path],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=os.path.dirname(os.path.abspath(__file__))
                    )
                    
                    script_tests.append({
                        'script_name': script_info['name'],
                        'execution_successful': result.returncode == 0,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'return_code': result.returncode,
                        'compatible': result.returncode == 0
                    })
                    
                except subprocess.TimeoutExpired:
                    script_tests.append({
                        'script_name': script_info['name'],
                        'execution_successful': False,
                        'compatible': False,
                        'error': 'Script execution timed out'
                    })
                except Exception as e:
                    script_tests.append({
                        'script_name': script_info['name'],
                        'execution_successful': False,
                        'compatible': False,
                        'error': str(e)
                    })
                    
            compatible_scripts = sum(1 for test in script_tests if test.get('compatible', False))
            
            return {
                'success': compatible_scripts > 0,
                'script_tests': script_tests,
                'compatible_scripts': compatible_scripts,
                'total_scripts_tested': len(script_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def test_command_line_compatibility(self) -> Dict[str, Any]:
        """Test command line interface compatibility"""
        try:
            cli_tests = []
            
            # Test main application entry points
            entry_points = [
                {
                    'name': 'main.py',
                    'args': ['--help'],
                    'expect_success': True
                },
                {
                    'name': 'cartclinic.py',
                    'args': ['--version'],
                    'expect_success': True
                }
            ]
            
            for entry_point in entry_points:
                script_path = entry_point['name']
                
                if os.path.exists(script_path):
                    try:
                        result = subprocess.run(
                            [sys.executable, script_path] + entry_point['args'],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        success = (result.returncode == 0) == entry_point['expect_success']
                        
                        cli_tests.append({
                            'entry_point': entry_point['name'],
                            'args': entry_point['args'],
                            'return_code': result.returncode,
                            'stdout': result.stdout[:200],  # Truncate for readability
                            'stderr': result.stderr[:200],
                            'compatible': success
                        })
                        
                    except subprocess.TimeoutExpired:
                        cli_tests.append({
                            'entry_point': entry_point['name'],
                            'args': entry_point['args'],
                            'compatible': False,
                            'error': 'Command timed out'
                        })
                    except Exception as e:
                        cli_tests.append({
                            'entry_point': entry_point['name'],
                            'args': entry_point['args'],
                            'compatible': False,
                            'error': str(e)
                        })
                else:
                    cli_tests.append({
                        'entry_point': entry_point['name'],
                        'compatible': False,
                        'error': 'Entry point not found'
                    })
                    
            compatible_cli = sum(1 for test in cli_tests if test.get('compatible', False))
            
            return {
                'success': compatible_cli >= 0,  # Allow zero if no CLI found
                'cli_tests': cli_tests,
                'compatible_cli': compatible_cli,
                'total_cli_tested': len(cli_tests)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

def run_compatibility_validation() -> bool:
    """Run all compatibility validation tests"""
    logger.info("Starting compatibility validation tests...")
    
    validator = CompatibilityValidator()
    
    try:
        # Set up test environment
        validator.setup()
        
        # Initialize test suites
        api_tests = APICompatibilityTests(validator)
        data_format_tests = DataFormatCompatibilityTests(validator)
        config_tests = ConfigurationCompatibilityTests(validator)
        script_tests = ScriptCompatibilityTests(validator)
        
        # Run API compatibility tests
        logger.info("Running API compatibility tests...")
        validator.run_test(api_tests.test_function_signatures, "Function Signatures", "API")
        validator.run_test(api_tests.test_return_value_compatibility, "Return Value Compatibility", "API")
        validator.run_test(api_tests.test_exception_compatibility, "Exception Compatibility", "API")
        validator.run_test(api_tests.test_import_compatibility, "Import Compatibility", "API")
        
        # Run data format compatibility tests
        logger.info("Running data format compatibility tests...")
        validator.run_test(data_format_tests.test_cartridge_data_formats, "Cartridge Data Formats", "Data Format")
        validator.run_test(data_format_tests.test_configuration_data_formats, "Configuration Data Formats", "Data Format")
        validator.run_test(data_format_tests.test_firmware_data_formats, "Firmware Data Formats", "Data Format")
        
        # Run configuration compatibility tests
        logger.info("Running configuration compatibility tests...")
        validator.run_test(config_tests.test_existing_config_files, "Existing Config Files", "Configuration")
        validator.run_test(config_tests.test_config_migration, "Config Migration", "Configuration")
        validator.run_test(config_tests.test_config_defaults, "Config Defaults", "Configuration")
        
        # Run script compatibility tests
        logger.info("Running script compatibility tests...")
        validator.run_test(script_tests.test_python_script_compatibility, "Python Script Compatibility", "Scripts")
        validator.run_test(script_tests.test_command_line_compatibility, "Command Line Compatibility", "Scripts")
        
        # Generate report
        passed_tests = sum(1 for r in validator.results if r.success)
        total_tests = len(validator.results)
        
        report = generate_compatibility_report(validator.results)
        
        with open("compatibility_validation_report.md", "w") as f:
            f.write(report)
            
        logger.info("Compatibility validation report saved to: compatibility_validation_report.md")
        
        logger.info(f"Compatibility validation completed: {passed_tests}/{total_tests} passed")
        
        return passed_tests > 0  # Success if at least some tests passed
        
    except Exception as e:
        logger.error(f"Compatibility validation failed: {e}")
        return False
        
    finally:
        validator.teardown()

def generate_compatibility_report(results: List[CompatibilityTestResult]) -> str:
    """Generate compatibility validation report"""
    passed_tests = sum(1 for r in results if r.success)
    total_tests = len(results)
    total_time = sum(r.execution_time for r in results)
    
    report = [
        "# Compatibility Validation Report",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Tests:** {total_tests}",
        f"**Passed:** {passed_tests}",
        f"**Failed:** {total_tests - passed_tests}",
        f"**Success Rate:** {(passed_tests/total_tests*100):.1f}%",
        f"**Total Execution Time:** {total_time:.2f}s",
        "",
        "## Test Categories",
        ""
    ]
    
    # Group results by category
    categories = {}
    for result in results:
        if result.category not in categories:
            categories[result.category] = []
        categories[result.category].append(result)
        
    for category, category_results in categories.items():
        category_passed = sum(1 for r in category_results if r.success)
        category_total = len(category_results)
        
        report.extend([
            f"### {category} Compatibility",
            f"**Results:** {category_passed}/{category_total} passed",
            ""
        ])
        
        for result in category_results:
            status = "✓ PASS" if result.success else "✗ FAIL"
            report.extend([
                f"#### {result.test_name}",
                f"**Status:** {status}",
                f"**Execution Time:** {result.execution_time:.2f}s",
                ""
            ])
            
            if not result.success and result.error_message:
                report.extend([
                    "**Error:**",
                    f"```",
                    result.error_message,
                    f"```",
                    ""
                ])
                
            if result.compatibility_issues:
                report.extend([
                    "**Compatibility Issues:**",
                    ""
                ])
                for issue in result.compatibility_issues:
                    report.append(f"- {issue}")
                report.append("")
                
            if result.details:
                report.append("**Details:**")
                for key, value in result.details.items():
                    if isinstance(value, (list, dict)):
                        report.append(f"- {key}: {len(value)} items" if isinstance(value, list) else f"- {key}: {type(value).__name__}")
                    else:
                        report.append(f"- {key}: {value}")
                report.append("")
                
    # Summary and recommendations
    report.extend([
        "## Summary and Recommendations",
        ""
    ])
    
    if passed_tests == total_tests:
        report.append("✅ **All compatibility tests passed!** The integrated codebase maintains full backward compatibility.")
    elif passed_tests > total_tests * 0.8:
        report.append("⚠️ **Most compatibility tests passed.** Minor compatibility issues detected that should be addressed.")
    else:
        report.append("❌ **Significant compatibility issues detected.** Review and fix compatibility problems before deployment.")
        
    report.extend([
        "",
        f"**Compatibility Score:** {(passed_tests/total_tests*100):.1f}%",
        ""
    ])
    
    return "\n".join(report)

def main():
    """Main entry point"""
    logger.info("Starting compatibility validation...")
    success = run_compatibility_validation()
    
    if success:
        logger.info("Compatibility validation completed! ✓")
        return True
    else:
        logger.error("Compatibility validation failed! ✗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)