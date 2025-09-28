"""
Enhanced Logging Utilities for Flashing Tool

Integrated logging utilities from decompiled codebase with
improved functionality and error handling.
"""

import logging
import random
import re
import time
from typing import Optional


class IntervalSamplingFilter(logging.Filter):
    """
    A logging filter for emitting events on a fixed time interval.

    Each filter object will always have a unique ID; a hash value that is a
    combination of the name and interval. Therefore, when multiple filters
    are added to the same logger via `Logger.addFilter`, only the new filters
    will be added to the logger's internal list of filters.

    The time interval uses monotonic time. In this way, it is unaffected
    by system time and shield from things like clock drift and timezone changes.

    Example usage:

    .. code-block:: python
    
        from flashing_tool.logging_utils import IntervalSamplingFilter

        logger = logging.getLogger(__name__)

        # Create the filter and add it to the logger.
        interval_filter = IntervalSamplingFilter(name="chromatic_scan_error", interval=3)
        logger.addFilter(interval_filter)

        # Annotate the log message with the filter
        logger.info(f"{interval_filter} Chromatic scan error")
    """
    
    def __init__(self, name: str, interval: float):
        """
        Initialize interval sampling filter
        
        Args:
            name: Filter name for identification
            interval: Minimum interval between log emissions (seconds)
        """
        super().__init__()
        self.name = name
        self.interval = interval
        self.previous: float = 0
        self._log_tag = f"tag:{self.name}"
    
    def __str__(self) -> str:
        """String representation returns the log tag"""
        return self._log_tag
    
    def __hash__(self) -> int:
        """Hash based on name and interval for uniqueness"""
        return hash(self.name + str(self.interval))
    
    @property
    def log_tag(self) -> str:
        """Get the log tag for this filter"""
        return self._log_tag
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since last emission"""
        return time.monotonic() - self.previous
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on interval sampling
        
        Args:
            record: Log record to filter
            
        Returns:
            True if record should be emitted, False otherwise
        """
        message = record.getMessage()
        
        # If this message doesn't contain our tag, let it through
        if self._log_tag not in message:
            return True
        
        # Remove the tag from the message for cleaner output
        filter_name_re = re.compile(re.escape(self._log_tag) + r'\s*')
        sanitized_msg = filter_name_re.sub('', message)
        record.msg = sanitized_msg
        
        # Check if enough time has elapsed since last emission
        current_time = time.monotonic()
        if self.previous == 0 or (current_time - self.previous) >= self.interval:
            self.previous = current_time
            return True
        
        return False


class UniformSamplingFilter(logging.Filter):
    """
    A logging filter for sampling logs with a fixed probability.

    This filter can either be attached to a handler or logger object. When
    attached to a handler, the filter will be consulted before the event is
    emitted by the handler. However, when attached to the logger, the filter
    will be consulted before the event is sent to the handler.
    """
    
    def __init__(self, p: float = 0.1, level: int = logging.INFO):
        """
        Initialize uniform sampling filter
        
        Args:
            p: Probability that the log record is emitted (0.0 to 1.0)
            level: Sampling applies to log records with this level or lower
        """
        super().__init__()
        self.sample_rate = max(0.0, min(1.0, p))  # Clamp to [0.0, 1.0]
        self.level = level
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on uniform sampling
        
        Args:
            record: Log record to filter
            
        Returns:
            True if record should be emitted, False otherwise
        """
        # Always emit records above the sampling level
        if record.levelno > self.level:
            return True
        
        # Sample records at or below the sampling level
        return random.random() < self.sample_rate


class ContextualFilter(logging.Filter):
    """
    A logging filter that adds contextual information to log records
    """
    
    def __init__(self, context: dict):
        """
        Initialize contextual filter
        
        Args:
            context: Dictionary of context information to add to records
        """
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add context information to log record
        
        Args:
            record: Log record to enhance
            
        Returns:
            Always True (doesn't filter, just enhances)
        """
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class ErrorCountFilter(logging.Filter):
    """
    A logging filter that tracks error counts and can suppress repeated errors
    """
    
    def __init__(self, max_errors: int = 10, reset_interval: float = 300):
        """
        Initialize error count filter
        
        Args:
            max_errors: Maximum errors to allow before suppression
            reset_interval: Time interval to reset error count (seconds)
        """
        super().__init__()
        self.max_errors = max_errors
        self.reset_interval = reset_interval
        self.error_count = 0
        self.last_reset = time.monotonic()
        self.suppressed_count = 0
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records based on error count
        
        Args:
            record: Log record to filter
            
        Returns:
            True if record should be emitted, False otherwise
        """
        current_time = time.monotonic()
        
        # Reset counter if interval has passed
        if current_time - self.last_reset > self.reset_interval:
            if self.suppressed_count > 0:
                # Log suppression summary
                summary_record = logging.LogRecord(
                    name=record.name,
                    level=logging.WARNING,
                    pathname=record.pathname,
                    lineno=record.lineno,
                    msg=f"Suppressed {self.suppressed_count} similar error messages",
                    args=(),
                    exc_info=None
                )
                # Emit the summary (bypass this filter)
                record.manager.handle(summary_record)
            
            self.error_count = 0
            self.suppressed_count = 0
            self.last_reset = current_time
        
        # Only count ERROR and CRITICAL level messages
        if record.levelno >= logging.ERROR:
            self.error_count += 1
            
            if self.error_count > self.max_errors:
                self.suppressed_count += 1
                return False
        
        return True


def setup_enhanced_logging(logger_name: str = 'mrupdater', 
                          level: int = logging.INFO,
                          enable_interval_sampling: bool = True,
                          enable_error_suppression: bool = True) -> logging.Logger:
    """
    Set up enhanced logging with integrated filters
    
    Args:
        logger_name: Name of the logger to configure
        level: Logging level
        enable_interval_sampling: Enable interval sampling for repeated messages
        enable_error_suppression: Enable error count suppression
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Create console handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Add enhanced filters
    if enable_interval_sampling:
        interval_filter = IntervalSamplingFilter('repeated_messages', 5.0)
        logger.addFilter(interval_filter)
    
    if enable_error_suppression:
        error_filter = ErrorCountFilter(max_errors=5, reset_interval=60)
        logger.addFilter(error_filter)
    
    return logger


__all__ = [
    'IntervalSamplingFilter',
    'UniformSamplingFilter', 
    'ContextualFilter',
    'ErrorCountFilter',
    'setup_enhanced_logging',
]