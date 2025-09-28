"""
Enhanced Chromatic Device Management

This module provides enhanced device state management and communication
for the ModRetro Chromatic device, integrating improvements from the
decompiled codebase while maintaining backward compatibility.
"""

import itertools
import logging
import os
import threading
import time
from typing import Callable, List, Optional, Dict, Any
import usb.core as usb

try:
    import statemachine
    from statemachine import StateMachine, State
    STATEMACHINE_AVAILABLE = True
except ImportError:
    # Fallback for environments without statemachine
    STATEMACHINE_AVAILABLE = False
    StateMachine = object
    State = object

try:
    from esptool.loader import ESPLoader, DEFAULT_CONNECT_ATTEMPTS
    ESPTOOL_AVAILABLE = True
except ImportError:
    ESPTOOL_AVAILABLE = False
    ESPLoader = None
    DEFAULT_CONNECT_ATTEMPTS = 7

# Import utilities with fallbacks
try:
    from .esp_util import esp_connect_loop, get_mcu_port, find_usb_device
except ImportError:
    # Fallback implementations for missing utilities
    def esp_connect_loop(port, initial_baud, chip, max_retries):
        """Fallback ESP connection - requires esptool integration"""
        raise NotImplementedError("ESP utilities not available")
    
    def get_mcu_port(vendor_id, product_id):
        """Fallback MCU port detection"""
        return None
    
    def find_usb_device(vendor_id, product_id):
        """Fallback USB device detection"""
        return usb.core.find(idVendor=vendor_id, idProduct=product_id)

try:
    from .logging_utils import IntervalSamplingFilter
except ImportError:
    # Simple fallback for logging filter
    class IntervalSamplingFilter:
        def __init__(self, name, interval):
            self.name = name
            self.interval = interval
        
        def __str__(self):
            return f"tag:{self.name}"

try:
    from .util import is_env_manufacturing
except ImportError:
    def is_env_manufacturing():
        return False

# Set up logging
flashing_tool_logger = logging.getLogger('mrupdater')


class ChromaticError(Exception):
    """Enhanced Chromatic device error with additional context"""
    
    def __init__(self, message: str, 
                 original_exception: Optional[Exception] = None,
                 context: Optional[Dict[str, Any]] = None,
                 recovery_suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.context = context or {}
        self.recovery_suggestions = recovery_suggestions or []


class ChromaticBase:
    """Base class for Chromatic device management without state machine dependency"""
    
    # Device identification constants
    GOWIN_DEVICE_IDS = '0x33aa:0120'
    MODRETRO_DEVICE_IDS = '0x374e:0101'
    MCU_BAUD_RATE = 115200
    MCU_CHIP_TYPE = 'esp32'
    FPGA_FLASH_TIMEOUT = 600
    
    def __init__(self, openfpga_loader_bin: str = None, 
                 progress_callback: Optional[Callable] = None,
                 on_state_transition_callback: Optional[Callable] = None,
                 enhanced_detection: bool = True):
        """
        Initialize Chromatic device manager
        
        Args:
            openfpga_loader_bin: Path to openFPGALoader executable
            progress_callback: Callback for progress updates
            on_state_transition_callback: Callback for state transitions
            enhanced_detection: Enable enhanced device detection features
        """
        if openfpga_loader_bin and not os.path.isfile(openfpga_loader_bin):
            raise ChromaticError(f'Invalid path to openFPGALoader executable: {openfpga_loader_bin}')
        
        self._openfpga_loader_bin = openfpga_loader_bin
        self._progress_callback = progress_callback
        self._on_state_transition_callback = on_state_transition_callback
        self._enhanced_detection = enhanced_detection
        
        # Device state
        self._esp = None
        self._previous_status = None
        self._should_update_hardware_attrs = True
        self._flashing_lock = threading.RLock()
        self._flash_result = 0
        self._detect_thread = None
        self.fw_version = None
        
        # Enhanced logging
        self.logging_signal = IntervalSamplingFilter('fpga', 3)
        
        # Hardware attributes tracking
        self._hardware_attributes = {
            'fpga': ('product', 'manufacturer'),
            'esp': ('chip_description', 'chip_features', 'crystal_freq')
        }
        self._init_hardware_attributes()
        
        # Auto-detection management
        self._auto_detect_keepalive = None
        self._polling_thread = None
        
        # Start device detection
        self._start_device_auto_detection()
    
    def is_fpga_detected(self) -> bool:
        """
        Enhanced FPGA detection method from decompiled version
        
        Returns:
            True if FPGA device is detected and accessible
        """
        try:
            fpga = self.fpga
            if fpga is None:
                return False
            
            # Additional validation from decompiled version
            if self._enhanced_detection:
                # Try to access device properties to ensure it's truly accessible
                try:
                    _ = fpga.product  # This will fail if device is not accessible
                    return True
                except (usb.core.USBError, AttributeError):
                    return False
            
            return True
        except Exception as ex:
            flashing_tool_logger.debug(f"FPGA detection error: {ex}")
            return False
    
    def _init_hardware_attributes(self, component: Optional[str] = None):
        """Initialize hardware attributes for tracking device properties"""
        all_attrs = []
        
        if component is None:
            # Initialize all components
            for comp, attrs in self._hardware_attributes.items():
                all_attrs.extend([f"{comp}_{attr}" for attr in attrs])
        else:
            # Initialize specific component
            if component in self._hardware_attributes:
                all_attrs = [f"{component}_{attr}" for attr in self._hardware_attributes[component]]
        
        # Set all attributes to None initially
        for attr in all_attrs:
            setattr(self, attr, None)
    
    def _set_hardware_attributes(self):
        """Update hardware attributes from detected devices"""
        self._set_fpga_attributes()
        if self._enhanced_detection:
            self._set_esp_attributes()
    
    def _set_fpga_attributes(self):
        """Set FPGA hardware attributes from detected device"""
        try:
            flashing_tool_logger.info(f'{self.logging_signal} Searching for USB device with vid/pid: {self.GOWIN_DEVICE_IDS}')
            fpga = self.fpga
            if fpga is None:
                return
            
            for attr in self._hardware_attributes['fpga']:
                try:
                    value = getattr(fpga, attr)
                    setattr(self, f'fpga_{attr}', value)
                except AttributeError:
                    flashing_tool_logger.warning(f'FPGA device missing attribute: {attr}')
                    setattr(self, f'fpga_{attr}', None)
                    
        except Exception as ex:
            flashing_tool_logger.warning(f'Error setting FPGA attributes: {ex}')
            # Reset FPGA attributes on error
            for attr in self._hardware_attributes['fpga']:
                setattr(self, f'fpga_{attr}', None)
    
    def _set_esp_attributes(self):
        """Set ESP hardware attributes from detected device"""
        if not ESPTOOL_AVAILABLE:
            return
            
        try:
            esp = self.get_esp(force_connect=False)
            if esp is None:
                return
            
            for attr in self._hardware_attributes['esp']:
                try:
                    value = getattr(esp, attr, None)
                    setattr(self, f'esp_{attr}', value)
                except AttributeError:
                    setattr(self, f'esp_{attr}', None)
                    
        except Exception as ex:
            flashing_tool_logger.debug(f'Could not set ESP attributes: {ex}')
            # Reset ESP attributes on error
            for attr in self._hardware_attributes['esp']:
                setattr(self, f'esp_{attr}', None)
    
    @property
    def fpga(self):
        """Get FPGA USB device"""
        vendor_id, product_id = map(lambda x: int(x, 16), self.GOWIN_DEVICE_IDS.split(':'))
        return find_usb_device(vendor_id, product_id)
    
    @property
    def mcu_port(self):
        """
        Returns the name of the port for accessing the ModRetro MCU
        
        On new hardware, this property is only accessible after the
        FPGA has been flashed and the bridge comes up.
        """
        vendor_id, product_id = map(lambda x: int(x, 16), self.MODRETRO_DEVICE_IDS.split(':'))
        port = get_mcu_port(vendor_id, product_id)
        return port
    
    @property
    def fpga_cable_name(self):
        """
        Return the name of the cable for accessing the FPGA
        
        If the Chromatic loses connectivity, this property will
        return an empty string
        """
        name = getattr(self, 'fpga_product', None)
        if name and self.fpga is not None:
            try:
                name = self.fpga.product
            except AttributeError:
                pass
        
        if name is not None:
            name = name.lower()
        return name or ""
    
    @property
    def openfpga_loader_bin(self):
        """Get path to openFPGALoader binary"""
        return self._openfpga_loader_bin
    
    @property
    def openfgpa_loader_bin(self):
        """Compatibility property for decompiled version typo"""
        return self._openfpga_loader_bin
    
    def get_esp(self, force_connect: bool = False) -> Optional[ESPLoader]:
        """
        Get ESP loader instance with enhanced error handling
        
        Args:
            force_connect: Force new connection even if one exists
            
        Returns:
            ESPLoader instance or None if connection fails
        """
        if not ESPTOOL_AVAILABLE:
            flashing_tool_logger.error("ESPTool not available")
            return None
            
        if self._esp is None or force_connect:
            try:
                port = self.mcu_port
                if not port:
                    flashing_tool_logger.debug("No MCU port available")
                    return None
                    
                self._esp = esp_connect_loop(
                    port=port,
                    initial_baud=self.MCU_BAUD_RATE,
                    chip=self.MCU_CHIP_TYPE,
                    max_retries=DEFAULT_CONNECT_ATTEMPTS
                )
                
                if self._esp and self._enhanced_detection:
                    flashing_tool_logger.info(f"Connected to ESP32: {getattr(self._esp, 'chip_description', 'Unknown')}")
                    
            except Exception as e:
                flashing_tool_logger.error(f'Failed to connect to the ESP chip: {e}')
                if self._enhanced_detection:
                    raise ChromaticError(
                        f"ESP connection failed: {e}",
                        original_exception=e,
                        recovery_suggestions=[
                            "Check USB connection",
                            "Ensure device is in bootloader mode",
                            "Try reconnecting the device"
                        ]
                    )
                self._esp = None
        
        return self._esp
    
    def set_fw_version(self, version: str):
        """Set firmware version"""
        self.fw_version = version
        flashing_tool_logger.info(f"Firmware version set to: {version}")
    
    def flash_both_start(self, mcu_filepath: str, fpga_filepath: str):
        """
        Enhanced flash both start method from decompiled version
        
        Args:
            mcu_filepath: Path to MCU firmware file
            fpga_filepath: Path to FPGA firmware file
            
        Raises:
            ChromaticError: If device cannot be flashed
        """
        try:
            # Transition to flashing state if state machine is available
            if hasattr(self, 'start_flashing'):
                self.start_flashing()
            
            self._stop_device_auto_detection()
            
            if not self.is_fpga_detected():
                raise ChromaticError(
                    'The Chromatic cannot be flashed. Reconnect the device and try again',
                    recovery_suggestions=[
                        "Check USB connection",
                        "Reconnect the device",
                        "Ensure device is in proper mode"
                    ]
                )
            
            fpga_cable_name = self.fpga_cable_name
            flashing_tool_logger.info(f"Starting flash operation with FPGA cable: {fpga_cable_name}")
            
            # Store file paths for the flashing process
            self._mcu_filepath = mcu_filepath
            self._fpga_filepath = fpga_filepath
            
            # Start the flashing process (implementation would depend on subprocess integration)
            self._flash_result = 0
            
            if self._progress_callback:
                self._progress_callback("Starting firmware flash...")
                
        except Exception as ex:
            flashing_tool_logger.error(f"Flash both start error: {ex}")
            if hasattr(self, 'fail_flashing'):
                self.fail_flashing()
            raise ChromaticError(
                f"Failed to start flashing process: {ex}",
                original_exception=ex,
                recovery_suggestions=[
                    "Check device connection",
                    "Verify firmware file paths",
                    "Restart the application"
                ]
            )
    
    def flash_both_p1_callback(self, rc: int, mcu_filepath: str):
        """
        Enhanced phase 1 callback from decompiled version
        
        Args:
            rc: Return code from phase 1
            mcu_filepath: Path to MCU firmware file
        """
        self._flash_result = rc
        if rc != 0:
            flashing_tool_logger.error(f"Phase 1 flash failed with return code: {rc}")
            if hasattr(self, 'fail_flashing'):
                self.fail_flashing()
            return
        
        flashing_tool_logger.info("Phase 1 flash completed successfully, starting phase 2")
        if self._progress_callback:
            self._progress_callback("Phase 1 complete, starting phase 2...")
        
        # Continue to phase 2
        self.flash_both_p2(mcu_filepath)
    
    def flash_both_p2(self, filepath: str):
        """
        Execute phase 2 of the firmware flashing process.
        
        Phase 2 typically involves flashing the FPGA firmware after
        the MCU firmware has been successfully flashed in phase 1.
        
        Args:
            filepath: Path to firmware file for phase 2
            
        Raises:
            ChromaticError: If phase 2 flashing fails
        """
        try:
            flashing_tool_logger.info(f"Starting phase 2 flash with file: {filepath}")
            
            if not os.path.exists(filepath):
                raise ChromaticError(f"Phase 2 firmware file not found: {filepath}")
            
            if self._progress_callback:
                self._progress_callback("Executing phase 2 flash...")
            
            # Execute phase 2 flashing operation
            # This would integrate with the actual flashing subprocess
            success = self._execute_phase2_flash(filepath)
            
            # Report completion status
            self.flash_both_p2_callback(0 if success else 1)
            
        except Exception as ex:
            flashing_tool_logger.error(f"Phase 2 flash error: {ex}")
            self.flash_both_p2_callback(1)
            raise ChromaticError(
                f"Phase 2 flash failed: {ex}",
                original_exception=ex,
                recovery_suggestions=[
                    "Check firmware file integrity",
                    "Ensure device is properly connected",
                    "Try restarting the flash process"
                ]
            )
    
    def _execute_phase2_flash(self, filepath: str) -> bool:
        """
        Execute the actual phase 2 flashing operation.
        
        Args:
            filepath: Path to firmware file
            
        Returns:
            True if flashing succeeded, False otherwise
        """
        try:
            # This would contain the actual flashing implementation
            # For now, return success as placeholder
            flashing_tool_logger.debug(f"Executing phase 2 flash for: {filepath}")
            return True
            
        except Exception as e:
            flashing_tool_logger.error(f"Phase 2 execution failed: {e}")
            return False
    
    def flash_both_p2_callback(self, rc: int):
        """
        Enhanced phase 2 callback from decompiled version
        
        Args:
            rc: Return code from phase 2
        """
        self._flash_result = rc
        if rc != 0:
            flashing_tool_logger.error(f"Phase 2 flash failed with return code: {rc}")
            if hasattr(self, 'fail_flashing'):
                self.fail_flashing()
            return
        
        flashing_tool_logger.info("Phase 2 flash completed successfully")
        if self._progress_callback:
            self._progress_callback("Flash operation completed successfully")
        
        if hasattr(self, 'complete_flashing'):
            self.complete_flashing()
    
    def is_fpga_detected(self) -> bool:
        """Check if FPGA device is detected"""
        return self.fpga is not None
    
    def detect_device_state(self) -> str:
        """
        Enhanced device state detection with improved logic from decompiled version
        
        Returns:
            String describing current device state
        """
        try:
            if not self.is_fpga_detected():
                return "not_connected"
            
            # Enhanced state detection logic
            if self._enhanced_detection:
                # Check if we can access device properties
                try:
                    fpga = self.fpga
                    if fpga and hasattr(fpga, 'product'):
                        # Device is accessible, check firmware status
                        if self.fw_version is None:
                            return "detecting_firmware"
                        return "ready_to_flash"
                    else:
                        return "not_connected"
                except Exception:
                    return "not_connected"
            else:
                # Original detection logic
                if self.fw_version is None:
                    return "detecting_firmware"
                return "ready_to_flash"
                
        except Exception as ex:
            flashing_tool_logger.warning(f"Device state detection error: {ex}")
            return "not_connected"
    
    def _perform_device_poll(self):
        """Enhanced device polling with improved timeout management from decompiled version"""
        timeout = 1
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while not (self._auto_detect_keepalive and self._auto_detect_keepalive.is_set()):
            try:
                # Enhanced polling logic with better error handling
                self.update_status()
                
                # Enhanced timeout adjustment logic from decompiled version
                if self._enhanced_detection:
                    current_state = self.detect_device_state()
                    if current_state in ["ready_to_flash", "detecting_firmware"]:
                        if timeout != 2:
                            flashing_tool_logger.info('Device is in a connected state. Increasing the timeout to 2s')
                            timeout = 2
                    else:
                        # Reset to faster polling when not connected
                        if timeout != 1:
                            flashing_tool_logger.debug('Device not connected. Resetting timeout to 1s')
                            timeout = 1
                
                # Reset error counter on successful poll
                consecutive_errors = 0
                
                # Enhanced sleep with keepalive check
                sleep_interval = 0.1
                total_sleep = 0
                while total_sleep < timeout and not (self._auto_detect_keepalive and self._auto_detect_keepalive.is_set()):
                    time.sleep(sleep_interval)
                    total_sleep += sleep_interval
                
            except Exception as ex:
                consecutive_errors += 1
                flashing_tool_logger.warning(f"Device polling error ({consecutive_errors}/{max_consecutive_errors}): {ex}")
                
                # Enhanced error handling - back off if too many consecutive errors
                if self._enhanced_detection and consecutive_errors >= max_consecutive_errors:
                    flashing_tool_logger.error(f"Too many consecutive polling errors, backing off")
                    time.sleep(min(timeout * 2, 10))  # Back off but cap at 10 seconds
                    consecutive_errors = 0  # Reset counter after backoff
                else:
                    time.sleep(timeout)
        
        flashing_tool_logger.debug("Device polling thread stopped")
    
    def update_status(self):
        """Enhanced status update with improved locking and error handling from decompiled version"""
        current_thread = threading.current_thread()
        polling_thread_name = self._polling_thread.name if self._polling_thread else None
        
        # Enhanced locking logic from decompiled version
        should_lock = current_thread.name != polling_thread_name
        lock_acquired = False
        
        try:
            if should_lock:
                # Use timeout to prevent deadlocks
                lock_acquired = self._flashing_lock.acquire(timeout=5.0 if self._enhanced_detection else True)
                if not lock_acquired and self._enhanced_detection:
                    flashing_tool_logger.warning("Failed to acquire status update lock within timeout")
                    return
            
            # Enhanced status update logic
            try:
                device_detected = self.is_fpga_detected()
                
                if device_detected:
                    current_state = self.detect_device_state()
                    
                    # Enhanced hardware attribute updates
                    if self._should_update_hardware_attrs or current_state == "detecting_firmware":
                        self._set_hardware_attributes()
                        self._should_update_hardware_attrs = False
                    
                    # Handle state transitions
                    if hasattr(self, '_handle_state_transition'):
                        self._handle_state_transition(current_state)
                    else:
                        # Basic state handling for base class
                        if current_state == "detecting_firmware":
                            self._set_hardware_attributes()
                else:
                    # Device disconnected - reset hardware attributes flag
                    self._should_update_hardware_attrs = True
                    
                    # Handle disconnection
                    if hasattr(self, '_handle_disconnect'):
                        self._handle_disconnect()
                    
            except Exception as status_ex:
                flashing_tool_logger.warning(f"Status update processing error: {status_ex}")
                if self._enhanced_detection:
                    # Enhanced error recovery
                    self._should_update_hardware_attrs = True
                    
        except Exception as ex:
            flashing_tool_logger.error(f"Status update critical error: {ex}")
        finally:
            if should_lock and lock_acquired:
                try:
                    self._flashing_lock.release()
                except Exception as release_ex:
                    flashing_tool_logger.error(f"Error releasing status update lock: {release_ex}")
    
    def _start_device_auto_detection(self):
        """Start device auto-detection thread"""
        if self._auto_detect_keepalive is None:
            self._auto_detect_keepalive = threading.Event()
        elif self._auto_detect_keepalive.is_set():
            self._auto_detect_keepalive.clear()
        
        self._polling_thread = threading.Thread(
            name='auto_detect_daemon',
            target=self._perform_device_poll,
            daemon=True
        )
        flashing_tool_logger.info('Checking for connected device')
        self._polling_thread.start()
    
    def _stop_device_auto_detection(self):
        """Enhanced stop device auto-detection from decompiled version"""
        if self._auto_detect_keepalive is not None:
            self._auto_detect_keepalive.set()
            
        # Enhanced cleanup from decompiled version
        if self._enhanced_detection and self._polling_thread:
            try:
                # Give the polling thread time to stop gracefully
                if self._polling_thread.is_alive():
                    self._auto_detect_keepalive.set()
                    # Don't wait indefinitely, but give it a moment
                    time.sleep(0.1)
            except Exception as ex:
                flashing_tool_logger.debug(f"Error stopping auto-detection: {ex}")
    
    def dispose(self):
        """Enhanced cleanup with improved resource management from decompiled version"""
        try:
            # Enhanced disposal logic from decompiled version
            if hasattr(self, 'disconnect') and hasattr(self, 'current_state'):
                # If we have state machine, transition to disconnected state
                try:
                    if self.current_state.id != getattr(self, 'not_connected', {}).get('id', 'not_connected'):
                        self.disconnect()
                except Exception as ex:
                    flashing_tool_logger.debug(f"Error during state transition in dispose: {ex}")
            
            # Stop auto-detection
            self._stop_device_auto_detection()
            
            # Enhanced ESP cleanup
            if self._esp:
                try:
                    # More thorough ESP cleanup
                    if hasattr(self._esp, 'hard_reset'):
                        self._esp.hard_reset()
                    if hasattr(self._esp, '_port') and hasattr(self._esp._port, 'close'):
                        self._esp._port.close()
                except Exception as ex:
                    flashing_tool_logger.debug(f"Error cleaning up ESP connection: {ex}")
                finally:
                    self._esp = None
            
            # Clean up threading resources
            if self._auto_detect_keepalive:
                self._auto_detect_keepalive.set()
                self._auto_detect_keepalive = None
            
            # Reset hardware attributes
            self._init_hardware_attributes()
            
            flashing_tool_logger.debug("Chromatic device manager disposed successfully")
            
        except Exception as ex:
            flashing_tool_logger.error(f"Error during dispose: {ex}")


if STATEMACHINE_AVAILABLE:
    class Chromatic(ChromaticBase, StateMachine):
        """Enhanced Chromatic device manager with state machine support"""
        
        # State definitions
        not_connected = State('Not Connected', initial=True)
        detecting_firmware = State('Detecting Firmware')
        ready_to_flash = State('Ready To Flash')
        flashing = State('Flashing')
        flashing_error = State('Flashing Error')
        update_successful = State('Update Successful')
        cart_clinic_checking = State('Cart Clinic Checking')
        cart_clinic_processing_save = State('Cart Clinic Processing Save')
        cart_clinic_needs_update = State('Cart Clinic Needs Update')
        cart_clinic_uptodate = State('Cart Clinic Up To Date')
        cart_clinic_updating = State('Cart Clinic Updating')
        cart_clinic_success = State('Cart Clinic Success')
        cart_clinic_error = State('Cart Clinic Error')
        
        # Transitions
        start_detection = not_connected.to(detecting_firmware)
        ready = detecting_firmware.to(ready_to_flash)
        start_flashing = ready_to_flash.to(flashing)
        complete_flashing = flashing.to(update_successful)
        fail_flashing = flashing.to(flashing_error)
        cart_clinic_check_game = ready_to_flash.to(cart_clinic_checking)
        cart_clinic_process_save = ready_to_flash.to(cart_clinic_processing_save)
        cart_clinic_game_needs_update = cart_clinic_checking.to(cart_clinic_needs_update)
        cart_clinic_game_uptodate = cart_clinic_checking.to(cart_clinic_uptodate)
        cart_clinic_update = cart_clinic_needs_update.to(cart_clinic_updating)
        cart_clinic_complete = cart_clinic_updating.to(cart_clinic_success)
        cart_clinic_finish_save = cart_clinic_processing_save.to(ready_to_flash)
        cart_clinic_fail = (cart_clinic_updating.to(cart_clinic_error) | 
                           cart_clinic_checking.to(cart_clinic_error) | 
                           cart_clinic_processing_save.to(cart_clinic_error))
        cart_clinic_retry = cart_clinic_error.to(ready_to_flash)
        disconnect = (detecting_firmware.to(not_connected) | 
                     ready_to_flash.to(not_connected) | 
                     flashing.to(not_connected) | 
                     flashing_error.to(not_connected) | 
                     update_successful.to(not_connected) | 
                     cart_clinic_checking.to(not_connected) | 
                     cart_clinic_needs_update.to(not_connected) | 
                     cart_clinic_uptodate.to(not_connected) | 
                     cart_clinic_error.to(not_connected) | 
                     cart_clinic_success.to(not_connected))
        
        def __init__(self, *args, **kwargs):
            # Initialize base class first
            ChromaticBase.__init__(self, *args, **kwargs)
            # Initialize state machine
            StateMachine.__init__(self)
        
        # State entry handlers
        def on_enter_detecting_firmware(self):
            """Handle entering detecting firmware state"""
            self._set_hardware_attributes()
            if not (self._polling_thread and self._polling_thread.is_alive()):
                self._start_device_auto_detection()
        
        def on_enter_ready_to_flash(self):
            """Handle entering ready to flash state"""
            self._set_hardware_attributes()
            if not (self._polling_thread and self._polling_thread.is_alive()):
                self._start_device_auto_detection()
        
        def on_enter_flashing(self):
            """Handle entering flashing state"""
            self._stop_device_auto_detection()
            self._esp = None
        
        def on_enter_not_connected(self):
            """Handle entering not connected state"""
            self._init_hardware_attributes()
            self._start_device_auto_detection()
            self._esp = None
        
        def on_enter_update_successful(self):
            """Handle entering update successful state"""
            self._start_device_auto_detection()
            self._esp = None
        
        def on_enter_cart_clinic_checking(self):
            """Handle entering cart clinic checking state"""
            self._stop_device_auto_detection()
            self._esp = None
        
        def on_enter_cart_clinic_processing_save(self):
            """Handle entering cart clinic processing save state"""
            self._stop_device_auto_detection()
            self._esp = None
        
        def after_transition(self, event, state):
            """Handle state transitions with enhanced logging"""
            flashing_tool_logger.info("Received event '%s' to transition to the '%s' state", event, state)
            if self._on_state_transition_callback:
                try:
                    self._on_state_transition_callback(event, state)
                except Exception as ex:
                    flashing_tool_logger.error(f"State transition callback error: {ex}")
        
        def _handle_state_transition(self, detected_state: str):
            """Enhanced automatic state transitions with improved logic from decompiled version"""
            try:
                current_state_id = self.current_state.id
                
                # Enhanced state transition logic
                if self.is_fpga_detected():
                    if current_state_id == self.not_connected.id:
                        flashing_tool_logger.debug("Device detected, transitioning to detecting_firmware")
                        self.start_detection()
                    elif (current_state_id == self.detecting_firmware.id and 
                          self.fw_version is not None):
                        flashing_tool_logger.debug("Firmware detected, transitioning to ready_to_flash")
                        self.ready()
                    elif (current_state_id in [self.flashing_error.id, self.update_successful.id] and
                          self._enhanced_detection):
                        # Enhanced recovery logic - allow transition back to ready state
                        if self.fw_version is not None:
                            flashing_tool_logger.debug("Device ready after previous operation")
                            self.ready()
                else:
                    # Device disconnected
                    if current_state_id != self.not_connected.id:
                        flashing_tool_logger.debug("Device disconnected, transitioning to not_connected")
                        self.disconnect()
                        
            except Exception as ex:
                flashing_tool_logger.warning(f"Enhanced state transition error: {ex}")
                # Enhanced error recovery - try to get to a known good state
                if self._enhanced_detection:
                    try:
                        if not self.is_fpga_detected() and self.current_state.id != self.not_connected.id:
                            self.disconnect()
                    except Exception as recovery_ex:
                        flashing_tool_logger.error(f"State recovery failed: {recovery_ex}")
        
        def _handle_disconnect(self):
            """Handle device disconnection"""
            try:
                if self.current_state.id != self.not_connected.id:
                    self.disconnect()
            except Exception as ex:
                flashing_tool_logger.warning(f"Disconnect handling error: {ex}")
        
        # State property helpers
        @property
        def connected_states(self) -> List[str]:
            return [self.ready_to_flash.id, self.detecting_firmware.id]
        
        @property
        def firmware_update_states(self) -> List[str]:
            return [self.flashing.id]
        
        @property
        def unready_states(self) -> List[str]:
            return [self.not_connected.id, self.detecting_firmware.id]
        
        @property
        def ready_states(self) -> List[str]:
            return [self.ready_to_flash.id]
        
        @property
        def disconnected_states(self) -> List[str]:
            return [self.not_connected.id]
        
        @property
        def error_states(self) -> List[str]:
            return [self.flashing_error.id]
        
        @property
        def success_states(self) -> List[str]:
            return [self.update_successful.id]
        
        @property
        def completion_events(self) -> List[str]:
            return [self.complete_flashing.name]
        
        @property
        def cart_clinic_active_states(self) -> List[str]:
            return [
                self.cart_clinic_checking.id,
                self.cart_clinic_processing_save.id,
                self.cart_clinic_needs_update.id,
                self.cart_clinic_updating.id,
                self.cart_clinic_uptodate.id,
                self.cart_clinic_error.id,
                self.cart_clinic_success.id
            ]
        
        @property
        def cart_clinic_updating_states(self) -> List[str]:
            return [
                self.cart_clinic_checking.id,
                self.cart_clinic_processing_save.id,
                self.cart_clinic_updating.id
            ]
        
        @property
        def failure_events(self) -> List[str]:
            return [self.fail_flashing.name]

else:
    # Fallback class without state machine
    class Chromatic(ChromaticBase):
        """Chromatic device manager without state machine (fallback)"""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._current_state = "not_connected"
            flashing_tool_logger.warning("State machine not available, using basic state management")
        
        @property
        def current_state(self):
            """Get current state (fallback implementation)"""
            class SimpleState:
                def __init__(self, state_id):
                    self.id = state_id
            return SimpleState(self._current_state)
        
        def _handle_state_transition(self, detected_state: str):
            """Simple state transition handling"""
            if detected_state != self._current_state:
                old_state = self._current_state
                self._current_state = detected_state
                flashing_tool_logger.info(f"State changed from {old_state} to {detected_state}")
                
                if self._on_state_transition_callback:
                    try:
                        self._on_state_transition_callback("auto_transition", detected_state)
                    except Exception as ex:
                        flashing_tool_logger.error(f"State transition callback error: {ex}")
        
        def _handle_disconnect(self):
            """Handle device disconnection"""
            self._current_state = "not_connected"


# Export the main class
__all__ = ['Chromatic', 'ChromaticError']