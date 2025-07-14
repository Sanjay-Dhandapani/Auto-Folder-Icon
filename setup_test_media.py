#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to recreate test media directories with sample media files
"""

import os
import shutil
import logging
import json
import sys
import requests
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Test media information
TEST_MEDIA = [
    {
        "name": "AttackOnTitan",
        "type": "anime",
        "seasons": 1,
        "episodes_per_season": 3,
    },
    {
        "name": "FullmetalAlchemist[BD][1080p]",
        "type": "anime",
        "seasons": 1,
        "episodes_per_season": 3,
    },
    {
        "name": "Interstellar",
        "type": "movie",
        "file": "Interstellar.mp4",
    },
    {
        "name": "KimetsuNoYaiba",
        "type": "anime",
        "seasons": 1,
        "episodes_per_season": 3,
    },
    {
        "name": "MyHeroAcademia",
        "type": "anime",
        "seasons": 1,
        "episodes_per_season": 3,
    },
    {
        "name": "TheOffice",
        "type": "tv",
        "seasons": 1,
        "episodes_per_season": 3,
    },
    {
        "name": "TheWitcher",
        "type": "tv",
        "seasons": 1,
        "episodes_per_season": 3,
    },
    {
        "name": "UnusualShowName2025",
        "type": "tv",
        "seasons": 1,
        "episodes_per_season": 3,
    },
    {
        "name": "YourName",
        "type": "anime_movie",
        "file": "YourName.mp4",
    },
    {
        "name": "BreakingBad",  # Adding Breaking Bad as a new test case
        "type": "tv",
        "seasons": 2,
        "episodes_per_season": 3,
    }
]

def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Convert any environment variables
    for key, value in config.items():
        if isinstance(value, str) and '%' in value:
            config[key] = os.path.expandvars(value)
    
    return config

def create_media_file(file_path):
    """Create a sample media file"""
    with open(file_path, 'wb') as f:
        # Write a minimal valid MP4 file header (8 bytes)
        f.write(b"\x00\x00\x00\x18\x66\x74\x79\x70")
        # Add some padding to make it look like a real file
        f.write(b"\x00" * 1024)
    
    logging.info(f"Created media file: {file_path}")

def download_sample_poster(media_name, output_path):
    """Download a sample poster image for the media"""
    try:
        # Use a placeholder image service
        url = f"https://via.placeholder.com/600x900.jpg?text={media_name}"
        response = requests.get(url, stream=True, timeout=10)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            logging.info(f"Downloaded poster for {media_name}")
            return True
        else:
            logging.error(f"Failed to download poster for {media_name}: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error downloading poster for {media_name}: {e}")
        return False

def create_dummy_poster(media_name, output_path):
    """Create a simple colored rectangle as a poster if download fails"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a blank image
        img = Image.new('RGB', (600, 900), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        
        # Try to use a system font
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Draw the title
        d.text((300, 450), media_name, fill=(255, 255, 255), font=font, anchor="mm")
        
        # Save the image
        img.save(output_path)
        logging.info(f"Created dummy poster for {media_name}")
        return True
    except Exception as e:
        logging.error(f"Error creating dummy poster for {media_name}: {e}")
        return False

def setup_media_directory(media_dir, media_info):
    """Set up a test media directory with sample files"""
    name = media_info["name"]
    media_type = media_info["type"]
    
    # Create the main directory
    media_path = os.path.join(media_dir, name)
    if not os.path.exists(media_path):
        os.makedirs(media_path)
    
    # Add poster image
    poster_path = os.path.join(media_path, "poster.jpg")
    if not download_sample_poster(name, poster_path):
        # If download fails, create a dummy poster
        create_dummy_poster(name, poster_path)
    
    if media_type in ["tv", "anime"]:
        # Create season directories with episodes
        for season in range(1, media_info["seasons"] + 1):
            season_dir = os.path.join(media_path, f"Season{season}")
            if not os.path.exists(season_dir):
                os.makedirs(season_dir)
            
            # Create episode files
            for episode in range(1, media_info["episodes_per_season"] + 1):
                episode_file = os.path.join(season_dir, f"S{season:02d}E{episode:02d}.mp4")
                create_media_file(episode_file)
        
    elif media_type in ["movie", "anime_movie"]:
        # Create a single movie file
        movie_file = os.path.join(media_path, media_info.get("file", f"{name}.mp4"))
        create_media_file(movie_file)
    
    logging.info(f"Set up test media directory for {name}")

def clean_and_setup_test_media():
    """Clean up old test media and set up fresh test directories"""
    config = load_config()
    media_dir = config["MEDIA_ROOT_DIR"]
    
    # Create media directory if it doesn't exist
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
    
    # Delete all existing content
    logging.info(f"Cleaning up existing test media in {media_dir}")
    for item in os.listdir(media_dir):
        item_path = os.path.join(media_dir, item)
        try:
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                # Handle read-only files and system files
                for root, dirs, files in os.walk(item_path, topdown=False):
                    for name in files:
                        file_path = os.path.join(root, name)
                        try:
                            os.chmod(file_path, 0o777)
                            os.unlink(file_path)
                        except Exception as e:
                            logging.warning(f"Could not delete file {file_path}: {e}")
                    for name in dirs:
                        dir_path = os.path.join(root, name)
                        try:
                            os.chmod(dir_path, 0o777)
                            os.rmdir(dir_path)
                        except Exception as e:
                            logging.warning(f"Could not delete directory {dir_path}: {e}")
                
                # Delete the main directory
                try:
                    os.chmod(item_path, 0o777)
                    os.rmdir(item_path)
                except Exception as e:
                    logging.warning(f"Could not delete directory {item_path}: {e}")
        except Exception as e:
            logging.error(f"Error deleting {item_path}: {e}")
    
    # Set up fresh test media directories
    logging.info("Setting up fresh test media directories")
    for media_info in TEST_MEDIA:
        setup_media_directory(media_dir, media_info)
    
    logging.info("Test media setup complete!")

if __name__ == "__main__":
    clean_and_setup_test_media()
