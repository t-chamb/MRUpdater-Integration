"""
Enhanced flasher form for the flashing tool.

This module provides the main flasher form UI integrated from the decompiled version,
with enhanced tab management, responsive design, and improved user experience.
"""

import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

# Qt imports with fallback handling
try:
    from PySide6.QtCore import Qt, QSize, QRect, QPoint, pyqtSignal, QTimer
    from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor, QPalette
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QStackedWidget, QFrame, QSizePolicy, QApplication
    )
    QT_AVAILABLE = True
except ImportError:
    # Fallback for environments without Qt
    QT_AVAILABLE = False
    QWidget = object
    pyqtSignal = lambda: None

from .ui_util import UITab, get_theme_manager, apply_theme_to_widget
from .screen_components import ScreenManager, ScreenType

logger = logging.getLogger('mrupdater')


class FlasherForm(QWidget):
    """Enhanced main flasher form with integrated UI components."""
    
    # Signals
    tab_changed = pyqtSignal(str)  # tab_name
    close_requested = pyqtSignal()
    manual_link_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tab = UITab.SYSTEM
        self._tab_widgets: Dict[UITab, QWidget] = {}
        self._screen_managers: Dict[UITab, ScreenManager] = {}
        
        self._setup_ui()
        self._setup_connections()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the main flasher form UI."""
        if not QT_AVAILABLE:
            return
        
        # Set window properties
        self.setObjectName("FlasherForm")
        self.resize(625, 432)
        self.setWindowFlags(Qt.FramelessWindowHint)  # Frameless window
        
        # Set font
        font = QFont()
        font.setPointSize(9)
        self.setFont(font)
        
        # Main layout (absolute positioning to match decompiled version)
        self.setLayout(None)  # Use absolute positioning
        
        # Background
        self._setup_background()
        
        # Title bar and controls
        self._setup_title_bar()
        
        # Tab buttons
        self._setup_tab_buttons()
        
        # Content area
        self._setup_content_area()
        
        # Footer
        self._setup_footer()
        
        # Splash screen
        self._setup_splash()
    
    def _setup_background(self):
        """Setup background image."""
        if not QT_AVAILABLE:
            return
        
        self._bg_label = QLabel(self)
        self._bg_label.setObjectName("bg")
        self._bg_label.setGeometry(QRect(0, 0, 625, 432))
        
        # Try to load background image
        try:
            pixmap = QPixmap(":/images/bg.png")  # Resource path
            if pixmap.isNull():
                pixmap = QPixmap("images/bg.png")  # File path fallback
            
            if not pixmap.isNull():
                self._bg_label.setPixmap(pixmap)
                self._bg_label.setScaledContents(True)
            else:
                # Fallback to solid color
                self._bg_label.setStyleSheet("background-color: #2d2d30;")
        except Exception as e:
            logger.debug(f"Could not load background image: {e}")
            self._bg_label.setStyleSheet("background-color: #2d2d30;")
        
        self._bg_label.lower()  # Send to back
    
    def _setup_title_bar(self):
        """Setup title bar with close button and drag area."""
        if not QT_AVAILABLE:
            return
        
        # Close button
        self._close_btn = QPushButton(self)
        self._close_btn.setObjectName("close_btn")
        self._close_btn.setGeometry(QRect(585, 18, 24, 23))
        self._close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Try to load close icon
        try:
            icon = QIcon(":/images/x_btn.png")
            if icon.isNull():
                icon = QIcon("images/x_btn.png")
            
            if not icon.isNull():
                self._close_btn.setIcon(icon)
                self._close_btn.setIconSize(QSize(24, 23))
            else:
                self._close_btn.setText("×")
        except Exception as e:
            logger.debug(f"Could not load close icon: {e}")
            self._close_btn.setText("×")
        
        # Drag area
        self._dragger = QLabel(self)
        self._dragger.setObjectName("dragger")
        self._dragger.setGeometry(QRect(30, 46, 560, 49))
        self._dragger.setCursor(QCursor(Qt.OpenHandCursor))
        
        # Mouse tracking for window dragging
        self._drag_position = QPoint()
        self._dragger.mousePressEvent = self._start_drag
        self._dragger.mouseMoveEvent = self._perform_drag
    
    def _setup_tab_buttons(self):
        """Setup tab navigation buttons."""
        if not QT_AVAILABLE:
            return
        
        # System tab button
        self._btn_tab_system = QPushButton(self)
        self._btn_tab_system.setObjectName("btn_tab_system")
        self._btn_tab_system.setGeometry(QRect(40, 15, 35, 30))
        self._btn_tab_system.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_tab_system.setToolTip("System Update")
        
        # Cart Clinic tab button
        self._btn_tab_cartclinic = QPushButton(self)
        self._btn_tab_cartclinic.setObjectName("btn_tab_cartclinic")
        self._btn_tab_cartclinic.setGeometry(QRect(86, 15, 35, 30))
        self._btn_tab_cartclinic.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_tab_cartclinic.setToolTip("Cart Clinic")
        
        # About tab button
        self._btn_tab_about = QPushButton(self)
        self._btn_tab_about.setObjectName("btn_tab_about")
        self._btn_tab_about.setGeometry(QRect(131, 15, 35, 30))
        self._btn_tab_about.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_tab_about.setToolTip("About")
        
        # Manufacturing tab button (hidden by default)
        self._btn_tab_manufacturing = QPushButton(self)
        self._btn_tab_manufacturing.setObjectName("btn_tab_manufacturing")
        self._btn_tab_manufacturing.setGeometry(QRect(515, 12, 42, 38))
        self._btn_tab_manufacturing.setCursor(QCursor(Qt.PointingHandCursor))
        self._btn_tab_manufacturing.setVisible(False)  # Hidden by default
        
        # Try to load tab icons
        self._load_tab_icons()
        
        # Style tab buttons
        tab_button_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """
        
        for button in [self._btn_tab_system, self._btn_tab_cartclinic, 
                      self._btn_tab_about, self._btn_tab_manufacturing]:
            button.setStyleSheet(tab_button_style)
    
    def _load_tab_icons(self):
        """Load icons for tab buttons."""
        if not QT_AVAILABLE:
            return
        
        try:
            # System tab icon
            system_icon = QIcon(":/images/tab1_btn.png")
            if system_icon.isNull():
                system_icon = QIcon("images/tab1_btn.png")
            if not system_icon.isNull():
                self._btn_tab_system.setIcon(system_icon)
                self._btn_tab_system.setIconSize(QSize(35, 30))
            
            # Cart Clinic tab icon
            cc_icon = QIcon(":/images/tab2_btn.png")
            if cc_icon.isNull():
                cc_icon = QIcon("images/tab2_btn.png")
            if not cc_icon.isNull():
                self._btn_tab_cartclinic.setIcon(cc_icon)
                self._btn_tab_cartclinic.setIconSize(QSize(35, 30))
            
            # About tab icon
            about_icon = QIcon(":/images/tab3_btn.png")
            if about_icon.isNull():
                about_icon = QIcon("images/tab3_btn.png")
            if not about_icon.isNull():
                self._btn_tab_about.setIcon(about_icon)
                self._btn_tab_about.setIconSize(QSize(35, 30))
            
            # Manufacturing tab icon
            mfg_icon = QIcon(":/fonts/images/tab4_btn.png")
            if mfg_icon.isNull():
                mfg_icon = QIcon("images/tab4_btn.png")
            if not mfg_icon.isNull():
                self._btn_tab_manufacturing.setIcon(mfg_icon)
                self._btn_tab_manufacturing.setIconSize(QSize(42, 38))
                
        except Exception as e:
            logger.debug(f"Could not load tab icons: {e}")
    
    def _setup_content_area(self):
        """Setup the main content area with tab widgets."""
        if not QT_AVAILABLE:
            return
        
        # Content area geometry
        content_rect = QRect(0, 95, 625, 300)
        
        # System tab
        self._tab_system = QWidget(self)
        self._tab_system.setObjectName("tab_system")
        self._tab_system.setGeometry(content_rect)
        self._tab_widgets[UITab.SYSTEM] = self._tab_system
        
        # Cart Clinic tab
        self._tab_cartclinic = QWidget(self)
        self._tab_cartclinic.setObjectName("tab_cartclinic")
        self._tab_cartclinic.setGeometry(content_rect)
        self._tab_widgets[UITab.CART_CLINIC] = self._tab_cartclinic
        
        # About tab
        self._tab_about = QWidget(self)
        self._tab_about.setObjectName("tab_about")
        self._tab_about.setGeometry(content_rect)
        self._tab_widgets[UITab.ABOUT] = self._tab_about
        
        # Manufacturing tab
        self._tab_manufacturing = QWidget(self)
        self._tab_manufacturing.setObjectName("tab_manufacturing")
        self._tab_manufacturing.setGeometry(content_rect)
        self._tab_widgets[UITab.MANUFACTURING] = self._tab_manufacturing
        
        # Setup screen managers for each tab
        self._setup_screen_managers()
        
        # Show initial tab
        self._show_tab(UITab.SYSTEM)
    
    def _setup_screen_managers(self):
        """Setup screen managers for each tab."""
        if not QT_AVAILABLE:
            return
        
        # System tab screen manager
        system_manager = ScreenManager(self._tab_system)
        self._screen_managers[UITab.SYSTEM] = system_manager
        
        # Add system screens
        from .screen_components import (
            SystemCheckScreen, SystemConnectScreen, SystemUpdatingScreen,
            SystemSuccessScreen, SystemErrorScreen
        )
        
        system_manager.add_screen(SystemCheckScreen())
        system_manager.add_screen(SystemConnectScreen())
        system_manager.add_screen(SystemUpdatingScreen())
        system_manager.add_screen(SystemSuccessScreen())
        system_manager.add_screen(SystemErrorScreen())
        
        # Layout system tab
        system_layout = QVBoxLayout(self._tab_system)
        system_layout.setContentsMargins(0, 0, 0, 0)
        system_layout.addWidget(system_manager.get_stack_widget())
        
        # Cart Clinic tab screen manager
        cc_manager = ScreenManager(self._tab_cartclinic)
        self._screen_managers[UITab.CART_CLINIC] = cc_manager
        
        # Add Cart Clinic screens
        from .screen_components import (
            CartClinicStartScreen, CartClinicUpdatingScreen
        )
        
        cc_manager.add_screen(CartClinicStartScreen())
        cc_manager.add_screen(CartClinicUpdatingScreen())
        
        # Layout Cart Clinic tab
        cc_layout = QVBoxLayout(self._tab_cartclinic)
        cc_layout.setContentsMargins(0, 0, 0, 0)
        cc_layout.addWidget(cc_manager.get_stack_widget())
        
        # About tab screen manager
        about_manager = ScreenManager(self._tab_about)
        self._screen_managers[UITab.ABOUT] = about_manager
        
        # Add About screen
        from .screen_components import AboutScreen
        about_manager.add_screen(AboutScreen())
        
        # Layout About tab
        about_layout = QVBoxLayout(self._tab_about)
        about_layout.setContentsMargins(0, 0, 0, 0)
        about_layout.addWidget(about_manager.get_stack_widget())
    
    def _setup_footer(self):
        """Setup footer with manual link."""
        if not QT_AVAILABLE:
            return
        
        # Manual link button
        self._chromatic_manual_link = QPushButton(self)
        self._chromatic_manual_link.setObjectName("chromatic_manual_link")
        self._chromatic_manual_link.setGeometry(QRect(35, 381, 100, 22))
        self._chromatic_manual_link.setCursor(QCursor(Qt.PointingHandCursor))
        
        # Try to load manual link icon
        try:
            icon = QIcon(":/images/manual_link.png")
            if icon.isNull():
                icon = QIcon("images/manual_link.png")
            
            if not icon.isNull():
                self._chromatic_manual_link.setIcon(icon)
                self._chromatic_manual_link.setIconSize(QSize(100, 22))
            else:
                self._chromatic_manual_link.setText("Manual")
        except Exception as e:
            logger.debug(f"Could not load manual link icon: {e}")
            self._chromatic_manual_link.setText("Manual")
    
    def _setup_splash(self):
        """Setup splash screen overlay."""
        if not QT_AVAILABLE:
            return
        
        self._splash = QLabel(self)
        self._splash.setObjectName("splash")
        self._splash.setGeometry(QRect(0, 0, 625, 432))
        self._splash.setAlignment(Qt.AlignCenter)
        
        # Try to load splash image
        try:
            pixmap = QPixmap(":/images/title.png")
            if pixmap.isNull():
                pixmap = QPixmap("images/title.png")
            
            if not pixmap.isNull():
                self._splash.setPixmap(pixmap)
                self._splash.setScaledContents(True)
            else:
                # Fallback text
                self._splash.setText("MRUpdater")
                self._splash.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        except Exception as e:
            logger.debug(f"Could not load splash image: {e}")
            self._splash.setText("MRUpdater")
            self._splash.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        # Hide splash after a delay
        self._splash_timer = QTimer()
        self._splash_timer.timeout.connect(self._hide_splash)
        self._splash_timer.setSingleShot(True)
        self._splash_timer.start(2000)  # 2 seconds
    
    def _setup_connections(self):
        """Setup signal connections."""
        if not QT_AVAILABLE:
            return
        
        # Tab button connections
        self._btn_tab_system.clicked.connect(lambda: self._switch_tab(UITab.SYSTEM))
        self._btn_tab_cartclinic.clicked.connect(lambda: self._switch_tab(UITab.CART_CLINIC))
        self._btn_tab_about.clicked.connect(lambda: self._switch_tab(UITab.ABOUT))
        self._btn_tab_manufacturing.clicked.connect(lambda: self._switch_tab(UITab.MANUFACTURING))
        
        # Close button connection
        self._close_btn.clicked.connect(self.close_requested.emit)
        
        # Manual link connection
        self._chromatic_manual_link.clicked.connect(self.manual_link_clicked.emit)
    
    def _apply_styling(self):
        """Apply styling to the form."""
        if not QT_AVAILABLE:
            return
        
        # Main form styling
        self.setStyleSheet("""
            QWidget {
                color: rgb(255, 255, 255);
                background: transparent;
            }
        """)
        
        # Apply theme
        apply_theme_to_widget(self, "dark")
    
    def _start_drag(self, event):
        """Start window dragging."""
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def _perform_drag(self, event):
        """Perform window dragging."""
        if event.buttons() == Qt.LeftButton and hasattr(self, '_drag_position'):
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
    
    def _hide_splash(self):
        """Hide the splash screen."""
        if hasattr(self, '_splash'):
            self._splash.hide()
    
    def _show_tab(self, tab: UITab):
        """Show a specific tab."""
        if not QT_AVAILABLE:
            return
        
        # Hide all tabs
        for tab_widget in self._tab_widgets.values():
            tab_widget.hide()
        
        # Show selected tab
        if tab in self._tab_widgets:
            self._tab_widgets[tab].show()
            self._current_tab = tab
            
            # Update tab button states
            self._update_tab_button_states()
            
            # Show initial screen for the tab
            if tab in self._screen_managers:
                manager = self._screen_managers[tab]
                if tab == UITab.SYSTEM:
                    manager.show_screen("system_check")
                elif tab == UITab.CART_CLINIC:
                    manager.show_screen("cc_start")
                elif tab == UITab.ABOUT:
                    manager.show_screen("about")
            
            self.tab_changed.emit(tab.value)
            logger.debug(f"Switched to tab: {tab.value}")
    
    def _switch_tab(self, tab: UITab):
        """Switch to a specific tab."""
        if tab != self._current_tab:
            self._show_tab(tab)
    
    def _update_tab_button_states(self):
        """Update tab button visual states."""
        if not QT_AVAILABLE:
            return
        
        # Reset all button styles
        normal_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """
        
        active_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """
        
        # Apply styles based on current tab
        self._btn_tab_system.setStyleSheet(
            active_style if self._current_tab == UITab.SYSTEM else normal_style
        )
        self._btn_tab_cartclinic.setStyleSheet(
            active_style if self._current_tab == UITab.CART_CLINIC else normal_style
        )
        self._btn_tab_about.setStyleSheet(
            active_style if self._current_tab == UITab.ABOUT else normal_style
        )
        self._btn_tab_manufacturing.setStyleSheet(
            active_style if self._current_tab == UITab.MANUFACTURING else normal_style
        )
    
    def get_current_tab(self) -> UITab:
        """Get the currently active tab."""
        return self._current_tab
    
    def get_screen_manager(self, tab: UITab) -> Optional[ScreenManager]:
        """Get the screen manager for a specific tab."""
        return self._screen_managers.get(tab)
    
    def show_manufacturing_tab(self, show: bool = True):
        """Show or hide the manufacturing tab."""
        if hasattr(self, '_btn_tab_manufacturing'):
            self._btn_tab_manufacturing.setVisible(show)
    
    def set_splash_visible(self, visible: bool):
        """Set splash screen visibility."""
        if hasattr(self, '_splash'):
            self._splash.setVisible(visible)


# Export the main form class
__all__ = ['FlasherForm']