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
        self.recently_processed = {}  # folder_path: last_processed_time
        self.REPROCESS_WINDOW = 5  # seconds
    
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
            now = time.time()
            # Avoid reprocessing the same folder within REPROCESS_WINDOW seconds
            last_time = self.recently_processed.get(str(folder_path), 0)
            if now - last_time < self.REPROCESS_WINDOW:
                logger.info(f'Skipping recently processed folder: "{folder_path}"')
                return
            self.recently_processed[str(folder_path)] = now

            # Skip processing if this is the root directory
            if str(folder_path) == str(self.config.MEDIA_ROOT_DIR):
                return

            # Check if the folder contains media files
            if not self._contains_media_files(folder_path):
                logger.info(f'No media in "{folder_path}" → skipping')
                return

            import re
            is_season_folder = re.search(r'^Season\s*\d+$', folder_path.name, re.IGNORECASE) is not None

            # If this is a season folder, set the parent folder as the target for the icon
            target_folder = folder_path.parent if is_season_folder else folder_path
            # Mark parent as recently processed to avoid duplicate work
            if is_season_folder:
                self.recently_processed[str(target_folder)] = now

            # Check if poster.jpg and desktop.ini already exist and are recent in the target folder
            poster_path = target_folder / "poster.jpg"
            desktop_ini_path = target_folder / "desktop.ini"
            if (poster_path.exists() and desktop_ini_path.exists() and 
                    time.time() - poster_path.stat().st_mtime < 30 * 24 * 60 * 60 and
                    not self.config.FORCE_UPDATE):
                logger.info(f'Poster already exists in "{target_folder}" → skipping')
                return

            # Infer the title from the target folder name
            title = self._infer_title(target_folder)
            if not title:
                logger.info(f'Could not infer title from "{target_folder}" → skipping')
                return

            logger.info(f'Detected folder "{target_folder}"')
            media_count = len(self._get_media_files(folder_path))
            logger.info(f'Found {media_count} media files → searching "{title}"')            # Determine if this is a TV show (has 'Season' in path)
            is_tv_show = any('season' in part.lower() for part in folder_path.parts)
            
            # Determine if this is likely anime based on common terms or patterns
            is_anime = self._is_likely_anime(title, folder_path)
            
            poster_data = self.api.get_poster(title, is_tv_show=is_tv_show, is_anime=is_anime)
            if not poster_data:
                logger.warning(f'No poster found for "{title}" → skipping')
                return
            with open(poster_path, 'wb') as f:
                f.write(poster_data)
            self.icon_setter.set_folder_icon(str(target_folder), "poster.jpg")
            logger.info(f'Downloaded poster.jpg → updated desktop.ini → icon set for "{target_folder}"')
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
            
        # Special case for "StrangerThings" or similar CamelCase (e.g., GameOfThrones)
        if re.match(r'^[A-Z][a-z]+([A-Z][a-z]+)+$', folder_name):
            # Split CamelCase into separate words
            cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', folder_name)
            # Also handle multiple uppercase letters in a row (e.g., "SNLShow")
            cleaned = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', cleaned)
            return cleaned.strip()
        
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
    
    def _is_likely_anime(self, title, folder_path) -> bool:
        """
        Determine if the media is likely anime based on title and folder path.
        
        Args:
            title: The inferred title of the media
            folder_path: The path to the media folder
            
        Returns:
            True if the media is likely anime, False otherwise
        """
        # Convert to lowercase for case-insensitive matching
        title_lower = title.lower()
        path_str = str(folder_path).lower()
        
        # Common anime-related terms
        anime_terms = [
            'anime', 'manga', 'subbed', 'dubbed', 'sub', 'dub',
            'season', 'episode', 'ova', 'special', 'movie',
            'chan', 'kun', 'san', 'sama', 'sensei',
            'otaku', 'weeaboo', 'weeb',
        ]
        
        # Popular anime titles for direct matching
        popular_anime = [
            'attack on titan', 'shingeki no kyojin', 'one piece', 'naruto', 'bleach',
            'my hero academia', 'boku no hero', 'dragon ball', 'sword art online',
            'death note', 'fullmetal alchemist', 'demon slayer', 'kimetsu no yaiba',
            'tokyo ghoul', 'hunter x hunter', 'cowboy bebop', 'one punch man',
            'jojo', 'evangelion', 'pokemon', 'fairy tail', 'code geass', 'steins gate',
            'your name', 'kimi no na wa', 'studio ghibli', 'miyazaki',
            'jujutsu kaisen', 'chainsaw man', 'spy x family', 'mob psycho',
            'attack on titan', 'my hero academia'
        ]
        
        # Check for direct match with popular anime titles
        for anime in popular_anime:
            if anime in title_lower:
                return True
        
        # Check for common anime studios/publishers
        anime_studios = [
            'toei', 'madhouse', 'bones', 'shaft', 'trigger',
            'gainax', 'kyoto animation', 'production i.g', 'a-1 pictures',
            'wit studio', 'ufotable', 'mappa', 'crunchyroll', 'funimation',
        ]
        
        # Common anime name patterns
        anime_patterns = [
            r'[\[\(](BD|720p|1080p)[\]\)]',  # Common anime release format
            r'S\d+E\d+',                     # Season/Episode format
            r'[\[\(](Sub|Dub)[\]\)]',        # Sub/Dub indicator
            r'\d+\s*-\s*\d+',                # Episode range
            r'[\[\(](?:Complete|Batch)[\]\)]',  # Complete or batch collection
        ]
        
        # Check terms
        for term in anime_terms:
            if term in title_lower or term in path_str:
                return True
        
        # Check studios
        for studio in anime_studios:
            if studio in title_lower or studio in path_str:
                return True
        
        # Check patterns
        import re
        for pattern in anime_patterns:
            if re.search(pattern, str(folder_path)):
                return True
        
        # Check for common anime folders/categories
        if 'anime' in path_str or 'japanese' in path_str:
            return True
            
        return False
    
    def scan_and_apply_icons(self, root_dir):
        """
        Scan all subfolders and apply icons immediately (for tray app manual scan).
        """
        logger.info(f"Manual scan and apply icons in: {root_dir}")
        for dirpath, _, filenames in os.walk(root_dir):
            media_files = [f for f in filenames if Path(f).suffix.lower() in MEDIA_EXTENSIONS]
            if media_files:
                self.process_folder(dirpath)
