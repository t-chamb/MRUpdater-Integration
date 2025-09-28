"""
Enhanced screen components for the flashing tool.

This module provides enhanced screen components integrated from the decompiled version,
including system update screens, cart clinic screens, and status displays with improved
user feedback and error handling.
"""

import logging
import time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Qt imports with fallback handling
try:
    from PySide6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QSize, QRect
    from PySide6.QtGui import QPixmap, QIcon, QFont, QMovie
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QProgressBar, QTextEdit, QFrame, QScrollArea, QSpacerItem, 
        QSizePolicy, QStackedWidget
    )
    QT_AVAILABLE = True
except ImportError:
    # Fallback for environments without Qt
    QT_AVAILABLE = False
    QWidget = object
    QTimer = object
    pyqtSignal = lambda: None

logger = logging.getLogger('mrupdater')


class ScreenType(Enum):
    """Types of screens available."""
    SYSTEM_CHECK = "system_check"
    SYSTEM_CONNECT = "system_connect"
    SYSTEM_UPDATE = "system_update"
    SYSTEM_UPDATING = "system_updating"
    SYSTEM_SUCCESS = "system_success"
    SYSTEM_ERROR = "system_error"
    SYSTEM_UPTODATE = "system_uptodate"
    SYSTEM_INTERNET = "system_internet"
    CC_START = "cc_start"
    CC_CHECK = "cc_check"
    CC_CONNECT = "cc_connect"
    CC_LOADING = "cc_loading"
    CC_UPDATE = "cc_update"
    CC_UPDATING = "cc_updating"
    CC_SUCCESS = "cc_success"
    CC_ERROR = "cc_error"
    CC_SAVE = "cc_save"
    CC_UPTODATE = "cc_uptodate"
    ABOUT = "about"


@dataclass
class ScreenConfig:
    """Configuration for screen appearance and behavior."""
    
    title: str = ""
    message: str = ""
    screen_type: ScreenType = ScreenType.SYSTEM_CHECK
    show_progress: bool = False
    show_buttons: bool = True
    auto_advance: bool = False
    auto_advance_delay: int = 3000  # milliseconds
    icon_path: Optional[str] = None
    background_image: Optional[str] = None


class BaseScreen(QWidget):
    """Base class for all screen components."""
    
    # Signals
    screen_completed = pyqtSignal(str)  # screen_id
    button_clicked = pyqtSignal(str)    # button_text
    progress_updated = pyqtSignal(int)  # progress_value
    
    def __init__(self, screen_id: str, config: ScreenConfig, parent=None):
        super().__init__(parent)
        self._screen_id = screen_id
        self._config = config
        self._progress_value = 0
        
        self._setup_ui()
        self._setup_connections()
        
        # Auto-advance timer if configured
        if config.auto_advance:
            self._auto_advance_timer = QTimer()
            self._auto_advance_timer.timeout.connect(self._handle_auto_advance)
            self._auto_advance_timer.setSingleShot(True)
    
    def _setup_ui(self):
        """Setup the screen UI. Override in subclasses."""
        if not QT_AVAILABLE:
            return
            
        # Main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setSpacing(20)
        self._main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Background
        if self._config.background_image:
            self._setup_background()
        
        # Content area
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setSpacing(15)
        
        # Title
        if self._config.title:
            self._title_label = QLabel(self._config.title)
            self._title_label.setAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(16)
            font.setBold(True)
            self._title_label.setFont(font)
            self._content_layout.addWidget(self._title_label)
        
        # Icon
        if self._config.icon_path:
            self._icon_label = QLabel()
            pixmap = QPixmap(self._config.icon_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._icon_label.setPixmap(scaled_pixmap)
                self._icon_label.setAlignment(Qt.AlignCenter)
                self._content_layout.addWidget(self._icon_label)
        
        # Message
        if self._config.message:
            self._message_label = QLabel(self._config.message)
            self._message_label.setWordWrap(True)
            self._message_label.setAlignment(Qt.AlignCenter)
            self._content_layout.addWidget(self._message_label)
        
        # Progress bar
        if self._config.show_progress:
            self._progress_bar = QProgressBar()
            self._progress_bar.setMinimum(0)
            self._progress_bar.setMaximum(100)
            self._progress_bar.setValue(0)
            self._content_layout.addWidget(self._progress_bar)
        
        # Spacer
        self._content_layout.addStretch()
        
        # Buttons
        if self._config.show_buttons:
            self._setup_buttons()
        
        self._main_layout.addWidget(self._content_widget)
    
    def _setup_background(self):
        """Setup background image."""
        if not QT_AVAILABLE:
            return
            
        try:
            self._background_label = QLabel(self)
            pixmap = QPixmap(self._config.background_image)
            if not pixmap.isNull():
                self._background_label.setPixmap(pixmap)
                self._background_label.setScaledContents(True)
                self._background_label.lower()  # Send to back
        except Exception as e:
            logger.warning(f"Failed to load background image: {e}")
    
    def _setup_buttons(self):
        """Setup default buttons. Override in subclasses for custom buttons."""
        if not QT_AVAILABLE:
            return
            
        self._button_layout = QHBoxLayout()
        self._button_layout.addStretch()
        
        # Default OK button
        self._ok_button = QPushButton("OK")
        self._ok_button.clicked.connect(lambda: self._handle_button_click("OK"))
        self._button_layout.addWidget(self._ok_button)
        
        self._content_layout.addLayout(self._button_layout)
    
    def _setup_connections(self):
        """Setup signal connections. Override in subclasses."""
        pass
    
    def _handle_button_click(self, button_text: str):
        """Handle button click."""
        self.button_clicked.emit(button_text)
        
        # Complete screen if it's a completion button
        if button_text in ["OK", "Continue", "Next", "Finish"]:
            self.screen_completed.emit(self._screen_id)
    
    def _handle_auto_advance(self):
        """Handle auto-advance timer."""
        self.screen_completed.emit(self._screen_id)
    
    def start_auto_advance(self):
        """Start the auto-advance timer."""
        if hasattr(self, '_auto_advance_timer') and self._config.auto_advance:
            self._auto_advance_timer.start(self._config.auto_advance_delay)
    
    def stop_auto_advance(self):
        """Stop the auto-advance timer."""
        if hasattr(self, '_auto_advance_timer'):
            self._auto_advance_timer.stop()
    
    def update_progress(self, value: int):
        """Update progress bar value."""
        self._progress_value = value
        if hasattr(self, '_progress_bar'):
            self._progress_bar.setValue(value)
        self.progress_updated.emit(value)
    
    def update_message(self, message: str):
        """Update the message text."""
        if hasattr(self, '_message_label'):
            self._message_label.setText(message)
    
    def get_screen_id(self) -> str:
        """Get the screen ID."""
        return self._screen_id


class SystemCheckScreen(BaseScreen):
    """System check screen with device detection."""
    
    def __init__(self, parent=None):
        config = ScreenConfig(
            title="System Check",
            message="Checking system compatibility and device connection...",
            screen_type=ScreenType.SYSTEM_CHECK,
            show_progress=True,
            show_buttons=False,
            auto_advance=True,
            auto_advance_delay=2000
        )
        super().__init__("system_check", config, parent)
    
    def _setup_ui(self):
        """Setup system check UI."""
        super()._setup_ui()
        
        if not QT_AVAILABLE:
            return
        
        # Add system info display
        self._system_info_frame = QFrame()
        self._system_info_frame.setFrameStyle(QFrame.StyledPanel)
        self._system_info_layout = QVBoxLayout(self._system_info_frame)
        
        self._system_info_label = QLabel("System Information:")
        self._system_info_label.setStyleSheet("font-weight: bold;")
        self._system_info_layout.addWidget(self._system_info_label)
        
        self._system_details = QLabel("Detecting system...")
        self._system_details.setWordWrap(True)
        self._system_info_layout.addWidget(self._system_details)
        
        # Insert before buttons
        self._content_layout.insertWidget(self._content_layout.count() - 2, self._system_info_frame)
    
    def update_system_info(self, info: str):
        """Update system information display."""
        if hasattr(self, '_system_details'):
            self._system_details.setText(info)


class SystemConnectScreen(BaseScreen):
    """System connect screen for device connection."""
    
    def __init__(self, parent=None):
        config = ScreenConfig(
            title="Connect Device",
            message="Please connect your Chromatic device and put it in update mode.",
            screen_type=ScreenType.SYSTEM_CONNECT,
            show_progress=False,
            show_buttons=True
        )
        super().__init__("system_connect", config, parent)
    
    def _setup_buttons(self):
        """Setup connect screen buttons."""
        if not QT_AVAILABLE:
            return
            
        self._button_layout = QHBoxLayout()
        
        self._retry_button = QPushButton("Retry")
        self._retry_button.clicked.connect(lambda: self._handle_button_click("Retry"))
        self._button_layout.addWidget(self._retry_button)
        
        self._button_layout.addStretch()
        
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.clicked.connect(lambda: self._handle_button_click("Cancel"))
        self._button_layout.addWidget(self._cancel_button)
        
        self._content_layout.addLayout(self._button_layout)


class SystemUpdatingScreen(BaseScreen):
    """System updating screen with detailed progress."""
    
    def __init__(self, parent=None):
        config = ScreenConfig(
            title="Updating System",
            message="Updating your Chromatic device firmware...",
            screen_type=ScreenType.SYSTEM_UPDATING,
            show_progress=True,
            show_buttons=False
        )
        super().__init__("system_updating", config, parent)
        self._current_step = ""
        self._total_steps = 0
        self._current_step_index = 0
    
    def _setup_ui(self):
        """Setup updating screen UI."""
        super()._setup_ui()
        
        if not QT_AVAILABLE:
            return
        
        # Add step indicator
        self._step_label = QLabel("Step 1 of 5: Preparing...")
        self._step_label.setAlignment(Qt.AlignCenter)
        self._step_label.setStyleSheet("color: #666; font-size: 10pt;")
        
        # Insert after progress bar
        progress_index = self._content_layout.indexOf(self._progress_bar)
        self._content_layout.insertWidget(progress_index + 1, self._step_label)
        
        # Add detailed status
        self._status_frame = QFrame()
        self._status_frame.setFrameStyle(QFrame.StyledPanel)
        self._status_frame.setMaximumHeight(100)
        
        self._status_layout = QVBoxLayout(self._status_frame)
        
        self._status_text = QTextEdit()
        self._status_text.setReadOnly(True)
        self._status_text.setMaximumHeight(80)
        self._status_layout.addWidget(self._status_text)
        
        # Insert before spacer
        self._content_layout.insertWidget(self._content_layout.count() - 2, self._status_frame)
    
    def update_step(self, step_index: int, total_steps: int, step_name: str):
        """Update the current step information."""
        self._current_step_index = step_index
        self._total_steps = total_steps
        self._current_step = step_name
        
        if hasattr(self, '_step_label'):
            self._step_label.setText(f"Step {step_index} of {total_steps}: {step_name}")
    
    def add_status_message(self, message: str):
        """Add a status message to the detailed status."""
        if hasattr(self, '_status_text'):
            timestamp = time.strftime('%H:%M:%S')
            self._status_text.append(f"[{timestamp}] {message}")
            
            # Auto-scroll to bottom
            scrollbar = self._status_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())


class SystemSuccessScreen(BaseScreen):
    """System update success screen."""
    
    def __init__(self, parent=None):
        config = ScreenConfig(
            title="Update Complete",
            message="Your Chromatic device has been successfully updated!",
            screen_type=ScreenType.SYSTEM_SUCCESS,
            show_progress=False,
            show_buttons=True,
            auto_advance=True,
            auto_advance_delay=5000
        )
        super().__init__("system_success", config, parent)
    
    def _setup_buttons(self):
        """Setup success screen buttons."""
        if not QT_AVAILABLE:
            return
            
        self._button_layout = QHBoxLayout()
        self._button_layout.addStretch()
        
        self._finish_button = QPushButton("Finish")
        self._finish_button.clicked.connect(lambda: self._handle_button_click("Finish"))
        self._finish_button.setDefault(True)
        self._button_layout.addWidget(self._finish_button)
        
        self._content_layout.addLayout(self._button_layout)


class SystemErrorScreen(BaseScreen):
    """System update error screen with recovery options."""
    
    def __init__(self, error_message: str = "", parent=None):
        config = ScreenConfig(
            title="Update Failed",
            message=f"An error occurred during the update: {error_message}",
            screen_type=ScreenType.SYSTEM_ERROR,
            show_progress=False,
            show_buttons=True
        )
        super().__init__("system_error", config, parent)
        self._error_message = error_message
    
    def _setup_ui(self):
        """Setup error screen UI."""
        super()._setup_ui()
        
        if not QT_AVAILABLE:
            return
        
        # Add error details frame
        self._error_frame = QFrame()
        self._error_frame.setFrameStyle(QFrame.StyledPanel)
        self._error_frame.setStyleSheet("background-color: #fff3cd; border: 1px solid #ffeaa7;")
        
        self._error_layout = QVBoxLayout(self._error_frame)
        
        self._error_details = QTextEdit()
        self._error_details.setPlainText(self._error_message)
        self._error_details.setReadOnly(True)
        self._error_details.setMaximumHeight(100)
        self._error_layout.addWidget(self._error_details)
        
        # Insert before buttons
        self._content_layout.insertWidget(self._content_layout.count() - 2, self._error_frame)
    
    def _setup_buttons(self):
        """Setup error screen buttons."""
        if not QT_AVAILABLE:
            return
            
        self._button_layout = QHBoxLayout()
        
        self._retry_button = QPushButton("Retry")
        self._retry_button.clicked.connect(lambda: self._handle_button_click("Retry"))
        self._button_layout.addWidget(self._retry_button)
        
        self._button_layout.addStretch()
        
        self._close_button = QPushButton("Close")
        self._close_button.clicked.connect(lambda: self._handle_button_click("Close"))
        self._button_layout.addWidget(self._close_button)
        
        self._content_layout.addLayout(self._button_layout)


class CartClinicStartScreen(BaseScreen):
    """Cart Clinic start screen."""
    
    def __init__(self, parent=None):
        config = ScreenConfig(
            title="Cart Clinic",
            message="Welcome to Cart Clinic. Connect your cartridge to get started.",
            screen_type=ScreenType.CC_START,
            show_progress=False,
            show_buttons=True
        )
        super().__init__("cc_start", config, parent)
    
    def _setup_buttons(self):
        """Setup start screen buttons."""
        if not QT_AVAILABLE:
            return
            
        self._button_layout = QHBoxLayout()
        self._button_layout.addStretch()
        
        self._start_button = QPushButton("Start")
        self._start_button.clicked.connect(lambda: self._handle_button_click("Start"))
        self._start_button.setDefault(True)
        self._button_layout.addWidget(self._start_button)
        
        self._content_layout.addLayout(self._button_layout)


class CartClinicUpdatingScreen(BaseScreen):
    """Cart Clinic updating screen with cartridge-specific progress."""
    
    def __init__(self, parent=None):
        config = ScreenConfig(
            title="Updating Cartridge",
            message="Updating your cartridge firmware...",
            screen_type=ScreenType.CC_UPDATING,
            show_progress=True,
            show_buttons=False
        )
        super().__init__("cc_updating", config, parent)
    
    def _setup_ui(self):
        """Setup cartridge updating UI."""
        super()._setup_ui()
        
        if not QT_AVAILABLE:
            return
        
        # Add cartridge info display
        self._cartridge_info_frame = QFrame()
        self._cartridge_info_frame.setFrameStyle(QFrame.StyledPanel)
        
        self._cartridge_info_layout = QVBoxLayout(self._cartridge_info_frame)
        
        self._cartridge_name_label = QLabel("Cartridge: Unknown")
        self._cartridge_name_label.setStyleSheet("font-weight: bold;")
        self._cartridge_info_layout.addWidget(self._cartridge_name_label)
        
        self._cartridge_details_label = QLabel("Detecting cartridge...")
        self._cartridge_details_label.setWordWrap(True)
        self._cartridge_info_layout.addWidget(self._cartridge_details_label)
        
        # Insert after message
        message_index = self._content_layout.indexOf(self._message_label)
        self._content_layout.insertWidget(message_index + 1, self._cartridge_info_frame)
    
    def update_cartridge_info(self, name: str, details: str):
        """Update cartridge information display."""
        if hasattr(self, '_cartridge_name_label'):
            self._cartridge_name_label.setText(f"Cartridge: {name}")
        if hasattr(self, '_cartridge_details_label'):
            self._cartridge_details_label.setText(details)


class AboutScreen(BaseScreen):
    """About screen with application information."""
    
    def __init__(self, version: str = "1.0.0", parent=None):
        config = ScreenConfig(
            title="About MRUpdater",
            message=f"MRUpdater Version {version}\n\nA tool for updating Chromatic devices and cartridges.",
            screen_type=ScreenType.ABOUT,
            show_progress=False,
            show_buttons=True
        )
        super().__init__("about", config, parent)
        self._version = version
    
    def _setup_ui(self):
        """Setup about screen UI."""
        super()._setup_ui()
        
        if not QT_AVAILABLE:
            return
        
        # Add logo/icon if available
        try:
            self._logo_label = QLabel()
            # Try to load application icon
            pixmap = QPixmap(":/images/icon.png")  # Resource path
            if pixmap.isNull():
                pixmap = QPixmap("icon.png")  # File path fallback
            
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._logo_label.setPixmap(scaled_pixmap)
                self._logo_label.setAlignment(Qt.AlignCenter)
                
                # Insert after title
                title_index = self._content_layout.indexOf(self._title_label)
                self._content_layout.insertWidget(title_index + 1, self._logo_label)
        except Exception as e:
            logger.debug(f"Could not load application logo: {e}")
        
        # Add additional info
        self._info_frame = QFrame()
        self._info_frame.setFrameStyle(QFrame.StyledPanel)
        
        self._info_layout = QVBoxLayout(self._info_frame)
        
        info_text = """
        Copyright © 2024 ModRetro
        
        This application is used to update Chromatic devices
        and manage cartridge firmware.
        
        For support and documentation, visit:
        https://www.modretro.com
        """
        
        self._info_label = QLabel(info_text.strip())
        self._info_label.setWordWrap(True)
        self._info_label.setAlignment(Qt.AlignCenter)
        self._info_layout.addWidget(self._info_label)
        
        # Insert before buttons
        self._content_layout.insertWidget(self._content_layout.count() - 2, self._info_frame)


class ScreenManager:
    """Manager for screen components and transitions."""
    
    def __init__(self, parent=None):
        self._parent = parent
        self._screens: Dict[str, BaseScreen] = {}
        self._current_screen: Optional[BaseScreen] = None
        
        if QT_AVAILABLE:
            self._stack_widget = QStackedWidget(parent)
        else:
            self._stack_widget = None
    
    def add_screen(self, screen: BaseScreen):
        """Add a screen to the manager."""
        screen_id = screen.get_screen_id()
        self._screens[screen_id] = screen
        
        if self._stack_widget:
            self._stack_widget.addWidget(screen)
        
        # Connect signals
        screen.screen_completed.connect(self._handle_screen_completed)
        screen.button_clicked.connect(self._handle_button_clicked)
    
    def show_screen(self, screen_id: str) -> bool:
        """Show a specific screen."""
        if screen_id not in self._screens:
            logger.error(f"Screen not found: {screen_id}")
            return False
        
        screen = self._screens[screen_id]
        self._current_screen = screen
        
        if self._stack_widget:
            self._stack_widget.setCurrentWidget(screen)
        
        # Start auto-advance if configured
        screen.start_auto_advance()
        
        logger.debug(f"Showing screen: {screen_id}")
        return True
    
    def get_current_screen(self) -> Optional[BaseScreen]:
        """Get the currently displayed screen."""
        return self._current_screen
    
    def get_stack_widget(self):
        """Get the stack widget for embedding in other UIs."""
        return self._stack_widget
    
    def _handle_screen_completed(self, screen_id: str):
        """Handle screen completion."""
        logger.debug(f"Screen completed: {screen_id}")
        # Override in subclasses to handle screen transitions
    
    def _handle_button_clicked(self, button_text: str):
        """Handle button clicks from screens."""
        logger.debug(f"Button clicked: {button_text}")
        # Override in subclasses to handle button actions


# Export all screen classes
__all__ = [
    'ScreenType',
    'ScreenConfig',
    'BaseScreen',
    'SystemCheckScreen',
    'SystemConnectScreen',
    'SystemUpdatingScreen',
    'SystemSuccessScreen',
    'SystemErrorScreen',
    'CartClinicStartScreen',
    'CartClinicUpdatingScreen',
    'AboutScreen',
    'ScreenManager'
]