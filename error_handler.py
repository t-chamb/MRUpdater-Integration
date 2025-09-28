"""
Unified Error Handler for MRUpdater

This module provides centralized error handling functionality that integrates
the enhanced exception system with logging, user notifications, and recovery strategies.
"""

import logging
import traceback
from typing import Optional, Dict, Any, Callable, List
from enum import Enum

try:
    from cartclinic.exceptions import (
        CartClinicBaseException,
        CartClinicErrorSeverity,
        create_enhanced_exception,
        is_recoverable_error,
        get_recovery_suggestions,
        get_exception_hierarchy
    )
except ImportError:
    # Fallback if unified exception system is not available
    class CartClinicErrorSeverity(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    class CartClinicBaseException(Exception):
        def __init__(self, message, severity=CartClinicErrorSeverity.MEDIUM, recovery_suggestions=None):
            super().__init__(message)
            self.severity = severity
            self.recovery_suggestions = recovery_suggestions or []
    
    def create_enhanced_exception(e, context=None):
        return CartClinicBaseException(str(e))
    
    def is_recoverable_error(e):
        return True
    
    def get_recovery_suggestions(e):
        return ["Try the operation again"]
    
    def get_exception_hierarchy():
        return {}

logger = logging.getLogger(__name__)


class ErrorHandlingStrategy(Enum):
    """Error handling strategies."""
    RAISE = "raise"           # Re-raise the exception
    LOG_AND_RAISE = "log_and_raise"  # Log then re-raise
    LOG_AND_SUPPRESS = "log_and_suppress"  # Log and suppress
    NOTIFY_USER = "notify_user"  # Show user notification
    ATTEMPT_RECOVERY = "attempt_recovery"  # Try automatic recovery


class UnifiedErrorHandler:
    """
    Unified error handler that provides consistent error handling across the application.
    """
    
    def __init__(self):
        self.error_callbacks: Dict[str, List[Callable]] = {}
        self.recovery_strategies: Dict[type, Callable] = {}
        self.error_statistics: Dict[str, int] = {}
        
    def register_error_callback(self, error_type: str, callback: Callable):
        """
        Register a callback for specific error types.
        
        Args:
            error_type: Error type name or 'all' for all errors
            callback: Callback function that takes (exception, context)
        """
        if error_type not in self.error_callbacks:
            self.error_callbacks[error_type] = []
        self.error_callbacks[error_type].append(callback)
    
    def register_recovery_strategy(self, exception_type: type, strategy: Callable):
        """
        Register a recovery strategy for specific exception types.
        
        Args:
            exception_type: Exception class
            strategy: Recovery function that takes (exception, context) and returns bool
        """
        self.recovery_strategies[exception_type] = strategy
    
    def handle_error(self, 
                    exception: Exception,
                    context: Optional[Dict[str, Any]] = None,
                    strategy: ErrorHandlingStrategy = ErrorHandlingStrategy.LOG_AND_RAISE,
                    user_message: Optional[str] = None) -> bool:
        """
        Handle an error using the specified strategy.
        
        Args:
            exception: The exception to handle
            context: Additional context information
            strategy: How to handle the error
            user_message: Custom user message (overrides default)
            
        Returns:
            True if error was handled successfully, False otherwise
        """
        context = context or {}
        
        # Update error statistics
        error_type = type(exception).__name__
        self.error_statistics[error_type] = self.error_statistics.get(error_type, 0) + 1
        
        # Enhance exception if needed
        if not isinstance(exception, CartClinicBaseException):
            enhanced_exception = create_enhanced_exception(exception, context)
        else:
            enhanced_exception = exception
        
        # Log the error
        self._log_error(enhanced_exception, context)
        
        # Call registered callbacks
        self._call_error_callbacks(enhanced_exception, context)
        
        # Handle based on strategy
        if strategy == ErrorHandlingStrategy.RAISE:
            raise exception
        elif strategy == ErrorHandlingStrategy.LOG_AND_RAISE:
            raise enhanced_exception
        elif strategy == ErrorHandlingStrategy.LOG_AND_SUPPRESS:
            return True
        elif strategy == ErrorHandlingStrategy.NOTIFY_USER:
            self._notify_user(enhanced_exception, user_message)
            return True
        elif strategy == ErrorHandlingStrategy.ATTEMPT_RECOVERY:
            return self._attempt_recovery(enhanced_exception, context)
        
        return False
    
    def _log_error(self, exception: Exception, context: Dict[str, Any]):
        """Log error with appropriate level based on severity."""
        if isinstance(exception, CartClinicBaseException):
            severity = exception.severity
            if severity == CartClinicErrorSeverity.CRITICAL:
                log_level = logging.CRITICAL
            elif severity == CartClinicErrorSeverity.HIGH:
                log_level = logging.ERROR
            elif severity == CartClinicErrorSeverity.MEDIUM:
                log_level = logging.WARNING
            else:
                log_level = logging.INFO
        else:
            log_level = logging.ERROR
        
        logger.log(log_level, f"Error: {exception}")
        
        if context:
            logger.debug(f"Error context: {context}")
        
        # Log stack trace for debugging
        if log_level >= logging.ERROR:
            logger.debug(f"Stack trace: {traceback.format_exc()}")
    
    def _call_error_callbacks(self, exception: Exception, context: Dict[str, Any]):
        """Call registered error callbacks."""
        error_type = type(exception).__name__
        
        # Call specific callbacks
        for callback in self.error_callbacks.get(error_type, []):
            try:
                callback(exception, context)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
        
        # Call general callbacks
        for callback in self.error_callbacks.get('all', []):
            try:
                callback(exception, context)
            except Exception as e:
                logger.error(f"Error in general error callback: {e}")
    
    def _notify_user(self, exception: Exception, user_message: Optional[str] = None):
        """Notify user about the error."""
        if user_message:
            message = user_message
        elif isinstance(exception, CartClinicBaseException):
            message = exception.message
        else:
            message = str(exception)
        
        # Try to show GUI notification if available
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            if QApplication.instance():
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Error")
                msg_box.setText(message)
                
                if isinstance(exception, CartClinicBaseException) and exception.recovery_suggestions:
                    suggestions = "\n".join(f"• {suggestion}" for suggestion in exception.recovery_suggestions)
                    msg_box.setDetailedText(f"Recovery suggestions:\n{suggestions}")
                
                msg_box.exec_()
                return
        except ImportError:
            pass
        
        # Fallback to console output
        print(f"ERROR: {message}")
        if isinstance(exception, CartClinicBaseException) and exception.recovery_suggestions:
            print("Recovery suggestions:")
            for suggestion in exception.recovery_suggestions:
                print(f"  • {suggestion}")
    
    def _attempt_recovery(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Attempt automatic recovery from the error using registered strategies.
        
        This method tries to recover from errors using the following approach:
        1. Check for registered recovery strategy for the specific exception type
        2. Fall back to generic recovery strategies for recoverable errors
        3. Log recovery attempts and results for monitoring
        
        Args:
            exception: The exception to recover from
            context: Additional context information
            
        Returns:
            True if recovery was successful, False otherwise
        """
        exception_type = type(exception)
        
        # Try registered recovery strategy first
        if exception_type in self.recovery_strategies:
            try:
                logger.info(f"Attempting registered recovery strategy for {exception_type.__name__}")
                success = self.recovery_strategies[exception_type](exception, context)
                
                if success:
                    logger.info(f"Recovery successful for {exception_type.__name__}")
                else:
                    logger.warning(f"Recovery strategy failed for {exception_type.__name__}")
                
                return success
                
            except Exception as recovery_error:
                logger.error(f"Recovery strategy execution failed: {recovery_error}")
                # Continue to generic recovery
        
        # Try generic recovery for recoverable errors
        if is_recoverable_error(exception):
            logger.info(f"Attempting generic recovery for {exception_type.__name__}")
            return self._attempt_generic_recovery(exception, context)
        
        logger.debug(f"No recovery strategy available for {exception_type.__name__}")
        return False
    
    def _attempt_generic_recovery(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Attempt generic recovery strategies for common error patterns.
        
        Args:
            exception: The exception to recover from
            context: Additional context information
            
        Returns:
            True if generic recovery was successful, False otherwise
        """
        try:
            error_message = str(exception).lower()
            
            # Connection-related errors
            if any(keyword in error_message for keyword in ['connection', 'timeout', 'network']):
                logger.info("Attempting connection recovery")
                return self._recover_connection_error(exception, context)
            
            # File access errors
            if any(keyword in error_message for keyword in ['permission', 'access', 'file']):
                logger.info("Attempting file access recovery")
                return self._recover_file_access_error(exception, context)
            
            # Resource errors
            if any(keyword in error_message for keyword in ['memory', 'resource', 'busy']):
                logger.info("Attempting resource recovery")
                return self._recover_resource_error(exception, context)
            
            return False
            
        except Exception as e:
            logger.error(f"Generic recovery attempt failed: {e}")
            return False
    
    def _recover_connection_error(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Attempt to recover from connection-related errors."""
        # Generic connection recovery logic
        logger.debug("Implementing connection error recovery")
        return False
    
    def _recover_file_access_error(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Attempt to recover from file access errors."""
        # Generic file access recovery logic
        logger.debug("Implementing file access error recovery")
        return False
    
    def _recover_resource_error(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """Attempt to recover from resource-related errors."""
        # Generic resource recovery logic
        logger.debug("Implementing resource error recovery")
        return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring and debugging."""
        total_errors = sum(self.error_statistics.values())
        return {
            'total_errors': total_errors,
            'error_counts': self.error_statistics.copy(),
            'most_common_error': max(self.error_statistics.items(), key=lambda x: x[1])[0] if self.error_statistics else None
        }
    
    def reset_statistics(self):
        """Reset error statistics."""
        self.error_statistics.clear()


# Global error handler instance
_global_error_handler = UnifiedErrorHandler()


def get_error_handler() -> UnifiedErrorHandler:
    """Get the global error handler instance."""
    return _global_error_handler


def handle_error(exception: Exception, 
                context: Optional[Dict[str, Any]] = None,
                strategy: ErrorHandlingStrategy = ErrorHandlingStrategy.LOG_AND_RAISE,
                user_message: Optional[str] = None) -> bool:
    """
    Convenience function to handle errors using the global error handler.
    
    Args:
        exception: The exception to handle
        context: Additional context information
        strategy: How to handle the error
        user_message: Custom user message
        
    Returns:
        True if error was handled successfully, False otherwise
    """
    return _global_error_handler.handle_error(exception, context, strategy, user_message)


def with_error_handling(strategy: ErrorHandlingStrategy = ErrorHandlingStrategy.LOG_AND_RAISE,
                       context: Optional[Dict[str, Any]] = None):
    """
    Decorator to add error handling to functions.
    
    Args:
        strategy: Error handling strategy
        context: Additional context information
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_context = context or {}
                func_context.update({
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                })
                handle_error(e, func_context, strategy)
        return wrapper
    return decorator


# Convenience decorators for common error handling patterns
def log_and_suppress_errors(func):
    """Decorator to log errors and suppress them."""
    return with_error_handling(ErrorHandlingStrategy.LOG_AND_SUPPRESS)(func)


def notify_user_on_error(func):
    """Decorator to notify user of errors."""
    return with_error_handling(ErrorHandlingStrategy.NOTIFY_USER)(func)


def attempt_recovery_on_error(func):
    """Decorator to attempt recovery from errors."""
    return with_error_handling(ErrorHandlingStrategy.ATTEMPT_RECOVERY)(func)


# Backward compatibility alias
ErrorHandler = UnifiedErrorHandler


__all__ = [
    'ErrorHandlingStrategy',
    'UnifiedErrorHandler',
    'ErrorHandler',  # Backward compatibility
    'get_error_handler',
    'handle_error',
    'with_error_handling',
    'log_and_suppress_errors',
    'notify_user_on_error',
    'attempt_recovery_on_error'
]