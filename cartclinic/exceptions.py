"""
Enhanced exception classes for Cart Clinic operations.

This module provides comprehensive exception handling for Cart Clinic
operations with enhanced error context and recovery suggestions.
"""

from typing import Optional, List, Dict, Any
from enum import Enum


class CartClinicErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CartClinicBaseException(Exception):
    """
    Base exception class for Cart Clinic operations.
    
    Provides enhanced error context and recovery suggestions.
    """
    
    def __init__(self, message: str, 
                 error_code: Optional[str] = None,
                 severity: CartClinicErrorSeverity = CartClinicErrorSeverity.MEDIUM,
                 recovery_suggestions: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None,
                 original_exception: Optional[Exception] = None):
        """
        Initialize Cart Clinic exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            severity: Error severity level
            recovery_suggestions: List of suggested recovery actions
            context: Additional error context
            original_exception: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.recovery_suggestions = recovery_suggestions or []
        self.context = context or {}
        self.original_exception = original_exception
    
    def get_full_error_info(self) -> Dict[str, Any]:
        """Get comprehensive error information."""
        return {
            'message': self.message,
            'error_code': self.error_code,
            'severity': self.severity.value,
            'recovery_suggestions': self.recovery_suggestions,
            'context': self.context,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }
    
    def __str__(self) -> str:
        """String representation with enhanced context."""
        result = f"{self.error_code}: {self.message}"
        if self.severity != CartClinicErrorSeverity.MEDIUM:
            result += f" (Severity: {self.severity.value})"
        return result


class CartridgeError(CartClinicBaseException):
    """Errors related to cartridge operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="CARTRIDGE_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            **kwargs
        )


class CommunicationError(CartClinicBaseException):
    """Errors related to device communication."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="COMMUNICATION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check device connection",
                "Try a different USB port",
                "Restart the device"
            ]),
            **kwargs
        )


class FirmwareError(CartClinicBaseException):
    """Errors related to firmware operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="FIRMWARE_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.CRITICAL),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Ensure firmware file is valid",
                "Check device compatibility",
                "Try redownloading firmware"
            ]),
            **kwargs
        )


class SessionError(CartClinicBaseException):
    """Errors related to Cart Clinic sessions."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="SESSION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Restart the Cart Clinic operation",
                "Check device connection",
                "Try reinitializing the session"
            ]),
            **kwargs
        )


class ServerError(CartClinicBaseException):
    """Errors related to server communication."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="SERVER_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check internet connection",
                "Try again later",
                "Contact support if problem persists"
            ]),
            **kwargs
        )


class GameRecognitionError(CartClinicBaseException):
    """Errors related to game recognition."""
    
    def __init__(self, message: str = "Game not recognized", **kwargs):
        super().__init__(
            message,
            error_code="GAME_NOT_RECOGNIZED",
            severity=kwargs.get('severity', CartClinicErrorSeverity.LOW),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Ensure cartridge is properly inserted",
                "Clean cartridge contacts",
                "Check if game is supported"
            ]),
            **kwargs
        )


class SaveOperationError(CartClinicBaseException):
    """Errors related to save data operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="SAVE_OPERATION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Ensure cartridge has save data support",
                "Check file permissions",
                "Try a different save location"
            ]),
            **kwargs
        )


class ValidationError(CartClinicBaseException):
    """Errors related to data validation."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            **kwargs
        )


class TimeoutError(CartClinicBaseException):
    """Errors related to operation timeouts."""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, **kwargs):
        context = kwargs.get('context', {})
        if timeout_duration:
            context['timeout_duration'] = timeout_duration
        
        super().__init__(
            message,
            error_code="TIMEOUT_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Try the operation again",
                "Check device connection",
                "Ensure device is not busy"
            ]),
            context=context,
            **kwargs
        )


class PermissionError(CartClinicBaseException):
    """Errors related to file or device permissions."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="PERMISSION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check file permissions",
                "Run as administrator if needed",
                "Ensure device is not in use by another application"
            ]),
            **kwargs
        )


class ConfigurationError(CartClinicBaseException):
    """Errors related to configuration issues."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check configuration settings",
                "Reset to default configuration",
                "Reinstall the application"
            ]),
            **kwargs
        )


# Enhanced exceptions from decompiled codebase integration
class InvalidCartridgeError(CartClinicBaseException):
    """Exception raised when the cartridge is not recognized as one used by ModRetro."""
    
    def __init__(self, **kwargs):
        super().__init__(
            message="MODRETRO CARTRIDGE NOT DETECTED\nPLEASE REINSERT THE CARTRIDGE",
            error_code="INVALID_CARTRIDGE",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Reinsert the cartridge firmly",
                "Clean cartridge contacts",
                "Check cartridge compatibility",
                "Try a different cartridge"
            ]),
            **kwargs
        )


class CartridgeUnpluggedError(CartClinicBaseException):
    """Exception raised when the cartridge is unplugged during a check or update."""
    
    def __init__(self, **kwargs):
        super().__init__(
            message="LOST CONNECTION TO THE CARTRIDGE\nPLEASE REINSERT THE CARTRIDGE",
            error_code="CARTRIDGE_UNPLUGGED",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Reinsert the cartridge",
                "Ensure cartridge is fully seated",
                "Check for loose connections",
                "Restart the operation"
            ]),
            **kwargs
        )


class CartridgeWriteError(CartClinicBaseException):
    """Exception raised when there is an error writing to the cartridge."""
    
    def __init__(self, message: str = "Error writing to cartridge", **kwargs):
        super().__init__(
            message=message,
            error_code="CARTRIDGE_WRITE_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.CRITICAL),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check cartridge write protection",
                "Verify cartridge is compatible",
                "Try erasing before writing",
                "Check power supply stability"
            ]),
            **kwargs
        )


class CartridgeTooSmallError(CartClinicBaseException):
    """Exception raised when the cartridge is too small for the provided ROM."""
    
    def __init__(self, game_banks: Optional[int] = None, cart_banks: Optional[int] = None, **kwargs):
        if game_banks and cart_banks:
            message = f"CARTRIDGE TOO SMALL FOR GAME ROM\nGame requires {game_banks} banks, cartridge has {cart_banks} banks"
        else:
            message = "CARTRIDGE TOO SMALL FOR GAME ROM"
        
        context = kwargs.get('context', {})
        if game_banks:
            context['game_banks'] = game_banks
        if cart_banks:
            context['cart_banks'] = cart_banks
        
        super().__init__(
            message=message,
            error_code="CARTRIDGE_TOO_SMALL",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Use a larger capacity cartridge",
                "Check ROM file size",
                "Verify cartridge specifications",
                "Try a different ROM file"
            ]),
            context=context,
            **kwargs
        )
        
        self.game_banks = game_banks
        self.cart_banks = cart_banks


class SaveWriteFailureError(CartClinicBaseException):
    """Exception raised when there is a failure writing save data to the cartridge."""
    
    def __init__(self, message: str = "Failed to write save data to cartridge", **kwargs):
        super().__init__(
            message=message,
            error_code="SAVE_WRITE_FAILURE",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check cartridge has save data support",
                "Verify save data format",
                "Try enabling RAM before writing",
                "Check for cartridge damage"
            ]),
            **kwargs
        )


# Communication-specific exceptions (enhanced from libpyretro)
class BankSwitchTimeOut(CartClinicBaseException):
    """Raised when a bank switch operation times out."""
    
    def __init__(self, bank_index: Optional[int] = None, timeout_seconds: Optional[float] = None, **kwargs):
        if bank_index is not None:
            message = f"Bank switch to bank {bank_index} timed out"
            if timeout_seconds:
                message += f" after {timeout_seconds} seconds"
        else:
            message = "Bank switch operation timed out"
        
        context = kwargs.get('context', {})
        if bank_index is not None:
            context['bank_index'] = bank_index
        if timeout_seconds is not None:
            context['timeout_seconds'] = timeout_seconds
        
        super().__init__(
            message=message,
            error_code="BANK_SWITCH_TIMEOUT",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check device connection",
                "Verify cartridge is properly inserted",
                "Try reducing communication speed",
                "Restart the device"
            ]),
            context=context,
            **kwargs
        )
        
        self.bank_index = bank_index
        self.timeout_seconds = timeout_seconds


class InvalidWriteBankSize(CartClinicBaseException):
    """Raised when attempting to write data of incorrect size to a bank."""
    
    def __init__(self, actual_size: int, expected_size: int = 16384, **kwargs):
        message = f"Invalid bank write size: {actual_size} bytes (expected {expected_size} bytes)"
        
        context = kwargs.get('context', {})
        context.update({
            'actual_size': actual_size,
            'expected_size': expected_size
        })
        
        super().__init__(
            message=message,
            error_code="INVALID_WRITE_BANK_SIZE",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                f"Ensure data is exactly {expected_size} bytes",
                "Check data preparation logic",
                "Verify bank size constants"
            ]),
            context=context,
            **kwargs
        )
        
        self.actual_size = actual_size
        self.expected_size = expected_size


class WriteBlockAddressError(CartClinicBaseException):
    """Raised when a write operation returns an unexpected address."""
    
    def __init__(self, expected_address: int, actual_address: int, **kwargs):
        message = f"Write address mismatch: expected 0x{expected_address:04x}, got 0x{actual_address:04x}"
        
        context = kwargs.get('context', {})
        context.update({
            'expected_address': expected_address,
            'actual_address': actual_address
        })
        
        super().__init__(
            message=message,
            error_code="WRITE_BLOCK_ADDRESS_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check address calculation logic",
                "Verify bank switching is working correctly",
                "Check for communication errors"
            ]),
            context=context,
            **kwargs
        )
        
        self.expected_address = expected_address
        self.actual_address = actual_address


class WriteBlockDataError(CartClinicBaseException):
    """Raised when a write operation doesn't write the expected data."""
    
    def __init__(self, address: int, expected_data: int, actual_data: int, **kwargs):
        message = f"Write data mismatch at 0x{address:04x}: expected 0x{expected_data:02x}, got 0x{actual_data:02x}"
        
        context = kwargs.get('context', {})
        context.update({
            'address': address,
            'expected_data': expected_data,
            'actual_data': actual_data
        })
        
        super().__init__(
            message=message,
            error_code="WRITE_BLOCK_DATA_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check data integrity before writing",
                "Verify flash programming is working correctly",
                "Check for communication errors",
                "Try erasing the sector before writing"
            ]),
            context=context,
            **kwargs
        )
        
        self.address = address
        self.expected_data = expected_data
        self.actual_data = actual_data


class ComparisonError(CartClinicBaseException):
    """Raised when data comparison operations fail."""
    
    def __init__(self, comparison_context: str, expected_value=None, actual_value=None, **kwargs):
        if expected_value is not None and actual_value is not None:
            message = f"Comparison failed in {comparison_context}: expected {expected_value}, got {actual_value}"
        else:
            message = f"Comparison failed in {comparison_context}"
        
        context = kwargs.get('context', {})
        context.update({
            'comparison_context': comparison_context,
            'expected_value': expected_value,
            'actual_value': actual_value
        })
        
        super().__init__(
            message=message,
            error_code="COMPARISON_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check data integrity",
                "Verify communication is working correctly",
                "Try the operation again"
            ]),
            context=context,
            **kwargs
        )
        
        self.comparison_context = comparison_context
        self.expected_value = expected_value
        self.actual_value = actual_value


class FlashDetectionError(CartClinicBaseException):
    """Raised when flash chip detection fails."""
    
    def __init__(self, flash_data: Optional[bytes] = None, **kwargs):
        message = "Flash chip could not be identified"
        if flash_data:
            flash_hex = ' '.join(f'{b:02x}' for b in flash_data[:8])
            message += f" (flash data: {flash_hex}...)"
        
        context = kwargs.get('context', {})
        if flash_data:
            context['flash_data'] = flash_data.hex() if len(flash_data) <= 32 else flash_data[:32].hex() + "..."
        
        super().__init__(
            message=message,
            error_code="FLASH_DETECTION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check cartridge connection",
                "Verify cartridge is a supported type",
                "Try reinserting the cartridge",
                "Check for damaged cartridge contacts"
            ]),
            context=context,
            **kwargs
        )
        
        self.flash_data = flash_data


class TransportError(CartClinicBaseException):
    """Raised when transport layer operations fail."""
    
    def __init__(self, message: str, transport_context: Optional[str] = None, **kwargs):
        if transport_context:
            full_message = f"Transport error in {transport_context}: {message}"
        else:
            full_message = f"Transport error: {message}"
        
        context = kwargs.get('context', {})
        if transport_context:
            context['transport_context'] = transport_context
        
        super().__init__(
            message=full_message,
            error_code="TRANSPORT_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check device connection",
                "Verify USB/serial port is available",
                "Try reconnecting the device",
                "Check device drivers"
            ]),
            context=context,
            **kwargs
        )
        
        self.transport_context = transport_context


class FramDetectionError(CartClinicBaseException):
    """Raised when FRAM detection operations fail."""
    
    def __init__(self, operation: Optional[str] = None, **kwargs):
        if operation:
            message = f"FRAM detection failed during {operation}"
        else:
            message = "FRAM detection failed"
        
        context = kwargs.get('context', {})
        if operation:
            context['operation'] = operation
        
        super().__init__(
            message=message,
            error_code="FRAM_DETECTION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check cartridge supports FRAM/SRAM",
                "Verify cartridge is properly inserted",
                "Try enabling RAM before detection",
                "Check for cartridge compatibility"
            ]),
            context=context,
            **kwargs
        )
        
        self.operation = operation


class CartridgeReadError(CartClinicBaseException):
    """Raised when cartridge reading operations fail."""
    
    def __init__(self, message: str = "Cartridge read operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="CARTRIDGE_READ_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.HIGH),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check cartridge connection",
                "Verify cartridge is properly inserted",
                "Try cleaning cartridge contacts",
                "Restart the read operation"
            ]),
            **kwargs
        )


class ChecksumValidationError(CartClinicBaseException):
    """Raised when ROM checksum validation fails."""
    
    def __init__(self, message: str = "ROM checksum validation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="CHECKSUM_VALIDATION_ERROR",
            severity=kwargs.get('severity', CartClinicErrorSeverity.MEDIUM),
            recovery_suggestions=kwargs.get('recovery_suggestions', [
                "Check cartridge data integrity",
                "Try reading the cartridge again",
                "Verify cartridge is not damaged",
                "Check for communication errors"
            ]),
            **kwargs
        )


def create_enhanced_exception(original_exception: Exception, 
                            context: Optional[Dict[str, Any]] = None) -> CartClinicBaseException:
    """
    Create an enhanced Cart Clinic exception from a generic exception.
    
    Args:
        original_exception: The original exception
        context: Additional context information
        
    Returns:
        CartClinicBaseException: Enhanced exception with context
    """
    message = str(original_exception)
    exception_type = type(original_exception).__name__
    
    # Map common exception types to Cart Clinic exceptions
    exception_mapping = {
        'ConnectionError': CommunicationError,
        'TimeoutError': TimeoutError,
        'PermissionError': PermissionError,
        'FileNotFoundError': ConfigurationError,
        'ValueError': ValidationError,
        'OSError': CommunicationError,
        'IOError': CommunicationError,
        'SerialException': CommunicationError,
        'USBError': CommunicationError,
        'RuntimeError': CartridgeError,
        'AttributeError': ConfigurationError,
        'ImportError': ConfigurationError,
        'ModuleNotFoundError': ConfigurationError
    }
    
    enhanced_exception_class = exception_mapping.get(exception_type, CartClinicBaseException)
    
    return enhanced_exception_class(
        message=message,
        original_exception=original_exception,
        context=context or {}
    )


def get_exception_hierarchy() -> Dict[str, List[str]]:
    """
    Get the complete exception hierarchy for debugging and documentation.
    
    Returns:
        Dictionary mapping exception categories to their exception classes
    """
    return {
        'base': ['CartClinicBaseException'],
        'cartridge_operations': [
            'CartridgeError',
            'InvalidCartridgeError', 
            'CartridgeUnpluggedError',
            'CartridgeWriteError',
            'CartridgeTooSmallError',
            'FlashDetectionError'
        ],
        'communication': [
            'CommunicationError',
            'TransportError',
            'BankSwitchTimeOut'
        ],
        'data_operations': [
            'WriteBlockAddressError',
            'WriteBlockDataError',
            'ComparisonError',
            'InvalidWriteBankSize'
        ],
        'save_operations': [
            'SaveOperationError',
            'SaveWriteFailureError',
            'FramDetectionError'
        ],
        'system': [
            'FirmwareError',
            'SessionError',
            'ServerError',
            'ValidationError',
            'TimeoutError',
            'PermissionError',
            'ConfigurationError'
        ],
        'recognition': [
            'GameRecognitionError'
        ]
    }


def is_recoverable_error(exception: Exception) -> bool:
    """
    Determine if an error is potentially recoverable.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if the error might be recoverable with user action
    """
    recoverable_types = {
        InvalidCartridgeError,
        CartridgeUnpluggedError,
        CommunicationError,
        TransportError,
        BankSwitchTimeOut,
        TimeoutError,
        GameRecognitionError,
        ConfigurationError
    }
    
    return type(exception) in recoverable_types or (
        isinstance(exception, CartClinicBaseException) and 
        exception.severity in [CartClinicErrorSeverity.LOW, CartClinicErrorSeverity.MEDIUM]
    )


def get_recovery_suggestions(exception: Exception) -> List[str]:
    """
    Get recovery suggestions for an exception.
    
    Args:
        exception: Exception to get suggestions for
        
    Returns:
        List of recovery suggestions
    """
    if isinstance(exception, CartClinicBaseException):
        return exception.recovery_suggestions
    
    # Create enhanced exception to get suggestions
    enhanced = create_enhanced_exception(exception)
    return enhanced.recovery_suggestions


def handle_exception_with_recovery(func):
    """
    Decorator to handle exceptions with automatic recovery suggestions.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with enhanced exception handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CartClinicBaseException:
            # Re-raise Cart Clinic exceptions as-is
            raise
        except Exception as e:
            # Convert generic exceptions to enhanced ones
            context = {
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            }
            enhanced_exception = create_enhanced_exception(e, context)
            raise enhanced_exception from e
    
    return wrapper