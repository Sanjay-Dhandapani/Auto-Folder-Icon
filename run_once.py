#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to run the media watcher once and exit
"""

import os
import sys
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import our modules
from media_api import MediaAPI
from win_icon import WinIconSetter
from file_icon import FileIconSetter
from media_watcher import MediaWatcher

def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Convert any environment variables
    for key, value in config.items():
        if isinstance(value, str) and '%' in value:
            config[key] = os.path.expandvars(value)
    
    # Enable file icons
    config['SET_MEDIA_FILE_ICONS'] = True
    config['SET_FOLDER_ICONS'] = True
    
    return type('Config', (object,), config)

def process_directory(media_dir):
    """Process all folders in the media directory"""
    logger.info(f"Processing media directory: {media_dir}")
    
    # Create media watcher
    config = load_config()
    watcher = MediaWatcher(config)
    
    # Scan and process folders
    folders_processed = 0
    files_processed = 0
    
    # Process test folders
    test_folders = ["YourName", "Interstellar", "TheOffice", "TheWitcher", "AttackOnTitan"]
    
    for folder in test_folders:
        folder_path = os.path.join(media_dir, folder)
        if os.path.exists(folder_path):
            logger.info(f"Processing {folder}")
            watcher.process_folder(folder_path)
            folders_processed += 1
            
            # Count media files
            media_files = 0
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if os.path.splitext(file)[1].lower() in ['.mp4', '.mkv', '.avi', '.mov']:
                        media_files += 1
            files_processed += media_files
            
    logger.info(f"Processed {folders_processed} folders and {files_processed} media files")

def main():
    """Main function"""
    config = load_config()
    media_dir = config.MEDIA_ROOT_DIR
    
    # Check if media directory exists
    if not os.path.exists(media_dir):
        logger.error(f"Media directory not found: {media_dir}")
        return False
    
    process_directory(media_dir)
    logger.info("Processing complete!")
    return True

if __name__ == "__main__":
    main()
