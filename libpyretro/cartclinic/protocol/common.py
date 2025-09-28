"""
Common protocol definitions and constants for CartClinic communication.

This module defines the core protocol elements including command IDs, reply payload lengths,
screen dimensions, and data structures used throughout the communication protocol.
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, Tuple

# Screen dimensions for Chromatic device
SCREEN_PIXEL_WIDTH = 160
SCREEN_PIXEL_HEIGHT = 144

# Protocol timing constants
BANK_SWITCH_TIMEOUT_S = 5
ERASE_SECTOR_TIMEOUT_S = 10
ERASE_ALL_TIMEOUT_S = 100
RESET_FLASH_CTLR_TIMEOUT_S = 5
START_ERASE_TIMEOUT_S = 5

# Bank and block size constants
BANKSIZE = 16384  # 16KB
BYTES_PER_BLOCK = 256
BLOCKS_PER_BANK = BANKSIZE // BYTES_PER_BLOCK  # 64 blocks per bank

# FRAM constants
FRAM_BANK_SIZE = 8192  # 8KB
BLOCKS_PER_FRAM_BANK = FRAM_BANK_SIZE // BYTES_PER_BLOCK  # 32 blocks per FRAM bank
NUM_FRAM_BANKS = 4  # Total of 32KB FRAM


class CmdId(IntEnum):
    """Command IDs for CartClinic protocol."""
    
    Loopback = 0x01
    ReadCartByte = 0x02
    WriteCartByte = 0x03
    WriteCartFlashByte = 0x04
    DetectCart = 0x05
    SetFrameBufferPixel = 0x06
    SetPSRAMAddress = 0x07
    WritePSRAMData = 0x08
    ReadPSRAMData = 0x09
    StartAudioPlayback = 0x0A
    StopAudioPlayback = 0x0B


class ReplyPayloadLen(IntEnum):
    """Expected reply payload lengths for each command."""
    
    Loopback = 4
    ReadCartByte = 2
    WriteCartByte = 1
    WriteCartFlashByte = 2
    DetectCart = 1
    SetFrameBufferPixel = 1
    SetPSRAMAddress = 1
    WritePSRAMData = 1
    ReadPSRAMData = 1
    StartAudioPlayback = 1
    StopAudioPlayback = 1


class FlashChipType(IntEnum):
    """Supported flash chip types."""
    
    UNKNOWN = 0
    SST39VF1681 = 1
    S29JL032J70 = 2
    IS29GL032 = 3
    SST39VF1682 = 4


@dataclass
class CartFlashInfo:
    """Information about a detected flash chip."""
    
    chip_type: FlashChipType
    manufacturer_id: int
    device_id: int
    capacity_kb: int
    sector_size_bytes: int
    total_sectors: int
    
    @property
    def chip_name(self) -> str:
        """Get human-readable chip name."""
        chip_names = {
            FlashChipType.SST39VF1681: "SST39VF1681",
            FlashChipType.S29JL032J70: "S29JL032J70", 
            FlashChipType.IS29GL032: "IS29GL032",
            FlashChipType.SST39VF1682: "SST39VF1682"
        }
        return chip_names.get(self.chip_type, "Unknown")
    
    @property
    def jedec_id(self) -> int:
        """Get JEDEC ID (manufacturer + device)."""
        return (self.manufacturer_id << 8) | self.device_id


@dataclass 
class ChromaticBitmap:
    """Represents a bitmap image for the Chromatic screen."""
    
    width: int = SCREEN_PIXEL_WIDTH
    height: int = SCREEN_PIXEL_HEIGHT
    data: Optional[bytes] = None
    
    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get RGB pixel value at coordinates."""
        if not self.data or x >= self.width or y >= self.height:
            return (0, 0, 0)
            
        # Assuming RGB888 format (3 bytes per pixel)
        pixel_offset = (y * self.width + x) * 3
        if pixel_offset + 2 < len(self.data):
            return (
                self.data[pixel_offset],      # R
                self.data[pixel_offset + 1],  # G  
                self.data[pixel_offset + 2]   # B
            )
        return (0, 0, 0)
    
    def set_pixel(self, x: int, y: int, rgb: Tuple[int, int, int]) -> None:
        """Set RGB pixel value at coordinates."""
        if x >= self.width or y >= self.height:
            return
            
        if not self.data:
            self.data = bytearray(self.width * self.height * 3)
            
        pixel_offset = (y * self.width + x) * 3
        if pixel_offset + 2 < len(self.data):
            self.data[pixel_offset] = rgb[0]      # R
            self.data[pixel_offset + 1] = rgb[1]  # G
            self.data[pixel_offset + 2] = rgb[2]  # B


# Flash chip identification data
FLASH_CHIP_DATABASE = {
    # JEDEC ID: (chip_type, capacity_kb, sector_size_bytes)
    0xBF48: (FlashChipType.SST39VF1681, 1024, 4096),   # SST39VF1681 - 1MB, 4KB sectors
    0x017E: (FlashChipType.S29JL032J70, 4096, 65536),  # S29JL032J70 - 4MB, 64KB sectors  
    0x9D70: (FlashChipType.IS29GL032, 4096, 65536),    # IS29GL032 - 4MB, 64KB sectors
    0xBF49: (FlashChipType.SST39VF1682, 2048, 4096),   # SST39VF1682 - 2MB, 4KB sectors
}


def identify_flash_chip(flash_data: bytes) -> Optional[CartFlashInfo]:
    """
    Identify flash chip from JEDEC identification data.
    
    Args:
        flash_data: Raw flash identification data (at least 32 bytes)
        
    Returns:
        CartFlashInfo if chip is identified, None otherwise
    """
    if len(flash_data) < 2:
        return None
        
    # Extract manufacturer and device ID from first two bytes
    manufacturer_id = flash_data[0]
    device_id = flash_data[1]
    jedec_id = (manufacturer_id << 8) | device_id
    
    # Look up chip in database
    chip_info = FLASH_CHIP_DATABASE.get(jedec_id)
    if not chip_info:
        return None
        
    chip_type, capacity_kb, sector_size_bytes = chip_info
    total_sectors = (capacity_kb * 1024) // sector_size_bytes
    
    return CartFlashInfo(
        chip_type=chip_type,
        manufacturer_id=manufacturer_id,
        device_id=device_id,
        capacity_kb=capacity_kb,
        sector_size_bytes=sector_size_bytes,
        total_sectors=total_sectors
    )