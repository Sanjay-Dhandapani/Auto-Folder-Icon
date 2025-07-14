# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Smart Media Icon Tray Application

This builds the Windows system tray application with all necessary dependencies,
resources, and optimizations for distribution.
"""

import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent

# Define paths
src_path = project_root / 'src'
resources_path = project_root / 'resources'
external_path = project_root / 'external'

# Hidden imports for dynamic imports and PyQt5
hidden_imports = [
    # Tray application modules
    'smart_media_icon.tray.main',
    'smart_media_icon.tray.tray_manager',
    'smart_media_icon.tray.file_watcher',
    'smart_media_icon.tray.processing_engine',
    'smart_media_icon.tray.settings_manager',
    'smart_media_icon.tray.notification_system',
    'smart_media_icon.tray.gui.settings_dialog',
    'smart_media_icon.tray.gui.about_dialog',
    'smart_media_icon.tray.gui.progress_dialog',
    
    # Existing core modules
    'smart_media_icon.core.icon_setter',
    'smart_media_icon.core.ffmpeg_handler',
    'smart_media_icon.core.windows_icons',
    'smart_media_icon.apis.media_api',
    'smart_media_icon.utils.config',
    
    # PyQt5 components (only what we need)
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.sip',
    
    # External dependencies
    'watchdog',
    'watchdog.observers',
    'watchdog.events',
    'watchdog.observers.winapi',
    'requests',
    'requests.packages.urllib3',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    
    # Windows-specific
    'winreg',
    'win32api',
    'win32con',
    'win32gui',
    'winsound',
]

# Data files to include
datas = []

# Add resources if they exist
if resources_path.exists():
    datas.append((str(resources_path / 'icons'), 'resources/icons'))
    datas.append((str(resources_path / 'ui'), 'resources/ui'))
    datas.append((str(resources_path / 'config'), 'resources/config'))

# Add configuration files
config_files = ['config.json', 'requirements.txt', 'README.md', 'LICENSE']
for config_file in config_files:
    config_path = project_root / config_file
    if config_path.exists():
        datas.append((str(config_path), '.'))

# FFmpeg binaries (if available)
ffmpeg_dir = external_path / 'ffmpeg'
if ffmpeg_dir.exists():
    for exe in ['ffmpeg.exe', 'ffprobe.exe']:
        exe_path = ffmpeg_dir / exe
        if exe_path.exists():
            datas.append((str(exe_path), 'external/ffmpeg'))

# Binaries (external DLLs)
binaries = []

# Analysis configuration
a = Analysis(
    [str(src_path / 'smart_media_icon' / 'tray' / 'main.py')],
    pathex=[str(src_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'doctest',
        'pdb',
        'unittest',
        'test',
        
        # Exclude unused PyQt5 modules
        'PyQt5.Qt3DAnimation',
        'PyQt5.Qt3DCore',
        'PyQt5.Qt3DExtras',
        'PyQt5.Qt3DInput',
        'PyQt5.Qt3DLogic',
        'PyQt5.Qt3DRender',
        'PyQt5.QtBluetooth',
        'PyQt5.QtChart',
        'PyQt5.QtDataVisualization',
        'PyQt5.QtDesigner',
        'PyQt5.QtHelp',
        'PyQt5.QtLocation',
        'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtNetwork',
        'PyQt5.QtNfc',
        'PyQt5.QtOpenGL',
        'PyQt5.QtPositioning',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtQml',
        'PyQt5.QtQuick',
        'PyQt5.QtQuickWidgets',
        'PyQt5.QtSensors',
        'PyQt5.QtSerialPort',
        'PyQt5.QtSql',
        'PyQt5.QtSvg',
        'PyQt5.QtTest',
        'PyQt5.QtWebChannel',
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebKit',
        'PyQt5.QtWebKitWidgets',
        'PyQt5.QtWebSockets',
        'PyQt5.QtWinExtras',
        'PyQt5.QtXml',
        'PyQt5.QtXmlPatterns',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files and optimize
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='smart_media_icon_tray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX if available
    console=False,  # Hide console window for tray app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(resources_path / 'icons' / 'app_icon.ico') if (resources_path / 'icons' / 'app_icon.ico').exists() else None,
    version=str(project_root / 'version_info.txt') if (project_root / 'version_info.txt').exists() else None,
    uac_admin=False,  # Don't require admin privileges
    uac_uiaccess=False,
)

# Create distribution directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='smart_media_icon_tray'
)