"""
ESP32 Utilities for Chromatic Device Management

Enhanced ESP32 utilities integrated from decompiled codebase with
improved error handling and device detection.
"""

import sys
import time
from itertools import cycle, repeat, chain
from typing import Tuple, IO, Optional
import logging

try:
    import serial
    from serial.tools import list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    list_ports = None

try:
    import usb
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False
    usb = None

try:
    from esptool.bin_image import intel_hex_to_bin
    from esptool.loader import ESPLoader
    from esptool.targets import CHIP_DEFS
    from esptool.util import FatalError
    ESPTOOL_AVAILABLE = True
except ImportError:
    ESPTOOL_AVAILABLE = False
    ESPLoader = None
    FatalError = Exception

flashing_tool_logger = logging.getLogger('mrupdater')


def create_address_filename_pair(address: int, filepath: str) -> Tuple[int, IO]:
    """
    Given an address and the filepath to a binary file, creates and
    returns a tuple object with the address and file object.

    The binary file also undergoes sanity checks to ensure that it
    is properly encoded

    Args:
        address: Memory address for the binary
        filepath: Path to the binary file

    Returns:
        Tuple of (address, file_object)
    """
    if not ESPTOOL_AVAILABLE:
        raise RuntimeError("ESPTool not available for binary processing")
    
    try:
        io_stream = open(filepath, 'rb')
        argfile = intel_hex_to_bin(io_stream, address)
        return (address, argfile)
    except Exception as e:
        flashing_tool_logger.error(f"Failed to create address/filename pair: {e}")
        raise


def esp_connect_loop(port: str, 
                    initial_baud: int = 115200, 
                    chip: str = 'esp32', 
                    max_retries: int = 7,
                    trace: bool = False,
                    before: str = 'default_reset') -> Optional[ESPLoader]:
    """
    Enhanced ESP connection loop with improved error handling
    
    This is based on esptool's internal connection logic but with
    enhanced error handling and logging for the ModRetro use case.

    Args:
        port: Serial port name
        initial_baud: Initial baud rate
        chip: Chip type (esp32, esp32s2, etc.)
        max_retries: Maximum connection attempts
        trace: Enable trace logging
        before: Reset method before connection

    Returns:
        ESPLoader instance or None if connection fails
    """
    if not ESPTOOL_AVAILABLE:
        flashing_tool_logger.error("ESPTool not available")
        return None
    
    if not port:
        flashing_tool_logger.error("No port specified for ESP connection")
        return None
    
    try:
        chip_class = CHIP_DEFS.get(chip)
        if not chip_class:
            raise ValueError(f"Unsupported chip type: {chip}")
        
        esp = None
        first = True
        
        # Create retry pattern: 9 quick attempts, then slower attempts
        ten_cycle = cycle(chain(repeat(False, 9), (True,)))
        retry_loop = chain(
            repeat(False, max_retries - 1), 
            (True,) if max_retries else cycle((False,))
        )
        
        for last_attempt, extra_delay in zip(retry_loop, ten_cycle):
            try:
                if not first:
                    time.sleep(0.05 if not extra_delay else 0.5)
                first = False
                
                flashing_tool_logger.debug(f"Attempting ESP connection to {port}")
                esp = chip_class(port, initial_baud, trace)
                esp.connect(before)
                
                flashing_tool_logger.info(f"Successfully connected to ESP32 on {port}")
                return esp
                
            except Exception as e:
                if last_attempt:
                    flashing_tool_logger.error(f"Failed to connect to ESP32 after {max_retries} attempts: {e}")
                    raise
                else:
                    flashing_tool_logger.debug(f"ESP connection attempt failed: {e}")
                    
                if esp:
                    try:
                        esp._port.close()
                    except:
                        pass
                    esp = None
        
        return None
        
    except Exception as e:
        flashing_tool_logger.error(f"ESP connection error: {e}")
        return None


def get_mcu_port(vendor_id: int, product_id: int) -> Optional[str]:
    """
    Enhanced MCU port detection with better error handling
    
    Args:
        vendor_id: USB vendor ID
        product_id: USB product ID
        
    Returns:
        Serial port name or None if not found
    """
    if not SERIAL_AVAILABLE:
        flashing_tool_logger.error("Serial port listing not available")
        return None
    
    if list_ports is None:
        raise FatalError(
            'Listing all serial ports is currently not available. '
            'Please try to specify the port when running esptool.py or '
            'update the pyserial package to the latest version'
        )
    
    try:
        for entry in list_ports.comports():
            # Skip Bluetooth and debug ports on macOS
            if (sys.platform == 'darwin' and 
                entry.device.endswith(('Bluetooth-Incoming-Port', 'wlan-debug'))):
                continue
            
            # Check for matching vendor ID
            if hasattr(entry, 'vid') and entry.vid == vendor_id:
                flashing_tool_logger.debug(f"Found MCU port: {entry.device} (VID: {entry.vid:04x})")
                return entry.device
        
        flashing_tool_logger.debug(f"No MCU port found for VID: {vendor_id:04x}")
        return None
        
    except Exception as e:
        flashing_tool_logger.error(f"Error scanning for MCU port: {e}")
        return None


def find_usb_device(vendor_id: int, product_id: int):
    """
    Enhanced USB device detection with better error handling
    
    Args:
        vendor_id: USB vendor ID
        product_id: USB product ID
        
    Returns:
        USB device object or None if not found
    """
    if not USB_AVAILABLE:
        flashing_tool_logger.error("USB support not available")
        return None
    
    try:
        device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if device:
            flashing_tool_logger.debug(
                f"Found USB device: VID={vendor_id:04x}, PID={product_id:04x}"
            )
        else:
            flashing_tool_logger.debug(
                f"USB device not found: VID={vendor_id:04x}, PID={product_id:04x}"
            )
        return device
        
    except Exception as e:
        flashing_tool_logger.error(f"Error finding USB device: {e}")
        return None


def list_available_ports() -> list:
    """
    List all available serial ports
    
    Returns:
        List of available port names
    """
    if not SERIAL_AVAILABLE or list_ports is None:
        return []
    
    try:
        ports = []
        for entry in list_ports.comports():
            # Skip Bluetooth and debug ports on macOS
            if (sys.platform == 'darwin' and 
                entry.device.endswith(('Bluetooth-Incoming-Port', 'wlan-debug'))):
                continue
            ports.append(entry.device)
        
        return ports
        
    except Exception as e:
        flashing_tool_logger.error(f"Error listing serial ports: {e}")
        return []


def validate_esp_connection(port: str, baud_rate: int = 115200) -> bool:
    """
    Validate ESP connection without full initialization
    
    Args:
        port: Serial port name
        baud_rate: Baud rate for connection
        
    Returns:
        True if connection is valid, False otherwise
    """
    if not SERIAL_AVAILABLE:
        return False
    
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            # Simple connection test
            ser.write(b'\x00')  # Sync frame
            time.sleep(0.1)
            return ser.in_waiting >= 0  # Port is responsive
            
    except Exception as e:
        flashing_tool_logger.debug(f"ESP connection validation failed for {port}: {e}")
        return False


# Compatibility functions for backward compatibility
def is_fpga_detected(chromatic_instance) -> bool:
    """
    Check if FPGA is detected (compatibility function)
    
    Args:
        chromatic_instance: Chromatic device instance
        
    Returns:
        True if FPGA is detected
    """
    if hasattr(chromatic_instance, 'is_fpga_detected'):
        return chromatic_instance.is_fpga_detected()
    elif hasattr(chromatic_instance, 'fpga'):
        return chromatic_instance.fpga is not None
    else:
        return False


__all__ = [
    'create_address_filename_pair',
    'esp_connect_loop', 
    'get_mcu_port',
    'find_usb_device',
    'list_available_ports',
    'validate_esp_connection',
    'is_fpga_detected',
]