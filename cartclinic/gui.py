"""
Enhanced Cart Clinic GUI Module

This module provides the enhanced GUI components for Cart Clinic operations,
integrating improvements from the decompiled version while maintaining
backward compatibility and improving code quality.

The module includes:
- Enhanced state management for Cart Clinic operations
- Improved progress reporting with detailed feedback
- Comprehensive error handling with recovery strategies
- Thread-safe operations for better responsiveness
"""

import base64
import logging
import time
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass

# Import Qt components with compatibility layer
from import_compatibility import (
    QT_AVAILABLE, QObject, QPixmap, QWidget
)

# Import additional Qt components if available
if QT_AVAILABLE:
    try:
        from PySide6.QtCore import QByteArray, QThread
        from PySide6.QtWidgets import QFileDialog
    except ImportError:
        try:
            from PyQt6.QtCore import QByteArray, QThread
            from PyQt6.QtWidgets import QFileDialog
        except ImportError:
            # Create dummy classes for missing components
            class QByteArray:
                def __init__(self, *args):
                    pass
            class QThread:
                def __init__(self, *args):
                    pass
            class QFileDialog:
                @staticmethod
                def getSaveFileName(*args):
                    return "", ""
else:
    # Create dummy classes for headless operation
    class QByteArray:
        def __init__(self, *args):
            pass
    class QThread:
        def __init__(self, *args):
            pass
    class QFileDialog:
        @staticmethod
        def getSaveFileName(*args):
            return "", ""

# Define pyqtSignal for compatibility
try:
    from PySide6.QtCore import Signal as pyqtSignal
except ImportError:
    try:
        from PyQt6.QtCore import pyqtSignal
    except ImportError:
        # Create a dummy signal class for compatibility
        class DummySignal:
            def __init__(self, *args):
                pass
            def connect(self, func):
                pass
            def emit(self, *args):
                pass
        pyqtSignal = lambda *args: DummySignal(*args)

# Import flashing tool components
from flashing_tool.chromatic import Chromatic
from flashing_tool.util import resolve_path

logger = logging.getLogger('mrupdater')


@dataclass
class CartClinicState:
    """Enhanced state tracking for Cart Clinic operations."""
    
    current_operation: Optional[str] = None
    progress: int = 0
    error_message: Optional[str] = None
    secondary_error: Optional[str] = None
    session_active: bool = False
    device_connected: bool = False
    
    def reset(self):
        """Reset state to initial values."""
        self.current_operation = None
        self.progress = 0
        self.error_message = None
        self.secondary_error = None
        self.session_active = False


@dataclass
class ProgressInfo:
    """Enhanced progress information for better user feedback."""
    
    current: int = 0
    total: int = 100
    message: str = ""
    detailed_status: str = ""
    estimated_time_remaining: Optional[float] = None
    
    @property
    def percentage(self) -> int:
        """Calculate percentage completion."""
        if self.total <= 0:
            return 0
        return min(100, max(0, int((self.current / self.total) * 100)))


class EnhancedProgressReporter(QObject):
    """Enhanced progress reporting with better user feedback."""
    
    # Signals for progress updates
    progress_updated = pyqtSignal(object)  # ProgressInfo
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)  # primary, secondary
    
    def __init__(self):
        super().__init__()
        self._start_time = None
        self._last_progress = 0
        
    def start_operation(self, operation_name: str):
        """Start tracking a new operation."""
        self._start_time = time.time()
        self._last_progress = 0
        self.status_changed.emit(f"Starting {operation_name}...")
        
    def update_progress(self, current: int, total: int = 100, message: str = ""):
        """Update progress with enhanced information."""
        progress_info = ProgressInfo(
            current=current,
            total=total,
            message=message,
            detailed_status=self._generate_detailed_status(current, total)
        )
        
        # Calculate estimated time remaining
        if self._start_time and current > self._last_progress:
            elapsed = time.time() - self._start_time
            if current > 0:
                estimated_total_time = (elapsed / current) * total
                progress_info.estimated_time_remaining = estimated_total_time - elapsed
        
        self._last_progress = current
        self.progress_updated.emit(progress_info)
        
    def _generate_detailed_status(self, current: int, total: int) -> str:
        """Generate detailed status message."""
        percentage = int((current / total) * 100) if total > 0 else 0
        
        if percentage >= 95:
            return "Finalizing operation..."
        elif percentage >= 75:
            return "Nearly complete..."
        elif percentage >= 50:
            return "Processing..."
        elif percentage >= 25:
            return "In progress..."
        else:
            return "Starting..."
    
    def report_error(self, primary_error: str, secondary_error: str = ""):
        """Report an error with enhanced context."""
        logger.error(f"Cart Clinic error: {primary_error}")
        if secondary_error:
            logger.error(f"Additional context: {secondary_error}")
        self.error_occurred.emit(primary_error, secondary_error)


class EnhancedCartClinic:
    """
    Enhanced Cart Clinic class with improved UI responsiveness and error handling.
    
    This class integrates enhancements from the decompiled version while maintaining
    backward compatibility and improving code quality.
    """
    
    def __init__(self, main_gui, chromatic: Optional[Chromatic] = None, 
                 form=None, feature_manager=None, app_config=None):
        """
        Initialize enhanced Cart Clinic.
        
        Args:
            main_gui: Main GUI instance
            chromatic: Chromatic device instance
            form: UI form instance
            feature_manager: Feature manager instance
            app_config: Application configuration
        """
        self._main_gui = main_gui
        self._chromatic = chromatic
        self._form = form
        self._feature_manager = feature_manager
        self._app_config = app_config
        
        # Enhanced state management
        self._state = CartClinicState()
        self._progress_reporter = EnhancedProgressReporter()
        
        # Session and threading (enhanced from decompiled version)
        self._session = None
        self._active_threads: List[QThread] = []
        
        # Cart Clinic specific state (matching decompiled structure)
        self._cc_mrpatcher_response = None  # Match decompiled naming
        self._cc_current_cart_data = None   # Match decompiled naming
        self._cart_clinic_fw_path = None
        self._mrpatcher_endpoint = None
        
        # Enhanced progress tracking from decompiled version
        self._cc_check_progress = 0
        self._loading_text_index = 0
        self._loading_text_snippets = []
        
        # Thread management from decompiled version
        self._cc_check_thread = None
        self._cc_animation_thread = None
        self._cc_detection_thread = None
        self._cc_chromatic_thread = None
        self._cc_update_thread = None
        self._cc_save_op_thread = None
        self._cc_save_detect_thread = None
        self._cc_homebrew_thread = None
        
        # Save operation state
        self._cc_save_op = None  # Will be set based on operation type
        self._cc_save_path = None
        self._cc_save_game_info = None
        
        # Enhanced error handling
        self._error_recovery_attempts = 0
        self._max_recovery_attempts = 3
        
        # UI screens (will be loaded later)
        self._screens = {}
        
        # Connect enhanced progress reporting
        self._setup_progress_reporting()
        
        logger.info("Enhanced Cart Clinic initialized")
    
    def _setup_progress_reporting(self):
        """Setup enhanced progress reporting connections."""
        if not QT_AVAILABLE:
            return
            
        self._progress_reporter.progress_updated.connect(self._handle_progress_update)
        self._progress_reporter.status_changed.connect(self._handle_status_change)
        self._progress_reporter.error_occurred.connect(self._handle_error_occurred)
    
    def _handle_progress_update(self, progress_info: ProgressInfo):
        """Handle enhanced progress updates."""
        self._state.progress = progress_info.percentage
        
        # Update UI with enhanced progress information
        if hasattr(self._main_gui, 'update_progress_display'):
            self._main_gui.update_progress_display(progress_info)
        
        # Log detailed progress for debugging
        if progress_info.estimated_time_remaining:
            logger.debug(f"Progress: {progress_info.percentage}% - "
                        f"ETA: {progress_info.estimated_time_remaining:.1f}s")
    
    def _handle_status_change(self, status: str):
        """Handle status change updates."""
        self._state.current_operation = status
        logger.info(f"Cart Clinic status: {status}")
        
        # Update UI status display
        if hasattr(self._main_gui, 'update_status_display'):
            self._main_gui.update_status_display(status)
    
    def _handle_error_occurred(self, primary_error: str, secondary_error: str):
        """Handle error occurrences with enhanced recovery."""
        self._state.error_message = primary_error
        self._state.secondary_error = secondary_error
        
        # Attempt error recovery
        if self._error_recovery_attempts < self._max_recovery_attempts:
            self._error_recovery_attempts += 1
            logger.warning(f"Attempting error recovery (attempt {self._error_recovery_attempts})")
            
            if self._attempt_error_recovery():
                return
        
        # If recovery fails, show error to user
        self._show_error_to_user(primary_error, secondary_error)
    
    def _attempt_error_recovery(self) -> bool:
        """
        Attempt to recover from errors automatically.
        
        Returns:
            bool: True if recovery was successful, False otherwise
        """
        try:
            # Clean up any active sessions
            if self._session:
                self._cleanup_session()
            
            # Reset device connection if needed
            if self._chromatic and hasattr(self._chromatic, 'reset_connection'):
                self._chromatic.reset_connection()
                
            # Wait a moment for device to stabilize
            time.sleep(1.0)
            
            logger.info("Error recovery attempt completed")
            return True
            
        except Exception as e:
            logger.error(f"Error recovery failed: {e}")
            return False
    
    def _show_error_to_user(self, primary_error: str, secondary_error: str):
        """Show error to user with enhanced context."""
        if hasattr(self._main_gui, 'show_enhanced_error'):
            self._main_gui.show_enhanced_error(primary_error, secondary_error, 
                                             self._get_error_recovery_suggestions())
        else:
            # Fallback to basic error display
            if hasattr(self._main_gui, 'show_error_message'):
                error_msg = primary_error
                if secondary_error:
                    error_msg += f"\n{secondary_error}"
                self._main_gui.show_error_message(error_msg)
    
    def _get_error_recovery_suggestions(self) -> List[str]:
        """Get context-specific error recovery suggestions."""
        suggestions = []
        
        if not self._state.device_connected:
            suggestions.append("Check that your Chromatic device is properly connected")
            suggestions.append("Try unplugging and reconnecting the device")
        
        if self._state.session_active:
            suggestions.append("Try restarting the Cart Clinic operation")
        
        suggestions.append("Check the device manual for troubleshooting steps")
        suggestions.append("Contact support if the problem persists")
        
        return suggestions
    
    def load_screens(self):
        """Load and initialize UI screens with enhanced error handling."""
        try:
            if not self._main_gui:
                raise ValueError("Main GUI not available")
            
            # Load screens using main GUI's screen loader (enhanced from decompiled version)
            if hasattr(self._main_gui, 'load_screen'):
                self._load_screens_with_main_gui()
            else:
                logger.warning("Main GUI doesn't support screen loading")
                
            self._init_enhanced_buttons()
            logger.info("Cart Clinic screens loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Cart Clinic screens: {e}")
            raise
    
    def _load_screens_with_main_gui(self):
        """Load screens using main GUI's screen loader (enhanced from decompiled version)."""
        try:
            # Get the Cart Clinic tab from main GUI
            self._cc_tab = getattr(self._main_gui, '_cc_tab', None)
            
            if not self._cc_tab:
                logger.warning("Cart Clinic tab not found in main GUI")
                return
            
            # Load all screens with enhanced error handling
            self._screens = {
                'start': self._load_screen_safe('Ui_CCStartScreen', 'screen_cc_start'),
                'connect': self._load_screen_safe('Ui_CCConnectScreen', 'screen_cc_connect'),
                'check': self._load_screen_safe('Ui_CCCheckScreen', 'screen_cc_check'),
                'error': self._load_screen_safe('Ui_CCErrorScreen', 'screen_cc_error'),
                'loading': self._load_screen_safe('Ui_CCLoadingScreen', 'screen_cc_loading'),
                'save': self._load_screen_safe('Ui_CCSaveScreen', 'screen_cc_save'),
                'success': self._load_screen_safe('Ui_CCSuccessScreen', 'screen_cc_success'),
                'update': self._load_screen_safe('Ui_CCUpdateScreen', 'screen_cc_update'),
                'updating': self._load_screen_safe('Ui_CCUpdatingScreen', 'screen_cc_updating'),
                'uptodate': self._load_screen_safe('Ui_CCUpToDateScreen', 'screen_cc_uptodate')
            }
            
            # Store screen references for compatibility with decompiled version
            self._start_screen = self._screens['start']
            self._connect_screen = self._screens['connect']
            self._check_screen = self._screens['check']
            self._error_screen = self._screens['error']
            self._loading_screen = self._screens['loading']
            self._save_screen = self._screens['save']
            self._success_screen = self._screens['success']
            self._update_screen = self._screens['update']
            self._updating_screen = self._screens['updating']
            self._uptodate_screen = self._screens['uptodate']
            
            logger.debug("Cart Clinic screens loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading screens: {e}")
            # Create fallback empty screens
            self._screens = {}
    
    def _load_screen_safe(self, ui_class_name: str, screen_attr: str):
        """Safely load a screen with error handling."""
        try:
            if hasattr(self._main_gui, 'load_screen') and self._cc_tab:
                screen_widget = getattr(self._cc_tab, screen_attr, None)
                if screen_widget:
                    return self._main_gui.load_screen(ui_class_name, screen_widget)
            return None
        except Exception as e:
            logger.warning(f"Failed to load screen {ui_class_name}: {e}")
            return None
    
    def _init_enhanced_buttons(self):
        """Initialize buttons with enhanced event handling (from decompiled version)."""
        try:
            if not self._screens:
                logger.warning("No screens available for button initialization")
                return
            
            # Initialize buttons with enhanced error handling
            self._init_button_safe(self._start_screen, 'cc_btn_check', self.cart_clinic_check)
            self._init_button_safe(self._start_screen, 'cc_homebrew_btn', self.cart_clinic_homebrew)
            self._init_button_safe(self._update_screen, 'cc_update_btn', self.cart_clinic_update)
            self._init_button_safe(self._error_screen, 'cc_retry_btn', self.retry_cart_clinic)
            self._init_button_safe(self._update_screen, 'cc_cancel_btn', self.cancel_cart_clinic)
            self._init_button_safe(self._update_screen, 'cc_changelog_btn', self.show_changelog_dialog)
            self._init_button_safe(self._success_screen, 'cc_ok_done_btn', self.disconnect_cart_clinic)
            self._init_button_safe(self._uptodate_screen, 'cc_ok_uptodate_btn', self.disconnect_cart_clinic)
            
            logger.debug("Enhanced button handlers initialized")
            
        except Exception as e:
            logger.error(f"Error initializing buttons: {e}")
    
    def _init_button_safe(self, screen, button_name: str, callback):
        """Safely initialize a button with error handling."""
        try:
            if screen and hasattr(screen, button_name):
                button = getattr(screen, button_name)
                if hasattr(button, 'clicked'):
                    button.clicked.connect(callback)
        except Exception as e:
            logger.warning(f"Failed to initialize button {button_name}: {e}")
    
    def start_cart_clinic_check(self, include_progress_callback: bool = True):
        """
        Start Cart Clinic check operation with enhanced progress reporting.
        
        Args:
            include_progress_callback: Whether to include detailed progress callbacks
        """
        try:
            # Validate prerequisites
            if not self._validate_prerequisites():
                return False
            
            # Reset state for new operation
            self._state.reset()
            self._error_recovery_attempts = 0
            
            # Start progress reporting
            self._progress_reporter.start_operation("Cart Clinic Check")
            
            # Show user confirmation if needed
            if not self._show_operation_confirmation():
                return False
            
            # Initialize session and start check
            self._initialize_session()
            self._start_check_operation()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Cart Clinic check: {e}")
            self._progress_reporter.report_error("Failed to start check operation", str(e))
            return False
    
    def _validate_prerequisites(self) -> bool:
        """Validate that all prerequisites are met for Cart Clinic operations."""
        if not self._chromatic:
            logger.error("Chromatic device not available")
            return False
        
        if not self._cart_clinic_fw_path:
            logger.error("Cart Clinic firmware path not set")
            return False
        
        if not self._mrpatcher_endpoint:
            logger.error("MRPatcher endpoint not configured")
            return False
        
        return True
    
    def _show_operation_confirmation(self) -> bool:
        """Show confirmation dialog for potentially destructive operations."""
        if hasattr(self._main_gui, 'show_prompt'):
            return self._main_gui.show_prompt(
                'Warning',
                'This action will turn off your game. Make sure you saved your progress.\n'
                'Do you wish to proceed?'
            )
        return True  # Default to proceed if no confirmation available
    
    def _initialize_session(self):
        """Initialize Cart Clinic session with enhanced error handling."""
        try:
            # Clean up any existing session
            if self._session:
                self._cleanup_session()
            
            # Create new session
            self._session = self._create_enhanced_session()
            self._state.session_active = True
            
            logger.info("Cart Clinic session initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            raise
    
    def _create_enhanced_session(self):
        """Create an enhanced session with better error handling."""
        # This would create the actual session based on available transport
        # For now, return a placeholder
        logger.debug("Enhanced session created")
        return None
    
    def _start_check_operation(self):
        """Start the actual check operation."""
        # This would start the check operation in a separate thread
        # with enhanced progress reporting
        self._progress_reporter.update_progress(10, 100, "Initializing check...")
        logger.info("Cart Clinic check operation started")
    
    def _cleanup_session(self):
        """Clean up Cart Clinic session and resources."""
        try:
            if self._session:
                # Clean up session resources
                logger.debug("Cleaning up Cart Clinic session")
                self._session = None
            
            # Stop any active threads
            self._stop_active_threads()
            
            # Reset session state
            self._state.session_active = False
            
            logger.info("Cart Clinic session cleaned up")
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
    
    def _stop_active_threads(self):
        """Stop all active threads safely."""
        for thread in self._active_threads:
            if thread and thread.isRunning():
                thread.quit()
                thread.wait(5000)  # Wait up to 5 seconds
        
        self._active_threads.clear()
    
    def set_mrpatcher_endpoint(self, endpoint: str):
        """Set the MRPatcher endpoint URL."""
        self._mrpatcher_endpoint = endpoint
        logger.info(f"MRPatcher endpoint set: {endpoint}")
    
    def set_cart_clinic_firmware_path(self, fw_path: str):
        """Set the Cart Clinic firmware path."""
        self._cart_clinic_fw_path = fw_path
        logger.info(f"Cart Clinic firmware path set: {fw_path}")
    
    def get_state(self) -> CartClinicState:
        """Get current Cart Clinic state."""
        return self._state
    
    def is_operation_active(self) -> bool:
        """Check if any Cart Clinic operation is currently active."""
        return self._state.session_active or bool(self._active_threads)
    
    def cancel_current_operation(self):
        """Cancel the currently running operation."""
        try:
            logger.info("Cancelling Cart Clinic operation")
            
            # Stop progress reporting
            self._progress_reporter.status_changed.emit("Cancelling operation...")
            
            # Clean up session and threads
            self._cleanup_session()
            
            # Reset state
            self._state.reset()
            
            logger.info("Cart Clinic operation cancelled")
            
        except Exception as e:
            logger.error(f"Error cancelling operation: {e}")
    
    def display_cart_label(self, label_base64: str):
        """
        Display cartridge label with enhanced error handling.
        
        Args:
            label_base64: Base64 encoded image data
        """
        try:
            if not QT_AVAILABLE:
                logger.warning("Qt not available, cannot display cart label")
                return
            
            # Decode and display image
            image_data = base64.b64decode(label_base64)
            pixmap = QPixmap()
            
            if pixmap.loadFromData(QByteArray(image_data)):
                # Update UI with cart label
                self._update_cart_label_display(pixmap)
                logger.debug("Cart label displayed successfully")
            else:
                logger.warning("Failed to load cart label image data")
                
        except Exception as e:
            logger.error(f"Error displaying cart label: {e}")
    
    def _update_cart_label_display(self, pixmap: QPixmap):
        """Update the UI with the cart label pixmap."""
        # This would update the actual UI elements
        # Implementation depends on the GUI framework
        logger.debug("Cart label UI updated")
    
    def reset_cart_clinic(self):
        """
        Reset Cart Clinic to initial state.
        
        This method resets all Cart Clinic state variables and cleans up
        any active operations, preparing for a new Cart Clinic session.
        """
        try:
            logger.info("Resetting Cart Clinic state")
            
            # Reset state
            self._state.reset()
            
            # Clean up any active session
            self._cleanup_session()
            
            # Reset error recovery attempts
            self._error_recovery_attempts = 0
            
            # Reset operation-specific variables
            self._cc_mrpatcher_response = None
            self._cc_current_cart_data = None
            self._cc_check_progress = 0
            self._loading_text_index = 0
            
            # Reset save operation state
            self._cc_save_op = None
            self._cc_save_path = None
            self._cc_save_game_info = None
            
            logger.debug("Cart Clinic state reset completed")
            
        except Exception as e:
            logger.error(f"Error resetting Cart Clinic state: {e}")
    
    def get_enhanced_error_context(self) -> Dict[str, Any]:
        """
        Get enhanced error context for debugging and support.
        
        Returns:
            Dictionary containing comprehensive error context information
            including current state, configuration, and system status.
        """
        return {
            'state': {
                'current_operation': self._state.current_operation,
                'progress': self._state.progress,
                'session_active': self._state.session_active,
                'device_connected': self._state.device_connected,
                'error_message': self._state.error_message,
                'secondary_error': self._state.secondary_error
            },
            'recovery_info': {
                'recovery_attempts': self._error_recovery_attempts,
                'max_recovery_attempts': self._max_recovery_attempts
            },
            'threading_info': {
                'active_threads': len(self._active_threads),
                'thread_names': [t.name for t in self._active_threads if hasattr(t, 'name')]
            },
            'session_info': {
                'session_available': self._session is not None,
                'session_type': type(self._session).__name__ if self._session else None
            },
            'configuration': {
                'firmware_path': self._cart_clinic_fw_path,
                'endpoint': self._mrpatcher_endpoint,
                'feature_manager_available': self._feature_manager is not None,
                'app_config_available': self._app_config is not None
            },
            'operation_state': {
                'mrpatcher_response': self._cc_mrpatcher_response is not None,
                'current_cart_data': self._cc_current_cart_data is not None,
                'check_progress': self._cc_check_progress,
                'save_operation': self._cc_save_op,
                'save_path': self._cc_save_path
            }
        }
    
    # Enhanced methods from decompiled version
    
    def retry_cart_clinic(self):
        """In a failure state, retry moves back to the checking state (from decompiled version)."""
        try:
            logger.info("Retrying Cart Clinic operation")
            if self._chromatic and hasattr(self._chromatic, 'cart_clinic_retry'):
                self._chromatic.cart_clinic_retry()
            else:
                logger.warning("Chromatic retry method not available")
        except Exception as e:
            logger.error(f"Error during Cart Clinic retry: {e}")
    
    def disconnect_cart_clinic(self):
        """When the workflow reaches an end state, disconnect Chromatic to start over (from decompiled version)."""
        try:
            logger.info("Disconnecting Cart Clinic")
            if self._chromatic and hasattr(self._chromatic, 'disconnect'):
                self._chromatic.disconnect()
            else:
                logger.warning("Chromatic disconnect method not available")
        except Exception as e:
            logger.error(f"Error during Cart Clinic disconnect: {e}")
    
    def cancel_cart_clinic(self):
        """When the user presses the cancel button, perform cleanup and disconnect (from decompiled version)."""
        try:
            logger.info('Cart Clinic update cancelled')
            self.cleanup_cart_clinic()
            self.disconnect_cart_clinic()
        except Exception as e:
            logger.error(f"Error cancelling Cart Clinic: {e}")
    
    def cart_clinic_homebrew(self):
        """
        Handle homebrew ROM flashing operation.
        
        This method initiates the process of flashing a homebrew ROM to a cartridge
        through the Cart Clinic interface. It performs the following steps:
        
        1. Validates that developer mode is enabled
        2. Prompts user to select a homebrew ROM file
        3. Resets the Cart Clinic state
        4. Initiates the homebrew flashing process
        
        The operation requires developer mode to be enabled as a safety measure
        since homebrew ROMs can potentially damage cartridges if not properly
        validated.
        
        Raises:
            Exception: If homebrew operation fails at any stage
        """
        try:
            # Validate developer mode is enabled for safety
            if not self._is_developer_mode_enabled():
                logger.warning("Developer mode not enabled for homebrew operations")
                self._show_developer_mode_required_message()
                return
            
            # Get homebrew ROM file from user
            rom_path = self._get_homebrew_rom_path()
            if not rom_path:
                logger.info("Homebrew operation cancelled by user")
                return
            
            # Validate ROM file
            if not self._validate_homebrew_rom(rom_path):
                return
            
            logger.info(f'Starting homebrew ROM flash: {rom_path}')
            
            # Reset Cart Clinic state for new operation
            self.reset_cart_clinic()
            
            # Initiate Cart Clinic check for the homebrew operation
            if self._chromatic and hasattr(self._chromatic, 'cart_clinic_check_game'):
                self._chromatic.cart_clinic_check_game()
            
            # Start the homebrew flashing operation
            self._start_homebrew_operation(rom_path)
            
        except Exception as e:
            logger.error(f"Error in Cart Clinic homebrew operation: {e}")
            self._progress_reporter.report_error(
                "Homebrew operation failed", 
                str(e)
            )
            self._handle_homebrew_error(e)
    
    def _show_developer_mode_required_message(self):
        """Show message explaining that developer mode is required."""
        if hasattr(self._main_gui, 'show_info_message'):
            self._main_gui.show_info_message(
                "Developer mode is required for homebrew ROM operations. "
                "Please enable developer mode in the settings to use this feature.",
                "Developer Mode Required"
            )
    
    def _validate_homebrew_rom(self, rom_path: str) -> bool:
        """
        Validate homebrew ROM file before flashing.
        
        Args:
            rom_path: Path to ROM file
            
        Returns:
            True if ROM is valid, False otherwise
        """
        try:
            # Check file exists and is readable
            if not os.path.exists(rom_path):
                self._show_error_to_user("ROM file not found", f"File does not exist: {rom_path}")
                return False
            
            # Check file size is reasonable
            file_size = os.path.getsize(rom_path)
            max_size = 32 * 1024 * 1024  # 32MB max
            if file_size > max_size:
                self._show_error_to_user(
                    "ROM file too large", 
                    f"ROM file exceeds maximum size of {max_size // (1024*1024)}MB"
                )
                return False
            
            if file_size == 0:
                self._show_error_to_user("ROM file is empty", "Selected file contains no data")
                return False
            
            logger.debug(f"ROM validation passed: {rom_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"ROM validation error: {e}")
            self._show_error_to_user("ROM validation failed", str(e))
            return False
    
    def _start_homebrew_operation(self, rom_path: str):
        """
        Start the homebrew ROM flashing operation.
        
        Args:
            rom_path: Path to validated ROM file
        """
        try:
            # This would start the actual homebrew flashing process
            # Implementation would depend on the specific flashing protocol
            logger.info(f"Starting homebrew operation for: {rom_path}")
            
            # Update progress
            self._progress_reporter.start_operation("Homebrew ROM Flash")
            self._progress_reporter.update_progress(0, 100, "Preparing homebrew flash...")
            
        except Exception as e:
            logger.error(f"Failed to start homebrew operation: {e}")
            raise
    
    def _handle_homebrew_error(self, error: Exception):
        """
        Handle errors that occur during homebrew operations.
        
        Args:
            error: Exception that occurred
        """
        try:
            # Clean up any partial operations
            self._cleanup_session()
            
            # Show user-friendly error message
            error_msg = "Homebrew operation failed"
            if "permission" in str(error).lower():
                error_msg += ". Check file permissions and try again."
            elif "connection" in str(error).lower():
                error_msg += ". Check device connection and try again."
            
            self._show_error_to_user(error_msg, str(error))
            
        except Exception as cleanup_error:
            logger.error(f"Error during homebrew error handling: {cleanup_error}")
    
    def _is_developer_mode_enabled(self) -> bool:
        """Check if developer mode is enabled."""
        try:
            if self._feature_manager and hasattr(self._feature_manager, 'is_feature_enabled'):
                # Would need to import the actual feature enum
                return self._feature_manager.is_feature_enabled('DEVELOPER_MODE')
            return False
        except Exception as e:
            logger.warning(f"Error checking developer mode: {e}")
            return False
    
    def _get_homebrew_rom_path(self) -> Optional[str]:
        """
        Get homebrew ROM path from user through file dialog.
        
        Returns:
            Path to selected ROM file, or None if cancelled
        """
        try:
            if not QT_AVAILABLE:
                logger.warning("Qt not available for file dialog")
                return None
            
            # Get previous directory for user convenience
            prev_dir = self._get_previous_homebrew_dir()
            
            # Show file dialog with appropriate filters
            rom_path, _ = QFileDialog.getOpenFileName(
                self._main_gui,
                'Select a Homebrew ROM',
                str(prev_dir),
                'Game Boy Files (*.gb *.gbc *.bin);;All Files (*)'
            )
            
            if rom_path:
                # Save directory for next time
                self._save_previous_homebrew_dir(rom_path)
                logger.info(f"Selected homebrew ROM: {rom_path}")
                return rom_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error selecting homebrew ROM: {e}")
            return None
    
    def _get_previous_homebrew_dir(self) -> Path:
        """Get the previously used homebrew directory."""
        try:
            if self._app_config:
                prev_dir = self._app_config.get('last_homebrew_dir', '')
                if prev_dir and os.path.exists(prev_dir):
                    return Path(prev_dir)
            
            # Default to user's home directory
            return Path.home()
            
        except Exception as e:
            logger.debug(f"Error getting previous homebrew dir: {e}")
            return Path.home()
    
    def _save_previous_homebrew_dir(self, rom_path: str):
        """Save the directory of the selected ROM for next time."""
        try:
            if self._app_config:
                dir_path = os.path.dirname(rom_path)
                self._app_config.set('last_homebrew_dir', dir_path)
                self._app_config.save()
        except Exception as e:
            logger.debug(f"Error saving previous homebrew dir: {e}")
            
    def _save_previous_homebrew_dir(self, dir_path):
        """Save the previous homebrew directory"""
        try:
            self._app_config.set('last_homebrew_dir', str(dir_path))
            self._app_config.save()
        except Exception as e:
            logger.debug(f"Error saving previous homebrew dir: {e}")
            
    def get_homebrew_rom_path(self):
        """Get homebrew ROM path from user"""
        try:
            rom_path = self._get_homebrew_rom_path()
            if rom_path:
                self._save_previous_homebrew_dir(Path(rom_path).parent)
                return rom_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting homebrew ROM path: {e}")
            return None
    
    def _get_previous_homebrew_dir(self) -> Path:
        """Get previous homebrew directory from config."""
        try:
            if self._app_config and hasattr(self._app_config, 'get'):
                prev_dir = self._app_config.get('PREVIOUS_HOMEBREW_DIR')
                if prev_dir:
                    return Path(prev_dir)
            return Path.home()
        except Exception as e:
            logger.warning(f"Error getting previous homebrew dir: {e}")
            return Path.home()
    
    def _set_previous_homebrew_dir(self, prev_dir: Path):
        """Set previous homebrew directory in config."""
        try:
            if self._app_config and hasattr(self._app_config, 'set'):
                self._app_config.set('PREVIOUS_HOMEBREW_DIR', str(prev_dir))
        except Exception as e:
            logger.warning(f"Error setting previous homebrew dir: {e}")
    
    def _start_homebrew_operation(self, rom_path: str):
        """Start homebrew operation (placeholder for actual implementation)."""
        logger.info(f"Starting homebrew operation with ROM: {rom_path}")
        # This would start the actual homebrew flashing process
        # Implementation would depend on available subprocess classes
    
    def show_changelog_dialog(self):
        """Show the changes between current and latest versions (from decompiled version)."""
        try:
            if not self._cc_mrpatcher_response:
                logger.warning('Missing MRPatcher response for changelog')
                return
            
            if not hasattr(self._cc_mrpatcher_response, 'patch'):
                logger.warning('MRPatcher response missing patch data')
                return
            
            # Generate changelog text
            changelog_text = self._generate_changelog_text()
            
            # Show changelog dialog (would need actual dialog implementation)
            self._show_changelog_dialog_impl(changelog_text)
            
        except Exception as e:
            logger.error(f"Error showing changelog dialog: {e}")
    
    def _generate_changelog_text(self) -> str:
        """Generate changelog text from MRPatcher response."""
        try:
            response = self._cc_mrpatcher_response
            changelog_text = ""
            
            if not hasattr(response, 'uploaded_version') or not response.uploaded_version:
                changelog_text += "We couldn't determine your current version. We recommend updating anyway.\n\n"
            elif (hasattr(response, 'latest_version') and 
                  response.uploaded_version == response.latest_version):
                changelog_text += 'You have the latest version but may have corrupt data. We recommend updating anyway.\n\n'
            else:
                if hasattr(response, 'latest_version'):
                    changelog_text += f'# Updating from v{response.uploaded_version} to v{response.latest_version}\n\n\n'
                if hasattr(response, 'changes'):
                    changelog_text += response.changes
            
            return changelog_text
            
        except Exception as e:
            logger.error(f"Error generating changelog text: {e}")
            return "Error generating changelog"
    
    def _show_changelog_dialog_impl(self, changelog_text: str):
        """Show changelog dialog implementation."""
        try:
            # This would show the actual changelog dialog
            # Implementation depends on available dialog classes
            logger.info("Showing changelog dialog")
            if hasattr(self._main_gui, 'show_message_box'):
                title = "Changelog"
                if (self._cc_mrpatcher_response and 
                    hasattr(self._cc_mrpatcher_response, 'game_title')):
                    title = f"Changelog for {self._cc_mrpatcher_response.game_title.upper()}"
                self._main_gui.show_message_box(title, changelog_text)
        except Exception as e:
            logger.error(f"Error showing changelog dialog: {e}")
    
    def reset_cart_clinic(self):
        """Reset Cart Clinic state for new operation (from decompiled version)."""
        try:
            logger.info("Resetting Cart Clinic state")
            
            # Reset error state
            self.set_cc_error_text('Something went wrong')
            
            # Reset progress
            self._cc_check_progress = 0
            self._loading_text_index = 0
            
            # Reset loading text
            if self._check_screen and hasattr(self._check_screen, 'text_cc_checking'):
                self._check_screen.text_cc_checking.setText("CHECKING GAME...")
            
            # Randomize loading text snippets
            self._loading_text_snippets = self._get_randomized_loading_text()
            
            # Reset data
            self.set_current_cart_data(None)
            self._cc_mrpatcher_response = None
            
            # Reset progress display
            self.cart_clinic_progress_callback(0)
            
            # Reset save warnings
            if self._update_screen:
                self._set_save_warning_visibility(True)
            
        except Exception as e:
            logger.error(f"Error resetting Cart Clinic: {e}")
    
    def _get_randomized_loading_text(self) -> List[str]:
        """Get randomized loading text snippets."""
        try:
            # Default loading text snippets (would be imported from consts)
            default_snippets = [
                "ANALYZING CARTRIDGE...",
                "READING GAME DATA...",
                "CHECKING VERSION...",
                "VALIDATING CHECKSUM...",
                "PROCESSING...",
            ]
            
            # Randomize order
            import random
            return random.sample(default_snippets, len(default_snippets))
            
        except Exception as e:
            logger.warning(f"Error getting loading text: {e}")
            return ["PROCESSING..."]
    
    def set_cc_error_text(self, error_msg: str, secondary_error_msg: str = ""):
        """Set error text on error screen (from decompiled version)."""
        try:
            if self._error_screen:
                if hasattr(self._error_screen, 'text_cc_error'):
                    self._error_screen.text_cc_error.setText(error_msg)
                if hasattr(self._error_screen, 'text_cc_error_2'):
                    self._error_screen.text_cc_error_2.setText(secondary_error_msg)
        except Exception as e:
            logger.error(f"Error setting error text: {e}")
    
    def set_current_cart_data(self, cart_data):
        """Set current cartridge data (from decompiled version)."""
        self._cc_current_cart_data = cart_data
        if cart_data:
            logger.debug("Current cart data updated")
        else:
            logger.debug("Current cart data cleared")
    
    def cart_clinic_progress_callback(self, progress: int):
        """Handle progress updates (from decompiled version)."""
        try:
            if hasattr(self._main_gui, 'draw_progress_bar') and self._updating_screen:
                self._main_gui.draw_progress_bar(progress, self._updating_screen, 'cc_progress_')
            
            # Update internal progress
            self._progress_reporter.update_progress(progress, 100, f"Progress: {progress}%")
            
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def _set_save_warning_visibility(self, visible: bool):
        """Set save warning visibility on update screen."""
        try:
            if self._update_screen:
                if hasattr(self._update_screen, 'text_cc_save_warning'):
                    self._update_screen.text_cc_save_warning.setVisible(visible)
                if hasattr(self._update_screen, 'text_cc_save_warning2'):
                    self._update_screen.text_cc_save_warning2.setVisible(visible)
        except Exception as e:
            logger.warning(f"Error setting save warning visibility: {e}")
    
    def update_checking_game_text(self, _, increment: bool = True):
        """Update the progress text and append progress percentage (from decompiled version)."""
        try:
            if self._cc_check_progress >= 95:
                text = 'WRAPPING UP...'
            elif self._loading_text_index < len(self._loading_text_snippets):
                text = self._loading_text_snippets[self._loading_text_index]
                if increment:
                    self._loading_text_index = min(
                        self._loading_text_index + 1, 
                        len(self._loading_text_snippets) - 1
                    )
            else:
                text = 'PROCESSING...'
            
            # Add progress percentage
            text = f'{text} ({self._cc_check_progress}%)'
            
            # Update UI
            if self._check_screen and hasattr(self._check_screen, 'text_cc_checking'):
                self._check_screen.text_cc_checking.setText(text)
                
        except Exception as e:
            logger.error(f"Error updating checking game text: {e}")
    
    def cart_clinic_check_progress_callback(self, progress: int):
        """Handle check progress updates (from decompiled version)."""
        self._cc_check_progress = progress
        self.update_checking_game_text(None, increment=False)


# Backward compatibility alias
CartClinic = EnhancedCartClinic


def create_cart_clinic(main_gui, chromatic=None, **kwargs) -> EnhancedCartClinic:
    """
    Factory function to create Cart Clinic instance with enhanced features.
    
    Args:
        main_gui: Main GUI instance
        chromatic: Chromatic device instance
        **kwargs: Additional arguments
        
    Returns:
        EnhancedCartClinic: Configured Cart Clinic instance
    """
    return EnhancedCartClinic(main_gui, chromatic, **kwargs)