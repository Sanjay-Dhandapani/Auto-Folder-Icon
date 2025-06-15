#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration module for the Media Iconer application.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Config:
    """Configuration handler for the Media Iconer application."""
      # Default configuration values
    DEFAULT_CONFIG = {
        # Media directory to monitor
        'MEDIA_ROOT_DIR': 'D:\\Media',
        
        # API keys
        'TMDB_API_KEY': '',
        'OMDB_API_KEY': '',
        
        # Cache settings
        'CACHE_DIR': os.path.join(os.path.expanduser('~'), '.media_iconer', 'cache'),
        'USE_CACHE': True,
        
        # Watching settings
        'SCAN_ON_START': True,
        'DEBOUNCE_TIME': 5.0,  # seconds to wait after changes before processing
        'FORCE_UPDATE': False,  # force update of existing icons
        
        # Poster settings
        'MAX_POSTER_SIZE': 1024,  # maximum width/height for posters
        
        # Mock API for demo/testing purposes
        'USE_MOCK_API': True  # Set to True to use mock API responses instead of real APIs
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration.
        
        Args:
            config_file: Path to a configuration file, or None to use default locations
        """
        self.config_data = dict(self.DEFAULT_CONFIG)
        
        # Try to load configuration from file
        if config_file:
            self._load_config(config_file)
        else:
            # Try standard locations
            locations = [
                os.path.join(os.getcwd(), 'config.json'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'),
                os.path.join(os.path.expanduser('~'), '.media_iconer', 'config.json')
            ]
            
            for location in locations:
                if os.path.exists(location):
                    self._load_config(location)
                    break
        
        # Expand environment variables in paths
        if 'CACHE_DIR' in self.config_data:
            self.config_data['CACHE_DIR'] = self._expand_env_vars(self.config_data['CACHE_DIR'])
        
        # Create cache directory
        os.makedirs(self.CACHE_DIR, exist_ok=True)
    
    def _load_config(self, config_file: str) -> None:
        """
        Load configuration from a file.
        
        Args:
            config_file: Path to the configuration file
        """
        try:
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                
                # Update configuration with values from file
                self.config_data.update(file_config)
                
                logger.info(f"Loaded configuration from {config_file}")
                
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")
    
    def save_config(self, config_file: Optional[str] = None) -> bool:
        """
        Save the current configuration to a file.
        
        Args:
            config_file: Path to save the configuration to, or None to use the last loaded file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # If no file is specified, use the first standard location
            if not config_file:
                config_dir = os.path.join(os.path.expanduser('~'), '.media_iconer')
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, 'config.json')
            
            # Save the configuration
            with open(config_file, 'w') as f:
                json.dump(self.config_data, f, indent=4)
                
            logger.info(f"Saved configuration to {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration to {config_file}: {e}")
            return False
    
    def __getattr__(self, name: str) -> Any:
        """
        Get a configuration value.
        
        Args:
            name: Name of the configuration value
            
        Returns:
            The configuration value, or None if not found
        """
        return self.config_data.get(name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            name: Name of the configuration value
            value: Value to set
        """
        if name == 'config_data':
            super().__setattr__(name, value)
        else:
            self.config_data[name] = value
    
    def _expand_env_vars(self, path: str) -> str:
        """
        Expand environment variables in a path string.
        
        Args:
            path: Path string that may contain environment variables
            
        Returns:
            Path with environment variables expanded
        """
        # Expand %USERPROFILE% and similar Windows environment variables
        if '%' in path:
            import re
            env_vars = re.findall(r'%(\w+)%', path)
            for var in env_vars:
                if var in os.environ:
                    path = path.replace(f'%{var}%', os.environ[var])
        
        # Also expand standard environment variables like $HOME
        path = os.path.expandvars(path)
        return path
