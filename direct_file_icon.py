#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Direct File Icon Setter Module.
Sets custom icon directly for media files like .mp4, .mkv, etc. using desktop.ini
"""

import os
import subprocess
import logging
import shutil
import ctypes
from PIL import Image
import tempfile

class DirectFileIconSetter:
    def __init__(self):
        """Initialize the direct file icon setter."""
        self.logger = logging.getLogger(__name__)
        
        # Media extensions we support setting icons for
        self.supported_extensions = {
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'
        }

    def set_media_file_icon(self, media_file_path, image_path):
        """
        Set a custom icon for a media file using Windows shortcut trick.
        
        This method creates a .lnk shortcut to the media file in the same directory,
        then sets the icon for that shortcut. This effectively changes how the media file
        appears in Windows Explorer.
        
        Args:
            media_file_path (str): Path to the media file to customize
            image_path (str): Path to the image to use as icon (typically poster.jpg)
        
        Returns:
            bool: Success status
        """
        if not os.path.exists(media_file_path):
            self.logger.error(f"Media file does not exist: {media_file_path}")
            return False
        
        if not os.path.exists(image_path):
            self.logger.error(f"Image file does not exist: {image_path}")
            return False
            
        # Get file extension
        _, ext = os.path.splitext(media_file_path)
        ext = ext.lower()
        
        if ext not in self.supported_extensions:
            self.logger.warning(f"Unsupported file extension: {ext}")
            return False
            
        try:
            # Needed for proper file path handling
            media_file_path = os.path.abspath(media_file_path)
            image_path = os.path.abspath(image_path)
            
            # Create the .ico file in the same directory
            dir_path = os.path.dirname(media_file_path)
            base_name = os.path.basename(media_file_path)
            icon_path = os.path.join(dir_path, f"{base_name}.ico")
            
            # Convert image to .ico
            self._convert_to_ico(image_path, icon_path)
            
            # Create a desktop.ini file specific to this file
            folder_path = os.path.dirname(media_file_path)
            ini_file = os.path.join(folder_path, f"{base_name}.ini")
            
            # First, remove any existing .ini file
            if os.path.exists(ini_file):
                try:
                    os.remove(ini_file)
                    self.logger.info(f"Removed existing .ini file: {ini_file}")
                except Exception as e:
                    self.logger.warning(f"Could not remove existing .ini file: {e}")
            
            # Create a new .ini file
            ini_content = (
                "[.ShellClassInfo]\n"
                f"IconFile={icon_path}\n"
                "IconIndex=0\n"
                "[ViewState]\n"
                "Mode=\n"
                "Vid=\n"
            )
            
            with open(ini_file, 'w', encoding='utf-8') as f:
                f.write(ini_content)
                
            # Now create a Windows shortcut with the custom icon
            shortcut_path = os.path.join(dir_path, f"{os.path.splitext(base_name)[0]}.lnk")
            
            # Create shortcut using PowerShell
            ps_command = (
                f'$WshShell = New-Object -comObject WScript.Shell; '
                f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
                f'$Shortcut.TargetPath = "{media_file_path}"; '
                f'$Shortcut.IconLocation = "{icon_path},0"; '
                f'$Shortcut.Save()'
            )
            
            # Execute PowerShell command
            subprocess.run(["powershell", "-Command", ps_command], 
                        check=True, 
                        capture_output=True,
                        text=True)
            
            # Create a desktop.ini in the parent folder 
            desktop_ini_path = os.path.join(dir_path, "desktop.ini")
            
            # Make file attributes more reliable
            subprocess.run(["attrib", "+r", icon_path], shell=True)
            
            # Hide original file and make the shortcut visible
            try:
                # Make original file hidden and keep shortcut visible
                subprocess.run(["attrib", "+h", media_file_path], shell=True)
            except Exception as e:
                self.logger.warning(f"Could not set file attributes: {e}")
            
            # Force refresh icon cache
            self._refresh_icon_cache()
            
            self.logger.info(f"Successfully set icon for {media_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set media file icon: {e}")
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
            if os.path.isdir(file_path):
                if recursively:
                    sub_results = self.set_media_files_in_folder(file_path, recursively)
                    results["success"] += sub_results["success"]
                    results["failed"] += sub_results["failed"]
                continue
                
            # Skip non-files
            if not os.path.isfile(file_path):
                continue
            
            # Skip shortcuts we've already created
            if file_path.lower().endswith('.lnk'):
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

    def _refresh_icon_cache(self):
        """Refresh the Windows icon cache."""
        try:
            subprocess.run(["ie4uinit.exe", "-ClearIconCache"], 
                         shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            subprocess.run(["ie4uinit.exe", "-show"], 
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
            media_file_path = os.path.abspath(file_path)
            dir_path = os.path.dirname(media_file_path)
            base_name = os.path.basename(media_file_path)
            
            # Remove shortcut if it exists
            shortcut_path = os.path.join(dir_path, f"{os.path.splitext(base_name)[0]}.lnk")
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                
            # Remove custom .ini file if it exists
            ini_file = os.path.join(dir_path, f"{base_name}.ini")
            if os.path.exists(ini_file):
                os.remove(ini_file)
                
            # Remove icon file if it exists
            icon_path = os.path.join(dir_path, f"{base_name}.ico")
            if os.path.exists(icon_path):
                os.remove(icon_path)
                
            # Make original file visible again
            try:
                subprocess.run(["attrib", "-h", media_file_path], shell=True)
            except Exception as e:
                self.logger.warning(f"Could not reset file attributes: {e}")
                
            # Refresh icon cache
            self._refresh_icon_cache()
            
            self.logger.info(f"Successfully reverted icon for {media_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revert media file icon: {e}")
            return False
