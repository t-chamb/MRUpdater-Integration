"""
Enhanced Cartridge Reading Operations

This module provides enhanced cartridge reading functionality with improved error handling,
progress reporting, checksum validation, and save data backup capabilities integrated
from the decompiled codebase.
"""

import logging
import time
import hashlib
from typing import Optional, Callable, Tuple, Union

from .consts import BANK_SIZE
from .exceptions import InvalidCartridgeError, CartridgeReadError, ChecksumValidationError
from libpyretro.cartclinic.comms import Session
from libpyretro.cartclinic.protocol import CartFlashInfo

logger = logging.getLogger('cartclinic.cartridge_read')


def read_cartridge_helper(
    session: Session,
    animation: Optional[object] = None,
    detection_thread: Optional[object] = None,
    emit_progress: Optional[Callable[[float], None]] = None,
    include_save_data: bool = False,
    validate_checksum: bool = True,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Union[bytearray, Tuple[bytearray, bytearray]]:
    """
    Enhanced cartridge reading helper with comprehensive functionality.
    
    This function reads the full cartridge data while continuously checking for
    cartridge presence, animating the Chromatic screen, and providing detailed
    progress reporting with optional save data backup and checksum validation.
    
    Args:
        session: Active CartClinic session for device communication
        animation: Optional animation subprocess for screen updates
        detection_thread: Optional detection subprocess for cartridge monitoring
        emit_progress: Optional progress callback (percentage: 0-100)
        include_save_data: Whether to read and return save data separately
        validate_checksum: Whether to validate ROM checksum after reading
        progress_callback: Optional detailed progress callback (status, current, total)
        
    Returns:
        If include_save_data is False: bytearray containing ROM data
        If include_save_data is True: tuple of (rom_data, save_data)
        
    Raises:
        InvalidCartridgeError: If cartridge cannot be identified or is invalid
        CartridgeReadError: If reading operations fail
        ChecksumValidationError: If checksum validation fails (when enabled)
    """
    logger.info("Starting enhanced cartridge read operation")
    
    # Run initial animation if available
    if animation:
        try:
            animation.run_once()
        except Exception as e:
            logger.warning(f"Animation error: {e}")
    
    # Detect and validate flash type
    try:
        if progress_callback:
            progress_callback("Detecting flash type...", 0, 1)
            
        cart_flash_info = session.get_flash_type()
        logger.info(f"Detected cartridge: {cart_flash_info.chip_name} "
                   f"({cart_flash_info.capacity_kb}KB)")
        
        if emit_progress:
            emit_progress(5.0)  # 5% for detection
            
    except Exception as e:
        logger.error(f"Could not identify cartridge flash: {e}")
        raise InvalidCartridgeError("Failed to detect cartridge flash type") from e
    
    # Calculate reading parameters
    num_bytes_to_read = cart_flash_info.capacity_kb * 1024
    num_total_banks = num_bytes_to_read // BANK_SIZE
    cart_data = bytearray(num_bytes_to_read)
    
    logger.info(f"Reading {num_bytes_to_read} bytes ({num_total_banks} banks)")
    
    # Read ROM data with enhanced progress tracking
    op_start = time.monotonic()
    
    try:
        for bank in range(num_total_banks):
            bank_start_time = time.monotonic()
            
            # Update progress reporting
            if progress_callback:
                progress_callback(f"Reading bank {bank + 1}/{num_total_banks}...", bank, num_total_banks)
            
            logger.debug(f"Reading bank {bank} of {num_total_banks}")
            
            # Run detection and animation if available
            if detection_thread:
                try:
                    detection_thread.run_once()
                except Exception as e:
                    logger.warning(f"Detection thread error: {e}")
            
            if animation:
                try:
                    animation.run_once()
                except Exception as e:
                    logger.warning(f"Animation error: {e}")
            
            # Read bank with progress callback
            def bank_progress(current_block, total_blocks):
                if emit_progress:
                    bank_progress_pct = (current_block / total_blocks) * (90.0 / num_total_banks)
                    total_progress = 5.0 + (bank / num_total_banks) * 90.0 + bank_progress_pct
                    emit_progress(min(total_progress, 95.0))
            
            try:
                bank_data = session.read_bank(bank, progress_callback=bank_progress)
                cart_data[bank * BANK_SIZE:(bank + 1) * BANK_SIZE] = bank_data
                
                bank_elapsed = time.monotonic() - bank_start_time
                logger.debug(f"Bank {bank} read in {bank_elapsed:.2f}s")
                
            except Exception as e:
                logger.error(f"Failed to read bank {bank}: {e}")
                raise CartridgeReadError(f"Bank {bank} read failed") from e
            
            # Update overall progress
            if emit_progress:
                progress = 5.0 + ((bank + 1) / num_total_banks) * 90.0
                emit_progress(min(progress, 95.0))
    
    except Exception as e:
        logger.error(f"ROM reading failed: {e}")
        raise CartridgeReadError("ROM data reading failed") from e
    
    total_elapsed = time.monotonic() - op_start
    logger.info(f"ROM read completed in {total_elapsed:.2f}s "
               f"({num_bytes_to_read / total_elapsed / 1024:.1f} KB/s)")
    
    # Validate ROM checksum if requested
    if validate_checksum:
        try:
            if progress_callback:
                progress_callback("Validating ROM checksum...", 1, 1)
            
            if not validate_rom_checksum(cart_data):
                logger.warning("ROM checksum validation failed")
                if validate_checksum:  # Strict validation
                    raise ChecksumValidationError("ROM checksum is invalid")
            else:
                logger.info("ROM checksum validation passed")
                
        except ChecksumValidationError:
            raise
        except Exception as e:
            logger.warning(f"Checksum validation error: {e}")
    
    # Read save data if requested
    save_data = None
    if include_save_data:
        try:
            if progress_callback:
                progress_callback("Reading save data...", 0, 1)
            
            logger.info("Reading save data...")
            save_data = read_save_data(session)
            
            if save_data:
                logger.info(f"Read {len(save_data)} bytes of save data")
            else:
                logger.info("No save data found or cartridge doesn't support saves")
                
        except Exception as e:
            logger.warning(f"Save data reading failed: {e}")
            # Don't fail the entire operation for save data errors
            save_data = None
    
    # Final progress update
    if emit_progress:
        emit_progress(100.0)
    
    if progress_callback:
        progress_callback("Read complete!", 1, 1)
    
    logger.info("Cartridge read operation completed successfully")
    
    if include_save_data:
        return cart_data, save_data
    else:
        return cart_data


def read_single_flash_bank(session: Session, bank: int, 
                          progress_callback: Optional[Callable[[int, int], None]] = None) -> bytearray:
    """
    Reads a single 16KB bank from the cartridge flash with enhanced error handling.
    
    Args:
        session: Active CartClinic session
        bank: Bank number to read (0-based)
        progress_callback: Optional progress callback (current_block, total_blocks)
        
    Returns:
        bytearray containing the 16KB bank data
        
    Raises:
        CartridgeReadError: If the bank read operation fails
    """
    logger.info(f"Reading single bank {bank} from cartridge")
    
    try:
        bank_data = session.read_bank(bank, progress_callback=progress_callback)
        logger.debug(f"Successfully read bank {bank} ({len(bank_data)} bytes)")
        return bank_data
        
    except Exception as e:
        logger.error(f"Failed to read bank {bank}: {e}")
        raise CartridgeReadError(f"Single bank {bank} read failed") from e


def read_save_data(session: Session) -> Optional[bytearray]:
    """
    Read save data from cartridge FRAM/SRAM with enhanced detection.
    
    Args:
        session: Active CartClinic session
        
    Returns:
        bytearray containing save data if found, None if no save data available
        
    Raises:
        CartridgeReadError: If save data reading fails
    """
    logger.info("Attempting to read save data")
    
    try:
        # First detect if cartridge has FRAM/SRAM
        has_fram = session.detect_fram()
        
        if not has_fram:
            logger.info("No FRAM detected, cartridge may not support saves")
            return None
        
        logger.info("FRAM detected, reading save data...")
        
        # Read FRAM data (implementation depends on session having read_fram method)
        if hasattr(session, 'read_fram'):
            save_data = session.read_fram()
            
            # Check if save data contains meaningful content (not all 0x00 or 0xFF)
            if save_data and not _is_empty_save_data(save_data):
                logger.info(f"Read {len(save_data)} bytes of save data")
                return save_data
            else:
                logger.info("Save data appears to be empty")
                return None
        else:
            logger.warning("Session does not support FRAM reading")
            return None
            
    except Exception as e:
        logger.error(f"Save data reading failed: {e}")
        raise CartridgeReadError("Save data read operation failed") from e


def validate_rom_checksum(rom_data: bytearray) -> bool:
    """
    Validate ROM checksum using Game Boy header checksum algorithm.
    
    Args:
        rom_data: ROM data to validate
        
    Returns:
        True if checksum is valid, False otherwise
    """
    if len(rom_data) < 0x150:
        logger.warning("ROM too small for checksum validation")
        return False
    
    try:
        # Game Boy header checksum (0x014D)
        header_checksum = rom_data[0x014D]
        
        # Calculate checksum over header bytes 0x0134-0x014C
        calculated_checksum = 0
        for addr in range(0x0134, 0x014D):
            calculated_checksum = (calculated_checksum - rom_data[addr] - 1) & 0xFF
        
        is_valid = calculated_checksum == header_checksum
        
        if is_valid:
            logger.debug(f"ROM header checksum valid: 0x{header_checksum:02X}")
        else:
            logger.warning(f"ROM header checksum invalid: expected 0x{calculated_checksum:02X}, "
                          f"got 0x{header_checksum:02X}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Checksum validation error: {e}")
        return False


def calculate_rom_hash(rom_data: bytearray, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of ROM data for verification purposes.
    
    Args:
        rom_data: ROM data to hash
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hexadecimal hash string
    """
    try:
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        elif algorithm == 'sha256':
            hasher = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        hasher.update(rom_data)
        hash_value = hasher.hexdigest()
        
        logger.debug(f"ROM {algorithm.upper()} hash: {hash_value}")
        return hash_value
        
    except Exception as e:
        logger.error(f"Hash calculation error: {e}")
        return ""


def _is_empty_save_data(save_data: bytearray) -> bool:
    """
    Check if save data appears to be empty (all 0x00 or 0xFF).
    
    Args:
        save_data: Save data to check
        
    Returns:
        True if save data appears empty, False otherwise
    """
    if not save_data:
        return True
    
    # Check for common empty patterns
    all_zero = all(b == 0x00 for b in save_data)
    all_ff = all(b == 0xFF for b in save_data)
    
    # Also check for mostly empty (>95% same byte)
    if len(save_data) > 100:
        zero_count = save_data.count(0x00)
        ff_count = save_data.count(0xFF)
        mostly_empty = (zero_count > len(save_data) * 0.95) or (ff_count > len(save_data) * 0.95)
        return all_zero or all_ff or mostly_empty
    
    return all_zero or all_ff


__all__ = [
    'read_cartridge_helper',
    'read_single_flash_bank', 
    'read_save_data',
    'validate_rom_checksum',
    'calculate_rom_hash'
]