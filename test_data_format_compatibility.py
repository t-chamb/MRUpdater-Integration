"""
Comprehensive Test Suite for Data Format Compatibility

This test suite validates that all existing data formats remain compatible
and that migration utilities work correctly for cartridge files, save data,
and configuration files.
"""

import json
import os
import tempfile
import unittest
import shutil
from pathlib import Path
from typing import Dict, Any

# Import data format migration modules
try:
    from data_format_migration import (
        DataFormatVersion, DataFormatVersions,
        CartridgeDataMigrator, SaveDataMigrator, ConfigurationMigrator,
        DataFormatManager, FileFormatMigrator,
        migrate_cartridge_data, migrate_save_data, migrate_config_data, migrate_file
    )
    MIGRATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Data migration modules not available: {e}")
    MIGRATION_AVAILABLE = False


class TestDataFormatVersions(unittest.TestCase):
    """Test data format version management"""
    
    def setUp(self):
        """Set up test environment"""
        if not MIGRATION_AVAILABLE:
            self.skipTest("Data migration modules not available")
    
    def test_version_creation(self):
        """Test data format version creation"""
        version = DataFormatVersion(1, 2, 3, "test_format", "Test format")
        
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 3)
        self.assertEqual(version.format_name, "test_format")
        self.assertEqual(version.version_string, "1.2.3")
    
    def test_version_compatibility(self):
        """Test version compatibility checking"""
        v1_0_0 = DataFormatVersion(1, 0, 0, "test", "Test v1.0.0")
        v1_1_0 = DataFormatVersion(1, 1, 0, "test", "Test v1.1.0")
        v2_0_0 = DataFormatVersion(2, 0, 0, "test", "Test v2.0.0")
        
        # Same major version should be compatible
        self.assertTrue(v1_0_0.is_compatible_with(v1_1_0))
        self.assertTrue(v1_1_0.is_compatible_with(v1_0_0))
        
        # Different major version should not be compatible
        self.assertFalse(v1_0_0.is_compatible_with(v2_0_0))
        self.assertFalse(v2_0_0.is_compatible_with(v1_0_0))
    
    def test_predefined_versions(self):
        """Test predefined data format versions"""
        # Test cartridge data versions
        self.assertEqual(DataFormatVersions.CARTRIDGE_DATA_V1.major, 1)
        self.assertEqual(DataFormatVersions.CARTRIDGE_DATA_V2.major, 2)
        self.assertEqual(DataFormatVersions.CARTRIDGE_DATA_V1.format_name, "cartridge_data")
        
        # Test save data versions
        self.assertEqual(DataFormatVersions.SAVE_DATA_V1.major, 1)
        self.assertEqual(DataFormatVersions.SAVE_DATA_V2.major, 2)
        self.assertEqual(DataFormatVersions.SAVE_DATA_V1.format_name, "save_data")
        
        # Test config versions
        self.assertEqual(DataFormatVersions.CONFIG_V1.major, 1)
        self.assertEqual(DataFormatVersions.CONFIG_V2.major, 2)
        self.assertEqual(DataFormatVersions.CONFIG_V1.format_name, "config")


class TestCartridgeDataMigration(unittest.TestCase):
    """Test cartridge data format migration"""
    
    def setUp(self):
        """Set up test environment"""
        if not MIGRATION_AVAILABLE:
            self.skipTest("Data migration modules not available")
        
        self.migrator = CartridgeDataMigrator()
        
        # Sample v1 cartridge data
        self.v1_data = {
            'rom_data': b'\x00\x01\x02\x03' * 1000,  # 4KB of test data
            'header_info': {
                'title': 'TEST GAME',
                'type': 0x00,
                'rom_size': 0x00,
                'ram_size': 0x00
            },
            'flash_info': {
                'chip_name': 'TEST_CHIP',
                'capacity_kb': 512,
                'jedec_id': 0x1234
            },
            'size_kb': 4,
            'save_data': b'\xFF' * 256  # 256 bytes of save data
        }
    
    def test_can_migrate_cartridge_data(self):
        """Test cartridge data migration capability detection"""
        v1 = DataFormatVersions.CARTRIDGE_DATA_V1
        v2 = DataFormatVersions.CARTRIDGE_DATA_V2
        config_v1 = DataFormatVersions.CONFIG_V1
        
        # Should be able to migrate cartridge data
        self.assertTrue(self.migrator.can_migrate(v1, v2))
        self.assertTrue(self.migrator.can_migrate(v2, v1))
        
        # Should not be able to migrate different format types
        self.assertFalse(self.migrator.can_migrate(v1, config_v1))
    
    def test_validate_v1_format(self):
        """Test v1 cartridge data format validation"""
        v1 = DataFormatVersions.CARTRIDGE_DATA_V1
        
        # Valid v1 data
        self.assertTrue(self.migrator.validate_data(self.v1_data, v1))
        
        # Invalid v1 data (missing required field)
        invalid_data = {'header_info': {}}
        self.assertFalse(self.migrator.validate_data(invalid_data, v1))
        
        # Invalid data type
        self.assertFalse(self.migrator.validate_data("not a dict", v1))
    
    def test_migrate_v1_to_v2(self):
        """Test migration from v1 to v2 cartridge data format"""
        v1 = DataFormatVersions.CARTRIDGE_DATA_V1
        v2 = DataFormatVersions.CARTRIDGE_DATA_V2
        
        # Migrate data
        v2_data = self.migrator.migrate(self.v1_data, v1, v2)
        
        # Validate v2 format
        self.assertTrue(self.migrator.validate_data(v2_data, v2))
        
        # Check that original data is preserved
        self.assertEqual(v2_data['rom_data'], self.v1_data['rom_data'])
        self.assertEqual(v2_data['header_info'], self.v1_data['header_info'])
        self.assertEqual(v2_data['flash_info'], self.v1_data['flash_info'])
        self.assertEqual(v2_data['size_kb'], self.v1_data['size_kb'])
        self.assertEqual(v2_data['save_data'], self.v1_data['save_data'])
        
        # Check that v2 enhancements are present
        self.assertIn('format_version', v2_data)
        self.assertIn('metadata', v2_data)
        self.assertIn('validation', v2_data)
        self.assertIn('migration_timestamp', v2_data)
        
        # Check metadata structure
        metadata = v2_data['metadata']
        self.assertIn('enhanced_features_used', metadata)
        self.assertIn('migration_source', metadata)
        self.assertEqual(metadata['migration_source'], 'v1_original')
    
    def test_migrate_v2_to_v1(self):
        """Test migration from v2 to v1 cartridge data format"""
        v1 = DataFormatVersions.CARTRIDGE_DATA_V1
        v2 = DataFormatVersions.CARTRIDGE_DATA_V2
        
        # First migrate to v2
        v2_data = self.migrator.migrate(self.v1_data, v1, v2)
        
        # Then migrate back to v1
        v1_restored = self.migrator.migrate(v2_data, v2, v1)
        
        # Validate v1 format
        self.assertTrue(self.migrator.validate_data(v1_restored, v1))
        
        # Check that core data is preserved
        self.assertEqual(v1_restored['rom_data'], self.v1_data['rom_data'])
        self.assertEqual(v1_restored['header_info'], self.v1_data['header_info'])
        self.assertEqual(v1_restored['flash_info'], self.v1_data['flash_info'])
        self.assertEqual(v1_restored['size_kb'], self.v1_data['size_kb'])
        self.assertEqual(v1_restored['save_data'], self.v1_data['save_data'])
        
        # Check that v2-specific fields are not present
        self.assertNotIn('format_version', v1_restored)
        self.assertNotIn('metadata', v1_restored)
        self.assertNotIn('validation', v1_restored)


class TestSaveDataMigration(unittest.TestCase):
    """Test save data format migration"""
    
    def setUp(self):
        """Set up test environment"""
        if not MIGRATION_AVAILABLE:
            self.skipTest("Data migration modules not available")
        
        self.migrator = SaveDataMigrator()
        
        # Sample v1 save data (raw bytes)
        self.v1_data = bytearray([0x01, 0x02, 0x03, 0x04] * 64)  # 256 bytes
    
    def test_can_migrate_save_data(self):
        """Test save data migration capability detection"""
        v1 = DataFormatVersions.SAVE_DATA_V1
        v2 = DataFormatVersions.SAVE_DATA_V2
        cartridge_v1 = DataFormatVersions.CARTRIDGE_DATA_V1
        
        # Should be able to migrate save data
        self.assertTrue(self.migrator.can_migrate(v1, v2))
        self.assertTrue(self.migrator.can_migrate(v2, v1))
        
        # Should not be able to migrate different format types
        self.assertFalse(self.migrator.can_migrate(v1, cartridge_v1))
    
    def test_validate_v1_format(self):
        """Test v1 save data format validation"""
        v1 = DataFormatVersions.SAVE_DATA_V1
        
        # Valid v1 data (bytes or bytearray)
        self.assertTrue(self.migrator.validate_data(self.v1_data, v1))
        self.assertTrue(self.migrator.validate_data(bytes(self.v1_data), v1))
        
        # Invalid data type
        self.assertFalse(self.migrator.validate_data("not bytes", v1))
        self.assertFalse(self.migrator.validate_data(123, v1))
    
    def test_migrate_v1_to_v2(self):
        """Test migration from v1 to v2 save data format"""
        v1 = DataFormatVersions.SAVE_DATA_V1
        v2 = DataFormatVersions.SAVE_DATA_V2
        
        # Migrate data
        v2_data = self.migrator.migrate(self.v1_data, v1, v2)
        
        # Validate v2 format
        self.assertTrue(self.migrator.validate_data(v2_data, v2))
        
        # Check that original data is preserved
        self.assertEqual(v2_data['save_data'], bytes(self.v1_data))
        
        # Check that v2 enhancements are present
        self.assertIn('format_version', v2_data)
        self.assertIn('metadata', v2_data)
        self.assertIn('validation', v2_data)
        self.assertIn('migration_timestamp', v2_data)
        
        # Check metadata structure
        metadata = v2_data['metadata']
        self.assertEqual(metadata['size_bytes'], len(self.v1_data))
        self.assertEqual(metadata['format'], 'raw')
        self.assertEqual(metadata['migration_source'], 'v1_original')
        
        # Check validation structure
        validation = v2_data['validation']
        self.assertIn('checksum', validation)
        self.assertIn('validated', validation)
        self.assertIn('empty_check', validation)
    
    def test_migrate_v2_to_v1(self):
        """Test migration from v2 to v1 save data format"""
        v1 = DataFormatVersions.SAVE_DATA_V1
        v2 = DataFormatVersions.SAVE_DATA_V2
        
        # First migrate to v2
        v2_data = self.migrator.migrate(self.v1_data, v1, v2)
        
        # Then migrate back to v1
        v1_restored = self.migrator.migrate(v2_data, v2, v1)
        
        # Validate v1 format
        self.assertTrue(self.migrator.validate_data(v1_restored, v1))
        
        # Check that data is preserved
        self.assertEqual(v1_restored, bytes(self.v1_data))
    
    def test_empty_save_data_detection(self):
        """Test empty save data detection"""
        # Test empty data
        empty_data = bytearray()
        self.assertTrue(self.migrator._is_empty_save_data(empty_data))
        
        # Test all zeros
        zero_data = bytearray([0x00] * 100)
        self.assertTrue(self.migrator._is_empty_save_data(zero_data))
        
        # Test all 0xFF
        ff_data = bytearray([0xFF] * 100)
        self.assertTrue(self.migrator._is_empty_save_data(ff_data))
        
        # Test mixed data (not empty)
        mixed_data = bytearray([0x01, 0x02, 0x03, 0x04])
        self.assertFalse(self.migrator._is_empty_save_data(mixed_data))


class TestConfigurationMigration(unittest.TestCase):
    """Test configuration format migration"""
    
    def setUp(self):
        """Set up test environment"""
        if not MIGRATION_AVAILABLE:
            self.skipTest("Data migration modules not available")
        
        self.migrator = ConfigurationMigrator()
        
        # Sample v1 configuration data
        self.v1_data = {
            'device_settings': {
                'timeout': 30,
                'baud_rate': 115200,
                'auto_detect': True
            },
            'gui_settings': {
                'theme': 'default',
                'window_size': '800x600',
                'show_advanced': False
            },
            'advanced_settings': {
                'debug_mode': False,
                'log_level': 'INFO',
                'max_retries': 3
            }
        }
    
    def test_can_migrate_config(self):
        """Test configuration migration capability detection"""
        v1 = DataFormatVersions.CONFIG_V1
        v2 = DataFormatVersions.CONFIG_V2
        save_v1 = DataFormatVersions.SAVE_DATA_V1
        
        # Should be able to migrate config data
        self.assertTrue(self.migrator.can_migrate(v1, v2))
        self.assertTrue(self.migrator.can_migrate(v2, v1))
        
        # Should not be able to migrate different format types
        self.assertFalse(self.migrator.can_migrate(v1, save_v1))
    
    def test_validate_v1_format(self):
        """Test v1 configuration format validation"""
        v1 = DataFormatVersions.CONFIG_V1
        
        # Valid v1 data (any dict)
        self.assertTrue(self.migrator.validate_data(self.v1_data, v1))
        self.assertTrue(self.migrator.validate_data({}, v1))
        
        # Invalid data type
        self.assertFalse(self.migrator.validate_data("not a dict", v1))
        self.assertFalse(self.migrator.validate_data(123, v1))
    
    def test_migrate_v1_to_v2(self):
        """Test migration from v1 to v2 configuration format"""
        v1 = DataFormatVersions.CONFIG_V1
        v2 = DataFormatVersions.CONFIG_V2
        
        # Migrate data
        v2_data = self.migrator.migrate(self.v1_data, v1, v2)
        
        # Validate v2 format
        self.assertTrue(self.migrator.validate_data(v2_data, v2))
        
        # Check that original data is preserved
        self.assertEqual(v2_data['device_settings'], self.v1_data['device_settings'])
        self.assertEqual(v2_data['gui_settings'], self.v1_data['gui_settings'])
        self.assertEqual(v2_data['advanced_settings'], self.v1_data['advanced_settings'])
        
        # Check that v2 enhancements are present
        self.assertIn('format_version', v2_data)
        self.assertIn('enhanced_features', v2_data)
        self.assertIn('compatibility', v2_data)
        self.assertIn('migration_info', v2_data)
        
        # Check enhanced features structure
        enhanced_features = v2_data['enhanced_features']
        self.assertIn('enabled', enhanced_features)
        self.assertIn('cartridge_reading_enhancements', enhanced_features)
        self.assertIn('error_handling_enhancements', enhanced_features)
        
        # Check compatibility structure
        compatibility = v2_data['compatibility']
        self.assertIn('api_version', compatibility)
        self.assertIn('compatibility_mode', compatibility)
        self.assertEqual(compatibility['api_version'], '2.0')
    
    def test_migrate_v2_to_v1(self):
        """Test migration from v2 to v1 configuration format"""
        v1 = DataFormatVersions.CONFIG_V1
        v2 = DataFormatVersions.CONFIG_V2
        
        # First migrate to v2
        v2_data = self.migrator.migrate(self.v1_data, v1, v2)
        
        # Then migrate back to v1
        v1_restored = self.migrator.migrate(v2_data, v2, v1)
        
        # Validate v1 format
        self.assertTrue(self.migrator.validate_data(v1_restored, v1))
        
        # Check that core data is preserved
        self.assertEqual(v1_restored['device_settings'], self.v1_data['device_settings'])
        self.assertEqual(v1_restored['gui_settings'], self.v1_data['gui_settings'])
        self.assertEqual(v1_restored['advanced_settings'], self.v1_data['advanced_settings'])
        
        # Check that v2-specific fields are not present
        self.assertNotIn('format_version', v1_restored)
        self.assertNotIn('enhanced_features', v1_restored)
        self.assertNotIn('compatibility', v1_restored)


class TestDataFormatManager(unittest.TestCase):
    """Test data format manager functionality"""
    
    def setUp(self):
        """Set up test environment"""
        if not MIGRATION_AVAILABLE:
            self.skipTest("Data migration modules not available")
        
        self.manager = DataFormatManager()
    
    def test_detect_format_version(self):
        """Test format version detection"""
        # Test v2 format with explicit version
        v2_data = {
            'format_version': '2.0.0',
            'some_data': 'test'
        }
        version = self.manager.detect_format_version(v2_data, 'test_format')
        self.assertEqual(version.major, 2)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
        self.assertEqual(version.format_name, 'test_format')
        
        # Test v1 format without explicit version
        v1_data = {
            'some_data': 'test'
        }
        version = self.manager.detect_format_version(v1_data, 'test_format')
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
    
    def test_get_migrator(self):
        """Test migrator selection"""
        cartridge_v1 = DataFormatVersions.CARTRIDGE_DATA_V1
        cartridge_v2 = DataFormatVersions.CARTRIDGE_DATA_V2
        save_v1 = DataFormatVersions.SAVE_DATA_V1
        
        # Should find cartridge data migrator
        migrator = self.manager.get_migrator(cartridge_v1, cartridge_v2)
        self.assertIsInstance(migrator, CartridgeDataMigrator)
        
        # Should find save data migrator
        migrator = self.manager.get_migrator(save_v1, save_v1)
        self.assertIsInstance(migrator, SaveDataMigrator)
        
        # Should not find migrator for incompatible formats
        migrator = self.manager.get_migrator(cartridge_v1, save_v1)
        self.assertIsNone(migrator)
    
    def test_ensure_compatibility(self):
        """Test data compatibility ensuring"""
        # Test cartridge data compatibility
        v1_cartridge_data = {
            'rom_data': b'\x00\x01\x02\x03',
            'header_info': {},
            'flash_info': {},
            'size_kb': 4
        }
        
        # Should migrate to v2 by default
        compatible_data = self.manager.ensure_compatibility(v1_cartridge_data, 'cartridge_data')
        self.assertIn('format_version', compatible_data)
        self.assertIn('metadata', compatible_data)
        
        # Should not migrate if already compatible
        v2_data = {'format_version': '2.0.0', 'rom_data': b'test'}
        result = self.manager.ensure_compatibility(v2_data, 'cartridge_data')
        self.assertEqual(result, v2_data)  # Should be unchanged


class TestFileFormatMigration(unittest.TestCase):
    """Test file-based format migration"""
    
    def setUp(self):
        """Set up test environment"""
        if not MIGRATION_AVAILABLE:
            self.skipTest("Data migration modules not available")
        
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DataFormatManager()
        self.file_migrator = FileFormatMigrator(self.manager)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_migrate_cartridge_file(self):
        """Test cartridge file migration"""
        # Create test cartridge file
        cartridge_data = {
            'rom_data': [0, 1, 2, 3] * 100,  # JSON-serializable
            'header_info': {'title': 'TEST'},
            'flash_info': {'chip_name': 'TEST_CHIP'},
            'size_kb': 4
        }
        
        cartridge_file = os.path.join(self.temp_dir, 'test_cartridge.json')
        with open(cartridge_file, 'w') as f:
            json.dump(cartridge_data, f)
        
        # Migrate file
        result = self.file_migrator.migrate_cartridge_file(cartridge_file, backup=True)
        self.assertTrue(result)
        
        # Check that backup was created
        backup_file = f"{cartridge_file}.backup"
        self.assertTrue(os.path.exists(backup_file))
        
        # Check that file was migrated
        with open(cartridge_file, 'r') as f:
            migrated_data = json.load(f)
        
        self.assertIn('format_version', migrated_data)
        self.assertIn('metadata', migrated_data)
    
    def test_migrate_config_file(self):
        """Test configuration file migration"""
        # Create test config file
        config_data = {
            'device_settings': {'timeout': 30},
            'gui_settings': {'theme': 'default'}
        }
        
        config_file = os.path.join(self.temp_dir, 'test_config.json')
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Migrate file
        result = self.file_migrator.migrate_config_file(config_file, backup=True)
        self.assertTrue(result)
        
        # Check that backup was created
        backup_file = f"{config_file}.backup"
        self.assertTrue(os.path.exists(backup_file))
        
        # Check that file was migrated
        with open(config_file, 'r') as f:
            migrated_data = json.load(f)
        
        self.assertIn('format_version', migrated_data)
        self.assertIn('enhanced_features', migrated_data)
    
    def test_migrate_directory(self):
        """Test directory migration"""
        # Create test files
        files_to_create = [
            ('test1.json', {'rom_data': [1, 2, 3]}),
            ('test2.json', {'device_settings': {}}),
            ('test.sav', None)  # Binary file
        ]
        
        for filename, data in files_to_create:
            filepath = os.path.join(self.temp_dir, filename)
            if data is not None:
                with open(filepath, 'w') as f:
                    json.dump(data, f)
            else:
                with open(filepath, 'wb') as f:
                    f.write(b'\x01\x02\x03\x04' * 64)
        
        # Migrate directory
        results = self.file_migrator.migrate_directory(self.temp_dir)
        
        # Check results
        self.assertIsInstance(results, dict)
        self.assertGreater(len(results), 0)
        
        # Check that some files were processed
        processed_files = [f for f, success in results.items() if success]
        self.assertGreater(len(processed_files), 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions for data migration"""
    
    def setUp(self):
        """Set up test environment"""
        if not MIGRATION_AVAILABLE:
            self.skipTest("Data migration modules not available")
    
    def test_migrate_cartridge_data_function(self):
        """Test migrate_cartridge_data convenience function"""
        v1_data = {
            'rom_data': b'\x00\x01\x02\x03',
            'header_info': {},
            'flash_info': {},
            'size_kb': 4
        }
        
        # Should migrate to v2 by default
        result = migrate_cartridge_data(v1_data)
        self.assertIn('format_version', result)
        self.assertIn('metadata', result)
    
    def test_migrate_save_data_function(self):
        """Test migrate_save_data convenience function"""
        v1_data = bytearray([1, 2, 3, 4] * 64)
        
        # Should migrate to v2 by default
        result = migrate_save_data(v1_data)
        self.assertIn('format_version', result)
        self.assertIn('save_data', result)
        self.assertEqual(result['save_data'], bytes(v1_data))
    
    def test_migrate_config_data_function(self):
        """Test migrate_config_data convenience function"""
        v1_data = {
            'device_settings': {'timeout': 30},
            'gui_settings': {'theme': 'default'}
        }
        
        # Should migrate to v2 by default
        result = migrate_config_data(v1_data)
        self.assertIn('format_version', result)
        self.assertIn('enhanced_features', result)
    
    def test_migrate_file_function(self):
        """Test migrate_file convenience function"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create test config file
            config_file = os.path.join(temp_dir, 'test.json')
            with open(config_file, 'w') as f:
                json.dump({'device_settings': {}}, f)
            
            # Migrate file
            result = migrate_file(config_file, backup=True)
            self.assertTrue(result)
            
            # Check backup exists
            self.assertTrue(os.path.exists(f"{config_file}.backup"))
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


def run_data_format_tests():
    """Run all data format compatibility tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestDataFormatVersions,
        TestCartridgeDataMigration,
        TestSaveDataMigration,
        TestConfigurationMigration,
        TestDataFormatManager,
        TestFileFormatMigration,
        TestConvenienceFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running MRUpdater Data Format Compatibility Tests...")
    print("=" * 55)
    
    success = run_data_format_tests()
    
    print("\n" + "=" * 55)
    if success:
        print("✓ All data format compatibility tests passed!")
        exit(0)
    else:
        print("✗ Some data format compatibility tests failed!")
        exit(1)