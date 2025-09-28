"""
MRUpdater Flashing Tool Module

This module provides device management and firmware flashing capabilities
for the ModRetro Chromatic device.
"""

__version__ = "2.0.0"
__author__ = "ModRetro"

from .chromatic import Chromatic, ChromaticError

__all__ = [
    'Chromatic',
    'ChromaticError',
]