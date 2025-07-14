#!/usr/bin/env python3
"""
Smart Media Icon System - Usage Examples

This script demonstrates various ways to use the Smart Media Icon System
for automatic media organization and icon management.
"""

import sys
import logging
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from smart_media_icon import SmartIconSetter, Config

def setup_logging():
    """Setup basic logging for examples."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )

def example_basic_usage():
    """Example 1: Basic usage with default configuration."""
    print("🎬 Example 1: Basic Usage")
    print("-" * 40)
    
    try:
        # Load default configuration
        config = Config()
        
        # Initialize the system
        setter = SmartIconSetter(config)
        
        # Create a sample media directory for demo
        sample_dir = Path("sample_media")
        sample_dir.mkdir(exist_ok=True)
        
        # Create sample TV series structure
        series_dir = sample_dir / "GameOfThrones"
        series_dir.mkdir(exist_ok=True)
        season_dir = series_dir / "Season1"
        season_dir.mkdir(exist_ok=True)
        (season_dir / "episode01.mp4").write_text("Sample episode")
        
        # Create sample movie structure  
        movie_dir = sample_dir / "Inception"
        movie_dir.mkdir(exist_ok=True)
        (movie_dir / "Inception.mp4").write_text("Sample movie")
        
        print(f"📁 Created sample media at: {sample_dir.resolve()}")
        
        # Process the sample directory
        success_count = setter.process_media_collection(str(sample_dir))
        print(f"✅ Processed {success_count} items successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_custom_config():
    """Example 2: Using custom configuration."""
    print("\n🔧 Example 2: Custom Configuration")
    print("-" * 40)
    
    try:
        # Create custom configuration
        config = Config()
        config.USE_MOCK_API = True  # Use mock API for demo
        config.USE_CACHE = False    # Disable caching for demo
        
        print("⚙️  Using custom configuration:")
        print(f"   - Mock API: {config.USE_MOCK_API}")
        print(f"   - Caching: {config.USE_CACHE}")
        
        # Initialize with custom config
        setter = SmartIconSetter(config)
        
        # Demo media type detection
        sample_series = "sample_media/GameOfThrones"
        sample_movie = "sample_media/Inception"
        
        if Path(sample_series).exists():
            media_type = setter.determine_media_type(sample_series)
            print(f"📺 {sample_series} detected as: {media_type}")
        
        if Path(sample_movie).exists():
            media_type = setter.determine_media_type(sample_movie) 
            print(f"🎬 {sample_movie} detected as: {media_type}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_api_usage():
    """Example 3: Direct API usage for poster fetching."""
    print("\n🌐 Example 3: Direct API Usage") 
    print("-" * 40)
    
    try:
        from smart_media_icon.apis import MediaAPI
        
        config = Config()
        config.USE_MOCK_API = True  # Use mock for demo
        
        api = MediaAPI(config)
        
        # Fetch poster for a movie
        print("🎬 Fetching movie poster...")
        movie_poster = api.get_poster("The Matrix", is_tv_show=False)
        
        if movie_poster:
            print(f"✅ Movie poster fetched: {len(movie_poster)} bytes")
        else:
            print("❌ No movie poster found")
        
        # Fetch poster for a TV show
        print("📺 Fetching TV show poster...")
        tv_poster = api.get_poster("Breaking Bad", is_tv_show=True)
        
        if tv_poster:
            print(f"✅ TV poster fetched: {len(tv_poster)} bytes")
        else:
            print("❌ No TV poster found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_error_handling():
    """Example 4: Proper error handling."""
    print("\n⚠️  Example 4: Error Handling")
    print("-" * 40)
    
    try:
        # Try to process non-existent directory
        config = Config()
        setter = SmartIconSetter(config)
        
        nonexistent_dir = "this_directory_does_not_exist"
        print(f"🔍 Attempting to process: {nonexistent_dir}")
        
        try:
            success_count = setter.process_media_collection(nonexistent_dir)
            print(f"✅ Processed {success_count} items")
        except FileNotFoundError:
            print("❌ Directory not found (handled gracefully)")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        # Try invalid configuration
        print("🔧 Testing invalid configuration...")
        try:
            invalid_config = Config("nonexistent_config.json")
        except FileNotFoundError:
            print("❌ Config file not found (handled gracefully)")
        except Exception as e:
            print(f"❌ Config error: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def cleanup_demo():
    """Clean up demo files."""
    print("\n🧹 Cleaning up demo files...")
    
    import shutil
    sample_dir = Path("sample_media")
    
    if sample_dir.exists():
        shutil.rmtree(sample_dir)
        print("✅ Demo files cleaned up")

def main():
    """Run all examples."""
    print("🎬 Smart Media Icon System - Usage Examples")
    print("=" * 60)
    
    setup_logging()
    
    try:
        example_basic_usage()
        example_custom_config() 
        example_api_usage()
        example_error_handling()
        
    finally:
        cleanup_demo()
    
    print("\n✅ All examples completed!")
    print("\n📚 Next steps:")
    print("   - Review the API documentation in docs/API.md")
    print("   - Configure your API keys in config.json")
    print("   - Run on your actual media directory")

if __name__ == "__main__":
    main()
