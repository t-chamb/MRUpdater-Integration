"""
Enhanced Firmware Management for ModRetro Devices

This module provides enhanced firmware version detection, management, and flashing
protocols integrated from the decompiled codebase with improved error handling
and validation.
"""

import hashlib
import logging
import os
import tempfile
import time
import yaml
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Callable
import threading

try:
    import boto3
    import botocore
    from botocore import UNSIGNED
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    boto3 = None
    botocore = None

try:
    from .util import (
        S3FirmwareInfo, ChromaticFirmwarePackage, CartClinicFirmwarePackage,
        MRUpdaterManifestData, validate_firmware_file, compare_versions
    )
except ImportError:
    # Fallback definitions if util module is not available
    @dataclass
    class S3FirmwareInfo:
        bucket: str
        key: str
        version: str
        size: Optional[int] = None
        etag: Optional[str] = None
        last_modified: Optional[str] = None

    @dataclass
    class ChromaticFirmwarePackage:
        fpga_file: str
        mcu_file: str
        version: str
        changelog: Optional[str] = None
        size: Optional[int] = None

    @dataclass
    class CartClinicFirmwarePackage:
        firmware_file: str
        version: str
        changelog: Optional[str] = None
        size: Optional[int] = None

    @dataclass
    class MRUpdaterManifestData:
        version: str
        chromatic_firmware: Optional[ChromaticFirmwarePackage] = None
        cart_clinic_firmware: Optional[CartClinicFirmwarePackage] = None
        changelog: Optional[str] = None
        release_notes: Optional[str] = None

    def validate_firmware_file(filepath: str) -> bool:
        return os.path.isfile(filepath) and os.path.getsize(filepath) > 0

    def compare_versions(v1: str, v2: str) -> int:
        # Simple version comparison fallback
        if v1 == v2:
            return 0
        return 1 if v1 > v2 else -1

flashing_tool_logger = logging.getLogger('mrupdater')


class FirmwareType(Enum):
    """Types of firmware supported"""
    CHROMATIC_FPGA = "chromatic_fpga"
    CHROMATIC_MCU = "chromatic_mcu"
    CART_CLINIC = "cart_clinic"
    UNKNOWN = "unknown"


class FirmwareState(Enum):
    """Firmware states"""
    UNKNOWN = "unknown"
    CURRENT = "current"
    OUTDATED = "outdated"
    NEWER = "newer"
    CORRUPTED = "corrupted"


@dataclass
class FirmwareInfo:
    """Information about firmware"""
    firmware_type: FirmwareType
    version: str
    file_path: Optional[str] = None
    size: Optional[int] = None
    checksum: Optional[str] = None
    state: FirmwareState = FirmwareState.UNKNOWN
    changelog: Optional[str] = None
    release_date: Optional[str] = None


@dataclass
class FirmwareValidationResult:
    """Result of firmware validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    checksum: Optional[str] = None
    size: Optional[int] = None


class FirmwareError(Exception):
    """Base exception for firmware operations"""
    
    def __init__(self, message: str, firmware_type: Optional[FirmwareType] = None,
                 recovery_suggestions: Optional[List[str]] = None):
        super().__init__(message)
        self.firmware_type = firmware_type
        self.recovery_suggestions = recovery_suggestions or []


class FirmwareDownloadError(FirmwareError):
    """Raised when firmware download fails"""
    pass


class FirmwareValidationError(FirmwareError):
    """Raised when firmware validation fails"""
    pass


class FirmwareVersionError(FirmwareError):
    """Raised when firmware version operations fail"""
    pass


class InvalidAwsCredentialsError(Exception):
    """Raised when AWS credentials are invalid or missing (from decompiled version)"""
    pass


class S3WrapperError(Exception):
    """Raised when the S3Wrapper encounters an error (from decompiled version)"""
    pass


class EnhancedS3Wrapper:
    """Enhanced S3 wrapper with improved error handling and retry logic"""
    
    REGION_NAME = 'us-east-1'
    BUCKET_NAME = 'updates.modretro.com'
    MANIFEST_KEY = 'apps/manifest.yaml'
    
    def __init__(self, bucket: str = None, credentials: Optional[Dict] = None,
                 retry_count: int = 3, retry_delay: float = 1.0):
        if not AWS_AVAILABLE:
            raise FirmwareError("AWS SDK not available for firmware downloads")
        
        self.bucket = bucket or self.BUCKET_NAME
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        
        # Enhanced AWS client configuration from decompiled patterns
        try:
            if credentials:
                # Validate credentials format
                if not isinstance(credentials, dict):
                    raise InvalidAwsCredentialsError("Credentials must be a dictionary")
                
                # Create client with provided credentials
                self.client = boto3.client('s3', region_name=self.REGION_NAME, **credentials)
            else:
                # Use unsigned requests for public buckets (enhanced from decompiled version)
                default_config = {
                    'config': boto3.session.Config(signature_version=UNSIGNED)
                }
                self.client = boto3.client('s3', region_name=self.REGION_NAME, **default_config)
            
            # Test client connectivity
            try:
                self.client.head_bucket(Bucket=self.bucket)
                flashing_tool_logger.debug(f"Successfully connected to S3 bucket: {self.bucket}")
            except Exception as e:
                flashing_tool_logger.warning(f"Could not verify S3 bucket access: {e}")
                
        except Exception as e:
            raise S3WrapperError(f"Failed to initialize S3 client: {e}")
    
    def download_file(self, key: str, destination: Optional[str] = None,
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """
        Download file from S3 with enhanced error handling and progress reporting
        
        Args:
            key: S3 object key
            destination: Local destination path (optional)
            progress_callback: Progress callback function (bytes_transferred, total_bytes)
            
        Returns:
            Path to downloaded file
        """
        if not destination:
            destination = os.path.join(tempfile.gettempdir(), os.path.basename(key))
        
        # Ensure destination directory exists
        dest_dir = os.path.dirname(destination)
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        
        for attempt in range(self.retry_count):
            try:
                # Get file size for progress reporting
                if progress_callback:
                    try:
                        metadata = self.client.head_object(Bucket=self.bucket, Key=key)
                        total_size = metadata.get('ContentLength', 0)
                        
                        # Create progress callback wrapper
                        def progress_wrapper(bytes_transferred):
                            progress_callback(bytes_transferred, total_size)
                        
                        self.client.download_file(
                            self.bucket, key, destination,
                            Callback=progress_wrapper
                        )
                    except Exception:
                        # Fall back to download without progress
                        self.client.download_file(self.bucket, key, destination)
                else:
                    self.client.download_file(self.bucket, key, destination)
                
                flashing_tool_logger.info(f"Downloaded {key} to {destination}")
                return destination
                
            except Exception as e:
                if attempt < self.retry_count - 1:
                    flashing_tool_logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise FirmwareDownloadError(
                        f"Failed to download {key} after {self.retry_count} attempts: {e}",
                        recovery_suggestions=[
                            "Check internet connection",
                            "Verify S3 bucket access",
                            "Try again later"
                        ]
                    )
    
    def download_files(self, keys: List[str], destination_dir: Optional[str] = None,
                      progress_callback: Optional[Callable[[str, int, int], None]] = None) -> Dict[str, str]:
        """
        Download multiple files from S3
        
        Args:
            keys: List of S3 object keys
            destination_dir: Destination directory (optional)
            progress_callback: Progress callback (key, bytes_transferred, total_bytes)
            
        Returns:
            Dictionary mapping keys to local file paths
        """
        destinations = {}
        
        for key in keys:
            if destination_dir:
                destination = os.path.join(destination_dir, os.path.basename(key))
            else:
                destination = None
            
            # Create per-file progress callback
            file_progress_callback = None
            if progress_callback:
                file_progress_callback = lambda transferred, total, k=key: progress_callback(k, transferred, total)
            
            destinations[key] = self.download_file(key, destination, file_progress_callback)
        
        return destinations
    
    def read_manifest(self) -> str:
        """Enhanced manifest reading with better error handling from decompiled patterns"""
        for attempt in range(self.retry_count):
            try:
                # Enhanced manifest reading from decompiled version
                response = self.client.get_object(Bucket=self.BUCKET_NAME, Key=self.MANIFEST_KEY)
                content = response['Body'].read().decode('utf-8')
                flashing_tool_logger.debug("Successfully read manifest from S3")
                return content
                
            except botocore.exceptions.ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                if attempt < self.retry_count - 1:
                    flashing_tool_logger.warning(f"Manifest read attempt {attempt + 1} failed ({error_code}): {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise S3WrapperError(f"Failed to read manifest after {self.retry_count} attempts: {e}")
            except Exception as e:
                if attempt < self.retry_count - 1:
                    flashing_tool_logger.warning(f"Manifest read attempt {attempt + 1} failed: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise FirmwareError(
                        f"Failed to read manifest: {e}",
                        recovery_suggestions=[
                            "Check internet connection",
                            "Verify manifest exists in S3 bucket",
                            "Try again later"
                        ]
                    )
    
    def read_file(self, key: str) -> str:
        """Enhanced file reading with retry logic from decompiled patterns"""
        for attempt in range(self.retry_count):
            try:
                response = self.client.get_object(Bucket=self.bucket, Key=key)
                return response['Body'].read().decode('utf-8')
                
            except botocore.exceptions.ClientError as e:
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise S3WrapperError(f"Failed to read file {key}: {e}")
            except Exception as e:
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise FirmwareError(f"Failed to read file {key}: {e}")
    
    def get_file_metadata(self, key: str) -> Dict[str, Any]:
        """Enhanced metadata retrieval with retry logic"""
        for attempt in range(self.retry_count):
            try:
                return self.client.head_object(Bucket=self.bucket, Key=key)
                
            except botocore.exceptions.ClientError as e:
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise S3WrapperError(f"Failed to get metadata for {key}: {e}")
            except Exception as e:
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise FirmwareError(f"Failed to get metadata for {key}: {e}")


class FirmwareManager:
    """Enhanced firmware manager with version detection and validation"""
    
    def __init__(self, s3_wrapper: Optional[EnhancedS3Wrapper] = None,
                 cache_dir: Optional[str] = None):
        self.s3_wrapper = s3_wrapper or (EnhancedS3Wrapper() if AWS_AVAILABLE else None)
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), 'mrupdater_firmware')
        self._manifest_cache = None
        self._manifest_cache_time = 0
        self._cache_timeout = 300  # 5 minutes
        self._lock = threading.RLock()
        
        # Enhanced initialization from decompiled patterns
        self._download_progress_callbacks = []
        self._validation_callbacks = []
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            
        flashing_tool_logger.debug(f"Firmware manager initialized with cache dir: {self.cache_dir}")
    
    def add_download_progress_callback(self, callback: Callable[[str, int, int], None]):
        """Add callback for download progress updates"""
        self._download_progress_callbacks.append(callback)
    
    def remove_download_progress_callback(self, callback: Callable[[str, int, int], None]):
        """Remove download progress callback"""
        if callback in self._download_progress_callbacks:
            self._download_progress_callbacks.remove(callback)
    
    def _notify_download_progress(self, filename: str, bytes_transferred: int, total_bytes: int):
        """Notify all download progress callbacks"""
        for callback in self._download_progress_callbacks:
            try:
                callback(filename, bytes_transferred, total_bytes)
            except Exception as e:
                flashing_tool_logger.error(f"Download progress callback error: {e}")
    
    def add_validation_callback(self, callback: Callable[[str, FirmwareValidationResult], None]):
        """Add callback for validation results"""
        self._validation_callbacks.append(callback)
    
    def remove_validation_callback(self, callback: Callable[[str, FirmwareValidationResult], None]):
        """Remove validation callback"""
        if callback in self._validation_callbacks:
            self._validation_callbacks.remove(callback)
    
    def _notify_validation_result(self, filename: str, result: FirmwareValidationResult):
        """Notify all validation callbacks"""
        for callback in self._validation_callbacks:
            try:
                callback(filename, result)
            except Exception as e:
                flashing_tool_logger.error(f"Validation callback error: {e}")
    
    def _get_cached_manifest(self) -> Optional[MRUpdaterManifestData]:
        """Get cached manifest if still valid"""
        with self._lock:
            if (self._manifest_cache and 
                time.time() - self._manifest_cache_time < self._cache_timeout):
                return self._manifest_cache
            return None
    
    def _cache_manifest(self, manifest: MRUpdaterManifestData):
        """Cache manifest data"""
        with self._lock:
            self._manifest_cache = manifest
            self._manifest_cache_time = time.time()
    
    def get_latest_manifest(self, force_refresh: bool = False) -> MRUpdaterManifestData:
        """
        Get latest firmware manifest with caching
        
        Args:
            force_refresh: Force refresh from S3 even if cached
            
        Returns:
            Latest manifest data
        """
        if not force_refresh:
            cached = self._get_cached_manifest()
            if cached:
                return cached
        
        if not self.s3_wrapper:
            raise FirmwareError("S3 wrapper not available for manifest retrieval")
        
        try:
            manifest_yaml = self.s3_wrapper.read_manifest()
            manifest_data = yaml.safe_load(manifest_yaml)
            
            # Parse manifest into structured data
            manifest = MRUpdaterManifestData(
                version=manifest_data.get('version', '0.0.0'),
                changelog=manifest_data.get('changelog'),
                release_notes=manifest_data.get('release_notes')
            )
            
            # Parse Chromatic firmware info
            if 'chromatic_firmware' in manifest_data:
                chromatic_data = manifest_data['chromatic_firmware']
                manifest.chromatic_firmware = ChromaticFirmwarePackage(
                    fpga_file=chromatic_data.get('fpga_file', ''),
                    mcu_file=chromatic_data.get('mcu_file', ''),
                    version=chromatic_data.get('version', '0.0.0'),
                    changelog=chromatic_data.get('changelog'),
                    size=chromatic_data.get('size')
                )
            
            # Parse Cart Clinic firmware info
            if 'cart_clinic_firmware' in manifest_data:
                cc_data = manifest_data['cart_clinic_firmware']
                manifest.cart_clinic_firmware = CartClinicFirmwarePackage(
                    firmware_file=cc_data.get('firmware_file', ''),
                    version=cc_data.get('version', '0.0.0'),
                    changelog=cc_data.get('changelog'),
                    size=cc_data.get('size')
                )
            
            self._cache_manifest(manifest)
            flashing_tool_logger.info(f"Retrieved manifest version {manifest.version}")
            return manifest
            
        except Exception as e:
            raise FirmwareError(f"Failed to parse manifest: {e}")
    
    def validate_firmware_file(self, file_path: str, 
                              expected_checksum: Optional[str] = None) -> FirmwareValidationResult:
        """
        Validate firmware file with enhanced checks
        
        Args:
            file_path: Path to firmware file
            expected_checksum: Expected SHA256 checksum (optional)
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        checksum = None
        size = None
        
        try:
            # Check file exists and is readable
            if not os.path.isfile(file_path):
                errors.append(f"Firmware file not found: {file_path}")
                return FirmwareValidationResult(False, errors, warnings)
            
            if not os.access(file_path, os.R_OK):
                errors.append(f"Firmware file not readable: {file_path}")
                return FirmwareValidationResult(False, errors, warnings)
            
            # Check file size
            size = os.path.getsize(file_path)
            if size == 0:
                errors.append("Firmware file is empty")
                return FirmwareValidationResult(False, errors, warnings)
            
            if size < 1024:  # Less than 1KB seems suspicious
                warnings.append(f"Firmware file is very small ({size} bytes)")
            
            # Calculate checksum
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.sha256()
                    while chunk := f.read(8192):
                        file_hash.update(chunk)
                    checksum = file_hash.hexdigest()
                
                # Verify checksum if provided
                if expected_checksum and checksum != expected_checksum:
                    errors.append(f"Checksum mismatch: expected {expected_checksum}, got {checksum}")
                
            except Exception as e:
                warnings.append(f"Could not calculate checksum: {e}")
            
            # Additional file format checks based on extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.bin', '.hex', '.elf']:
                # Basic binary file checks
                try:
                    with open(file_path, 'rb') as f:
                        header = f.read(16)
                        if len(header) < 16:
                            warnings.append("Firmware file header is incomplete")
                        elif header == b'\x00' * 16:
                            warnings.append("Firmware file appears to be empty (all zeros)")
                except Exception as e:
                    warnings.append(f"Could not read firmware header: {e}")
            
            is_valid = len(errors) == 0
            return FirmwareValidationResult(is_valid, errors, warnings, checksum, size)
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return FirmwareValidationResult(False, errors, warnings)
    
    def detect_firmware_version(self, device_info: Dict[str, Any]) -> Optional[str]:
        """
        Detect current firmware version from device
        
        Args:
            device_info: Device information dictionary
            
        Returns:
            Detected firmware version or None
        """
        try:
            # Try to extract version from device info
            if 'firmware_version' in device_info:
                return device_info['firmware_version']
            
            if 'version' in device_info:
                return device_info['version']
            
            # Try to parse from device strings
            if 'product' in device_info:
                product = device_info['product']
                # Look for version patterns in product string
                import re
                version_match = re.search(r'v?(\d+\.\d+(?:\.\d+)?)', product)
                if version_match:
                    return version_match.group(1)
            
            flashing_tool_logger.debug("Could not detect firmware version from device info")
            return None
            
        except Exception as e:
            flashing_tool_logger.error(f"Error detecting firmware version: {e}")
            return None
    
    def compare_firmware_versions(self, current_version: str, 
                                 available_version: str) -> FirmwareState:
        """
        Compare firmware versions to determine state
        
        Args:
            current_version: Currently installed version
            available_version: Available version
            
        Returns:
            Firmware state
        """
        try:
            comparison = compare_versions(current_version, available_version)
            
            if comparison == 0:
                return FirmwareState.CURRENT
            elif comparison < 0:
                return FirmwareState.OUTDATED
            else:
                return FirmwareState.NEWER
                
        except Exception as e:
            flashing_tool_logger.error(f"Error comparing versions: {e}")
            return FirmwareState.UNKNOWN
    
    def download_firmware(self, firmware_package: Union[ChromaticFirmwarePackage, CartClinicFirmwarePackage],
                         progress_callback: Optional[Callable[[str, int, int], None]] = None) -> Dict[str, str]:
        """
        Download firmware files
        
        Args:
            firmware_package: Firmware package information
            progress_callback: Progress callback (filename, bytes_transferred, total_bytes)
            
        Returns:
            Dictionary mapping firmware types to local file paths
        """
        if not self.s3_wrapper:
            raise FirmwareDownloadError("S3 wrapper not available for firmware download")
        
        files_to_download = []
        
        if isinstance(firmware_package, ChromaticFirmwarePackage):
            if firmware_package.fpga_file:
                files_to_download.append(firmware_package.fpga_file)
            if firmware_package.mcu_file:
                files_to_download.append(firmware_package.mcu_file)
        elif isinstance(firmware_package, CartClinicFirmwarePackage):
            if firmware_package.firmware_file:
                files_to_download.append(firmware_package.firmware_file)
        
        if not files_to_download:
            raise FirmwareDownloadError("No firmware files specified in package")
        
        try:
            downloaded_files = self.s3_wrapper.download_files(
                files_to_download, 
                self.cache_dir,
                progress_callback
            )
            
            # Validate downloaded files
            for key, file_path in downloaded_files.items():
                validation = self.validate_firmware_file(file_path)
                if not validation.is_valid:
                    raise FirmwareValidationError(
                        f"Downloaded firmware file {key} failed validation: {', '.join(validation.errors)}"
                    )
                
                if validation.warnings:
                    for warning in validation.warnings:
                        flashing_tool_logger.warning(f"Firmware {key}: {warning}")
            
            return downloaded_files
            
        except Exception as e:
            if isinstance(e, (FirmwareDownloadError, FirmwareValidationError)):
                raise
            else:
                raise FirmwareDownloadError(f"Firmware download failed: {e}")
    
    def get_firmware_info(self, firmware_type: FirmwareType, 
                         current_version: Optional[str] = None) -> Optional[FirmwareInfo]:
        """
        Get firmware information for specified type
        
        Args:
            firmware_type: Type of firmware
            current_version: Current installed version (optional)
            
        Returns:
            Firmware information or None if not available
        """
        try:
            manifest = self.get_latest_manifest()
            
            if firmware_type == FirmwareType.CHROMATIC_FPGA or firmware_type == FirmwareType.CHROMATIC_MCU:
                if not manifest.chromatic_firmware:
                    return None
                
                firmware_info = FirmwareInfo(
                    firmware_type=firmware_type,
                    version=manifest.chromatic_firmware.version,
                    changelog=manifest.chromatic_firmware.changelog,
                    size=manifest.chromatic_firmware.size
                )
                
            elif firmware_type == FirmwareType.CART_CLINIC:
                if not manifest.cart_clinic_firmware:
                    return None
                
                firmware_info = FirmwareInfo(
                    firmware_type=firmware_type,
                    version=manifest.cart_clinic_firmware.version,
                    changelog=manifest.cart_clinic_firmware.changelog,
                    size=manifest.cart_clinic_firmware.size
                )
            else:
                return None
            
            # Determine state if current version is provided
            if current_version:
                firmware_info.state = self.compare_firmware_versions(
                    current_version, firmware_info.version
                )
            
            return firmware_info
            
        except Exception as e:
            flashing_tool_logger.error(f"Error getting firmware info: {e}")
            return None
    
    def cleanup_cache(self, max_age_days: int = 7):
        """
        Clean up old cached firmware files
        
        Args:
            max_age_days: Maximum age of files to keep in days
        """
        try:
            if not os.path.exists(self.cache_dir):
                return
            
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            removed_count = 0
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            removed_count += 1
                            flashing_tool_logger.debug(f"Removed old cached file: {filename}")
                        except Exception as e:
                            flashing_tool_logger.warning(f"Could not remove cached file {filename}: {e}")
            
            if removed_count > 0:
                flashing_tool_logger.info(f"Cleaned up {removed_count} old cached firmware files")
            
        except Exception as e:
            flashing_tool_logger.error(f"Error cleaning up cache: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached firmware files
        
        Returns:
            Dictionary with cache information
        """
        cache_info = {
            'cache_dir': self.cache_dir,
            'total_files': 0,
            'total_size': 0,
            'files': []
        }
        
        try:
            if not os.path.exists(self.cache_dir):
                return cache_info
            
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    file_info = {
                        'name': filename,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'path': file_path
                    }
                    cache_info['files'].append(file_info)
                    cache_info['total_files'] += 1
                    cache_info['total_size'] += stat.st_size
            
        except Exception as e:
            flashing_tool_logger.error(f"Error getting cache info: {e}")
        
        return cache_info
    
    def split_version_string(self, aggregate_version: str) -> str:
        """
        Split aggregate version string into FPGA/MCU components (from decompiled patterns)
        
        Args:
            aggregate_version: Combined version string (e.g., 'v18.0_0.12.3')
            
        Returns:
            Formatted version string with components separated
        """
        try:
            import re
            fw_search = re.match(r'v(\d+\.\d+)_(\d+\.\d+\.\d+)', aggregate_version)
            if fw_search:
                return f"FPGA: {fw_search.group(1)}, MCU: {fw_search.group(2)}"
            return aggregate_version
            
        except Exception as e:
            flashing_tool_logger.debug(f"Error splitting version string: {e}")
            return aggregate_version
    
    def is_firmware_cached(self, firmware_package: Union[ChromaticFirmwarePackage, CartClinicFirmwarePackage]) -> bool:
        """
        Check if firmware package is already cached locally
        
        Args:
            firmware_package: Firmware package to check
            
        Returns:
            True if all firmware files are cached
        """
        try:
            files_to_check = []
            
            if isinstance(firmware_package, ChromaticFirmwarePackage):
                if firmware_package.fpga_file:
                    files_to_check.append(os.path.basename(firmware_package.fpga_file))
                if firmware_package.mcu_file:
                    files_to_check.append(os.path.basename(firmware_package.mcu_file))
            elif isinstance(firmware_package, CartClinicFirmwarePackage):
                if firmware_package.firmware_file:
                    files_to_check.append(os.path.basename(firmware_package.firmware_file))
            
            for filename in files_to_check:
                cache_path = os.path.join(self.cache_dir, filename)
                if not os.path.isfile(cache_path):
                    return False
                
                # Validate cached file
                validation = self.validate_firmware_file(cache_path)
                if not validation.is_valid:
                    return False
            
            return len(files_to_check) > 0
            
        except Exception as e:
            flashing_tool_logger.debug(f"Error checking firmware cache: {e}")
            return False


# Backward compatibility functions
def create_firmware_manager(cache_dir: Optional[str] = None) -> FirmwareManager:
    """Create firmware manager instance"""
    return FirmwareManager(cache_dir=cache_dir)


def validate_firmware_file_simple(filepath: str) -> bool:
    """Simple firmware file validation (backward compatibility)"""
    return validate_firmware_file(filepath)


__all__ = [
    'FirmwareType',
    'FirmwareState',
    'FirmwareInfo',
    'FirmwareValidationResult',
    'FirmwareError',
    'FirmwareDownloadError',
    'FirmwareValidationError',
    'FirmwareVersionError',
    'InvalidAwsCredentialsError',
    'S3WrapperError',
    'EnhancedS3Wrapper',
    'FirmwareManager',
    'create_firmware_manager',
    'validate_firmware_file_simple',
]