#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File Icon Setter Module.
Sets custom icon for media files like .mp4, .mkv, etc.
"""

import os
import subprocess
import logging
import winreg
from PIL import Image

class FileIconSetter:
    def __init__(self):
        """Initialize the file icon setter."""
        self.logger = logging.getLogger(__name__)
        
        # Media extensions we support setting icons for
        self.supported_extensions = {
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'
        }

    def set_media_file_icon(self, file_path, image_path):
        """
        Set a custom icon for a media file.
        
        Args:
            file_path (str): Path to the media file to customize
            image_path (str): Path to the image to use as icon (typically poster.jpg)
        
        Returns:
            bool: Success status
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Media file does not exist: {file_path}")
            return False
        
        if not os.path.exists(image_path):
            self.logger.error(f"Image file does not exist: {image_path}")
            return False
            
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext not in self.supported_extensions:
            self.logger.warning(f"Unsupported file extension: {ext}")
            return False
        
        # Create .ico file in the same directory as the media file
        dir_path = os.path.dirname(file_path)
        icon_name = os.path.basename(file_path) + ".ico"
        icon_path = os.path.join(dir_path, icon_name)
        
        # Convert the image to .ico
        try:
            self._convert_to_ico(image_path, icon_path)
        except Exception as e:
            self.logger.error(f"Failed to convert image to icon: {e}")
            return False
            
        # Create registry entry for this specific file
        if self._create_registry_entry_for_file(file_path, icon_path):
            # Force icon cache refresh
            self._refresh_icon_cache()
            return True
        
        return False

    def set_media_files_in_folder(self, folder_path, recursively=False):
        """
        Set custom icons for all supported media files in a folder.
        
        Args:
            folder_path (str): Path to the folder containing media files
            recursively (bool): Whether to process subfolders recursively
            
        Returns:
            dict: Count of processed files {success: int, failed: int}
        """
        if not os.path.exists(folder_path):
            self.logger.error(f"Folder does not exist: {folder_path}")
            return {"success": 0, "failed": 0}
            
        # Find poster image
        poster_path = os.path.join(folder_path, "poster.jpg")
        
        if not os.path.exists(poster_path):
            self.logger.error(f"No poster.jpg found in {folder_path}")
            return {"success": 0, "failed": 0}
        
        results = {"success": 0, "failed": 0}
        
        # Process files in the current folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Skip directories when not recursive
            if os.path.isdir(file_path) and recursively:
                sub_results = self.set_media_files_in_folder(file_path, recursively)
                results["success"] += sub_results["success"]
                results["failed"] += sub_results["failed"]
                continue
                
            # Skip non-files
            if not os.path.isfile(file_path):
                continue
                
            # Skip non-media files
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            if ext not in self.supported_extensions:
                continue
                
            # Set icon for media file
            if self.set_media_file_icon(file_path, poster_path):
                results["success"] += 1
                self.logger.info(f"Set icon for {file_path}")
            else:
                results["failed"] += 1
                self.logger.warning(f"Failed to set icon for {file_path}")
                
        return results

    def _convert_to_ico(self, image_path, icon_path):
        """Convert an image to .ico format."""
        # Target icon sizes (square)
        sizes = [(256,256), (128,128), (64,64), (48,48), (32,32), (16,16)]
        icons = []
        
        img = Image.open(image_path).convert("RGBA")
        for size in sizes:
            # For media files, we want to maintain the poster aspect ratio
            # but ensure it's centered with a transparent background
            w, h = size
            poster_ratio = 2/3  # Standard poster ratio
            
            # Calculate poster size for this icon size
            poster_h = int(h * 0.9)  # 90% of icon height
            poster_w = int(poster_h * poster_ratio)
            if poster_w > w * 0.9:
                poster_w = int(w * 0.9)
                poster_h = int(poster_w / poster_ratio)
                
            canvas = Image.new("RGBA", size, (0,0,0,0))
            poster = img.resize((poster_w, poster_h), Image.LANCZOS)
            offset = ((w - poster_w)//2, (h - poster_h)//2)
            canvas.paste(poster, offset, poster)
            icons.append(canvas)
        
        icons[0].save(icon_path, format="ICO", sizes=sizes)
        return True

    def _create_registry_entry_for_file(self, file_path, icon_path):
        """
        Create a registry entry to set a custom icon for a specific file.
        This method uses IconHandler registry approach for file-specific icons.
        """
        try:
            # Each file needs its own unique registry key
            file_key = os.path.basename(file_path)
            registry_path = f"Software\\Classes\\{file_key}\\DefaultIcon"
            
            # Create the key structure
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path)
            
            # Set the icon path as the default value
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"{icon_path},0")
            
            # Close the key
            winreg.CloseKey(key)
            
            # Also need to associate the file with this custom class
            file_assoc_path = f"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\{os.path.splitext(file_key)[1]}\\UserChoice"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, file_assoc_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProgId", 0, winreg.REG_SZ, file_key)
                winreg.CloseKey(key)
            except Exception as e:
                self.logger.warning(f"Could not set file association (non-critical): {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create registry entry: {e}")
            return False

    def _refresh_icon_cache(self):
        """Refresh the Windows icon cache."""
        try:
            subprocess.run(["ie4uinit.exe", "-ClearIconCache"], 
                         shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            return True
        except Exception as e:
            self.logger.warning(f"Could not refresh icon cache: {e}")
            return False
            
    def revert_media_file_icon(self, file_path):
        """
        Remove the custom icon for a media file.
        
        Args:
            file_path (str): Path to the media file
            
        Returns:
            bool: Success status
        """
        try:
            # Remove registry entry
            file_key = os.path.basename(file_path)
            registry_path = f"Software\\Classes\\{file_key}"
            
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{registry_path}\\DefaultIcon")
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, registry_path)
            except FileNotFoundError:
                # Key doesn't exist, that's fine
                pass
                
            # Remove icon file if it exists
            icon_path = file_path + ".ico"
            if os.path.exists(icon_path):
                os.remove(icon_path)
                
            # Refresh icon cache
            self._refresh_icon_cache()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revert media file icon: {e}")
            return False
