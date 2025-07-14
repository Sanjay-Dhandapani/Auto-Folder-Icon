"""
Smart Media Icon Tray Application

A Windows system tray application that provides automatic folder monitoring
and media icon management with a user-friendly interface.
"""

__version__ = "1.0.0"
__author__ = "Smart Media Icon Team"

from .main import TrayApplication
from .tray_manager import TrayManager
from .file_watcher import FileWatcher
from .processing_engine import ProcessingEngine
from .settings_manager import TraySettingsManager
from .notification_system import NotificationSystem

__all__ = [
    "TrayApplication",
    "TrayManager", 
    "FileWatcher",
    "ProcessingEngine",
    "TraySettingsManager",
    "NotificationSystem"
]