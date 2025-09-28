"""
Enhanced UI utilities for the flashing tool.

This module provides utility functions and classes for enhanced UI operations,
including dynamic font sizing, responsive layouts, and improved user feedback.
"""

import logging
from typing import Optional, Dict, Any, Tuple, List
from enum import Enum
from dataclasses import dataclass

# Qt imports with fallback handling
try:
    from PySide6.QtCore import Qt, QSize, QRect
    from PySide6.QtGui import QFont, QFontMetrics, QPalette, QColor
    from PySide6.QtWidgets import QWidget, QLabel, QApplication
    QT_AVAILABLE = True
except ImportError:
    # Fallback for environments without Qt
    QT_AVAILABLE = False
    QWidget = object
    QLabel = object
    QFont = object
    QFontMetrics = object

logger = logging.getLogger('mrupdater')


class UITab(Enum):
    """UI tab identifiers."""
    SYSTEM = "system"
    CART_CLINIC = "cart_clinic"
    ABOUT = "about"
    MANUFACTURING = "manufacturing"


@dataclass
class FontConfig:
    """Configuration for dynamic font sizing."""
    
    base_size: int = 10
    min_size: int = 8
    max_size: int = 16
    scale_factor: float = 1.0
    font_family: str = "Arial"
    bold: bool = False
    italic: bool = False


@dataclass
class LayoutMetrics:
    """Metrics for responsive layout calculations."""
    
    widget_width: int = 0
    widget_height: int = 0
    content_width: int = 0
    content_height: int = 0
    available_space: int = 0
    scale_factor: float = 1.0


class ResponsiveLayoutManager:
    """Manager for responsive UI layouts."""
    
    def __init__(self):
        self._breakpoints = {
            'small': 480,
            'medium': 768,
            'large': 1024,
            'xlarge': 1200
        }
        self._current_breakpoint = 'medium'
    
    def get_breakpoint(self, width: int) -> str:
        """Get the current breakpoint based on width."""
        if width < self._breakpoints['small']:
            return 'xsmall'
        elif width < self._breakpoints['medium']:
            return 'small'
        elif width < self._breakpoints['large']:
            return 'medium'
        elif width < self._breakpoints['xlarge']:
            return 'large'
        else:
            return 'xlarge'
    
    def calculate_layout_metrics(self, widget: QWidget) -> LayoutMetrics:
        """Calculate layout metrics for a widget."""
        if not QT_AVAILABLE or not widget:
            return LayoutMetrics()
        
        size = widget.size()
        rect = widget.rect()
        
        return LayoutMetrics(
            widget_width=size.width(),
            widget_height=size.height(),
            content_width=rect.width(),
            content_height=rect.height(),
            available_space=min(size.width(), size.height()),
            scale_factor=self._calculate_scale_factor(size.width())
        )
    
    def _calculate_scale_factor(self, width: int) -> float:
        """Calculate scale factor based on width."""
        base_width = self._breakpoints['medium']
        return max(0.5, min(2.0, width / base_width))


class DynamicFontManager:
    """Manager for dynamic font sizing and styling."""
    
    def __init__(self):
        self._font_cache: Dict[str, QFont] = {}
        self._default_config = FontConfig()
    
    def set_dynamic_font_size(self, label: QLabel, config: Optional[FontConfig] = None):
        """
        Set dynamic font size for a label based on its content and size.
        
        Args:
            label: The label widget to update
            config: Font configuration (uses default if None)
        """
        if not QT_AVAILABLE or not label:
            return
        
        config = config or self._default_config
        
        try:
            # Get label dimensions
            label_rect = label.rect()
            text = label.text()
            
            if not text or label_rect.width() <= 0:
                return
            
            # Calculate optimal font size
            optimal_size = self._calculate_optimal_font_size(
                text, label_rect, config
            )
            
            # Create and apply font
            font = self._create_font(config, optimal_size)
            label.setFont(font)
            
            logger.debug(f"Set dynamic font size {optimal_size} for label: {text[:30]}...")
            
        except Exception as e:
            logger.error(f"Failed to set dynamic font size: {e}")
    
    def _calculate_optimal_font_size(self, text: str, rect: QRect, 
                                   config: FontConfig) -> int:
        """Calculate the optimal font size for given text and rectangle."""
        if not QT_AVAILABLE:
            return config.base_size
        
        # Start with base size and adjust
        font_size = config.base_size
        
        # Create test font
        test_font = self._create_font(config, font_size)
        metrics = QFontMetrics(test_font)
        
        # Adjust size to fit width
        text_width = metrics.horizontalAdvance(text)
        available_width = rect.width() - 20  # Leave some margin
        
        if available_width > 0:
            scale_factor = available_width / text_width
            font_size = int(font_size * scale_factor)
        
        # Clamp to min/max sizes
        font_size = max(config.min_size, min(config.max_size, font_size))
        
        return font_size
    
    def _create_font(self, config: FontConfig, size: int) -> QFont:
        """Create a font with the given configuration and size."""
        if not QT_AVAILABLE:
            return None
        
        # Check cache first
        cache_key = f"{config.font_family}_{size}_{config.bold}_{config.italic}"
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        # Create new font
        font = QFont(config.font_family, size)
        font.setBold(config.bold)
        font.setItalic(config.italic)
        
        # Cache the font
        self._font_cache[cache_key] = font
        
        return font
    
    def clear_font_cache(self):
        """Clear the font cache."""
        self._font_cache.clear()


class ThemeManager:
    """Manager for UI themes and styling."""
    
    def __init__(self):
        self._current_theme = "default"
        self._themes = {
            "default": self._get_default_theme(),
            "dark": self._get_dark_theme(),
            "high_contrast": self._get_high_contrast_theme()
        }
    
    def _get_default_theme(self) -> Dict[str, Any]:
        """Get the default theme configuration."""
        return {
            "background_color": "#ffffff",
            "text_color": "#000000",
            "accent_color": "#0078d4",
            "error_color": "#d13438",
            "warning_color": "#ff8c00",
            "success_color": "#107c10",
            "border_color": "#cccccc",
            "button_style": """
                QPushButton {
                    background-color: #0078d4;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """
        }
    
    def _get_dark_theme(self) -> Dict[str, Any]:
        """Get the dark theme configuration."""
        return {
            "background_color": "#2d2d30",
            "text_color": "#ffffff",
            "accent_color": "#0e639c",
            "error_color": "#f14c4c",
            "warning_color": "#ffb900",
            "success_color": "#6bb6ff",
            "border_color": "#3f3f46",
            "button_style": """
                QPushButton {
                    background-color: #0e639c;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QPushButton:pressed {
                    background-color: #0a4f7c;
                }
                QPushButton:disabled {
                    background-color: #555555;
                    color: #999999;
                }
            """
        }
    
    def _get_high_contrast_theme(self) -> Dict[str, Any]:
        """Get the high contrast theme configuration."""
        return {
            "background_color": "#000000",
            "text_color": "#ffffff",
            "accent_color": "#ffff00",
            "error_color": "#ff0000",
            "warning_color": "#ffff00",
            "success_color": "#00ff00",
            "border_color": "#ffffff",
            "button_style": """
                QPushButton {
                    background-color: #ffff00;
                    color: black;
                    border: 2px solid white;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #ffffff;
                    color: black;
                }
                QPushButton:pressed {
                    background-color: #cccccc;
                    color: black;
                }
                QPushButton:disabled {
                    background-color: #666666;
                    color: #999999;
                }
            """
        }
    
    def apply_theme(self, widget: QWidget, theme_name: str = None):
        """Apply a theme to a widget."""
        if not QT_AVAILABLE or not widget:
            return
        
        theme_name = theme_name or self._current_theme
        theme = self._themes.get(theme_name, self._themes["default"])
        
        try:
            # Apply theme styles
            stylesheet = f"""
                QWidget {{
                    background-color: {theme['background_color']};
                    color: {theme['text_color']};
                }}
                QLabel {{
                    color: {theme['text_color']};
                }}
                {theme['button_style']}
            """
            
            widget.setStyleSheet(stylesheet)
            
            logger.debug(f"Applied theme '{theme_name}' to widget")
            
        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self._current_theme
    
    def set_current_theme(self, theme_name: str):
        """Set the current theme."""
        if theme_name in self._themes:
            self._current_theme = theme_name
            logger.info(f"Theme changed to: {theme_name}")
        else:
            logger.warning(f"Unknown theme: {theme_name}")


class ProgressBarStyler:
    """Utility for styling progress bars with enhanced visual feedback."""
    
    @staticmethod
    def style_progress_bar(progress_bar, theme: str = "default"):
        """Apply enhanced styling to a progress bar."""
        if not QT_AVAILABLE or not progress_bar:
            return
        
        styles = {
            "default": """
                QProgressBar {
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #f0f0f0;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 3px;
                }
            """,
            "success": """
                QProgressBar {
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #f0f0f0;
                }
                QProgressBar::chunk {
                    background-color: #107c10;
                    border-radius: 3px;
                }
            """,
            "warning": """
                QProgressBar {
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #f0f0f0;
                }
                QProgressBar::chunk {
                    background-color: #ff8c00;
                    border-radius: 3px;
                }
            """,
            "error": """
                QProgressBar {
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #f0f0f0;
                }
                QProgressBar::chunk {
                    background-color: #d13438;
                    border-radius: 3px;
                }
            """
        }
        
        style = styles.get(theme, styles["default"])
        progress_bar.setStyleSheet(style)


# Global instances
_layout_manager = ResponsiveLayoutManager()
_font_manager = DynamicFontManager()
_theme_manager = ThemeManager()


def set_dynamic_font_size(label: QLabel, config: Optional[FontConfig] = None):
    """
    Global function to set dynamic font size for a label.
    
    Args:
        label: The label widget to update
        config: Font configuration (uses default if None)
    """
    _font_manager.set_dynamic_font_size(label, config)


def get_layout_manager() -> ResponsiveLayoutManager:
    """Get the global layout manager instance."""
    return _layout_manager


def get_font_manager() -> DynamicFontManager:
    """Get the global font manager instance."""
    return _font_manager


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    return _theme_manager


def apply_theme_to_widget(widget: QWidget, theme_name: str = None):
    """
    Apply a theme to a widget using the global theme manager.
    
    Args:
        widget: Widget to apply theme to
        theme_name: Theme name (uses current theme if None)
    """
    _theme_manager.apply_theme(widget, theme_name)


def calculate_responsive_size(base_size: int, widget: QWidget) -> int:
    """
    Calculate responsive size based on widget dimensions.
    
    Args:
        base_size: Base size value
        widget: Widget to calculate for
        
    Returns:
        int: Responsive size
    """
    if not QT_AVAILABLE or not widget:
        return base_size
    
    metrics = _layout_manager.calculate_layout_metrics(widget)
    return int(base_size * metrics.scale_factor)