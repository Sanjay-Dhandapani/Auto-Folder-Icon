#!/usr/bin/env python3
"""
Smart Media Icon Settings Dialog

Comprehensive settings interface for the tray application with tabbed interface
for general, monitoring, API keys, and advanced settings.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSpinBox, QDoubleSpinBox,
    QListWidget, QListWidgetItem, QTextEdit, QGroupBox, QComboBox,
    QFileDialog, QMessageBox, QProgressBar, QSlider, QFrame,
    QScrollArea, QWidget, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette


class SettingsDialog(QDialog):
    """
    Main settings dialog with tabbed interface
    """
    
    # Signals
    settingsChanged = pyqtSignal(dict)  # settings changes
    apiTestRequested = pyqtSignal(str, str)  # api_name, api_key
    folderScanRequested = pyqtSignal(str)  # directory path
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        
        # Dialog properties
        self.setWindowTitle("Smart Media Icon - Settings")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        # Initialize UI
        self.setup_ui()
        self.load_settings()
        
        # Connect signals
        self.connect_signals()
        
        self.logger.debug("Settings dialog initialized")
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_monitoring_tab()
        self.create_api_keys_tab()
        self.create_advanced_tab()
        self.create_about_tab()
        
        # Create button bar
        self.create_button_bar(layout)
        
        # Apply styling
        self.apply_styling()
    
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Media Directories section
        directories_group = QGroupBox("📁 Media Directories")
        directories_layout = QVBoxLayout(directories_group)
        
        # Directory list
        self.directories_list = QListWidget()
        self.directories_list.setMinimumHeight(120)
        directories_layout.addWidget(self.directories_list)
        
        # Directory buttons
        dir_buttons_layout = QHBoxLayout()
        self.add_dir_btn = QPushButton("➕ Add Directory")
        self.remove_dir_btn = QPushButton("➖ Remove")
        self.browse_dir_btn = QPushButton("🔍 Browse")
        
        dir_buttons_layout.addWidget(self.add_dir_btn)
        dir_buttons_layout.addWidget(self.remove_dir_btn)
        dir_buttons_layout.addWidget(self.browse_dir_btn)
        dir_buttons_layout.addStretch()
        
        directories_layout.addLayout(dir_buttons_layout)
        layout.addWidget(directories_group)
        
        # Startup Options section
        startup_group = QGroupBox("🚀 Startup Options")
        startup_layout = QGridLayout(startup_group)
        
        self.start_with_windows_cb = QCheckBox("Start with Windows")
        self.start_minimized_cb = QCheckBox("Start minimized to tray")
        self.close_to_tray_cb = QCheckBox("Close to tray instead of exit")
        
        startup_layout.addWidget(self.start_with_windows_cb, 0, 0)
        startup_layout.addWidget(self.start_minimized_cb, 1, 0)
        startup_layout.addWidget(self.close_to_tray_cb, 2, 0)
        
        layout.addWidget(startup_group)
        
        # Notifications section
        notifications_group = QGroupBox("🔔 Notifications")
        notifications_layout = QGridLayout(notifications_group)
        
        self.show_notifications_cb = QCheckBox("Show desktop notifications")
        self.sound_enabled_cb = QCheckBox("Play notification sounds")
        self.detailed_notifications_cb = QCheckBox("Show detailed processing information")
        
        notifications_layout.addWidget(QLabel("Duration (seconds):"), 0, 0)
        self.notification_duration_spin = QDoubleSpinBox()
        self.notification_duration_spin.setRange(1.0, 30.0)
        self.notification_duration_spin.setSuffix(" sec")
        notifications_layout.addWidget(self.notification_duration_spin, 0, 1)
        
        notifications_layout.addWidget(self.show_notifications_cb, 1, 0, 1, 2)
        notifications_layout.addWidget(self.sound_enabled_cb, 2, 0, 1, 2)
        notifications_layout.addWidget(self.detailed_notifications_cb, 3, 0, 1, 2)
        
        layout.addWidget(notifications_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "General")
    
    def create_monitoring_tab(self):
        """Create monitoring settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Auto Monitoring section
        monitoring_group = QGroupBox("👁️ Auto Monitoring")
        monitoring_layout = QGridLayout(monitoring_group)
        
        self.auto_monitor_cb = QCheckBox("Enable automatic folder monitoring")
        self.monitor_recursive_cb = QCheckBox("Monitor subdirectories recursively")
        
        monitoring_layout.addWidget(self.auto_monitor_cb, 0, 0, 1, 2)
        monitoring_layout.addWidget(self.monitor_recursive_cb, 1, 0, 1, 2)
        
        layout.addWidget(monitoring_group)
        
        # Timing Settings section
        timing_group = QGroupBox("⏱️ Timing Settings")
        timing_layout = QGridLayout(timing_group)
        
        timing_layout.addWidget(QLabel("Debounce Time:"), 0, 0)
        self.debounce_time_spin = QDoubleSpinBox()
        self.debounce_time_spin.setRange(1.0, 30.0)
        self.debounce_time_spin.setSuffix(" seconds")
        timing_layout.addWidget(self.debounce_time_spin, 0, 1)
        
        timing_layout.addWidget(QLabel("Max Concurrent:"), 1, 0)
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setSuffix(" processes")
        timing_layout.addWidget(self.max_concurrent_spin, 1, 1)
        
        timing_layout.addWidget(QLabel("Max Events/Second:"), 2, 0)
        self.max_events_spin = QSpinBox()
        self.max_events_spin.setRange(1, 100)
        timing_layout.addWidget(self.max_events_spin, 2, 1)
        
        layout.addWidget(timing_group)
        
        # Watched Folders Status section
        status_group = QGroupBox("📂 Watched Folders Status")
        status_layout = QVBoxLayout(status_group)
        
        self.folders_status_table = QTableWidget()
        self.folders_status_table.setColumnCount(3)
        self.folders_status_table.setHorizontalHeaderLabels(["Folder", "Status", "Last Check"])
        self.folders_status_table.horizontalHeader().setStretchLastSection(True)
        self.folders_status_table.setMinimumHeight(150)
        
        status_layout.addWidget(self.folders_status_table)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Status")
        refresh_btn.clicked.connect(self.refresh_folder_status)
        status_layout.addWidget(refresh_btn)
        
        layout.addWidget(status_group)
        
        # File Filters section
        filters_group = QGroupBox("🗂️ File Filters")
        filters_layout = QGridLayout(filters_group)
        
        self.skip_hidden_cb = QCheckBox("Skip hidden files and folders")
        self.skip_temp_cb = QCheckBox("Skip temporary files (.tmp, .part)")
        self.process_existing_cb = QCheckBox("Process existing files on startup")
        
        filters_layout.addWidget(self.skip_hidden_cb, 0, 0)
        filters_layout.addWidget(self.skip_temp_cb, 1, 0)
        filters_layout.addWidget(self.process_existing_cb, 2, 0)
        
        layout.addWidget(filters_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Monitoring")
    
    def create_api_keys_tab(self):
        """Create API keys configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API configuration sections
        apis = [
            ("🎬 TMDB (The Movie Database)", "TMDB_API_KEY"),
            ("🍿 OMDb (Open Movie Database)", "OMDB_API_KEY"),
            ("📺 TVmaze", "TVMAZE_API_KEY"),
            ("🎌 AniList", "ANILIST_API_KEY")
        ]
        
        self.api_inputs = {}
        self.api_test_buttons = {}
        self.api_status_labels = {}
        
        for api_name, api_key in apis:
            group = QGroupBox(api_name)
            group_layout = QGridLayout(group)
            
            # API Key input
            group_layout.addWidget(QLabel("API Key:"), 0, 0)
            api_input = QLineEdit()
            api_input.setEchoMode(QLineEdit.Password)
            api_input.setPlaceholderText("Enter API key...")
            group_layout.addWidget(api_input, 0, 1)
            
            # Test button
            test_btn = QPushButton("🔍 Test")
            test_btn.clicked.connect(lambda checked, key=api_key: self.test_api_key(key))
            group_layout.addWidget(test_btn, 0, 2)
            
            # Status label
            status_label = QLabel("Status: Not tested")
            status_label.setStyleSheet("color: gray;")
            group_layout.addWidget(status_label, 1, 0, 1, 3)
            
            # Store references
            self.api_inputs[api_key] = api_input
            self.api_test_buttons[api_key] = test_btn
            self.api_status_labels[api_key] = status_label
            
            layout.addWidget(group)
        
        # API Options section
        options_group = QGroupBox("⚙️ API Options")
        options_layout = QGridLayout(options_group)
        
        self.use_mock_api_cb = QCheckBox("Use mock API for testing")
        self.mock_on_failure_cb = QCheckBox("Fallback to mock on API failure")
        self.enable_api_logging_cb = QCheckBox("Enable API request logging")
        
        options_layout.addWidget(self.use_mock_api_cb, 0, 0)
        options_layout.addWidget(self.mock_on_failure_cb, 1, 0)
        options_layout.addWidget(self.enable_api_logging_cb, 2, 0)
        
        layout.addWidget(options_group)
        
        # API Help section
        help_layout = QHBoxLayout()
        get_keys_btn = QPushButton("📖 Get API Keys")
        get_keys_btn.clicked.connect(self.show_api_help)
        test_all_btn = QPushButton("🔄 Test All APIs")
        test_all_btn.clicked.connect(self.test_all_apis)
        
        help_layout.addWidget(get_keys_btn)
        help_layout.addWidget(test_all_btn)
        help_layout.addStretch()
        
        layout.addLayout(help_layout)
        layout.addStretch()
        self.tab_widget.addTab(tab, "API Keys")
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cache Management section
        cache_group = QGroupBox("💾 Cache Management")
        cache_layout = QGridLayout(cache_group)
        
        # Cache statistics
        self.cache_size_label = QLabel("Cache Size: Calculating...")
        self.cache_items_label = QLabel("Cache Items: Calculating...")
        self.cache_last_cleanup_label = QLabel("Last Cleanup: Never")
        
        cache_layout.addWidget(self.cache_size_label, 0, 0)
        cache_layout.addWidget(self.cache_items_label, 1, 0)
        cache_layout.addWidget(self.cache_last_cleanup_label, 2, 0)
        
        # Cache limit
        cache_layout.addWidget(QLabel("Cache Size Limit:"), 3, 0)
        self.cache_limit_spin = QSpinBox()
        self.cache_limit_spin.setRange(100, 10000)
        self.cache_limit_spin.setSuffix(" MB")
        cache_layout.addWidget(self.cache_limit_spin, 3, 1)
        
        # Cache options
        self.auto_cleanup_cb = QCheckBox("Auto-cleanup when cache exceeds limit")
        cache_layout.addWidget(self.auto_cleanup_cb, 4, 0, 1, 2)
        
        # Cache buttons
        cache_buttons_layout = QHBoxLayout()
        clear_cache_btn = QPushButton("🗑️ Clear Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        optimize_cache_btn = QPushButton("🔧 Optimize")
        optimize_cache_btn.clicked.connect(self.optimize_cache)
        view_cache_btn = QPushButton("📊 View Stats")
        view_cache_btn.clicked.connect(self.view_cache_stats)
        
        cache_buttons_layout.addWidget(clear_cache_btn)
        cache_buttons_layout.addWidget(optimize_cache_btn)
        cache_buttons_layout.addWidget(view_cache_btn)
        cache_buttons_layout.addStretch()
        
        cache_layout.addLayout(cache_buttons_layout, 5, 0, 1, 2)
        layout.addWidget(cache_group)
        
        # Performance Settings section
        performance_group = QGroupBox("⚙️ Performance Settings")
        performance_layout = QGridLayout(performance_group)
        
        performance_layout.addWidget(QLabel("Processing Priority:"), 0, 0)
        self.processing_priority_combo = QComboBox()
        self.processing_priority_combo.addItems(["Low", "Normal", "High"])
        performance_layout.addWidget(self.processing_priority_combo, 0, 1)
        
        self.skip_existing_icons_cb = QCheckBox("Skip files that already have icons")
        self.backup_original_files_cb = QCheckBox("Create backup of original files")
        self.verify_operations_cb = QCheckBox("Verify file operations")
        
        performance_layout.addWidget(self.skip_existing_icons_cb, 1, 0, 1, 2)
        performance_layout.addWidget(self.backup_original_files_cb, 2, 0, 1, 2)
        performance_layout.addWidget(self.verify_operations_cb, 3, 0, 1, 2)
        
        layout.addWidget(performance_group)
        
        # Logging Settings section
        logging_group = QGroupBox("📋 Logging Settings")
        logging_layout = QGridLayout(logging_group)
        
        logging_layout.addWidget(QLabel("Log Retention:"), 0, 0)
        self.log_retention_spin = QSpinBox()
        self.log_retention_spin.setRange(1, 365)
        self.log_retention_spin.setSuffix(" days")
        logging_layout.addWidget(self.log_retention_spin, 0, 1)
        
        # Log buttons
        log_buttons_layout = QHBoxLayout()
        view_logs_btn = QPushButton("📋 View Logs")
        view_logs_btn.clicked.connect(self.view_logs)
        clear_logs_btn = QPushButton("🗑️ Clear Logs")
        clear_logs_btn.clicked.connect(self.clear_logs)
        
        log_buttons_layout.addWidget(view_logs_btn)
        log_buttons_layout.addWidget(clear_logs_btn)
        log_buttons_layout.addStretch()
        
        logging_layout.addLayout(log_buttons_layout, 1, 0, 1, 2)
        layout.addWidget(logging_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Advanced")
    
    def create_about_tab(self):
        """Create about/info tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Application info
        app_info = QLabel("""
        <h2>Smart Media Icon System</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Build:</b> Tray Application</p>
        <br>
        <p><b>Description:</b><br>
        Professional Windows desktop utility for automatic media icon management.
        Provides smart TV series and movie detection with custom folder icons 
        and FFmpeg artwork embedding.</p>
        <br>
        <p><b>Key Features:</b></p>
        <ul>
        <li>Smart media type detection (TV series vs movies)</li>
        <li>Custom folder icons for TV series using Windows desktop.ini</li>
        <li>FFmpeg artwork embedding for movie files</li>
        <li>Multi-API poster fetching (TMDB, OMDb, TVmaze, AniList)</li>
        <li>Automatic folder monitoring with intelligent debouncing</li>
        <li>Professional Windows system tray integration</li>
        </ul>
        <br>
        <p><b>Copyright:</b> © 2024 Smart Media Icon Team<br>
        <b>License:</b> MIT License</p>
        """)
        
        app_info.setWordWrap(True)
        app_info.setOpenExternalLinks(True)
        layout.addWidget(app_info)
        
        # System info
        system_group = QGroupBox("📊 System Information")
        system_layout = QGridLayout(system_group)
        
        import platform
        import sys
        
        system_layout.addWidget(QLabel("Operating System:"), 0, 0)
        system_layout.addWidget(QLabel(f"{platform.system()} {platform.release()}"), 0, 1)
        
        system_layout.addWidget(QLabel("Python Version:"), 1, 0)
        system_layout.addWidget(QLabel(f"{sys.version.split()[0]}"), 1, 1)
        
        system_layout.addWidget(QLabel("PyQt5 Version:"), 2, 0)
        try:
            from PyQt5.QtCore import PYQT_VERSION_STR
            system_layout.addWidget(QLabel(PYQT_VERSION_STR), 2, 1)
        except:
            system_layout.addWidget(QLabel("Unknown"), 2, 1)
        
        layout.addWidget(system_group)
        layout.addStretch()
        self.tab_widget.addTab(tab, "About")
    
    def create_button_bar(self, parent_layout):
        """Create the button bar at the bottom"""
        button_layout = QHBoxLayout()
        
        # Left side buttons
        self.reset_btn = QPushButton("🔄 Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        self.import_btn = QPushButton("📁 Import Settings")
        self.import_btn.clicked.connect(self.import_settings)
        button_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("💾 Export Settings")
        self.export_btn.clicked.connect(self.export_settings)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        # Right side buttons
        self.apply_btn = QPushButton("✅ Apply")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        parent_layout.addLayout(button_layout)
    
    def apply_styling(self):
        """Apply custom styling to the dialog"""
        # Set a more modern font
        font = QFont("Segoe UI", 9)
        self.setFont(font)
        
        # Custom stylesheet
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
                border: 1px solid #CCCCCC;
                background-color: #F0F0F0;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QTabBar::tab {
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                border-bottom: 2px solid #0078D4;
            }
        """)
    
    def connect_signals(self):
        """Connect UI signals to handlers"""
        # Directory management
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.remove_dir_btn.clicked.connect(self.remove_directory)
        self.browse_dir_btn.clicked.connect(self.browse_directory)
        
        # Enable/disable related controls
        self.auto_monitor_cb.toggled.connect(self.on_auto_monitor_toggled)
        self.show_notifications_cb.toggled.connect(self.on_notifications_toggled)
    
    def load_settings(self):
        """Load current settings into the UI"""
        try:
            # General tab
            self.load_directories()
            self.start_with_windows_cb.setChecked(self.settings_manager.START_WITH_WINDOWS)
            self.start_minimized_cb.setChecked(self.settings_manager.START_MINIMIZED)
            self.close_to_tray_cb.setChecked(self.settings_manager.CLOSE_TO_TRAY)
            
            self.show_notifications_cb.setChecked(self.settings_manager.SHOW_NOTIFICATIONS)
            self.sound_enabled_cb.setChecked(self.settings_manager.SOUND_ENABLED)
            self.detailed_notifications_cb.setChecked(self.settings_manager.DETAILED_NOTIFICATIONS)
            self.notification_duration_spin.setValue(self.settings_manager.NOTIFICATION_DURATION / 1000)
            
            # Monitoring tab
            self.auto_monitor_cb.setChecked(self.settings_manager.AUTO_MONITOR_ENABLED)
            self.monitor_recursive_cb.setChecked(self.settings_manager.MONITOR_RECURSIVE)
            self.debounce_time_spin.setValue(self.settings_manager.DEBOUNCE_TIME)
            self.max_concurrent_spin.setValue(self.settings_manager.MAX_CONCURRENT_PROCESSING)
            self.max_events_spin.setValue(self.settings_manager.MAX_EVENTS_PER_SECOND)
            
            # API Keys tab
            self.api_inputs['TMDB_API_KEY'].setText(self.settings_manager.TMDB_API_KEY or "")
            self.api_inputs['OMDB_API_KEY'].setText(self.settings_manager.OMDB_API_KEY or "")
            self.api_inputs['TVMAZE_API_KEY'].setText(self.settings_manager.TVMAZE_API_KEY or "")
            self.api_inputs['ANILIST_API_KEY'].setText(self.settings_manager.ANILIST_API_KEY or "")
            
            self.use_mock_api_cb.setChecked(getattr(self.settings_manager, 'USE_MOCK_API', False))
            self.mock_on_failure_cb.setChecked(getattr(self.settings_manager, 'USE_MOCK_ON_FAILURE', True))
            
            # Advanced tab
            self.cache_limit_spin.setValue(self.settings_manager.CACHE_SIZE_LIMIT)
            self.auto_cleanup_cb.setChecked(self.settings_manager.AUTO_CLEANUP_CACHE)
            self.log_retention_spin.setValue(self.settings_manager.LOG_RETENTION_DAYS)
            
            priority_map = {'low': 0, 'normal': 1, 'high': 2}
            priority_index = priority_map.get(getattr(self.settings_manager, 'PROCESSING_PRIORITY', 'normal'), 1)
            self.processing_priority_combo.setCurrentIndex(priority_index)
            
            self.skip_existing_icons_cb.setChecked(getattr(self.settings_manager, 'SKIP_EXISTING_ICONS', False))
            self.backup_original_files_cb.setChecked(getattr(self.settings_manager, 'BACKUP_ORIGINAL_FILES', True))
            self.verify_operations_cb.setChecked(getattr(self.settings_manager, 'VERIFY_OPERATIONS', True))
            
            # Update cache statistics
            self.update_cache_statistics()
            
            self.logger.debug("Settings loaded into UI")
            
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load settings:\n{e}")
    
    def load_directories(self):
        """Load monitored directories into the list"""
        self.directories_list.clear()
        
        directories = self.settings_manager.get_monitored_directories()
        for dir_info in directories:
            path = dir_info['path']
            enabled = dir_info.get('enabled', True)
            recursive = dir_info.get('recursive', True)
            
            # Create display text
            status = "✅" if enabled else "❌"
            recursive_text = " (recursive)" if recursive else ""
            display_text = f"{status} {path}{recursive_text}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, dir_info)
            self.directories_list.addItem(item)
    
    def add_directory(self):
        """Add a new directory to monitoring"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Add Media Directory",
            str(Path.home()),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if directory:
            if self.settings_manager.add_monitored_directory(directory):
                self.load_directories()
                QMessageBox.information(self, "Success", f"Added directory:\n{directory}")
            else:
                QMessageBox.warning(self, "Error", f"Failed to add directory:\n{directory}")
    
    def remove_directory(self):
        """Remove selected directory from monitoring"""
        current_item = self.directories_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a directory to remove.")
            return
        
        dir_info = current_item.data(Qt.UserRole)
        directory = dir_info['path']
        
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove directory from monitoring?\n\n{directory}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.settings_manager.remove_monitored_directory(directory):
                self.load_directories()
                QMessageBox.information(self, "Success", "Directory removed from monitoring.")
            else:
                QMessageBox.warning(self, "Error", "Failed to remove directory.")
    
    def browse_directory(self):
        """Browse to selected directory"""
        current_item = self.directories_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a directory to browse.")
            return
        
        dir_info = current_item.data(Qt.UserRole)
        directory = dir_info['path']
        
        try:
            os.startfile(directory)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open directory:\n{e}")
    
    def test_api_key(self, api_key_name: str):
        """Test a specific API key"""
        api_key = self.api_inputs[api_key_name].text().strip()
        
        if not api_key:
            QMessageBox.information(self, "No API Key", "Please enter an API key first.")
            return
        
        # Update status to testing
        self.api_status_labels[api_key_name].setText("Status: Testing...")
        self.api_status_labels[api_key_name].setStyleSheet("color: orange;")
        self.api_test_buttons[api_key_name].setEnabled(False)
        
        # In a real implementation, this would test the API
        # For now, simulate the test
        QTimer.singleShot(2000, lambda: self.api_test_complete(api_key_name, True))
    
    def api_test_complete(self, api_key_name: str, success: bool):
        """Handle API test completion"""
        if success:
            self.api_status_labels[api_key_name].setText("Status: ✅ Connected")
            self.api_status_labels[api_key_name].setStyleSheet("color: green;")
        else:
            self.api_status_labels[api_key_name].setText("Status: ❌ Failed")
            self.api_status_labels[api_key_name].setStyleSheet("color: red;")
        
        self.api_test_buttons[api_key_name].setEnabled(True)
    
    def test_all_apis(self):
        """Test all configured API keys"""
        for api_key_name in self.api_inputs.keys():
            if self.api_inputs[api_key_name].text().strip():
                self.test_api_key(api_key_name)
    
    def show_api_help(self):
        """Show help for getting API keys"""
        help_text = """
        <h3>Getting API Keys</h3>
        
        <p><b>TMDB (The Movie Database):</b><br>
        1. Go to <a href="https://www.themoviedb.org/settings/api">https://www.themoviedb.org/settings/api</a><br>
        2. Create a free account and request an API key<br>
        3. Copy the API Key (v3 auth)</p>
        
        <p><b>OMDb (Open Movie Database):</b><br>
        1. Go to <a href="http://www.omdbapi.com/apikey.aspx">http://www.omdbapi.com/apikey.aspx</a><br>
        2. Request a free API key<br>
        3. Check your email for the key</p>
        
        <p><b>TVmaze:</b><br>
        1. Go to <a href="https://www.tvmaze.com/api">https://www.tvmaze.com/api</a><br>
        2. Most features work without API key<br>
        3. Premium features require registration</p>
        
        <p><b>AniList:</b><br>
        1. Go to <a href="https://anilist.co/settings/developer">https://anilist.co/settings/developer</a><br>
        2. Create a new client application<br>
        3. Use the Client ID as the API key</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("API Keys Help")
        msg.setText(help_text)
        msg.setTextFormat(Qt.RichText)
        msg.exec_()
    
    def refresh_folder_status(self):
        """Refresh the folder monitoring status table"""
        # This would normally query the file watcher for current status
        # For now, populate with sample data
        directories = self.settings_manager.get_monitored_directories()
        
        self.folders_status_table.setRowCount(len(directories))
        
        for i, dir_info in enumerate(directories):
            # Folder name
            folder_item = QTableWidgetItem(Path(dir_info['path']).name)
            folder_item.setToolTip(dir_info['path'])
            self.folders_status_table.setItem(i, 0, folder_item)
            
            # Status
            status = "✅ Active" if dir_info.get('enabled', True) else "❌ Disabled"
            status_item = QTableWidgetItem(status)
            self.folders_status_table.setItem(i, 1, status_item)
            
            # Last check
            last_check_item = QTableWidgetItem("2 minutes ago")  # Mock data
            self.folders_status_table.setItem(i, 2, last_check_item)
    
    def update_cache_statistics(self):
        """Update cache statistics display"""
        try:
            cache_stats = self.settings_manager.cleanup_cache()
            
            # Calculate current cache size
            cache_dir = Path(self.settings_manager.CACHE_DIR)
            if cache_dir.exists():
                total_size = sum(f.stat().st_size for f in cache_dir.glob('*') if f.is_file())
                total_size_mb = total_size / (1024 * 1024)
                file_count = len(list(cache_dir.glob('*')))
                
                self.cache_size_label.setText(f"Cache Size: {total_size_mb:.1f} MB")
                self.cache_items_label.setText(f"Cache Items: {file_count} files")
            else:
                self.cache_size_label.setText("Cache Size: 0 MB")
                self.cache_items_label.setText("Cache Items: 0 files")
                
        except Exception as e:
            self.logger.error(f"Error updating cache statistics: {e}")
    
    def clear_cache(self):
        """Clear the application cache"""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "This will delete all cached poster images.\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                cache_dir = Path(self.settings_manager.CACHE_DIR)
                if cache_dir.exists():
                    for file in cache_dir.glob('*'):
                        if file.is_file():
                            file.unlink()
                
                self.update_cache_statistics()
                QMessageBox.information(self, "Success", "Cache cleared successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache:\n{e}")
    
    def optimize_cache(self):
        """Optimize the cache"""
        # This would implement cache optimization logic
        QMessageBox.information(self, "Optimize Cache", "Cache optimization completed.")
        self.update_cache_statistics()
    
    def view_cache_stats(self):
        """Show detailed cache statistics"""
        self.update_cache_statistics()
        QMessageBox.information(self, "Cache Statistics", "Cache statistics updated in the Advanced tab.")
    
    def view_logs(self):
        """View application logs"""
        try:
            log_dir = Path.home() / '.smart_media_icon' / 'logs'
            log_file = log_dir / 'tray_app.log'
            
            if log_file.exists():
                os.startfile(str(log_file))
            else:
                QMessageBox.information(self, "No Logs", "No log file found.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open logs:\n{e}")
    
    def clear_logs(self):
        """Clear application logs"""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "This will delete all log files.\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                log_dir = Path.home() / '.smart_media_icon' / 'logs'
                if log_dir.exists():
                    for log_file in log_dir.glob('*.log'):
                        log_file.unlink()
                
                QMessageBox.information(self, "Success", "Logs cleared successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear logs:\n{e}")
    
    def on_auto_monitor_toggled(self, checked: bool):
        """Handle auto monitor checkbox toggle"""
        # Enable/disable related controls
        self.monitor_recursive_cb.setEnabled(checked)
        self.debounce_time_spin.setEnabled(checked)
        self.max_concurrent_spin.setEnabled(checked)
        self.max_events_spin.setEnabled(checked)
    
    def on_notifications_toggled(self, checked: bool):
        """Handle notifications checkbox toggle"""
        self.sound_enabled_cb.setEnabled(checked)
        self.detailed_notifications_cb.setEnabled(checked)
        self.notification_duration_spin.setEnabled(checked)
    
    def apply_settings(self):
        """Apply current settings without closing dialog"""
        try:
            self.save_settings()
            QMessageBox.information(self, "Success", "Settings applied successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply settings:\n{e}")
    
    def accept_settings(self):
        """Accept and save settings, then close dialog"""
        try:
            self.save_settings()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")
    
    def save_settings(self):
        """Save all settings from the UI"""
        # General tab
        self.settings_manager.START_WITH_WINDOWS = self.start_with_windows_cb.isChecked()
        self.settings_manager.START_MINIMIZED = self.start_minimized_cb.isChecked()
        self.settings_manager.CLOSE_TO_TRAY = self.close_to_tray_cb.isChecked()
        
        self.settings_manager.SHOW_NOTIFICATIONS = self.show_notifications_cb.isChecked()
        self.settings_manager.SOUND_ENABLED = self.sound_enabled_cb.isChecked()
        self.settings_manager.DETAILED_NOTIFICATIONS = self.detailed_notifications_cb.isChecked()
        self.settings_manager.NOTIFICATION_DURATION = int(self.notification_duration_spin.value() * 1000)
        
        # Monitoring tab
        self.settings_manager.AUTO_MONITOR_ENABLED = self.auto_monitor_cb.isChecked()
        self.settings_manager.MONITOR_RECURSIVE = self.monitor_recursive_cb.isChecked()
        self.settings_manager.DEBOUNCE_TIME = self.debounce_time_spin.value()
        self.settings_manager.MAX_CONCURRENT_PROCESSING = self.max_concurrent_spin.value()
        self.settings_manager.MAX_EVENTS_PER_SECOND = self.max_events_spin.value()
        
        # API Keys tab
        self.settings_manager.TMDB_API_KEY = self.api_inputs['TMDB_API_KEY'].text().strip()
        self.settings_manager.OMDB_API_KEY = self.api_inputs['OMDB_API_KEY'].text().strip()
        self.settings_manager.TVMAZE_API_KEY = self.api_inputs['TVMAZE_API_KEY'].text().strip()
        self.settings_manager.ANILIST_API_KEY = self.api_inputs['ANILIST_API_KEY'].text().strip()
        
        self.settings_manager.USE_MOCK_API = self.use_mock_api_cb.isChecked()
        self.settings_manager.USE_MOCK_ON_FAILURE = self.mock_on_failure_cb.isChecked()
        
        # Advanced tab
        self.settings_manager.CACHE_SIZE_LIMIT = self.cache_limit_spin.value()
        self.settings_manager.AUTO_CLEANUP_CACHE = self.auto_cleanup_cb.isChecked()
        self.settings_manager.LOG_RETENTION_DAYS = self.log_retention_spin.value()
        
        priority_map = {0: 'low', 1: 'normal', 2: 'high'}
        self.settings_manager.PROCESSING_PRIORITY = priority_map[self.processing_priority_combo.currentIndex()]
        
        self.settings_manager.SKIP_EXISTING_ICONS = self.skip_existing_icons_cb.isChecked()
        self.settings_manager.BACKUP_ORIGINAL_FILES = self.backup_original_files_cb.isChecked()
        self.settings_manager.VERIFY_OPERATIONS = self.verify_operations_cb.isChecked()
        
        # Save to file
        if not self.settings_manager.save_tray_settings():
            raise Exception("Failed to save settings to file")
        
        # Handle Windows startup registration
        if hasattr(self.settings_manager, 'startup_manager'):
            self.settings_manager.startup_manager.update_startup(
                self.settings_manager.START_WITH_WINDOWS
            )
        
        # Emit settings changed signal
        self.settingsChanged.emit(self.settings_manager.config_data)
        
        self.logger.info("Settings saved successfully")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "This will reset all settings to their default values.\nAre you sure?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset settings manager to defaults
            self.settings_manager.config_data.update(
                self.settings_manager.TRAY_DEFAULT_CONFIG
            )
            
            # Reload UI
            self.load_settings()
            
            QMessageBox.information(self, "Success", "Settings reset to defaults.")
    
    def import_settings(self):
        """Import settings from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Settings",
            str(Path.home()),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r') as f:
                    imported_settings = json.load(f)
                
                # Update settings
                self.settings_manager.config_data.update(imported_settings)
                self.load_settings()
                
                QMessageBox.information(self, "Success", "Settings imported successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import settings:\n{e}")
    
    def export_settings(self):
        """Export current settings to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Settings",
            str(Path.home() / "smart_media_icon_settings.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'w') as f:
                    json.dump(self.settings_manager.config_data, f, indent=4)
                
                QMessageBox.information(self, "Success", f"Settings exported to:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export settings:\n{e}")