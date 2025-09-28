"""
Import compatibility layer for MRUpdater integration.

This module provides a unified import structure that works with both original 
and enhanced code, resolving conflicts between library versions and imports.
"""

import sys
import logging
from typing import Optional, Any, Dict, List

logger = logging.getLogger(__name__)

# =============================================================================
# Qt Framework Compatibility
# =============================================================================

QT_AVAILABLE = False
QT_VERSION = None

try:
    from PySide6.QtCore import Qt, QEvent, QObject, QUrl, QTimer
    from PySide6.QtGui import (QIcon, QMovie, QPixmap, QFontDatabase, QFontMetrics, 
                              QDesktopServices, QShortcut, QKeySequence, QTransform)
    from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QLabel, 
                                  QDialog, QWidget, QInputDialog, QVBoxLayout,
                                  QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
                                  QHBoxLayout)
    QT_AVAILABLE = True
    QT_VERSION = "PySide6"
    logger.info("Using PySide6 for Qt framework")
except ImportError as e:
    logger.warning(f"PySide6 not available: {e}")
    try:
        from PyQt6.QtCore import Qt, QEvent, QObject, QUrl, QTimer
        from PyQt6.QtGui import (QIcon, QMovie, QPixmap, QFontDatabase, QFontMetrics, 
                                QDesktopServices, QShortcut, QKeySequence, QTransform)
        from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox, QLabel, 
                                    QDialog, QWidget, QInputDialog, QVBoxLayout,
                                    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
                                    QHBoxLayout)
        QT_AVAILABLE = True
        QT_VERSION = "PyQt6"
        logger.info("Using PyQt6 for Qt framework")
    except ImportError:
        logger.warning("No Qt framework available, creating dummy classes")
        # Create dummy classes for headless operation
        class DummyQtClass:
            def __init__(self, *args, **kwargs):
                pass
            def __call__(self, *args, **kwargs):
                return self
            def __getattr__(self, name):
                return DummyQtClass()
        
        QMainWindow = DummyQtClass
        QObject = DummyQtClass
        QTimer = DummyQtClass
        QApplication = DummyQtClass
        QMessageBox = DummyQtClass
        QLabel = DummyQtClass
        QDialog = DummyQtClass
        QWidget = DummyQtClass
        QInputDialog = DummyQtClass
        QVBoxLayout = DummyQtClass
        QPushButton = DummyQtClass
        QScrollArea = DummyQtClass
        QSizePolicy = DummyQtClass
        QSpacerItem = DummyQtClass
        QHBoxLayout = DummyQtClass
        QIcon = DummyQtClass
        QMovie = DummyQtClass
        QPixmap = DummyQtClass
        QFontDatabase = DummyQtClass
        QFontMetrics = DummyQtClass
        QDesktopServices = DummyQtClass
        QShortcut = DummyQtClass
        QKeySequence = DummyQtClass
        QTransform = DummyQtClass
        Qt = DummyQtClass
        QEvent = DummyQtClass
        QObject = DummyQtClass
        QUrl = DummyQtClass
        QTimer = DummyQtClass

# =============================================================================
# USB Communication Compatibility
# =============================================================================

USB_AVAILABLE = False
USB_BACKEND = None

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
    USB_BACKEND = "pyusb"
    logger.info("USB communication available via pyusb")
except ImportError as e:
    logger.warning(f"USB communication not available: {e}")
    # Create dummy USB module
    class DummyUSB:
        class core:
            @staticmethod
            def find(*args, **kwargs):
                return None
            @staticmethod
            def get_descriptor(*args, **kwargs):
                return None
        class util:
            @staticmethod
            def get_string(*args, **kwargs):
                return ""
            @staticmethod
            def find_descriptor(*args, **kwargs):
                return None
        @staticmethod
        def USBError(*args, **kwargs):
            return Exception("USB not available")
    usb = DummyUSB()
    
    # Also create module-level imports that might be expected
    sys.modules['usb'] = usb
    sys.modules['usb.core'] = usb.core
    sys.modules['usb.util'] = usb.util

# =============================================================================
# Serial Communication Compatibility
# =============================================================================

SERIAL_AVAILABLE = False

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
    logger.info("Serial communication available")
except ImportError as e:
    logger.warning(f"Serial communication not available: {e}")
    # Create dummy serial module
    class DummySerial:
        class Serial:
            def __init__(self, *args, **kwargs):
                pass
            def close(self):
                pass
            def read(self, *args):
                return b''
            def write(self, *args):
                return 0
        class tools:
            class list_ports:
                @staticmethod
                def comports():
                    return []
    serial = DummySerial()

# =============================================================================
# ESP Tool Compatibility
# =============================================================================

ESPTOOL_AVAILABLE = False

try:
    from esptool.loader import ESPLoader, DEFAULT_CONNECT_ATTEMPTS
    from esptool.bin_image import intel_hex_to_bin
    ESPTOOL_AVAILABLE = True
    logger.info("ESP tool available")
except ImportError as e:
    logger.warning(f"ESP tool not available: {e}")
    # Create dummy ESP tool classes
    class DummyESPLoader:
        DEFAULT_CONNECT_ATTEMPTS = 7
        def __init__(self, *args, **kwargs):
            pass
    ESPLoader = DummyESPLoader
    DEFAULT_CONNECT_ATTEMPTS = 7
    def intel_hex_to_bin(*args, **kwargs):
        return b''

# =============================================================================
# State Machine Compatibility
# =============================================================================

STATEMACHINE_AVAILABLE = False

try:
    from statemachine import StateMachine, State
    import statemachine
    STATEMACHINE_AVAILABLE = True
    logger.info("State machine library available")
except ImportError as e:
    logger.warning(f"State machine library not available: {e}")
    # Create dummy state machine classes
    class DummyStateMachine:
        def __init__(self, *args, **kwargs):
            pass
    class DummyState:
        def __init__(self, *args, **kwargs):
            pass
    StateMachine = DummyStateMachine
    State = DummyState
    class DummyStateMachineModule:
        StateMachine = DummyStateMachine
        State = DummyState
    statemachine = DummyStateMachineModule()

# =============================================================================
# AWS/Boto3 Compatibility
# =============================================================================

BOTO3_AVAILABLE = False

try:
    import boto3
    import botocore
    from botocore import UNSIGNED
    BOTO3_AVAILABLE = True
    logger.info("AWS boto3 library available")
except ImportError as e:
    logger.warning(f"AWS boto3 library not available: {e}")
    # Create dummy boto3 classes
    class DummyBoto3:
        @staticmethod
        def client(*args, **kwargs):
            return DummyBoto3()
        def download_file(self, *args, **kwargs):
            pass
    class DummyBotocore:
        UNSIGNED = None
    boto3 = DummyBoto3()
    botocore = DummyBotocore()
    UNSIGNED = None

# =============================================================================
# HTTP Requests Compatibility
# =============================================================================

REQUESTS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
    logger.info("Requests library available")
except ImportError as e:
    logger.warning(f"Requests library not available: {e}")
    # Create dummy requests module
    class DummyRequests:
        class Response:
            def __init__(self):
                self.status_code = 200
                self.text = ""
                self.json_data = {}
            def json(self):
                return self.json_data
        @staticmethod
        def get(*args, **kwargs):
            return DummyRequests.Response()
        @staticmethod
        def post(*args, **kwargs):
            return DummyRequests.Response()
    requests = DummyRequests()

# =============================================================================
# Platform Directories Compatibility
# =============================================================================

PLATFORMDIRS_AVAILABLE = False

try:
    from platformdirs import user_data_dir, user_config_dir
    PLATFORMDIRS_AVAILABLE = True
    logger.info("Platform directories library available")
except ImportError as e:
    logger.warning(f"Platform directories library not available: {e}")
    # Create dummy platform directories functions
    import os
    def user_data_dir(appname=None, appauthor=None):
        if sys.platform == "win32":
            return os.path.expanduser("~/AppData/Local")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support")
        else:
            return os.path.expanduser("~/.local/share")
    
    def user_config_dir(appname=None, appauthor=None):
        if sys.platform == "win32":
            return os.path.expanduser("~/AppData/Local")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Preferences")
        else:
            return os.path.expanduser("~/.config")

# =============================================================================
# Additional Dependencies from Decompiled Version
# =============================================================================

PYDANTIC_AVAILABLE = False

try:
    import pydantic
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
    logger.info("Pydantic library available")
except ImportError as e:
    logger.warning(f"Pydantic library not available: {e}")
    # Create dummy pydantic classes
    class DummyBaseModel:
        def __init__(self, *args, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        def dict(self):
            return {}
        def json(self):
            return "{}"
    BaseModel = DummyBaseModel
    def Field(*args, **kwargs):
        return None
    class DummyPydantic:
        BaseModel = DummyBaseModel
        Field = Field
    pydantic = DummyPydantic()

REEDSOLO_AVAILABLE = False

try:
    import reedsolo
    REEDSOLO_AVAILABLE = True
    logger.info("Reed-Solomon library available")
except ImportError as e:
    logger.warning(f"Reed-Solomon library not available: {e}")
    # Create dummy reedsolo module
    class DummyReedSolo:
        class RSCodec:
            def __init__(self, *args, **kwargs):
                pass
            def encode(self, data):
                return data
            def decode(self, data):
                return data
    reedsolo = DummyReedSolo()

HASHLIB_AVAILABLE = False

try:
    import hashlib
    HASHLIB_AVAILABLE = True
    logger.info("Hashlib library available")
except ImportError as e:
    logger.warning(f"Hashlib library not available: {e}")
    # Create dummy hashlib module
    class DummyHashlib:
        @staticmethod
        def sha256(data=b''):
            class DummyHash:
                def update(self, data):
                    pass
                def hexdigest(self):
                    return "dummy_hash"
                def digest(self):
                    return b"dummy_hash"
            return DummyHash()
        @staticmethod
        def md5(data=b''):
            return DummyHashlib.sha256(data)
    hashlib = DummyHashlib()

# =============================================================================
# Compatibility Information
# =============================================================================

def get_compatibility_info() -> Dict[str, Any]:
    """Get information about available libraries and compatibility status."""
    return {
        'qt': {
            'available': QT_AVAILABLE,
            'version': QT_VERSION
        },
        'usb': {
            'available': USB_AVAILABLE,
            'backend': USB_BACKEND
        },
        'serial': {
            'available': SERIAL_AVAILABLE
        },
        'esptool': {
            'available': ESPTOOL_AVAILABLE
        },
        'statemachine': {
            'available': STATEMACHINE_AVAILABLE
        },
        'boto3': {
            'available': BOTO3_AVAILABLE
        },
        'requests': {
            'available': REQUESTS_AVAILABLE
        },
        'platformdirs': {
            'available': PLATFORMDIRS_AVAILABLE
        },
        'pydantic': {
            'available': PYDANTIC_AVAILABLE
        },
        'reedsolo': {
            'available': REEDSOLO_AVAILABLE
        },
        'hashlib': {
            'available': HASHLIB_AVAILABLE
        }
    }

def check_required_dependencies(required: List[str]) -> Dict[str, bool]:
    """Check if required dependencies are available."""
    compatibility = get_compatibility_info()
    results = {}
    
    for dep in required:
        if dep in compatibility:
            results[dep] = compatibility[dep]['available']
        else:
            results[dep] = False
    
    return results

def resolve_decompiled_imports() -> Dict[str, Any]:
    """
    Resolve imports that may conflict between original and decompiled versions.
    
    Returns:
        Dictionary of resolved imports with conflict resolution status
    """
    resolved = {}
    
    # Import the unified resolver
    try:
        from unified_import_resolver import get_resolver
        resolver = get_resolver()
        
        # Key modules that may have conflicts
        conflict_modules = [
            'cartclinic.gui',
            'cartclinic.cartridge_read', 
            'cartclinic.cartridge_write',
            'flashing_tool.chromatic',
            'flashing_tool.util',
            'libpyretro.cartclinic.comms',
            'libpyretro.cartclinic.protocol.common'
        ]
        
        for module_name in conflict_modules:
            result = resolver.resolve_import(module_name)
            resolved[module_name] = {
                'available': result is not None,
                'module': result,
                'source': 'unified_resolver'
            }
            
    except ImportError as e:
        logger.warning(f"Unified resolver not available: {e}")
        # Fallback to basic resolution
        for module_name in conflict_modules:
            try:
                import importlib
                module = importlib.import_module(module_name)
                resolved[module_name] = {
                    'available': True,
                    'module': module,
                    'source': 'direct_import'
                }
            except ImportError:
                resolved[module_name] = {
                    'available': False,
                    'module': None,
                    'source': 'failed'
                }
                
    return resolved

def log_compatibility_status():
    """Log the current compatibility status."""
    info = get_compatibility_info()
    logger.info("=== Dependency Compatibility Status ===")
    for lib, status in info.items():
        if status['available']:
            version_info = f" ({status.get('version', status.get('backend', 'available'))})"
            logger.info(f"✓ {lib}: Available{version_info}")
        else:
            logger.warning(f"✗ {lib}: Not available (using dummy implementation)")

# Log compatibility status on import
if __name__ != "__main__":
    log_compatibility_status()