"""
Enhanced Cartridge Writing Operations

This module provides enhanced cartridge writing functionality with improved error handling,
retry logic, verification methods, and save data writing capabilities integrated
from the decompiled codebase.
"""

import logging
import time
from typing import Optional, Callable, Union, Tuple

from .consts import BANK_SIZE, NUM_WRITE_RETRIES
from .exceptions import (
    CartridgeTooSmallError, CartridgeWriteError, InvalidCartridgeError,
    SaveWriteFailureError, CartridgeReadError
)
from .mrpatcher import GameSaveSettings
from libpyretro.cartclinic.comms import Session
from libpyretro.cartclinic.protocol import CartFlashInfo

logger = logging.getLogger('cartclinic.cartridge_write')


def write_cartridge_helper(
    session: Session,
    game_data: bytearray,
    game_save_settings: Optional[object] = None,
    animation_thread: Optional[object] = None,
    detection_thread: Optional[object] = None,
    emit_progress: Optional[Callable[[float], None]] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    verify_writes: bool = True,
    save_data: Optional[bytearray] = None
) -> bool:
    """
    Enhanced cartridge writing helper with comprehensive functionality.
    
    This function writes game data to the cartridge while continuously checking for
    cartridge presence, animating the Chromatic screen, and providing detailed
    progress reporting with enhanced error handling and verification.
    
    Args:
        session: Active CartClinic session for device communication
        game_data: Game ROM data to write to cartridge
        game_save_settings: Optional game save configuration
        animation_thread: Optional animation subprocess for screen updates
        detection_thread: Optional detection subprocess for cartridge monitoring
        emit_progress: Optional progress callback (percentage: 0-100)
        progress_callback: Optional detailed progress callback (status, current, total)
        verify_writes: Whether to verify written data
        save_data: Optional save data to write to cartridge
        
    Returns:
        True if write operation completed successfully
        
    Raises:
        InvalidCartridgeError: If cartridge cannot be identified or is invalid
        CartridgeTooSmallError: If cartridge is too small for the game data
        CartridgeWriteError: If writing operations fail
    """
    logger.info("Starting enhanced cartridge write operation")
    
    # Detect and validate flash type
    try:
        if progress_callback:
            progress_callback("Detecting flash type...", 0, 1)
            
        cart_flash_info = session.get_flash_type()
        logger.info(f"Detected cartridge: {cart_flash_info.chip_name} "
                   f"({cart_flash_info.capacity_kb}KB)")
        
        if emit_progress:
            emit_progress(2.0)  # 2% for detection
            
    except Exception as e:
        logger.error(f"Could not identify cartridge flash: {e}")
        raise InvalidCartridgeError("Failed to detect cartridge flash type") from e
    
    # Calculate sector erase parameters
    sector_erase_cadence = max(1, cart_flash_info.sector_size_bytes // BANK_SIZE)
    if sector_erase_cadence == 0:
        raise ValueError("Sectors must be erased every N banks. SECTOR_ALIGNMENT_IN_BANK=0 is invalid")
    
    # Determine write parameters
    stop_erasing_after_game = False
    if game_save_settings and hasattr(game_save_settings, 'saves_to_rom') and game_save_settings.saves_to_rom:
        stop_erasing_after_game = getattr(game_save_settings, 'save_compatible', False)
    
    num_total_banks = cart_flash_info.capacity_kb * 1024 // BANK_SIZE
    num_game_banks = len(game_data) // BANK_SIZE
    
    # Adjust for save-to-ROM games
    if stop_erasing_after_game and game_save_settings and hasattr(game_save_settings, 'offset_kb'):
        save_start_banks = game_save_settings.offset_kb * 1024 // BANK_SIZE
        logger.info(f"Game saves to ROM, erasing will stop after {save_start_banks} game banks")
    
    # Validate game data alignment
    if len(game_data) % BANK_SIZE != 0:
        raise ValueError(f"Game data must be aligned to BANK_SIZE={BANK_SIZE}")
    
    # Check cartridge capacity
    if num_game_banks > num_total_banks:
        logger.error(f"Cartridge is too small: needs {num_game_banks} banks, has {num_total_banks} banks")
        raise CartridgeTooSmallError(num_game_banks, num_total_banks)
    
    logger.info(f"Writing {len(game_data)} bytes ({num_game_banks} banks) to cartridge")
    
    # Main write operation
    op_start = time.monotonic()
    
    try:
        for bank in range(num_total_banks):
            bank_start_time = time.monotonic()
            
            # Update progress reporting
            if progress_callback:
                if bank < num_game_banks:
                    progress_callback(f"Writing bank {bank + 1}/{num_game_banks}...", bank, num_game_banks)
                else:
                    progress_callback(f"Erasing bank {bank + 1}/{num_total_banks}...", bank, num_total_banks)
            
            logger.debug(f"Processing bank {bank} of {num_total_banks}")
            
            # Run detection and animation if available
            if detection_thread:
                try:
                    detection_thread.run_once()
                except Exception as e:
                    logger.warning(f"Detection thread error: {e}")
            
            if animation_thread:
                try:
                    animation_thread.run_once()
                except Exception as e:
                    logger.warning(f"Animation error: {e}")
            
            # Erase sector if needed
            if bank % sector_erase_cadence == 0:
                should_erase = True
                if stop_erasing_after_game and bank >= num_game_banks:
                    should_erase = False
                
                if should_erase:
                    logger.info(f"Erasing sector starting at bank {bank}")
                    
                    # Handle special case for Infineon S29JL032J70 chip
                    if (hasattr(cart_flash_info, 'chip_type') and 
                        'S29JL032J70' in str(cart_flash_info.chip_type) and bank == 0):
                        
                        # Erase 8KB sectors for this specific chip
                        for i in range(8):
                            if not session.erase_flash_sector(i, 8192):
                                logger.error(f"Erasing S29JL032J70 8K sector {i} failed")
                                raise CartridgeWriteError(f"Sector erase failed at sector {i}")
                            logger.info(f"Erased 8K sector {i} OK")
                    else:
                        # Standard sector erase
                        sector_num = bank // sector_erase_cadence
                        sector_size = sector_erase_cadence * BANK_SIZE
                        
                        if not session.erase_flash_sector(sector_num, sector_size):
                            logger.error(f"Erasing sector {sector_num} failed")
                            raise CartridgeWriteError(f"Sector erase failed at sector {sector_num}")
                        
                        logger.info(f"Erased sector {sector_num} OK")
            
            # Write game data if within game banks
            if bank < num_game_banks:
                chunk_start = bank * BANK_SIZE
                chunk_end = chunk_start + BANK_SIZE
                chunk = game_data[chunk_start:chunk_end]
                
                logger.debug(f"Writing bank {bank} ({len(chunk)} bytes)")
                
                # Write bank with progress callback
                def bank_progress(current_block, total_blocks):
                    if emit_progress:
                        bank_progress_pct = (current_block / total_blocks) * (90.0 / num_total_banks)
                        total_progress = 2.0 + (bank / num_total_banks) * 90.0 + bank_progress_pct
                        emit_progress(min(total_progress, 95.0))
                
                success = write_single_flash_bank(
                    session, bank, chunk, 
                    verify_writes=verify_writes,
                    progress_callback=bank_progress
                )
                
                if not success:
                    raise CartridgeWriteError(f"Failed to write bank {bank}")
                
                bank_elapsed = time.monotonic() - bank_start_time
                logger.debug(f"Bank {bank} written in {bank_elapsed:.2f}s")
            
            # Update overall progress
            if emit_progress:
                progress = 2.0 + ((bank + 1) / num_total_banks) * 90.0
                emit_progress(min(progress, 95.0))
    
    except Exception as e:
        logger.error(f"Cartridge writing failed: {e}")
        raise CartridgeWriteError("Cartridge write operation failed") from e
    
    # Write save data if provided
    if save_data:
        try:
            if progress_callback:
                progress_callback("Writing save data...", 0, 1)
            
            logger.info("Writing save data...")
            success = write_save_data(session, save_data)
            
            if not success:
                logger.warning("Save data write failed")
                # Don't fail the entire operation for save data errors
            else:
                logger.info(f"Successfully wrote {len(save_data)} bytes of save data")
                
        except Exception as e:
            logger.warning(f"Save data writing failed: {e}")
            # Don't fail the entire operation for save data errors
    
    total_elapsed = time.monotonic() - op_start
    logger.info(f"Cartridge write completed in {total_elapsed:.2f}s")
    
    # Final progress update
    if emit_progress:
        emit_progress(100.0)
    
    if progress_callback:
        progress_callback("Write complete!", 1, 1)
    
    logger.info("Cartridge write operation completed successfully")
    return True


def write_single_flash_bank(
    session: Session, 
    bank: int, 
    data: bytearray,
    verify_writes: bool = True,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Writes and verifies a single 16KB bank to the cartridge flash with enhanced retry logic.
    
    Args:
        session: Active CartClinic session
        bank: Bank number to write (0-based)
        data: Data to write (must be BANK_SIZE bytes)
        verify_writes: Whether to verify written data
        progress_callback: Optional progress callback (current_block, total_blocks)
        
    Returns:
        True if write operation completed successfully
        
    Raises:
        CartridgeWriteError: If the bank write operation fails after all retries
    """
    if len(data) != BANK_SIZE:
        raise ValueError(f"Data must be exactly {BANK_SIZE} bytes, got {len(data)} bytes")
    
    logger.debug(f"Writing bank {bank} ({len(data)} bytes)")
    
    write_tries = 1
    last_error = None
    
    while write_tries <= NUM_WRITE_RETRIES:
        try:
            # Write bank data
            bank_readback = session.write_bank(bank, data, progress_callback=progress_callback)
            
            if verify_writes:
                # Verify write amount
                if len(bank_readback) != BANK_SIZE:
                    raise CartridgeWriteError(
                        f"[Bank {bank}] Failed to write back all data, "
                        f"expected={BANK_SIZE}, actual={len(bank_readback)}"
                    )
                
                logger.debug(f"[Bank {bank}] Write amount OK")
                
                # Verify write data
                for i, (original, written) in enumerate(zip(data, bank_readback)):
                    if original != written:
                        raise CartridgeWriteError(
                            f"[Bank {bank}] Write verification failed at offset {i}: "
                            f"expected 0x{original:02x}, got 0x{written:02x}"
                        )
                
                logger.debug(f"[Bank {bank}] Write verification passed")
            
            logger.info(f"[Bank {bank}] Write successful on attempt {write_tries}")
            return True
            
        except Exception as e:
            last_error = e
            logger.warning(
                f"[Bank {bank}] [Attempt {write_tries}/{NUM_WRITE_RETRIES}] "
                f"Write failed with exception: {e}"
            )
            
            write_tries += 1
            
            if write_tries <= NUM_WRITE_RETRIES:
                # Brief delay before retry
                time.sleep(0.1)
            else:
                break
    
    # All retries exhausted
    logger.error(f"[Bank {bank}] Write failed after {NUM_WRITE_RETRIES} attempts")
    raise CartridgeWriteError(
        f"[Bank {bank}] Write failed after {NUM_WRITE_RETRIES} attempts"
    ) from last_error


def write_save_data(session: Session, save_data: bytearray) -> bool:
    """
    Write save data to cartridge FRAM/SRAM with enhanced error handling.
    
    Args:
        session: Active CartClinic session
        save_data: Save data to write
        
    Returns:
        True if save data was written successfully
        
    Raises:
        SaveWriteFailureError: If save data writing fails
    """
    logger.info(f"Writing {len(save_data)} bytes of save data")
    
    try:
        # Check if cartridge supports FRAM/SRAM
        has_fram = session.detect_fram()
        
        if not has_fram:
            logger.warning("No FRAM detected, cartridge may not support save data")
            return False
        
        logger.info("FRAM detected, writing save data...")
        
        # Write FRAM data (implementation depends on session having write_fram method)
        if hasattr(session, 'write_fram'):
            success = session.write_fram(save_data)
            
            if success:
                logger.info(f"Successfully wrote {len(save_data)} bytes of save data")
                
                # Verify save data if possible
                if hasattr(session, 'read_fram'):
                    try:
                        readback_data = session.read_fram()
                        if readback_data and readback_data[:len(save_data)] == save_data:
                            logger.info("Save data verification passed")
                        else:
                            logger.warning("Save data verification failed")
                            return False
                    except Exception as e:
                        logger.warning(f"Save data verification error: {e}")
                
                return True
            else:
                logger.error("Save data write operation failed")
                return False
        else:
            logger.warning("Session does not support FRAM writing")
            return False
            
    except Exception as e:
        logger.error(f"Save data writing failed: {e}")
        raise SaveWriteFailureError("Save data write operation failed") from e


def verify_cartridge_write(session: Session, original_data: bytearray, 
                          progress_callback: Optional[Callable[[str, int, int], None]] = None) -> bool:
    """
    Verify that cartridge data matches the original data.
    
    Args:
        session: Active CartClinic session
        original_data: Original data that was written
        progress_callback: Optional progress callback
        
    Returns:
        True if verification passes, False otherwise
        
    Raises:
        CartridgeReadError: If reading for verification fails
    """
    logger.info("Verifying cartridge write...")
    
    try:
        num_banks = len(original_data) // BANK_SIZE
        
        for bank in range(num_banks):
            if progress_callback:
                progress_callback(f"Verifying bank {bank + 1}/{num_banks}...", bank, num_banks)
            
            # Read bank data
            bank_data = session.read_bank(bank)
            
            # Compare with original
            start_offset = bank * BANK_SIZE
            end_offset = start_offset + BANK_SIZE
            original_bank = original_data[start_offset:end_offset]
            
            if bank_data != original_bank:
                logger.error(f"Verification failed at bank {bank}")
                
                # Find first difference for debugging
                for i, (orig, read) in enumerate(zip(original_bank, bank_data)):
                    if orig != read:
                        logger.error(f"First difference at bank {bank}, offset {i}: "
                                   f"expected 0x{orig:02x}, got 0x{read:02x}")
                        break
                
                return False
            
            logger.debug(f"Bank {bank} verification passed")
        
        logger.info("Cartridge write verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Cartridge verification failed: {e}")
        raise CartridgeReadError("Cartridge verification read failed") from e


def erase_cartridge(session: Session, 
                   progress_callback: Optional[Callable[[str, int, int], None]] = None) -> bool:
    """
    Erase entire cartridge flash memory.
    
    Args:
        session: Active CartClinic session
        progress_callback: Optional progress callback
        
    Returns:
        True if erase operation completed successfully
        
    Raises:
        CartridgeWriteError: If erase operation fails
    """
    logger.info("Starting full cartridge erase...")
    
    try:
        if progress_callback:
            progress_callback("Erasing cartridge...", 0, 1)
        
        # Use session's erase_flash_all method if available
        if hasattr(session, 'erase_flash_all'):
            success = session.erase_flash_all()
            
            if success:
                logger.info("Cartridge erase completed successfully")
                return True
            else:
                logger.error("Cartridge erase failed")
                raise CartridgeWriteError("Full cartridge erase failed")
        else:
            logger.warning("Session does not support full erase operation")
            return False
            
    except Exception as e:
        logger.error(f"Cartridge erase failed: {e}")
        raise CartridgeWriteError("Cartridge erase operation failed") from e
    finally:
        if progress_callback:
            progress_callback("Erase complete!", 1, 1)


__all__ = [
    'write_cartridge_helper',
    'write_single_flash_bank',
    'write_save_data',
    'verify_cartridge_write',
    'erase_cartridge'
]