"""
Enhanced GUI components for the flashing tool.

This module provides enhanced dialog systems, progress reporting, error handling
dialogs, and screen components integrated from the decompiled version while 
maintaining backward compatibility.
"""

import logging
import time
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Qt imports with fallback handling
try:
    from PySide6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
    from PySide6.QtGui import QPixmap, QIcon, QFont
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QProgressBar, QTextEdit, QMessageBox, QWidget, QFrame,
        QScrollArea, QCheckBox, QSpacerItem, QSizePolicy
    )
    QT_AVAILABLE = True
except ImportError:
    # Fallback for environments without Qt
    QT_AVAILABLE = False
    QDialog = object
    QWidget = object
    QObject = object
    QTimer = object
    pyqtSignal = lambda: None
    QThread = object

# Import enhanced components
from .screen_components import *
from .flasher_form import FlasherForm

logger = logging.getLogger('mrupdater')


class DialogType(Enum):
    """Types of dialogs available."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"
    PROGRESS = "progress"


@dataclass
class DialogConfig:
    """Configuration for dialog appearance and behavior."""
    
    title: str = "MRUpdater"
    message: str = ""
    dialog_type: DialogType = DialogType.INFO
    show_cancel: bool = False
    auto_close_timeout: Optional[int] = None
    custom_buttons: Optional[List[str]] = None
    icon_path: Optional[str] = None
    min_width: int = 400
    min_height: int = 200


class EnhancedProgressDialog(QDialog):
    """Enhanced progress dialog with detailed status and cancellation support."""
    
    # Signals
    cancelled = pyqtSignal()
    
    def __init__(self, config: DialogConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._is_cancelled = False
        self._start_time = time.time()
        self._estimated_time_remaining = None
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup the progress dialog UI."""
        if not QT_AVAILABLE:
            return
            
        self.setWindowTitle(self._config.title)
        self.setMinimumSize(self._config.min_width, self._config.min_height)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title label
        self._title_label = QLabel(self._config.message)
        self._title_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self._title_label.setFont(font)
        layout.addWidget(self._title_label)
        
        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)
        
        # Status label
        self._status_label = QLabel("Initializing...")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)
        
        # Detailed status (collapsible)
        self._details_frame = QFrame()
        self._details_frame.setFrameStyle(QFrame.StyledPanel)
        self._details_frame.setVisible(False)
        
        details_layout = QVBoxLayout(self._details_frame)
        
        self._details_text = QTextEdit()
        self._details_text.setMaximumHeight(100)
        self._details_text.setReadOnly(True)
        details_layout.addWidget(self._details_text)
        
        layout.addWidget(self._details_frame)
        
        # Time information
        self._time_label = QLabel("")
        self._time_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self._time_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Show/Hide details button
        self._details_button = QPushButton("Show Details")
        self._details_button.clicked.connect(self._toggle_details)
        button_layout.addWidget(self._details_button)
        
        button_layout.addStretch()
        
        # Cancel button
        if self._config.show_cancel:
            self._cancel_button = QPushButton("Cancel")
            self._cancel_button.clicked.connect(self._handle_cancel)
            button_layout.addWidget(self._cancel_button)
        
        layout.addLayout(button_layout)
        
        # Setup timer for time updates
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_time_display)
        self._timer.start(1000)  # Update every second
    
    def _setup_connections(self):
        """Setup signal connections."""
        pass
    
    def _toggle_details(self):
        """Toggle the visibility of detailed status."""
        if self._details_frame.isVisible():
            self._details_frame.setVisible(False)
            self._details_button.setText("Show Details")
            self.adjustSize()
        else:
            self._details_frame.setVisible(True)
            self._details_button.setText("Hide Details")
            self.adjustSize()
    
    def _handle_cancel(self):
        """Handle cancel button click."""
        self._is_cancelled = True
        self.cancelled.emit()
        
        # Update UI to show cancellation
        self._status_label.setText("Cancelling operation...")
        if hasattr(self, '_cancel_button'):
            self._cancel_button.setEnabled(False)
    
    def _update_time_display(self):
        """Update the time display with elapsed and estimated time."""
        elapsed = time.time() - self._start_time
        elapsed_str = f"Elapsed: {elapsed:.0f}s"
        
        if self._estimated_time_remaining:
            eta_str = f"ETA: {self._estimated_time_remaining:.0f}s"
            self._time_label.setText(f"{elapsed_str} | {eta_str}")
        else:
            self._time_label.setText(elapsed_str)
    
    def update_progress(self, value: int, message: str = "", details: str = ""):
        """
        Update the progress dialog.
        
        Args:
            value: Progress value (0-100)
            message: Status message
            details: Detailed status information
        """
        if not QT_AVAILABLE:
            return
            
        self._progress_bar.setValue(value)
        
        if message:
            self._status_label.setText(message)
        
        if details:
            self._details_text.append(f"[{time.strftime('%H:%M:%S')}] {details}")
            # Auto-scroll to bottom
            scrollbar = self._details_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        # Estimate time remaining
        if value > 0:
            elapsed = time.time() - self._start_time
            estimated_total = (elapsed / value) * 100
            self._estimated_time_remaining = estimated_total - elapsed
    
    def is_cancelled(self) -> bool:
        """Check if the operation was cancelled."""
        return self._is_cancelled
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if not self._is_cancelled:
            self._handle_cancel()
        super().closeEvent(event)


class EnhancedErrorDialog(QDialog):
    """Enhanced error dialog with detailed error information and recovery suggestions."""
    
    def __init__(self, title: str, message: str, details: str = "", 
                 recovery_suggestions: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._message = message
        self._details = details
        self._recovery_suggestions = recovery_suggestions or []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the error dialog UI."""
        if not QT_AVAILABLE:
            return
            
        self.setWindowTitle(self._title)
        self.setMinimumSize(450, 300)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Error icon and message
        header_layout = QHBoxLayout()
        
        # Error icon
        icon_label = QLabel()
        if hasattr(QMessageBox, 'Critical'):
            icon = self.style().standardIcon(self.style().SP_MessageBoxCritical)
            icon_label.setPixmap(icon.pixmap(48, 48))
        header_layout.addWidget(icon_label)
        
        # Error message
        message_label = QLabel(self._message)
        message_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        message_label.setFont(font)
        header_layout.addWidget(message_label, 1)
        
        layout.addLayout(header_layout)
        
        # Details section (collapsible)
        if self._details:
            self._details_frame = QFrame()
            self._details_frame.setFrameStyle(QFrame.StyledPanel)
            self._details_frame.setVisible(False)
            
            details_layout = QVBoxLayout(self._details_frame)
            
            details_text = QTextEdit()
            details_text.setPlainText(self._details)
            details_text.setReadOnly(True)
            details_text.setMaximumHeight(150)
            details_layout.addWidget(details_text)
            
            layout.addWidget(self._details_frame)
        
        # Recovery suggestions
        if self._recovery_suggestions:
            suggestions_label = QLabel("Suggested solutions:")
            suggestions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(suggestions_label)
            
            for suggestion in self._recovery_suggestions:
                suggestion_label = QLabel(f"• {suggestion}")
                suggestion_label.setWordWrap(True)
                suggestion_label.setStyleSheet("margin-left: 15px;")
                layout.addWidget(suggestion_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Show/Hide details button
        if self._details:
            self._details_button = QPushButton("Show Details")
            self._details_button.clicked.connect(self._toggle_details)
            button_layout.addWidget(self._details_button)
        
        button_layout.addStretch()
        
        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
    
    def _toggle_details(self):
        """Toggle the visibility of error details."""
        if hasattr(self, '_details_frame'):
            if self._details_frame.isVisible():
                self._details_frame.setVisible(False)
                self._details_button.setText("Show Details")
            else:
                self._details_frame.setVisible(True)
                self._details_button.setText("Hide Details")
            self.adjustSize()


class EnhancedChangelogDialog(QDialog):
    """Enhanced changelog dialog with better formatting and navigation."""
    
    def __init__(self, title: str, changelog_text: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._changelog_text = changelog_text
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the changelog dialog UI."""
        if not QT_AVAILABLE:
            return
            
        self.setWindowTitle(self._title)
        self.setMinimumSize(600, 400)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel(self._title)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Changelog content
        changelog_text = QTextEdit()
        changelog_text.setPlainText(self._changelog_text)
        changelog_text.setReadOnly(True)
        
        # Style the text area
        changelog_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        
        layout.addWidget(changelog_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)


class EnhancedAlertDialog(QDialog):
    """Enhanced alert dialog with customizable buttons and icons."""
    
    def __init__(self, config: DialogConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._result = None
        
        self._setup_ui()
        
        # Auto-close timer if specified
        if config.auto_close_timeout:
            self._auto_close_timer = QTimer()
            self._auto_close_timer.timeout.connect(self._auto_close)
            self._auto_close_timer.start(config.auto_close_timeout * 1000)
    
    def _setup_ui(self):
        """Setup the alert dialog UI."""
        if not QT_AVAILABLE:
            return
            
        self.setWindowTitle(self._config.title)
        self.setMinimumSize(self._config.min_width, self._config.min_height)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Content layout
        content_layout = QHBoxLayout()
        
        # Icon
        if self._config.icon_path or self._config.dialog_type != DialogType.INFO:
            icon_label = QLabel()
            icon = self._get_dialog_icon()
            if icon:
                icon_label.setPixmap(icon.pixmap(48, 48))
            content_layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(self._config.message)
        message_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(11)
        message_label.setFont(font)
        content_layout.addWidget(message_label, 1)
        
        layout.addLayout(content_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if self._config.custom_buttons:
            for button_text in self._config.custom_buttons:
                button = QPushButton(button_text)
                button.clicked.connect(lambda checked, text=button_text: self._handle_button_click(text))
                button_layout.addWidget(button)
        else:
            # Default buttons based on dialog type
            if self._config.dialog_type == DialogType.QUESTION:
                yes_button = QPushButton("Yes")
                yes_button.clicked.connect(lambda: self._handle_button_click("Yes"))
                button_layout.addWidget(yes_button)
                
                no_button = QPushButton("No")
                no_button.clicked.connect(lambda: self._handle_button_click("No"))
                button_layout.addWidget(no_button)
            else:
                ok_button = QPushButton("OK")
                ok_button.clicked.connect(lambda: self._handle_button_click("OK"))
                ok_button.setDefault(True)
                button_layout.addWidget(ok_button)
            
            if self._config.show_cancel:
                cancel_button = QPushButton("Cancel")
                cancel_button.clicked.connect(lambda: self._handle_button_click("Cancel"))
                button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _get_dialog_icon(self) -> Optional[QIcon]:
        """Get the appropriate icon for the dialog type."""
        if not QT_AVAILABLE:
            return None
            
        if self._config.icon_path:
            return QIcon(self._config.icon_path)
        
        style = self.style()
        icon_map = {
            DialogType.INFO: style.SP_MessageBoxInformation,
            DialogType.WARNING: style.SP_MessageBoxWarning,
            DialogType.ERROR: style.SP_MessageBoxCritical,
            DialogType.QUESTION: style.SP_MessageBoxQuestion
        }
        
        icon_type = icon_map.get(self._config.dialog_type)
        if icon_type:
            return style.standardIcon(icon_type)
        
        return None
    
    def _handle_button_click(self, button_text: str):
        """Handle button click."""
        self._result = button_text
        self.accept()
    
    def _auto_close(self):
        """Auto-close the dialog."""
        self._result = "Timeout"
        self.accept()
    
    def get_result(self) -> Optional[str]:
        """Get the dialog result."""
        return self._result


class EnhancedConsentDialog(QDialog):
    """Enhanced consent dialog with detailed terms and checkboxes."""
    
    def __init__(self, title: str, consent_text: str, 
                 required_checkboxes: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self._title = title
        self._consent_text = consent_text
        self._required_checkboxes = required_checkboxes or []
        self._checkboxes = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the consent dialog UI."""
        if not QT_AVAILABLE:
            return
            
        self.setWindowTitle(self._title)
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel(self._title)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        # Consent text in scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        consent_widget = QWidget()
        consent_layout = QVBoxLayout(consent_widget)
        
        consent_label = QLabel(self._consent_text)
        consent_label.setWordWrap(True)
        consent_label.setStyleSheet("padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd;")
        consent_layout.addWidget(consent_label)
        
        scroll_area.setWidget(consent_widget)
        layout.addWidget(scroll_area)
        
        # Required checkboxes
        if self._required_checkboxes:
            checkbox_frame = QFrame()
            checkbox_frame.setFrameStyle(QFrame.StyledPanel)
            checkbox_layout = QVBoxLayout(checkbox_frame)
            
            for checkbox_text in self._required_checkboxes:
                checkbox = QCheckBox(checkbox_text)
                checkbox.stateChanged.connect(self._update_accept_button)
                self._checkboxes[checkbox_text] = checkbox
                checkbox_layout.addWidget(checkbox)
            
            layout.addWidget(checkbox_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._accept_button = QPushButton("Accept")
        self._accept_button.clicked.connect(self.accept)
        self._accept_button.setEnabled(len(self._required_checkboxes) == 0)
        button_layout.addWidget(self._accept_button)
        
        decline_button = QPushButton("Decline")
        decline_button.clicked.connect(self.reject)
        button_layout.addWidget(decline_button)
        
        layout.addLayout(button_layout)
    
    def _update_accept_button(self):
        """Update the accept button state based on checkbox states."""
        if not QT_AVAILABLE:
            return
            
        all_checked = all(checkbox.isChecked() for checkbox in self._checkboxes.values())
        self._accept_button.setEnabled(all_checked)


class DialogManager:
    """Manager for creating and displaying enhanced dialogs."""
    
    def __init__(self, parent=None):
        self._parent = parent
        self._active_dialogs: List[QDialog] = []
    
    def show_progress_dialog(self, title: str, message: str, 
                           show_cancel: bool = True) -> EnhancedProgressDialog:
        """Show an enhanced progress dialog."""
        config = DialogConfig(
            title=title,
            message=message,
            dialog_type=DialogType.PROGRESS,
            show_cancel=show_cancel
        )
        
        dialog = EnhancedProgressDialog(config, self._parent)
        self._active_dialogs.append(dialog)
        dialog.show()
        
        return dialog
    
    def show_error_dialog(self, title: str, message: str, details: str = "",
                         recovery_suggestions: Optional[List[str]] = None) -> int:
        """Show an enhanced error dialog."""
        dialog = EnhancedErrorDialog(title, message, details, recovery_suggestions, self._parent)
        self._active_dialogs.append(dialog)
        
        result = dialog.exec()
        self._active_dialogs.remove(dialog)
        
        return result
    
    def show_alert_dialog(self, config: DialogConfig) -> str:
        """Show an enhanced alert dialog."""
        dialog = EnhancedAlertDialog(config, self._parent)
        self._active_dialogs.append(dialog)
        
        dialog.exec()
        result = dialog.get_result()
        self._active_dialogs.remove(dialog)
        
        return result or "Cancel"
    
    def show_changelog_dialog(self, title: str, changelog_text: str) -> int:
        """Show an enhanced changelog dialog."""
        dialog = EnhancedChangelogDialog(title, changelog_text, self._parent)
        self._active_dialogs.append(dialog)
        
        result = dialog.exec()
        self._active_dialogs.remove(dialog)
        
        return result
    
    def show_consent_dialog(self, title: str, consent_text: str,
                          required_checkboxes: Optional[List[str]] = None) -> bool:
        """Show an enhanced consent dialog."""
        dialog = EnhancedConsentDialog(title, consent_text, required_checkboxes, self._parent)
        self._active_dialogs.append(dialog)
        
        result = dialog.exec()
        self._active_dialogs.remove(dialog)
        
        return result == QDialog.Accepted if QT_AVAILABLE else True
    
    def close_all_dialogs(self):
        """Close all active dialogs."""
        for dialog in self._active_dialogs[:]:  # Copy list to avoid modification during iteration
            dialog.close()
        self._active_dialogs.clear()


# Backward compatibility aliases
AlertDialog = EnhancedAlertDialog
ChangelogDialog = EnhancedChangelogDialog
ConsentDialog = EnhancedConsentDialog
ErrorDialog = EnhancedErrorDialog

# Export all dialog and screen classes
__all__ = [
    # Dialog classes
    'DialogType',
    'DialogConfig',
    'EnhancedProgressDialog',
    'EnhancedErrorDialog',
    'EnhancedChangelogDialog',
    'EnhancedAlertDialog',
    'EnhancedConsentDialog',
    'DialogManager',
    'AlertDialog',
    'ChangelogDialog',
    'ConsentDialog',
    'ErrorDialog',
    # Screen classes (imported from screen_components)
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
    'ScreenManager',
    # Main form
    'FlasherForm'
]