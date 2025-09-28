"""
Reply classes for CartClinic protocol.

This module defines the reply structures used to parse responses from CartClinic devices.
Each reply class handles decoding of binary protocol data into structured information.
"""

import struct
from typing import Dict, Any
from .common import CmdId


class BaseReply:
    """Base class for all CartClinic replies."""
    
    def __init__(self, cmd_id: CmdId):
        self.cmd_id = cmd_id
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        """Decode binary data to structured format. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement decode()")


class ReplyLoopback(BaseReply):
    """Reply for loopback command."""
    
    def __init__(self):
        super().__init__(CmdId.Loopback)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 4:
            raise ValueError("Insufficient data for loopback reply")
        
        value = struct.unpack('<I', data[:4])[0]
        return {'data': value}


class ReplyReadCartByte(BaseReply):
    """Reply for read cartridge byte command."""
    
    def __init__(self):
        super().__init__(CmdId.ReadCartByte)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 2:
            raise ValueError("Insufficient data for read cart byte reply")
        
        addr, byte_data = struct.unpack('<HB', data[:3]) if len(data) >= 3 else (0, data[0])
        return {'addr': addr, 'data': byte_data}


class ReplyWriteCartByte(BaseReply):
    """Reply for write cartridge byte command."""
    
    def __init__(self):
        super().__init__(CmdId.WriteCartByte)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 1:
            raise ValueError("Insufficient data for write cart byte reply")
        
        # Simple acknowledgment - just return the data byte
        return {'addr': 0, 'data': data[0]}


class ReplyWriteCartFlashByte(BaseReply):
    """Reply for write cartridge flash byte command."""
    
    def __init__(self):
        super().__init__(CmdId.WriteCartFlashByte)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 2:
            raise ValueError("Insufficient data for write cart flash byte reply")
        
        addr, byte_data = struct.unpack('<HB', data[:3]) if len(data) >= 3 else (0, data[0])
        return {'addr': addr, 'data': byte_data}


class ReplyDetectCart(BaseReply):
    """Reply for detect cartridge command."""
    
    def __init__(self):
        super().__init__(CmdId.DetectCart)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 1:
            raise ValueError("Insufficient data for detect cart reply")
        
        status = data[0]
        # Bit 0: inserted, Bit 1: removed
        return {
            'inserted': (status & 0x01),
            'removed': (status & 0x02) >> 1
        }


class ReplySetFrameBufferPixel(BaseReply):
    """Reply for set frame buffer pixel command."""
    
    def __init__(self):
        super().__init__(CmdId.SetFrameBufferPixel)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 1:
            raise ValueError("Insufficient data for set frame buffer pixel reply")
        
        # Simple acknowledgment
        return {'status': data[0]}


class ReplySetPSRAMAddress(BaseReply):
    """Reply for set PSRAM address command."""
    
    def __init__(self):
        super().__init__(CmdId.SetPSRAMAddress)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 1:
            raise ValueError("Insufficient data for set PSRAM address reply")
        
        return {'status': data[0]}


class ReplyWritePSRAMData(BaseReply):
    """Reply for write PSRAM data command."""
    
    def __init__(self):
        super().__init__(CmdId.WritePSRAMData)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 1:
            raise ValueError("Insufficient data for write PSRAM data reply")
        
        return {'status': data[0]}


class ReplyReadPSRAMData(BaseReply):
    """Reply for read PSRAM data command."""
    
    def __init__(self):
        super().__init__(CmdId.ReadPSRAMData)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        return {'data': data}


class ReplyStartAudioPlayback(BaseReply):
    """Reply for start audio playback command."""
    
    def __init__(self):
        super().__init__(CmdId.StartAudioPlayback)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 1:
            raise ValueError("Insufficient data for start audio playback reply")
        
        return {'status': data[0]}


class ReplyStopAudioPlayback(BaseReply):
    """Reply for stop audio playback command."""
    
    def __init__(self):
        super().__init__(CmdId.StopAudioPlayback)
    
    def decode(self, data: bytes) -> Dict[str, Any]:
        if len(data) < 1:
            raise ValueError("Insufficient data for stop audio playback reply")
        
        return {'status': data[0]}


__all__ = [
    'BaseReply',
    'ReplyLoopback',
    'ReplyReadCartByte',
    'ReplyWriteCartByte',
    'ReplyWriteCartFlashByte', 
    'ReplyDetectCart',
    'ReplySetFrameBufferPixel',
    'ReplySetPSRAMAddress',
    'ReplyWritePSRAMData',
    'ReplyReadPSRAMData',
    'ReplyStartAudioPlayback',
    'ReplyStopAudioPlayback'
]