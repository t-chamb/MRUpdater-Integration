"""
Constants for Cart Clinic operations.

This module defines constants used throughout the Cart Clinic system,
including loading text, operation types, and configuration items.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


# Loading text constants
LOADING_TEXT_DEFAULT = "CHECKING CARTRIDGE..."

LOADING_TEXT_SNIPPETS = [
    "ANALYZING CARTRIDGE DATA...",
    "READING ROM HEADER...",
    "DETECTING FLASH TYPE...",
    "VALIDATING CHECKSUM...",
    "CHECKING SAVE DATA...",
    "COMMUNICATING WITH SERVER...",
    "PROCESSING GAME INFO...",
    "VERIFYING COMPATIBILITY...",
    "PREPARING UPDATE DATA...",
    "FINALIZING ANALYSIS..."
]


class CartClinicFeature(Enum):
    """Cart Clinic feature flags."""
    DEVELOPER_MODE = "developer_mode"
    SAVE_OPERATIONS = "save_operations"
    HOMEBREW_SUPPORT = "homebrew_support"
    ADVANCED_DIAGNOSTICS = "advanced_diagnostics"


class CartClinicConfigItem(Enum):
    """Configuration items for Cart Clinic."""
    PREVIOUS_HOMEBREW_DIR = "previous_homebrew_dir"
    PREVIOUS_SAVE_DIR = "previous_save_dir"
    AUTO_BACKUP_SAVES = "auto_backup_saves"
    CONFIRMATION_DIALOGS = "confirmation_dialogs"


class CartClinicSaveOperation(Enum):
    """Save operation types with associated messages."""
    
    @dataclass
    class SaveOpInfo:
        warning_message: str
        success_message: str
        status_message: str
    
    BACKUP = SaveOpInfo(
        warning_message="This will backup your save data to a file. Continue?",
        success_message="Save data backed up successfully!",
        status_message="BACKING UP SAVE DATA..."
    )
    
    RESTORE = SaveOpInfo(
        warning_message="This will overwrite your current save data. Continue?",
        success_message="Save data restored successfully!",
        status_message="RESTORING SAVE DATA..."
    )
    
    ERASE = SaveOpInfo(
        warning_message="This will permanently erase your save data. Continue?",
        success_message="Save data erased successfully!",
        status_message="ERASING SAVE DATA..."
    )


class CartClinicState(Enum):
    """Cart Clinic operation states."""
    IDLE = "idle"
    CONNECTING = "connecting"
    CHECKING = "checking"
    UPDATING = "updating"
    PROCESSING_SAVE = "processing_save"
    ERROR = "error"
    SUCCESS = "success"
    UPTODATE = "uptodate"


class CartClinicError(Enum):
    """Common Cart Clinic error types."""
    DEVICE_NOT_CONNECTED = "Device not connected"
    CARTRIDGE_NOT_DETECTED = "Cartridge not detected"
    FIRMWARE_LOAD_FAILED = "Failed to load Cart Clinic firmware"
    COMMUNICATION_ERROR = "Communication error with device"
    SERVER_ERROR = "Server communication error"
    GAME_NOT_RECOGNIZED = "Game not recognized"
    SAVE_OPERATION_FAILED = "Save operation failed"
    UPDATE_FAILED = "Update operation failed"


# FRAM detection constants
FRAM_SIZE = 32768  # 32KB FRAM size

# Bank size constants (from decompiled version)
BANK_SIZE = 16384  # 16KB bank size for ROM banks

# Write operation constants
NUM_WRITE_RETRIES = 3  # Number of retries for write operations
WRITE_VERIFY_ENABLED = True  # Enable write verification by default
WRITE_TIMEOUT_SECONDS = 30  # Timeout for write operations


# Progress thresholds
PROGRESS_THRESHOLDS = {
    'INITIALIZATION': 10,
    'CARTRIDGE_DETECTION': 25,
    'GAME_ANALYSIS': 50,
    'SERVER_COMMUNICATION': 75,
    'FINALIZATION': 95,
    'COMPLETE': 100
}


# Timeout constants (in seconds)
TIMEOUTS = {
    'DEVICE_CONNECTION': 30,
    'CARTRIDGE_DETECTION': 60,
    'SERVER_REQUEST': 45,
    'FIRMWARE_LOAD': 120,
    'SAVE_OPERATION': 180
}


# File extensions
SUPPORTED_ROM_EXTENSIONS = ['.gb', '.gbc', '.bin']
SAVE_FILE_EXTENSIONS = ['.sav', '.srm']


# UI Constants
UI_UPDATE_INTERVAL_MS = 100  # Milliseconds between UI updates
ANIMATION_FRAME_RATE = 30    # FPS for animations


class CartridgeType(Enum):
    """Cartridge type detection."""
    UNKNOWN = "unknown"
    GAME_BOY = "gameboy"
    GAME_BOY_COLOR = "gameboy_color"
    HOMEBREW = "homebrew"


class FlashType(Enum):
    """Flash memory types."""
    UNKNOWN = "unknown"
    NOR_FLASH = "nor_flash"
    NAND_FLASH = "nand_flash"
    FRAM = "fram"
    EEPROM = "eeprom"


# Default configuration values
DEFAULT_CONFIG = {
    CartClinicConfigItem.PREVIOUS_HOMEBREW_DIR: "",
    CartClinicConfigItem.PREVIOUS_SAVE_DIR: "",
    CartClinicConfigItem.AUTO_BACKUP_SAVES: True,
    CartClinicConfigItem.CONFIRMATION_DIALOGS: True
}


# Error recovery strategies
ERROR_RECOVERY_STRATEGIES = {
    CartClinicError.DEVICE_NOT_CONNECTED: [
        "Check USB connection",
        "Try a different USB port",
        "Restart the device"
    ],
    CartClinicError.CARTRIDGE_NOT_DETECTED: [
        "Ensure cartridge is properly inserted",
        "Clean cartridge contacts",
        "Try reinserting the cartridge"
    ],
    CartClinicError.COMMUNICATION_ERROR: [
        "Check device connection",
        "Restart the application",
        "Try a different USB cable"
    ]
}