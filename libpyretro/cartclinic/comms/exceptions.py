"""
Communication exceptions for CartClinic operations.

This module defines specialized exceptions for various communication and
cartridge operation errors, providing detailed error context and recovery suggestions.

Note: This module now imports from the unified exception system in cartclinic.exceptions
for consistency and enhanced error handling.
"""

# Import unified exception system
try:
    from cartclinic.exceptions import (
        CartClinicBaseException as CartClinicError,
        BankSwitchTimeOut,
        InvalidWriteBankSize,
        WriteBlockAddressError,
        WriteBlockDataError,
        ComparisonError,
        FlashDetectionError,
        TransportError,
        FramDetectionError
    )
    
    # Re-export for backward compatibility
    __all__ = [
        'CartClinicError',
        'BankSwitchTimeOut',
        'InvalidWriteBankSize', 
        'WriteBlockAddressError',
        'WriteBlockDataError',
        'ComparisonError',
        'FlashDetectionError',
        'TransportError',
        'FramDetectionError'
    ]
    
except ImportError:
    # Fallback definitions if unified system is not available
    class CartClinicError(Exception):
        """Base exception for all CartClinic operations."""
        
        def __init__(self, message: str, recovery_suggestions: list = None):
            super().__init__(message)
            self.recovery_suggestions = recovery_suggestions or []


    # Fallback exception definitions (only used if unified system import fails)
    class BankSwitchTimeOut(CartClinicError):
        """Raised when a bank switch operation times out."""
        
        def __init__(self, bank_index: int = None, timeout_seconds: float = None):
            if bank_index is not None:
                message = f"Bank switch to bank {bank_index} timed out"
                if timeout_seconds:
                    message += f" after {timeout_seconds} seconds"
            else:
                message = "Bank switch operation timed out"
                
            recovery_suggestions = [
                "Check device connection",
                "Verify cartridge is properly inserted",
                "Try reducing communication speed",
                "Restart the device"
            ]
            
            super().__init__(message, recovery_suggestions)
            self.bank_index = bank_index
            self.timeout_seconds = timeout_seconds

    # Add other fallback exceptions as needed
    class InvalidWriteBankSize(CartClinicError):
        pass
    
    class WriteBlockAddressError(CartClinicError):
        pass
    
    class WriteBlockDataError(CartClinicError):
        pass
    
    class ComparisonError(CartClinicError):
        pass
    
    class FlashDetectionError(CartClinicError):
        pass
    
    class TransportError(CartClinicError):
        pass
    
    class FramDetectionError(CartClinicError):
        pass