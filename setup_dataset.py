#!/usr/bin/env python3
"""
Extract specific words from WLASL dataset and copy their videos to lexicon folder.
"""

import json
import os
import shutil
from pathlib import Path

# Target words to extract
TARGET_WORDS = ['HELLO', 'YOU', 'GO', 'WHERE']

# Paths
WLASL_JSON = 'assets/wlasl_data/WLASL_v0.3.json'
WLASL_VIDEOS_BASE = 'assets/wlasl_data'
OUTPUT_DIR = 'assets/raw_videos/lexicon'

def find_videos_for_words(json_path, words):
    """Find video IDs for specified words in WLASL dataset."""
    print(f"Reading {json_path}...")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    word_videos = {}
    
    for entry in data:
        gloss = entry['gloss'].upper()
        
        if gloss in words:
            if gloss not in word_videos:
                word_videos[gloss] = []
            
            # Extract video IDs from instances
            for instance in entry.get('instances', []):
                video_id = instance.get('video_id')
                if video_id:
                    word_videos[gloss].append(video_id)
    
    return word_videos

def find_video_files(video_dir, video_ids):
    """Find .mp4 files matching video IDs in dataset folder."""
    found_files = {}
    
    print(f"\nSearching for video files in {video_dir}...")
    
    # Common naming patterns: video_id.mp4, VIDEO_ID.mp4, etc.
    for root, dirs, files in os.walk(video_dir):
        for file in files:
            if file.endswith('.mp4'):
                # Extract video ID from filename (remove .mp4 and extension)
                base_name = file.replace('.mp4', '')
                
                # Check if this ID matches any we're looking for
                for vid_id in video_ids:
                    if base_name == vid_id or base_name == str(vid_id):
                        found_files[vid_id] = os.path.join(root, file)
                        break
    
    return found_files

def copy_videos(word_videos, wlasl_base, output_dir):
    """Copy videos to lexicon folder, organized by word."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    total_copied = 0
    
    for word, video_ids in sorted(word_videos.items()):
        print(f"\n{word}: {len(video_ids)} video(s)")
        
        for video_id in video_ids:
            # Find the video file
            video_files = find_video_files(wlasl_base, [video_id])
            
            if video_id in video_files:
                src = video_files[video_id]
                # Name: word_videoid.mp4
                dst_name = f"{word}_{video_id}.mp4"
                dst = os.path.join(output_dir, dst_name)
                
                try:
                    print(f"  Copying {video_id}: {os.path.basename(src)} → {dst_name}")
                    shutil.copy2(src, dst)
                    total_copied += 1
                except Exception as e:
                    print(f"  ERROR copying {video_id}: {e}")
            else:
                print(f"  NOT FOUND: {video_id}")
    
    return total_copied

def main():
    print("=" * 60)
    print("WLASL Dataset Video Extractor")
    print("=" * 60)
    
    # Check if JSON exists
    if not os.path.exists(WLASL_JSON):
        print(f"ERROR: {WLASL_JSON} not found")
        return 1
    
    # Find videos for target words
    word_videos = find_videos_for_words(WLASL_JSON, TARGET_WORDS)
    
    if not word_videos:
        print(f"ERROR: No videos found for {TARGET_WORDS}")
        return 1
    
    print(f"\nFound videos:")
    for word, ids in sorted(word_videos.items()):
        print(f"  {word}: {len(ids)} video(s)")
    
    # Copy videos
    total = copy_videos(word_videos, WLASL_VIDEOS_BASE, OUTPUT_DIR)
    
    print("\n" + "=" * 60)
    print(f"Copied {total} video(s) to {OUTPUT_DIR}")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    exit(main())
