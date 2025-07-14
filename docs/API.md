# API Reference

## Core Classes

### SmartIconSetter

Main orchestration class that determines media type and applies appropriate icon strategy.

```python
from smart_media_icon import SmartIconSetter, Config

# Initialize with config
config = Config('config.json')
setter = SmartIconSetter(config)

# Process a directory
success_count = setter.process_media_collection('/path/to/media')
```

#### Methods

##### `process_media_collection(directory_path: str) -> int`

Processes all media folders in the specified directory.

**Parameters:**
- `directory_path`: Path to the media directory

**Returns:**
- Number of successfully processed items

##### `determine_media_type(folder_path: str) -> str`

Determines if a folder contains a TV series or movie.

**Parameters:**
- `folder_path`: Path to the media folder

**Returns:**
- `"series"` for TV shows with seasons/episodes
- `"movie"` for single media files
- `"unknown"` for unrecognized content

### MediaAPI

Handles fetching posters from multiple APIs with intelligent fallbacks.

```python
from smart_media_icon.apis import MediaAPI
from smart_media_icon.utils import Config

config = Config()
api = MediaAPI(config)

# Get poster for a movie
poster_data = api.get_poster("Inception", is_tv_show=False)

# Get poster for a TV show
poster_data = api.get_poster("Game of Thrones", is_tv_show=True)
```

#### Methods

##### `get_poster(title: str, is_tv_show: bool = False, is_anime: bool = False) -> Optional[bytes]`

Fetches poster image data for the specified title.

**Parameters:**
- `title`: Media title to search for
- `is_tv_show`: Whether to search TV show databases
- `is_anime`: Whether to prioritize anime databases

**Returns:**
- Poster image data as bytes, or None if not found

### Config

Configuration management with validation and defaults.

```python
from smart_media_icon.utils import Config

# Load from file
config = Config('config.json')

# Access configuration
api_key = config.TMDB_API_KEY
cache_dir = config.CACHE_DIR
```

#### Properties

- `TMDB_API_KEY`: TMDB API key
- `OMDB_API_KEY`: OMDb API key  
- `TVMAZE_API_KEY`: TVmaze API key
- `ANILIST_API_KEY`: AniList API key
- `CACHE_DIR`: Cache directory path
- `USE_CACHE`: Enable/disable caching
- `USE_MOCK_API`: Use mock API for testing

## Usage Examples

### Basic Usage

```python
from smart_media_icon import SmartIconSetter, Config

# Load configuration
config = Config('config.json')

# Initialize the system
setter = SmartIconSetter(config)

# Process your media directory
success_count = setter.process_media_collection('C:\\Media')
print(f"Processed {success_count} items successfully")
```

### Custom Configuration

```python
from smart_media_icon.utils import Config

# Create custom config
config = Config()
config.TMDB_API_KEY = "your_api_key_here"
config.USE_MOCK_API = True  # For testing

# Use with SmartIconSetter
setter = SmartIconSetter(config)
```

### Manual API Usage

```python
from smart_media_icon.apis import MediaAPI
from smart_media_icon.utils import Config

config = Config()
api = MediaAPI(config)

# Fetch poster manually
poster_bytes = api.get_poster("The Matrix", is_tv_show=False)

if poster_bytes:
    with open("poster.jpg", "wb") as f:
        f.write(poster_bytes)
```

## Error Handling

The system includes comprehensive error handling:

```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

try:
    setter = SmartIconSetter(config)
    result = setter.process_media_collection(media_dir)
except FileNotFoundError:
    print("Media directory not found")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration File Format

```json
{
    "TMDB_API_KEY": "your_tmdb_api_key",
    "OMDB_API_KEY": "your_omdb_api_key",
    "TVMAZE_API_KEY": "your_tvmaze_api_key", 
    "ANILIST_API_KEY": "your_anilist_api_key",
    "CACHE_DIR": "%USERPROFILE%\\.smart_media_icon\\cache",
    "USE_CACHE": true,
    "USE_MOCK_API": false
}
```
