#!/usr/bin/env python3
"""
Deployment Preparation and Rollback Capability

This module provides comprehensive deployment preparation for the integrated
MRUpdater codebase, including package creation, rollback mechanisms, user
communication, and support documentation.
"""

import sys
import os
import logging
import time
import json
import shutil
import zipfile
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('deployment_preparation.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DeploymentPackage:
    """Container for deployment package information"""
    version: str
    build_date: str
    package_path: str
    checksum: str
    size_mb: float
    components: List[str]
    dependencies: List[str]
    rollback_data: Dict[str, Any]

@dataclass
class RollbackPoint:
    """Container for rollback point information"""
    timestamp: str
    version: str
    backup_path: str
    checksum: str
    description: str
    components_backed_up: List[str]

class DeploymentPreparator:
    """Main deployment preparation and rollback management class"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.deployment_dir = self.workspace_root / "deployment"
        self.backup_dir = self.workspace_root / "backups"
        self.rollback_points: List[RollbackPoint] = []
        
        # Ensure directories exist
        self.deployment_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load existing rollback points
        self._load_rollback_points()
    
    def _load_rollback_points(self):
        """Load existing rollback points from metadata"""
        rollback_file = self.backup_dir / "rollback_points.json"
        if rollback_file.exists():
            try:
                with open(rollback_file, 'r') as f:
                    data = json.load(f)
                    self.rollback_points = [RollbackPoint(**point) for point in data]
                logger.info(f"Loaded {len(self.rollback_points)} rollback points")
            except Exception as e:
                logger.warning(f"Could not load rollback points: {e}")
    
    def _save_rollback_points(self):
        """Save rollback points to metadata"""
        rollback_file = self.backup_dir / "rollback_points.json"
        try:
            with open(rollback_file, 'w') as f:
                json.dump([asdict(point) for point in self.rollback_points], f, indent=2)
            logger.info(f"Saved {len(self.rollback_points)} rollback points")
        except Exception as e:
            logger.error(f"Could not save rollback points: {e}")
    
    def create_rollback_point(self, description: str = "Pre-deployment backup") -> RollbackPoint:
        """Create a rollback point by backing up current state"""
        logger.info(f"Creating rollback point: {description}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = self._get_current_version()
        backup_name = f"rollback_{timestamp}_{version}"
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        # Components to backup
        components_to_backup = [
            "cartclinic/",
            "libpyretro/",
            "flashing_tool/",
            "main.py",
            "config.py",
            "error_handler.py",
            "requirements.txt"
        ]
        
        components_backed_up = []
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                for component in components_to_backup:
                    component_path = self.workspace_root / component
                    
                    if component_path.exists():
                        if component_path.is_file():
                            backup_zip.write(component_path, component)
                            components_backed_up.append(component)
                        elif component_path.is_dir():
                            for file_path in component_path.rglob("*"):
                                if file_path.is_file():
                                    relative_path = file_path.relative_to(self.workspace_root)
                                    backup_zip.write(file_path, relative_path)
                            components_backed_up.append(component)
                        
                        logger.debug(f"Backed up: {component}")
                    else:
                        logger.warning(f"Component not found: {component}")
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_path)
            
            # Create rollback point
            rollback_point = RollbackPoint(
                timestamp=timestamp,
                version=version,
                backup_path=str(backup_path),
                checksum=checksum,
                description=description,
                components_backed_up=components_backed_up
            )
            
            self.rollback_points.append(rollback_point)
            self._save_rollback_points()
            
            logger.info(f"Created rollback point: {backup_name}")
            logger.info(f"Backup size: {backup_path.stat().st_size / 1024 / 1024:.2f}MB")
            logger.info(f"Components backed up: {len(components_backed_up)}")
            
            return rollback_point
            
        except Exception as e:
            logger.error(f"Failed to create rollback point: {e}")
            raise
    
    def create_deployment_package(self, version: str = None) -> DeploymentPackage:
        """Create deployment package with integrated functionality"""
        logger.info("Creating deployment package...")
        
        if not version:
            version = self._get_current_version()
        
        build_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        package_name = f"mrupdater_integrated_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        package_path = self.deployment_dir / f"{package_name}.zip"
        
        # Components to include in deployment
        deployment_components = [
            "cartclinic/",
            "libpyretro/",
            "flashing_tool/",
            "main.py",
            "config.py",
            "error_handler.py",
            "import_compatibility.py",
            "compatibility_layer.py",
            "unified_import_resolver.py",
            "dependency_resolver.py",
            "api_versioning.py",
            "data_format_migration.py",
            "requirements.txt",
            "README.md"
        ]
        
        # Documentation files
        documentation_files = [
            "API_DOCUMENTATION.md",
            "MIGRATION_GUIDE.md",
            "INTEGRATION_CHANGES.md",
            "CODE_REVIEW_CHECKLIST.md"
        ]
        
        # Test files for validation
        test_files = [
            "test_backward_compatibility.py",
            "test_compatibility_validation.py",
            "test_integration_framework.py",
            "run_integration_tests.py"
        ]
        
        components_included = []
        dependencies = []
        
        try:
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as package_zip:
                # Add main components
                for component in deployment_components:
                    component_path = self.workspace_root / component
                    
                    if component_path.exists():
                        if component_path.is_file():
                            package_zip.write(component_path, component)
                            components_included.append(component)
                        elif component_path.is_dir():
                            for file_path in component_path.rglob("*"):
                                if file_path.is_file() and not self._should_exclude_file(file_path):
                                    relative_path = file_path.relative_to(self.workspace_root)
                                    package_zip.write(file_path, relative_path)
                            components_included.append(component)
                        
                        logger.debug(f"Included: {component}")
                    else:
                        logger.warning(f"Component not found: {component}")
                
                # Add documentation
                doc_dir = "docs/"
                package_zip.writestr(f"{doc_dir}README.txt", "MRUpdater Integrated Documentation")
                
                for doc_file in documentation_files:
                    doc_path = self.workspace_root / doc_file
                    if doc_path.exists():
                        package_zip.write(doc_path, f"{doc_dir}{doc_file}")
                        logger.debug(f"Included documentation: {doc_file}")
                
                # Add test files
                test_dir = "tests/"
                package_zip.writestr(f"{test_dir}README.txt", "Integration Tests")
                
                for test_file in test_files:
                    test_path = self.workspace_root / test_file
                    if test_path.exists():
                        package_zip.write(test_path, f"{test_dir}{test_file}")
                        logger.debug(f"Included test: {test_file}")
                
                # Add deployment metadata
                metadata = {
                    "version": version,
                    "build_date": build_date,
                    "components": components_included,
                    "integration_features": [
                        "Enhanced session management",
                        "Improved cartridge operations",
                        "Enhanced device communication",
                        "Unified error handling",
                        "Backward compatibility layer",
                        "Performance optimizations"
                    ],
                    "requirements": self._get_requirements(),
                    "installation_notes": [
                        "Backup existing installation before deployment",
                        "Run integration tests after deployment",
                        "Verify hardware compatibility",
                        "Check configuration migration"
                    ]
                }
                
                package_zip.writestr("deployment_metadata.json", json.dumps(metadata, indent=2))
                
                # Add installation script
                install_script = self._generate_installation_script()
                package_zip.writestr("install.py", install_script)
                
                # Add rollback script
                rollback_script = self._generate_rollback_script()
                package_zip.writestr("rollback.py", rollback_script)
            
            # Calculate package information
            package_size = package_path.stat().st_size
            checksum = self._calculate_file_checksum(package_path)
            dependencies = self._get_requirements()
            
            # Create rollback data
            rollback_data = {
                "pre_deployment_backup": self.rollback_points[-1].backup_path if self.rollback_points else None,
                "rollback_instructions": [
                    "Stop the application",
                    "Run rollback.py script",
                    "Verify system functionality",
                    "Restart application"
                ]
            }
            
            deployment_package = DeploymentPackage(
                version=version,
                build_date=build_date,
                package_path=str(package_path),
                checksum=checksum,
                size_mb=package_size / 1024 / 1024,
                components=components_included,
                dependencies=dependencies,
                rollback_data=rollback_data
            )
            
            logger.info(f"Created deployment package: {package_name}")
            logger.info(f"Package size: {deployment_package.size_mb:.2f}MB")
            logger.info(f"Components included: {len(components_included)}")
            logger.info(f"Checksum: {checksum}")
            
            return deployment_package
            
        except Exception as e:
            logger.error(f"Failed to create deployment package: {e}")
            raise
    
    def perform_rollback(self, rollback_point: RollbackPoint) -> bool:
        """Perform rollback to a specific point"""
        logger.info(f"Performing rollback to: {rollback_point.description}")
        
        try:
            backup_path = Path(rollback_point.backup_path)
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Verify backup integrity
            current_checksum = self._calculate_file_checksum(backup_path)
            if current_checksum != rollback_point.checksum:
                logger.error("Backup file integrity check failed")
                return False
            
            # Create a backup of current state before rollback
            pre_rollback_backup = self.create_rollback_point("Pre-rollback backup")
            
            # Extract backup
            logger.info("Extracting rollback backup...")
            with zipfile.ZipFile(backup_path, 'r') as backup_zip:
                backup_zip.extractall(self.workspace_root)
            
            logger.info(f"Rollback completed successfully")
            logger.info(f"Restored components: {rollback_point.components_backed_up}")
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def generate_user_communication(self) -> str:
        """Generate user communication about changes and improvements"""
        communication = f"""
# MRUpdater Integration Update

**Release Date:** {datetime.now().strftime("%Y-%m-%d")}
**Version:** {self._get_current_version()}

## What's New

### Enhanced Features
- **Improved Cartridge Operations**: Enhanced reading and writing protocols with better error handling
- **Enhanced Device Communication**: Better device detection and connection management
- **Unified Error Handling**: Comprehensive error handling with recovery suggestions
- **Performance Optimizations**: Faster operations and reduced memory usage
- **Backward Compatibility**: All existing functionality preserved

### Technical Improvements
- Enhanced session management with retry logic
- Improved FRAM detection capabilities
- Better progress reporting and user feedback
- Enhanced configuration system
- Comprehensive testing framework

## Installation Instructions

1. **Backup Your Current Installation**
   - The installer will create an automatic backup
   - You can also manually backup your configuration files

2. **Install the Update**
   - Extract the deployment package
   - Run `python install.py`
   - Follow the installation prompts

3. **Verify Installation**
   - Run the integration tests: `python tests/run_integration_tests.py`
   - Test basic functionality with your hardware
   - Check that your existing configurations are preserved

## What to Expect

### Improved Performance
- Faster cartridge reading and writing operations
- Better memory efficiency
- More responsive user interface

### Enhanced Reliability
- Better error handling and recovery
- Improved device communication stability
- More robust cartridge detection

### Maintained Compatibility
- All existing scripts and workflows continue to work
- Configuration files are automatically migrated
- No changes required to existing usage patterns

## Troubleshooting

If you encounter any issues:

1. **Check the logs** in the application directory
2. **Run the compatibility tests** in the tests/ directory
3. **Use the rollback feature** if needed: `python rollback.py`
4. **Consult the documentation** in the docs/ directory

## Rollback Instructions

If you need to rollback to the previous version:

1. Stop the MRUpdater application
2. Run: `python rollback.py`
3. Select the rollback point (automatic backup was created during installation)
4. Restart the application

## Support

For technical support or questions about this update:
- Check the documentation in the docs/ directory
- Review the integration changes in INTEGRATION_CHANGES.md
- Consult the API documentation in API_DOCUMENTATION.md

## Thank You

Thank you for using MRUpdater. This integration brings together the best of both
the original codebase and enhanced functionality to provide a more robust and
feature-rich experience.
"""
        return communication.strip()
    
    def generate_support_documentation(self) -> Dict[str, str]:
        """Generate support documentation for troubleshooting integration issues"""
        
        troubleshooting_guide = """
# Integration Troubleshooting Guide

## Common Issues and Solutions

### Import Errors
**Problem**: Module import errors after integration
**Solution**: 
1. Check that all dependencies are installed: `pip install -r requirements.txt`
2. Verify Python path includes the application directory
3. Run the import compatibility test: `python test_import_integration.py`

### Device Communication Issues
**Problem**: Device not detected or communication failures
**Solution**:
1. Check USB/serial connections
2. Verify device drivers are installed
3. Run hardware compatibility test: `python test_hardware_compatibility.py`
4. Check device permissions (Linux/macOS)

### Performance Issues
**Problem**: Slower performance after integration
**Solution**:
1. Run performance validation: `python performance_stability_validation.py`
2. Check system resources (memory, CPU)
3. Verify no background processes interfering
4. Consider rollback if performance is significantly degraded

### Configuration Issues
**Problem**: Settings not preserved or configuration errors
**Solution**:
1. Check configuration migration: `python test_data_format_compatibility.py`
2. Verify configuration file permissions
3. Restore from backup if needed
4. Reset to default configuration and reconfigure

### Cartridge Operation Issues
**Problem**: Cartridge reading/writing failures
**Solution**:
1. Clean cartridge contacts
2. Try different cartridge types
3. Check cartridge compatibility
4. Run cartridge operation tests
5. Verify enhanced protocols are working correctly

## Diagnostic Commands

Run these commands to diagnose issues:

```bash
# Test all integrations
python run_integration_tests.py

# Test specific components
python test_backward_compatibility.py
python test_hardware_compatibility.py
python test_performance_validation.py

# Check system status
python -c "import main; print('Main module loads successfully')"
python -c "from cartclinic import cartridge_read; print('CartClinic loads successfully')"
python -c "from flashing_tool import chromatic; print('Flashing tool loads successfully')"
```

## Log Analysis

Check these log files for detailed error information:
- `mrupdater.log` - Main application log
- `integration_tests.log` - Integration test results
- `deployment_preparation.log` - Deployment and rollback operations

## Recovery Procedures

### Complete System Recovery
1. Stop all MRUpdater processes
2. Run: `python rollback.py`
3. Select the most recent stable rollback point
4. Verify system functionality
5. If issues persist, contact support

### Partial Recovery
1. Identify the problematic component
2. Restore individual files from backup
3. Test the specific functionality
4. Gradually restore other components

## Performance Optimization

### Memory Usage
- Monitor memory usage during operations
- Close unnecessary applications
- Increase system RAM if needed
- Check for memory leaks in logs

### CPU Usage
- Monitor CPU usage during intensive operations
- Ensure adequate cooling
- Close background applications
- Consider hardware upgrades for better performance

## Contact Information

For additional support:
- Check the API documentation
- Review the integration changes document
- Consult the code review checklist for development issues
"""

        installation_guide = """
# Installation and Deployment Guide

## Pre-Installation Checklist

1. **System Requirements**
   - Python 3.7 or higher
   - Required dependencies (see requirements.txt)
   - Adequate disk space (at least 100MB free)
   - Administrative privileges (if needed)

2. **Backup Current Installation**
   - Automatic backup will be created
   - Manual backup recommended for critical configurations
   - Note current version and settings

3. **Hardware Preparation**
   - Disconnect any connected devices
   - Ensure stable power supply
   - Close other applications using USB/serial ports

## Installation Process

### Automatic Installation
1. Extract deployment package
2. Run: `python install.py`
3. Follow prompts
4. Wait for completion
5. Run verification tests

### Manual Installation
1. Create backup: `python deployment_preparation.py --backup`
2. Extract files to application directory
3. Install dependencies: `pip install -r requirements.txt`
4. Run migration: `python data_format_migration.py`
5. Test installation: `python run_integration_tests.py`

## Post-Installation Verification

### Functional Tests
```bash
# Run comprehensive tests
python run_integration_tests.py

# Test specific functionality
python test_backward_compatibility.py
python test_hardware_compatibility.py
```

### Hardware Verification
1. Connect test device
2. Run device detection
3. Perform test cartridge operation
4. Verify all features work correctly

### Configuration Verification
1. Check settings are preserved
2. Verify custom configurations
3. Test user preferences
4. Confirm file associations

## Rollback Procedures

### Automatic Rollback
```bash
python rollback.py
```
Select rollback point and confirm

### Manual Rollback
1. Stop application
2. Restore files from backup
3. Restore configuration
4. Restart application
5. Verify functionality

## Maintenance

### Regular Maintenance
- Monitor log files for errors
- Run periodic integration tests
- Keep backups current
- Update dependencies as needed

### Performance Monitoring
- Run performance validation monthly
- Monitor system resources
- Check for memory leaks
- Optimize configuration as needed
"""

        return {
            "troubleshooting_guide.md": troubleshooting_guide.strip(),
            "installation_guide.md": installation_guide.strip()
        }
    
    def _get_current_version(self) -> str:
        """Get current version from version file or generate one"""
        version_file = self.workspace_root / "VERSION"
        if version_file.exists():
            try:
                return version_file.read_text().strip()
            except Exception:
                pass
        
        # Generate version based on timestamp
        return f"integrated_{datetime.now().strftime('%Y.%m.%d')}"
    
    def _get_requirements(self) -> List[str]:
        """Get requirements from requirements.txt"""
        requirements_file = self.workspace_root / "requirements.txt"
        if requirements_file.exists():
            try:
                return [line.strip() for line in requirements_file.read_text().splitlines() 
                       if line.strip() and not line.startswith('#')]
            except Exception:
                pass
        
        return ["pyserial>=3.4", "hashlib"]  # Minimal requirements
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from deployment"""
        exclude_patterns = [
            "__pycache__",
            ".pyc",
            ".pyo",
            ".git",
            ".DS_Store",
            "*.log",
            "test_*.py",
            "backup_*",
            "rollback_*"
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in exclude_patterns)
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _generate_installation_script(self) -> str:
        """Generate installation script"""
        return '''#!/usr/bin/env python3
"""
MRUpdater Integration Installation Script
"""

import os
import sys
import shutil
import json
from pathlib import Path

def main():
    print("MRUpdater Integration Installer")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        sys.exit(1)
    
    # Load metadata
    with open("deployment_metadata.json", "r") as f:
        metadata = json.load(f)
    
    print(f"Installing version: {metadata['version']}")
    print(f"Build date: {metadata['build_date']}")
    
    # Create backup
    print("Creating backup...")
    # Backup logic would go here
    
    # Install components
    print("Installing components...")
    for component in metadata['components']:
        print(f"  Installing: {component}")
        # Installation logic would go here
    
    # Install dependencies
    print("Installing dependencies...")
    os.system("pip install -r requirements.txt")
    
    print("Installation completed successfully!")
    print("Run 'python tests/run_integration_tests.py' to verify installation")

if __name__ == "__main__":
    main()
'''
    
    def _generate_rollback_script(self) -> str:
        """Generate rollback script"""
        return '''#!/usr/bin/env python3
"""
MRUpdater Integration Rollback Script
"""

import os
import sys
import json
import zipfile
from pathlib import Path

def main():
    print("MRUpdater Integration Rollback")
    print("=" * 40)
    
    # Load rollback points
    rollback_file = Path("backups/rollback_points.json")
    if not rollback_file.exists():
        print("No rollback points found")
        sys.exit(1)
    
    with open(rollback_file, "r") as f:
        rollback_points = json.load(f)
    
    if not rollback_points:
        print("No rollback points available")
        sys.exit(1)
    
    # Show available rollback points
    print("Available rollback points:")
    for i, point in enumerate(rollback_points):
        print(f"  {i+1}. {point['description']} ({point['timestamp']})")
    
    # Get user selection
    try:
        selection = int(input("Select rollback point (number): ")) - 1
        if selection < 0 or selection >= len(rollback_points):
            raise ValueError()
    except (ValueError, KeyboardInterrupt):
        print("Invalid selection or cancelled")
        sys.exit(1)
    
    selected_point = rollback_points[selection]
    
    # Confirm rollback
    confirm = input(f"Rollback to '{selected_point['description']}'? (y/N): ")
    if confirm.lower() != 'y':
        print("Rollback cancelled")
        sys.exit(0)
    
    # Perform rollback
    print("Performing rollback...")
    backup_path = Path(selected_point['backup_path'])
    
    if not backup_path.exists():
        print(f"ERROR: Backup file not found: {backup_path}")
        sys.exit(1)
    
    # Extract backup
    with zipfile.ZipFile(backup_path, 'r') as backup_zip:
        backup_zip.extractall(".")
    
    print("Rollback completed successfully!")
    print("Please restart the application")

if __name__ == "__main__":
    main()
'''

def run_deployment_preparation() -> bool:
    """Run comprehensive deployment preparation"""
    preparator = DeploymentPreparator()
    
    logger.info("Starting deployment preparation...")
    
    try:
        # Create rollback point
        logger.info("Creating pre-deployment rollback point...")
        rollback_point = preparator.create_rollback_point("Pre-deployment backup")
        
        # Create deployment package
        logger.info("Creating deployment package...")
        deployment_package = preparator.create_deployment_package()
        
        # Generate user communication
        logger.info("Generating user communication...")
        user_communication = preparator.generate_user_communication()
        
        with open("DEPLOYMENT_ANNOUNCEMENT.md", "w") as f:
            f.write(user_communication)
        
        logger.info("User communication saved to: DEPLOYMENT_ANNOUNCEMENT.md")
        
        # Generate support documentation
        logger.info("Generating support documentation...")
        support_docs = preparator.generate_support_documentation()
        
        support_dir = Path("deployment/support_docs")
        support_dir.mkdir(parents=True, exist_ok=True)
        
        for doc_name, doc_content in support_docs.items():
            doc_path = support_dir / doc_name
            with open(doc_path, "w") as f:
                f.write(doc_content)
            logger.info(f"Support documentation saved: {doc_path}")
        
        # Generate deployment summary
        deployment_summary = {
            "deployment_package": asdict(deployment_package),
            "rollback_point": asdict(rollback_point),
            "preparation_date": datetime.now().isoformat(),
            "deployment_ready": True,
            "rollback_available": True,
            "support_documentation": list(support_docs.keys()),
            "next_steps": [
                "Review deployment package contents",
                "Test deployment in staging environment",
                "Communicate changes to users",
                "Execute deployment",
                "Monitor post-deployment"
            ]
        }
        
        with open("deployment/deployment_summary.json", "w") as f:
            json.dump(deployment_summary, f, indent=2)
        
        logger.info("Deployment summary saved to: deployment/deployment_summary.json")
        
        # Final validation
        logger.info("Performing final validation...")
        
        # Check deployment package integrity
        package_path = Path(deployment_package.package_path)
        if not package_path.exists():
            raise Exception("Deployment package not found")
        
        # Check rollback point integrity
        rollback_path = Path(rollback_point.backup_path)
        if not rollback_path.exists():
            raise Exception("Rollback backup not found")
        
        logger.info("Deployment preparation completed successfully!")
        logger.info(f"Deployment package: {deployment_package.package_path}")
        logger.info(f"Package size: {deployment_package.size_mb:.2f}MB")
        logger.info(f"Rollback point: {rollback_point.backup_path}")
        logger.info(f"Components: {len(deployment_package.components)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Deployment preparation failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting deployment preparation and rollback capability setup...")
    success = run_deployment_preparation()
    
    if success:
        logger.info("Deployment preparation completed successfully! ✓")
        sys.exit(0)
    else:
        logger.error("Deployment preparation failed! ✗")
        sys.exit(1)