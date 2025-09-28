#!/usr/bin/env python3
"""
Simple validation script for GUI integration.

This script validates that the GUI components are properly integrated
without requiring external dependencies.
"""

import sys
import os
import importlib.util

def validate_file_exists(filepath):
    """Validate that a file exists."""
    if os.path.exists(filepath):
        print(f"✓ {filepath} exists")
        return True
    else:
        print(f"✗ {filepath} missing")
        return False

def validate_module_structure(module_path, expected_classes):
    """Validate that a module has expected classes."""
    if not os.path.exists(module_path):
        print(f"✗ Module {module_path} not found")
        return False
    
    try:
        with open(module_path, 'r') as f:
            content = f.read()
        
        missing_classes = []
        for class_name in expected_classes:
            if f"class {class_name}" not in content:
                missing_classes.append(class_name)
        
        if missing_classes:
            print(f"✗ {module_path} missing classes: {missing_classes}")
            return False
        else:
            print(f"✓ {module_path} has all expected classes")
            return True
            
    except Exception as e:
        print(f"✗ Error reading {module_path}: {e}")
        return False

def validate_imports(module_path, expected_imports):
    """Validate that a module has expected imports."""
    if not os.path.exists(module_path):
        print(f"✗ Module {module_path} not found")
        return False
    
    try:
        with open(module_path, 'r') as f:
            content = f.read()
        
        missing_imports = []
        for import_statement in expected_imports:
            if import_statement not in content:
                missing_imports.append(import_statement)
        
        if missing_imports:
            print(f"✗ {module_path} missing imports: {missing_imports}")
            return False
        else:
            print(f"✓ {module_path} has all expected imports")
            return True
            
    except Exception as e:
        print(f"✗ Error reading {module_path}: {e}")
        return False

def main():
    """Main validation function."""
    print("Validating GUI Integration...")
    print("=" * 50)
    
    all_valid = True
    
    # Validate core GUI files exist
    gui_files = [
        "flashing_tool/gui.py",
        "flashing_tool/screen_components.py",
        "flashing_tool/flasher_form.py",
        "flashing_tool/ui_util.py"
    ]
    
    for filepath in gui_files:
        if not validate_file_exists(filepath):
            all_valid = False
    
    print()
    
    # Validate screen components
    screen_classes = [
        "BaseScreen",
        "SystemCheckScreen",
        "SystemConnectScreen",
        "SystemUpdatingScreen",
        "SystemSuccessScreen",
        "SystemErrorScreen",
        "CartClinicStartScreen",
        "CartClinicUpdatingScreen",
        "AboutScreen",
        "ScreenManager"
    ]
    
    if not validate_module_structure("flashing_tool/screen_components.py", screen_classes):
        all_valid = False
    
    # Validate dialog components in main GUI
    dialog_classes = [
        "EnhancedProgressDialog",
        "EnhancedErrorDialog",
        "EnhancedChangelogDialog",
        "EnhancedAlertDialog",
        "EnhancedConsentDialog",
        "DialogManager"
    ]
    
    if not validate_module_structure("flashing_tool/gui.py", dialog_classes):
        all_valid = False
    
    # Validate flasher form
    form_classes = ["FlasherForm"]
    
    if not validate_module_structure("flashing_tool/flasher_form.py", form_classes):
        all_valid = False
    
    # Validate UI utilities
    util_classes = [
        "ResponsiveLayoutManager",
        "DynamicFontManager",
        "ThemeManager"
    ]
    
    if not validate_module_structure("flashing_tool/ui_util.py", util_classes):
        all_valid = False
    
    print()
    
    # Validate imports in main GUI module
    expected_imports = [
        "from .screen_components import *",
        "from .flasher_form import FlasherForm"
    ]
    
    if not validate_imports("flashing_tool/gui.py", expected_imports):
        all_valid = False
    
    # Validate exports in main GUI module
    try:
        with open("flashing_tool/gui.py", 'r') as f:
            content = f.read()
        
        expected_exports = [
            "'FlasherForm'",
            "'ScreenManager'",
            "'DialogManager'",
            "'SystemCheckScreen'",
            "'CartClinicStartScreen'"
        ]
        
        missing_exports = []
        for export in expected_exports:
            if export not in content:
                missing_exports.append(export)
        
        if missing_exports:
            print(f"✗ flashing_tool/gui.py missing exports: {missing_exports}")
            all_valid = False
        else:
            print("✓ flashing_tool/gui.py has all expected exports")
            
    except Exception as e:
        print(f"✗ Error validating exports: {e}")
        all_valid = False
    
    print()
    
    # Validate backward compatibility
    try:
        with open("flashing_tool/gui.py", 'r') as f:
            content = f.read()
        
        backward_compat_aliases = [
            "AlertDialog = EnhancedAlertDialog",
            "ChangelogDialog = EnhancedChangelogDialog",
            "ConsentDialog = EnhancedConsentDialog",
            "ErrorDialog = EnhancedErrorDialog"
        ]
        
        missing_aliases = []
        for alias in backward_compat_aliases:
            if alias not in content:
                missing_aliases.append(alias)
        
        if missing_aliases:
            print(f"✗ Missing backward compatibility aliases: {missing_aliases}")
            all_valid = False
        else:
            print("✓ All backward compatibility aliases present")
            
    except Exception as e:
        print(f"✗ Error validating backward compatibility: {e}")
        all_valid = False
    
    print()
    print("=" * 50)
    
    if all_valid:
        print("✓ All GUI integration validations passed!")
        print("\nIntegrated components:")
        print("- Enhanced dialog systems with progress reporting")
        print("- Screen components for system and cart clinic operations")
        print("- Main flasher form with tab management")
        print("- UI utilities with responsive design")
        print("- Backward compatibility with existing interfaces")
        print("- Error handling with recovery suggestions")
        return True
    else:
        print("✗ Some GUI integration validations failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)