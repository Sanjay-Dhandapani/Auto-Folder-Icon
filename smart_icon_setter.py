#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart Icon Setter Module.
Automatically determines whether to set folder icons (for series) or file icons (for movies).
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from win_icon import WinIconSetter
from ffmpeg_icon_setter import FFmpegIconSetter

class SmartIconSetter:
    """
    Intelligently sets icons for media based on content type.
    - For TV series (multiple episodes): Sets folder icon
    - For movies (single file): Sets file icon using FFmpeg
    """
    
    def __init__(self):
        """Initialize the smart icon setter."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize icon setters
        self.folder_icon_setter = WinIconSetter()
        self.file_icon_setter = FFmpegIconSetter()
        
        # Media file extensions
        self.media_extensions = {
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
            '.mpg', '.mpeg', '.m2v', '.3gp', '.3g2', '.f4v', '.asf', '.rm', 
            '.rmvb', '.ts', '.mts', '.m2ts', '.vob', '.ogv', '.divx', '.xvid'
        }
        
        # Ignore files/folders
        self.ignore_patterns = {
            'desktop.ini', 'thumbs.db', '.ds_store', 'folder.ico', 'poster.jpg', 
            'poster.png', 'cover.jpg', 'cover.png', 'fanart.jpg', 'banner.jpg'
        }
    
    def _get_media_files_in_directory(self, directory_path: str) -> List[str]:
        """Get all media files in a directory (non-recursive)."""
        media_files = []
        
        try:
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                
                if os.path.isfile(item_path):
                    if Path(item).suffix.lower() in self.media_extensions:
                        if item.lower() not in self.ignore_patterns:
                            media_files.append(item_path)
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory_path}: {e}")
        
        return media_files
    
    def _has_subdirectories_with_media(self, directory_path: str) -> bool:
        """Check if directory has subdirectories containing media files."""
        try:
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                
                if os.path.isdir(item_path):
                    # Skip common ignore patterns
                    if item.lower() in self.ignore_patterns:
                        continue
                    
                    # Check if this subdirectory has media files
                    media_files = self._get_media_files_in_directory(item_path)
                    if media_files:
                        return True
        except Exception as e:
            self.logger.error(f"Error checking subdirectories in {directory_path}: {e}")
        
        return False
    
    def _find_poster_image(self, directory_path: str) -> Optional[str]:
        """Find a poster image in the directory."""
        poster_names = [
            'poster.jpg', 'poster.png', 'poster.jpeg',
            'cover.jpg', 'cover.png', 'cover.jpeg',
            'folder.jpg', 'folder.png', 'folder.jpeg',
            'fanart.jpg', 'fanart.png', 'fanart.jpeg'
        ]
        
        for poster_name in poster_names:
            poster_path = os.path.join(directory_path, poster_name)
            if os.path.exists(poster_path):
                return poster_path
        
        return None
    
    def determine_media_type(self, directory_path: str) -> str:
        """
        Determine if this is a movie or TV series directory.
        
        Args:
            directory_path (str): Path to the media directory
            
        Returns:
            str: 'movie', 'series', or 'unknown'
        """
        if not os.path.exists(directory_path):
            return 'unknown'
        
        # Get media files in the root directory
        root_media_files = self._get_media_files_in_directory(directory_path)
        
        # Check if there are subdirectories with media
        has_media_subdirs = self._has_subdirectories_with_media(directory_path)
        
        # Decision logic:
        # 1. If there are subdirectories with media files, it's likely a series
        # 2. If there's only one media file in the root and no media subdirs, it's a movie
        # 3. If there are multiple media files in the root, it could be either
        
        if has_media_subdirs:
            self.logger.info(f"Detected as SERIES: {Path(directory_path).name} (has season/episode subdirectories)")
            return 'series'
        elif len(root_media_files) == 1:
            self.logger.info(f"Detected as MOVIE: {Path(directory_path).name} (single media file)")
            return 'movie'
        elif len(root_media_files) > 1:
            # Multiple files in root - could be movie parts or series episodes
            # Check file names for common patterns
            file_names = [Path(f).stem.lower() for f in root_media_files]
            
            # Look for episode patterns
            episode_patterns = ['episode', 'ep', 'e', 's01e', 's1e', 'season']
            has_episode_pattern = any(
                any(pattern in name for pattern in episode_patterns)
                for name in file_names
            )
            
            # Look for part/disc patterns (movies)
            part_patterns = ['part', 'disc', 'cd', 'dvd', 'bd']
            has_part_pattern = any(
                any(pattern in name for pattern in part_patterns)
                for name in file_names
            )
            
            if has_episode_pattern and not has_part_pattern:
                self.logger.info(f"Detected as SERIES: {Path(directory_path).name} (multiple episodes in root)")
                return 'series'
            elif has_part_pattern and not has_episode_pattern:
                self.logger.info(f"Detected as MOVIE: {Path(directory_path).name} (movie parts)")
                return 'movie'
            else:
                # Default to series if uncertain
                self.logger.info(f"Detected as SERIES: {Path(directory_path).name} (multiple files, defaulting to series)")
                return 'series'
        else:
            self.logger.warning(f"No media files found in: {Path(directory_path).name}")
            return 'unknown'
    
    def set_icons_for_media_directory(self, directory_path: str) -> bool:
        """
        Set appropriate icons for a media directory.
        
        Args:
            directory_path (str): Path to the media directory
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(directory_path):
            self.logger.error(f"Directory does not exist: {directory_path}")
            return False
        
        # Find poster image
        poster_path = self._find_poster_image(directory_path)
        if not poster_path:
            self.logger.warning(f"No poster image found in: {Path(directory_path).name}")
            return False
        
        # Determine media type
        media_type = self.determine_media_type(directory_path)
        
        if media_type == 'series':
            return self._set_series_icons(directory_path, poster_path)
        elif media_type == 'movie':
            return self._set_movie_icons(directory_path, poster_path)
        else:
            self.logger.warning(f"Unknown media type for: {Path(directory_path).name}")
            return False
    
    def _set_series_icons(self, directory_path: str, poster_path: str) -> bool:
        """Set folder icon for TV series."""
        self.logger.info(f"Setting FOLDER ICON for series: {Path(directory_path).name}")
        
        try:
            # Extract just the filename from the full poster path
            poster_filename = os.path.basename(poster_path)
            success = self.folder_icon_setter.set_folder_icon(directory_path, poster_filename)
            if success:
                self.logger.info(f"Successfully set folder icon for series: {Path(directory_path).name}")
            else:
                self.logger.error(f"Failed to set folder icon for series: {Path(directory_path).name}")
            return success
        except Exception as e:
            self.logger.error(f"Error setting series folder icon: {e}")
            return False
    
    def _set_movie_icons(self, directory_path: str, poster_path: str) -> bool:
        """Set file icon for movie files."""
        self.logger.info(f"Setting FILE ICON for movie: {Path(directory_path).name}")
        
        # Get all media files in the directory
        media_files = self._get_media_files_in_directory(directory_path)
        
        if not media_files:
            self.logger.error(f"No media files found in movie directory: {Path(directory_path).name}")
            return False
        
        success_count = 0
        total_files = len(media_files)
        
        for media_file in media_files:
            try:
                if self.file_icon_setter.set_movie_file_icon(media_file, poster_path):
                    success_count += 1
                    self.logger.info(f"Set file icon for: {Path(media_file).name}")
                else:
                    self.logger.error(f"Failed to set file icon for: {Path(media_file).name}")
            except Exception as e:
                self.logger.error(f"Error setting file icon for {Path(media_file).name}: {e}")
        
        # Note: For movies, we ONLY set file icons, not folder icons (as per user requirement)
        
        success_rate = success_count / total_files if total_files > 0 else 0
        self.logger.info(f"Movie icon setting: {success_count}/{total_files} files successful ({success_rate:.0%})")
        
        return success_count > 0
    
    def process_media_collection(self, root_directory: str) -> Dict[str, Any]:
        """
        Process an entire media collection directory.
        
        Args:
            root_directory (str): Root directory containing media folders
            
        Returns:
            dict: Processing results summary
        """
        if not os.path.exists(root_directory):
            self.logger.error(f"Root directory does not exist: {root_directory}")
            return {'error': 'Directory not found'}
        
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'series_count': 0,
            'movie_count': 0,
            'unknown_count': 0,
            'details': []
        }
        
        self.logger.info(f"Processing media collection: {Path(root_directory).name}")
        
        try:
            for item in os.listdir(root_directory):
                item_path = os.path.join(root_directory, item)
                
                if os.path.isdir(item_path):
                    # Skip system/hidden directories
                    if item.startswith('.') or item.lower() in self.ignore_patterns:
                        continue
                    
                    results['total_processed'] += 1
                    
                    # Determine media type first for statistics
                    media_type = self.determine_media_type(item_path)
                    if media_type == 'series':
                        results['series_count'] += 1
                    elif media_type == 'movie':
                        results['movie_count'] += 1
                    else:
                        results['unknown_count'] += 1
                    
                    # Process the directory
                    success = self.set_icons_for_media_directory(item_path)
                    
                    if success:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                    
                    results['details'].append({
                        'name': item,
                        'type': media_type,
                        'success': success
                    })
        
        except Exception as e:
            self.logger.error(f"Error processing media collection: {e}")
            results['error'] = str(e)
        
        # Log summary
        self.logger.info(f"Processing complete: {results['successful']}/{results['total_processed']} successful")
        self.logger.info(f"Media types: {results['series_count']} series, {results['movie_count']} movies, {results['unknown_count']} unknown")
        
        return results
