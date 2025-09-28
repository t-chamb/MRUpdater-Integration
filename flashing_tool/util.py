"""
Enhanced Utility Functions for Flashing Tool

Integrated utility functions from decompiled codebase with
improved functionality and error handling.
"""

import os
import platform
import re
import sys
import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import logging

# Configuration constants
CONFIG_FILE_NAME = 'config.ini'
CPU_TYPES = {
    'AMD64': 'x86_64',
    'x86_64': 'x86_64', 
    'arm64': 'arm64',
    'aarch64': 'arm64'
}

# Try to import environment configuration (enhanced integration)
try:
    from config import __env__, get_config, MRUpdaterFeature
    _config = get_config()
except ImportError:
    __env__ = 'production'
    _config = None
    
    # Fallback MRUpdaterFeature for compatibility
    class MRUpdaterFeature:
        PREVIEW_FIRMWARE = 'mrupdater.system:preview-firmware'
        ROLLBACK_FIRMWARE = 'mrupdater.system:rollback-firmware'
        ENHANCED_DETECTION = 'mrupdater.cartridge:enhanced-detection'
        FRAM_SUPPORT = 'mrupdater.cartridge:fram-support'
        ADVANCED_LOGGING = 'mrupdater.system:advanced-logging'

flashing_tool_logger = logging.getLogger('mrupdater')


class FlashOperation(Enum):
    """Enumeration of flash operation types"""
    BOTH = 1
    FPGA = 2
    MCU = 3
    CART = 4


@dataclass
class S3FirmwareInfo:
    """Information about firmware stored in S3"""
    bucket: str
    key: str
    version: str
    size: Optional[int] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None


@dataclass
class ChromaticFirmwarePackage:
    """Chromatic firmware package information"""
    fpga_file: str
    mcu_file: str
    version: str
    changelog: Optional[str] = None
    size: Optional[int] = None


@dataclass
class CartClinicFirmwarePackage:
    """Cart Clinic firmware package information"""
    firmware_file: str
    version: str
    changelog: Optional[str] = None
    size: Optional[int] = None


@dataclass
class MRUpdaterManifestData:
    """MRUpdater manifest data structure"""
    version: str
    chromatic_firmware: Optional[ChromaticFirmwarePackage] = None
    cart_clinic_firmware: Optional[CartClinicFirmwarePackage] = None
    changelog: Optional[str] = None
    release_notes: Optional[str] = None


def resolve_path(path: str) -> str:
    """
    Returns the absolute path for the specified relative path

    The value specified in @param path should be relative to the application's
    entry point, not the module calling resolve_path.
    
    Args:
        path: Relative path to resolve
        
    Returns:
        Absolute path
    """
    # Get the execution path (handles both bundled and development environments)
    exec_path = getattr(sys, '_MEIPASS', os.getcwd())
    resolved_path = os.path.abspath(os.path.join(exec_path, path))
    
    flashing_tool_logger.debug(f"Resolved path '{path}' to '{resolved_path}'")
    return resolved_path


def split_version_string(aggregate_version: str) -> str:
    """
    Splits an aggregate version string into its FPGA/MCU components

    Args:
        aggregate_version: Combined version string eg v18.0_0.12.3

    Returns:
        Formatted version string with FPGA and MCU components
    """
    if not aggregate_version:
        return aggregate_version
    
    # Match pattern like v18.0_0.12.3
    fw_search = re.match(r'v(\d+\.\d+)_(\d+\.\d+\.\d+)', aggregate_version)
    if fw_search:
        fpga_version = fw_search.group(1)
        mcu_version = fw_search.group(2)
        return f'FPGA: {fpga_version}, MCU: {mcu_version}'
    
    # If pattern doesn't match, return original
    return aggregate_version


def is_env_manufacturing() -> bool:
    """
    Check if running in manufacturing environment
    
    Returns:
        True if in manufacturing environment
    """
    return __env__ == 'manufacturing'


def is_env_dev() -> bool:
    """
    Check if running in development environment
    
    Returns:
        True if in development environment
    """
    return __env__ == 'dev'


def is_env_production() -> bool:
    """
    Check if running in production environment
    
    Returns:
        True if in production environment
    """
    return __env__ == 'production'


def get_environment() -> str:
    """
    Get current environment name
    
    Returns:
        Environment name string
    """
    return __env__


def get_openfpga_loader_bin_path() -> str:
    """
    Gets and returns the path to the openFPGALoader executable

    The path to the executable depends on the current execution
    environment. When the app is in bundled form, only a single
    binary is available. However, for development purposes, there
    are multiple binaries - one for each of the supported platforms
    and CPU architectures
    
    Returns:
        Path to openFPGALoader executable
    """
    binary_name = 'openFPGALoader'
    cpu_type = CPU_TYPES.get(platform.machine(), platform.machine())
    
    # Add platform-specific extensions
    if sys.platform == 'win32':
        binary_name += '.exe'
    elif sys.platform == 'linux':
        binary_name += f'-{cpu_type}.AppImage'
    
    # Determine platform path
    platform_path = ''
    if not hasattr(sys, '_MEIPASS'):  # Development environment
        if sys.platform == 'darwin':
            platform_path = os.path.join(sys.platform, cpu_type)
        else:
            platform_path = sys.platform
    
    # Construct relative path
    relative_path = os.path.join('lib', 'openFPGALoader', platform_path, binary_name)
    full_path = resolve_path(relative_path)
    
    flashing_tool_logger.debug(f"openFPGALoader binary path: {full_path}")
    return full_path


def validate_firmware_file(filepath: str) -> bool:
    """
    Validate that a firmware file exists and is readable
    
    Args:
        filepath: Path to firmware file
        
    Returns:
        True if file is valid
    """
    if not filepath:
        return False
    
    try:
        if not os.path.isfile(filepath):
            flashing_tool_logger.error(f"Firmware file not found: {filepath}")
            return False
        
        if not os.access(filepath, os.R_OK):
            flashing_tool_logger.error(f"Firmware file not readable: {filepath}")
            return False
        
        # Check file size (should be > 0)
        if os.path.getsize(filepath) == 0:
            flashing_tool_logger.error(f"Firmware file is empty: {filepath}")
            return False
        
        return True
        
    except Exception as e:
        flashing_tool_logger.error(f"Error validating firmware file {filepath}: {e}")
        return False


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging and logging
    
    Returns:
        Dictionary containing system information
    """
    try:
        info = {
            'platform': sys.platform,
            'machine': platform.machine(),
            'cpu_type': CPU_TYPES.get(platform.machine(), platform.machine()),
            'python_version': sys.version,
            'environment': get_environment(),
            'bundled': hasattr(sys, '_MEIPASS'),
        }
        
        # Add platform-specific information
        if sys.platform == 'darwin':
            info['macos_version'] = platform.mac_ver()[0]
        elif sys.platform == 'win32':
            info['windows_version'] = platform.win32_ver()[0]
        elif sys.platform == 'linux':
            info['linux_distribution'] = platform.linux_distribution()
        
        return info
        
    except Exception as e:
        flashing_tool_logger.error(f"Error getting system info: {e}")
        return {'error': str(e)}


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def parse_version_string(version: str) -> Tuple[int, ...]:
    """
    Parse version string into tuple of integers for comparison
    
    Args:
        version: Version string (e.g., "1.2.3")
        
    Returns:
        Tuple of version components as integers
    """
    if not version:
        return (0,)
    
    try:
        # Remove 'v' prefix if present
        clean_version = version.lstrip('v')
        
        # Split on dots and convert to integers
        parts = []
        for part in clean_version.split('.'):
            # Extract numeric part (ignore non-numeric suffixes)
            numeric_part = re.match(r'(\d+)', part)
            if numeric_part:
                parts.append(int(numeric_part.group(1)))
            else:
                parts.append(0)
        
        return tuple(parts)
        
    except Exception as e:
        flashing_tool_logger.warning(f"Error parsing version '{version}': {e}")
        return (0,)


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    v1_parts = parse_version_string(version1)
    v2_parts = parse_version_string(version2)
    
    # Pad shorter version with zeros
    max_len = max(len(v1_parts), len(v2_parts))
    v1_padded = v1_parts + (0,) * (max_len - len(v1_parts))
    v2_padded = v2_parts + (0,) * (max_len - len(v2_parts))
    
    if v1_padded < v2_padded:
        return -1
    elif v1_padded > v2_padded:
        return 1
    else:
        return 0


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe filesystem usage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed"
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    return sanitized


def create_backup_filename(original_path: str) -> str:
    """
    Create backup filename for a given file path
    
    Args:
        original_path: Original file path
        
    Returns:
        Backup filename
    """
    if not original_path:
        return "backup"
    
    base, ext = os.path.splitext(original_path)
    timestamp = int(time.time())
    
    return f"{base}_backup_{timestamp}{ext}"


def get_config_value(key: str, section: str = 'DEFAULT', fallback: Any = None) -> Any:
    """
    Get configuration value with enhanced error handling
    
    Args:
        key: Configuration key
        section: Configuration section
        fallback: Fallback value if key not found
        
    Returns:
        Configuration value or fallback
    """
    if _config is None:
        return fallback
    
    try:
        return _config.get(key, section, str(fallback) if fallback is not None else '')
    except Exception as e:
        flashing_tool_logger.warning(f"Error getting config value {key}: {e}")
        return fallback


def is_feature_enabled(feature: str) -> bool:
    """
    Check if a feature is enabled in configuration
    
    Args:
        feature: Feature name or MRUpdaterFeature enum value
        
    Returns:
        True if feature is enabled
    """
    if _config is None:
        return False
    
    try:
        if hasattr(MRUpdaterFeature, feature):
            feature_enum = getattr(MRUpdaterFeature, feature)
            return _config.is_feature_enabled(feature_enum)
        else:
            # Direct feature string check
            return _config.get_bool(f'feature_{feature}', fallback=False)
    except Exception as e:
        flashing_tool_logger.warning(f"Error checking feature {feature}: {e}")
        return False


def get_enhanced_mode() -> bool:
    """
    Check if enhanced mode is enabled
    
    Returns:
        True if enhanced mode is enabled
    """
    if _config is None:
        return False
    
    return _config.get_bool('enhanced_mode', fallback=False)


def get_connection_timeout() -> int:
    """
    Get connection timeout from configuration
    
    Returns:
        Connection timeout in seconds
    """
    if _config is None:
        return 30
    
    return _config.get_int('connection_timeout', fallback=30)


def get_retry_attempts() -> int:
    """
    Get retry attempts from configuration
    
    Returns:
        Number of retry attempts
    """
    if _config is None:
        return 3
    
    return _config.get_int('retry_attempts', fallback=3)


def should_backup_saves() -> bool:
    """
    Check if save data should be backed up
    
    Returns:
        True if save backups are enabled
    """
    if _config is None:
        return True
    
    return _config.get_bool('backup_saves', fallback=True)


def get_log_level() -> str:
    """
    Get logging level from configuration
    
    Returns:
        Log level string
    """
    if _config is None:
        return 'INFO'
    
    return _config.get('log_level', fallback='INFO')


def validate_and_sanitize_path(path: str, must_exist: bool = False) -> Optional[str]:
    """
    Validate and sanitize a file path
    
    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        
    Returns:
        Sanitized path or None if invalid
    """
    if not path:
        return None
    
    try:
        # Resolve and normalize path
        normalized_path = os.path.normpath(os.path.expanduser(path))
        
        # Check if path must exist
        if must_exist and not os.path.exists(normalized_path):
            flashing_tool_logger.error(f"Path does not exist: {normalized_path}")
            return None
        
        # Basic security check - prevent path traversal
        if '..' in normalized_path:
            flashing_tool_logger.warning(f"Potentially unsafe path: {normalized_path}")
        
        return normalized_path
        
    except Exception as e:
        flashing_tool_logger.error(f"Error validating path {path}: {e}")
        return None


def ensure_directory_exists(directory: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        directory: Directory path
        
    Returns:
        True if directory exists or was created successfully
    """
    if not directory:
        return False
    
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        flashing_tool_logger.error(f"Error creating directory {directory}: {e}")
        return False


def get_app_data_directory() -> str:
    """
    Get application data directory
    
    Returns:
        Application data directory path
    """
    if _config is None:
        # Fallback directory calculation
        if os.name == 'nt':
            return os.path.join(os.environ.get('APPDATA', ''), 'MRUpdater')
        else:
            return os.path.join(os.path.expanduser('~'), '.mrupdater')
    
    return _config.get_config_info()['app_data_dir']


# Backward compatibility aliases
def get_cpu_type() -> str:
    """Get CPU type (backward compatibility)"""
    return CPU_TYPES.get(platform.machine(), platform.machine())


def is_bundled() -> bool:
    """Check if running as bundled application (backward compatibility)"""
    return hasattr(sys, '_MEIPASS')


__all__ = [
    'FlashOperation',
    'S3FirmwareInfo',
    'ChromaticFirmwarePackage', 
    'CartClinicFirmwarePackage',
    'MRUpdaterManifestData',
    'resolve_path',
    'split_version_string',
    'is_env_manufacturing',
    'is_env_dev',
    'is_env_production',
    'get_environment',
    'get_openfpga_loader_bin_path',
    'validate_firmware_file',
    'get_system_info',
    'format_file_size',
    'parse_version_string',
    'compare_versions',
    'sanitize_filename',
    'create_backup_filename',
    'get_cpu_type',
    'is_bundled',
    'get_config_value',
    'is_feature_enabled',
    'get_enhanced_mode',
    'get_connection_timeout',
    'get_retry_attempts',
    'should_backup_saves',
    'get_log_level',
    'validate_and_sanitize_path',
    'ensure_directory_exists',
    'get_app_data_directory',
]