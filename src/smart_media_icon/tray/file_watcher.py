#!/usr/bin/env python3
"""
Smart Media Icon File Watcher

Provides intelligent file system monitoring with debouncing and filtering
for the tray application. Integrates with the existing watchdog dependency.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Set, Optional, List, Any
from collections import defaultdict, deque

from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class FileWatcher(QObject):
    """
    Main file watching component that monitors directories for media file changes
    """
    
    # Signals
    fileEvent = pyqtSignal(str, str)  # path, event_type
    monitoringStarted = pyqtSignal(str)  # directory
    monitoringStopped = pyqtSignal(str)  # directory
    processingQueued = pyqtSignal(str, int)  # directory, priority
    
    def __init__(self, settings_manager, processing_engine):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Store component references
        self.settings_manager = settings_manager
        self.processing_engine = processing_engine
        
        # Watchdog components
        self.observer = Observer()
        self.event_handler = MediaEventHandler(self)
        
        # Debounce management
        self.debounce_manager = DebounceManager(
            self.settings_manager.DEBOUNCE_TIME,
            self.settings_manager.MAX_EVENTS_PER_SECOND
        )
        
        # Monitoring state
        self.monitored_paths = {}  # path -> watch handle
        self.is_monitoring = False
        
        # Media file extensions (from existing SmartIconSetter)
        self.media_extensions = {
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
            '.mpg', '.mpeg', '.m2v', '.3gp', '.ts', '.mts', '.vob'
        }
        
        # Ignore patterns (from existing SmartIconSetter)
        self.ignore_patterns = {
            'desktop.ini', 'thumbs.db', '.ds_store', 'folder.ico', 'poster.jpg', 
            'poster.png', 'cover.jpg', 'cover.png', 'fanart.jpg', 'banner.jpg',
            # Additional patterns for file watching
            '*.tmp', '*.part', '*.crdownload', '*.download', '*.!ut'
        }
        
        # Connect debounce manager
        self.debounce_manager.processingRequested.connect(self.queue_for_processing)
        
        self.logger.info("📁 File watcher initialized")
    
    def start_monitoring(self) -> bool:
        """Start file system monitoring"""
        try:
            if self.is_monitoring:
                self.logger.warning("File monitoring is already active")
                return True
            
            self.logger.info("👁️ Starting file system monitoring...")
            
            # Get monitored directories from settings
            monitored_dirs = self.settings_manager.get_monitored_directories()
            
            if not monitored_dirs:
                self.logger.warning("No directories configured for monitoring")
                return False
            
            # Add directories to watchdog observer
            for dir_config in monitored_dirs:
                if not dir_config.get('enabled', True):
                    continue
                
                directory = dir_config['path']
                recursive = dir_config.get('recursive', True)
                
                if self.add_directory(directory, recursive):
                    self.logger.info(f"📂 Monitoring: {directory} (recursive: {recursive})")
                else:
                    self.logger.error(f"❌ Failed to monitor: {directory}")
            
            # Start the observer
            if self.monitored_paths:
                self.observer.start()
                self.is_monitoring = True
                self.logger.info(f"✅ File monitoring started for {len(self.monitored_paths)} directories")
                return True
            else:
                self.logger.error("No valid directories to monitor")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop file system monitoring"""
        try:
            if not self.is_monitoring:
                return
            
            self.logger.info("🛑 Stopping file system monitoring...")
            
            # Stop the observer
            self.observer.stop()
            self.observer.join(timeout=5.0)
            
            # Clear monitored paths
            self.monitored_paths.clear()
            
            self.is_monitoring = False
            self.logger.info("✅ File monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {e}")
    
    def add_directory(self, directory: str, recursive: bool = True) -> bool:
        """
        Add a directory to monitoring
        
        Args:
            directory: Directory path to monitor
            recursive: Whether to monitor subdirectories
            
        Returns:
            bool: True if added successfully
        """
        try:
            directory = os.path.abspath(directory)
            
            if not os.path.exists(directory):
                self.logger.error(f"Directory does not exist: {directory}")
                return False
            
            if not os.path.isdir(directory):
                self.logger.error(f"Path is not a directory: {directory}")
                return False
            
            # Check if already monitoring
            if directory in self.monitored_paths:
                self.logger.warning(f"Directory already being monitored: {directory}")
                return True
            
            # Add to watchdog observer
            watch = self.observer.schedule(
                self.event_handler,
                directory,
                recursive=recursive
            )
            
            self.monitored_paths[directory] = watch
            self.monitoringStarted.emit(directory)
            
            self.logger.info(f"📁 Added directory to monitoring: {directory}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add directory {directory}: {e}")
            return False
    
    def remove_directory(self, directory: str) -> bool:
        """
        Remove a directory from monitoring
        
        Args:
            directory: Directory path to remove
            
        Returns:
            bool: True if removed successfully
        """
        try:
            directory = os.path.abspath(directory)
            
            if directory not in self.monitored_paths:
                self.logger.warning(f"Directory not being monitored: {directory}")
                return False
            
            # Remove from watchdog observer
            watch = self.monitored_paths[directory]
            self.observer.unschedule(watch)
            
            # Remove from our tracking
            del self.monitored_paths[directory]
            self.monitoringStopped.emit(directory)
            
            self.logger.info(f"📁 Removed directory from monitoring: {directory}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove directory {directory}: {e}")
            return False
    
    def refresh_monitoring(self):
        """Refresh monitoring based on current settings"""
        try:
            # Stop current monitoring
            if self.is_monitoring:
                self.stop_monitoring()
            
            # Start monitoring with current settings
            if self.settings_manager.AUTO_MONITOR_ENABLED:
                self.start_monitoring()
                
        except Exception as e:
            self.logger.error(f"Failed to refresh monitoring: {e}")
    
    def queue_for_processing(self, directory: str, priority: int = 1):
        """Queue a directory for processing"""
        try:
            self.logger.debug(f"Queueing for processing: {directory} (priority: {priority})")
            
            # Emit signal for processing engine
            self.processingQueued.emit(directory, priority)
            
            # Queue in processing engine
            if hasattr(self.processing_engine, 'queue_directory_for_processing'):
                self.processing_engine.queue_directory_for_processing(directory, priority)
            
        except Exception as e:
            self.logger.error(f"Failed to queue directory for processing: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'is_monitoring': self.is_monitoring,
            'monitored_directories': list(self.monitored_paths.keys()),
            'observer_running': self.observer.is_alive() if hasattr(self.observer, 'is_alive') else False,
            'debounce_time': self.debounce_manager.debounce_time,
            'pending_events': self.debounce_manager.get_pending_count()
        }


class MediaEventHandler(FileSystemEventHandler):
    """
    File system event handler that filters and processes media-related events
    """
    
    def __init__(self, file_watcher):
        super().__init__()
        
        self.file_watcher = file_watcher
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_event_time = 0
        self.event_count = 0
        self.rate_limit_window = 1.0  # 1 second
        
    def on_created(self, event: FileSystemEvent):
        """Handle file/directory creation events"""
        if self._should_process_event(event):
            self.logger.debug(f"File created: {event.src_path}")
            self._schedule_processing(event.src_path, "created", priority=2)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file/directory modification events"""
        if self._should_process_event(event):
            # Lower priority for modifications
            self.logger.debug(f"File modified: {event.src_path}")
            self._schedule_processing(event.src_path, "modified", priority=3)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file/directory move events"""
        if self._should_process_event(event):
            self.logger.debug(f"File moved: {event.src_path} -> {event.dest_path}")
            # Process both source and destination
            self._schedule_processing(event.dest_path, "moved", priority=2)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file/directory deletion events"""
        # We don't typically process deletions for icon setting
        pass
    
    def _should_process_event(self, event: FileSystemEvent) -> bool:
        """
        Determine if an event should be processed
        
        Args:
            event: File system event
            
        Returns:
            bool: True if event should be processed
        """
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                return False
            
            path = Path(event.src_path)
            
            # Skip if path doesn't exist (for some events)
            if not path.exists():
                return False
            
            # Check ignore patterns
            if self._matches_ignore_pattern(path.name):
                return False
            
            # For files, check if it's a media file
            if path.is_file():
                if path.suffix.lower() not in self.file_watcher.media_extensions:
                    return False
            
            # For directories, check if it might contain media
            elif path.is_dir():
                # Quick check for obvious non-media directories
                if path.name.startswith('.'):
                    return False
                
                # Check if directory contains media files (limited scan)
                if not self._directory_has_media_potential(path):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Error checking event: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.last_event_time > self.rate_limit_window:
            self.event_count = 0
            self.last_event_time = current_time
        
        # Check rate limit
        max_events = self.file_watcher.settings_manager.MAX_EVENTS_PER_SECOND
        if self.event_count >= max_events:
            return False
        
        self.event_count += 1
        return True
    
    def _matches_ignore_pattern(self, filename: str) -> bool:
        """Check if filename matches ignore patterns"""
        filename_lower = filename.lower()
        
        for pattern in self.file_watcher.ignore_patterns:
            if pattern.startswith('*'):
                # Wildcard pattern
                if filename_lower.endswith(pattern[1:]):
                    return True
            else:
                # Exact match
                if filename_lower == pattern:
                    return True
        
        return False
    
    def _directory_has_media_potential(self, directory: Path) -> bool:
        """
        Quick check if directory might contain media files
        
        Args:
            directory: Directory path to check
            
        Returns:
            bool: True if directory might contain media
        """
        try:
            # Limit scan to avoid performance issues
            file_count = 0
            max_scan = 20
            
            for item in directory.iterdir():
                if file_count >= max_scan:
                    break
                
                if item.is_file():
                    if item.suffix.lower() in self.file_watcher.media_extensions:
                        return True
                elif item.is_dir():
                    # Check for season/episode patterns
                    dir_name = item.name.lower()
                    if any(keyword in dir_name for keyword in ['season', 'episode', 'ep', 's01', 's1']):
                        return True
                
                file_count += 1
            
            return False
            
        except (PermissionError, OSError):
            return False
    
    def _schedule_processing(self, path: str, event_type: str, priority: int = 1):
        """Schedule path for processing"""
        try:
            # Determine the directory to process
            path_obj = Path(path)
            
            if path_obj.is_file():
                # For files, process the parent directory
                process_dir = str(path_obj.parent)
            else:
                # For directories, process the directory itself
                process_dir = str(path_obj)
            
            # Emit file event signal
            self.file_watcher.fileEvent.emit(path, event_type)
            
            # Schedule for debounced processing
            self.file_watcher.debounce_manager.schedule_processing(process_dir, priority)
            
        except Exception as e:
            self.logger.error(f"Failed to schedule processing for {path}: {e}")


class DebounceManager(QObject):
    """
    Manages debouncing of file system events to prevent excessive processing
    """
    
    # Signals
    processingRequested = pyqtSignal(str, int)  # directory, priority
    
    def __init__(self, debounce_time: float = 5.0, max_events_per_second: int = 10):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.debounce_time = debounce_time
        self.max_events_per_second = max_events_per_second
        
        # Event tracking
        self.pending_events = defaultdict(dict)  # directory -> {last_update, priority, timer}
        self.recent_events = deque(maxlen=100)  # Recent event timestamps
        
        self.logger.debug(f"Debounce manager initialized (time: {debounce_time}s)")
    
    def schedule_processing(self, directory: str, priority: int = 1):
        """
        Schedule a directory for processing with debouncing
        
        Args:
            directory: Directory path to process
            priority: Processing priority (lower = higher priority)
        """
        try:
            directory = os.path.abspath(directory)
            current_time = time.time()
            
            # Add to recent events for rate limiting
            self.recent_events.append(current_time)
            
            # Check rate limiting
            if self._is_rate_limited():
                self.logger.debug(f"Rate limited, skipping: {directory}")
                return
            
            # Update or create pending event
            if directory in self.pending_events:
                # Update existing event
                event_info = self.pending_events[directory]
                
                # Cancel existing timer
                if 'timer' in event_info and event_info['timer']:
                    event_info['timer'].stop()
                
                # Update priority (use higher priority)
                event_info['priority'] = min(event_info.get('priority', priority), priority)
            else:
                # Create new event
                event_info = {'priority': priority}
                self.pending_events[directory] = event_info
            
            # Update timestamp
            event_info['last_update'] = current_time
            
            # Create new timer
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._process_event(directory))
            timer.start(int(self.debounce_time * 1000))  # Convert to milliseconds
            
            event_info['timer'] = timer
            
            self.logger.debug(f"Scheduled processing: {directory} (priority: {priority})")
            
        except Exception as e:
            self.logger.error(f"Failed to schedule processing: {e}")
    
    def _process_event(self, directory: str):
        """Process a debounced event"""
        try:
            if directory not in self.pending_events:
                return
            
            event_info = self.pending_events[directory]
            priority = event_info.get('priority', 1)
            
            # Remove from pending events
            del self.pending_events[directory]
            
            # Emit processing request
            self.processingRequested.emit(directory, priority)
            
            self.logger.debug(f"Processing triggered: {directory}")
            
        except Exception as e:
            self.logger.error(f"Failed to process event for {directory}: {e}")
    
    def _is_rate_limited(self) -> bool:
        """Check if we're currently rate limited"""
        current_time = time.time()
        
        # Count events in the last second
        recent_count = sum(1 for t in self.recent_events if current_time - t <= 1.0)
        
        return recent_count > self.max_events_per_second
    
    def get_pending_count(self) -> int:
        """Get number of pending events"""
        return len(self.pending_events)
    
    def clear_pending(self):
        """Clear all pending events"""
        for event_info in self.pending_events.values():
            if 'timer' in event_info and event_info['timer']:
                event_info['timer'].stop()
        
        self.pending_events.clear()
        self.logger.debug("Cleared all pending events")
    
    def update_debounce_time(self, new_time: float):
        """Update debounce time"""
        self.debounce_time = new_time
        self.logger.debug(f"Updated debounce time to {new_time}s")
    
    def get_status(self) -> Dict[str, Any]:
        """Get debounce manager status"""
        return {
            'debounce_time': self.debounce_time,
            'pending_count': len(self.pending_events),
            'recent_events': len(self.recent_events),
            'rate_limited': self._is_rate_limited()
        }