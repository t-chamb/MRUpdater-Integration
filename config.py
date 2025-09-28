"""
Enhanced Configuration System for MRUpdater

This module provides a comprehensive configuration management system that integrates
features from both the original and enhanced codebases. It maintains backward
compatibility while adding new functionality for enhanced features.

Key Features:
- Backward compatible configuration loading
- Enhanced feature flag management
- Automatic configuration migration
- Type-safe configuration access
- Comprehensive error handling
"""

import os
import configparser
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from enum import Enum

# Version information
version = '1.6.1'
sha = '437adea'
__version__ = version
__version_sha__ = f'v{version}+{sha}'
__env__ = 'prod'

# Configuration constants (enhanced from both codebases)
CONFIG_FILE_NAME = 'config.ini'
APP_NAME = 'MRUpdater'
APP_AUTHOR = 'ModRetro'

# Try to import platformdirs for enhanced directory management
try:
    from platformdirs import user_data_dir
    APP_DATA_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
except ImportError:
    # Fallback to basic directory structure
    if os.name == 'nt':
        APP_DATA_DIR = os.path.join(os.environ.get('APPDATA', ''), APP_NAME)
    else:
        APP_DATA_DIR = os.path.join(os.path.expanduser('~'), f'.{APP_NAME.lower()}')

# Enhanced feature flags (from decompiled version)
class MRUpdaterFeature(Enum):
    PREVIEW_FIRMWARE = 'mrupdater.system:preview-firmware'
    ROLLBACK_FIRMWARE = 'mrupdater.system:rollback-firmware'
    ENHANCED_DETECTION = 'mrupdater.cartridge:enhanced-detection'
    FRAM_SUPPORT = 'mrupdater.cartridge:fram-support'
    ADVANCED_LOGGING = 'mrupdater.system:advanced-logging'


class EnhancedConfigParser:
    """
    Enhanced configuration parser that integrates features from both codebases.
    Maintains backward compatibility while adding new functionality.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = configparser.ConfigParser()
        self.config_file = config_file or CONFIG_FILE_NAME
        self.config_path = os.path.join(APP_DATA_DIR, self.config_file)
        self._ensure_config_directory()
        self._load_defaults()
        
    def _ensure_config_directory(self):
        """Ensure the configuration directory exists."""
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        
    def _load_defaults(self):
        """Load default configuration values."""
        defaults = {
            'DEFAULT': {
                'version': __version__,
                'environment': __env__,
                'log_level': 'INFO',
                'enhanced_mode': 'true',
                'auto_detect_devices': 'true',
                'enable_fram_detection': 'true',
                'connection_timeout': '30',
                'retry_attempts': '3',
                'backup_saves': 'true'
            },
            'FIRMWARE': {
                'fpga_fw_file_path': '',
                'mcu_fw_file_path': '',
                'cart_fw_file_path': '',
                'auto_update_check': 'true',
                'preview_firmware_enabled': 'false',
                'rollback_enabled': 'true'
            },
            'GUI': {
                'theme': 'default',
                'font_size': '10',
                'enable_animations': 'true',
                'show_advanced_options': 'false',
                'remember_window_size': 'true'
            },
            'CARTRIDGE': {
                'default_read_mode': 'enhanced',
                'verify_checksums': 'true',
                'backup_before_write': 'true',
                'enable_save_data_backup': 'true'
            },
            'LOGGING': {
                'enable_file_logging': 'true',
                'log_file_path': '',
                'max_log_size_mb': '10',
                'log_retention_days': '30'
            }
        }
        
        for section, options in defaults.items():
            if not self.config.has_section(section) and section != 'DEFAULT':
                self.config.add_section(section)
            for option, value in options.items():
                if section == 'DEFAULT':
                    self.config.set('DEFAULT', option, value)
                else:
                    self.config.set(section, option, value)
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.
        Returns a dictionary with all configuration values.
        Maintains backward compatibility with original load() method.
        """
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path, encoding='utf-8')
        except Exception as e:
            logging.warning(f"Failed to load configuration: {e}")
            
        # Return backward-compatible dictionary for original code
        result = {
            'fpga_fw_file_path': self.get('fpga_fw_file_path', section='FIRMWARE'),
            'mcu_fw_file_path': self.get('mcu_fw_file_path', section='FIRMWARE'),
            'cart_fw_file_path': self.get('cart_fw_file_path', section='FIRMWARE')
        }
        
        # Add enhanced configuration options
        result.update({
            'version': self.get('version'),
            'environment': self.get('environment'),
            'enhanced_mode': self.get_bool('enhanced_mode'),
            'log_level': self.get('log_level'),
            'theme': self.get('theme', section='GUI'),
            'auto_detect_devices': self.get_bool('auto_detect_devices'),
            'enable_fram_detection': self.get_bool('enable_fram_detection'),
            'connection_timeout': self.get_int('connection_timeout'),
            'retry_attempts': self.get_int('retry_attempts')
        })
        
        return result
    
    def get(self, option: str, section: str = 'DEFAULT', fallback: str = '') -> str:
        """
        Get a configuration value as string.
        Enhanced version with section support and better error handling.
        """
        try:
            return self.config.get(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_bool(self, option: str, section: str = 'DEFAULT', fallback: bool = False) -> bool:
        """Get a configuration value as boolean."""
        try:
            return self.config.getboolean(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_int(self, option: str, section: str = 'DEFAULT', fallback: int = 0) -> int:
        """Get a configuration value as integer."""
        try:
            return self.config.getint(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_float(self, option: str, section: str = 'DEFAULT', fallback: float = 0.0) -> float:
        """Get a configuration value as float."""
        try:
            return self.config.getfloat(section, option, fallback=fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def set(self, option: str, value: Union[str, int, float, bool], section: str = 'DEFAULT'):
        """
        Set a configuration value.
        Enhanced version with section support and type handling.
        """
        if section != 'DEFAULT' and not self.config.has_section(section):
            self.config.add_section(section)
            
        # Convert value to string for configparser
        str_value = str(value).lower() if isinstance(value, bool) else str(value)
        self.config.set(section, option, str_value)
    
    def save(self):
        """Save configuration to file with enhanced error handling."""
        try:
            self._ensure_config_directory()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            raise
    
    def get_eula_consent_key(self) -> str:
        """
        Get EULA consent key (from decompiled version).
        This method maintains compatibility with the decompiled consent system.
        """
        # Import here to avoid circular dependencies
        try:
            from flashing_tool.gui.consent_dialog import ConsentDialog
            return f'eula_consented_{ConsentDialog.get_eula_sha()}'
        except ImportError:
            # Fallback if consent dialog is not available
            return 'eula_consented_default'
    
    def is_feature_enabled(self, feature: MRUpdaterFeature) -> bool:
        """Check if a specific feature is enabled."""
        feature_key = f'feature_{feature.value.replace(":", "_").replace("-", "_")}'
        return self.get_bool(feature_key, fallback=False)
    
    def enable_feature(self, feature: MRUpdaterFeature, enabled: bool = True):
        """Enable or disable a specific feature."""
        feature_key = f'feature_{feature.value.replace(":", "_").replace("-", "_")}'
        self.set(feature_key, enabled)
    
    def migrate_from_old_config(self, old_config_path: str) -> bool:
        """
        Migrate configuration from an old format.
        Provides backward compatibility for existing installations.
        """
        if not os.path.exists(old_config_path):
            return False
            
        try:
            old_config = configparser.ConfigParser()
            old_config.read(old_config_path, encoding='utf-8')
            
            # Migrate known settings
            migration_map = {
                ('DEFAULT', 'fpga_fw_file_path'): ('FIRMWARE', 'fpga_fw_file_path'),
                ('DEFAULT', 'mcu_fw_file_path'): ('FIRMWARE', 'mcu_fw_file_path'),
                ('DEFAULT', 'cart_fw_file_path'): ('FIRMWARE', 'cart_fw_file_path'),
            }
            
            for (old_section, old_option), (new_section, new_option) in migration_map.items():
                try:
                    value = old_config.get(old_section, old_option)
                    self.set(new_option, value, new_section)
                except (configparser.NoSectionError, configparser.NoOptionError):
                    continue
            
            self.save()
            return True
            
        except Exception as e:
            logging.error(f"Failed to migrate configuration: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config.clear()
        self._load_defaults()
        self.save()
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about the current configuration."""
        return {
            'config_path': self.config_path,
            'config_exists': os.path.exists(self.config_path),
            'app_data_dir': APP_DATA_DIR,
            'version': __version__,
            'environment': __env__,
            'sections': list(self.config.sections()) + ['DEFAULT']
        }


# Global configuration instance for backward compatibility
_global_config = None

def get_config() -> EnhancedConfigParser:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = EnhancedConfigParser()
        _global_config.load()
    return _global_config

def load_config() -> Dict[str, Any]:
    """Load configuration (backward compatible function)."""
    return get_config().load()

# Backward compatibility aliases
ConfigParser = EnhancedConfigParser