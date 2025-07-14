# Smart Media Icon System

A Windows desktop utility that automatically sets custom icons for TV series folders and embeds artwork in movie files.

## 🌟 Features

### Smart Detection
- **Automatically detects media type:**
  - **TV Series**: Folders with season/episode subdirectories → Gets custom folder icons
  - **Movies**: Folders with single media files → Gets artwork embedded in video files

### Dual Icon Strategy
- **📺 TV Series**: Sets folder icons using Windows `desktop.ini` system
- **🎬 Movies**: Embeds poster artwork directly into video files using FFmpeg

### Multi-API Poster Fetching
- **TMDB** (The Movie Database) - Primary source for movies and TV shows
- **OMDb** (Open Movie Database) - Backup for movies and TV shows  
- **TVmaze** - Specialized TV show database
- **AniList** - Anime and manga database
- **Mock API** - Generates placeholder posters for testing

### Professional Benefits
- **Windows Explorer**: TV series folders display custom poster icons
- **Media Players**: Movies show embedded artwork (VLC, Windows Media Player, etc.)
- **File Properties**: Right-click movie files show poster thumbnails
- **Media Centers**: Plex, Jellyfin, Emby can use embedded artwork
- **Organization**: Visual identification of media content at a glance

## 🛠️ Technical Implementation

### For TV Series (Folder Icons)
```
Series Folder/
├── desktop.ini          # Windows folder icon configuration
├── folder.ico           # Converted poster in .ico format
├── poster.jpg           # Original poster image
├── Season1/
│   ├── episode01.mp4
│   └── episode02.mp4
└── Season2/
    ├── episode01.mp4
    └── episode02.mp4
```

### For Movies (Embedded Artwork)
```
Movie Folder/
├── MovieTitle.mp4       # Video file with embedded poster artwork
├── MovieTitle.mp4.backup # Backup of original file
└── poster.jpg           # Original poster image
```

## 📋 Prerequisites

- **Python 3.7+**
- **Windows 10+**
- **FFmpeg** (for movie artwork embedding)
- **API keys** (optional, system works with mock data)

## 🚀 Installation

### 1. Install FFmpeg
```powershell
# Using winget (recommended)
winget install "FFmpeg (Essentials Build)"

# Or download from https://ffmpeg.org/download.html
```

### 2. Clone Repository
```bash
git clone https://github.com/yourusername/smart-media-icon-system.git
cd smart-media-icon-system
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure (Optional)
Create `config.json`:
```json
{
    "MEDIA_ROOT_DIR": "D:\\Media",
    "TMDB_API_KEY": "your_tmdb_api_key_here",
    "OMDB_API_KEY": "your_omdb_api_key_here",
    "TVMAZE_API_KEY": "your_tvmaze_api_key_here",
    "ANILIST_API_KEY": "your_anilist_api_key_here",
    "USE_CACHE": true,
    "USE_MOCK_API": false
}
```

## 🎯 Usage

### Quick Start
```bash
# Test on sample media collection
python test_smart_icons.py

# Process specific directory
python smart_icon_setter.py "C:\Path\To\Media"

# Run main application
python main.py
```

### Testing
```bash
# Create fresh test media structure
python create_fresh_test_media.py

# Run complete system test
python test_complete_system.py

# Verify results
python final_verification.py
```

## 📊 How It Works

### 1. Media Type Detection
```python
# Series Detection Logic
if has_season_subdirectories:
    media_type = "series"  → Apply folder icon
    
# Movie Detection Logic  
elif has_single_media_file:
    media_type = "movie"   → Embed artwork with FFmpeg
```

### 2. API Poster Fetching
```python
# Intelligent API selection
if media_type == "series":
    poster = api.get_poster(title, is_tv_show=True)
else:
    poster = api.get_poster(title, is_tv_show=False)
```

### 3. Icon Application
```python
# For TV Series
win_icon.set_folder_icon(series_path, poster_path)
# Creates: desktop.ini + folder.ico

# For Movies  
ffmpeg_setter.embed_artwork_in_media(movie_file, poster_path)
# Embeds poster directly in video file
```

## 📁 Project Structure

```
smart-media-icon-system/
├── main.py                    # Main application entry point
├── smart_icon_setter.py       # Core smart detection logic
├── media_api.py              # Multi-API poster fetching
├── win_icon.py               # Windows folder icon setting
├── ffmpeg_icon_setter.py     # FFmpeg artwork embedding
├── config.py                 # Configuration management
├── test_smart_icons.py       # Smart system testing
├── test_complete_system.py   # End-to-end testing
├── final_verification.py     # Results verification
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🔍 Example Results

### Before Processing
```
Media/
├── GameOfThrones/           # Generic folder icon
│   ├── Season1/
│   └── Season2/
└── Inception/               # Generic folder icon
    └── Inception.mp4        # No embedded artwork
```

### After Processing  
```
Media/
├── GameOfThrones/           # ✅ Custom poster folder icon
│   ├── desktop.ini          # ✅ Windows icon config
│   ├── folder.ico           # ✅ Poster in .ico format
│   ├── poster.jpg           # ✅ Original poster
│   ├── Season1/
│   └── Season2/ 
└── Inception/               # Standard folder (movie inside)
    ├── Inception.mp4        # ✅ Contains embedded poster artwork
    ├── Inception.mp4.backup # ✅ Original backup
    └── poster.jpg           # ✅ Original poster
```

## 🎮 Media Player Benefits

### VLC Media Player
- Displays embedded poster as video thumbnail
- Shows artwork in playlist and media info

### Windows Media Player  
- Shows embedded poster in library view
- Displays artwork during playback

### Plex/Jellyfin/Emby
- Automatically uses embedded artwork
- No need for separate poster files

### File Properties
- Right-click → Properties shows poster thumbnail
- Enhanced file identification

## 🧪 Testing Results

**Latest Test Results: 100% Success Rate**
```
📊 FINAL STATISTICS:
  Total folders processed: 12
  Series folders: 6/6 (100% success)
  Movie folders: 6/6 (100% success)
  Overall success: 12/12 (100%)

✅ SERIES FOLDER ICONS:
  ✅ AttackOnTitan        → ✓ desktop.ini  ✓ folder.ico  ✓ poster.jpg
  ✅ BreakingBad          → ✓ desktop.ini  ✓ folder.ico  ✓ poster.jpg
  ✅ GameOfThrones        → ✓ desktop.ini  ✓ folder.ico  ✓ poster.jpg
  ✅ Naruto               → ✓ desktop.ini  ✓ folder.ico  ✓ poster.jpg
  ✅ StrangerThings       → ✓ desktop.ini  ✓ folder.ico  ✓ poster.jpg
  ✅ TheOffice            → ✓ desktop.ini  ✓ folder.ico  ✓ poster.jpg

🎥 MOVIE FILE ARTWORK:
  ✅ Avengers             → ✓ 125,809 bytes  ✓ artwork embedded
  ✅ Inception            → ✓ 113,138 bytes  ✓ artwork embedded  
  ✅ Interstellar         → ✓ 129,503 bytes  ✓ artwork embedded
  ✅ SpiritedAway         → ✓ 144,816 bytes  ✓ artwork embedded
  ✅ TheMatrix            → ✓ 96,373 bytes   ✓ artwork embedded
  ✅ YourName             → ✓ 92,977 bytes   ✓ artwork embedded
```

## 🔧 Troubleshooting

### FFmpeg Issues
```bash
# Verify FFmpeg installation
ffmpeg -version

# Install if missing
winget install "FFmpeg (Essentials Build)"
```

### Folder Icons Not Showing
1. Restart Windows Explorer: `Ctrl+Shift+Esc` → Restart "Windows Explorer"
2. Check folder attributes: Should have System + Read-only
3. Verify `desktop.ini` exists and has Hidden + System attributes

### API Rate Limits
- The system includes intelligent rate limiting and caching
- Mock API provides fallback when real APIs are unavailable
- Cache prevents repeated API calls for same content

### Supported Video Formats
- `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.mpg`, `.mpeg`

## 🚀 Future Enhancements

- [ ] Real-time folder monitoring
- [ ] Batch processing GUI
- [ ] Additional video format support
- [ ] Custom poster upload option
- [ ] Integration with media servers

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Submit a pull request

## 🙏 Acknowledgments

- **TMDB** for comprehensive movie/TV database
- **FFmpeg** for powerful media processing
- **Pillow** for image manipulation
- **Windows API** for folder icon integration
