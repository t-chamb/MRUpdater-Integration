"""
Protocol module for CartClinic communication.

This module defines the low-level communication protocol for interacting with
ModRetro devices, including command definitions, reply structures, and protocol constants.
"""

from .common import (
    CmdId, ReplyPayloadLen, CartFlashInfo, FlashChipType, ChromaticBitmap,
    SCREEN_PIXEL_WIDTH, SCREEN_PIXEL_HEIGHT, identify_flash_chip
)
from .cmd import *
from .reply import *

__all__ = [
    'CmdId',
    'ReplyPayloadLen', 
    'CartFlashInfo',
    'FlashChipType',
    'ChromaticBitmap',
    'SCREEN_PIXEL_WIDTH',
    'SCREEN_PIXEL_HEIGHT',
    'identify_flash_chip',
    # Command classes
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
    'CmdStopAudioPlayback',
    # Reply classes
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