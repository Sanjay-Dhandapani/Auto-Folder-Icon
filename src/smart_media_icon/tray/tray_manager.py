#!/usr/bin/env python3
"""
Smart Media Icon Tray Manager

Manages the system tray icon, context menu, and user interactions.
Provides a professional Windows tray application interface.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (
    QSystemTrayIcon, QMenu, QAction, QActionGroup, QApplication,
    QFileDialog, QMessageBox, QWidget
)
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QIcon, QPixmap


class TrayManager(QObject):
    """
    Manages the system tray icon and provides user interface functionality
    """
    
    # Signals
    exitRequested = pyqtSignal()
    settingsRequested = pyqtSignal()
    scanRequested = pyqtSignal(str)  # directory path
    monitoringToggled = pyqtSignal(bool)  # enabled/disabled
    
    def __init__(self, settings_manager, file_watcher, processing_engine, notification_system):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Store component references
        self.settings_manager = settings_manager
        self.file_watcher = file_watcher
        self.processing_engine = processing_engine
        self.notification_system = notification_system
        
        # Tray components
        self.tray_icon = None
        self.context_menu = None
        self.settings_dialog = None
        
        # Menu actions
        self.actions = {}
        
        # Status tracking
        self.current_status = "idle"
        self.last_scan_info = {"count": 0, "time": None}
        self.monitoring_enabled = False
        
        # Update timer for dynamic menu content
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_menu_status)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def start(self) -> bool:
        """Initialize and start the tray icon"""
        try:
            self.logger.info("🎯 Starting tray manager...")
            
            # Create tray icon
            self.tray_icon = QSystemTrayIcon()
            
            # Set initial icon
            self.set_tray_icon("idle")
            
            # Create context menu
            self.create_context_menu()
            
            # Set the context menu
            self.tray_icon.setContextMenu(self.context_menu)
            
            # Connect tray icon signals
            self.tray_icon.activated.connect(self.on_tray_icon_activated)
            
            # Show the tray icon
            self.tray_icon.show()
            
            # Set initial tooltip
            self.update_tooltip("Smart Media Icon - Ready")
            
            self.logger.info("✅ Tray manager started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start tray manager: {e}")
            return False
    
    def stop(self):
        """Stop the tray manager"""
        self.logger.info("🛑 Stopping tray manager...")
        
        if self.update_timer:
            self.update_timer.stop()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        self.logger.info("✅ Tray manager stopped")
    
    def create_context_menu(self):
        """Create the context menu for the tray icon"""
        self.context_menu = QMenu()
        
        # Title (non-clickable)
        title_action = QAction("📱 Smart Media Icon", self.context_menu)
        title_action.setEnabled(False)
        self.context_menu.addAction(title_action)
        self.context_menu.addSeparator()
        
        # Quick scan actions
        self.actions['scan_current'] = QAction("🔍 Scan Current Directory", self.context_menu)
        self.actions['scan_current'].triggered.connect(self.scan_current_directory)
        self.context_menu.addAction(self.actions['scan_current'])
        
        self.actions['scan_folder'] = QAction("📂 Scan Specific Folder...", self.context_menu)
        self.actions['scan_folder'].triggered.connect(self.scan_specific_folder)
        self.context_menu.addAction(self.actions['scan_folder'])
        
        self.context_menu.addSeparator()
        
        # Monitored folders submenu
        self.create_monitored_folders_menu()
        
        self.context_menu.addSeparator()
        
        # Auto monitor toggle
        self.actions['auto_monitor'] = QAction("🎯 Auto Monitor", self.context_menu)
        self.actions['auto_monitor'].setCheckable(True)
        self.actions['auto_monitor'].setChecked(self.settings_manager.AUTO_MONITOR_ENABLED)
        self.actions['auto_monitor'].triggered.connect(self.toggle_auto_monitoring)
        self.context_menu.addAction(self.actions['auto_monitor'])
        
        # Monitor settings
        self.actions['monitor_settings'] = QAction("⚙️ Monitor Settings...", self.context_menu)
        self.actions['monitor_settings'].triggered.connect(self.show_monitor_settings)
        self.context_menu.addAction(self.actions['monitor_settings'])
        
        self.context_menu.addSeparator()
        
        # Status submenu
        self.create_status_menu()
        
        self.context_menu.addSeparator()
        
        # Settings and info
        self.actions['settings'] = QAction("⚙️ Settings...", self.context_menu)
        self.actions['settings'].triggered.connect(self.show_settings)
        self.context_menu.addAction(self.actions['settings'])
        
        self.actions['view_logs'] = QAction("📋 View Logs...", self.context_menu)
        self.actions['view_logs'].triggered.connect(self.view_logs)
        self.context_menu.addAction(self.actions['view_logs'])
        
        self.actions['about'] = QAction("ℹ️ About...", self.context_menu)
        self.actions['about'].triggered.connect(self.show_about)
        self.context_menu.addAction(self.actions['about'])
        
        self.context_menu.addSeparator()
        
        # Exit
        self.actions['exit'] = QAction("❌ Exit", self.context_menu)
        self.actions['exit'].triggered.connect(self.exit_application)
        self.context_menu.addAction(self.actions['exit'])
    
    def create_monitored_folders_menu(self):
        """Create the monitored folders submenu"""
        folders_menu = QMenu("📁 Monitored Folders", self.context_menu)
        
        # Get monitored directories from settings
        monitored_dirs = getattr(self.settings_manager, 'MONITORED_DIRECTORIES', [])
        
        if monitored_dirs:
            for directory in monitored_dirs:
                if isinstance(directory, dict):
                    path = directory.get('path', '')
                    enabled = directory.get('enabled', True)
                else:
                    path = str(directory)
                    enabled = True
                
                if path:
                    icon = "✅" if enabled else "❌"
                    action = QAction(f"{icon} {Path(path).name}", folders_menu)
                    action.setToolTip(path)
                    action.triggered.connect(lambda checked, p=path: self.scan_directory(p))
                    folders_menu.addAction(action)
        else:
            no_folders_action = QAction("No folders configured", folders_menu)
            no_folders_action.setEnabled(False)
            folders_menu.addAction(no_folders_action)
        
        folders_menu.addSeparator()
        
        # Add folder action
        add_folder_action = QAction("➕ Add Folder...", folders_menu)
        add_folder_action.triggered.connect(self.add_monitored_folder)
        folders_menu.addAction(add_folder_action)
        
        # Manage folders action
        manage_folders_action = QAction("⚙️ Manage Folders...", folders_menu)
        manage_folders_action.triggered.connect(self.manage_folders)
        folders_menu.addAction(manage_folders_action)
        
        self.context_menu.addMenu(folders_menu)
    
    def create_status_menu(self):
        """Create the status submenu"""
        status_menu = QMenu("📊 Status", self.context_menu)
        
        # Last scan info
        last_scan_text = f"📈 Last Scan: {self.last_scan_info['count']} items"
        last_scan_action = QAction(last_scan_text, status_menu)
        last_scan_action.setEnabled(False)
        status_menu.addAction(last_scan_action)
        
        # Next check countdown (if monitoring)
        if self.monitoring_enabled:
            next_check_action = QAction("🕒 Next Check: 30s", status_menu)
            next_check_action.setEnabled(False)
            status_menu.addAction(next_check_action)
        
        # Cache statistics
        cache_info = self.get_cache_statistics()
        cache_action = QAction(f"💾 Cache: {cache_info['count']} posters", status_menu)
        cache_action.setEnabled(False)
        status_menu.addAction(cache_action)
        
        # API status
        api_status = self.get_api_status()
        api_action = QAction(f"🔗 APIs: {api_status['active']}/{api_status['total']} Active", status_menu)
        api_action.setEnabled(False)
        status_menu.addAction(api_action)
        
        self.context_menu.addMenu(status_menu)
    
    def set_tray_icon(self, status: str):
        """Set the tray icon based on current status"""
        icon_map = {
            "idle": "💻",
            "processing": "🔄", 
            "monitoring": "👁️",
            "error": "❌",
            "disabled": "⏸️"
        }
        
        # For now, use a simple text-based icon
        # In production, you'd use actual .ico files
        icon_text = icon_map.get(status, "💻")
        
        # Create a simple icon (in production, load from resources)
        try:
            # Try to create a basic icon
            pixmap = QPixmap(16, 16)
            pixmap.fill()
            icon = QIcon(pixmap)
            self.tray_icon.setIcon(icon)
        except:
            # Fallback: use default system icon
            self.tray_icon.setIcon(self.tray_icon.style().standardIcon(self.tray_icon.style().SP_ComputerIcon))
        
        self.current_status = status
    
    def update_tooltip(self, message: str):
        """Update the tray icon tooltip"""
        if self.tray_icon:
            self.tray_icon.setToolTip(message)
    
    def update_menu_status(self):
        """Update dynamic menu content"""
        try:
            # Update monitoring status
            self.monitoring_enabled = getattr(self.settings_manager, 'AUTO_MONITOR_ENABLED', False)
            if 'auto_monitor' in self.actions:
                self.actions['auto_monitor'].setChecked(self.monitoring_enabled)
            
            # Update tooltip based on current status
            if self.current_status == "processing":
                self.update_tooltip("Smart Media Icon - Processing files...")
            elif self.monitoring_enabled:
                monitored_count = len(getattr(self.settings_manager, 'MONITORED_DIRECTORIES', []))
                self.update_tooltip(f"Smart Media Icon - Monitoring {monitored_count} folders")
            else:
                self.update_tooltip("Smart Media Icon - Ready")
                
        except Exception as e:
            self.logger.debug(f"Error updating menu status: {e}")
    
    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation (click events)"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_settings()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click - show status in tooltip
            self.update_menu_status()
    
    # Action handlers
    def scan_current_directory(self):
        """Scan the currently active directory in Windows Explorer"""
        try:
            # Get current directory from Windows Explorer
            current_dir = self.get_current_explorer_directory()
            if current_dir:
                self.scan_directory(current_dir)
            else:
                # Fallback to user's home directory
                home_dir = str(Path.home())
                self.scan_directory(home_dir)
        except Exception as e:
            self.logger.error(f"Error scanning current directory: {e}")
            self.notification_system.show_notification(
                "Scan Error", f"Failed to scan current directory: {e}", "error"
            )
    
    def scan_specific_folder(self):
        """Open folder dialog and scan selected folder"""
        try:
            dialog = QFileDialog()
            folder = dialog.getExistingDirectory(
                None,
                "Select Media Folder to Scan",
                str(Path.home()),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            
            if folder:
                self.scan_directory(folder)
        except Exception as e:
            self.logger.error(f"Error in folder selection: {e}")
    
    def scan_directory(self, directory: str):
        """Trigger directory scan"""
        self.logger.info(f"🔍 Scanning directory: {directory}")
        self.scanRequested.emit(directory)
    
    def toggle_auto_monitoring(self, enabled: bool):
        """Toggle automatic monitoring on/off"""
        self.logger.info(f"🎯 Auto monitoring {'enabled' if enabled else 'disabled'}")
        self.settings_manager.AUTO_MONITOR_ENABLED = enabled
        self.settings_manager.save_tray_settings()
        self.monitoringToggled.emit(enabled)
        
        # Update tray icon
        if enabled:
            self.set_tray_icon("monitoring")
        else:
            self.set_tray_icon("idle")
    
    def add_monitored_folder(self):
        """Add a new folder to monitoring"""
        try:
            dialog = QFileDialog()
            folder = dialog.getExistingDirectory(
                None,
                "Add Folder to Monitor",
                str(Path.home()),
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            
            if folder:
                # Add to monitored directories
                monitored_dirs = getattr(self.settings_manager, 'MONITORED_DIRECTORIES', [])
                if not any(d.get('path') == folder if isinstance(d, dict) else d == folder for d in monitored_dirs):
                    monitored_dirs.append({
                        'path': folder,
                        'enabled': True,
                        'recursive': True
                    })
                    self.settings_manager.MONITORED_DIRECTORIES = monitored_dirs
                    self.settings_manager.save_tray_settings()
                    
                    self.logger.info(f"📁 Added folder to monitoring: {folder}")
                    self.notification_system.show_notification(
                        "Folder Added", f"Now monitoring: {Path(folder).name}", "info"
                    )
                    
                    # Recreate menu to show new folder
                    self.create_context_menu()
                else:
                    self.notification_system.show_notification(
                        "Folder Already Monitored", f"Folder is already being monitored", "warning"
                    )
        except Exception as e:
            self.logger.error(f"Error adding monitored folder: {e}")
    
    def manage_folders(self):
        """Open folder management dialog"""
        # This would open a dedicated folder management dialog
        self.show_settings()  # For now, redirect to settings
    
    def show_monitor_settings(self):
        """Show monitor-specific settings"""
        self.show_settings()  # For now, redirect to main settings
    
    def show_settings(self):
        """Show the settings dialog"""
        self.settingsRequested.emit()
    
    def show_settings_dialog(self):
        """Actually create and show the settings dialog"""
        try:
            from .gui.settings_dialog import SettingsDialog
            
            if not self.settings_dialog:
                self.settings_dialog = SettingsDialog(self.settings_manager)
            
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            
        except ImportError:
            # Settings dialog not implemented yet
            QMessageBox.information(
                None, 
                "Settings", 
                "Settings dialog will be available in the next update."
            )
        except Exception as e:
            self.logger.error(f"Error showing settings dialog: {e}")
            QMessageBox.critical(None, "Error", f"Failed to open settings: {e}")
    
    def view_logs(self):
        """Open log file viewer"""
        try:
            log_dir = Path.home() / '.smart_media_icon' / 'logs'
            log_file = log_dir / 'tray_app.log'
            
            if log_file.exists():
                # Try to open with default text editor
                os.startfile(str(log_file))
            else:
                QMessageBox.information(None, "Logs", "No log file found.")
        except Exception as e:
            self.logger.error(f"Error opening logs: {e}")
            QMessageBox.critical(None, "Error", f"Failed to open logs: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h3>Smart Media Icon System</h3>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Description:</b> Professional Windows desktop utility for automatic media icon management</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Smart TV series and movie detection</li>
        <li>Custom folder icons for TV series</li>
        <li>FFmpeg artwork embedding for movies</li>
        <li>Multi-API poster fetching</li>
        <li>Automatic folder monitoring</li>
        </ul>
        <p><b>Copyright:</b> © 2024 Smart Media Icon Team</p>
        <p><b>License:</b> MIT License</p>
        """
        
        QMessageBox.about(None, "About Smart Media Icon", about_text)
    
    def exit_application(self):
        """Exit the application"""
        self.logger.info("👋 User requested application exit")
        self.exitRequested.emit()
    
    # Helper methods
    def get_current_explorer_directory(self) -> Optional[str]:
        """Get the current directory from Windows Explorer"""
        try:
            # This would use Windows API to get active Explorer window
            # For now, return None to use fallback
            return None
        except:
            return None
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            cache_dir = Path(self.settings_manager.CACHE_DIR)
            if cache_dir.exists():
                cache_files = list(cache_dir.glob("*.jpg"))
                return {
                    'count': len(cache_files),
                    'size': sum(f.stat().st_size for f in cache_files) / (1024 * 1024)  # MB
                }
        except:
            pass
        
        return {'count': 0, 'size': 0}
    
    def get_api_status(self) -> Dict[str, int]:
        """Get API connectivity status"""
        # In a real implementation, this would check API connectivity
        total_apis = 4  # TMDB, OMDb, TVmaze, AniList
        active_apis = 3  # Mock for now
        
        return {
            'total': total_apis,
            'active': active_apis
        }
    
    def update_processing_status(self, status: str, message: str = ""):
        """Update the tray icon and tooltip based on processing status"""
        if status == "started":
            self.set_tray_icon("processing")
            self.update_tooltip(f"Smart Media Icon - Processing: {message}")
        elif status == "finished":
            self.set_tray_icon("monitoring" if self.monitoring_enabled else "idle")
            self.update_tooltip("Smart Media Icon - Processing complete")
        elif status == "error":
            self.set_tray_icon("error")
            self.update_tooltip(f"Smart Media Icon - Error: {message}")