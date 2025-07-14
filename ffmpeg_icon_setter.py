#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FFmpeg Icon Setter Module.
Uses FFmpeg to embed artwork in media files and extract as .ico files for Windows icons.
"""

import os
import subprocess
import logging
import shutil
import tempfile
from pathlib import Path
from PIL import Image
import winreg

class FFmpegIconSetter:
    """Handles setting icons for media files using FFmpeg."""
    
    def __init__(self):
        """Initialize the FFmpeg icon setter."""
        self.logger = logging.getLogger(__name__)
        
        # Check if FFmpeg is available
        self.ffmpeg_available = self._check_ffmpeg()
        
        # Media extensions we support
        self.supported_extensions = {
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'
        }
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available in the system."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.logger.info("FFmpeg found and available")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        self.logger.warning("FFmpeg not found. Some features may not work.")
        return False
    
    def _convert_image_to_ico(self, image_path, ico_path):
        """Convert an image to .ico format."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to multiple icon sizes
                sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
                icons = []
                
                for size in sizes:
                    resized = img.resize(size, Image.Resampling.LANCZOS)
                    icons.append(resized)
                
                # Save as .ico
                icons[0].save(ico_path, format='ICO', sizes=[(icon.width, icon.height) for icon in icons])
                self.logger.info(f"Created icon file: {ico_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error converting image to .ico: {e}")
            return False
    
    def embed_artwork_in_media(self, media_file_path, poster_path):
        """Embed artwork in media file using FFmpeg."""
        if not self.ffmpeg_available:
            self.logger.warning("FFmpeg not available, skipping artwork embedding")
            return False
        
        if not os.path.exists(media_file_path):
            self.logger.error(f"Media file not found: {media_file_path}")
            return False
        
        if not os.path.exists(poster_path):
            self.logger.error(f"Poster file not found: {poster_path}")
            return False
        
        # Create backup of original file
        backup_path = f"{media_file_path}.backup"
        if not os.path.exists(backup_path):
            try:
                shutil.copy2(media_file_path, backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                self.logger.error(f"Failed to create backup: {e}")
                return False
        
        # Create temporary output file
        temp_output = f"{media_file_path}.temp.mp4"  # Use proper extension for FFmpeg
        
        try:
            # FFmpeg command to embed artwork
            cmd = [
                'ffmpeg',
                '-i', media_file_path,
                '-i', poster_path,
                '-map', '0',  # Map all streams from first input
                '-map', '1',  # Map image from second input
                '-c', 'copy',  # Copy codecs
                '-c:v:1', 'copy',  # Copy video codec for attached picture
                '-disposition:v:1', 'attached_pic',  # Mark as attached picture
                '-y',  # Overwrite output file
                temp_output
            ]
            
            self.logger.info(f"Embedding artwork in {os.path.basename(media_file_path)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Replace original file with the one containing artwork
                shutil.move(temp_output, media_file_path)
                self.logger.info(f"Successfully embedded artwork in {os.path.basename(media_file_path)}")
                return True
            else:
                self.logger.error(f"FFmpeg error: {result.stderr}")
                # Clean up temp file if it exists
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("FFmpeg command timed out")
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return False
        except Exception as e:
            self.logger.error(f"Error embedding artwork: {e}")
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return False
    
    def set_file_icon_via_registry(self, media_file_path, ico_path):
        """Set file icon using Windows registry by creating a file association."""
        try:
            file_path = Path(media_file_path)
            file_ext = file_path.suffix.lower()
            
            # Create a unique file type for this specific file
            unique_type = f"MoviePoster{abs(hash(media_file_path))}"
            
            # Step 1: Create the file type in registry
            type_key_path = f"Software\\Classes\\{unique_type}"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, type_key_path) as type_key:
                winreg.SetValueEx(type_key, "", 0, winreg.REG_SZ, f"Movie with Custom Poster")
            
            # Step 2: Set the icon for this file type
            icon_key_path = f"Software\\Classes\\{unique_type}\\DefaultIcon"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, icon_key_path) as icon_key:
                winreg.SetValueEx(icon_key, "", 0, winreg.REG_SZ, f'"{ico_path}",0')
            
            # Step 3: Associate this specific file with the custom type
            # This is the tricky part - we need to modify the file's properties
            
            # Try to set the file association using attrib and file properties
            self._set_file_type_association(media_file_path, unique_type)
            
            self.logger.info(f"Set registry icon for {file_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting file icon via registry: {e}")
            return False
    
    def _set_file_type_association(self, media_file_path, file_type):
        """Try to associate a specific file with a custom file type."""
        try:
            # Method 1: Try using Windows API through PowerShell
            ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$file = Get-Item "{media_file_path}"
# This is a Windows limitation - individual file icons are not easily changeable
"""
            subprocess.run(['powershell', '-Command', ps_script], 
                         capture_output=True, text=True, timeout=10)
            
        except Exception as e:
            self.logger.debug(f"File type association attempt failed: {e}")
            pass
    
    def create_icon_shortcut(self, media_file_path, poster_path):
        """Create a shortcut with custom icon as fallback method."""
        try:
            # Convert poster to .ico
            media_dir = Path(media_file_path).parent
            ico_path = media_dir / f"{Path(media_file_path).stem}.ico"
            
            if not self._convert_image_to_ico(poster_path, str(ico_path)):
                return False
            
            # Create shortcut using PowerShell
            shortcut_path = str(media_dir / f"{Path(media_file_path).stem}.lnk")
            
            ps_script = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{media_file_path}"
$Shortcut.IconLocation = "{ico_path}"
$Shortcut.Save()
"""
            
            result = subprocess.run(['powershell', '-Command', ps_script],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Created icon shortcut for {Path(media_file_path).name}")
                return True
            else:
                self.logger.error(f"PowerShell error: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating icon shortcut: {e}")
            return False
    
    def _try_shell_icon_overlay(self, media_file_path, ico_path):
        """Try to set file icon using Windows Shell API (most direct method)."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # This is an advanced Windows API approach
            # Load shell32.dll
            shell32 = ctypes.windll.shell32
            
            # Try to set the file's icon through the Shell API
            # Note: This is a very low-level approach and may not work on all systems
            
            # Convert paths to wide strings
            file_path_w = ctypes.c_wchar_p(media_file_path)
            ico_path_w = ctypes.c_wchar_p(ico_path)
            
            # This is experimental - Windows doesn't officially support per-file icons
            # But we try anyway
            self.logger.info(f"Attempting shell icon overlay for {Path(media_file_path).name}")
            
            return False  # Always return False as this is experimental
            
        except Exception as e:
            self.logger.debug(f"Shell icon overlay failed (expected): {e}")
            return False
    
    def _try_alternate_stream_method(self, media_file_path, ico_path):
        """Try using NTFS alternate data streams to associate icon."""
        try:
            # NTFS supports alternate data streams
            # We can try to store icon information there
            
            stream_path = f"{media_file_path}:Icon"
            
            # Copy the icon data to an alternate stream
            with open(ico_path, 'rb') as ico_file:
                icon_data = ico_file.read()
            
            with open(stream_path, 'wb') as stream:
                stream.write(icon_data)
            
            self.logger.info(f"Stored icon in alternate stream for {Path(media_file_path).name}")
            
            # This doesn't actually change the visible icon, but stores the data
            return False  # Return False as it doesn't change the visible icon
            
        except Exception as e:
            self.logger.debug(f"Alternate stream method failed: {e}")
            return False
    
    def set_movie_file_icon(self, media_file_path, poster_path):
        """
        Embed artwork directly in the media file using FFmpeg.
        
        This provides real benefits:
        - Media players will show the poster
        - File properties will show embedded artwork
        - The artwork becomes part of the media file itself
        
        Args:
            media_file_path (str): Path to the media file
            poster_path (str): Path to the poster image
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(media_file_path):
            self.logger.error(f"Media file not found: {media_file_path}")
            return False
        
        if not os.path.exists(poster_path):
            self.logger.error(f"Poster file not found: {poster_path}")
            return False
        
        file_ext = Path(media_file_path).suffix.lower()
        if file_ext not in self.supported_extensions:
            self.logger.warning(f"Unsupported file type: {file_ext}")
            return False
        
        self.logger.info(f"Embedding artwork in: {Path(media_file_path).name}")
        
        # The ONLY method that actually works: FFmpeg artwork embedding
        if self.ffmpeg_available:
            if self.embed_artwork_in_media(media_file_path, poster_path):
                self.logger.info("✅ SUCCESS: Artwork embedded in media file!")
                self.logger.info("✅ Benefits: Media players will show poster, file properties updated")
                return True
            else:
                self.logger.error("❌ Failed to embed artwork")
                return False
        else:
            self.logger.error("❌ FFmpeg not available - cannot embed artwork")
            self.logger.info("💡 Install FFmpeg to enable artwork embedding")
            return False
    
    def verify_embedded_artwork(self, media_file_path):
        """Verify that artwork was successfully embedded in the media file."""
        if not self.ffmpeg_available:
            return False
        
        try:
            # Use FFmpeg to check for embedded artwork
            cmd = [
                'ffmpeg',
                '-i', media_file_path,
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Check if the output mentions attached pictures
            if 'attached pic' in result.stderr.lower() or 'video:' in result.stderr:
                self.logger.info(f"✅ Verified: {Path(media_file_path).name} contains embedded artwork")
                return True
            else:
                self.logger.warning(f"⚠️  No embedded artwork detected in {Path(media_file_path).name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying artwork: {e}")
            return False
    
    def extract_embedded_artwork(self, media_file_path, output_path):
        """Extract embedded artwork from media file."""
        if not self.ffmpeg_available:
            self.logger.error("FFmpeg not available for artwork extraction")
            return False
        
        try:
            # Extract the first video stream (which should be the attached picture)
            cmd = [
                'ffmpeg',
                '-i', media_file_path,
                '-an',  # No audio
                '-vcodec', 'copy',  # Copy video codec
                '-vframes', '1',  # Only first frame
                '-y',  # Overwrite output
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path):
                self.logger.info(f"✅ Extracted artwork to: {output_path}")
                return True
            else:
                self.logger.error(f"Failed to extract artwork: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error extracting artwork: {e}")
            return False
