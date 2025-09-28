"""
Command classes for CartClinic protocol.

This module defines the command structures used to communicate with CartClinic devices.
Each command class handles encoding of parameters into the binary protocol format.
"""

import struct
from .common import CmdId


class BaseCommand:
    """Base class for all CartClinic commands."""
    
    def __init__(self, cmd_id: CmdId):
        self.cmd_id = cmd_id
    
    def encode(self) -> bytes:
        """Encode command to binary format. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement encode()")


class CmdLoopback(BaseCommand):
    """Loopback command for testing communication."""
    
    def __init__(self, data: int = 0):
        super().__init__(CmdId.Loopback)
        self.data = data
    
    def encode(self) -> bytes:
        return struct.pack('<BI', self.cmd_id, self.data)


class CmdReadCartByte(BaseCommand):
    """Command to read a byte from cartridge memory."""
    
    def __init__(self, addr: int):
        super().__init__(CmdId.ReadCartByte)
        self.addr = addr
    
    def encode(self) -> bytes:
        return struct.pack('<BH', self.cmd_id, self.addr)


class CmdWriteCartByte(BaseCommand):
    """Command to write a byte to cartridge memory."""
    
    def __init__(self, addr: int, data: int):
        super().__init__(CmdId.WriteCartByte)
        self.addr = addr
        self.data = data
    
    def encode(self) -> bytes:
        return struct.pack('<BHB', self.cmd_id, self.addr, self.data)


class CmdWriteCartFlashByte(BaseCommand):
    """Command to write a byte to cartridge flash memory."""
    
    def __init__(self, addr: int, data: int):
        super().__init__(CmdId.WriteCartFlashByte)
        self.addr = addr
        self.data = data
    
    def encode(self) -> bytes:
        return struct.pack('<BHB', self.cmd_id, self.addr, self.data)


class CmdDetectCart(BaseCommand):
    """Command to detect cartridge presence."""
    
    def __init__(self):
        super().__init__(CmdId.DetectCart)
    
    def encode(self) -> bytes:
        return struct.pack('<B', self.cmd_id)


class CmdSetFrameBufferPixel(BaseCommand):
    """Command to set a pixel in the frame buffer."""
    
    def __init__(self, addr: int, r: int, g: int, b: int):
        super().__init__(CmdId.SetFrameBufferPixel)
        self.addr = addr
        self.r = r
        self.g = g
        self.b = b
    
    def encode(self) -> bytes:
        return struct.pack('<BHBBB', self.cmd_id, self.addr, self.r, self.g, self.b)


class CmdSetPSRAMAddress(BaseCommand):
    """Command to set PSRAM address."""
    
    def __init__(self, addr: int):
        super().__init__(CmdId.SetPSRAMAddress)
        self.addr = addr
    
    def encode(self) -> bytes:
        return struct.pack('<BI', self.cmd_id, self.addr)


class CmdWritePSRAMData(BaseCommand):
    """Command to write data to PSRAM."""
    
    def __init__(self, data: bytes):
        super().__init__(CmdId.WritePSRAMData)
        self.data = data
    
    def encode(self) -> bytes:
        return struct.pack('<B', self.cmd_id) + self.data


class CmdReadPSRAMData(BaseCommand):
    """Command to read data from PSRAM."""
    
    def __init__(self, length: int):
        super().__init__(CmdId.ReadPSRAMData)
        self.length = length
    
    def encode(self) -> bytes:
        return struct.pack('<BH', self.cmd_id, self.length)


class CmdStartAudioPlayback(BaseCommand):
    """Command to start audio playback."""
    
    def __init__(self):
        super().__init__(CmdId.StartAudioPlayback)
    
    def encode(self) -> bytes:
        return struct.pack('<B', self.cmd_id)


class CmdStopAudioPlayback(BaseCommand):
    """Command to stop audio playback."""
    
    def __init__(self):
        super().__init__(CmdId.StopAudioPlayback)
    
    def encode(self) -> bytes:
        return struct.pack('<B', self.cmd_id)


__all__ = [
    'BaseCommand',
    'CmdLoopback',
    'CmdReadCartByte',
    'CmdWriteCartByte', 
    'CmdWriteCartFlashByte',
    'CmdDetectCart',
    'CmdSetFrameBufferPixel',
    'CmdSetPSRAMAddress',
    'CmdWritePSRAMData',
    'CmdReadPSRAMData',
    'CmdStartAudioPlayback',
    'CmdStopAudioPlayback'
]