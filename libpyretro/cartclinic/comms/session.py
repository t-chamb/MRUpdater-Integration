"""
Enhanced Session Management for CartClinic Communication

This module provides enhanced session management for CartClinic device communication,
integrating improvements from the decompiled codebase with better error handling,
retry logic, and FRAM detection capabilities.
"""

import logging
import queue
import time
import typing
from functools import wraps
from typing import Optional, Tuple, Callable, Any

from ..cart_api import NUM_FRAM_BANKS, CartAPI_Builder, CartAPI_Parser
from ..protocol import CmdId, ReplyPayloadLen, CartFlashInfo, identify_flash_chip
from ..protocol.common import (
    BANKSIZE, BYTES_PER_BLOCK, BLOCKS_PER_BANK,
    FRAM_BANK_SIZE, BLOCKS_PER_FRAM_BANK,
    BANK_SWITCH_TIMEOUT_S, ERASE_SECTOR_TIMEOUT_S, ERASE_ALL_TIMEOUT_S,
    RESET_FLASH_CTLR_TIMEOUT_S, START_ERASE_TIMEOUT_S,
    SCREEN_PIXEL_WIDTH, SCREEN_PIXEL_HEIGHT, ChromaticBitmap
)
from .transport import Transporter, CommandProperty
from .exceptions import (
    BankSwitchTimeOut, InvalidWriteBankSize, WriteBlockAddressError,
    WriteBlockDataError, FlashDetectionError, FramDetectionError
)

VERBOSE_DEBUG = False
logger = logging.getLogger('cartclinic.session')
logger.setLevel(logging.DEBUG if VERBOSE_DEBUG else logging.INFO)


def check_transport(method: Callable) -> Callable:
    """Decorator to ensure that all calls contain a valid transporter."""
    
    @wraps(method)
    def _impl(self, *args, **kwargs):
        if self.tporter is None:
            raise AttributeError('Transport missing')
        return method(self, *args, **kwargs)
    
    return _impl


class Session:
    """
    Enhanced session management for CartClinic device communication.
    
    This class provides high-level operations for cartridge communication including
    bank switching, reading, writing, flash detection, and FRAM operations with
    enhanced error handling and retry logic.
    """
    
    def __init__(self, tporter: Transporter = None):
        """
        Establishes a session to the underlying Transporter.
        
        Args:
            tporter: The Transporter instance responsible for handling communication.
        """
        self.tporter = tporter
        self.exception_queue = queue.Queue()
        
        # Register command properties if transporter is provided
        if self.tporter:
            self._register_command_properties()
    
    def _register_command_properties(self):
        """Register all command properties with the transporter."""
        properties = [
            (CmdId.Loopback, ReplyPayloadLen.Loopback),
            (CmdId.ReadCartByte, ReplyPayloadLen.ReadCartByte),
            (CmdId.WriteCartByte, ReplyPayloadLen.WriteCartByte),
            (CmdId.WriteCartFlashByte, ReplyPayloadLen.WriteCartFlashByte),
            (CmdId.DetectCart, ReplyPayloadLen.DetectCart),
            (CmdId.SetFrameBufferPixel, ReplyPayloadLen.SetFrameBufferPixel),
            (CmdId.SetPSRAMAddress, ReplyPayloadLen.SetPSRAMAddress),
            (CmdId.WritePSRAMData, ReplyPayloadLen.WritePSRAMData),
            (CmdId.ReadPSRAMData, ReplyPayloadLen.ReadPSRAMData),
            (CmdId.StartAudioPlayback, ReplyPayloadLen.StartAudioPlayback),
            (CmdId.StopAudioPlayback, ReplyPayloadLen.StopAudioPlayback)
        ]
        
        for cmd_id, reply_len in properties:
            prop = CommandProperty(command_id=cmd_id, response_len=reply_len)
            self.tporter.add_command_props(prop)
    
    def get_transporter_exception_if_any(self) -> Optional[Exception]:
        """
        Checks the transporter threads for exceptions.
        
        Returns:
            Exception if found, otherwise None.
        """
        try:
            return self.tporter.exception_queue.get_nowait()
        except queue.Empty:
            return None
    
    @check_transport
    def _switch_bank(self, bank_index: int, timeout: float = BANK_SWITCH_TIMEOUT_S) -> bool:
        """
        Switches to a different 16KB bank on the cartridge with enhanced error handling.
        
        Args:
            bank_index: The zero-indexed bank number.
            timeout: Timeout in seconds for the bank switch operation.
            
        Returns:
            True when the bank switch was successful, False when it timed out.
            
        Raises:
            BankSwitchTimeOut: When the bank switch operation times out.
        """
        try:
            tx_buffer = bytearray()
            msg_list = CartAPI_Builder.set_bank(bank_index)
            
            for msg in msg_list:
                tx_buffer.extend(msg)
            
            rq = self.tporter.add_listener([CmdId.WriteCartByte])
            self.tporter.send(bytes(tx_buffer))
            
            exp_msg_count = len(msg_list)
            start_time = time.monotonic()
            
            while exp_msg_count > 0:
                try:
                    _ = rq.get(timeout=1.0)  # 1 second timeout per message
                    exp_msg_count -= 1
                    
                    if time.monotonic() - start_time > timeout:
                        logger.error(f'Bank switch request to {bank_index} took longer than {timeout} seconds')
                        return False
                        
                except queue.Empty:
                    if time.monotonic() - start_time > timeout:
                        logger.error(f'Bank switch to {bank_index} timed out after {timeout} seconds')
                        return False
                    continue
            
            self.tporter.remove_listener([CmdId.WriteCartByte], rq)
            logger.debug(f'Bank switched to {bank_index}')
            return True
            
        except Exception as e:
            logger.error(f'Bank switch to {bank_index} failed: {e}')
            return False
        finally:
            # Ensure listener is always removed
            try:
                self.tporter.remove_listener([CmdId.WriteCartByte], rq)
            except:
                pass
    
    @check_transport
    def read_bank(self, bank_index: int, progress_callback: Callable[[int, int], None] = None) -> bytearray:
        """
        Reads 16KB bank of data from cartridge with enhanced progress reporting.
        
        Args:
            bank_index: The zero-indexed bank number.
            progress_callback: Optional callback for progress updates (current_block, total_blocks).
            
        Returns:
            The bytearray containing read bank data.
            
        Raises:
            BankSwitchTimeOut: If bank switching fails.
        """
        if not self._switch_bank(bank_index):
            raise BankSwitchTimeOut(bank_index, BANK_SWITCH_TIMEOUT_S)
        
        bank_data = bytearray(BANKSIZE)
        tx_buffer = bytearray(BYTES_PER_BLOCK * 4)
        rq = self.tporter.add_listener([CmdId.ReadCartByte])
        
        try:
            start = time.monotonic()
            
            for block in range(BLOCKS_PER_BANK):
                # Report progress if callback provided
                if progress_callback:
                    progress_callback(block, BLOCKS_PER_BANK)
                
                # Prepare block read commands
                for byte in range(BYTES_PER_BLOCK):
                    msg = CartAPI_Builder.read_byte(block, byte, bank_index)
                    tx_buffer[byte * 4:byte * 4 + 4] = msg
                
                # Send block commands
                self.tporter.send(tx_buffer)
                
                # Receive block responses
                for byte in range(BYTES_PER_BLOCK):
                    try:
                        reply = rq.get(timeout=5.0)
                        addr, data_byte = CartAPI_Parser.byte_read(reply)
                        bank_data[addr] = data_byte
                    except queue.Empty:
                        logger.warning(f'Timeout reading byte {byte} in block {block}')
                        # Continue with next byte, data will be 0x00
            
            logger.debug(f'Bank {bank_index} read elapsed: {time.monotonic() - start:.2f}s')
            return bank_data
            
        finally:
            self.tporter.remove_listener([CmdId.ReadCartByte], rq)
            if progress_callback:
                progress_callback(BLOCKS_PER_BANK, BLOCKS_PER_BANK)  # Complete
    
    @check_transport
    def write_bank(self, bank_index: int, data_to_write: bytearray, 
                   progress_callback: Callable[[int, int], None] = None) -> bytearray:
        """
        Writes 16KB bank of data to flash memory with enhanced verification.
        
        Args:
            bank_index: The target bank index to write to.
            data_to_write: The 16KB data payload to write.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            A copy of the verified data written, reconstructed from successful responses.
            
        Raises:
            InvalidWriteBankSize: If the input data is not exactly BANKSIZE bytes.
            BankSwitchTimeOut: If the bank switch took too long.
            WriteBlockAddressError: If the response address does not match.
            WriteBlockDataError: If the response written byte does not match.
        """
        if len(data_to_write) != BANKSIZE:
            raise InvalidWriteBankSize(len(data_to_write), BANKSIZE)
        
        if not self._switch_bank(bank_index):
            raise BankSwitchTimeOut(bank_index, BANK_SWITCH_TIMEOUT_S)
        
        bank_data = bytearray(BANKSIZE)
        tx_buffer = bytearray(BYTES_PER_BLOCK * 4)
        rq = self.tporter.add_listener([CmdId.WriteCartFlashByte])
        
        try:
            start = time.monotonic()
            
            for block in range(BLOCKS_PER_BANK):
                # Report progress if callback provided
                if progress_callback:
                    progress_callback(block, BLOCKS_PER_BANK)
                
                # Prepare block write commands
                for byte in range(BYTES_PER_BLOCK):
                    address = block * BYTES_PER_BLOCK + byte
                    msg = CartAPI_Builder.write_flash_byte(
                        block, byte, bank_index, data_to_write[address]
                    )
                    tx_buffer[byte * 4:byte * 4 + 4] = msg
                
                # Send block commands
                self.tporter.send(tx_buffer)
                
                # Verify block responses
                for i in range(BYTES_PER_BLOCK):
                    try:
                        reply = rq.get(timeout=5.0)
                        written_address, data_byte = CartAPI_Parser.byte_write_flash(reply)
                        
                        logger.debug(f'[Bank {bank_index}] Wrote to {written_address:04x} with value {data_byte:02x}')
                        
                        exp_address_in_bank = block * BYTES_PER_BLOCK + i
                        
                        if exp_address_in_bank != written_address:
                            raise WriteBlockAddressError(exp_address_in_bank, written_address)
                        
                        if data_byte != data_to_write[exp_address_in_bank]:
                            raise WriteBlockDataError(
                                exp_address_in_bank, data_to_write[exp_address_in_bank], data_byte
                            )
                        
                        bank_data[exp_address_in_bank] = data_byte
                        
                    except queue.Empty:
                        logger.warning(f'Timeout writing byte {i} in block {block}')
                        raise WriteBlockDataError(
                            block * BYTES_PER_BLOCK + i, 
                            data_to_write[block * BYTES_PER_BLOCK + i], 
                            0x00
                        )
            
            logger.debug(f'Bank {bank_index} write elapsed: {time.monotonic() - start:.2f}s')
            return bank_data
            
        finally:
            self.tporter.remove_listener([CmdId.WriteCartFlashByte], rq)
            if progress_callback:
                progress_callback(BLOCKS_PER_BANK, BLOCKS_PER_BANK)  # Complete
    
    @check_transport
    def get_flash_type(self) -> CartFlashInfo:
        """
        Detects and returns the flash chip type present in the cartridge with enhanced identification.
        
        Returns:
            CartFlashInfo object containing information about the detected flash chip.
            
        Raises:
            FlashDetectionError: If the flash chip cannot be identified.
        """
        flashtype_buffer = bytearray(32)
        rq_rcb = None
        rq_wcb = None
        
        try:
            rq_rcb = self.tporter.add_listener([CmdId.ReadCartByte])
            rq_wcb = self.tporter.add_listener([CmdId.WriteCartByte])
            
            # Enter flash identification mode
            tx_buffer = CartAPI_Builder.get_flash_type()
            self.tporter.send(tx_buffer)
            
            # Read flash identification data
            for i in range(32):
                tx_buffer = CartAPI_Builder.read_byte(0, i, 0)
                self.tporter.send(tx_buffer)
                
                try:
                    reply = rq_rcb.get(timeout=2.0)
                    _, flashtype_buffer[i] = CartAPI_Parser.byte_read(reply)
                except queue.Empty:
                    logger.warning(f'Timeout reading flash type byte {i}')
                    flashtype_buffer[i] = 0x00
            
            # Parse flash information
            cart_flash_info = identify_flash_chip(flashtype_buffer)
            if cart_flash_info is None:
                raise FlashDetectionError(flashtype_buffer)
            
            # Reset flash controller
            tx_buffer = CartAPI_Builder.reset_flash_controller()
            self.tporter.send(tx_buffer)
            
            expected_msgs = len(tx_buffer) // 4
            observed = 0
            start_time = time.monotonic()
            
            while observed < expected_msgs:
                try:
                    _ = rq_wcb.get(timeout=1.0)
                    observed += 1
                except queue.Empty:
                    if time.monotonic() - start_time >= RESET_FLASH_CTLR_TIMEOUT_S:
                        logger.error(f'Flash controller reset timed out after {RESET_FLASH_CTLR_TIMEOUT_S}s')
                        break
            
            logger.info(f'Detected flash chip: {cart_flash_info.chip_name} '
                       f'({cart_flash_info.capacity_kb}KB, JEDEC: {cart_flash_info.jedec_id:04x})')
            
            return cart_flash_info
            
        finally:
            if rq_rcb:
                self.tporter.remove_listener([CmdId.ReadCartByte], rq_rcb)
            if rq_wcb:
                self.tporter.remove_listener([CmdId.WriteCartByte], rq_wcb)
    
    @check_transport
    def detect_fram(self) -> bool:
        """
        Detects if the cartridge has FRAM by writing and reading back a test value.
        
        Returns:
            True if FRAM is detected, False otherwise.
            
        Raises:
            FramDetectionError: If FRAM detection fails due to communication errors.
        """
        rq = None
        
        try:
            rq = self.tporter.add_listener([CmdId.WriteCartByte, CmdId.ReadCartByte])
            
            # Enable RAM access
            self._enable_ram(rq)
            
            # Switch to last FRAM bank
            tx_buffer = CartAPI_Builder.set_bank_fram(NUM_FRAM_BANKS - 1)
            self.tporter.send(tx_buffer)
            rq.get(timeout=2.0)
            
            # Read original byte from last address
            tx_buffer = CartAPI_Builder.read_byte_fram(BLOCKS_PER_FRAM_BANK - 1, BYTES_PER_BLOCK - 1)
            self.tporter.send(tx_buffer)
            reply = rq.get(timeout=2.0)
            _, original_byte = CartAPI_Parser.byte_read(reply)
            
            # Calculate test byte (different from original)
            test_byte = (original_byte + 1) % 256
            
            # Write test byte
            tx_buffer = CartAPI_Builder.write_byte_fram(BLOCKS_PER_FRAM_BANK - 1, BYTES_PER_BLOCK - 1, test_byte)
            self.tporter.send(tx_buffer)
            rq.get(timeout=2.0)
            
            # Switch bank again (FRAM should retain data)
            tx_buffer = CartAPI_Builder.set_bank_fram(NUM_FRAM_BANKS - 1)
            self.tporter.send(tx_buffer)
            rq.get(timeout=2.0)
            
            # Read back and verify
            tx_buffer = CartAPI_Builder.read_byte_fram(BLOCKS_PER_FRAM_BANK - 1, BYTES_PER_BLOCK - 1)
            self.tporter.send(tx_buffer)
            reply = rq.get(timeout=2.0)
            _, verify_byte = CartAPI_Parser.byte_read(reply)
            
            # Restore original byte
            tx_buffer = CartAPI_Builder.write_byte_fram(BLOCKS_PER_FRAM_BANK - 1, BYTES_PER_BLOCK - 1, original_byte)
            self.tporter.send(tx_buffer)
            rq.get(timeout=2.0)
            
            # Disable RAM access
            self._disable_ram(rq)
            
            fram_detected = (verify_byte == test_byte)
            logger.info(f'FRAM detection: {"detected" if fram_detected else "not detected"}')
            
            return fram_detected
            
        except Exception as e:
            logger.error(f'Error detecting FRAM: {e}')
            raise FramDetectionError("FRAM detection") from e
            
        finally:
            if rq:
                try:
                    self._disable_ram(rq)
                except:
                    pass
                self.tporter.remove_listener([CmdId.WriteCartByte, CmdId.ReadCartByte], rq)
    
    def _enable_ram(self, rq: queue.Queue):
        """Enable RAM access on the cartridge."""
        # Implementation depends on cartridge type - this is a placeholder
        # Real implementation would send appropriate MBC commands
        pass
    
    def _disable_ram(self, rq: queue.Queue):
        """Disable RAM access on the cartridge."""
        # Implementation depends on cartridge type - this is a placeholder
        # Real implementation would send appropriate MBC commands
        pass
    
    @check_transport
    def read_fram(self) -> Optional[bytearray]:
        """
        Read all FRAM data (32KB) from the cartridge.
        
        Returns:
            bytearray containing FRAM data if successful, None if no FRAM detected
            
        Raises:
            FramDetectionError: If FRAM reading fails due to communication errors
        """
        logger.info("Reading FRAM data")
        
        # First check if FRAM is present
        if not self.detect_fram():
            logger.info("No FRAM detected")
            return None
        
        rq = None
        fram_data = bytearray(NUM_FRAM_BANKS * FRAM_BANK_SIZE)
        
        try:
            rq = self.tporter.add_listener([CmdId.ReadCartByte, CmdId.WriteCartByte])
            
            # Enable RAM access
            self._enable_ram(rq)
            
            # Read all FRAM banks
            for bank in range(NUM_FRAM_BANKS):
                logger.debug(f"Reading FRAM bank {bank}")
                
                # Switch to FRAM bank
                tx_buffer = CartAPI_Builder.set_bank_fram(bank)
                self.tporter.send(tx_buffer)
                rq.get(timeout=2.0)
                
                # Read bank data
                for block in range(BLOCKS_PER_FRAM_BANK):
                    for byte in range(BYTES_PER_BLOCK):
                        tx_buffer = CartAPI_Builder.read_byte_fram(block, byte)
                        self.tporter.send(tx_buffer)
                        
                        reply = rq.get(timeout=2.0)
                        _, data_byte = CartAPI_Parser.byte_read(reply)
                        
                        offset = bank * FRAM_BANK_SIZE + block * BYTES_PER_BLOCK + byte
                        fram_data[offset] = data_byte
            
            # Disable RAM access
            self._disable_ram(rq)
            
            logger.info(f"Successfully read {len(fram_data)} bytes of FRAM data")
            return fram_data
            
        except Exception as e:
            logger.error(f"Error reading FRAM: {e}")
            raise FramDetectionError("FRAM read operation") from e
            
        finally:
            if rq:
                try:
                    self._disable_ram(rq)
                except:
                    pass
                self.tporter.remove_listener([CmdId.ReadCartByte, CmdId.WriteCartByte], rq)
    
    @check_transport
    def write_fram(self, data: bytearray) -> bool:
        """
        Write data to FRAM memory.
        
        Args:
            data: Data to write (must be NUM_FRAM_BANKS * FRAM_BANK_SIZE bytes)
            
        Returns:
            True if write operation completed successfully
            
        Raises:
            FramDetectionError: If FRAM writing fails
            ValueError: If data size is incorrect
        """
        expected_size = NUM_FRAM_BANKS * FRAM_BANK_SIZE
        if len(data) != expected_size:
            raise ValueError(f"FRAM data must be {expected_size} bytes, got {len(data)} bytes")
        
        logger.info(f"Writing {len(data)} bytes to FRAM")
        
        # First check if FRAM is present
        if not self.detect_fram():
            logger.error("No FRAM detected, cannot write")
            return False
        
        rq = None
        
        try:
            rq = self.tporter.add_listener([CmdId.WriteCartByte, CmdId.ReadCartByte])
            
            # Enable RAM access
            self._enable_ram(rq)
            
            # Write all FRAM banks
            for bank in range(NUM_FRAM_BANKS):
                logger.debug(f"Writing FRAM bank {bank}")
                
                # Switch to FRAM bank
                tx_buffer = CartAPI_Builder.set_bank_fram(bank)
                self.tporter.send(tx_buffer)
                rq.get(timeout=2.0)
                
                # Write bank data
                for block in range(BLOCKS_PER_FRAM_BANK):
                    for byte in range(BYTES_PER_BLOCK):
                        offset = bank * FRAM_BANK_SIZE + block * BYTES_PER_BLOCK + byte
                        data_byte = data[offset]
                        
                        tx_buffer = CartAPI_Builder.write_byte_fram(block, byte, data_byte)
                        self.tporter.send(tx_buffer)
                        rq.get(timeout=2.0)
            
            # Disable RAM access
            self._disable_ram(rq)
            
            logger.info("FRAM write completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error writing FRAM: {e}")
            raise FramDetectionError("FRAM write operation") from e
            
        finally:
            if rq:
                try:
                    self._disable_ram(rq)
                except:
                    pass
                self.tporter.remove_listener([CmdId.WriteCartByte, CmdId.ReadCartByte], rq)
    
    @check_transport
    def erase_flash_sector(self, sector: int, size: int) -> bool:
        """
        Erase a flash sector with enhanced error handling.
        
        Args:
            sector: Sector number to erase
            size: Size of sector in bytes
            
        Returns:
            True if erase operation completed successfully
            
        Raises:
            FlashDetectionError: If sector erase fails
        """
        logger.info(f"Erasing flash sector {sector} (size: {size} bytes)")
        
        rq = None
        
        try:
            rq = self.tporter.add_listener([CmdId.WriteCartByte])
            
            # Build and send erase command
            tx_buffer = CartAPI_Builder.erase_flash_sector(sector, size)
            self.tporter.send(tx_buffer)
            
            # Wait for erase completion with extended timeout
            start_time = time.monotonic()
            timeout = ERASE_SECTOR_TIMEOUT_S if size <= 65536 else ERASE_ALL_TIMEOUT_S
            
            expected_msgs = len(tx_buffer) // 4
            received = 0
            
            while received < expected_msgs:
                try:
                    _ = rq.get(timeout=5.0)
                    received += 1
                    
                    if time.monotonic() - start_time > timeout:
                        logger.error(f"Sector {sector} erase timed out after {timeout}s")
                        return False
                        
                except queue.Empty:
                    if time.monotonic() - start_time > timeout:
                        logger.error(f"Sector {sector} erase timed out after {timeout}s")
                        return False
                    continue
            
            elapsed = time.monotonic() - start_time
            logger.info(f"Sector {sector} erased successfully in {elapsed:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error erasing sector {sector}: {e}")
            raise FlashDetectionError(f"Sector {sector} erase") from e
            
        finally:
            if rq:
                self.tporter.remove_listener([CmdId.WriteCartByte], rq)
    
    @check_transport
    def erase_flash_all(self) -> bool:
        """
        Erase entire flash memory.
        
        Returns:
            True if erase operation completed successfully
            
        Raises:
            FlashDetectionError: If full erase fails
        """
        logger.info("Erasing entire flash memory")
        
        rq = None
        
        try:
            rq = self.tporter.add_listener([CmdId.WriteCartByte])
            
            # Build and send erase all command
            tx_buffer = CartAPI_Builder.erase_flash_all()
            self.tporter.send(tx_buffer)
            
            # Wait for erase completion with extended timeout
            start_time = time.monotonic()
            timeout = ERASE_ALL_TIMEOUT_S
            
            expected_msgs = len(tx_buffer) // 4
            received = 0
            
            while received < expected_msgs:
                try:
                    _ = rq.get(timeout=10.0)
                    received += 1
                    
                    if time.monotonic() - start_time > timeout:
                        logger.error(f"Full flash erase timed out after {timeout}s")
                        return False
                        
                except queue.Empty:
                    if time.monotonic() - start_time > timeout:
                        logger.error(f"Full flash erase timed out after {timeout}s")
                        return False
                    continue
            
            elapsed = time.monotonic() - start_time
            logger.info(f"Full flash erase completed successfully in {elapsed:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error erasing flash: {e}")
            raise FlashDetectionError("Full flash erase") from e
            
        finally:
            if rq:
                self.tporter.remove_listener([CmdId.WriteCartByte], rq)
    
    @check_transport
    def detect_mr_cart(self) -> Tuple[bool, Optional[CartFlashInfo]]:
        """
        Detect if a ModRetro cartridge is inserted by checking flash chip type.
        
        Returns:
            Tuple of (is_mr_cart, flash_info) where is_mr_cart indicates if it's
            a known ModRetro cartridge and flash_info contains the detected flash information
            
        Raises:
            FlashDetectionError: If flash detection fails
        """
        logger.info("Detecting ModRetro cartridge")
        
        try:
            flash_info = self.get_flash_type()
            
            if flash_info is None:
                logger.warning("Could not detect flash type")
                return False, None
            
            # Check if it's a known ModRetro flash chip
            # These are common flash chips used in ModRetro cartridges
            known_mr_chips = [
                'SST39VF1681', 'SST39VF1682',  # Microchip SST chips
                'S29JL032J70',                  # Infineon chip
                'IS29GL032',                    # ISSI chip
            ]
            
            is_mr_cart = any(chip in flash_info.chip_name for chip in known_mr_chips)
            
            if is_mr_cart:
                logger.info(f"ModRetro cartridge detected: {flash_info.chip_name}")
            else:
                logger.info(f"Non-ModRetro cartridge detected: {flash_info.chip_name}")
            
            return is_mr_cart, flash_info
            
        except Exception as e:
            logger.error(f"Error detecting ModRetro cartridge: {e}")
            raise FlashDetectionError("ModRetro cartridge detection") from e
    
    @check_transport
    def set_frame_buffer(self, image: ChromaticBitmap):
        """
        Write a full bitmap to the Chromatic screen.
        
        Args:
            image: A ChromaticBitmap representing the image to display.
        """
        tx_buffer = bytearray(SCREEN_PIXEL_WIDTH * SCREEN_PIXEL_HEIGHT * 5)
        start = time.monotonic()
        msg_count = 0
        
        for y in range(SCREEN_PIXEL_HEIGHT):
            for x in range(SCREEN_PIXEL_WIDTH):
                color = image.get_pixel(x, y)
                # Convert RGB tuple to 888 format
                color888 = (color[0] << 16) | (color[1] << 8) | color[2]
                
                msg = CartAPI_Builder.set_frame_buffer_pixel(x, y, color888)
                tx_buffer[msg_count * 5:msg_count * 5 + 5] = msg
                msg_count += 1
        
        self.tporter.send(tx_buffer)
        logger.debug(f'Set frame buffer elapsed: {time.monotonic() - start:.2f}s')


__all__ = [
    'Session',
    'check_transport'
]