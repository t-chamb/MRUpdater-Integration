"""
API Versioning System for MRUpdater Integration

This module provides a comprehensive API versioning system that allows
users to choose between original and enhanced functionality, with
configuration flags to enable/disable specific features.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger('mrupdater.versioning')


@dataclass
class FeatureFlags:
    """Feature flags for controlling enhanced functionality"""
    
    # Core enhanced features
    enhanced_cartridge_reading: bool = True
    enhanced_cartridge_writing: bool = True
    enhanced_device_communication: bool = True
    enhanced_error_handling: bool = True
    enhanced_progress_reporting: bool = True
    
    # Protocol enhancements
    enhanced_flash_detection: bool = True
    enhanced_fram_support: bool = True
    enhanced_session_management: bool = True
    enhanced_retry_logic: bool = True
    
    # GUI enhancements
    enhanced_gui_responsiveness: bool = True
    enhanced_progress_dialogs: bool = True
    enhanced_error_dialogs: bool = True
    
    # Validation and safety features
    enhanced_checksum_validation: bool = True
    enhanced_data_verification: bool = True
    enhanced_save_data_handling: bool = True
    
    # Performance features
    memory_efficient_operations: bool = True
    optimized_bank_reading: bool = True
    parallel_operations: bool = False  # Disabled by default for safety
    
    # Debugging and logging
    verbose_logging: bool = False
    performance_metrics: bool = False
    debug_mode: bool = False
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> 'FeatureFlags':
        """Create from dictionary"""
        return cls(**data)
    
    def enable_all(self):
        """Enable all features"""
        for field in self.__dataclass_fields__:
            setattr(self, field, True)
    
    def disable_all(self):
        """Disable all features"""
        for field in self.__dataclass_fields__:
            setattr(self, field, False)
    
    def enable_safe_features(self):
        """Enable only safe, well-tested features"""
        self.disable_all()
        self.enhanced_error_handling = True
        self.enhanced_progress_reporting = True
        self.enhanced_checksum_validation = True
        self.enhanced_data_verification = True
        self.memory_efficient_operations = True
    
    def enable_performance_features(self):
        """Enable performance-oriented features"""
        self.enable_safe_features()
        self.enhanced_flash_detection = True
        self.enhanced_session_management = True
        self.enhanced_retry_logic = True
        self.optimized_bank_reading = True
    
    def enable_all_enhancements(self):
        """Enable all enhancement features"""
        self.enable_performance_features()
        self.enhanced_cartridge_reading = True
        self.enhanced_cartridge_writing = True
        self.enhanced_device_communication = True
        self.enhanced_fram_support = True
        self.enhanced_gui_responsiveness = True
        self.enhanced_progress_dialogs = True
        self.enhanced_error_dialogs = True
        self.enhanced_save_data_handling = True


@dataclass
class APIConfiguration:
    """Complete API configuration including version and feature flags"""
    
    version: str = "2.0"
    feature_flags: FeatureFlags = None
    compatibility_mode: str = "enhanced"  # "strict", "enhanced", "hybrid"
    auto_fallback: bool = True
    warn_deprecated: bool = True
    migration_enabled: bool = True
    
    def __post_init__(self):
        if self.feature_flags is None:
            self.feature_flags = FeatureFlags()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'version': self.version,
            'feature_flags': self.feature_flags.to_dict(),
            'compatibility_mode': self.compatibility_mode,
            'auto_fallback': self.auto_fallback,
            'warn_deprecated': self.warn_deprecated,
            'migration_enabled': self.migration_enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIConfiguration':
        """Create from dictionary"""
        feature_flags_data = data.get('feature_flags', {})
        feature_flags = FeatureFlags.from_dict(feature_flags_data)
        
        return cls(
            version=data.get('version', '2.0'),
            feature_flags=feature_flags,
            compatibility_mode=data.get('compatibility_mode', 'enhanced'),
            auto_fallback=data.get('auto_fallback', True),
            warn_deprecated=data.get('warn_deprecated', True),
            migration_enabled=data.get('migration_enabled', True)
        )


class APIVersionManager:
    """Manages API versions and feature flags"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize API version manager
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config = APIConfiguration()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Try to use user's home directory first
        home_dir = Path.home()
        config_dir = home_dir / '.mrupdater'
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / 'api_config.json')
    
    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                self._config = APIConfiguration.from_dict(data)
                logger.info(f"Loaded API configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load API configuration: {e}, using defaults")
                self._config = APIConfiguration()
        else:
            logger.info("No API configuration found, using defaults")
            self._save_config()  # Create default config file
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self._config.to_dict(), f, indent=2)
            logger.debug(f"Saved API configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save API configuration: {e}")
    
    @property
    def version(self) -> str:
        """Get current API version"""
        return self._config.version
    
    @property
    def feature_flags(self) -> FeatureFlags:
        """Get current feature flags"""
        return self._config.feature_flags
    
    @property
    def compatibility_mode(self) -> str:
        """Get current compatibility mode"""
        return self._config.compatibility_mode
    
    def set_version(self, version: str):
        """Set API version"""
        if version not in ['1.0', '2.0']:
            raise ValueError(f"Invalid API version: {version}")
        
        self._config.version = version
        
        # Adjust feature flags based on version
        if version == '1.0':
            self._config.feature_flags.disable_all()
            self._config.compatibility_mode = 'strict'
        elif version == '2.0':
            self._config.feature_flags.enable_all_enhancements()
            self._config.compatibility_mode = 'enhanced'
        
        self._save_config()
        logger.info(f"API version set to {version}")
    
    def set_compatibility_mode(self, mode: str):
        """
        Set compatibility mode
        
        Args:
            mode: 'strict' (original only), 'enhanced' (new features), 'hybrid' (mixed)
        """
        if mode not in ['strict', 'enhanced', 'hybrid']:
            raise ValueError(f"Invalid compatibility mode: {mode}")
        
        self._config.compatibility_mode = mode
        
        # Adjust feature flags based on mode
        if mode == 'strict':
            self._config.feature_flags.disable_all()
        elif mode == 'enhanced':
            self._config.feature_flags.enable_all_enhancements()
        elif mode == 'hybrid':
            self._config.feature_flags.enable_safe_features()
        
        self._save_config()
        logger.info(f"Compatibility mode set to {mode}")
    
    def enable_feature(self, feature_name: str, enabled: bool = True):
        """Enable or disable a specific feature"""
        if hasattr(self._config.feature_flags, feature_name):
            setattr(self._config.feature_flags, feature_name, enabled)
            self._save_config()
            logger.info(f"Feature {feature_name} {'enabled' if enabled else 'disabled'}")
        else:
            raise ValueError(f"Unknown feature: {feature_name}")
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return getattr(self._config.feature_flags, feature_name, False)
    
    def get_enabled_features(self) -> List[str]:
        """Get list of enabled features"""
        enabled = []
        for field_name, field in self._config.feature_flags.__dataclass_fields__.items():
            if getattr(self._config.feature_flags, field_name):
                enabled.append(field_name)
        return enabled
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self._config = APIConfiguration()
        self._save_config()
        logger.info("API configuration reset to defaults")
    
    def create_preset(self, name: str, description: str = ""):
        """Create a configuration preset"""
        preset_data = {
            'name': name,
            'description': description,
            'config': self._config.to_dict()
        }
        
        presets_dir = Path(self.config_path).parent / 'presets'
        presets_dir.mkdir(exist_ok=True)
        
        preset_file = presets_dir / f"{name}.json"
        with open(preset_file, 'w') as f:
            json.dump(preset_data, f, indent=2)
        
        logger.info(f"Created preset '{name}' at {preset_file}")
    
    def load_preset(self, name: str):
        """Load a configuration preset"""
        presets_dir = Path(self.config_path).parent / 'presets'
        preset_file = presets_dir / f"{name}.json"
        
        if not preset_file.exists():
            raise FileNotFoundError(f"Preset '{name}' not found")
        
        with open(preset_file, 'r') as f:
            preset_data = json.load(f)
        
        self._config = APIConfiguration.from_dict(preset_data['config'])
        self._save_config()
        logger.info(f"Loaded preset '{name}'")
    
    def list_presets(self) -> List[Dict[str, str]]:
        """List available presets"""
        presets_dir = Path(self.config_path).parent / 'presets'
        if not presets_dir.exists():
            return []
        
        presets = []
        for preset_file in presets_dir.glob('*.json'):
            try:
                with open(preset_file, 'r') as f:
                    preset_data = json.load(f)
                presets.append({
                    'name': preset_data.get('name', preset_file.stem),
                    'description': preset_data.get('description', ''),
                    'file': str(preset_file)
                })
            except Exception as e:
                logger.warning(f"Failed to load preset {preset_file}: {e}")
        
        return presets
    
    def get_status_report(self) -> str:
        """Generate status report"""
        report = []
        report.append("MRUpdater API Configuration Status")
        report.append("=" * 40)
        report.append(f"Version: {self.version}")
        report.append(f"Compatibility Mode: {self.compatibility_mode}")
        report.append(f"Auto Fallback: {self._config.auto_fallback}")
        report.append(f"Warn Deprecated: {self._config.warn_deprecated}")
        report.append(f"Migration Enabled: {self._config.migration_enabled}")
        report.append("")
        
        report.append("Enabled Features:")
        enabled_features = self.get_enabled_features()
        if enabled_features:
            for feature in enabled_features:
                report.append(f"  ✓ {feature}")
        else:
            report.append("  (none)")
        
        report.append("")
        report.append("Disabled Features:")
        all_features = list(self._config.feature_flags.__dataclass_fields__.keys())
        disabled_features = [f for f in all_features if f not in enabled_features]
        if disabled_features:
            for feature in disabled_features:
                report.append(f"  ✗ {feature}")
        else:
            report.append("  (none)")
        
        return "\n".join(report)


# Global API version manager instance
_api_manager = None


def get_api_manager() -> APIVersionManager:
    """Get global API version manager instance"""
    global _api_manager
    if _api_manager is None:
        _api_manager = APIVersionManager()
    return _api_manager


def get_current_version() -> str:
    """Get current API version"""
    return get_api_manager().version


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return get_api_manager().is_feature_enabled(feature_name)


def set_api_version(version: str):
    """Set API version globally"""
    get_api_manager().set_version(version)


def set_compatibility_mode(mode: str):
    """Set compatibility mode globally"""
    get_api_manager().set_compatibility_mode(mode)


def enable_feature(feature_name: str, enabled: bool = True):
    """Enable or disable a feature globally"""
    get_api_manager().enable_feature(feature_name, enabled)


# Convenience functions for common configurations
def enable_original_mode():
    """Enable original API mode (v1.0, strict compatibility)"""
    manager = get_api_manager()
    manager.set_version('1.0')
    manager.set_compatibility_mode('strict')


def enable_enhanced_mode():
    """Enable enhanced API mode (v2.0, all features)"""
    manager = get_api_manager()
    manager.set_version('2.0')
    manager.set_compatibility_mode('enhanced')


def enable_safe_mode():
    """Enable safe mode (v2.0, only safe features)"""
    manager = get_api_manager()
    manager.set_version('2.0')
    manager.set_compatibility_mode('hybrid')


def create_default_presets():
    """Create default configuration presets"""
    manager = get_api_manager()
    
    # Original mode preset
    manager.set_version('1.0')
    manager.set_compatibility_mode('strict')
    manager.create_preset('original', 'Original MRUpdater behavior (v1.0)')
    
    # Safe mode preset
    manager.set_version('2.0')
    manager.set_compatibility_mode('hybrid')
    manager.create_preset('safe', 'Safe enhanced features only')
    
    # Enhanced mode preset
    manager.set_version('2.0')
    manager.set_compatibility_mode('enhanced')
    manager.create_preset('enhanced', 'All enhanced features enabled')
    
    # Performance mode preset
    manager.set_version('2.0')
    manager.feature_flags.enable_performance_features()
    manager.create_preset('performance', 'Performance-optimized configuration')
    
    logger.info("Created default configuration presets")


__all__ = [
    'FeatureFlags',
    'APIConfiguration', 
    'APIVersionManager',
    'get_api_manager',
    'get_current_version',
    'is_feature_enabled',
    'set_api_version',
    'set_compatibility_mode',
    'enable_feature',
    'enable_original_mode',
    'enable_enhanced_mode',
    'enable_safe_mode',
    'create_default_presets'
]