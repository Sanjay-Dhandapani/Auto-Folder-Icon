#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Media Watcher module.
Monitors a directory for changes and processes media folders.
"""

import os
import time
import logging
from pathlib import Path
from typing import Set, List, Optional
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from media_api import MediaAPI
from win_icon import WinIconSetter

logger = logging.getLogger(__name__)

# List of common media file extensions
MEDIA_EXTENSIONS = {
    # Video
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.3gp',
    # Audio
    '.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma'
}


class MediaEventHandler(FileSystemEventHandler):
    """Handles file system events for the media watcher."""
    
    def __init__(self, media_watcher):
        """Initialize the event handler with a reference to the media watcher."""
        self.media_watcher = media_watcher
        self.pending_folders = set()
        self.process_timer = None
        self.lock = threading.Lock()
    
    def on_created(self, event):
        """Handle file or directory creation events."""
        if not event.is_directory:
            self._handle_file_event(event.src_path)
    
    def on_modified(self, event):
        """Handle file or directory modification events."""
        if not event.is_directory:
            self._handle_file_event(event.src_path)
    
    def on_moved(self, event):
        """Handle file or directory move events."""
        if not event.is_directory:
            self._handle_file_event(event.dest_path)
    
    def _handle_file_event(self, file_path):
        """Handle a file event by scheduling its parent folder for processing."""
        try:
            file_path = Path(file_path)
            
            # Check if the file has a media extension
            if file_path.suffix.lower() in MEDIA_EXTENSIONS:
                folder_path = file_path.parent
                
                with self.lock:
                    self.pending_folders.add(str(folder_path))
                    
                    # Schedule processing after a debounce period
                    if self.process_timer:
                        self.process_timer.cancel()
                    
                    self.process_timer = threading.Timer(
                        self.media_watcher.config.DEBOUNCE_TIME,
                        self._process_pending_folders
                    )
                    self.process_timer.daemon = True
                    self.process_timer.start()
        except Exception as e:
            logger.error(f"Error handling file event: {e}")
    
    def _process_pending_folders(self):
        """Process all pending folders."""
        with self.lock:
            folders = self.pending_folders.copy()
            self.pending_folders.clear()
        
        for folder in folders:
            self.media_watcher.process_folder(folder)


class MediaWatcher:
    """Watches a directory for media files and processes folders containing them."""
    
    def __init__(self, config):
        """Initialize the media watcher with configuration."""
        self.config = config
        self.api = MediaAPI(config)
        self.icon_setter = WinIconSetter()
        self.observer = None
    
    def watch(self, root_dir):
        """Start watching the root directory for changes."""
        self.observer = Observer()
        event_handler = MediaEventHandler(self)
        
        self.observer.schedule(event_handler, root_dir, recursive=True)
        self.observer.start()
        
        logger.info(f"Started watching directory: {root_dir}")
        
        # Perform initial scan of existing directories
        if self.config.SCAN_ON_START:
            self._initial_scan(root_dir)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        
        self.observer.join()
    
    def _initial_scan(self, root_dir):
        """Scan existing directories on startup."""
        logger.info(f"Performing initial scan of: {root_dir}")
        for dirpath, _, filenames in os.walk(root_dir):
            # Check if directory contains media files
            media_files = [f for f in filenames if Path(f).suffix.lower() in MEDIA_EXTENSIONS]
            if media_files:
                self.process_folder(dirpath)
    
    def process_folder(self, folder_path):
        """
        Process a folder that potentially contains media files.
        
        Args:
            folder_path: Path to the folder to process
        """
        try:
            folder_path = Path(folder_path)
            
            # Skip processing if this is the root directory
            if str(folder_path) == str(self.config.MEDIA_ROOT_DIR):
                return
            
            # Check if the folder contains media files
            if not self._contains_media_files(folder_path):
                logger.info(f'No media in "{folder_path}" → skipping')
                return
            
            # Check if poster.jpg and desktop.ini already exist and are recent
            poster_path = folder_path / "poster.jpg"
            desktop_ini_path = folder_path / "desktop.ini"
            
            # If both exist and are recent (within the last 30 days), skip processing
            if (poster_path.exists() and desktop_ini_path.exists() and 
                    time.time() - poster_path.stat().st_mtime < 30 * 24 * 60 * 60 and
                    not self.config.FORCE_UPDATE):
                logger.info(f'Poster already exists in "{folder_path}" → skipping')
                return
            
            # Infer the title from the folder name
            title = self._infer_title(folder_path)
            if not title:
                logger.info(f'Could not infer title from "{folder_path}" → skipping')
                return
            
            logger.info(f'Detected folder "{folder_path}"')
            media_count = len(self._get_media_files(folder_path))
            logger.info(f'Found {media_count} media files → searching "{title}"')
            
            # Get poster image from API
            poster_data = self.api.get_poster(title)
            if not poster_data:
                logger.warning(f'No poster found for "{title}" → skipping')
                return
              # Save the poster image
            with open(poster_path, 'wb') as f:
                f.write(poster_data)
            
            # Set the folder icon
            self.icon_setter.set_folder_icon(str(folder_path), "poster.jpg")
            
            logger.info(f'Downloaded poster.jpg → updated desktop.ini → icon set')
            
        except Exception as e:
            logger.error(f"Error processing folder {folder_path}: {e}")
    
    def _contains_media_files(self, folder_path) -> bool:
        """Check if the folder contains any media files."""
        return len(self._get_media_files(folder_path)) > 0
    
    def _get_media_files(self, folder_path) -> List[Path]:
        """Get a list of media files in the folder."""
        media_files = []
        for file_path in folder_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in MEDIA_EXTENSIONS:
                media_files.append(file_path)
        return media_files
    
    def _infer_title(self, folder_path) -> Optional[str]:
        """
        Infer the media title from the folder name.
        
        This method tries to clean up the folder name to extract a searchable title.
        It removes common patterns like season indicators, quality markers, etc.
        """
        import re
        
        # Get the folder name
        folder_name = folder_path.name
        
        # Check if this is a Season folder
        is_season_folder = re.search(r'^Season\s*\d+$', folder_name, re.IGNORECASE) is not None
        
        # If this is a season folder, use the parent folder name instead
        if is_season_folder:
            parent_folder = folder_path.parent
            if parent_folder.name.lower() not in ["media", "test_media"]:
                return self._infer_title(parent_folder)
            
        # Special case for "StrangerThings" format (camel case)
        if re.match(r'^[A-Z][a-z]+[A-Z][a-z]+$', folder_name):
            # Split CamelCase into separate words
            return re.sub(r'([a-z])([A-Z])', r'\1 \2', folder_name)
        
        # Remove common patterns that aren't part of the title
        patterns = [
            r'\bS\d{1,2}E\d{1,2}\b',          # S01E01 format
            r'\b\d{1,2}x\d{1,2}\b',            # 1x01 format
            r'\b(720p|1080p|2160p|4K|UHD)\b',  # Quality indicators
            r'\b(HDTV|BluRay|WEB-DL|WEBRip)\b', # Source indicators
            r'\b(x264|x265|HEVC|AVC)\b',       # Codec indicators
            r'\bSeason\s\d+\b',                # "Season X" text
            r'\[.*?\]',                        # Anything in square brackets
            r'\(.*?\)',                        # Anything in parentheses
            r'\.\w+$'                          # File extension
        ]
        
        cleaned_name = folder_name
        for pattern in patterns:
            cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
        
        # Replace dots, underscores, and excessive spaces with a single space
        cleaned_name = re.sub(r'[._]+', ' ', cleaned_name)
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
        
        return cleaned_name.strip()
