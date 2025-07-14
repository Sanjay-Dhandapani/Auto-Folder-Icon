#!/usr/bin/env python3
"""
Create a fresh test media structure with TV series and movies.
"""

import os
import subprocess
import sys

def create_test_structure():
    """Create a comprehensive test media structure."""
    base_path = r"d:\PROJECTS AND FILES\CustomIcon\test_media"
    
    # TV Series (should get folder icons)
    tv_series = [
        ("GameOfThrones", ["Season1", "Season2"]),
        ("StrangerThings", ["Season1", "Season2", "Season3"]),
        ("TheOffice", ["Season1", "Season2"]),
        ("BreakingBad", ["Season1", "Season2"]),
        ("AttackOnTitan", ["Season1", "Season2"]),
        ("Naruto", ["Season1"])
    ]
    
    # Movies (should get artwork embedded)
    movies = [
        "Inception",
        "Interstellar", 
        "YourName",
        "SpiritedAway",
        "Avengers",
        "TheMatrix"
    ]
    
    print("Creating TV series folders...")
    for show, seasons in tv_series:
        show_path = os.path.join(base_path, show)
        os.makedirs(show_path, exist_ok=True)
        
        for season in seasons:
            season_path = os.path.join(show_path, season)
            os.makedirs(season_path, exist_ok=True)
            
            # Create dummy episode files
            for i in range(1, 4):  # 3 episodes per season
                episode_file = os.path.join(season_path, f"episode{i:02d}.mp4")
                with open(episode_file, 'w') as f:
                    f.write(f"Dummy episode file for {show} {season} Episode {i}")
        
        print(f"  Created: {show}")
    
    print("\nCreating movie folders...")
    for movie in movies:
        movie_path = os.path.join(base_path, movie)
        os.makedirs(movie_path, exist_ok=True)
        
        # Create a dummy movie file
        movie_file = os.path.join(movie_path, f"{movie}.mp4")
        with open(movie_file, 'w') as f:
            f.write(f"Dummy movie file for {movie}")
        
        print(f"  Created: {movie}")
    
    print(f"\nTest media structure created at: {base_path}")
    return base_path

def create_real_video_files(base_path):
    """Create real video files for testing FFmpeg artwork embedding."""
    print("\nCreating real video files for FFmpeg testing...")
    
    # Create one real video file per category for testing
    test_videos = [
        os.path.join(base_path, "Inception", "Inception.mp4"),
        os.path.join(base_path, "GameOfThrones", "Season1", "episode01.mp4")
    ]
    
    for video_path in test_videos:
        print(f"Creating real video: {video_path}")
        try:
            # Create a 5-second test video
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc=duration=5:size=320x240:rate=1",
                "-c:v", "libx264", "-preset", "ultrafast",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✓ Created: {os.path.basename(video_path)}")
            else:
                print(f"  ✗ Failed to create {os.path.basename(video_path)}: {result.stderr}")
        except Exception as e:
            print(f"  ✗ Error creating {os.path.basename(video_path)}: {e}")

if __name__ == "__main__":
    base_path = create_test_structure()
    create_real_video_files(base_path)
    print("\nFresh test media structure is ready!")
    print(f"Location: {base_path}")
