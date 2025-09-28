"""
Enhanced Transport Layer for CartClinic Communication

This module provides the transport layer abstraction for CartClinic device communication,
integrating improvements from the decompiled codebase with enhanced error handling
and protocol management.
"""

import logging
import queue
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Dict, Any, List, Callable, Union, Tuple
# Use compatibility layer for USB and serial imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from import_compatibility import (
    USB_AVAILABLE, usb, 
    SERIAL_AVAILABLE, serial
)

logger = logging.getLogger('cartclinic.transport')


class TransportState(IntEnum):
    """Transport layer states"""
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    ERROR = 3
    TIMEOUT = 4


@dataclass
class CommandProperty:
    """Properties for a command including expected response length"""
    command_id: int
    response_len: int
    timeout: float = 5.0
    retry_count: int = 3
    
    def __post_init__(self):
        """Validate command properties"""
        if self.command_id < 0:
            raise ValueError("Command ID must be non-negative")
        if self.response_len < 0:
            raise ValueError("Response length must be non-negative")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.retry_count < 0:
            raise ValueError("Retry count must be non-negative")


class TransportError(Exception):
    """Base exception for transport layer errors"""
    
    def __init__(self, message: str, transport_context: str = None,
                 recovery_suggestions: List[str] = None):
        if transport_context:
            message = f"Transport error in {transport_context}: {message}"
        super().__init__(message)
        self.transport_context = transport_context
        self.recovery_suggestions = recovery_suggestions or []


class TransportTimeoutError(TransportError):
    """Raised when transport operations timeout"""
    pass


class TransportInterface(ABC):
    """Abstract interface for transport layer implementations"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the transport"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the transport"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected"""
        pass
    
    @abstractmethod
    def send(self, data: bytes) -> bool:
        """Send data through transport"""
        pass
    
    @abstractmethod
    def receive(self, size: int = None, timeout: float = None) -> bytes:
        """Receive data from transport"""
        pass
    
    @abstractmethod
    def get_state(self) -> TransportState:
        """Get current transport state"""
        pass


class USBTransport(TransportInterface):
    """USB transport implementation with enhanced error handling"""
    
    def __init__(self, vendor_id: int, product_id: int, 
                 timeout: float = 5.0, buffer_size: int = 4096):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.device = None
        self.endpoint_in = None
        self.endpoint_out = None
        self._state = TransportState.DISCONNECTED
        self._lock = threading.RLock()
    
    def connect(self) -> bool:
        """Connect to USB device"""
        with self._lock:
            try:
                self._state = TransportState.CONNECTING
                
                # Find device
                self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
                if self.device is None:
                    raise TransportError(
                        f"USB device not found (VID: {self.vendor_id:04x}, PID: {self.product_id:04x})",
                        "USB connection",
                        ["Check USB connection", "Verify device is powered", "Try different USB port"]
                    )
                
                # Configure device
                try:
                    self.device.set_configuration()
                except usb.core.USBError as e:
                    if e.errno == 16:  # Device busy
                        logger.warning("Device busy, attempting to detach kernel driver")
                        try:
                            if self.device.is_kernel_driver_active(0):
                                self.device.detach_kernel_driver(0)
                            self.device.set_configuration()
                        except Exception:
                            raise TransportError("Failed to configure USB device", "USB setup")
                    else:
                        raise TransportError(f"USB configuration error: {e}", "USB setup")
                
                # Find endpoints
                cfg = self.device.get_active_configuration()
                intf = cfg[(0, 0)]
                
                self.endpoint_out = usb.util.find_descriptor(
                    intf,
                    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
                )
                
                self.endpoint_in = usb.util.find_descriptor(
                    intf,
                    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
                )
                
                if not self.endpoint_out or not self.endpoint_in:
                    raise TransportError("Could not find USB endpoints", "USB setup")
                
                self._state = TransportState.CONNECTED
                logger.info(f"Connected to USB device {self.vendor_id:04x}:{self.product_id:04x}")
                return True
                
            except Exception as e:
                self._state = TransportState.ERROR
                logger.error(f"USB transport connection failed: {e}")
                return False
    
    def disconnect(self) -> bool:
        """Disconnect from USB device"""
        with self._lock:
            try:
                if self.device:
                    usb.util.dispose_resources(self.device)
                    self.device = None
                
                self.endpoint_in = None
                self.endpoint_out = None
                self._state = TransportState.DISCONNECTED
                logger.info("USB transport disconnected")
                return True
                
            except Exception as e:
                logger.error(f"USB transport disconnection error: {e}")
                return False
    
    def is_connected(self) -> bool:
        """Check if USB transport is connected"""
        return self._state == TransportState.CONNECTED and self.device is not None
    
    def send(self, data: bytes) -> bool:
        """Send data via USB"""
        if not self.is_connected():
            return False
        
        with self._lock:
            try:
                bytes_written = self.endpoint_out.write(data, timeout=int(self.timeout * 1000))
                return bytes_written == len(data)
                
            except usb.core.USBTimeoutError:
                self._state = TransportState.TIMEOUT
                logger.warning("USB send timeout")
                return False
                
            except usb.core.USBError as e:
                self._state = TransportState.ERROR
                logger.error(f"USB send error: {e}")
                return False
    
    def receive(self, size: int = None, timeout: float = None) -> bytes:
        """Receive data via USB"""
        if not self.is_connected():
            return b''
        
        size = size or self.buffer_size
        timeout = timeout or self.timeout
        
        with self._lock:
            try:
                data = self.endpoint_in.read(size, timeout=int(timeout * 1000))
                return bytes(data)
                
            except usb.core.USBTimeoutError:
                logger.debug("USB receive timeout")
                return b''
                
            except usb.core.USBError as e:
                self._state = TransportState.ERROR
                logger.error(f"USB receive error: {e}")
                return b''
    
    def get_state(self) -> TransportState:
        """Get current transport state"""
        return self._state


class SerialTransport(TransportInterface):
    """Serial transport implementation"""
    
    def __init__(self, port: str, baud_rate: int = 115200, 
                 timeout: float = 5.0, buffer_size: int = 4096):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.connection = None
        self._state = TransportState.DISCONNECTED
        self._lock = threading.RLock()
    
    def connect(self) -> bool:
        """Connect to serial port"""
        if not SERIAL_AVAILABLE:
            logger.error("Serial transport not available")
            return False
        
        with self._lock:
            try:
                self._state = TransportState.CONNECTING
                
                self.connection = serial.Serial(
                    port=self.port,
                    baudrate=self.baud_rate,
                    timeout=self.timeout,
                    write_timeout=self.timeout
                )
                
                self._state = TransportState.CONNECTED
                logger.info(f"Connected to serial port {self.port} at {self.baud_rate} baud")
                return True
                
            except Exception as e:
                self._state = TransportState.ERROR
                logger.error(f"Serial transport connection failed: {e}")
                return False
    
    def disconnect(self) -> bool:
        """Disconnect from serial port"""
        with self._lock:
            try:
                if self.connection and self.connection.is_open:
                    self.connection.close()
                
                self.connection = None
                self._state = TransportState.DISCONNECTED
                logger.info("Serial transport disconnected")
                return True
                
            except Exception as e:
                logger.error(f"Serial transport disconnection error: {e}")
                return False
    
    def is_connected(self) -> bool:
        """Check if serial transport is connected"""
        return (self._state == TransportState.CONNECTED and 
                self.connection and self.connection.is_open)
    
    def send(self, data: bytes) -> bool:
        """Send data via serial"""
        if not self.is_connected():
            return False
        
        with self._lock:
            try:
                bytes_written = self.connection.write(data)
                self.connection.flush()
                return bytes_written == len(data)
                
            except Exception as e:
                self._state = TransportState.ERROR
                logger.error(f"Serial send error: {e}")
                return False
    
    def receive(self, size: int = None, timeout: float = None) -> bytes:
        """Receive data via serial"""
        if not self.is_connected():
            return b''
        
        # Set timeout if specified
        if timeout and timeout != self.connection.timeout:
            old_timeout = self.connection.timeout
            self.connection.timeout = timeout
        else:
            old_timeout = None
        
        with self._lock:
            try:
                if size:
                    data = self.connection.read(size)
                else:
                    data = self.connection.read_all()
                
                return data
                
            except Exception as e:
                self._state = TransportState.ERROR
                logger.error(f"Serial receive error: {e}")
                return b''
            finally:
                # Restore original timeout
                if old_timeout is not None:
                    self.connection.timeout = old_timeout
    
    def get_state(self) -> TransportState:
        """Get current transport state"""
        return self._state


class Transporter:
    """
    Enhanced transporter with command management and response handling
    
    This class manages communication with CartClinic devices, handling
    command properties, response queuing, and error management.
    """
    
    def __init__(self, transport: TransportInterface):
        self.transport = transport
        self.command_properties: Dict[int, CommandProperty] = {}
        self.listeners: Dict[int, queue.Queue] = {}
        self.exception_queue = queue.Queue()
        self._lock = threading.RLock()
        self._running = False
        self._receive_thread = None
        self._response_handlers: Dict[int, Callable] = {}
    
    def add_command_props(self, command_prop: CommandProperty):
        """Add command properties for a command ID"""
        with self._lock:
            self.command_properties[command_prop.command_id] = command_prop
            logger.debug(f"Added command properties for ID {command_prop.command_id}")
    
    def remove_command_props(self, command_id: int):
        """Remove command properties for a command ID"""
        with self._lock:
            if command_id in self.command_properties:
                del self.command_properties[command_id]
                logger.debug(f"Removed command properties for ID {command_id}")
    
    def add_listener(self, command_ids: List[int]) -> queue.Queue:
        """Add listener queue for specific command IDs"""
        with self._lock:
            listener_queue = queue.Queue()
            for cmd_id in command_ids:
                if cmd_id not in self.listeners:
                    self.listeners[cmd_id] = []
                self.listeners[cmd_id].append(listener_queue)
            
            logger.debug(f"Added listener for command IDs: {command_ids}")
            return listener_queue
    
    def remove_listener(self, command_ids: List[int], listener_queue: queue.Queue = None):
        """Remove listener for specific command IDs"""
        with self._lock:
            for cmd_id in command_ids:
                if cmd_id in self.listeners:
                    if listener_queue:
                        try:
                            self.listeners[cmd_id].remove(listener_queue)
                        except ValueError:
                            pass
                    else:
                        # Remove all listeners for this command
                        self.listeners[cmd_id].clear()
                    
                    # Clean up empty listener lists
                    if not self.listeners[cmd_id]:
                        del self.listeners[cmd_id]
            
            logger.debug(f"Removed listener for command IDs: {command_ids}")
    
    def send(self, data: bytes) -> bool:
        """Send data through transport"""
        try:
            success = self.transport.send(data)
            if not success:
                self.exception_queue.put(TransportError("Failed to send data"))
            return success
            
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.exception_queue.put(e)
            return False
    
    def start_receiving(self):
        """Start the receive thread"""
        if self._running:
            return
        
        self._running = True
        self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._receive_thread.start()
        logger.info("Started transport receive thread")
    
    def stop_receiving(self):
        """Stop the receive thread"""
        self._running = False
        if self._receive_thread and self._receive_thread.is_alive():
            self._receive_thread.join(timeout=1.0)
        logger.info("Stopped transport receive thread")
    
    def _receive_loop(self):
        """Main receive loop for handling incoming data"""
        while self._running:
            try:
                if not self.transport.is_connected():
                    time.sleep(0.1)
                    continue
                
                # Receive data with short timeout to allow thread shutdown
                data = self.transport.receive(timeout=0.5)
                if data:
                    self._process_received_data(data)
                
            except Exception as e:
                logger.error(f"Receive loop error: {e}")
                self.exception_queue.put(e)
                time.sleep(0.1)
    
    def _process_received_data(self, data: bytes):
        """Process received data and distribute to listeners"""
        try:
            # Parse command ID from data (implementation depends on protocol)
            if len(data) < 1:
                return
            
            command_id = data[0]  # Simplified - actual parsing may be more complex
            
            with self._lock:
                # Send to registered listeners
                if command_id in self.listeners:
                    for listener_queue in self.listeners[command_id]:
                        try:
                            listener_queue.put_nowait(data)
                        except queue.Full:
                            logger.warning(f"Listener queue full for command {command_id}")
                
                # Call response handlers
                if command_id in self._response_handlers:
                    try:
                        self._response_handlers[command_id](data)
                    except Exception as e:
                        logger.error(f"Response handler error for command {command_id}: {e}")
        
        except Exception as e:
            logger.error(f"Error processing received data: {e}")
            self.exception_queue.put(e)
    
    def add_response_handler(self, command_id: int, handler: Callable[[bytes], None]):
        """Add response handler for a command ID"""
        with self._lock:
            self._response_handlers[command_id] = handler
            logger.debug(f"Added response handler for command {command_id}")
    
    def remove_response_handler(self, command_id: int):
        """Remove response handler for a command ID"""
        with self._lock:
            if command_id in self._response_handlers:
                del self._response_handlers[command_id]
                logger.debug(f"Removed response handler for command {command_id}")
    
    def connect(self) -> bool:
        """Connect the transport"""
        success = self.transport.connect()
        if success:
            self.start_receiving()
        return success
    
    def disconnect(self) -> bool:
        """Disconnect the transport"""
        self.stop_receiving()
        return self.transport.disconnect()
    
    def is_connected(self) -> bool:
        """Check if transport is connected"""
        return self.transport.is_connected()
    
    def get_state(self) -> TransportState:
        """Get current transport state"""
        return self.transport.get_state()
    
    def wait_for_response(self, command_id: int, timeout: float = 5.0) -> Optional[bytes]:
        """Wait for a response to a specific command"""
        listener_queue = self.add_listener([command_id])
        try:
            response = listener_queue.get(timeout=timeout)
            return response
        except queue.Empty:
            raise TransportTimeoutError(f"Timeout waiting for response to command {command_id}")
        finally:
            self.remove_listener([command_id], listener_queue)


# Factory functions for creating transports
def create_usb_transport(vendor_id: int, product_id: int, **kwargs) -> USBTransport:
    """Create USB transport instance"""
    return USBTransport(vendor_id, product_id, **kwargs)


def create_serial_transport(port: str, baud_rate: int = 115200, **kwargs) -> SerialTransport:
    """Create serial transport instance"""
    return SerialTransport(port, baud_rate, **kwargs)


def create_transporter(transport: TransportInterface) -> Transporter:
    """Create transporter instance with given transport"""
    return Transporter(transport)


class MockTransport(TransportInterface):
    """Mock transport implementation for testing"""
    
    def __init__(self, simulate_errors: bool = False):
        self.simulate_errors = simulate_errors
        self._state = TransportState.DISCONNECTED
        self._connected = False
        self.sent_data = []
        self.receive_data = queue.Queue()
        self._lock = threading.RLock()
        
        # Pre-populate with some test data
        self._populate_test_data()
    
    def _populate_test_data(self):
        """Populate mock transport with test data"""
        # Flash type response
        flash_response = bytearray([0x01, 0x00, 0x02, 0x00])  # Mock flash info
        self.receive_data.put(flash_response)
        
        # Bank data response
        bank_data = bytearray(16384)  # 16KB bank
        for i in range(len(bank_data)):
            bank_data[i] = i % 256
        self.receive_data.put(bank_data)
        
        # FRAM detection response
        fram_response = bytearray([0x01])  # FRAM detected
        self.receive_data.put(fram_response)
    
    def connect(self) -> bool:
        """Mock connect"""
        if self.simulate_errors:
            return False
        
        with self._lock:
            self._state = TransportState.CONNECTED
            self._connected = True
            return True
    
    def disconnect(self) -> bool:
        """Mock disconnect"""
        with self._lock:
            self._state = TransportState.DISCONNECTED
            self._connected = False
            return True
    
    def is_connected(self) -> bool:
        """Check if mock transport is connected"""
        return self._connected
    
    def send(self, data: bytes) -> bool:
        """Mock send - store sent data"""
        if not self.is_connected():
            return False
        
        if self.simulate_errors:
            return False
        
        with self._lock:
            self.sent_data.append(bytes(data))
            return True
    
    def receive(self, size: int = None, timeout: float = None) -> bytes:
        """Mock receive - return queued data"""
        if not self.is_connected():
            return b''
        
        if self.simulate_errors:
            return b''
        
        try:
            data = self.receive_data.get_nowait()
            if size and len(data) > size:
                # Return only requested size and put remainder back
                remainder = data[size:]
                self.receive_data.put(remainder)
                return bytes(data[:size])
            return bytes(data)
        except queue.Empty:
            return b''
    
    def get_state(self) -> TransportState:
        """Get mock transport state"""
        return self._state
    
    def add_receive_data(self, data: bytes):
        """Add data to receive queue for testing"""
        self.receive_data.put(bytearray(data))
    
    def get_sent_data(self) -> List[bytes]:
        """Get all sent data for testing"""
        with self._lock:
            return self.sent_data.copy()
    
    def clear_sent_data(self):
        """Clear sent data history"""
        with self._lock:
            self.sent_data.clear()


def create_mock_transport(simulate_errors: bool = False) -> MockTransport:
    """Create mock transport instance for testing"""
    return MockTransport(simulate_errors)


__all__ = [
    'TransportState',
    'CommandProperty',
    'TransportError',
    'TransportTimeoutError',
    'TransportInterface',
    'USBTransport',
    'SerialTransport',
    'MockTransport',
    'Transporter',
    'create_usb_transport',
    'create_serial_transport',
    'create_mock_transport',
    'create_transporter',
]