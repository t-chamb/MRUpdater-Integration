"""
IPS (International Patching System) utilities for LibPyRetro.

This module provides utilities for working with IPS patch files,
commonly used for ROM modifications and updates.
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class IPSPatch:
    """Represents an IPS patch."""
    offset: int
    data: bytes
    
class IPSPatcher:
    """
    Simplified IPS patcher implementation.
    
    This provides basic IPS patching functionality for the integrated
    codebase without requiring the full decompiled implementation.
    """
    
    IPS_HEADER = b'PATCH'
    IPS_EOF = b'EOF'
    
    def __init__(self):
        self.patches: List[IPSPatch] = []
        
    def load_patch(self, patch_data: bytes) -> bool:
        """
        Load an IPS patch from binary data.
        
        Args:
            patch_data: Raw IPS patch file data
            
        Returns:
            True if patch loaded successfully, False otherwise
        """
        try:
            if not patch_data.startswith(self.IPS_HEADER):
                logger.error("Invalid IPS patch: missing header")
                return False
                
            self.patches.clear()
            offset = len(self.IPS_HEADER)
            
            while offset < len(patch_data) - 3:
                # Check for EOF marker
                if patch_data[offset:offset+3] == self.IPS_EOF:
                    break
                    
                # Read offset (3 bytes, big-endian)
                if offset + 3 > len(patch_data):
                    break
                    
                patch_offset = int.from_bytes(patch_data[offset:offset+3], 'big')
                offset += 3
                
                # Read size (2 bytes, big-endian)
                if offset + 2 > len(patch_data):
                    break
                    
                size = int.from_bytes(patch_data[offset:offset+2], 'big')
                offset += 2
                
                if size == 0:
                    # RLE encoding
                    if offset + 2 > len(patch_data):
                        break
                    rle_size = int.from_bytes(patch_data[offset:offset+2], 'big')
                    offset += 2
                    
                    if offset + 1 > len(patch_data):
                        break
                    rle_byte = patch_data[offset]
                    offset += 1
                    
                    data = bytes([rle_byte] * rle_size)
                else:
                    # Normal patch
                    if offset + size > len(patch_data):
                        break
                    data = patch_data[offset:offset+size]
                    offset += size
                    
                self.patches.append(IPSPatch(patch_offset, data))
                
            logger.info(f"Loaded IPS patch with {len(self.patches)} patches")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load IPS patch: {e}")
            return False
            
    def apply_patch(self, rom_data: bytes) -> Optional[bytes]:
        """
        Apply loaded patches to ROM data.
        
        Args:
            rom_data: Original ROM data
            
        Returns:
            Patched ROM data or None if patching failed
        """
        try:
            if not self.patches:
                logger.warning("No patches loaded")
                return rom_data
                
            # Create mutable copy of ROM data
            patched_data = bytearray(rom_data)
            
            # Apply each patch
            for patch in self.patches:
                # Extend ROM if necessary
                required_size = patch.offset + len(patch.data)
                if required_size > len(patched_data):
                    patched_data.extend(b'\x00' * (required_size - len(patched_data)))
                    
                # Apply patch
                patched_data[patch.offset:patch.offset+len(patch.data)] = patch.data
                
            logger.info(f"Applied {len(self.patches)} patches to ROM")
            return bytes(patched_data)
            
        except Exception as e:
            logger.error(f"Failed to apply IPS patch: {e}")
            return None
            
    def create_patch(self, original_data: bytes, modified_data: bytes) -> Optional[bytes]:
        """
        Create an IPS patch from original and modified data.
        
        Args:
            original_data: Original ROM data
            modified_data: Modified ROM data
            
        Returns:
            IPS patch data or None if creation failed
        """
        try:
            patch_data = bytearray(self.IPS_HEADER)
            
            # Find differences
            max_len = max(len(original_data), len(modified_data))
            i = 0
            
            while i < max_len:
                # Find start of difference
                while i < max_len:
                    orig_byte = original_data[i] if i < len(original_data) else 0
                    mod_byte = modified_data[i] if i < len(modified_data) else 0
                    if orig_byte != mod_byte:
                        break
                    i += 1
                    
                if i >= max_len:
                    break
                    
                # Find end of difference
                start = i
                while i < max_len:
                    orig_byte = original_data[i] if i < len(original_data) else 0
                    mod_byte = modified_data[i] if i < len(modified_data) else 0
                    if orig_byte == mod_byte:
                        break
                    i += 1
                    
                # Create patch entry
                if start < max_len:
                    size = i - start
                    if size > 0 and size <= 65535 and start <= 0xFFFFFF:
                        # Add offset (3 bytes, big-endian)
                        patch_data.extend(start.to_bytes(3, 'big'))
                        # Add size (2 bytes, big-endian)
                        patch_data.extend(size.to_bytes(2, 'big'))
                        # Add data
                        patch_data.extend(modified_data[start:start+size])
                        
            # Add EOF marker
            patch_data.extend(self.IPS_EOF)
            
            logger.info(f"Created IPS patch with {len(patch_data)} bytes")
            return bytes(patch_data)
            
        except Exception as e:
            logger.error(f"Failed to create IPS patch: {e}")
            return None

# Convenience functions
def apply_ips_patch(rom_data: bytes, patch_data: bytes) -> Optional[bytes]:
    """Apply an IPS patch to ROM data."""
    patcher = IPSPatcher()
    if patcher.load_patch(patch_data):
        return patcher.apply_patch(rom_data)
    return None

def create_ips_patch(original_data: bytes, modified_data: bytes) -> Optional[bytes]:
    """Create an IPS patch from original and modified data."""
    patcher = IPSPatcher()
    return patcher.create_patch(original_data, modified_data)

# Export main classes and functions
__all__ = [
    'IPSPatcher',
    'IPSPatch',
    'apply_ips_patch',
    'create_ips_patch'
]