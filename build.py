#!/usr/bin/env python3
"""
Smart Media Icon Build Script

Automated build script for creating distributable packages of the Smart Media Icon System.
Supports both tray and CLI applications with proper dependency management.
"""

import os
import sys
import shutil
import subprocess
import zipfile
import json
import urllib.request
from pathlib import Path
from typing import Optional


class SmartMediaIconBuilder:
    """Main builder class for Smart Media Icon System"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / 'build'
        self.dist_dir = self.project_root / 'dist'
        self.resources_dir = self.project_root / 'resources'
        self.external_dir = self.project_root / 'external'
        
        # Build configuration
        self.config = {
            'version': '1.0.0',
            'build_tray': True,
            'build_cli': True,
            'include_ffmpeg': True,
            'create_installer': False,
            'create_portable': True,
            'upx_compress': True
        }
        
        print("🚀 Smart Media Icon Build System")
        print(f"📁 Project Root: {self.project_root}")
        print(f"🔧 Build Directory: {self.build_dir}")
        print(f"📦 Distribution Directory: {self.dist_dir}")
    
    def clean_build(self):
        """Clean previous build artifacts"""
        print("\n🧹 Cleaning previous build artifacts...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        
        for directory in dirs_to_clean:
            if directory.exists():
                try:
                    shutil.rmtree(directory)
                    print(f"✅ Cleaned: {directory}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not clean {directory}: {e}")
        
        print("✅ Build cleanup complete")
    
    def prepare_resources(self):
        """Prepare resources for packaging"""
        print("\n📋 Preparing resources...")
        
        # Create resources directory structure
        os.makedirs(self.resources_dir / 'icons', exist_ok=True)
        os.makedirs(self.resources_dir / 'ui', exist_ok=True)
        os.makedirs(self.resources_dir / 'config', exist_ok=True)
        
        # Create a simple app icon (placeholder)
        self.create_simple_icon()
        
        # Copy configuration templates
        self.prepare_config_templates()
        
        print("✅ Resources prepared")
    
    def create_simple_icon(self):
        """Create a simple application icon"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple 256x256 icon
            img = Image.new('RGBA', (256, 256), (70, 130, 180, 255))  # Steel blue
            draw = ImageDraw.Draw(img)
            
            # Draw a simple media icon representation
            # Folder shape
            draw.rectangle([50, 80, 206, 200], fill=(100, 149, 237, 255), outline=(25, 25, 112, 255), width=3)
            
            # Media symbol (play button)
            triangle_points = [(110, 120), (110, 160), (150, 140)]
            draw.polygon(triangle_points, fill=(255, 255, 255, 255))
            
            # Save as ICO
            icon_path = self.resources_dir / 'icons' / 'app_icon.ico'
            img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            
            print(f"✅ Created application icon: {icon_path}")
            
        except ImportError:
            print("⚠️ Warning: PIL not available, skipping icon creation")
        except Exception as e:
            print(f"⚠️ Warning: Could not create icon: {e}")
    
    def prepare_config_templates(self):
        """Prepare configuration file templates"""
        config_template = {
            "MEDIA_ROOT_DIR": "D:\\Media",
            "TMDB_API_KEY": "",
            "OMDB_API_KEY": "",
            "TVMAZE_API_KEY": "",
            "ANILIST_API_KEY": "",
            "CACHE_DIR": "%USERPROFILE%\\.smart_media_icon\\cache",
            "USE_CACHE": True,
            "USE_MOCK_API": True,
            "USE_MOCK_ON_FAILURE": True,
            "MAX_POSTER_SIZE": 1024,
            "tray_settings": {
                "AUTO_MONITOR_ENABLED": True,
                "MONITORED_DIRECTORIES": [],
                "DEBOUNCE_TIME": 5.0,
                "SHOW_NOTIFICATIONS": True,
                "START_WITH_WINDOWS": False,
                "START_MINIMIZED": True
            }
        }
        
        config_path = self.resources_dir / 'config' / 'config_template.json'
        with open(config_path, 'w') as f:
            json.dump(config_template, f, indent=4)
        
        print(f"✅ Created config template: {config_path}")
    
    def download_ffmpeg(self):
        """Download FFmpeg binaries if not present"""
        if not self.config['include_ffmpeg']:
            print("⏭️ Skipping FFmpeg download (disabled in config)")
            return
        
        print("\n📥 Checking FFmpeg binaries...")
        
        ffmpeg_dir = self.external_dir / 'ffmpeg'
        ffmpeg_exe = ffmpeg_dir / 'ffmpeg.exe'
        ffprobe_exe = ffmpeg_dir / 'ffprobe.exe'
        
        if ffmpeg_exe.exists() and ffprobe_exe.exists():
            print("✅ FFmpeg binaries already present")
            return
        
        print("📥 FFmpeg binaries not found. Download required.")
        print("💡 Please manually download FFmpeg essentials from:")
        print("   https://www.gyan.dev/ffmpeg/builds/")
        print("   Extract ffmpeg.exe and ffprobe.exe to: external/ffmpeg/")
        
        # Create directory
        os.makedirs(ffmpeg_dir, exist_ok=True)
        
        # For automated builds, you could implement download logic here
        # This is left as manual step for security and licensing reasons
    
    def check_dependencies(self):
        """Check build dependencies"""
        print("\n🔍 Checking build dependencies...")
        
        required_packages = ['PyInstaller', 'PyQt5', 'watchdog', 'requests', 'Pillow']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.lower().replace('-', '_'))
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package}")
        
        if missing_packages:
            print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False
        
        print("✅ All dependencies satisfied")
        return True
    
    def build_tray_app(self):
        """Build tray application"""
        if not self.config['build_tray']:
            print("⏭️ Skipping tray application build")
            return True
        
        print("\n🔨 Building tray application...")
        
        spec_file = self.project_root / 'smart_media_icon_tray.spec'
        if not spec_file.exists():
            print(f"❌ Spec file not found: {spec_file}")
            return False
        
        try:
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--clean',
                '--noconfirm',
                str(spec_file)
            ]
            
            print(f"🚀 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, check=True, 
                                  capture_output=True, text=True)
            
            print("✅ Tray application built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            print(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def build_cli_app(self):
        """Build CLI application"""
        if not self.config['build_cli']:
            print("⏭️ Skipping CLI application build")
            return True
        
        print("\n🔨 Building CLI application...")
        
        # For CLI, we'll create a simple PyInstaller command
        try:
            cli_main = self.project_root / 'src' / 'smart_media_icon' / 'cli.py'
            
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--clean',
                '--noconfirm',
                '--onedir',
                '--console',
                '--name', 'smart_media_icon_cli',
                '--paths', str(self.project_root / 'src'),
                str(cli_main)
            ]
            
            print(f"🚀 Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, check=True,
                                  capture_output=True, text=True)
            
            print("✅ CLI application built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ CLI build failed: {e}")
            print(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def create_portable_package(self):
        """Create portable ZIP package"""
        if not self.config['create_portable']:
            print("⏭️ Skipping portable package creation")
            return True
        
        print("\n📦 Creating portable package...")
        
        try:
            portable_dir = self.dist_dir / 'portable'
            os.makedirs(portable_dir, exist_ok=True)
            
            # Copy tray application
            tray_dist = self.dist_dir / 'smart_media_icon_tray'
            if tray_dist.exists():
                shutil.copytree(tray_dist, portable_dir / 'tray', dirs_exist_ok=True)
            
            # Copy CLI application  
            cli_dist = self.dist_dir / 'smart_media_icon_cli'
            if cli_dist.exists():
                shutil.copytree(cli_dist, portable_dir / 'cli', dirs_exist_ok=True)
            
            # Copy documentation
            docs_to_copy = ['README.md', 'LICENSE', 'config.json']
            for doc in docs_to_copy:
                doc_path = self.project_root / doc
                if doc_path.exists():
                    shutil.copy2(doc_path, portable_dir)
            
            # Create run scripts
            self.create_run_scripts(portable_dir)
            
            # Create ZIP file
            zip_path = self.dist_dir / f'smart_media_icon_v{self.config["version"]}_portable.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in portable_dir.rglob('*'):
                    if file_path.is_file():
                        arc_path = file_path.relative_to(portable_dir)
                        zf.write(file_path, arc_path)
            
            print(f"✅ Portable package created: {zip_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create portable package: {e}")
            return False
    
    def create_run_scripts(self, portable_dir: Path):
        """Create convenience run scripts"""
        # Tray application script
        tray_script = portable_dir / 'run_tray.bat'
        with open(tray_script, 'w') as f:
            f.write('@echo off\n')
            f.write('title Smart Media Icon - Tray\n')
            f.write('cd /d "%~dp0"\n')
            f.write('if exist "tray\\smart_media_icon_tray.exe" (\n')
            f.write('    start "" "tray\\smart_media_icon_tray.exe"\n')
            f.write(') else (\n')
            f.write('    echo Error: Tray application not found!\n')
            f.write('    pause\n')
            f.write(')\n')
        
        # CLI application script
        cli_script = portable_dir / 'run_cli.bat'
        with open(cli_script, 'w') as f:
            f.write('@echo off\n')
            f.write('title Smart Media Icon - CLI\n')
            f.write('cd /d "%~dp0"\n')
            f.write('if exist "cli\\smart_media_icon_cli.exe" (\n')
            f.write('    "cli\\smart_media_icon_cli.exe" %*\n')
            f.write(') else (\n')
            f.write('    echo Error: CLI application not found!\n')
            f.write(')\n')
            f.write('pause\n')
        
        # README for portable version
        readme_portable = portable_dir / 'README_PORTABLE.txt'
        with open(readme_portable, 'w') as f:
            f.write('Smart Media Icon System - Portable Version\n')
            f.write('==========================================\n\n')
            f.write('This is the portable version of Smart Media Icon System.\n')
            f.write('No installation is required.\n\n')
            f.write('Quick Start:\n')
            f.write('1. Double-click "run_tray.bat" to start the tray application\n')
            f.write('2. Or double-click "run_cli.bat" to use the command line version\n\n')
            f.write('Configuration:\n')
            f.write('- Edit "config.json" to configure API keys and settings\n')
            f.write('- The tray application also has a settings dialog\n\n')
            f.write('Requirements:\n')
            f.write('- Windows 10 or later\n')
            f.write('- FFmpeg (for movie artwork embedding)\n\n')
            f.write('For more information, see README.md\n')
        
        print("✅ Run scripts created")
    
    def validate_build(self):
        """Validate the built applications"""
        print("\n🔍 Validating build...")
        
        validation_passed = True
        
        # Check tray application
        if self.config['build_tray']:
            tray_exe = self.dist_dir / 'smart_media_icon_tray' / 'smart_media_icon_tray.exe'
            if tray_exe.exists():
                print(f"✅ Tray executable: {tray_exe}")
            else:
                print(f"❌ Tray executable missing: {tray_exe}")
                validation_passed = False
        
        # Check CLI application
        if self.config['build_cli']:
            cli_exe = self.dist_dir / 'smart_media_icon_cli' / 'smart_media_icon_cli.exe'
            if cli_exe.exists():
                print(f"✅ CLI executable: {cli_exe}")
            else:
                print(f"❌ CLI executable missing: {cli_exe}")
                validation_passed = False
        
        # Check portable package
        if self.config['create_portable']:
            portable_zip = self.dist_dir / f'smart_media_icon_v{self.config["version"]}_portable.zip'
            if portable_zip.exists():
                print(f"✅ Portable package: {portable_zip}")
            else:
                print(f"❌ Portable package missing: {portable_zip}")
                validation_passed = False
        
        return validation_passed
    
    def print_summary(self):
        """Print build summary"""
        print("\n" + "="*60)
        print("🎉 BUILD SUMMARY")
        print("="*60)
        
        if self.dist_dir.exists():
            print(f"📦 Distribution files in: {self.dist_dir}")
            
            for item in self.dist_dir.iterdir():
                if item.is_dir():
                    print(f"   📁 {item.name}/")
                else:
                    size_mb = item.stat().st_size / (1024 * 1024)
                    print(f"   📄 {item.name} ({size_mb:.1f} MB)")
        
        print("\n🚀 Quick Start:")
        print("1. Run the tray application:")
        print(f"   {self.dist_dir}\\smart_media_icon_tray\\smart_media_icon_tray.exe")
        print("\n2. Or use the portable version:")
        print(f"   Extract and run: smart_media_icon_v{self.config['version']}_portable.zip")
        
        print("\n💡 Next Steps:")
        print("- Configure API keys in settings")
        print("- Add media directories to monitor")
        print("- Install FFmpeg for movie artwork embedding")
        
        print("\n✅ Build completed successfully!")
    
    def build_all(self):
        """Run the complete build process"""
        print("Starting Smart Media Icon build process...")
        
        try:
            # Pre-build steps
            if not self.check_dependencies():
                return False
            
            self.clean_build()
            self.prepare_resources()
            self.download_ffmpeg()
            
            # Build applications
            if not self.build_tray_app():
                return False
            
            if not self.build_cli_app():
                return False
            
            # Package
            if not self.create_portable_package():
                return False
            
            # Validate
            if not self.validate_build():
                print("⚠️ Build validation failed, but executables may still work")
            
            # Summary
            self.print_summary()
            return True
            
        except KeyboardInterrupt:
            print("\n⏹️ Build interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Build failed with error: {e}")
            return False


def main():
    """Main entry point"""
    builder = SmartMediaIconBuilder()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Smart Media Icon Build Script")
    parser.add_argument('--tray-only', action='store_true', help='Build only tray application')
    parser.add_argument('--cli-only', action='store_true', help='Build only CLI application')
    parser.add_argument('--no-portable', action='store_true', help='Skip portable package creation')
    parser.add_argument('--no-ffmpeg', action='store_true', help='Skip FFmpeg setup')
    
    args = parser.parse_args()
    
    # Update configuration based on arguments
    if args.tray_only:
        builder.config['build_cli'] = False
    if args.cli_only:
        builder.config['build_tray'] = False
    if args.no_portable:
        builder.config['create_portable'] = False
    if args.no_ffmpeg:
        builder.config['include_ffmpeg'] = False
    
    # Run build
    success = builder.build_all()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())