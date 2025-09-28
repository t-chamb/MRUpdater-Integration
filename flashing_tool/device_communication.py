"""
Enhanced Device Communication Protocols

This module provides enhanced USB/serial communication handling for ModRetro devices,
integrating improvements from the decompiled codebase with better error detection
and recovery mechanisms.
"""

import logging
import threading
import time
import queue
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional, Dict, Any, List, Callable, Union
import usb.core
import usb.util

try:
    import serial
    from serial.tools import list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    serial = None
    list_ports = None

flashing_tool_logger = logging.getLogger('mrupdater')


class DeviceType(Enum):
    """Enumeration of supported device types"""
    CHROMATIC_FPGA = "chromatic_fpga"
    CHROMATIC_MCU = "chromatic_mcu"
    CART_CLINIC = "cart_clinic"
    UNKNOWN = "unknown"


class ConnectionState(IntEnum):
    """Device connection states"""
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    ERROR = 3
    TIMEOUT = 4


@dataclass
class DeviceInfo:
    """Information about a detected device"""
    device_type: DeviceType
    vendor_id: int
    product_id: int
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    product: Optional[str] = None
    port: Optional[str] = None
    connection_state: ConnectionState = ConnectionState.DISCONNECTED


@dataclass
class CommunicationConfig:
    """Configuration for device communication"""
    timeout: float = 5.0
    retry_count: int = 3
    retry_delay: float = 0.1
    buffer_size: int = 4096
    baud_rate: int = 115200
    enable_flow_control: bool = False
    enable_enhanced_detection: bool = True


class CommunicationError(Exception):
    """Base exception for communication errors"""
    
    def __init__(self, message: str, device_info: Optional[DeviceInfo] = None,
                 recovery_suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.device_info = device_info
        self.recovery_suggestions = recovery_suggestions or []


class DeviceNotFoundError(CommunicationError):
    """Raised when a device cannot be found"""
    pass


class ConnectionTimeoutError(CommunicationError):
    """Raised when connection times out"""
    pass


class DeviceCommunicationInterface(ABC):
    """Abstract interface for device communication"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the device"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the device"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if device is connected"""
        pass
    
    @abstractmethod
    def send_data(self, data: bytes) -> bool:
        """Send data to device"""
        pass
    
    @abstractmethod
    def receive_data(self, size: int = None) -> bytes:
        """Receive data from device"""
        pass
    
    @abstractmethod
    def get_device_info(self) -> DeviceInfo:
        """Get device information"""
        pass


class USBDeviceCommunication(DeviceCommunicationInterface):
    """Enhanced USB device communication with improved error handling"""
    
    def __init__(self, vendor_id: int, product_id: int, 
                 config: Optional[CommunicationConfig] = None):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.config = config or CommunicationConfig()
        self.device = None
        self.endpoint_in = None
        self.endpoint_out = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._lock = threading.RLock()
        self._last_error = None
    
    def connect(self) -> bool:
        """Connect to USB device with enhanced error handling"""
        with self._lock:
            try:
                self._connection_state = ConnectionState.CONNECTING
                
                # Find the device
                self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
                if self.device is None:
                    raise DeviceNotFoundError(
                        f"USB device not found (VID: {self.vendor_id:04x}, PID: {self.product_id:04x})",
                        recovery_suggestions=[
                            "Check USB connection",
                            "Verify device is powered on",
                            "Try a different USB port",
                            "Check device drivers"
                        ]
                    )
                
                # Set configuration
                try:
                    self.device.set_configuration()
                except usb.core.USBError as e:
                    if e.errno == 16:  # Device busy
                        flashing_tool_logger.warning("Device busy, attempting to detach kernel driver")
                        try:
                            if self.device.is_kernel_driver_active(0):
                                self.device.detach_kernel_driver(0)
                            self.device.set_configuration()
                        except Exception as detach_error:
                            flashing_tool_logger.error(f"Failed to detach kernel driver: {detach_error}")
                            raise
                    else:
                        raise
                
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
                
                if self.endpoint_out is None or self.endpoint_in is None:
                    raise CommunicationError(
                        "Could not find USB endpoints",
                        recovery_suggestions=["Check device compatibility", "Try reconnecting device"]
                    )
                
                self._connection_state = ConnectionState.CONNECTED
                flashing_tool_logger.info(f"Connected to USB device {self.vendor_id:04x}:{self.product_id:04x}")
                return True
                
            except Exception as e:
                self._connection_state = ConnectionState.ERROR
                self._last_error = e
                flashing_tool_logger.error(f"USB connection failed: {e}")
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
                self._connection_state = ConnectionState.DISCONNECTED
                flashing_tool_logger.info("Disconnected from USB device")
                return True
                
            except Exception as e:
                flashing_tool_logger.error(f"USB disconnection error: {e}")
                return False
    
    def is_connected(self) -> bool:
        """Check if USB device is connected"""
        return self._connection_state == ConnectionState.CONNECTED and self.device is not None
    
    def send_data(self, data: bytes) -> bool:
        """Send data to USB device with retry logic"""
        if not self.is_connected():
            return False
        
        with self._lock:
            for attempt in range(self.config.retry_count):
                try:
                    bytes_written = self.endpoint_out.write(data, timeout=int(self.config.timeout * 1000))
                    if bytes_written == len(data):
                        return True
                    else:
                        flashing_tool_logger.warning(f"Partial write: {bytes_written}/{len(data)} bytes")
                        
                except usb.core.USBTimeoutError:
                    flashing_tool_logger.warning(f"USB write timeout (attempt {attempt + 1})")
                    if attempt < self.config.retry_count - 1:
                        time.sleep(self.config.retry_delay)
                        continue
                    else:
                        self._connection_state = ConnectionState.TIMEOUT
                        return False
                        
                except usb.core.USBError as e:
                    flashing_tool_logger.error(f"USB write error: {e}")
                    self._connection_state = ConnectionState.ERROR
                    return False
            
            return False
    
    def receive_data(self, size: int = None) -> bytes:
        """Receive data from USB device with enhanced error handling"""
        if not self.is_connected():
            return b''
        
        size = size or self.config.buffer_size
        
        with self._lock:
            for attempt in range(self.config.retry_count):
                try:
                    data = self.endpoint_in.read(size, timeout=int(self.config.timeout * 1000))
                    return bytes(data)
                    
                except usb.core.USBTimeoutError:
                    flashing_tool_logger.debug(f"USB read timeout (attempt {attempt + 1})")
                    if attempt < self.config.retry_count - 1:
                        time.sleep(self.config.retry_delay)
                        continue
                    else:
                        self._connection_state = ConnectionState.TIMEOUT
                        return b''
                        
                except usb.core.USBError as e:
                    flashing_tool_logger.error(f"USB read error: {e}")
                    self._connection_state = ConnectionState.ERROR
                    return b''
            
            return b''
    
    def get_device_info(self) -> DeviceInfo:
        """Get USB device information"""
        device_info = DeviceInfo(
            device_type=DeviceType.UNKNOWN,
            vendor_id=self.vendor_id,
            product_id=self.product_id,
            connection_state=self._connection_state
        )
        
        if self.device:
            try:
                device_info.serial_number = usb.util.get_string(self.device, self.device.iSerialNumber)
                device_info.manufacturer = usb.util.get_string(self.device, self.device.iManufacturer)
                device_info.product = usb.util.get_string(self.device, self.device.iProduct)
            except Exception as e:
                flashing_tool_logger.debug(f"Could not get USB device strings: {e}")
        
        return device_info


class SerialDeviceCommunication(DeviceCommunicationInterface):
    """Enhanced serial device communication"""
    
    def __init__(self, port: str, baud_rate: int = 115200,
                 config: Optional[CommunicationConfig] = None):
        self.port = port
        self.baud_rate = baud_rate
        self.config = config or CommunicationConfig()
        self.serial_connection = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._lock = threading.RLock()
        self._last_error = None
    
    def connect(self) -> bool:
        """Connect to serial device"""
        if not SERIAL_AVAILABLE:
            flashing_tool_logger.error("Serial communication not available")
            return False
        
        with self._lock:
            try:
                self._connection_state = ConnectionState.CONNECTING
                
                self.serial_connection = serial.Serial(
                    port=self.port,
                    baudrate=self.baud_rate,
                    timeout=self.config.timeout,
                    write_timeout=self.config.timeout
                )
                
                if self.config.enable_flow_control:
                    self.serial_connection.rtscts = True
                    self.serial_connection.dsrdtr = True
                
                self._connection_state = ConnectionState.CONNECTED
                flashing_tool_logger.info(f"Connected to serial device {self.port} at {self.baud_rate} baud")
                return True
                
            except Exception as e:
                self._connection_state = ConnectionState.ERROR
                self._last_error = e
                flashing_tool_logger.error(f"Serial connection failed: {e}")
                return False
    
    def disconnect(self) -> bool:
        """Disconnect from serial device"""
        with self._lock:
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.close()
                
                self.serial_connection = None
                self._connection_state = ConnectionState.DISCONNECTED
                flashing_tool_logger.info("Disconnected from serial device")
                return True
                
            except Exception as e:
                flashing_tool_logger.error(f"Serial disconnection error: {e}")
                return False
    
    def is_connected(self) -> bool:
        """Check if serial device is connected"""
        return (self._connection_state == ConnectionState.CONNECTED and 
                self.serial_connection and self.serial_connection.is_open)
    
    def send_data(self, data: bytes) -> bool:
        """Send data to serial device"""
        if not self.is_connected():
            return False
        
        with self._lock:
            try:
                bytes_written = self.serial_connection.write(data)
                self.serial_connection.flush()
                return bytes_written == len(data)
                
            except Exception as e:
                flashing_tool_logger.error(f"Serial write error: {e}")
                self._connection_state = ConnectionState.ERROR
                return False
    
    def receive_data(self, size: int = None) -> bytes:
        """Receive data from serial device"""
        if not self.is_connected():
            return b''
        
        with self._lock:
            try:
                if size:
                    return self.serial_connection.read(size)
                else:
                    return self.serial_connection.read_all()
                    
            except Exception as e:
                flashing_tool_logger.error(f"Serial read error: {e}")
                self._connection_state = ConnectionState.ERROR
                return b''
    
    def get_device_info(self) -> DeviceInfo:
        """Get serial device information"""
        return DeviceInfo(
            device_type=DeviceType.UNKNOWN,
            vendor_id=0,
            product_id=0,
            port=self.port,
            connection_state=self._connection_state
        )


class EnhancedDeviceManager:
    """Enhanced device manager with improved detection and connection management"""
    
    # Known device configurations (enhanced from decompiled version)
    DEVICE_CONFIGS = {
        DeviceType.CHROMATIC_FPGA: {
            'vendor_id': 0x33aa,
            'product_id': 0x0120,
            'name': 'Chromatic FPGA',
            'description': 'ModRetro Chromatic FPGA Device'
        },
        DeviceType.CHROMATIC_MCU: {
            'vendor_id': 0x374e,
            'product_id': 0x0101,
            'name': 'Chromatic MCU',
            'description': 'ModRetro Chromatic MCU Device'
        },
        DeviceType.CART_CLINIC: {
            'vendor_id': 0x374e,
            'product_id': 0x0102,  # Hypothetical Cart Clinic PID
            'name': 'Cart Clinic',
            'description': 'ModRetro Cart Clinic Device'
        }
    }
    
    def __init__(self, config: Optional[CommunicationConfig] = None):
        self.config = config or CommunicationConfig()
        self._devices = {}
        self._lock = threading.RLock()
        self._detection_callbacks = []
    
    def add_detection_callback(self, callback: Callable[[DeviceInfo], None]):
        """Add callback for device detection events"""
        self._detection_callbacks.append(callback)
    
    def remove_detection_callback(self, callback: Callable[[DeviceInfo], None]):
        """Remove device detection callback"""
        if callback in self._detection_callbacks:
            self._detection_callbacks.remove(callback)
    
    def _notify_detection_callbacks(self, device_info: DeviceInfo):
        """Notify all detection callbacks"""
        for callback in self._detection_callbacks:
            try:
                callback(device_info)
            except Exception as e:
                flashing_tool_logger.error(f"Detection callback error: {e}")
    
    def detect_devices(self) -> List[DeviceInfo]:
        """Enhanced device detection with improved logic from decompiled patterns"""
        detected_devices = []
        
        # Detect USB devices with enhanced error handling
        for device_type, config in self.DEVICE_CONFIGS.items():
            try:
                device = usb.core.find(idVendor=config['vendor_id'], idProduct=config['product_id'])
                if device:
                    device_info = DeviceInfo(
                        device_type=device_type,
                        vendor_id=config['vendor_id'],
                        product_id=config['product_id'],
                        connection_state=ConnectionState.DISCONNECTED
                    )
                    
                    # Enhanced device information gathering
                    try:
                        # Try to get device strings with better error handling
                        if hasattr(device, 'iSerialNumber') and device.iSerialNumber:
                            device_info.serial_number = usb.util.get_string(device, device.iSerialNumber)
                        if hasattr(device, 'iManufacturer') and device.iManufacturer:
                            device_info.manufacturer = usb.util.get_string(device, device.iManufacturer)
                        if hasattr(device, 'iProduct') and device.iProduct:
                            device_info.product = usb.util.get_string(device, device.iProduct)
                        
                        # Enhanced device validation from decompiled patterns
                        if self.config.enable_enhanced_detection:
                            # Try to access device to ensure it's truly available
                            try:
                                _ = device.product  # This will fail if device is not accessible
                                device_info.connection_state = ConnectionState.CONNECTED
                            except (usb.core.USBError, AttributeError):
                                device_info.connection_state = ConnectionState.ERROR
                                flashing_tool_logger.debug(f"Device {device_type} found but not accessible")
                        
                    except Exception as info_ex:
                        flashing_tool_logger.debug(f"Could not get device info for {device_type}: {info_ex}")
                    
                    detected_devices.append(device_info)
                    self._notify_detection_callbacks(device_info)
                    flashing_tool_logger.debug(f"Detected {device_type}: {config['name']}")
                    
            except Exception as e:
                flashing_tool_logger.debug(f"Error detecting {device_type}: {e}")
        
        # Enhanced serial device detection
        if self.config.enable_enhanced_detection and SERIAL_AVAILABLE and list_ports:
            try:
                for port_info in list_ports.comports():
                    # Enhanced port filtering from decompiled patterns
                    if hasattr(port_info, 'device'):
                        # Skip known problematic ports (enhanced list)
                        skip_patterns = ('Bluetooth-Incoming-Port', 'wlan-debug', 'debug-console')
                        if any(port_info.device.endswith(pattern) for pattern in skip_patterns):
                            continue
                    
                    # Enhanced ModRetro device detection
                    if hasattr(port_info, 'vid') and port_info.vid:
                        # Check against all known vendor IDs
                        matching_configs = [
                            (device_type, config) for device_type, config in self.DEVICE_CONFIGS.items()
                            if config['vendor_id'] == port_info.vid
                        ]
                        
                        for device_type, config in matching_configs:
                            # More specific device type detection based on PID
                            detected_device_type = device_type
                            if hasattr(port_info, 'pid') and port_info.pid:
                                if port_info.pid == config['product_id']:
                                    detected_device_type = device_type
                                else:
                                    # Default to MCU for serial connections
                                    detected_device_type = DeviceType.CHROMATIC_MCU
                            
                            device_info = DeviceInfo(
                                device_type=detected_device_type,
                                vendor_id=port_info.vid,
                                product_id=getattr(port_info, 'pid', 0),
                                port=port_info.device,
                                serial_number=getattr(port_info, 'serial_number', None),
                                manufacturer=getattr(port_info, 'manufacturer', None),
                                product=getattr(port_info, 'product', None),
                                connection_state=ConnectionState.DISCONNECTED
                            )
                            
                            detected_devices.append(device_info)
                            self._notify_detection_callbacks(device_info)
                            flashing_tool_logger.debug(f"Detected serial device {detected_device_type}: {port_info.device}")
                            break  # Only add once per port
                        
            except Exception as e:
                flashing_tool_logger.debug(f"Error detecting serial devices: {e}")
        
        flashing_tool_logger.info(f"Device detection completed: found {len(detected_devices)} devices")
        return detected_devices
    
    def create_communication_interface(self, device_info: DeviceInfo) -> Optional[DeviceCommunicationInterface]:
        """Create appropriate communication interface for device"""
        try:
            if device_info.port:
                # Serial device
                return SerialDeviceCommunication(
                    port=device_info.port,
                    baud_rate=self.config.baud_rate,
                    config=self.config
                )
            else:
                # USB device
                return USBDeviceCommunication(
                    vendor_id=device_info.vendor_id,
                    product_id=device_info.product_id,
                    config=self.config
                )
                
        except Exception as e:
            flashing_tool_logger.error(f"Error creating communication interface: {e}")
            return None
    
    def get_device_by_type(self, device_type: DeviceType) -> Optional[DeviceInfo]:
        """Get first detected device of specified type"""
        devices = self.detect_devices()
        for device in devices:
            if device.device_type == device_type:
                return device
        return None
    
    def get_all_devices_by_type(self, device_type: DeviceType) -> List[DeviceInfo]:
        """Get all detected devices of specified type"""
        devices = self.detect_devices()
        return [device for device in devices if device.device_type == device_type]
    
    def validate_device_connection(self, device_info: DeviceInfo) -> bool:
        """
        Enhanced device connection validation
        
        Args:
            device_info: Device information to validate
            
        Returns:
            True if device connection is valid
        """
        try:
            comm_interface = self.create_communication_interface(device_info)
            if not comm_interface:
                return False
            
            # Try to connect and immediately disconnect
            if comm_interface.connect():
                comm_interface.disconnect()
                return True
            
            return False
            
        except Exception as e:
            flashing_tool_logger.debug(f"Device validation failed: {e}")
            return False
    
    def monitor_device_changes(self, callback: Callable[[List[DeviceInfo]], None], 
                             interval: float = 2.0) -> threading.Thread:
        """
        Monitor for device connection changes
        
        Args:
            callback: Function to call when devices change
            interval: Polling interval in seconds
            
        Returns:
            Thread object for the monitoring task
        """
        def monitor_loop():
            last_devices = []
            
            while True:
                try:
                    current_devices = self.detect_devices()
                    
                    # Check if device list has changed
                    if len(current_devices) != len(last_devices):
                        callback(current_devices)
                        last_devices = current_devices
                    else:
                        # Check for changes in device states
                        changed = False
                        for curr, last in zip(current_devices, last_devices):
                            if (curr.connection_state != last.connection_state or
                                curr.device_type != last.device_type):
                                changed = True
                                break
                        
                        if changed:
                            callback(current_devices)
                            last_devices = current_devices
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    flashing_tool_logger.error(f"Device monitoring error: {e}")
                    time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def get_device_capabilities(self, device_info: DeviceInfo) -> Dict[str, Any]:
        """
        Get device capabilities based on device type
        
        Args:
            device_info: Device information
            
        Returns:
            Dictionary of device capabilities
        """
        capabilities = {
            'supports_firmware_update': False,
            'supports_cartridge_operations': False,
            'supports_serial_communication': False,
            'supports_usb_communication': False,
            'max_transfer_size': 0,
            'supported_protocols': []
        }
        
        if device_info.device_type == DeviceType.CHROMATIC_FPGA:
            capabilities.update({
                'supports_firmware_update': True,
                'supports_usb_communication': True,
                'max_transfer_size': 64 * 1024,  # 64KB
                'supported_protocols': ['USB', 'FPGA_FLASH']
            })
        elif device_info.device_type == DeviceType.CHROMATIC_MCU:
            capabilities.update({
                'supports_firmware_update': True,
                'supports_serial_communication': True,
                'supports_usb_communication': bool(device_info.port is None),
                'max_transfer_size': 32 * 1024,  # 32KB
                'supported_protocols': ['SERIAL', 'ESP32', 'MCU_FLASH']
            })
        elif device_info.device_type == DeviceType.CART_CLINIC:
            capabilities.update({
                'supports_cartridge_operations': True,
                'supports_serial_communication': True,
                'supports_usb_communication': True,
                'max_transfer_size': 16 * 1024,  # 16KB
                'supported_protocols': ['SERIAL', 'USB', 'CARTRIDGE']
            })
        
        return capabilities


# Enhanced backward compatibility functions with improved error handling
def find_usb_device(vendor_id: int, product_id: int):
    """Enhanced USB device finder with better error handling (backward compatibility)"""
    try:
        device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if device:
            flashing_tool_logger.debug(f"Found USB device: VID={vendor_id:04x}, PID={product_id:04x}")
        return device
    except Exception as e:
        flashing_tool_logger.debug(f"Error finding USB device {vendor_id:04x}:{product_id:04x}: {e}")
        return None


class DeviceCommunication:
    """Main device communication class for backward compatibility"""
    
    def __init__(self, config: Optional[CommunicationConfig] = None):
        self.config = config or CommunicationConfig()
        self.device_manager = EnhancedDeviceManager(self.config)
        self._active_connections = {}
        self._lock = threading.RLock()
    
    def find_devices(self) -> List[Dict[str, Any]]:
        """Find devices and return in legacy format"""
        devices = self.device_manager.detect_devices()
        legacy_devices = []
        
        for device in devices:
            legacy_device = {
                'path': device.port or f"usb:{device.vendor_id:04x}:{device.product_id:04x}",
                'type': device.device_type.value,
                'vendor_id': device.vendor_id,
                'product_id': device.product_id,
                'serial_number': device.serial_number,
                'manufacturer': device.manufacturer,
                'product': device.product
            }
            legacy_devices.append(legacy_device)
        
        return legacy_devices
    
    def connect_to_device(self, device_path: str) -> Optional[DeviceCommunicationInterface]:
        """Connect to a device by path"""
        with self._lock:
            if device_path in self._active_connections:
                return self._active_connections[device_path]
            
            # Parse device path
            if device_path.startswith('usb:'):
                # USB device path format: usb:VVVV:PPPP
                parts = device_path.split(':')
                if len(parts) == 3:
                    vendor_id = int(parts[1], 16)
                    product_id = int(parts[2], 16)
                    
                    comm = USBDeviceCommunication(vendor_id, product_id, self.config)
                    if comm.connect():
                        self._active_connections[device_path] = comm
                        return comm
            else:
                # Serial device path
                comm = SerialDeviceCommunication(device_path, self.config.baud_rate, self.config)
                if comm.connect():
                    self._active_connections[device_path] = comm
                    return comm
            
            return None
    
    def disconnect_from_device(self, device_path: str) -> bool:
        """Disconnect from a device"""
        with self._lock:
            if device_path in self._active_connections:
                comm = self._active_connections[device_path]
                success = comm.disconnect()
                if success:
                    del self._active_connections[device_path]
                return success
            return True
    
    def get_device_info(self, device_path: str) -> Optional[Dict[str, Any]]:
        """Get device information"""
        devices = self.find_devices()
        for device in devices:
            if device['path'] == device_path:
                return device
        return None


def get_mcu_port(vendor_id: int, product_id: int) -> Optional[str]:
    """Enhanced MCU port detection with better filtering (backward compatibility)"""
    if not SERIAL_AVAILABLE or not list_ports:
        flashing_tool_logger.debug("Serial port listing not available")
        return None
    
    try:
        for entry in list_ports.comports():
            # Enhanced port filtering
            if hasattr(entry, 'device'):
                # Skip problematic ports on macOS
                if (hasattr(entry, 'device') and 
                    entry.device.endswith(('Bluetooth-Incoming-Port', 'wlan-debug'))):
                    continue
            
            # Check vendor ID match
            if hasattr(entry, 'vid') and entry.vid == vendor_id:
                flashing_tool_logger.debug(f"Found MCU port: {entry.device} (VID: {vendor_id:04x})")
                return entry.device
                
    except Exception as e:
        flashing_tool_logger.debug(f"Error scanning for MCU port: {e}")
    
    return None


def is_device_connected(vendor_id: int, product_id: int) -> bool:
    """
    Check if a specific device is connected
    
    Args:
        vendor_id: USB vendor ID
        product_id: USB product ID
        
    Returns:
        True if device is connected and accessible
    """
    try:
        # Check USB connection
        usb_device = find_usb_device(vendor_id, product_id)
        if usb_device:
            # Try to access device to ensure it's truly available
            try:
                _ = usb_device.product
                return True
            except (usb.core.USBError, AttributeError):
                pass
        
        # Check serial connection
        serial_port = get_mcu_port(vendor_id, product_id)
        if serial_port and SERIAL_AVAILABLE:
            try:
                with serial.Serial(serial_port, timeout=0.1) as ser:
                    return ser.is_open
            except Exception:
                pass
        
        return False
        
    except Exception as e:
        flashing_tool_logger.debug(f"Device connection check failed: {e}")
        return False


def get_device_info_by_ids(vendor_id: int, product_id: int) -> Optional[DeviceInfo]:
    """
    Get device information by vendor and product IDs
    
    Args:
        vendor_id: USB vendor ID
        product_id: USB product ID
        
    Returns:
        DeviceInfo object or None if not found
    """
    try:
        manager = EnhancedDeviceManager()
        devices = manager.detect_devices()
        
        for device in devices:
            if device.vendor_id == vendor_id and device.product_id == product_id:
                return device
        
        return None
        
    except Exception as e:
        flashing_tool_logger.debug(f"Error getting device info: {e}")
        return None


__all__ = [
    'DeviceType',
    'ConnectionState',
    'DeviceInfo',
    'CommunicationConfig',
    'CommunicationError',
    'DeviceNotFoundError',
    'ConnectionTimeoutError',
    'DeviceCommunicationInterface',
    'USBDeviceCommunication',
    'SerialDeviceCommunication',
    'EnhancedDeviceManager',
    'find_usb_device',
    'get_mcu_port',
    'is_device_connected',
    'get_device_info_by_ids',
]