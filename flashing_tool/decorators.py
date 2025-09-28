"""
Enhanced Decorators for Flashing Tool

Utility decorators for tracing, exception handling, and performance monitoring.
Integrated from decompiled codebase with improvements.
"""

import logging
import time
import functools
from typing import Callable, Any, Union, Optional, List, Type
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def trace(debug: bool = False, sample_rate: Optional[float] = None):
    """
    Traces and times function execution.

    When a `sample_rate` is provided [0.0, 1.0], only a percentage of the traces will
    be logged. This is enforced by sampling logic to mitigate a deluge of traces which
    can make it difficult to spot anomalies.

    Args:
        debug: When True, function parameters are logged at DEBUG level
        sample_rate: Probability that the trace is logged. Float value in the range [0.0, 1.0]
        
    Returns:
        Decorated function with tracing capabilities
    """
    import random
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check sampling rate
            if sample_rate is not None and random.random() > sample_rate:
                return func(*args, **kwargs)
            
            # Increment call count
            if not hasattr(wrapper, 'call_count'):
                wrapper.call_count = 0
            wrapper.call_count += 1
            
            # Log function call
            logger.info(f'Call no. {wrapper.call_count} of {func.__name__}')
            
            if debug:
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f'{k}={repr(v)}' for k, v in kwargs.items()]
                signature = ', '.join(args_repr + kwargs_repr)
                logger.debug(f'Calling {func.__name__}({signature})')
            
            # Time execution
            started_at = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - started_at
                logger.info(f'{func.__name__} completed in {elapsed:.4f}s')
                
                if debug:
                    logger.debug(f'{func.__name__} returned: {repr(result)}')
                
                return result
                
            except Exception as e:
                elapsed = time.perf_counter() - started_at
                logger.error(f'{func.__name__} failed after {elapsed:.4f}s: {e}')
                raise
        
        wrapper.call_count = 0
        return wrapper
    
    return decorator


def handle_exceptions(
    exceptions: Optional[Union[Type[Exception], List[Type[Exception]]]] = None,
    raise_as: Optional[Type[Exception]] = None,
    log_level: int = logging.ERROR,
    return_value: Any = None,
    suppress: bool = False
):
    """
    Handles a list of exceptions and optionally re-raises them as a different exception.
    
    Args:
        exceptions: Exception type(s) to catch. If None, catches all exceptions
        raise_as: Exception type to raise instead of the original
        log_level: Logging level for caught exceptions
        return_value: Value to return if exception is suppressed
        suppress: If True, suppress exceptions and return return_value
        
    Returns:
        Decorated function with exception handling
    """
    if exceptions is None:
        exceptions = [Exception]
    elif not isinstance(exceptions, list):
        exceptions = [exceptions]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(exceptions) as e:
                logger.log(log_level, f'Exception in {func.__name__}: {e}')
                
                if suppress:
                    return return_value
                elif raise_as:
                    raise raise_as(f'Error in {func.__name__}: {e}') from e
                else:
                    raise
        
        return wrapper
    
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Optional[Union[Type[Exception], List[Type[Exception]]]] = None,
    on_retry: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Exception type(s) to retry on. If None, retries on all exceptions
        on_retry: Callback function called on each retry attempt
        
    Returns:
        Decorated function with retry logic
    """
    if exceptions is None:
        exceptions = [Exception]
    elif not isinstance(exceptions, list):
        exceptions = [exceptions]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt, re-raise the exception
                        logger.error(f'{func.__name__} failed after {max_attempts} attempts: {e}')
                        raise
                    
                    logger.warning(f'{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...')
                    
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


def timeout(seconds: float):
    """
    Timeout decorator that raises TimeoutError if function takes too long.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function with timeout
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f'{func.__name__} timed out after {seconds} seconds')
            
            # Set up signal handler (Unix only)
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(seconds))
                
                try:
                    result = func(*args, **kwargs)
                    signal.alarm(0)  # Cancel the alarm
                    return result
                finally:
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Fallback for Windows - use threading
                import threading
                result = [None]
                exception = [None]
                
                def target():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(seconds)
                
                if thread.is_alive():
                    logger.error(f'{func.__name__} timed out after {seconds} seconds')
                    raise TimeoutError(f'{func.__name__} timed out after {seconds} seconds')
                
                if exception[0]:
                    raise exception[0]
                
                return result[0]
        
        return wrapper
    
    return decorator


def cache_result(ttl: Optional[float] = None):
    """
    Cache function result with optional TTL (time-to-live).
    
    Args:
        ttl: Time-to-live in seconds. If None, cache never expires
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key = str(args) + str(sorted(kwargs.items()))
            
            # Check if result is cached and still valid
            if key in cache:
                result, timestamp = cache[key]
                if ttl is None or time.time() - timestamp < ttl:
                    logger.debug(f'Cache hit for {func.__name__}')
                    return result
                else:
                    logger.debug(f'Cache expired for {func.__name__}')
                    del cache[key]
            
            # Call function and cache result
            logger.debug(f'Cache miss for {func.__name__}')
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            
            return result
        
        # Add cache management methods
        def clear_cache():
            cache.clear()
            logger.debug(f'Cache cleared for {func.__name__}')
        
        def cache_info():
            return {
                'size': len(cache),
                'entries': list(cache.keys())
            }
        
        wrapper.clear_cache = clear_cache
        wrapper.cache_info = cache_info
        
        return wrapper
    
    return decorator


@contextmanager
def performance_monitor(operation_name: str):
    """
    Context manager for monitoring performance of code blocks.
    
    Args:
        operation_name: Name of the operation being monitored
        
    Yields:
        Dictionary with performance metrics
    """
    metrics = {
        'operation': operation_name,
        'start_time': time.perf_counter(),
        'memory_start': None,
        'memory_peak': None,
        'memory_end': None
    }
    
    # Try to get memory usage if psutil is available
    try:
        import psutil
        process = psutil.Process()
        metrics['memory_start'] = process.memory_info().rss
    except ImportError:
        pass
    
    logger.info(f'Starting performance monitoring for: {operation_name}')
    
    try:
        yield metrics
    finally:
        metrics['end_time'] = time.perf_counter()
        metrics['duration'] = metrics['end_time'] - metrics['start_time']
        
        # Get final memory usage
        try:
            import psutil
            process = psutil.Process()
            metrics['memory_end'] = process.memory_info().rss
            if metrics['memory_start']:
                metrics['memory_delta'] = metrics['memory_end'] - metrics['memory_start']
        except ImportError:
            pass
        
        logger.info(f'Performance monitoring completed for: {operation_name} '
                   f'(Duration: {metrics["duration"]:.4f}s)')


def validate_types(**type_hints):
    """
    Decorator to validate function argument types at runtime.
    
    Args:
        **type_hints: Mapping of argument names to expected types
        
    Returns:
        Decorated function with type validation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate types
            for param_name, expected_type in type_hints.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is not None and not isinstance(value, expected_type):
                        raise TypeError(
                            f'{func.__name__}() argument {param_name} must be '
                            f'{expected_type.__name__}, got {type(value).__name__}'
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


__all__ = [
    'trace',
    'handle_exceptions',
    'retry',
    'timeout',
    'cache_result',
    'performance_monitor',
    'validate_types',
]