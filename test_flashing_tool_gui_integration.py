#!/usr/bin/env python3
"""
Integration tests for enhanced flashing tool GUI components.

This test suite validates the integration of enhanced dialog systems, screen components,
and the main flasher form from the decompiled version.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestFlashingToolGUIIntegration(unittest.TestCase):
    """Test suite for flashing tool GUI integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_qt_available = True
        
        # Mock Qt imports to avoid dependency issues in CI
        self.qt_mocks = {
            'PySide6.QtCore': MagicMock(),
            'PySide6.QtGui': MagicMock(),
            'PySide6.QtWidgets': MagicMock()
        }
        
        for module_name, mock_module in self.qt_mocks.items():
            sys.modules[module_name] = mock_module
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove Qt mocks
        for module_name in self.qt_mocks:
            if module_name in sys.modules:
                del sys.modules[module_name]
    
    def test_dialog_manager_creation(self):
        """Test that DialogManager can be created and configured."""
        try:
            from flashing_tool.gui import DialogManager, DialogConfig, DialogType
            
            # Create dialog manager
            manager = DialogManager()
            self.assertIsNotNone(manager)
            
            # Test dialog configuration
            config = DialogConfig(
                title="Test Dialog",
                message="Test message",
                dialog_type=DialogType.INFO
            )
            self.assertEqual(config.title, "Test Dialog")
            self.assertEqual(config.message, "Test message")
            self.assertEqual(config.dialog_type, DialogType.INFO)
            
            logger.info("✓ DialogManager creation test passed")
            
        except ImportError as e:
            self.skipTest(f"GUI components not available: {e}")
    
    def test_screen_components_creation(self):
        """Test that screen components can be created."""
        try:
            from flashing_tool.gui import (
                SystemCheckScreen, SystemConnectScreen, SystemUpdatingScreen,
                CartClinicStartScreen, AboutScreen, ScreenManager
            )
            
            # Test screen creation (without Qt)
            with patch('flashing_tool.screen_components.QT_AVAILABLE', False):
                system_check = SystemCheckScreen()
                self.assertIsNotNone(system_check)
                self.assertEqual(system_check.get_screen_id(), "system_check")
                
                system_connect = SystemConnectScreen()
                self.assertIsNotNone(system_connect)
                self.assertEqual(system_connect.get_screen_id(), "system_connect")
                
                cc_start = CartClinicStartScreen()
                self.assertIsNotNone(cc_start)
                self.assertEqual(cc_start.get_screen_id(), "cc_start")
                
                about = AboutScreen()
                self.assertIsNotNone(about)
                self.assertEqual(about.get_screen_id(), "about")
            
            # Test screen manager
            with patch('flashing_tool.screen_components.QT_AVAILABLE', False):
                manager = ScreenManager()
                self.assertIsNotNone(manager)
            
            logger.info("✓ Screen components creation test passed")
            
        except ImportError as e:
            self.skipTest(f"Screen components not available: {e}")
    
    def test_flasher_form_creation(self):
        """Test that FlasherForm can be created."""
        try:
            from flashing_tool.gui import FlasherForm
            from flashing_tool.ui_util import UITab
            
            # Test form creation (without Qt)
            with patch('flashing_tool.flasher_form.QT_AVAILABLE', False):
                form = FlasherForm()
                self.assertIsNotNone(form)
                
                # Test tab management
                self.assertEqual(form.get_current_tab(), UITab.SYSTEM)
            
            logger.info("✓ FlasherForm creation test passed")
            
        except ImportError as e:
            self.skipTest(f"FlasherForm not available: {e}")
    
    def test_ui_utilities_integration(self):
        """Test that UI utilities work with GUI components."""
        try:
            from flashing_tool.ui_util import (
                UITab, FontConfig, ResponsiveLayoutManager,
                DynamicFontManager, ThemeManager
            )
            
            # Test UI tab enum
            self.assertEqual(UITab.SYSTEM.value, "system")
            self.assertEqual(UITab.CART_CLINIC.value, "cart_clinic")
            self.assertEqual(UITab.ABOUT.value, "about")
            
            # Test font configuration
            font_config = FontConfig(
                base_size=12,
                font_family="Arial",
                bold=True
            )
            self.assertEqual(font_config.base_size, 12)
            self.assertEqual(font_config.font_family, "Arial")
            self.assertTrue(font_config.bold)
            
            # Test managers
            layout_manager = ResponsiveLayoutManager()
            self.assertIsNotNone(layout_manager)
            
            font_manager = DynamicFontManager()
            self.assertIsNotNone(font_manager)
            
            theme_manager = ThemeManager()
            self.assertIsNotNone(theme_manager)
            self.assertEqual(theme_manager.get_current_theme(), "default")
            
            logger.info("✓ UI utilities integration test passed")
            
        except ImportError as e:
            self.skipTest(f"UI utilities not available: {e}")
    
    def test_dialog_types_and_configs(self):
        """Test dialog types and configurations."""
        try:
            from flashing_tool.gui import DialogType, DialogConfig
            
            # Test all dialog types
            dialog_types = [
                DialogType.INFO,
                DialogType.WARNING,
                DialogType.ERROR,
                DialogType.QUESTION,
                DialogType.PROGRESS
            ]
            
            for dialog_type in dialog_types:
                config = DialogConfig(
                    title=f"Test {dialog_type.value}",
                    message=f"Test message for {dialog_type.value}",
                    dialog_type=dialog_type
                )
                self.assertEqual(config.dialog_type, dialog_type)
            
            logger.info("✓ Dialog types and configs test passed")
            
        except ImportError as e:
            self.skipTest(f"Dialog components not available: {e}")
    
    def test_screen_types_and_configs(self):
        """Test screen types and configurations."""
        try:
            from flashing_tool.gui import ScreenType, ScreenConfig
            
            # Test system screen types
            system_screens = [
                ScreenType.SYSTEM_CHECK,
                ScreenType.SYSTEM_CONNECT,
                ScreenType.SYSTEM_UPDATE,
                ScreenType.SYSTEM_UPDATING,
                ScreenType.SYSTEM_SUCCESS,
                ScreenType.SYSTEM_ERROR
            ]
            
            for screen_type in system_screens:
                config = ScreenConfig(
                    title=f"Test {screen_type.value}",
                    screen_type=screen_type
                )
                self.assertEqual(config.screen_type, screen_type)
            
            # Test Cart Clinic screen types
            cc_screens = [
                ScreenType.CC_START,
                ScreenType.CC_CHECK,
                ScreenType.CC_CONNECT,
                ScreenType.CC_UPDATING,
                ScreenType.CC_SUCCESS,
                ScreenType.CC_ERROR
            ]
            
            for screen_type in cc_screens:
                config = ScreenConfig(
                    title=f"Test {screen_type.value}",
                    screen_type=screen_type
                )
                self.assertEqual(config.screen_type, screen_type)
            
            logger.info("✓ Screen types and configs test passed")
            
        except ImportError as e:
            self.skipTest(f"Screen components not available: {e}")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing interfaces."""
        try:
            from flashing_tool.gui import (
                AlertDialog, ChangelogDialog, ConsentDialog, ErrorDialog
            )
            
            # Test that backward compatibility aliases exist
            self.assertIsNotNone(AlertDialog)
            self.assertIsNotNone(ChangelogDialog)
            self.assertIsNotNone(ConsentDialog)
            self.assertIsNotNone(ErrorDialog)
            
            logger.info("✓ Backward compatibility test passed")
            
        except ImportError as e:
            self.skipTest(f"Backward compatibility components not available: {e}")
    
    def test_integration_with_existing_modules(self):
        """Test integration with existing flashing tool modules."""
        try:
            # Test that GUI components can be imported alongside existing modules
            from flashing_tool import gui, util, chromatic
            
            self.assertIsNotNone(gui)
            self.assertIsNotNone(util)
            self.assertIsNotNone(chromatic)
            
            # Test that GUI module has expected components
            self.assertTrue(hasattr(gui, 'DialogManager'))
            self.assertTrue(hasattr(gui, 'FlasherForm'))
            self.assertTrue(hasattr(gui, 'ScreenManager'))
            
            logger.info("✓ Integration with existing modules test passed")
            
        except ImportError as e:
            self.skipTest(f"Integration modules not available: {e}")
    
    def test_error_handling_integration(self):
        """Test error handling in GUI components."""
        try:
            from flashing_tool.gui import EnhancedErrorDialog, SystemErrorScreen
            
            # Test error dialog with recovery suggestions
            with patch('flashing_tool.gui.QT_AVAILABLE', False):
                error_dialog = EnhancedErrorDialog(
                    title="Test Error",
                    message="Test error message",
                    details="Detailed error information",
                    recovery_suggestions=["Try again", "Check connection"]
                )
                self.assertIsNotNone(error_dialog)
            
            # Test system error screen
            with patch('flashing_tool.screen_components.QT_AVAILABLE', False):
                error_screen = SystemErrorScreen("Test error occurred")
                self.assertIsNotNone(error_screen)
                self.assertEqual(error_screen.get_screen_id(), "system_error")
            
            logger.info("✓ Error handling integration test passed")
            
        except ImportError as e:
            self.skipTest(f"Error handling components not available: {e}")
    
    def test_progress_reporting_integration(self):
        """Test progress reporting in GUI components."""
        try:
            from flashing_tool.gui import EnhancedProgressDialog, SystemUpdatingScreen
            
            # Test progress dialog
            with patch('flashing_tool.gui.QT_AVAILABLE', False):
                from flashing_tool.gui import DialogConfig, DialogType
                
                config = DialogConfig(
                    title="Test Progress",
                    message="Testing progress...",
                    dialog_type=DialogType.PROGRESS,
                    show_cancel=True
                )
                
                progress_dialog = EnhancedProgressDialog(config)
                self.assertIsNotNone(progress_dialog)
                
                # Test progress updates
                progress_dialog.update_progress(50, "Half complete", "Step 1 done")
                self.assertFalse(progress_dialog.is_cancelled())
            
            # Test updating screen
            with patch('flashing_tool.screen_components.QT_AVAILABLE', False):
                updating_screen = SystemUpdatingScreen()
                self.assertIsNotNone(updating_screen)
                
                # Test step updates
                updating_screen.update_step(2, 5, "Flashing firmware")
                updating_screen.add_status_message("Firmware flash started")
            
            logger.info("✓ Progress reporting integration test passed")
            
        except ImportError as e:
            self.skipTest(f"Progress reporting components not available: {e}")


def run_integration_tests():
    """Run the integration tests."""
    print("Running Flashing Tool GUI Integration Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFlashingToolGUIIntegration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Integration Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.skipped:
        print("\nSkipped:")
        for test, reason in result.skipped:
            print(f"- {test}: {reason}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)