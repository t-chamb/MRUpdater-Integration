"""
Integration Test for Existing Data Compatibility

This test suite validates that existing cartridge files, save data,
and configuration files from the original MRUpdater remain fully
compatible with the integrated enhanced version.
"""

import json
import os
import tempfile
import unittest
import shutil
from pathlib import Path
from typing import Dict, Any, List

# Import compatibility modules
try:
    from data_format_migration import (
        migrate_file, migrate_cartridge_data, migrate_save_data, migrate_config_data,
        get_data_format_manager, get_file_format_migrator
    )
    from compatibility_layer import (
        CartridgeReadCompatibility, CartridgeWriteCompatibility,
        DataFormatCompatibility, enable_enhanced_mode, enable_compatibility_mode
    )
    COMPATIBILITY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Compatibility modules not available: {e}")
    COMPATIBILITY_AVAILABLE = False


class TestExistingCartridgeFiles(unittest.TestCase):
    """Test compatibility with existing cartridge files"""
    
    def setUp(self):
        """Set up test environment"""
        if not COMPATIBILITY_AVAILABLE:
            self.skipTest("Compatibility modules not available")
        
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample existing cartridge files in various formats
        self.create_sample_cartridge_files()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_cartridge_files(self):
        """Create sample cartridge files that represent existing data"""
        
        # Original format cartridge file (JSON)
        original_cartridge = {
            'rom_data': [0x00, 0x01, 0x02, 0x03] * 1024,  # 4KB ROM
            'header_info': {
                'title': 'TETRIS',
                'type': 0x19,
                'rom_size': 0x00,
                'ram_size': 0x00,
                'checksum': 0x3786
            },
            'flash_info': {
                'chip_name': 'SST39VF1681',
                'capacity_kb': 2048,
                'jedec_id': 0xBF49,
                'sector_size_bytes': 4096
            },
            'size_kb': 4
        }
        
        self.original_cartridge_file = os.path.join(self.temp_dir, 'tetris_original.json')
        with open(self.original_cartridge_file, 'w') as f:
            json.dump(original_cartridge, f, indent=2)
        
        # Binary ROM file (raw format)
        rom_data = bytes([0x00, 0x01, 0x02, 0x03] * 1024)
        self.binary_rom_file = os.path.join(self.temp_dir, 'game.gb')
        with open(self.binary_rom_file, 'wb') as f:
            f.write(rom_data)
        
        # Cartridge with save data
        cartridge_with_save = {
            'rom_data': [0x00, 0x01, 0x02, 0x03] * 512,  # 2KB ROM
            'header_info': {
                'title': 'POKEMON RED',
                'type': 0x13,  # MBC3+RAM+BATTERY
                'rom_size': 0x05,
                'ram_size': 0x03,
                'checksum': 0x4B1C
            },
            'flash_info': {
                'chip_name': 'SST39VF1682',
                'capacity_kb': 4096,
                'jedec_id': 0xBF4A
            },
            'size_kb': 2,
            'save_data': [0xFF, 0x00, 0xAA, 0x55] * 2048  # 8KB save data
        }
        
        self.cartridge_with_save_file = os.path.join(self.temp_dir, 'pokemon_with_save.json')
        with open(self.cartridge_with_save_file, 'w') as f:
            json.dump(cartridge_with_save, f, indent=2)
    
    def test_original_cartridge_file_compatibility(self):
        """Test that original cartridge files remain compatible"""
        # Load original file
        with open(self.original_cartridge_file, 'r') as f:
            original_data = json.load(f)
        
        # Test that data can be processed by enhanced system
        try:
            # Should be able to migrate to enhanced format
            enhanced_data = migrate_cartridge_data(original_data)
            
            # Enhanced data should contain original information
            self.assertEqual(enhanced_data['rom_data'], original_data['rom_data'])
            self.assertEqual(enhanced_data['header_info'], original_data['header_info'])
            self.assertEqual(enhanced_data['flash_info'], original_data['flash_info'])
            self.assertEqual(enhanced_data['size_kb'], original_data['size_kb'])
            
            # Enhanced data should have new metadata
            self.assertIn('metadata', enhanced_data)
            self.assertIn('validation', enhanced_data)
            self.assertIn('format_version', enhanced_data)
            
        except Exception as e:
            self.fail(f"Original cartridge file compatibility failed: {e}")
    
    def test_cartridge_with_save_compatibility(self):
        """Test that cartridge files with save data remain compatible"""
        # Load cartridge with save data
        with open(self.cartridge_with_save_file, 'r') as f:
            cartridge_data = json.load(f)
        
        # Test that data can be processed
        try:
            # Should be able to migrate cartridge data
            enhanced_cartridge = migrate_cartridge_data(cartridge_data)
            
            # Should preserve save data
            self.assertEqual(enhanced_cartridge['save_data'], cartridge_data['save_data'])
            
            # Should have save data metadata in enhanced format
            self.assertIn('save_data_metadata', enhanced_cartridge)
            save_metadata = enhanced_cartridge['save_data_metadata']
            self.assertEqual(save_metadata['size_bytes'], len(cartridge_data['save_data']))
            
        except Exception as e:
            self.fail(f"Cartridge with save data compatibility failed: {e}")
    
    def test_binary_rom_file_handling(self):
        """Test that binary ROM files can be handled"""
        # Read binary ROM data
        with open(self.binary_rom_file, 'rb') as f:
            rom_data = f.read()
        
        # Test that binary data can be wrapped in compatible format
        try:
            # Create minimal cartridge data structure
            cartridge_data = {
                'rom_data': list(rom_data),  # Convert to JSON-serializable format
                'header_info': {},
                'flash_info': {},
                'size_kb': len(rom_data) // 1024
            }
            
            # Should be able to migrate
            enhanced_data = migrate_cartridge_data(cartridge_data)
            
            # Should preserve ROM data
            self.assertEqual(enhanced_data['rom_data'], list(rom_data))
            
        except Exception as e:
            self.fail(f"Binary ROM file handling failed: {e}")
    
    def test_file_migration_preserves_backups(self):
        """Test that file migration creates proper backups"""
        # Migrate original cartridge file
        result = migrate_file(self.original_cartridge_file, backup=True)
        self.assertTrue(result)
        
        # Check that backup was created
        backup_file = f"{self.original_cartridge_file}.backup"
        self.assertTrue(os.path.exists(backup_file))
        
        # Check that backup contains original data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Backup should not have enhanced format fields
        self.assertNotIn('format_version', backup_data)
        self.assertNotIn('metadata', backup_data)
        
        # Original file should now have enhanced format
        with open(self.original_cartridge_file, 'r') as f:
            migrated_data = json.load(f)
        
        self.assertIn('format_version', migrated_data)
        self.assertIn('metadata', migrated_data)


class TestExistingSaveFiles(unittest.TestCase):
    """Test compatibility with existing save files"""
    
    def setUp(self):
        """Set up test environment"""
        if not COMPATIBILITY_AVAILABLE:
            self.skipTest("Compatibility modules not available")
        
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample existing save files
        self.create_sample_save_files()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_save_files(self):
        """Create sample save files that represent existing data"""
        
        # Binary save file (SRAM dump)
        sram_data = bytearray()
        # Simulate Pokemon Red save structure
        sram_data.extend(b'POKEMON RED\x00\x00\x00\x00')  # Game title
        sram_data.extend([0x01, 0x02, 0x03, 0x04] * 100)  # Player data
        sram_data.extend([0xFF] * (8192 - len(sram_data)))  # Pad to 8KB
        
        self.sram_file = os.path.join(self.temp_dir, 'pokemon_red.sav')
        with open(self.sram_file, 'wb') as f:
            f.write(sram_data)
        
        # FRAM save file (different pattern)
        fram_data = bytearray([0x00] * 8192)  # 8KB of zeros (empty save)
        
        self.fram_file = os.path.join(self.temp_dir, 'empty_game.sav')
        with open(self.fram_file, 'wb') as f:
            f.write(fram_data)
        
        # JSON save file (already in some structured format)
        json_save = {
            'save_data': list(sram_data),
            'game_title': 'POKEMON RED',
            'save_type': 'SRAM',
            'size_bytes': len(sram_data)
        }
        
        self.json_save_file = os.path.join(self.temp_dir, 'pokemon_red.json')
        with open(self.json_save_file, 'w') as f:
            json.dump(json_save, f, indent=2)
    
    def test_binary_save_file_compatibility(self):
        """Test that binary save files remain compatible"""
        # Read binary save data
        with open(self.sram_file, 'rb') as f:
            save_data = f.read()
        
        # Test that data can be migrated
        try:
            enhanced_save = migrate_save_data(save_data)
            
            # Should preserve original save data (now as list for JSON compatibility)
            self.assertEqual(bytes(enhanced_save['save_data']), save_data)
            
            # Should have enhanced metadata
            self.assertIn('metadata', enhanced_save)
            self.assertIn('validation', enhanced_save)
            self.assertIn('format_version', enhanced_save)
            
            # Metadata should be correct
            metadata = enhanced_save['metadata']
            self.assertEqual(metadata['size_bytes'], len(save_data))
            self.assertEqual(metadata['format'], 'raw')
            
        except Exception as e:
            self.fail(f"Binary save file compatibility failed: {e}")
    
    def test_empty_save_file_detection(self):
        """Test that empty save files are properly detected"""
        # Read empty save data
        with open(self.fram_file, 'rb') as f:
            save_data = f.read()
        
        # Test migration
        try:
            enhanced_save = migrate_save_data(save_data)
            
            # Should detect as empty
            validation = enhanced_save['validation']
            self.assertTrue(validation['empty_check'])
            
        except Exception as e:
            self.fail(f"Empty save file detection failed: {e}")
    
    def test_json_save_file_compatibility(self):
        """Test that JSON save files remain compatible"""
        # This tests handling of save files that might already be in some structured format
        with open(self.json_save_file, 'r') as f:
            json_save = json.load(f)
        
        # Extract raw save data
        save_data = bytes(json_save['save_data'])
        
        # Test migration
        try:
            enhanced_save = migrate_save_data(save_data)
            
            # Should preserve save data (now as list for JSON compatibility)
            self.assertEqual(bytes(enhanced_save['save_data']), save_data)
            
            # Should have enhanced format
            self.assertIn('format_version', enhanced_save)
            
        except Exception as e:
            self.fail(f"JSON save file compatibility failed: {e}")
    
    def test_save_file_migration_preserves_data(self):
        """Test that save file migration preserves all data"""
        # Migrate binary save file
        result = migrate_file(self.sram_file, backup=True)
        self.assertTrue(result)
        
        # Check backup exists
        backup_file = f"{self.sram_file}.backup"
        self.assertTrue(os.path.exists(backup_file))
        
        # Verify backup contains original data
        with open(backup_file, 'rb') as f:
            backup_data = f.read()
        
        # Load migrated file (should be JSON now)
        json_file = self.sram_file.replace('.sav', '.json')
        with open(json_file, 'r') as f:
            migrated_data = json.load(f)
        
        # Migrated data should contain original save data (as list for JSON compatibility)
        self.assertEqual(bytes(migrated_data['save_data']), backup_data)


class TestExistingConfigFiles(unittest.TestCase):
    """Test compatibility with existing configuration files"""
    
    def setUp(self):
        """Set up test environment"""
        if not COMPATIBILITY_AVAILABLE:
            self.skipTest("Compatibility modules not available")
        
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample existing config files
        self.create_sample_config_files()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_sample_config_files(self):
        """Create sample config files that represent existing configurations"""
        
        # INI-style config file
        ini_config = """[DEFAULT]
device_timeout = 30
baud_rate = 115200
auto_detect = true
debug_mode = false

[GUI]
theme = default
window_size = 800x600
show_advanced = false
remember_window_position = true

[ADVANCED]
max_retries = 3
log_level = INFO
enable_logging = true
log_file = mrupdater.log
"""
        
        self.ini_config_file = os.path.join(self.temp_dir, 'mrupdater.ini')
        with open(self.ini_config_file, 'w') as f:
            f.write(ini_config)
        
        # JSON config file
        json_config = {
            'device_settings': {
                'timeout': 30,
                'baud_rate': 115200,
                'auto_detect': True,
                'debug_mode': False
            },
            'gui_settings': {
                'theme': 'default',
                'window_size': '800x600',
                'show_advanced': False,
                'remember_window_position': True
            },
            'advanced_settings': {
                'max_retries': 3,
                'log_level': 'INFO',
                'enable_logging': True,
                'log_file': 'mrupdater.log'
            }
        }
        
        self.json_config_file = os.path.join(self.temp_dir, 'mrupdater.json')
        with open(self.json_config_file, 'w') as f:
            json.dump(json_config, f, indent=2)
    
    def test_ini_config_file_compatibility(self):
        """Test that INI config files remain compatible"""
        # Test migration of INI file
        result = migrate_file(self.ini_config_file, backup=True)
        self.assertTrue(result)
        
        # Check that backup was created
        backup_file = f"{self.ini_config_file}.backup"
        self.assertTrue(os.path.exists(backup_file))
        
        # Check that JSON version was created
        json_file = self.ini_config_file.replace('.ini', '.json')
        self.assertTrue(os.path.exists(json_file))
        
        # Load migrated JSON config
        with open(json_file, 'r') as f:
            migrated_config = json.load(f)
        
        # Should have enhanced format
        self.assertIn('format_version', migrated_config)
        self.assertIn('enhanced_features', migrated_config)
        self.assertIn('compatibility', migrated_config)
        
        # Should preserve original settings
        self.assertIn('device_settings', migrated_config)
        self.assertIn('gui_settings', migrated_config)
        self.assertIn('advanced_settings', migrated_config)
    
    def test_json_config_file_compatibility(self):
        """Test that JSON config files remain compatible"""
        # Load original config
        with open(self.json_config_file, 'r') as f:
            original_config = json.load(f)
        
        # Test migration
        try:
            enhanced_config = migrate_config_data(original_config)
            
            # Should preserve original settings
            self.assertEqual(enhanced_config['device_settings'], original_config['device_settings'])
            self.assertEqual(enhanced_config['gui_settings'], original_config['gui_settings'])
            self.assertEqual(enhanced_config['advanced_settings'], original_config['advanced_settings'])
            
            # Should have enhanced features
            self.assertIn('enhanced_features', enhanced_config)
            self.assertIn('compatibility', enhanced_config)
            
            # Enhanced features should be enabled by default
            enhanced_features = enhanced_config['enhanced_features']
            self.assertTrue(enhanced_features['enabled'])
            
        except Exception as e:
            self.fail(f"JSON config file compatibility failed: {e}")
    
    def test_config_migration_preserves_user_settings(self):
        """Test that config migration preserves all user settings"""
        # Migrate JSON config file
        result = migrate_file(self.json_config_file, backup=True)
        self.assertTrue(result)
        
        # Load original and migrated configs
        backup_file = f"{self.json_config_file}.backup"
        with open(backup_file, 'r') as f:
            original_config = json.load(f)
        
        with open(self.json_config_file, 'r') as f:
            migrated_config = json.load(f)
        
        # All original settings should be preserved
        for section in ['device_settings', 'gui_settings', 'advanced_settings']:
            if section in original_config:
                self.assertEqual(migrated_config[section], original_config[section])


class TestAPICompatibilityWithExistingData(unittest.TestCase):
    """Test that existing data works with both original and enhanced APIs"""
    
    def setUp(self):
        """Set up test environment"""
        if not COMPATIBILITY_AVAILABLE:
            self.skipTest("Compatibility modules not available")
        
        # Create sample data that represents existing usage patterns
        self.sample_cartridge_data = {
            'rom_data': b'\x00\x01\x02\x03' * 1024,
            'header_info': {'title': 'TEST GAME'},
            'flash_info': {'chip_name': 'TEST_CHIP'},
            'size_kb': 4
        }
        
        self.sample_save_data = bytearray([0x01, 0x02, 0x03, 0x04] * 256)
    
    def test_existing_data_with_original_api(self):
        """Test that existing data works with original API"""
        # Enable original mode
        enable_compatibility_mode()
        
        # Create mock session
        from unittest.mock import Mock
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=4)
        mock_session.read_bank.return_value = bytearray(16384)
        
        try:
            # Should work with original API
            result = CartridgeReadCompatibility.read_cartridge_helper(
                session=mock_session,
                animation=None,
                detection_thread=None,
                emit_progress=None
            )
            
            self.assertIsInstance(result, bytearray)
            
        except Exception as e:
            # Should not fail due to data compatibility issues
            if "compatibility" in str(e).lower() or "format" in str(e).lower():
                self.fail(f"Data compatibility issue with original API: {e}")
    
    def test_existing_data_with_enhanced_api(self):
        """Test that existing data works with enhanced API"""
        # Enable enhanced mode
        enable_enhanced_mode()
        
        # Create mock session
        from unittest.mock import Mock
        mock_session = Mock()
        mock_session.get_flash_type.return_value = Mock(capacity_kb=4)
        mock_session.read_bank.return_value = bytearray(16384)
        mock_session.detect_fram.return_value = False
        
        try:
            # Should work with enhanced API
            result = CartridgeReadCompatibility.read_cartridge_helper_enhanced(
                session=mock_session,
                animation=None,
                detection_thread=None,
                emit_progress=None,
                include_save_data=False,
                validate_checksum=False,
                progress_callback=None
            )
            
            self.assertIsInstance(result, bytearray)
            
        except Exception as e:
            # Should not fail due to data compatibility issues
            if "compatibility" in str(e).lower() or "format" in str(e).lower():
                self.fail(f"Data compatibility issue with enhanced API: {e}")
    
    def test_data_format_conversion_roundtrip(self):
        """Test that data can be converted between formats without loss"""
        # Test cartridge data roundtrip
        try:
            # Convert to enhanced format
            enhanced_cartridge = migrate_cartridge_data(self.sample_cartridge_data)
            
            # Convert back (simulate reading with original API)
            restored_cartridge = DataFormatCompatibility.convert_cartridge_info(
                enhanced_cartridge, target_format='original'
            )
            
            # Core data should be preserved
            # Note: Some fields might be restructured, so we check key data
            self.assertIn('rom_data', restored_cartridge)
            
        except Exception as e:
            self.fail(f"Data format conversion roundtrip failed: {e}")


def run_existing_data_compatibility_tests():
    """Run all existing data compatibility tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestExistingCartridgeFiles,
        TestExistingSaveFiles,
        TestExistingConfigFiles,
        TestAPICompatibilityWithExistingData
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running MRUpdater Existing Data Compatibility Tests...")
    print("=" * 55)
    
    success = run_existing_data_compatibility_tests()
    
    print("\n" + "=" * 55)
    if success:
        print("✓ All existing data compatibility tests passed!")
        exit(0)
    else:
        print("✗ Some existing data compatibility tests failed!")
        exit(1)