"""
Core modules for Smart Media Icon System.

This package contains the core functionality:
- SmartIconSetter: Main orchestration and media type detection
- FFmpegHandler: Video artwork embedding using FFmpeg  
- WindowsIcons: Windows folder icon setting via desktop.ini
"""

from .icon_setter import SmartIconSetter
from .ffmpeg_handler import FFmpegIconSetter
from .windows_icons import WinIconSetter

__all__ = [
    "SmartIconSetter",
    "FFmpegIconSetter", 
    "WinIconSetter"
]
