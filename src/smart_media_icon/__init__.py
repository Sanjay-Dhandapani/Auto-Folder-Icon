"""
Smart Media Icon System

A professional Windows desktop utility that automatically sets custom icons 
for TV series folders and embeds artwork in movie files.

Features:
- Smart detection of TV series vs movies
- Custom folder icons for TV series using Windows desktop.ini
- FFmpeg artwork embedding for movie files
- Multi-API poster fetching (TMDB, OMDb, TVmaze, AniList)
- Professional Windows integration

Author: Smart Media Icon Team
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Smart Media Icon Team"
__license__ = "MIT"

from .core.icon_setter import SmartIconSetter
from .apis.media_api import MediaAPI
from .utils.config import Config

__all__ = [
    "SmartIconSetter",
    "MediaAPI", 
    "Config"
]
