#!/usr/bin/env python3
"""
Smart Media Icon Tray Settings Manager

Extended configuration management for the tray application,
building upon the existing Config class while maintaining compatibility.
"""

import os
import json
import logging
import winreg
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import the base Config class
from ..utils.config import Config


class TraySettingsManager(Config):
    """
    Extends the base Config class with tray-specific settings
    while maintaining full CLI compatibility
    """
    
    # Tray-specific default configuration
    TRAY_DEFAULT_CONFIG = {
        # Tray Application Settings
        'TRAY_ENABLED': True,
        'START_WITH_WINDOWS': False,
        'START_MINIMIZED': True,
        'CLOSE_TO_TRAY': True,
        
        # Monitoring Settings
        'AUTO_MONITOR_ENABLED': True,
        'MONITORED_DIRECTORIES': [],
        'MONITOR_RECURSIVE': True,
        'DEBOUNCE_TIME': 5.0,  # seconds
        'MAX_CONCURRENT_PROCESSING': 3,
        'RECURSIVE_DEPTH_LIMIT': 5,
        'BATCH_SIZE': 50,
        'RETRY_ATTEMPTS': 3,
        'MONITOR_HIDDEN_FOLDERS': False,
        'EXCLUDE_PATTERNS': ['*.tmp', '*.part', '*.crdownload'],
        
        # Notification Settings
        'SHOW_NOTIFICATIONS': True,
        'NOTIFICATION_DURATION': 5000,  # milliseconds
        'SOUND_ENABLED': False,
        'DETAILED_NOTIFICATIONS': False,
        
        # UI Settings
        'REMEMBER_WINDOW_POSITION': True,
        'THEME': 'system',  # system, light, dark
        'LANGUAGE': 'en',
        'WINDOW_POSITIONS': {},
        
        # Performance Settings
        'CACHE_SIZE_LIMIT': 1000,  # MB
        'AUTO_CLEANUP_CACHE': True,
        'LOG_RETENTION_DAYS': 30,
        'MAX_EVENTS_PER_SECOND': 10,
        
        # File Processing Settings
        'PROCESSING_PRIORITY': 'normal',  # low, normal, high
        'SKIP_EXISTING_ICONS': False,
        'BACKUP_ORIGINAL_FILES': True,
        'VERIFY_OPERATIONS': True,
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the tray settings manager
        
        Args:
            config_file: Path to configuration file (optional)
        """
        # Initialize the base Config class first
        super().__init__(config_file)
        
        self.logger = logging.getLogger(__name__)
        
        # Add tray-specific defaults to the configuration
        self.config_data.update(self.TRAY_DEFAULT_CONFIG)
        
        # Load tray-specific settings
        self._load_tray_settings()
        
        # Initialize Windows startup manager
        self.startup_manager = WindowsStartupManager()
        
        self.logger.info("⚙️ Tray settings manager initialized")
    
    def _load_tray_settings(self):
        """Load tray-specific settings from configuration file"""
        try:
            # Look for tray_settings section in the existing config file
            config_paths = [
                os.path.join(os.getcwd(), 'config.json'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'config.json'),
                os.path.join(os.path.expanduser('~'), '.smart_media_icon', 'config.json')
            ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)
                            
                        # Load tray-specific settings if they exist
                        if 'tray_settings' in config_data:
                            tray_settings = config_data['tray_settings']
                            self.config_data.update(tray_settings)
                            self.logger.info(f"Loaded tray settings from: {config_path}")
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to load tray settings from {config_path}: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Error loading tray settings: {e}")
    
    def save_tray_settings(self) -> bool:
        """
        Save tray-specific settings while preserving base configuration
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Determine config file path
            config_file = os.path.join(os.getcwd(), 'config.json')
            
            # Load existing configuration
            existing_config = {}
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        existing_config = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load existing config: {e}")
            
            # Extract tray-specific settings
            tray_settings = {}
            for key in self.TRAY_DEFAULT_CONFIG.keys():
                if hasattr(self, key):
                    tray_settings[key] = getattr(self, key)
                elif key in self.config_data:
                    tray_settings[key] = self.config_data[key]
            
            # Update existing config with tray settings
            existing_config['tray_settings'] = tray_settings
            
            # Also preserve base settings in root level for CLI compatibility
            base_keys = ['TMDB_API_KEY', 'OMDB_API_KEY', 'TVMAZE_API_KEY', 'ANILIST_API_KEY',
                        'CACHE_DIR', 'USE_CACHE', 'USE_MOCK_API', 'USE_MOCK_ON_FAILURE',
                        'MAX_POSTER_SIZE', 'MEDIA_ROOT_DIR']
            
            for key in base_keys:
                if hasattr(self, key):
                    existing_config[key] = getattr(self, key)
                elif key in self.config_data:
                    existing_config[key] = self.config_data[key]
            
            # Save the updated configuration
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(existing_config, f, indent=4)
            
            self.logger.info(f"Tray settings saved to: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save tray settings: {e}")
            return False
    
    def get_cli_compatible_config(self) -> Config:
        """
        Return a base Config object for CLI compatibility
        
        Returns:
            Config: Base configuration object without tray settings
        """
        # Create a temporary config file with only base settings
        try:
            import tempfile
            
            base_config = {}
            base_keys = ['TMDB_API_KEY', 'OMDB_API_KEY', 'TVMAZE_API_KEY', 'ANILIST_API_KEY',
                        'CACHE_DIR', 'USE_CACHE', 'USE_MOCK_API', 'USE_MOCK_ON_FAILURE',
                        'MAX_POSTER_SIZE', 'MEDIA_ROOT_DIR']
            
            for key in base_keys:
                if hasattr(self, key):
                    base_config[key] = getattr(self, key)
                elif key in self.config_data:
                    base_config[key] = self.config_data[key]
            
            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(base_config, f, indent=4)
                temp_config_path = f.name
            
            # Return base Config object
            cli_config = Config(temp_config_path)
            
            # Clean up temporary file
            os.unlink(temp_config_path)
            
            return cli_config
            
        except Exception as e:
            self.logger.error(f"Failed to create CLI-compatible config: {e}")
            return Config()  # Return default config
    
    def add_monitored_directory(self, path: str, recursive: bool = True, enabled: bool = True) -> bool:
        """
        Add a directory to the monitoring list
        
        Args:
            path: Directory path to monitor
            recursive: Whether to monitor subdirectories
            enabled: Whether monitoring is enabled for this directory
            
        Returns:
            bool: True if added successfully
        """
        try:
            path = os.path.abspath(path)
            
            if not os.path.exists(path):
                self.logger.error(f"Directory does not exist: {path}")
                return False
            
            # Check if already in the list
            monitored_dirs = self.MONITORED_DIRECTORIES or []
            for existing in monitored_dirs:
                existing_path = existing.get('path') if isinstance(existing, dict) else existing
                if os.path.abspath(existing_path) == path:
                    self.logger.warning(f"Directory already monitored: {path}")
                    return False
            
            # Add new directory
            new_entry = {
                'path': path,
                'recursive': recursive,
                'enabled': enabled,
                'added_date': self._get_current_timestamp()
            }
            
            monitored_dirs.append(new_entry)
            self.MONITORED_DIRECTORIES = monitored_dirs
            
            self.logger.info(f"Added monitored directory: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add monitored directory: {e}")
            return False
    
    def remove_monitored_directory(self, path: str) -> bool:
        """
        Remove a directory from the monitoring list
        
        Args:
            path: Directory path to remove
            
        Returns:
            bool: True if removed successfully
        """
        try:
            path = os.path.abspath(path)
            monitored_dirs = self.MONITORED_DIRECTORIES or []
            
            # Find and remove the directory
            updated_dirs = []
            removed = False
            
            for existing in monitored_dirs:
                existing_path = existing.get('path') if isinstance(existing, dict) else existing
                if os.path.abspath(existing_path) != path:
                    updated_dirs.append(existing)
                else:
                    removed = True
            
            if removed:
                self.MONITORED_DIRECTORIES = updated_dirs
                self.logger.info(f"Removed monitored directory: {path}")
                return True
            else:
                self.logger.warning(f"Directory not found in monitoring list: {path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove monitored directory: {e}")
            return False
    
    def update_monitored_directory(self, path: str, **kwargs) -> bool:
        """
        Update settings for a monitored directory
        
        Args:
            path: Directory path
            **kwargs: Settings to update (recursive, enabled, etc.)
            
        Returns:
            bool: True if updated successfully
        """
        try:
            path = os.path.abspath(path)
            monitored_dirs = self.MONITORED_DIRECTORIES or []
            
            # Find and update the directory
            updated = False
            for existing in monitored_dirs:
                if isinstance(existing, dict):
                    existing_path = existing.get('path', '')
                    if os.path.abspath(existing_path) == path:
                        existing.update(kwargs)
                        existing['modified_date'] = self._get_current_timestamp()
                        updated = True
                        break
            
            if updated:
                self.MONITORED_DIRECTORIES = monitored_dirs
                self.logger.info(f"Updated monitored directory: {path}")
                return True
            else:
                self.logger.warning(f"Directory not found for update: {path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update monitored directory: {e}")
            return False
    
    def get_monitored_directories(self) -> List[Dict[str, Any]]:
        """
        Get list of monitored directories with full details
        
        Returns:
            List of dictionaries containing directory information
        """
        monitored_dirs = self.MONITORED_DIRECTORIES or []
        result = []
        
        for directory in monitored_dirs:
            if isinstance(directory, dict):
                result.append(directory.copy())
            else:
                # Convert old string format to new dict format
                result.append({
                    'path': str(directory),
                    'recursive': True,
                    'enabled': True,
                    'added_date': None
                })
        
        return result
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Validate API key configuration
        
        Returns:
            Dictionary mapping API names to validation status
        """
        api_validation = {}
        
        # Check each API key
        apis = {
            'TMDB': self.TMDB_API_KEY,
            'OMDb': self.OMDB_API_KEY,
            'TVmaze': self.TVMAZE_API_KEY,
            'AniList': self.ANILIST_API_KEY
        }
        
        for api_name, api_key in apis.items():
            # Basic validation (non-empty, reasonable length)
            if api_key and len(str(api_key).strip()) > 10:
                api_validation[api_name] = True
            else:
                api_validation[api_name] = False
        
        return api_validation
    
    def cleanup_cache(self) -> Dict[str, Any]:
        """
        Clean up old cache files based on retention settings
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cache_dir = Path(self.CACHE_DIR)
            if not cache_dir.exists():
                return {'cleaned': 0, 'size_freed': 0, 'error': None}
            
            import time
            current_time = time.time()
            retention_seconds = self.LOG_RETENTION_DAYS * 24 * 3600
            
            cleaned_count = 0
            size_freed = 0
            
            for cache_file in cache_dir.glob('*'):
                if cache_file.is_file():
                    file_age = current_time - cache_file.stat().st_mtime
                    if file_age > retention_seconds:
                        file_size = cache_file.stat().st_size
                        cache_file.unlink()
                        cleaned_count += 1
                        size_freed += file_size
            
            self.logger.info(f"Cache cleanup: {cleaned_count} files, {size_freed / (1024*1024):.1f} MB freed")
            
            return {
                'cleaned': cleaned_count,
                'size_freed': size_freed,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Cache cleanup failed: {e}")
            return {'cleaned': 0, 'size_freed': 0, 'error': str(e)}
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def migrate_legacy_config(self, legacy_config: dict) -> bool:
        """
        Migrate legacy configuration to new tray format
        
        Args:
            legacy_config: Old configuration dictionary
            
        Returns:
            bool: True if migration successful
        """
        try:
            # Migrate base settings
            base_keys = ['TMDB_API_KEY', 'OMDB_API_KEY', 'CACHE_DIR', 'USE_CACHE']
            for key in base_keys:
                if key in legacy_config:
                    setattr(self, key, legacy_config[key])
            
            # Migrate monitoring settings if they exist
            if 'MEDIA_ROOT_DIR' in legacy_config:
                # Convert single directory to monitored directories list
                root_dir = legacy_config['MEDIA_ROOT_DIR']
                if root_dir and os.path.exists(root_dir):
                    self.add_monitored_directory(root_dir)
            
            self.logger.info("Legacy configuration migrated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to migrate legacy config: {e}")
            return False


class WindowsStartupManager:
    """
    Manages Windows startup registration for the tray application
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_name = "Smart Media Icon"
        self.registry_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def is_startup_enabled(self) -> bool:
        """
        Check if application is registered for startup
        
        Returns:
            bool: True if registered for startup
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key) as key:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                return bool(value)
        except (FileNotFoundError, OSError):
            return False
    
    def enable_startup(self, executable_path: str) -> bool:
        """
        Enable application startup with Windows
        
        Args:
            executable_path: Path to the application executable
            
        Returns:
            bool: True if successful
        """
        try:
            # Create startup command with --minimized flag
            startup_command = f'"{executable_path}" --minimized'
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, startup_command)
            
            self.logger.info("Enabled Windows startup registration")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable startup: {e}")
            return False
    
    def disable_startup(self) -> bool:
        """
        Disable application startup with Windows
        
        Returns:
            bool: True if successful
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, self.app_name)
            
            self.logger.info("Disabled Windows startup registration")
            return True
            
        except FileNotFoundError:
            # Already not registered
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable startup: {e}")
            return False
    
    def update_startup(self, enabled: bool, executable_path: str = None) -> bool:
        """
        Update startup registration status
        
        Args:
            enabled: Whether to enable or disable startup
            executable_path: Path to executable (required if enabling)
            
        Returns:
            bool: True if successful
        """
        if enabled:
            if not executable_path:
                executable_path = self._get_current_executable_path()
            return self.enable_startup(executable_path)
        else:
            return self.disable_startup()
    
    def _get_current_executable_path(self) -> str:
        """Get the current executable path"""
        import sys
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle
            return sys.executable
        else:
            # Running as Python script
            return f"{sys.executable} {os.path.abspath(__file__)}"