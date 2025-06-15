# Media Iconer

A Windows desktop utility that automatically sets folder icons for media content.

## Features

- Monitors a root "Media" folder (and all its subfolders) in the background
- Detects folders containing video or audio files
- Parses folder names to infer the media title
- Fetches poster images from TMDB or OMDB
- Sets the poster as the folder icon using desktop.ini
- Runs as a background service (auto-starts on login)

## Installation

### Prerequisites

- Python 3.7 or higher
- Windows 10 or higher
- API key from TMDB (https://www.themoviedb.org/settings/api) or OMDB (https://www.omdbapi.com/apikey.aspx)

### Setup

1. Clone or download this repository.

2. Create a virtual environment:
   ```
   cd media-iconer
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```
   .\venv\Scripts\Activate.ps1
   ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

5. Configure the application:
   - Create a configuration file in one of these locations:
     - `config.json` in the application directory
     - `%USERPROFILE%\.media_iconer\config.json`

   Example `config.json`:
   ```json
   {
       "MEDIA_ROOT_DIR": "D:\\Media",
       "TMDB_API_KEY": "your_tmdb_api_key",
       "OMDB_API_KEY": "your_omdb_api_key",
       "SCAN_ON_START": true,
       "DEBOUNCE_TIME": 5.0
   }
   ```

## Usage

### Running Manually

To start the application:

```
python main.py
```

You can specify a custom configuration file:

```
python main.py --config path\to\config.json
```

### Setting Up Auto-Start on Login

#### Method 1: Task Scheduler

1. Open Task Scheduler
2. Create a new Task with these settings:
   - General Tab:
     - Name: "Media Iconer"
     - Run whether user is logged on or not
     - Run with highest privileges
   - Triggers Tab:
     - New Trigger: At log on
   - Actions Tab:
     - New Action: Start a program
     - Program/script: `<path_to_python_exe>` (e.g., `C:\Python39\python.exe`)
     - Add arguments: `main.py`
     - Start in: `<path_to_media_iconer_directory>`

#### Method 2: Startup Folder

1. Create a batch file (media_iconer.bat) with the following content:
   ```batch
   @echo off
   cd /d "C:\path\to\media-iconer"
   "C:\path\to\media-iconer\venv\Scripts\python.exe" main.py
   ```

2. Place a shortcut to this batch file in your Startup folder:
   `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`

### Installing as a Windows Service

1. Install NSSM (Non-Sucking Service Manager) from https://nssm.cc/

2. Open a Command Prompt as Administrator and run:
   ```
   nssm install MediaIconer
   ```

3. In the NSSM dialog:
   - Path: `<path_to_python_exe>` (e.g., `C:\path\to\media-iconer\venv\Scripts\python.exe`)
   - Startup directory: `<path_to_media_iconer_directory>`
   - Arguments: `main.py`

4. Set appropriate service name and description, then click "Install service"

## Folder Structure

```
media-iconer/
├── main.py             # Main entry point, starts watcher service
├── media_watcher.py    # Monitors folder changes
├── media_api.py        # Fetches poster from TMDB/OMDB
├── win_icon.py         # Desktop.ini and attribute setter
├── config.py           # Configuration handling
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Troubleshooting

### Folder Icons Not Showing

1. Make sure the folder has the "System" and "Read-only" attributes.
2. Check that "desktop.ini" exists in the folder and has "System" and "Hidden" attributes.
3. Try restarting Windows Explorer:
   - Press Ctrl+Shift+Esc to open Task Manager
   - Find "Windows Explorer" in the Processes tab
   - Right-click and select "Restart"

### API Issues

1. Verify your API keys are correct.
2. Check your internet connection.
3. The TMDB and OMDB APIs have rate limits, so you might be temporarily blocked if you make too many requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
