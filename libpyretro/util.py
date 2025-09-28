"""
Utility functions for LibPyRetro.

This module provides common utility functions used throughout the LibPyRetro
library, including path resolution, shell command execution, and platform
detection utilities.
"""

import os
import platform
import subprocess
import sys
import stat
from pathlib import Path
from typing import Union, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Platform detection constants
SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0

CPU_TYPES = {
    'amd64': 'x86_64',
    'x86_64': 'x86_64', 
    'arm64': 'arm64',
    'aarch64': 'arm64',
    'i386': 'x86',
    'i686': 'x86'
}

OS_NAME = platform.system().lower()
CPU_TYPE = CPU_TYPES.get(platform.machine().lower(), 'unknown')

# Type aliases
CommandResult = Union[str, None]

class ShellCommandError(Exception):
    """Raised when a shell command fails to execute."""
    pass

class PathResolutionError(Exception):
    """Raised when path resolution fails."""
    pass

def resolve_path(path: Optional[str] = None) -> str:
    """
    Returns the absolute path for the specified relative path.
    
    The path should be relative to the application's entry point,
    not the module calling resolve_path.
    
    Args:
        path: Relative path to resolve
        
    Returns:
        Absolute path
        
    Raises:
        PathResolutionError: If path resolution fails
    """
    try:
        # Get the executable path (handles PyInstaller bundled apps)
        exec_path = getattr(sys, '_MEIPASS', os.getcwd())
        
        if path is None:
            return os.path.abspath(exec_path)
            
        resolved_path = os.path.abspath(os.path.join(exec_path, path))
        return resolved_path
        
    except Exception as e:
        raise PathResolutionError(f"Failed to resolve path '{path}': {e}")

def shell_execute(cmd: List[str], 
                 redirect_to_stdout: bool = True,
                 timeout: Optional[int] = None,
                 cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command and return the result.
    
    Args:
        cmd: Command and arguments as a list
        redirect_to_stdout: Whether to redirect stderr to stdout
        timeout: Command timeout in seconds
        cwd: Working directory for the command
        
    Returns:
        Tuple of (return_code, stdout, stderr)
        
    Raises:
        ShellCommandError: If command execution fails
    """
    try:
        kwargs = {
            'creationflags': SUBPROCESS_FLAGS,
            'shell': False,
            'stdout': subprocess.PIPE,
            'text': True,
            'universal_newlines': True,
            'timeout': timeout,
            'cwd': cwd
        }
        
        if not redirect_to_stdout:
            kwargs['stderr'] = subprocess.PIPE
        else:
            kwargs['stderr'] = subprocess.STDOUT
            
        logger.debug(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, **kwargs)
        
        stdout = result.stdout or ""
        stderr = result.stderr or "" if not redirect_to_stdout else ""
        
        logger.debug(f"Command completed with return code: {result.returncode}")
        
        return result.returncode, stdout, stderr
        
    except subprocess.TimeoutExpired as e:
        raise ShellCommandError(f"Command timed out after {timeout}s: {' '.join(cmd)}")
    except subprocess.CalledProcessError as e:
        raise ShellCommandError(f"Command failed with return code {e.returncode}: {' '.join(cmd)}")
    except Exception as e:
        raise ShellCommandError(f"Failed to execute command: {e}")

def make_executable(file_path: str) -> bool:
    """
    Make a file executable on Unix-like systems.
    
    Args:
        file_path: Path to the file to make executable
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if OS_NAME != 'windows':
            current_mode = os.stat(file_path).st_mode
            os.chmod(file_path, current_mode | stat.S_IEXEC)
            logger.debug(f"Made file executable: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to make file executable: {e}")
        return False

def get_platform_info() -> dict:
    """
    Get detailed platform information.
    
    Returns:
        Dictionary containing platform details
    """
    return {
        'os_name': OS_NAME,
        'cpu_type': CPU_TYPE,
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version()
    }

def find_executable(name: str, paths: Optional[List[str]] = None) -> Optional[str]:
    """
    Find an executable in the system PATH or specified paths.
    
    Args:
        name: Name of the executable to find
        paths: Optional list of paths to search
        
    Returns:
        Full path to executable if found, None otherwise
    """
    # Add common executable extensions on Windows
    if OS_NAME == 'windows' and not name.endswith('.exe'):
        name += '.exe'
        
    # Search in specified paths first
    if paths:
        for path in paths:
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
                
    # Search in system PATH
    for path in os.environ.get('PATH', '').split(os.pathsep):
        if path:
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
                
    return None

def ensure_directory(directory: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Path to the directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False

def safe_filename(filename: str) -> str:
    """
    Convert a string to a safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')
        
    # Remove leading/trailing whitespace and dots
    safe_name = safe_name.strip(' .')
    
    # Ensure it's not empty
    if not safe_name:
        safe_name = 'unnamed'
        
    return safe_name

def get_file_size(file_path: str) -> Optional[int]:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes, or None if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except (OSError, IOError):
        return None

def format_bytes(size: int) -> str:
    """
    Format a byte size into a human-readable string.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

# Export main functions
__all__ = [
    'resolve_path',
    'shell_execute', 
    'make_executable',
    'get_platform_info',
    'find_executable',
    'ensure_directory',
    'safe_filename',
    'get_file_size',
    'format_bytes',
    'ShellCommandError',
    'PathResolutionError',
    'OS_NAME',
    'CPU_TYPE',
    'SUBPROCESS_FLAGS'
]