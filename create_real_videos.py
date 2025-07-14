#!/usr/bin/env python3
"""
Create real video files for all movie folders to enable FFmpeg artwork embedding.
"""

import os
import subprocess
import sys

def create_real_video_files():
    """Create real video files for all movie folders."""
    base_path = r"d:\PROJECTS AND FILES\CustomIcon\test_media"
    
    # Movie folders (single media files)
    movies = [
        "Avengers",
        "Interstellar", 
        "SpiritedAway",
        "TheMatrix",
        "YourName"
    ]
    
    print("Creating real video files for movies...")
    
    for movie in movies:
        movie_path = os.path.join(base_path, movie)
        video_file = os.path.join(movie_path, f"{movie}.mp4")
        
        # Remove dummy file if it exists
        if os.path.exists(video_file):
            os.remove(video_file)
        
        print(f"Creating real video: {movie}.mp4")
        try:
            # Create a 5-second test video with some pattern
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"testsrc=duration=5:size=320x240:rate=1",
                "-f", "lavfi", "-i", f"sine=frequency=1000:duration=5",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-c:a", "aac",
                video_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✓ Created: {movie}.mp4")
            else:
                print(f"  ✗ Failed to create {movie}.mp4: {result.stderr}")
        except Exception as e:
            print(f"  ✗ Error creating {movie}.mp4: {e}")
    
    print("\nReal video files creation complete!")

if __name__ == "__main__":
    create_real_video_files()
