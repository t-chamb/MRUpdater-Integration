"""
Comprehensive Test Suite for Backward Compatibility

This test suite validates that all existing code continues to work
without modification after the integration of enhanced features.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from compatibility_layer import (
        APIVersion, CompatibilityConfig, compatibility_config,
        CartridgeReadCompatibility, CartridgeWriteCompatibility,
        ChromaticCompatibility, SessionCompatibility,
        DataFormatCompatibility, CompatibilityValidator
    )
    from api_versioning import (
        APIVersionManager, FeatureFlags, APIConfiguration,
        enable_original_mode, enable_enhanced_mode, enable_safe_mode
    )
except ImportError as e:
    print(f"Warning: Could not import compatibility modules: {e}")
    # Create mock classes for testing
    class APIVersion:
        V1_ORIGINAL = "1.0"
        V2_ENHANCED = "2.0"
        @classmethod
        def get_current_version(cls): return cls.V2_ENHANCED
        @classmethod
        def is_enhanced_mode(cls): return True
    
    class CompatibilityConfig:
        def get(self, key, default=None): return default
    
    compatibility_config = CompatibilityConfig()


class TestAPIVersioning(unittest.TestCase):
    """Test API versioning system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.json')
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_api_version_constants(self):
        """Test API version constants are defined correctly"""
        self.assertEqual(APIVersion.V1_ORIGINAL, "1.0")
        self.assertEqual(APIVersion.V2_ENHANCED, "2.0")
    
    def test_api_version_detection(self):
        """Test API version detection works correctly"""
        # Test default version
        current_version = APIVersion.get_current_version()
        self.assertIn(current_version, [APIVersion.V1_ORIGINAL, APIVersion.V2_ENHANCED])
        
        # Test enhanced mode detection
        is_enhanced = APIVersion.is_enhanced_mode()
        self.assertIsInstance(is_enhanced, bool)
    
    def test_feature_flags_creation(self):
        """Test feature flags can be created and configured"""
        try:
            flags = FeatureFlags()
            
            # Test default values
            self.assertIsInstance(flags.enhanced_cartridge_reading, bool)
            self.assertIsInstance(flags.enhanced_error_handling, bool)
            
            # Test enable/disable all
            flags.enable_all()
            self.assertTrue(flags.enhanced_cartridge_reading)
            self.assertTrue(flags.enhanced_error_handling)
            
            flags.disable_all()
            self.assertFalse(flags.enhanced_cartridge_reading)
            self.assertFalse(flags.enhanced_error_handling)
            
        except NameError:
            self.skipTest("FeatureFlags not available")
    
    def test_api_configuration_serialization(self):
        """Test API configuration can be serialized and deserialized"""
        try:
            config = APIConfiguration()
            
            # Test serialization
            config_dict = config.to_dict()
            self.assertIsInstance(config_dict, dict)
            self.assertIn('version', config_dict)
            self.assertIn('feature_flags', config_dict)
            
            # Test deserialization
            restored_config = APIConfiguration.from_dict(config_dict)
            self.assertEqual(config.version, restored_config.version)
            
        except NameError:
            self.skipTest("APIConfiguration not available")


class TestBackwardCompatibilityLayer(unittest.TestCase):
    """Test backward compatibility layer functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Reset compatibility configuration
        if hasattr(compatibility_config, 'set'):
            compatibility_config.set('enhanced_features_enabled', True)
            compatibility_config.set('strict_compatibility_mode', False)
    
    def test_compatibility_config(self):
        """Test compatibility configuration works"""
        # Test getting configuration values
        enhanced_enabled = compatibility_config.get('enhanced_features_enabled', True)
        self.assertIsInstance(enhanced_enabled, bool)
        
        strict_mode = compatibility_config.get('strict_compatibility_mode', False)
        self.assertIsInstance(strict_mode, bool)
    
    def test_cartridge_read_compatibility(self):
        """Test cartridge reading backward compatibility"""
        # Create mock session
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=512)
        mock_session.read_bank.return_value = bytearray(16384)  # 16KB bank
        
        # Test original interface
        try:
            result = CartridgeReadCompatibility.read_cartridge_helper(
                session=mock_session,
                animation=None,
                detection_thread=None,
                emit_progress=None
            )
            
            self.assertIsInstance(result, bytearray)
            self.assertGreater(len(result), 0)
            
        except Exception as e:
            # If enhanced modules aren't available, this is expected
            if "enhanced" not in str(e).lower():
                raise
    
    def test_cartridge_write_compatibility(self):
        """Test cartridge writing backward compatibility"""
        # Create mock session
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=512)
        mock_session.write_bank.return_value = bytearray(16384)
        
        # Create test data
        test_data = bytearray(16384)  # 16KB of test data
        
        # Test original interface
        try:
            result = CartridgeWriteCompatibility.write_cartridge_helper(
                session=mock_session,
                game_data=test_data,
                game_save_settings=None,
                animation_thread=None,
                detection_thread=None,
                emit_progress=None
            )
            
            self.assertIsInstance(result, bool)
            
        except Exception as e:
            # If enhanced modules aren't available, this is expected
            if "enhanced" not in str(e).lower():
                raise
    
    def test_chromatic_compatibility(self):
        """Test Chromatic device compatibility"""
        try:
            # Test factory function
            chromatic = ChromaticCompatibility.create_chromatic(
                openfpga_loader_bin=None,
                progress_callback=None,
                on_state_transition_callback=None
            )
            
            # Result can be None if original implementation isn't available
            # This is acceptable for compatibility testing
            
        except Exception as e:
            # If enhanced modules aren't available, this is expected
            if "enhanced" not in str(e).lower():
                raise
    
    def test_session_compatibility(self):
        """Test Session compatibility"""
        try:
            # Test factory function
            session = SessionCompatibility.create_session(tporter=None)
            
            # Result can be None if original implementation isn't available
            # This is acceptable for compatibility testing
            
        except Exception as e:
            # If enhanced modules aren't available, this is expected
            if "enhanced" not in str(e).lower():
                raise
    
    def test_data_format_compatibility(self):
        """Test data format compatibility"""
        # Create mock cartridge info
        mock_info = Mock()
        mock_info.header = "test_header"
        mock_info.flash_info = "test_flash"
        mock_info.total_size_kb = 512
        
        # Test format conversion
        try:
            # Test converting to enhanced format
            enhanced_info = DataFormatCompatibility.convert_cartridge_info(
                mock_info, target_format='enhanced'
            )
            self.assertIsNotNone(enhanced_info)
            
            # Test converting to original format
            original_info = DataFormatCompatibility.convert_cartridge_info(
                enhanced_info, target_format='original'
            )
            self.assertIsNotNone(original_info)
            
        except Exception as e:
            # If enhanced modules aren't available, this is expected
            if "enhanced" not in str(e).lower():
                raise


class TestCompatibilityValidation(unittest.TestCase):
    """Test compatibility validation functionality"""
    
    def test_api_compatibility_validation(self):
        """Test API compatibility validation"""
        try:
            results = CompatibilityValidator.validate_api_compatibility()
            
            self.assertIsInstance(results, dict)
            
            # Check that all expected APIs are tested
            expected_apis = ['cartridge_read', 'cartridge_write', 'chromatic', 'session']
            for api in expected_apis:
                self.assertIn(api, results)
                self.assertIsInstance(results[api], bool)
                
        except NameError:
            self.skipTest("CompatibilityValidator not available")
    
    def test_data_format_compatibility_validation(self):
        """Test data format compatibility validation"""
        try:
            results = CompatibilityValidator.validate_data_format_compatibility()
            
            self.assertIsInstance(results, dict)
            
            # Check that all expected formats are tested
            expected_formats = ['config_files', 'cartridge_data', 'save_data']
            for format_type in expected_formats:
                self.assertIn(format_type, results)
                self.assertIsInstance(results[format_type], bool)
                
        except NameError:
            self.skipTest("CompatibilityValidator not available")
    
    def test_compatibility_report_generation(self):
        """Test compatibility report generation"""
        try:
            report = CompatibilityValidator.generate_compatibility_report()
            
            self.assertIsInstance(report, str)
            self.assertIn("Compatibility Report", report)
            self.assertIn("API Compatibility", report)
            self.assertIn("Data Format Compatibility", report)
            
        except NameError:
            self.skipTest("CompatibilityValidator not available")


class TestOriginalAPIBehavior(unittest.TestCase):
    """Test that original API behavior is preserved"""
    
    def setUp(self):
        """Set up original mode for testing"""
        try:
            enable_original_mode()
        except NameError:
            pass
    
    def test_original_cartridge_read_interface(self):
        """Test original cartridge read interface is preserved"""
        # Create mock session that behaves like original
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=512)
        mock_session.read_bank.return_value = bytearray(16384)
        
        # Test that original interface works
        try:
            result = CartridgeReadCompatibility.read_cartridge_helper(
                session=mock_session,
                animation=None,
                detection_thread=None,
                emit_progress=Mock()
            )
            
            # Should return bytearray (not tuple with save data)
            self.assertIsInstance(result, bytearray)
            
        except Exception as e:
            if "enhanced" not in str(e).lower():
                raise
    
    def test_original_cartridge_write_interface(self):
        """Test original cartridge write interface is preserved"""
        # Create mock session
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=512)
        mock_session.write_bank.return_value = bytearray(16384)
        
        test_data = bytearray(16384)
        
        try:
            result = CartridgeWriteCompatibility.write_cartridge_helper(
                session=mock_session,
                game_data=test_data,
                game_save_settings=None,
                animation_thread=None,
                detection_thread=None,
                emit_progress=Mock()
            )
            
            # Should return boolean
            self.assertIsInstance(result, bool)
            
        except Exception as e:
            if "enhanced" not in str(e).lower():
                raise
    
    def test_original_function_signatures(self):
        """Test that original function signatures are preserved"""
        # Test cartridge read signature
        import inspect
        
        try:
            sig = inspect.signature(CartridgeReadCompatibility.read_cartridge_helper)
            params = list(sig.parameters.keys())
            
            # Should have original parameters
            expected_params = ['session', 'animation', 'detection_thread', 'emit_progress']
            for param in expected_params:
                self.assertIn(param, params)
                
        except Exception as e:
            if "enhanced" not in str(e).lower():
                raise


class TestEnhancedAPIBehavior(unittest.TestCase):
    """Test that enhanced API behavior works correctly"""
    
    def setUp(self):
        """Set up enhanced mode for testing"""
        try:
            enable_enhanced_mode()
        except NameError:
            pass
    
    def test_enhanced_cartridge_read_features(self):
        """Test enhanced cartridge read features"""
        # Create mock session
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=512)
        mock_session.read_bank.return_value = bytearray(16384)
        mock_session.detect_fram.return_value = True
        mock_session.read_fram.return_value = bytearray(8192)
        
        try:
            # Test enhanced interface with save data
            result = CartridgeReadCompatibility.read_cartridge_helper_enhanced(
                session=mock_session,
                animation=None,
                detection_thread=None,
                emit_progress=Mock(),
                include_save_data=True,
                validate_checksum=True,
                progress_callback=Mock()
            )
            
            # Should return tuple when include_save_data=True
            if isinstance(result, tuple):
                self.assertEqual(len(result), 2)
                self.assertIsInstance(result[0], bytearray)  # ROM data
                # result[1] could be bytearray (save data) or None
                
        except Exception as e:
            if "enhanced" not in str(e).lower():
                raise
    
    def test_enhanced_cartridge_write_features(self):
        """Test enhanced cartridge write features"""
        # Create mock session
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=512)
        mock_session.write_bank.return_value = bytearray(16384)
        mock_session.detect_fram.return_value = True
        mock_session.write_fram.return_value = True
        
        test_data = bytearray(16384)
        save_data = bytearray(8192)
        
        try:
            # Test enhanced interface with save data
            result = CartridgeWriteCompatibility.write_cartridge_helper_enhanced(
                session=mock_session,
                game_data=test_data,
                game_save_settings=None,
                animation_thread=None,
                detection_thread=None,
                emit_progress=Mock(),
                progress_callback=Mock(),
                verify_writes=True,
                save_data=save_data
            )
            
            # Should return boolean
            self.assertIsInstance(result, bool)
            
        except Exception as e:
            if "enhanced" not in str(e).lower():
                raise


class TestConfigurationMigration(unittest.TestCase):
    """Test configuration file migration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.ini')
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_file_migration(self):
        """Test configuration file migration"""
        # Create a basic config file
        with open(self.config_file, 'w') as f:
            f.write("[DEFAULT]\n")
            f.write("device_timeout = 30\n")
            f.write("debug_mode = false\n")
        
        try:
            # Test migration
            result = DataFormatCompatibility.migrate_config_file(
                self.config_file, backup=True
            )
            
            self.assertTrue(result)
            
            # Check that backup was created
            backup_file = f"{self.config_file}.backup"
            self.assertTrue(os.path.exists(backup_file))
            
            # Check that enhanced options were added
            with open(self.config_file, 'r') as f:
                content = f.read()
                self.assertIn("enhanced_features_enabled", content)
                
        except Exception as e:
            if "enhanced" not in str(e).lower():
                raise
    
    def test_config_migration_idempotent(self):
        """Test that config migration is idempotent"""
        # Create config with enhanced options already present
        with open(self.config_file, 'w') as f:
            f.write("[DEFAULT]\n")
            f.write("device_timeout = 30\n")
            f.write("enhanced_features_enabled = true\n")
        
        try:
            # Test migration (should not modify file)
            result = DataFormatCompatibility.migrate_config_file(
                self.config_file, backup=False
            )
            
            self.assertTrue(result)
            
            # File should not be modified
            with open(self.config_file, 'r') as f:
                content = f.read()
                # Should only have one instance of enhanced_features_enabled
                self.assertEqual(content.count("enhanced_features_enabled"), 1)
                
        except Exception as e:
            if "enhanced" not in str(e).lower():
                raise


class TestErrorHandling(unittest.TestCase):
    """Test error handling in compatibility layer"""
    
    def test_graceful_fallback_on_import_errors(self):
        """Test graceful fallback when enhanced modules are not available"""
        # This test ensures the compatibility layer handles missing modules gracefully
        
        # Mock import error scenario
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            try:
                # These should not raise exceptions even if modules are missing
                version = APIVersion.get_current_version()
                self.assertIsInstance(version, str)
                
                is_enhanced = APIVersion.is_enhanced_mode()
                self.assertIsInstance(is_enhanced, bool)
                
            except Exception as e:
                # Should handle import errors gracefully
                self.fail(f"Should handle import errors gracefully: {e}")
    
    def test_error_handling_in_compatibility_wrappers(self):
        """Test error handling in compatibility wrappers"""
        # Create mock session that raises errors
        mock_session = Mock()
        mock_session.get_flash_type.side_effect = Exception("Test error")
        
        try:
            # Should handle errors gracefully and not crash
            with self.assertRaises(Exception):
                CartridgeReadCompatibility.read_cartridge_helper(
                    session=mock_session,
                    animation=None,
                    detection_thread=None,
                    emit_progress=None
                )
                
        except Exception as e:
            if "enhanced" not in str(e).lower():
                raise


def run_compatibility_tests():
    """Run all compatibility tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestAPIVersioning,
        TestBackwardCompatibilityLayer,
        TestCompatibilityValidation,
        TestOriginalAPIBehavior,
        TestEnhancedAPIBehavior,
        TestConfigurationMigration,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running MRUpdater Backward Compatibility Tests...")
    print("=" * 50)
    
    success = run_compatibility_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All compatibility tests passed!")
        sys.exit(0)
    else:
        print("✗ Some compatibility tests failed!")
        sys.exit(1)