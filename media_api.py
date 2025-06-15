#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Media API module.
Handles communication with external APIs to fetch media metadata and posters.
"""

import logging
import time
from typing import Optional, Dict, Any, Union, Tuple
import json
import os
from pathlib import Path

import requests
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class MediaAPI:
    """Handles interactions with media metadata APIs like TMDB and OMDB."""
    
    def __init__(self, config):
        """Initialize the API client with configuration."""
        self.config = config
        self.cache_dir = Path(self.config.CACHE_DIR)
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache for API responses to reduce API calls
        self.response_cache = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load the cache from disk."""
        cache_file = self.cache_dir / "api_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.response_cache = json.load(f)
                logger.info(f"Loaded {len(self.response_cache)} cached API responses")
            except Exception as e:
                logger.error(f"Error loading API cache: {e}")
                self.response_cache = {}
    
    def _save_cache(self):
        """Save the cache to disk."""
        cache_file = self.cache_dir / "api_cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.response_cache, f)
        except Exception as e:
            logger.error(f"Error saving API cache: {e}")
    
    def _get_tvmaze_poster(self, title: str) -> Optional[bytes]:
        """
        Get a poster from TVmaze for TV shows.
        
        Args:
            title: The title to search for
            
        Returns:
            Bytes of the poster image, or None if no poster was found
        """
        try:
            search_url = f"https://api.tvmaze.com/singlesearch/shows"
            params = {"q": title}
            headers = {}
            if hasattr(self.config, 'TVMAZE_API_KEY') and self.config.TVMAZE_API_KEY:
                headers["Authorization"] = f"Bearer {self.config.TVMAZE_API_KEY}"
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"TVmaze search failed: {response.status_code} - {response.text}")
                return None
            result = response.json()
            image_url = result.get("image", {}).get("original") or result.get("image", {}).get("medium")
            if not image_url:
                logger.info(f"No TVmaze poster found for: {title}")
                return None
            poster_response = requests.get(image_url, timeout=10)
            if poster_response.status_code != 200:
                logger.error(f"TVmaze poster download failed: {poster_response.status_code}")
                return None
            return self._process_poster_image(poster_response.content)
        except Exception as e:
            logger.error(f"Error getting TVmaze poster: {e}")
            return None

    def get_poster(self, title: str, is_tv_show: bool = False, is_anime: bool = False) -> Optional[bytes]:
        """
        Get a poster image for the given title.
        
        Args:
            title: The title to search for
            is_tv_show: If True, prefer TV show APIs (TVmaze)
            is_anime: If True, prefer anime APIs (AniList)
            
        Returns:
            Bytes of the poster image, or None if no poster was found
        """
        # Check if we should use mock API for demo/testing purposes
        if hasattr(self.config, 'USE_MOCK_API') and self.config.USE_MOCK_API:
            return self._get_mock_poster(title)
        
        # Check cache first
        cache_type = 'anime' if is_anime else ('tv' if is_tv_show else 'movie')
        cache_key = f"poster_{title}_{cache_type}"
        if cache_key in self.response_cache and self.config.USE_CACHE:
            poster_path = self.cache_dir / f"{cache_key}.jpg"
            if poster_path.exists():
                try:
                    with open(poster_path, 'rb') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Error reading cached poster: {e}")
        
        # Try AniList first for anime
        if is_anime:
            poster_data = self._get_anilist_poster(title)
            if poster_data:
                self._cache_poster(cache_key, poster_data)
                return poster_data
        
        # TV shows: try TVmaze first
        if is_tv_show:
            poster_data = self._get_tvmaze_poster(title)
            if poster_data:
                self._cache_poster(cache_key, poster_data)
                return poster_data
        
        # Try TMDB for all types
        if hasattr(self.config, 'TMDB_API_KEY') and self.config.TMDB_API_KEY:
            poster_data = self._get_tmdb_poster(title)
            if poster_data:
                self._cache_poster(cache_key, poster_data)
                return poster_data
        
        # Try OMDB for all types
        if hasattr(self.config, 'OMDB_API_KEY') and self.config.OMDB_API_KEY:
            poster_data = self._get_omdb_poster(title)
            if poster_data:
                self._cache_poster(cache_key, poster_data)
                return poster_data
        
        # If nothing found and it's not already tried as anime, try AniList as fallback
        if not is_anime:
            poster_data = self._get_anilist_poster(title)
            if poster_data:
                self._cache_poster(cache_key, poster_data)
                return poster_data
        
        return None
    
    def _cache_poster(self, cache_key: str, poster_data: bytes):
        """Cache the poster image."""
        try:
            # Save the poster to the cache directory
            poster_path = self.cache_dir / f"{cache_key}.jpg"
            with open(poster_path, 'wb') as f:
                f.write(poster_data)
            
            # Update the response cache
            self.response_cache[cache_key] = str(poster_path)
            self._save_cache()
        except Exception as e:
            logger.error(f"Error caching poster: {e}")
    
    def _get_tmdb_poster(self, title: str) -> Optional[bytes]:
        """
        Get a poster from The Movie Database (TMDB).
        
        Args:
            title: The title to search for
            
        Returns:
            Bytes of the poster image, or None if no poster was found
        """
        try:
            # First, search for the title
            search_url = "https://api.themoviedb.org/3/search/multi"
            params = {
                "api_key": self.config.TMDB_API_KEY,
                "query": title,
                "include_adult": "false"
            }
            
            response = requests.get(search_url, params=params)
            if response.status_code != 200:
                logger.error(f"TMDB search failed: {response.status_code} - {response.text}")
                return None
            
            results = response.json().get("results", [])
            if not results:
                logger.info(f"No TMDB results found for: {title}")
                return None
            
            # Get the first result with a poster path
            result = next((r for r in results if r.get("poster_path")), None)
            if not result:
                logger.info(f"No TMDB poster found for: {title}")
                return None
            
            # Get the poster image
            poster_path = result.get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/original{poster_path}"
            
            poster_response = requests.get(poster_url)
            if poster_response.status_code != 200:
                logger.error(f"TMDB poster download failed: {poster_response.status_code}")
                return None
            
            # Resize and optimize the poster
            return self._process_poster_image(poster_response.content)
            
        except Exception as e:
            logger.error(f"Error getting TMDB poster: {e}")
            return None
    
    def _get_omdb_poster(self, title: str) -> Optional[bytes]:
        """
        Get a poster from the Open Movie Database (OMDB).
        
        Args:
            title: The title to search for
            
        Returns:
            Bytes of the poster image, or None if no poster was found
        """
        try:
            # Search for the title
            url = "http://www.omdbapi.com/"
            params = {
                "apikey": self.config.OMDB_API_KEY,
                "t": title,
                "r": "json"
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                logger.error(f"OMDB search failed: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            if result.get("Response") != "True" or not result.get("Poster"):
                logger.info(f"No OMDB poster found for: {title}")
                return None
            
            # Get the poster image
            poster_url = result.get("Poster")
            poster_response = requests.get(poster_url)
            if poster_response.status_code != 200:
                logger.error(f"OMDB poster download failed: {poster_response.status_code}")
                return None
            
            # Resize and optimize the poster
            return self._process_poster_image(poster_response.content)
            
        except Exception as e:
            logger.error(f"Error getting OMDB poster: {e}")
            return None
    
    def _get_anilist_poster(self, title: str) -> Optional[bytes]:
        """
        Get a poster from AniList API (good for anime series and movies).
        
        Args:
            title: The title to search for
            
        Returns:
            Bytes of the poster image, or None if no poster was found
        """
        try:
            # AniList uses GraphQL API
            url = 'https://graphql.anilist.co'
            query = '''
            query ($search: String) {
                Media (search: $search, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    coverImage {
                        large
                        medium
                        extraLarge
                    }
                }
            }
            '''
            variables = {'search': title}
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            
            # Note: AniList doesn't require API keys for basic public queries
            # We'll log some debugging info
            logger.debug(f"Searching AniList for anime: {title}")
            
            response = requests.post(
                url, 
                json={'query': query, 'variables': variables},
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"AniList search failed: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            media = data.get('data', {}).get('Media')
            
            if not media or not media.get('coverImage'):
                logger.info(f"No AniList result found for: {title}")
                return None
            
            # Get the poster image URL - try extraLarge first, then large, then medium
            image_url = (media['coverImage'].get('extraLarge') or 
                         media['coverImage'].get('large') or 
                         media['coverImage'].get('medium'))
            
            if not image_url:
                logger.info(f"No AniList poster found for: {title}")
                return None
            
            logger.info(f"Found AniList poster for: {title}")
            poster_response = requests.get(image_url, timeout=10)
            if poster_response.status_code != 200:
                logger.error(f"AniList poster download failed: {poster_response.status_code}")
                return None
            
            return self._process_poster_image(poster_response.content)
            
        except Exception as e:
            logger.error(f"Error getting AniList poster: {e}")
            return None
    
    def _process_poster_image(self, image_data: bytes) -> bytes:
        """
        Process the poster image to ensure it's the right format and size.
        
        Args:
            image_data: The original image data
            
        Returns:
            Processed image data
        """
        try:
            # Open the image
            img = Image.open(BytesIO(image_data))
            
            # Convert to RGB if it's not already
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Resize if needed while maintaining aspect ratio
            max_size = self.config.MAX_POSTER_SIZE
            if max_size and (img.width > max_size or img.height > max_size):
                ratio = min(max_size / img.width, max_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Save the image to a BytesIO object
            output = BytesIO()
            img.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error processing poster image: {e}")
            return image_data  # Return the original image data if processing fails
    
    def _get_mock_poster(self, title: str) -> Optional[bytes]:
        """
        Generate a simple mock poster image for testing/demo purposes.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            # Create a new image with a nice dark blue background
            img = Image.new('RGB', (400, 600), color=(40, 40, 80))
            draw = ImageDraw.Draw(img)
            
            # Use a default font
            font = None
            try:
                font = ImageFont.truetype("arial.ttf", 32)
            except Exception:
                try:
                    # Try system font on Windows
                    font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 32)
                except Exception:
                    font = ImageFont.load_default()
            
            # Calculate text position (using textbbox for modern Pillow)
            text = title
            try:
                # Modern Pillow method (>=8.0.0)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except (AttributeError, TypeError):
                # Fallback for older Pillow versions
                try:
                    text_width, text_height = draw.textsize(text, font=font)
                except Exception:
                    # Ultimate fallback
                    text_width, text_height = len(text) * 15, 32
            
            # Draw the text centered
            x_position = (400 - text_width) // 2
            y_position = (600 - text_height) // 2
            draw.text((x_position, y_position), text, fill=(255, 255, 255), font=font)
            
            # Convert to bytes
            output = BytesIO()
            img.save(output, format="JPEG", quality=90)
            
            logger.info(f"Created mock poster for: {title}")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating mock poster: {e}")
            
            # Try an even simpler fallback method
            try:
                # Create a simple colored image as fallback
                img = Image.new('RGB', (400, 600), color=(40, 40, 80))
                output = BytesIO()
                img.save(output, format="JPEG", quality=85)
                return output.getvalue()
            except Exception:
                return None
