# MRUpdater Enhanced API Documentation

## Overview

This document provides comprehensive API documentation for the enhanced MRUpdater system. The enhanced APIs maintain full backward compatibility while providing access to new features and improved functionality.

## API Versioning

### Version Management

```python
from compatibility_layer import APIVersion

# Check current API version
current_version = APIVersion.get_current_version()
print(f"Current API version: {current_version}")

# Set API version programmatically
APIVersion.set_version(APIVersion.V2_ENHANCED)

# Check if enhanced mode is enabled
if APIVersion.is_enhanced_mode():
    print("Enhanced features available")
```

### Available Versions

- **V1_ORIGINAL (1.0)**: Original MRUpdater_Source behavior
- **V2_ENHANCED (2.0)**: Integrated with decompiled enhancements

## Core APIs

### Configuration Management

#### EnhancedConfigParser

```python
from config import EnhancedConfigParser, MRUpdaterFeature

# Create configuration instance
config = EnhancedConfigParser()

# Load configuration
config_data = config.load()

# Type-safe access methods
enhanced_mode = config.get_bool('enhanced_mode')
connection_timeout = config.get_int('connection_timeout')
log_level = config.get('log_level')

# Feature management
is_enabled = config.is_feature_enabled(MRUpdaterFeature.FRAM_SUPPORT)
config.enable_feature(MRUpdaterFeature.ENHANCED_DETECTION, True)

# Save configuration
config.save()
```

#### Configuration Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `load()` | Load configuration from file | None | `Dict[str, Any]` |
| `get(option, section, fallback)` | Get string value | `str, str, str` | `str` |
| `get_bool(option, section, fallback)` | Get boolean value | `str, str, bool` | `bool` |
| `get_int(option, section, fallback)` | Get integer value | `str, str, int` | `int` |
| `get_float(option, section, fallback)` | Get float value | `str, str, float` | `float` |
| `set(option, value, section)` | Set configuration value | `str, Any, str` | `None` |
| `save()` | Save configuration to file | None | `None` |
| `is_feature_enabled(feature)` | Check if feature is enabled | `MRUpdaterFeature` | `bool` |
| `enable_feature(feature, enabled)` | Enable/disable feature | `MRUpdaterFeature, bool` | `None` |

### Error Handling

#### UnifiedErrorHandler

```python
from error_handler import (
    UnifiedErrorHandler, 
    ErrorHandlingStrategy,
    get_error_handler,
    handle_error
)

# Get global error handler
handler = get_error_handler()

# Register error callback
def my_error_callback(exception, context):
    print(f"Error occurred: {exception}")

handler.register_error_callback('all', my_error_callback)

# Register recovery strategy
def connection_recovery(exception, context):
    # Attempt to recover from connection error
    return True

handler.register_recovery_strategy(ConnectionError, connection_recovery)

# Handle error with specific strategy
try:
    # Some operation that might fail
    pass
except Exception as e:
    handle_error(e, strategy=ErrorHandlingStrategy.ATTEMPT_RECOVERY)
```

#### Error Handling Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `handle_error(exception, context, strategy, user_message)` | Handle error with strategy | `Exception, Dict, ErrorHandlingStrategy, str` | `bool` |
| `register_error_callback(error_type, callback)` | Register error callback | `str, Callable` | `None` |
| `register_recovery_strategy(exception_type, strategy)` | Register recovery strategy | `type, Callable` | `None` |
| `get_error_statistics()` | Get error statistics | None | `Dict[str, Any]` |
| `reset_statistics()` | Reset error statistics | None | `None` |

#### Error Handling Decorators

```python
from error_handler import (
    with_error_handling,
    log_and_suppress_errors,
    notify_user_on_error,
    attempt_recovery_on_error
)

# Custom error handling
@with_error_handling(ErrorHandlingStrategy.NOTIFY_USER)
def risky_operation():
    # Operation that might fail
    pass

# Predefined decorators
@log_and_suppress_errors
def background_task():
    # Task that should not interrupt user
    pass

@notify_user_on_error
def user_initiated_action():
    # Action that user should know about if it fails
    pass

@attempt_recovery_on_error
def recoverable_operation():
    # Operation that can be automatically recovered
    pass
```

### Cartridge Operations

#### Enhanced Cartridge Reading

```python
from cartclinic.cartridge_read import read_cartridge_helper
from compatibility_layer import CartridgeReadCompatibility

# Original API (backward compatible)
cart_data = CartridgeReadCompatibility.read_cartridge_helper(
    session=session,
    emit_progress=progress_callback
)

# Enhanced API with new features
cart_data, save_data = CartridgeReadCompatibility.read_cartridge_helper_enhanced(
    session=session,
    emit_progress=progress_callback,
    include_save_data=True,
    validate_checksum=True,
    progress_callback=detailed_progress_callback
)
```

#### Cartridge Reading Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `read_cartridge_helper()` | Original cartridge reading | `session, animation, detection_thread, emit_progress` | `bytearray` |
| `read_cartridge_helper_enhanced()` | Enhanced cartridge reading | `session, ..., include_save_data, validate_checksum, progress_callback` | `Union[bytearray, Tuple[bytearray, bytearray]]` |

#### Enhanced Cartridge Writing

```python
from cartclinic.cartridge_write import write_cartridge_helper
from compatibility_layer import CartridgeWriteCompatibility

# Original API (backward compatible)
success = CartridgeWriteCompatibility.write_cartridge_helper(
    session=session,
    game_data=rom_data,
    emit_progress=progress_callback
)

# Enhanced API with new features
success = CartridgeWriteCompatibility.write_cartridge_helper_enhanced(
    session=session,
    game_data=rom_data,
    emit_progress=progress_callback,
    verify_writes=True,
    save_data=save_data,
    progress_callback=detailed_progress_callback
)
```

#### Cartridge Writing Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `write_cartridge_helper()` | Original cartridge writing | `session, game_data, game_save_settings, animation_thread, detection_thread, emit_progress` | `bool` |
| `write_cartridge_helper_enhanced()` | Enhanced cartridge writing | `session, ..., verify_writes, save_data, progress_callback` | `bool` |

### Device Management

#### Enhanced Chromatic Device Management

```python
from flashing_tool.chromatic import Chromatic, ChromaticBase, ChromaticError
from compatibility_layer import ChromaticCompatibility

# Create Chromatic instance with compatibility
chromatic = ChromaticCompatibility.create_chromatic(
    openfpga_loader_bin="/path/to/loader",
    progress_callback=progress_callback,
    enhanced_detection=True
)

# Enhanced device operations
try:
    # Enhanced device state detection
    state = chromatic.detect_device_state()
    
    # Enhanced firmware flashing
    chromatic.flash_both_start(mcu_file, fpga_file)
    
except ChromaticError as e:
    print(f"Device error: {e}")
    print(f"Recovery suggestions: {e.recovery_suggestions}")
```

#### Chromatic Device Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `is_fpga_detected()` | Check if FPGA is detected | None | `bool` |
| `detect_device_state()` | Get current device state | None | `str` |
| `flash_both_start(mcu_file, fpga_file)` | Start firmware flashing | `str, str` | `None` |
| `get_esp(force_connect)` | Get ESP loader instance | `bool` | `Optional[ESPLoader]` |
| `set_fw_version(version)` | Set firmware version | `str` | `None` |
| `update_status()` | Update device status | None | `None` |
| `dispose()` | Clean up resources | None | `None` |

### Session Management

#### Enhanced Session Management

```python
from libpyretro.cartclinic.comms.session import Session
from compatibility_layer import SessionCompatibility

# Create session with compatibility
session = SessionCompatibility.create_session(tporter=transport)

# Enhanced session operations
if session:
    # Enhanced flash type detection
    flash_info = session.get_flash_type()
    
    # Enhanced bank reading with retry logic
    bank_data = session.read_bank(bank_number)
    
    # FRAM detection (enhanced feature)
    if hasattr(session, 'detect_fram'):
        fram_detected = session.detect_fram()
```

#### Session Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `get_flash_type()` | Get flash type information | None | `FlashInfo` |
| `read_bank(bank)` | Read bank data | `int` | `bytes` |
| `write_bank(bank, data)` | Write bank data | `int, bytes` | `None` |
| `detect_fram()` | Detect FRAM cartridge | None | `bool` |

### GUI Components

#### Enhanced Cart Clinic GUI

```python
from cartclinic.gui import EnhancedCartClinic

# Create enhanced Cart Clinic instance
cart_clinic = EnhancedCartClinic(
    main_gui=main_window,
    chromatic=chromatic_device,
    form=ui_form
)

# Enhanced operations
cart_clinic.start_cart_clinic_check(include_progress_callback=True)
cart_clinic.cart_clinic_homebrew()

# State management
state = cart_clinic.get_state()
is_active = cart_clinic.is_operation_active()

# Error context for debugging
error_context = cart_clinic.get_enhanced_error_context()
```

#### Cart Clinic GUI Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `start_cart_clinic_check(include_progress_callback)` | Start Cart Clinic check | `bool` | `bool` |
| `cart_clinic_homebrew()` | Start homebrew operation | None | `None` |
| `get_state()` | Get current state | None | `CartClinicState` |
| `is_operation_active()` | Check if operation is active | None | `bool` |
| `cancel_current_operation()` | Cancel current operation | None | `None` |
| `get_enhanced_error_context()` | Get error context | None | `Dict[str, Any]` |

### Compatibility Layer

#### Backward Compatibility Management

```python
from compatibility_layer import (
    APIVersion,
    CompatibilityConfig,
    compatibility_config,
    enable_enhanced_mode,
    enable_compatibility_mode,
    get_compatibility_status
)

# Enable enhanced mode
enable_enhanced_mode()

# Configure compatibility options
compatibility_config.enable_enhanced_features(True)
compatibility_config.enable_strict_compatibility(False)

# Get compatibility status
status = get_compatibility_status()
print(f"Enhanced mode: {status['enhanced_mode']}")
```

#### Compatibility Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `enable_enhanced_mode()` | Enable enhanced mode | None | `None` |
| `enable_compatibility_mode()` | Enable compatibility mode | None | `None` |
| `get_compatibility_status()` | Get compatibility status | None | `Dict[str, Any]` |

#### Data Format Compatibility

```python
from compatibility_layer import DataFormatCompatibility

# Convert between data formats
enhanced_info = DataFormatCompatibility.convert_cartridge_info(
    original_info, 
    target_format='enhanced'
)

# Migrate configuration files
success = DataFormatCompatibility.migrate_config_file(
    'config.ini', 
    backup=True
)
```

#### Compatibility Validation

```python
from compatibility_layer import CompatibilityValidator

validator = CompatibilityValidator()

# Validate API compatibility
api_results = validator.validate_api_compatibility()

# Validate data format compatibility
data_results = validator.validate_data_format_compatibility()

# Generate comprehensive report
report = validator.generate_compatibility_report()
print(report)
```

## Data Structures

### Enhanced Data Classes

#### WindowState

```python
from main import WindowState

state = WindowState(
    is_visible=True,
    is_minimized=False,
    is_maximized=False,
    is_fullscreen=False,
    position=(100, 100),
    size=(800, 600),
    is_responsive=True,
    last_response_time=time.time()
)
```

#### ApplicationState

```python
from main import ApplicationState

app_state = ApplicationState(
    is_initialized=True,
    is_shutting_down=False,
    current_tab='system',
    active_operations=['firmware_flash'],
    error_count=0,
    last_error_time=0.0
)
```

#### CartClinicState

```python
from cartclinic.gui import CartClinicState

cc_state = CartClinicState(
    current_operation='checking',
    progress=50,
    error_message=None,
    secondary_error=None,
    session_active=True,
    device_connected=True
)
```

#### ProgressInfo

```python
from cartclinic.gui import ProgressInfo

progress = ProgressInfo(
    current=50,
    total=100,
    message="Processing...",
    detailed_status="Nearly complete...",
    estimated_time_remaining=30.5
)

print(f"Progress: {progress.percentage}%")
```

### Exception Classes

#### ChromaticError

```python
from flashing_tool.chromatic import ChromaticError

try:
    # Device operation
    pass
except ChromaticError as e:
    print(f"Error: {e}")
    print(f"Original exception: {e.original_exception}")
    print(f"Context: {e.context}")
    print(f"Recovery suggestions: {e.recovery_suggestions}")
```

#### CartClinicBaseException

```python
from cartclinic.exceptions import CartClinicBaseException, CartClinicErrorSeverity

try:
    # Cart Clinic operation
    pass
except CartClinicBaseException as e:
    print(f"Error: {e}")
    print(f"Severity: {e.severity}")
    print(f"Recovery suggestions: {e.recovery_suggestions}")
```

## Usage Examples

### Complete Firmware Update Example

```python
from compatibility_layer import ChromaticCompatibility
from error_handler import handle_error, ErrorHandlingStrategy
from config import get_config

def update_firmware():
    """Complete firmware update with enhanced error handling."""
    try:
        # Load configuration
        config = get_config()
        
        # Create Chromatic device
        chromatic = ChromaticCompatibility.create_chromatic(
            openfpga_loader_bin=config.get('openfpga_loader_path'),
            progress_callback=update_progress,
            enhanced_detection=True
        )
        
        # Check device state
        state = chromatic.detect_device_state()
        if state != 'ready_to_flash':
            raise Exception(f"Device not ready: {state}")
        
        # Start firmware update
        mcu_file = config.get('mcu_fw_file_path', section='FIRMWARE')
        fpga_file = config.get('fpga_fw_file_path', section='FIRMWARE')
        
        chromatic.flash_both_start(mcu_file, fpga_file)
        
        print("Firmware update completed successfully")
        
    except Exception as e:
        # Handle error with automatic recovery attempt
        success = handle_error(
            e, 
            context={'operation': 'firmware_update'},
            strategy=ErrorHandlingStrategy.ATTEMPT_RECOVERY
        )
        
        if not success:
            print(f"Firmware update failed: {e}")

def update_progress(message):
    """Progress callback for firmware update."""
    print(f"Progress: {message}")

# Run firmware update
update_firmware()
```

### Complete Cart Clinic Example

```python
from cartclinic.gui import EnhancedCartClinic
from compatibility_layer import SessionCompatibility
from error_handler import handle_error

def cart_clinic_operation():
    """Complete Cart Clinic operation with enhanced features."""
    try:
        # Create enhanced Cart Clinic
        cart_clinic = EnhancedCartClinic(
            main_gui=main_window,
            chromatic=chromatic_device
        )
        
        # Set configuration
        cart_clinic.set_mrpatcher_endpoint("https://api.example.com")
        cart_clinic.set_cart_clinic_firmware_path("/path/to/firmware")
        
        # Start Cart Clinic check
        success = cart_clinic.start_cart_clinic_check(
            include_progress_callback=True
        )
        
        if success:
            print("Cart Clinic check started successfully")
            
            # Monitor operation
            while cart_clinic.is_operation_active():
                state = cart_clinic.get_state()
                print(f"Progress: {state.progress}%")
                time.sleep(1)
            
            print("Cart Clinic operation completed")
        else:
            print("Failed to start Cart Clinic check")
            
    except Exception as e:
        # Get enhanced error context
        context = cart_clinic.get_enhanced_error_context()
        
        handle_error(
            e,
            context=context,
            strategy=ErrorHandlingStrategy.NOTIFY_USER
        )

# Run Cart Clinic operation
cart_clinic_operation()
```

### Configuration Management Example

```python
from config import get_config, MRUpdaterFeature

def configure_enhanced_features():
    """Configure enhanced features based on user preferences."""
    config = get_config()
    
    # Enable enhanced features
    config.set('enhanced_mode', True)
    config.set('enhanced_error_handling', True)
    config.set('enhanced_progress_reporting', True)
    
    # Configure specific features
    config.enable_feature(MRUpdaterFeature.FRAM_SUPPORT, True)
    config.enable_feature(MRUpdaterFeature.ENHANCED_DETECTION, True)
    
    # Configure GUI enhancements
    config.set('enable_animations', True, 'GUI')
    config.set('remember_window_size', True, 'GUI')
    
    # Configure cartridge enhancements
    config.set('verify_checksums', True, 'CARTRIDGE')
    config.set('backup_before_write', True, 'CARTRIDGE')
    
    # Save configuration
    config.save()
    
    print("Enhanced features configured successfully")

# Configure enhanced features
configure_enhanced_features()
```

## Migration from Original API

### API Mapping

| Original API | Enhanced API | Notes |
|-------------|-------------|-------|
| `cartridge_read.read_cartridge_helper()` | `CartridgeReadCompatibility.read_cartridge_helper_enhanced()` | Backward compatible with new features |
| `cartridge_write.write_cartridge_helper()` | `CartridgeWriteCompatibility.write_cartridge_helper_enhanced()` | Enhanced with verification |
| `chromatic.Chromatic()` | `ChromaticCompatibility.create_chromatic()` | Enhanced with better error handling |
| `config.load_config()` | `get_config().load()` | Enhanced with type safety |

### Migration Steps

1. **Update imports** to use compatibility layer
2. **Add error handling** using enhanced error handler
3. **Enable enhanced features** through configuration
4. **Test compatibility** using validation tools
5. **Gradually adopt** new enhanced APIs

## Best Practices

### Error Handling

```python
# Use enhanced error handling for better user experience
from error_handler import handle_error, ErrorHandlingStrategy

try:
    # Your operation
    pass
except Exception as e:
    handle_error(e, strategy=ErrorHandlingStrategy.ATTEMPT_RECOVERY)
```

### Configuration Management

```python
# Use type-safe configuration access
config = get_config()
timeout = config.get_int('connection_timeout', fallback=30)
enhanced_mode = config.get_bool('enhanced_mode', fallback=True)
```

### Progress Reporting

```python
# Use enhanced progress reporting for better user feedback
from cartclinic.gui import EnhancedProgressReporter

reporter = EnhancedProgressReporter()
reporter.start_operation("Firmware Update")
reporter.update_progress(50, 100, "Flashing FPGA...")
```

### Compatibility

```python
# Check compatibility before using enhanced features
from compatibility_layer import APIVersion

if APIVersion.is_enhanced_mode():
    # Use enhanced features
    pass
else:
    # Use original features
    pass
```

## Support and Resources

### API Reference
- Complete method signatures and parameters
- Return value documentation
- Exception handling information
- Usage examples for each API

### Migration Tools
- Compatibility validation utilities
- Configuration migration scripts
- API mapping documentation
- Testing frameworks

### Community Resources
- GitHub repository with examples
- Community forum for questions
- Documentation wiki
- Developer chat for real-time support

This API documentation provides comprehensive coverage of the enhanced MRUpdater system while maintaining full backward compatibility. The enhanced APIs provide improved functionality, better error handling, and enhanced user experience while preserving all existing capabilities.