"""
CartClinic API Builder and Parser

This module provides the CartAPI_Builder and CartAPI_Parser classes for constructing
and parsing cartridge communication commands. Enhanced with improvements from the
decompiled codebase.
"""

from .protocol import (
    CmdId, CmdReadCartByte, CmdWriteCartByte, CmdWriteCartFlashByte, CmdDetectCart,
    CmdSetFrameBufferPixel, ReplyReadCartByte, ReplyWriteCartByte, 
    ReplyWriteCartFlashByte, ReplyDetectCart, ReplySetFrameBufferPixel,
    FlashChipType, CartFlashInfo
)
from .protocol.common import SCREEN_PIXEL_WIDTH

# Constants
MAX_CART_SIZE_KB = 8388608
MAX_BANK_SIZE_KB = 16384
NUM_BANKS = MAX_CART_SIZE_KB // MAX_BANK_SIZE_KB
NUM_FRAM_BANKS = 4


class CartAPI_Builder:
    """
    Builder class for constructing cartridge communication commands.
    Enhanced with FRAM support and improved error handling.
    """
    
    @staticmethod
    def set_bank(bank_num: int) -> list:
        """
        Constructs messages to switch to a specific ROM bank.
        
        Args:
            bank_num: Bank number to switch to (0-based)
            
        Returns:
            List of encoded command messages
            
        Raises:
            ValueError: If bank number exceeds maximum
        """
        if bank_num < 0 or bank_num >= NUM_BANKS:
            raise ValueError(f'Bank number {bank_num} exceeds the maximum of NUM_BANKS={NUM_BANKS}')
        
        # High bank register (0x3000)
        high_bank = CmdWriteCartByte(0x3000, (bank_num >> 8) & 0x01)
        # Low bank register (0x2100) 
        low_bank = CmdWriteCartByte(0x2100, bank_num & 0xFF)
        
        return [high_bank.encode(), low_bank.encode()]
    
    @staticmethod
    def set_bank_fram(bank_num: int) -> bytes:
        """
        Constructs message to switch to a specific FRAM bank.
        
        Args:
            bank_num: FRAM bank number to switch to (0-based)
            
        Returns:
            Encoded command message
            
        Raises:
            ValueError: If bank number exceeds maximum FRAM banks
        """
        if bank_num < 0 or bank_num >= NUM_FRAM_BANKS:
            raise ValueError(f'Bank number {bank_num} exceeds the maximum of NUM_FRAM_BANKS={NUM_FRAM_BANKS}')
        
        return CmdWriteCartByte(0x4000, bank_num).encode()
    
    @staticmethod
    def read_byte(block: int, byte_offset: int, bank_index: int = 0) -> bytes:
        """
        Constructs message to read a byte from cartridge ROM.
        
        Args:
            block: Block number within bank
            byte_offset: Byte offset within block
            bank_index: Bank index (affects address calculation)
            
        Returns:
            Encoded command message
        """
        byte_offset &= 0xFF
        block &= 0xFF
        
        if bank_index > 0:
            block |= 0x40  # Set bank bit
            
        addr = byte_offset | (block << 8)
        return CmdReadCartByte(addr).encode()
    
    @staticmethod
    def read_byte_fram(block: int, byte_offset: int) -> bytes:
        """
        Constructs message to read a byte from cartridge FRAM.
        
        Args:
            block: Block number within FRAM bank
            byte_offset: Byte offset within block
            
        Returns:
            Encoded command message
        """
        byte_offset &= 0xFF
        block = 0xA0 | (block & 0xFF)  # FRAM block marker
        
        addr = byte_offset | (block << 8)
        return CmdReadCartByte(addr).encode()
    
    @staticmethod
    def write_byte(block: int, offset: int, bank_index: int, data_byte: int) -> bytes:
        """
        Constructs message to write a byte to cartridge ROM.
        
        Args:
            block: Block number within bank
            offset: Byte offset within block
            bank_index: Bank index (affects address calculation)
            data_byte: Data byte to write
            
        Returns:
            Encoded command message
        """
        offset &= 0xFF
        block &= 0xFF
        
        if bank_index > 0:
            block |= 0x40  # Set bank bit
            
        addr = offset | (block << 8)
        return CmdWriteCartByte(addr, data_byte).encode()
    
    @staticmethod
    def write_byte_fram(block: int, offset: int, data_byte: int) -> bytes:
        """
        Constructs message to write a byte to cartridge FRAM.
        
        Args:
            block: Block number within FRAM bank
            offset: Byte offset within block
            data_byte: Data byte to write
            
        Returns:
            Encoded command message
        """
        offset &= 0xFF
        block = 0xA0 | (block & 0xFF)  # FRAM block marker
        
        addr = offset | (block << 8)
        return CmdWriteCartByte(addr, data_byte).encode()
    
    @staticmethod
    def write_flash_byte(block: int, offset: int, bank_index: int, data_byte: int) -> bytes:
        """
        Constructs message to write a byte to cartridge flash memory.
        
        Args:
            block: Block number within bank
            offset: Byte offset within block
            bank_index: Bank index (affects address calculation)
            data_byte: Data byte to write
            
        Returns:
            Encoded command message
        """
        offset &= 0xFF
        block &= 0xFF
        
        if bank_index > 0:
            block |= 0x40  # Set bank bit
            
        addr = offset | (block << 8)
        return CmdWriteCartFlashByte(addr, data_byte).encode()
    
    @staticmethod
    def get_flash_type() -> bytes:
        """
        Constructs messages to place the device into identification mode.
        Uses JEDEC standard magic numbers for flash identification.
        
        Returns:
            Encoded command messages
        """
        # JEDEC standard identification sequence
        cmd1 = CmdWriteCartByte(0x0AAA, 0xAA)  # 0x0AAA = 2730
        cmd2 = CmdWriteCartByte(0x0555, 0x55)  # 0x0555 = 1365
        cmd3 = CmdWriteCartByte(0x0AAA, 0x90)  # Enter ID mode
        
        return cmd1.encode() + cmd2.encode() + cmd3.encode()
    
    @staticmethod
    def reset_flash_controller() -> bytes:
        """
        Constructs messages to reset the device into normal mode.
        Uses JEDEC standard magic numbers.
        
        Returns:
            Encoded command messages
        """
        # JEDEC standard reset sequence
        cmd1 = CmdWriteCartByte(0x0AAA, 0xAA)
        cmd2 = CmdWriteCartByte(0x0555, 0x55)
        cmd3 = CmdWriteCartByte(0x0000, 0xF0)  # Reset command
        
        return cmd1.encode() + cmd2.encode() + cmd3.encode()
    
    @staticmethod
    def erase_flash_all() -> bytes:
        """
        Constructs messages to erase the entire flash contents.
        Uses JEDEC standard magic numbers.
        
        Returns:
            Encoded command messages
        """
        # JEDEC standard chip erase sequence
        cmd1 = CmdWriteCartByte(0x0AAA, 0xAA)
        cmd2 = CmdWriteCartByte(0x0555, 0x55)
        cmd3 = CmdWriteCartByte(0x0AAA, 0x80)  # Erase setup
        cmd4 = CmdWriteCartByte(0x0AAA, 0xAA)
        cmd5 = CmdWriteCartByte(0x0555, 0x55)
        cmd6 = CmdWriteCartByte(0x0AAA, 0x10)  # Chip erase
        
        return (cmd1.encode() + cmd2.encode() + cmd3.encode() + 
                cmd4.encode() + cmd5.encode() + cmd6.encode())
    
    @staticmethod
    def erase_flash_sector(sector_num: int, sector_size: int) -> bytes:
        """
        Constructs messages to erase a specific sector within flash.
        Uses JEDEC standard magic numbers.
        
        Args:
            sector_num: Sector number to erase
            sector_size: Size of sector in bytes
            
        Returns:
            Encoded command messages
            
        Raises:
            ValueError: If sector size is zero
        """
        if sector_size == 0:
            raise ValueError('The sector must have a non-zero size')
        
        # Calculate sector address
        sector_start_addr = sector_num * sector_size
        bank = sector_start_addr // MAX_BANK_SIZE_KB
        offset = sector_start_addr & 0x3FFF  # 16KB mask
        sector = offset >> 8
        
        if bank > 0:
            sector |= 0x40  # Set bank bit
            
        sector <<= 8
        
        # JEDEC standard sector erase sequence
        cmd1 = CmdWriteCartByte(0x0AAA, 0xAA)
        cmd2 = CmdWriteCartByte(0x0555, 0x55)
        cmd3 = CmdWriteCartByte(0x0AAA, 0x80)  # Erase setup
        cmd4 = CmdWriteCartByte(0x0AAA, 0xAA)
        cmd5 = CmdWriteCartByte(0x0555, 0x55)
        cmd6 = CmdWriteCartByte(sector, 0x30)  # Sector erase
        
        return (cmd1.encode() + cmd2.encode() + cmd3.encode() + 
                cmd4.encode() + cmd5.encode() + cmd6.encode())
    
    @staticmethod
    def detect_cart() -> bytes:
        """
        Constructs message to detect cartridge presence.
        
        Returns:
            Encoded command message
        """
        return CmdDetectCart().encode()
    
    @staticmethod
    def set_frame_buffer_pixel(x: int, y: int, color888: int) -> bytes:
        """
        Constructs message to set a pixel in the frame buffer.
        
        Args:
            x: X coordinate (0-159)
            y: Y coordinate (0-143)
            color888: RGB888 color value
            
        Returns:
            Encoded command message
        """
        addr = y * SCREEN_PIXEL_WIDTH + x
        
        # Convert RGB888 to RGB555
        r = (color888 >> 16) & 0xFF
        g = (color888 >> 8) & 0xFF
        b = color888 & 0xFF
        
        # Convert to 5-bit values
        r5 = (r >> 3) & 0x1F
        g5 = (g >> 3) & 0x1F
        b5 = (b >> 3) & 0x1F
        
        return CmdSetFrameBufferPixel(addr, r5, g5, b5).encode()
    
    @staticmethod
    def enable_ram() -> bytes:
        """
        Constructs message to enable RAM access.
        
        Returns:
            Encoded command message
        """
        return CmdWriteCartByte(0x0000, 0x0A).encode()
    
    @staticmethod
    def disable_ram() -> bytes:
        """
        Constructs message to disable RAM access.
        
        Returns:
            Encoded command message
        """
        return CmdWriteCartByte(0x0000, 0x00).encode()


class CartAPI_Parser:
    """
    Parser class for interpreting cartridge communication responses.
    Enhanced with improved error handling and flash chip identification.
    """
    
    @staticmethod
    def byte_read(response: bytes) -> tuple:
        """
        Parse byte read response.
        
        Args:
            response: Raw response bytes
            
        Returns:
            Tuple of (address, data_byte)
        """
        reply = ReplyReadCartByte()
        msg = reply.decode(response)
        addr = msg['addr'] & 0x3FFF  # Mask to 16KB
        return (addr, msg['data'])
    
    @staticmethod
    def byte_write(response: bytes) -> tuple:
        """
        Parse byte write response.
        
        Args:
            response: Raw response bytes
            
        Returns:
            Tuple of (address, data_byte)
        """
        reply = ReplyWriteCartByte()
        msg = reply.decode(response)
        return (msg['addr'], msg['data'])
    
    @staticmethod
    def byte_write_flash(response: bytes) -> tuple:
        """
        Parse flash byte write response.
        
        Args:
            response: Raw response bytes
            
        Returns:
            Tuple of (address, data_byte)
        """
        reply = ReplyWriteCartFlashByte()
        msg = reply.decode(response)
        addr = msg['addr'] & 0x3FFF  # Mask to 16KB
        return (addr, msg['data'])
    
    @staticmethod
    def cart_detection_status(response: bytes) -> tuple:
        """
        Parse cartridge detection status.
        
        Args:
            response: Raw response bytes
            
        Returns:
            Tuple of (inserted, removed) boolean flags
        """
        reply = ReplyDetectCart()
        msg = reply.decode(response)
        return (msg['inserted'] == 1, msg['removed'] == 1)
    
    @staticmethod
    def set_frame_buffer_pixel_confirmation(response: bytes) -> bool:
        """
        Parse frame buffer pixel set confirmation.
        
        Args:
            response: Raw response bytes
            
        Returns:
            True if successful
        """
        ReplySetFrameBufferPixel().decode(response)
        return True


# Export constants for use by other modules
__all__ = [
    'CartAPI_Builder',
    'CartAPI_Parser', 
    'NUM_FRAM_BANKS',
    'MAX_BANK_SIZE_KB',
    'MAX_CART_SIZE_KB',
    'NUM_BANKS'
]