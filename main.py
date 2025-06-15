#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Media Iconer application.
Starts the media watcher service and ensures only one instance is running.
"""

import os
import sys
import time
import logging
import argparse
from pathlib import Path
import tempfile
import atexit

# Local imports
from config import Config
from media_watcher import MediaWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M'
)
logger = logging.getLogger(__name__)

def create_lock_file():
    """Create a lock file to ensure only one instance runs at a time."""
    lock_file = Path(tempfile.gettempdir()) / 'media_iconer.lock'
    
    # Check if the lock file exists and is recent
    if lock_file.exists():
        # Check if the lock file is stale (more than 10 seconds old)
        if time.time() - lock_file.stat().st_mtime < 10:
            logger.error("Another instance of Media Iconer is already running.")
            sys.exit(1)
    
    # Create or update the lock file
    with open(lock_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Register a function to remove the lock file when the application exits
    def remove_lock_file():
        try:
            if lock_file.exists():
                lock_file.unlink()
        except Exception as e:
            logger.error(f"Failed to remove lock file: {e}")
    
    atexit.register(remove_lock_file)
    
    # Update the lock file periodically to prevent it from becoming stale
    def update_lock_file():
        try:
            if lock_file.exists():
                lock_file.touch()
        except Exception as e:
            logger.error(f"Failed to update lock file: {e}")
    
    # Update the lock file every 5 seconds
    import threading
    def lock_file_updater():
        while True:
            update_lock_file()
            time.sleep(5)
    
    threading.Thread(target=lock_file_updater, daemon=True).start()


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Media Iconer - Set folder icons for media content')
    parser.add_argument('--config', type=str, help='Path to config file')
    args = parser.parse_args()
    
    # Ensure only one instance is running
    create_lock_file()
    
    # Load configuration
    config = Config(config_file=args.config)
    
    # Validate the media directory
    media_dir = Path(config.MEDIA_ROOT_DIR)
    if not media_dir.exists() or not media_dir.is_dir():
        logger.error(f"Media directory does not exist: {media_dir}")
        sys.exit(1)
    
    logger.info(f'Watching "{media_dir}"')
    
    # Create and start the media watcher
    watcher = MediaWatcher(config)
    
    try:
        # Start watching the media directory
        watcher.watch(str(media_dir))
    except KeyboardInterrupt:
        logger.info("Stopping Media Iconer...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
