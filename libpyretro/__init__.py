"""
LibPyRetro - Python library for ModRetro device communication and cartridge operations.

This library provides high-level interfaces for communicating with ModRetro devices,
managing cartridge operations, and handling firmware updates.
"""

__version__ = "1.0.0"
__author__ = "ModRetro Team"

# Core modules
from . import cartclinic
from . import feature_api
from . import ips_util
from . import util

__all__ = [
    'cartclinic',
    'feature_api', 
    'ips_util',
    'util'
]