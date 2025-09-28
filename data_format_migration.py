"""
Data Format Compatibility and Migration Utilities

This module provides comprehensive data format compatibility and migration
utilities to ensure all existing data formats remain compatible while
supporting enhanced data structures from the integrated codebase.
"""

import json
import logging
import os
import shutil
import struct
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

logger = logging.getLogger('mrupdater.migration')


@dataclass
class DataFormatVersion:
    """Data format version information"""
    major: int
    minor: int
    patch: int
    format_name: str
    description: str = ""
    
    @property
    def version_string(self) -> str:
        """Get version as string"""
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __str__(self) -> str:
        return f"{self.format_name} v{self.version_string}"
    
    def is_compatible_with(self, other: 'DataFormatVersion') -> bool:
        """Check if this version is compatible with another"""
        # Same major version is compatible
        return self.major == other.major


# Define supported data format versions
class DataFormatVersions:
    """Registry of supported data format versions"""
    
    # Cartridge data formats
    CARTRIDGE_DATA_V1 = DataFormatVersion(1, 0, 0, "cartridge_data", "Original cartridge data format")
    CARTRIDGE_DATA_V2 = DataFormatVersion(2, 0, 0, "cartridge_data", "Enhanced cartridge data with metadata")
    
    # Save data formats
    SAVE_DATA_V1 = DataFormatVersion(1, 0, 0, "save_data", "Original save data format")
    SAVE_DATA_V2 = DataFormatVersion(2, 0, 0, "save_data", "Enhanced save data with validation")
    
    # Configuration formats
    CONFIG_V1 = DataFormatVersion(1, 0, 0, "config", "Original configuration format")
    CONFIG_V2 = DataFormatVersion(2, 0, 0, "config", "Enhanced configuration with feature flags")
    
    # Firmware data formats
    FIRMWARE_V1 = DataFormatVersion(1, 0, 0, "firmware", "Original firmware format")
    FIRMWARE_V2 = DataFormatVersion(2, 0, 0, "firmware", "Enhanced firmware with metadata")


class DataMigrator(ABC):
    """Abstract base class for data migrators"""
    
    @abstractmethod
    def can_migrate(self, from_version: DataFormatVersion, to_version: DataFormatVersion) -> bool:
        """Check if this migrator can handle the version migration"""
        pass
    
    @abstractmethod
    def migrate(self, data: Any, from_version: DataFormatVersion, to_version: DataFormatVersion) -> Any:
        """Migrate data from one version to another"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Any, version: DataFormatVersion) -> bool:
        """Validate data format"""
        pass


class CartridgeDataMigrator(DataMigrator):
    """Migrator for cartridge data formats"""
    
    def can_migrate(self, from_version: DataFormatVersion, to_version: DataFormatVersion) -> bool:
        """Check if can migrate cartridge data"""
        return (from_version.format_name == "cartridge_data" and 
                to_version.format_name == "cartridge_data")
    
    def migrate(self, data: Any, from_version: DataFormatVersion, to_version: DataFormatVersion) -> Any:
        """Migrate cartridge data between versions"""
        if from_version.major == 1 and to_version.major == 2:
            return self._migrate_v1_to_v2(data)
        elif from_version.major == 2 and to_version.major == 1:
            return self._migrate_v2_to_v1(data)
        else:
            raise ValueError(f"Unsupported migration: {from_version} -> {to_version}")
    
    def validate_data(self, data: Any, version: DataFormatVersion) -> bool:
        """Validate cartridge data format"""
        if version.major == 1:
            return self._validate_v1_format(data)
        elif version.major == 2:
            return self._validate_v2_format(data)
        else:
            return False
    
    def _migrate_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate v1 cartridge data to v2 format"""
        logger.info("Migrating cartridge data from v1 to v2")
        
        # V2 format adds metadata and enhanced validation
        v2_data = {
            'format_version': DataFormatVersions.CARTRIDGE_DATA_V2.version_string,
            'migration_timestamp': time.time(),
            'original_format_version': DataFormatVersions.CARTRIDGE_DATA_V1.version_string,
            
            # Original data (preserved)
            'rom_data': data.get('rom_data'),
            'header_info': data.get('header_info', {}),
            'flash_info': data.get('flash_info', {}),
            'size_kb': data.get('size_kb', 0),
            
            # Enhanced metadata (new in v2)
            'metadata': {
                'checksum_validated': False,
                'fram_detected': False,
                'save_data_present': False,
                'enhanced_features_used': True,
                'migration_source': 'v1_original'
            },
            
            # Enhanced validation data
            'validation': {
                'header_checksum': None,
                'data_hash': None,
                'validation_timestamp': time.time()
            },
            
            # Save data (if present)
            'save_data': data.get('save_data'),
            'save_data_metadata': {
                'size_bytes': len(data.get('save_data', b'')),
                'format': 'raw',
                'validated': False
            } if data.get('save_data') else None
        }
        
        return v2_data
    
    def _migrate_v2_to_v1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate v2 cartridge data to v1 format"""
        logger.info("Migrating cartridge data from v2 to v1")
        
        # V1 format is simpler, extract core data
        v1_data = {
            'rom_data': data.get('rom_data'),
            'header_info': data.get('header_info', {}),
            'flash_info': data.get('flash_info', {}),
            'size_kb': data.get('size_kb', 0),
            'save_data': data.get('save_data')
        }
        
        return v1_data
    
    def _validate_v1_format(self, data: Any) -> bool:
        """Validate v1 cartridge data format"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ['rom_data']
        return all(field in data for field in required_fields)
    
    def _validate_v2_format(self, data: Any) -> bool:
        """Validate v2 cartridge data format"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ['format_version', 'rom_data', 'metadata', 'validation']
        return all(field in data for field in required_fields)


class SaveDataMigrator(DataMigrator):
    """Migrator for save data formats"""
    
    def can_migrate(self, from_version: DataFormatVersion, to_version: DataFormatVersion) -> bool:
        """Check if can migrate save data"""
        return (from_version.format_name == "save_data" and 
                to_version.format_name == "save_data")
    
    def migrate(self, data: Any, from_version: DataFormatVersion, to_version: DataFormatVersion) -> Any:
        """Migrate save data between versions"""
        if from_version.major == 1 and to_version.major == 2:
            return self._migrate_v1_to_v2(data)
        elif from_version.major == 2 and to_version.major == 1:
            return self._migrate_v2_to_v1(data)
        else:
            raise ValueError(f"Unsupported migration: {from_version} -> {to_version}")
    
    def validate_data(self, data: Any, version: DataFormatVersion) -> bool:
        """Validate save data format"""
        if version.major == 1:
            return self._validate_v1_format(data)
        elif version.major == 2:
            return self._validate_v2_format(data)
        else:
            return False
    
    def _migrate_v1_to_v2(self, data: Union[bytes, bytearray]) -> Dict[str, Any]:
        """Migrate v1 save data to v2 format"""
        logger.info("Migrating save data from v1 to v2")
        
        # Convert bytes to list for JSON serialization
        save_data_list = list(data) if data else []
        
        # V2 format adds metadata and validation
        v2_data = {
            'format_version': DataFormatVersions.SAVE_DATA_V2.version_string,
            'migration_timestamp': time.time(),
            'original_format_version': DataFormatVersions.SAVE_DATA_V1.version_string,
            
            # Original save data (as list for JSON compatibility)
            'save_data': save_data_list,
            
            # Enhanced metadata
            'metadata': {
                'size_bytes': len(data) if data else 0,
                'format': 'raw',
                'game_title': None,
                'save_type': 'unknown',
                'migration_source': 'v1_original'
            },
            
            # Validation data
            'validation': {
                'checksum': self._calculate_checksum(data) if data else None,
                'validated': False,
                'validation_timestamp': time.time(),
                'empty_check': self._is_empty_save_data(data) if data else True
            }
        }
        
        return v2_data
    
    def _migrate_v2_to_v1(self, data: Dict[str, Any]) -> Union[bytes, bytearray]:
        """Migrate v2 save data to v1 format"""
        logger.info("Migrating save data from v2 to v1")
        
        # V1 format is just raw bytes
        save_data = data.get('save_data', [])
        
        # Handle both list (JSON format) and bytes
        if isinstance(save_data, list):
            return bytes(save_data)
        elif isinstance(save_data, (bytes, bytearray)):
            return bytes(save_data)
        else:
            return b''
    
    def _validate_v1_format(self, data: Any) -> bool:
        """Validate v1 save data format"""
        return isinstance(data, (bytes, bytearray))
    
    def _validate_v2_format(self, data: Any) -> bool:
        """Validate v2 save data format"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ['format_version', 'save_data', 'metadata', 'validation']
        return all(field in data for field in required_fields)
    
    def _calculate_checksum(self, data: Union[bytes, bytearray]) -> int:
        """Calculate simple checksum for save data"""
        if not data:
            return 0
        return sum(data) & 0xFFFF
    
    def _is_empty_save_data(self, data: Union[bytes, bytearray]) -> bool:
        """Check if save data appears to be empty"""
        if not data:
            return True
        
        # Check for common empty patterns
        all_zero = all(b == 0x00 for b in data)
        all_ff = all(b == 0xFF for b in data)
        
        return all_zero or all_ff


class ConfigurationMigrator(DataMigrator):
    """Migrator for configuration formats"""
    
    def can_migrate(self, from_version: DataFormatVersion, to_version: DataFormatVersion) -> bool:
        """Check if can migrate configuration"""
        return (from_version.format_name == "config" and 
                to_version.format_name == "config")
    
    def migrate(self, data: Any, from_version: DataFormatVersion, to_version: DataFormatVersion) -> Any:
        """Migrate configuration between versions"""
        if from_version.major == 1 and to_version.major == 2:
            return self._migrate_v1_to_v2(data)
        elif from_version.major == 2 and to_version.major == 1:
            return self._migrate_v2_to_v1(data)
        else:
            raise ValueError(f"Unsupported migration: {from_version} -> {to_version}")
    
    def validate_data(self, data: Any, version: DataFormatVersion) -> bool:
        """Validate configuration format"""
        if version.major == 1:
            return self._validate_v1_format(data)
        elif version.major == 2:
            return self._validate_v2_format(data)
        else:
            return False
    
    def _migrate_v1_to_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate v1 configuration to v2 format"""
        logger.info("Migrating configuration from v1 to v2")
        
        # V2 format adds enhanced features configuration
        v2_data = {
            'format_version': DataFormatVersions.CONFIG_V2.version_string,
            'migration_timestamp': time.time(),
            'original_format_version': DataFormatVersions.CONFIG_V1.version_string,
            
            # Original configuration (preserved)
            'device_settings': data.get('device_settings', {}),
            'gui_settings': data.get('gui_settings', {}),
            'advanced_settings': data.get('advanced_settings', {}),
            
            # Enhanced features configuration (new in v2)
            'enhanced_features': {
                'enabled': True,
                'cartridge_reading_enhancements': True,
                'cartridge_writing_enhancements': True,
                'device_communication_enhancements': True,
                'error_handling_enhancements': True,
                'progress_reporting_enhancements': True,
                'flash_detection_enhancements': True,
                'fram_support_enhancements': True,
                'session_management_enhancements': True,
                'gui_responsiveness_enhancements': True,
                'checksum_validation_enhancements': True,
                'save_data_handling_enhancements': True
            },
            
            # Compatibility settings
            'compatibility': {
                'api_version': '2.0',
                'compatibility_mode': 'enhanced',
                'auto_fallback': True,
                'warn_deprecated': True,
                'strict_compatibility': False
            },
            
            # Migration metadata
            'migration_info': {
                'migrated_from': 'v1_original',
                'migration_timestamp': time.time(),
                'migration_reason': 'enhanced_features_integration'
            }
        }
        
        return v2_data
    
    def _migrate_v2_to_v1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate v2 configuration to v1 format"""
        logger.info("Migrating configuration from v2 to v1")
        
        # V1 format is simpler, extract core settings
        v1_data = {
            'device_settings': data.get('device_settings', {}),
            'gui_settings': data.get('gui_settings', {}),
            'advanced_settings': data.get('advanced_settings', {})
        }
        
        return v1_data
    
    def _validate_v1_format(self, data: Any) -> bool:
        """Validate v1 configuration format"""
        return isinstance(data, dict)
    
    def _validate_v2_format(self, data: Any) -> bool:
        """Validate v2 configuration format"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ['format_version', 'enhanced_features', 'compatibility']
        return all(field in data for field in required_fields)


class DataFormatManager:
    """Manages data format compatibility and migration"""
    
    def __init__(self):
        """Initialize data format manager"""
        self.migrators = [
            CartridgeDataMigrator(),
            SaveDataMigrator(),
            ConfigurationMigrator()
        ]
    
    def detect_format_version(self, data: Any, format_name: str) -> Optional[DataFormatVersion]:
        """Detect the version of data format"""
        if isinstance(data, dict) and 'format_version' in data:
            # V2+ format with explicit version
            version_str = data['format_version']
            parts = version_str.split('.')
            if len(parts) >= 3:
                major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
                return DataFormatVersion(major, minor, patch, format_name)
        
        # Assume V1 format if no version information
        return DataFormatVersion(1, 0, 0, format_name)
    
    def get_migrator(self, from_version: DataFormatVersion, to_version: DataFormatVersion) -> Optional[DataMigrator]:
        """Get appropriate migrator for version transition"""
        for migrator in self.migrators:
            if migrator.can_migrate(from_version, to_version):
                return migrator
        return None
    
    def migrate_data(self, data: Any, from_version: DataFormatVersion, to_version: DataFormatVersion) -> Any:
        """Migrate data between versions"""
        migrator = self.get_migrator(from_version, to_version)
        if migrator is None:
            raise ValueError(f"No migrator available for {from_version} -> {to_version}")
        
        logger.info(f"Migrating data: {from_version} -> {to_version}")
        return migrator.migrate(data, from_version, to_version)
    
    def validate_data(self, data: Any, version: DataFormatVersion) -> bool:
        """Validate data format"""
        migrator = self.get_migrator(version, version)  # Same version
        if migrator is None:
            logger.warning(f"No validator available for {version}")
            return True  # Assume valid if no validator
        
        return migrator.validate_data(data, version)
    
    def ensure_compatibility(self, data: Any, format_name: str, target_version: Optional[DataFormatVersion] = None) -> Any:
        """Ensure data is compatible with target version"""
        current_version = self.detect_format_version(data, format_name)
        
        if target_version is None:
            # Default to latest version for format
            if format_name == "cartridge_data":
                target_version = DataFormatVersions.CARTRIDGE_DATA_V2
            elif format_name == "save_data":
                target_version = DataFormatVersions.SAVE_DATA_V2
            elif format_name == "config":
                target_version = DataFormatVersions.CONFIG_V2
            else:
                return data  # No migration needed
        
        if current_version.is_compatible_with(target_version):
            return data  # Already compatible
        
        # Migrate to target version
        return self.migrate_data(data, current_version, target_version)


class FileFormatMigrator:
    """Handles migration of file-based data formats"""
    
    def __init__(self, data_format_manager: DataFormatManager):
        """Initialize file format migrator"""
        self.data_manager = data_format_manager
    
    def migrate_cartridge_file(self, file_path: str, backup: bool = True) -> bool:
        """Migrate cartridge data file to latest format"""
        try:
            # Create backup if requested
            if backup:
                backup_path = f"{file_path}.backup"
                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Load current data
            with open(file_path, 'rb') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                else:
                    # Assume binary cartridge data
                    data = {'rom_data': f.read()}
            
            # Detect and migrate format
            current_version = self.data_manager.detect_format_version(data, "cartridge_data")
            target_version = DataFormatVersions.CARTRIDGE_DATA_V2
            
            if not current_version.is_compatible_with(target_version):
                migrated_data = self.data_manager.migrate_data(data, current_version, target_version)
                
                # Save migrated data
                with open(file_path, 'w') as f:
                    json.dump(migrated_data, f, indent=2)
                
                logger.info(f"Migrated cartridge file: {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate cartridge file {file_path}: {e}")
            return False
    
    def migrate_save_file(self, file_path: str, backup: bool = True) -> bool:
        """Migrate save data file to latest format"""
        try:
            # Create backup if requested
            if backup:
                backup_path = f"{file_path}.backup"
                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Load current data
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                # Assume binary save data
                with open(file_path, 'rb') as f:
                    data = f.read()
            
            # Detect and migrate format
            current_version = self.data_manager.detect_format_version(data, "save_data")
            target_version = DataFormatVersions.SAVE_DATA_V2
            
            if not current_version.is_compatible_with(target_version):
                migrated_data = self.data_manager.migrate_data(data, current_version, target_version)
                
                # Convert bytes to list for JSON serialization
                if 'save_data' in migrated_data and isinstance(migrated_data['save_data'], bytes):
                    migrated_data['save_data'] = list(migrated_data['save_data'])
                
                # Save migrated data as JSON
                json_path = file_path.replace('.sav', '.json').replace('.save', '.json')
                with open(json_path, 'w') as f:
                    json.dump(migrated_data, f, indent=2)
                
                logger.info(f"Migrated save file: {file_path} -> {json_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate save file {file_path}: {e}")
            return False
    
    def migrate_config_file(self, file_path: str, backup: bool = True) -> bool:
        """Migrate configuration file to latest format"""
        try:
            # Create backup if requested
            if backup:
                backup_path = f"{file_path}.backup"
                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Load current configuration
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                # Parse INI-style config
                data = self._parse_ini_config(file_path)
            
            # Detect and migrate format
            current_version = self.data_manager.detect_format_version(data, "config")
            target_version = DataFormatVersions.CONFIG_V2
            
            if not current_version.is_compatible_with(target_version):
                migrated_data = self.data_manager.migrate_data(data, current_version, target_version)
                
                # Save migrated configuration as JSON
                json_path = file_path.replace('.ini', '.json').replace('.cfg', '.json')
                with open(json_path, 'w') as f:
                    json.dump(migrated_data, f, indent=2)
                
                logger.info(f"Migrated config file: {file_path} -> {json_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate config file {file_path}: {e}")
            return False
    
    def _parse_ini_config(self, file_path: str) -> Dict[str, Any]:
        """Parse INI-style configuration file"""
        import configparser
        
        config = configparser.ConfigParser()
        config.read(file_path)
        
        data = {}
        for section_name in config.sections():
            data[section_name] = dict(config[section_name])
        
        return data
    
    def migrate_directory(self, directory_path: str, file_patterns: List[str] = None) -> Dict[str, bool]:
        """Migrate all compatible files in a directory"""
        if file_patterns is None:
            file_patterns = ['*.json', '*.sav', '*.cfg', '*.ini']
        
        results = {}
        directory = Path(directory_path)
        
        for pattern in file_patterns:
            for file_path in directory.glob(pattern):
                file_str = str(file_path)
                
                if any(ext in file_str for ext in ['.sav', '.save']):
                    results[file_str] = self.migrate_save_file(file_str)
                elif any(ext in file_str for ext in ['.cfg', '.ini', '.config']):
                    results[file_str] = self.migrate_config_file(file_str)
                elif '.json' in file_str:
                    # Try to determine type from content
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        if 'rom_data' in data:
                            results[file_str] = self.migrate_cartridge_file(file_str)
                        elif 'save_data' in data:
                            results[file_str] = self.migrate_save_file(file_str)
                        else:
                            results[file_str] = self.migrate_config_file(file_str)
                    except:
                        results[file_str] = False
        
        return results


# Global data format manager instance
_data_format_manager = None
_file_format_migrator = None


def get_data_format_manager() -> DataFormatManager:
    """Get global data format manager instance"""
    global _data_format_manager
    if _data_format_manager is None:
        _data_format_manager = DataFormatManager()
    return _data_format_manager


def get_file_format_migrator() -> FileFormatMigrator:
    """Get global file format migrator instance"""
    global _file_format_migrator
    if _file_format_migrator is None:
        _file_format_migrator = FileFormatMigrator(get_data_format_manager())
    return _file_format_migrator


# Convenience functions
def migrate_cartridge_data(data: Any, target_version: Optional[DataFormatVersion] = None) -> Any:
    """Migrate cartridge data to target version"""
    return get_data_format_manager().ensure_compatibility(data, "cartridge_data", target_version)


def migrate_save_data(data: Any, target_version: Optional[DataFormatVersion] = None) -> Any:
    """Migrate save data to target version"""
    return get_data_format_manager().ensure_compatibility(data, "save_data", target_version)


def migrate_config_data(data: Any, target_version: Optional[DataFormatVersion] = None) -> Any:
    """Migrate configuration data to target version"""
    return get_data_format_manager().ensure_compatibility(data, "config", target_version)


def migrate_file(file_path: str, backup: bool = True) -> bool:
    """Migrate any supported file to latest format"""
    migrator = get_file_format_migrator()
    
    if any(ext in file_path for ext in ['.sav', '.save']):
        return migrator.migrate_save_file(file_path, backup)
    elif any(ext in file_path for ext in ['.cfg', '.ini', '.config']):
        return migrator.migrate_config_file(file_path, backup)
    elif '.json' in file_path:
        # Try to determine type from content
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if 'rom_data' in data:
                return migrator.migrate_cartridge_file(file_path, backup)
            elif 'save_data' in data:
                return migrator.migrate_save_file(file_path, backup)
            else:
                return migrator.migrate_config_file(file_path, backup)
        except:
            return False
    else:
        logger.warning(f"Unknown file type for migration: {file_path}")
        return False


__all__ = [
    'DataFormatVersion',
    'DataFormatVersions',
    'DataMigrator',
    'CartridgeDataMigrator',
    'SaveDataMigrator',
    'ConfigurationMigrator',
    'DataFormatManager',
    'FileFormatMigrator',
    'get_data_format_manager',
    'get_file_format_migrator',
    'migrate_cartridge_data',
    'migrate_save_data',
    'migrate_config_data',
    'migrate_file'
]