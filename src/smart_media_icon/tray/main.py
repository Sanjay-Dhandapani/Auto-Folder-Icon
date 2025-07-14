#!/usr/bin/env python3
"""
Smart Media Icon Tray Application - Main Entry Point

This is the main entry point for the Windows system tray application.
It integrates with the existing smart_media_icon functionality while
providing a user-friendly tray interface.
"""

import sys
import os
import logging
import signal
from pathlib import Path
from typing import Optional

# PyQt5 imports
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon

# Import existing smart_media_icon components
from ..core.icon_setter import SmartIconSetter
from ..utils.config import Config

# Import tray-specific components
from .tray_manager import TrayManager
from .settings_manager import TraySettingsManager
from .file_watcher import FileWatcher
from .processing_engine import ProcessingEngine
from .notification_system import NotificationSystem


class TrayApplication(QObject):
    """
    Main tray application class that coordinates all components
    """
    
    # Signals for inter-component communication
    statusChanged = pyqtSignal(str, str)  # status, message
    processingStarted = pyqtSignal(str)   # directory
    processingFinished = pyqtSignal(dict) # results
    
    def __init__(self, config_file: Optional[str] = None):
        super().__init__()
        
        # Initialize logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🚀 Starting Smart Media Icon Tray Application")
        
        # Initialize configuration
        try:
            self.settings_manager = TraySettingsManager(config_file)
            self.logger.info(f"⚙️ Configuration loaded from: {config_file or 'default locations'}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load configuration: {e}")
            QMessageBox.critical(None, "Configuration Error", 
                               f"Failed to load configuration:\n{e}")
            sys.exit(1)
        
        # Initialize core components
        self.notification_system = None
        self.tray_manager = None
        self.file_watcher = None
        self.processing_engine = None
        
        # Application state
        self.is_running = False
        self.app_icon = None
        
    def setup_logging(self):
        """Configure logging for the tray application"""
        log_level = logging.INFO  # Can be made configurable
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(name)s - %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # File handler (optional)
        log_dir = Path.home() / '.smart_media_icon' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / 'tray_app.log')
        file_handler.setFormatter(formatter)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=[console_handler, file_handler],
            force=True
        )
        
        # Reduce noise from external libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
    
    def initialize_components(self):
        """Initialize all tray application components"""
        try:
            self.logger.info("🔧 Initializing tray components...")
            
            # Initialize notification system first
            self.notification_system = NotificationSystem(self.settings_manager)
            
            # Initialize processing engine
            self.processing_engine = ProcessingEngine(
                self.settings_manager,
                self.notification_system
            )
            
            # Initialize file watcher
            self.file_watcher = FileWatcher(
                self.settings_manager,
                self.processing_engine
            )
            
            # Initialize tray manager
            self.tray_manager = TrayManager(
                self.settings_manager,
                self.file_watcher,
                self.processing_engine,
                self.notification_system
            )
            
            # Connect signals
            self.connect_signals()
            
            self.logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize components: {e}")
            return False
    
    def connect_signals(self):
        """Connect signals between components"""
        # Connect processing signals
        self.processing_engine.processingStarted.connect(self.on_processing_started)
        self.processing_engine.processingFinished.connect(self.on_processing_finished)
        self.processing_engine.statusChanged.connect(self.on_status_changed)
        
        # Connect file watcher signals
        self.file_watcher.fileEvent.connect(self.on_file_event)
        
        # Connect tray manager signals
        self.tray_manager.exitRequested.connect(self.quit_application)
        self.tray_manager.settingsRequested.connect(self.show_settings)
    
    def on_processing_started(self, directory: str):
        """Handle processing started signal"""
        self.logger.info(f"🔄 Processing started for: {directory}")
        self.processingStarted.emit(directory)
    
    def on_processing_finished(self, results: dict):
        """Handle processing finished signal"""
        success_count = results.get('successful', 0)
        total_count = results.get('total_processed', 0)
        self.logger.info(f"✅ Processing finished: {success_count}/{total_count} successful")
        self.processingFinished.emit(results)
    
    def on_status_changed(self, status: str, message: str):
        """Handle status change signal"""
        self.logger.debug(f"Status: {status} - {message}")
        self.statusChanged.emit(status, message)
    
    def on_file_event(self, event_path: str, event_type: str):
        """Handle file system event"""
        self.logger.debug(f"File event: {event_type} - {event_path}")
    
    def show_settings(self):
        """Show settings dialog"""
        try:
            self.tray_manager.show_settings_dialog()
        except Exception as e:
            self.logger.error(f"Failed to show settings: {e}")
    
    def start(self):
        """Start the tray application"""
        if self.is_running:
            self.logger.warning("Application is already running")
            return False
        
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "System Tray", 
                               "System tray is not available on this system.")
            return False
        
        # Initialize components
        if not self.initialize_components():
            return False
        
        # Start the tray manager
        if not self.tray_manager.start():
            self.logger.error("Failed to start tray manager")
            return False
        
        # Start file watching if enabled
        if self.settings_manager.AUTO_MONITOR_ENABLED:
            self.file_watcher.start_monitoring()
            self.logger.info("👁️ File monitoring started")
        
        self.is_running = True
        self.logger.info("🎉 Tray application started successfully")
        
        # Show startup notification
        if self.settings_manager.SHOW_NOTIFICATIONS:
            self.notification_system.show_notification(
                "Smart Media Icon",
                "Tray application started successfully",
                "info"
            )
        
        return True
    
    def stop(self):
        """Stop the tray application"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 Stopping tray application...")
        
        # Stop file watching
        if self.file_watcher:
            self.file_watcher.stop_monitoring()
        
        # Stop processing engine
        if self.processing_engine:
            self.processing_engine.stop()
        
        # Stop tray manager
        if self.tray_manager:
            self.tray_manager.stop()
        
        self.is_running = False
        self.logger.info("✅ Tray application stopped")
    
    def quit_application(self):
        """Quit the application gracefully"""
        self.stop()
        QApplication.quit()


def setup_signal_handlers(app: TrayApplication):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        app.quit_application()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point for the tray application"""
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Smart Media Icon")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Smart Media Icon Team")
    app.setQuitOnLastWindowClosed(False)  # Keep running when windows are closed
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Smart Media Icon Tray Application")
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    # Adjust logging level if debug is enabled
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create tray application
        tray_app = TrayApplication(args.config)
        
        # Setup signal handlers
        setup_signal_handlers(tray_app)
        
        # Start the application
        if not tray_app.start():
            print("Failed to start tray application")
            return 1
        
        # Run the Qt event loop
        return app.exec_()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())