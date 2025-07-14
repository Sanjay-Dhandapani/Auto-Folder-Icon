#!/usr/bin/env python3
"""
Smart Media Icon Notification System

Provides Windows toast notifications and status updates for the tray application.
Integrates with Windows notification system for professional user feedback.
"""

import logging
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from PyQt5.QtWidgets import QSystemTrayIcon, QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon


class NotificationSystem(QObject):
    """
    Manages notifications and user feedback for the tray application
    """
    
    # Signals
    notificationClicked = pyqtSignal(str, str)  # notification_id, action
    
    def __init__(self, settings_manager):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        
        # Notification state
        self.notification_history = []
        self.pending_notifications = []
        
        # Windows notification support
        self.windows_notifications_available = self._check_windows_notifications()
        
        self.logger.info("🔔 Notification system initialized")
    
    def _check_windows_notifications(self) -> bool:
        """Check if Windows 10+ notifications are available"""
        try:
            # Try to import Windows notification libraries
            if sys.platform == 'win32':
                import platform
                version = platform.version()
                # Windows 10 and later support toast notifications
                major_version = int(version.split('.')[0])
                if major_version >= 10:
                    return True
            return False
        except:
            return False
    
    def show_notification(self, title: str, message: str, notification_type: str = "info", 
                         duration: Optional[int] = None, action_data: Optional[Dict] = None):
        """
        Show a notification to the user
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error)
            duration: Duration in milliseconds (None for default)
            action_data: Optional data for notification actions
        """
        if not self.settings_manager.SHOW_NOTIFICATIONS:
            self.logger.debug(f"Notifications disabled, skipping: {title}")
            return
        
        try:
            # Use default duration if not specified
            if duration is None:
                duration = self.settings_manager.NOTIFICATION_DURATION
            
            # Create notification data
            notification = {
                'title': title,
                'message': message,
                'type': notification_type,
                'duration': duration,
                'action_data': action_data or {},
                'timestamp': self._get_timestamp()
            }
            
            # Add to history
            self.notification_history.append(notification)
            
            # Keep history limited
            if len(self.notification_history) > 100:
                self.notification_history = self.notification_history[-50:]
            
            # Show the notification
            if self.windows_notifications_available:
                self._show_windows_notification(notification)
            else:
                self._show_tray_notification(notification)
            
            # Play sound if enabled
            if self.settings_manager.SOUND_ENABLED:
                self._play_notification_sound(notification_type)
            
            self.logger.debug(f"Notification shown: {title} - {message}")
            
        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")
    
    def _show_windows_notification(self, notification: Dict):
        """Show Windows 10+ toast notification"""
        try:
            # Try to use Windows toast notifications
            # This would require win10toast or similar library
            # For now, fallback to tray notification
            self._show_tray_notification(notification)
            
        except Exception as e:
            self.logger.debug(f"Windows notification failed, using tray: {e}")
            self._show_tray_notification(notification)
    
    def _show_tray_notification(self, notification: Dict):
        """Show system tray notification"""
        try:
            # Get tray icon from application
            app = QApplication.instance()
            if not app:
                return
            
            # Find system tray icon
            tray_icon = None
            for widget in app.allWidgets():
                if isinstance(widget, QSystemTrayIcon):
                    tray_icon = widget
                    break
            
            if not tray_icon:
                self.logger.warning("No system tray icon found for notification")
                return
            
            # Map notification types to tray icon types
            icon_map = {
                'info': QSystemTrayIcon.Information,
                'success': QSystemTrayIcon.Information,
                'warning': QSystemTrayIcon.Warning,
                'error': QSystemTrayIcon.Critical
            }
            
            icon_type = icon_map.get(notification['type'], QSystemTrayIcon.Information)
            
            # Show tray notification
            tray_icon.showMessage(
                notification['title'],
                notification['message'],
                icon_type,
                notification['duration']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to show tray notification: {e}")
    
    def _play_notification_sound(self, notification_type: str):
        """Play notification sound"""
        try:
            if sys.platform == 'win32':
                import winsound
                
                # Map notification types to system sounds
                sound_map = {
                    'info': winsound.MB_OK,
                    'success': winsound.MB_OK,
                    'warning': winsound.MB_ICONEXCLAMATION,
                    'error': winsound.MB_ICONHAND
                }
                
                sound_type = sound_map.get(notification_type, winsound.MB_OK)
                winsound.MessageBeep(sound_type)
                
        except Exception as e:
            self.logger.debug(f"Failed to play notification sound: {e}")
    
    def show_processing_notification(self, directory: str, item_count: int):
        """Show notification for processing start"""
        folder_name = Path(directory).name
        message = f"Processing {item_count} items in '{folder_name}'"
        
        self.show_notification(
            "Processing Started",
            message,
            "info",
            action_data={'directory': directory, 'count': item_count}
        )
    
    def show_completion_notification(self, results: Dict[str, Any]):
        """Show notification for processing completion"""
        successful = results.get('successful', 0)
        total = results.get('total_processed', 0)
        failed = results.get('failed', 0)
        
        if failed == 0:
            # All successful
            message = f"Successfully processed {successful} items"
            notification_type = "success"
            title = "Processing Complete"
        elif successful == 0:
            # All failed
            message = f"Failed to process {failed} items"
            notification_type = "error"
            title = "Processing Failed"
        else:
            # Mixed results
            message = f"Processed {successful}/{total} items successfully"
            notification_type = "warning"
            title = "Processing Complete"
        
        # Add details if enabled
        if self.settings_manager.DETAILED_NOTIFICATIONS:
            details = results.get('details', [])
            if details:
                series_count = results.get('series_count', 0)
                movie_count = results.get('movie_count', 0)
                if series_count or movie_count:
                    message += f"\n{series_count} TV series, {movie_count} movies"
        
        self.show_notification(title, message, notification_type, action_data=results)
    
    def show_error_notification(self, title: str, error_message: str, context: Optional[Dict] = None):
        """Show error notification with context"""
        # Truncate long error messages
        if len(error_message) > 100:
            error_message = error_message[:97] + "..."
        
        self.show_notification(
            title,
            error_message,
            "error",
            action_data={'context': context or {}}
        )
    
    def show_api_error_notification(self, api_name: str, error_details: str):
        """Show API-specific error notification"""
        title = f"{api_name} API Error"
        message = f"Failed to connect to {api_name}: {error_details}"
        
        self.show_notification(
            title,
            message,
            "warning",
            action_data={'api': api_name, 'error': error_details}
        )
    
    def show_monitoring_notification(self, action: str, directory: str):
        """Show monitoring-related notification"""
        folder_name = Path(directory).name
        
        if action == "started":
            title = "Monitoring Started"
            message = f"Now monitoring '{folder_name}' for changes"
            notification_type = "info"
        elif action == "stopped":
            title = "Monitoring Stopped"
            message = f"Stopped monitoring '{folder_name}'"
            notification_type = "info"
        elif action == "added":
            title = "Folder Added"
            message = f"Added '{folder_name}' to monitoring"
            notification_type = "success"
        elif action == "removed":
            title = "Folder Removed"
            message = f"Removed '{folder_name}' from monitoring"
            notification_type = "info"
        else:
            return
        
        self.show_notification(
            title,
            message,
            notification_type,
            action_data={'action': action, 'directory': directory}
        )
    
    def show_cache_notification(self, action: str, details: Dict[str, Any]):
        """Show cache-related notification"""
        if action == "cleaned":
            cleaned_count = details.get('cleaned', 0)
            size_freed = details.get('size_freed', 0) / (1024 * 1024)  # Convert to MB
            
            if cleaned_count > 0:
                message = f"Cleaned {cleaned_count} files, freed {size_freed:.1f} MB"
                self.show_notification("Cache Cleaned", message, "success")
        elif action == "full":
            message = "Cache is full, cleaning old files..."
            self.show_notification("Cache Full", message, "warning")
    
    def show_startup_notification(self):
        """Show application startup notification"""
        if self.settings_manager.START_MINIMIZED:
            message = "Smart Media Icon is running in the system tray"
            self.show_notification(
                "Application Started",
                message,
                "info",
                duration=3000  # Shorter duration for startup
            )
    
    def show_settings_saved_notification(self):
        """Show notification when settings are saved"""
        self.show_notification(
            "Settings Saved",
            "Configuration has been saved successfully",
            "success",
            duration=2000  # Short duration
        )
    
    def get_notification_history(self, limit: int = 20) -> list:
        """
        Get recent notification history
        
        Args:
            limit: Maximum number of notifications to return
            
        Returns:
            List of recent notifications
        """
        return self.notification_history[-limit:] if self.notification_history else []
    
    def clear_notification_history(self):
        """Clear notification history"""
        self.notification_history.clear()
        self.logger.info("Notification history cleared")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def update_settings(self, settings_manager):
        """Update notification settings"""
        self.settings_manager = settings_manager
        self.logger.debug("Notification settings updated")


class NotificationQueue(QObject):
    """
    Manages notification queuing to prevent overwhelming the user
    """
    
    def __init__(self, notification_system):
        super().__init__()
        
        self.notification_system = notification_system
        self.queue = []
        self.is_processing = False
        
        # Timer for processing queue
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self._process_queue)
        self.process_timer.start(1000)  # Process every second
    
    def add_notification(self, title: str, message: str, notification_type: str = "info", **kwargs):
        """Add notification to queue"""
        notification = {
            'title': title,
            'message': message,
            'type': notification_type,
            'kwargs': kwargs,
            'added_time': self._get_timestamp()
        }
        
        # Check for duplicates
        if not self._is_duplicate(notification):
            self.queue.append(notification)
    
    def _process_queue(self):
        """Process notifications from queue"""
        if self.is_processing or not self.queue:
            return
        
        self.is_processing = True
        
        try:
            # Process one notification at a time
            notification = self.queue.pop(0)
            
            self.notification_system.show_notification(
                notification['title'],
                notification['message'],
                notification['type'],
                **notification['kwargs']
            )
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Error processing notification queue: {e}")
        finally:
            self.is_processing = False
    
    def _is_duplicate(self, new_notification: Dict) -> bool:
        """Check if notification is duplicate of recent ones"""
        # Simple duplicate detection based on title and type
        for existing in self.queue[-5:]:  # Check last 5 notifications
            if (existing['title'] == new_notification['title'] and 
                existing['type'] == new_notification['type']):
                return True
        return False
    
    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def clear_queue(self):
        """Clear notification queue"""
        self.queue.clear()
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self.queue)