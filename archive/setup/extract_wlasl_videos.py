#!/usr/bin/env python3
"""
Extract videos from WLASL dataset for specific words.
Copies .mp4 files to assets/raw_videos/lexicon/
"""

import json
import shutil
import os
from pathlib import Path

# Target words
TARGET_WORDS = ['HELLO', 'YOU', 'GO', 'WHERE']

# Paths
WLASL_JSON = 'assets/wlasl_data/WLASL_v0.3.json'
WLASL_VIDEOS = 'assets/wlasl_data'  # Main dataset folder
OUTPUT_DIR = 'assets/raw_videos/lexicon'

print("=" * 60)
print("WLASL Video Extractor")
print("=" * 60)

# Load WLASL JSON
print(f"\n📖 Loading {WLASL_JSON}...")
with open(WLASL_JSON, 'r') as f:
    wlasl_data = json.load(f)

print(f"✓ Loaded {len(wlasl_data)} entries")

# Find video IDs for target words
print(f"\n🔍 Finding videos for: {TARGET_WORDS}")

video_map = {}
for entry in wlasl_data:
    gloss = entry.get('gloss', '').upper()
    
    if gloss in TARGET_WORDS:
        if gloss not in video_map:
            video_map[gloss] = []
        
        # Extract video IDs from instances
        for instance in entry.get('instances', []):
            video_id = instance.get('video_id')
            if video_id:
                video_map[gloss].append(video_id)

# Display found videos
print(f"\n📹 Found videos:")
total_videos = 0
for word in TARGET_WORDS:
    count = len(video_map.get(word, []))
    print(f"  {word}: {count} video(s)")
    total_videos += count

if total_videos == 0:
    print("❌ No videos found!")
    exit(1)

# Create output directory
output_path = Path(OUTPUT_DIR)
output_path.mkdir(parents=True, exist_ok=True)
print(f"\n📁 Output directory: {output_path.absolute()}")

# Copy videos
print(f"\n📋 Copying {total_videos} video(s)...")

copied = 0
failed = 0

for word, video_ids in video_map.items():
    for video_id in video_ids:
        # Video file is named like: 00000.mp4
        src_file = Path(WLASL_VIDEOS) / f"{video_id}.mp4"
        dst_file = output_path / f"{word}_{video_id}.mp4"
        
        if src_file.exists():
            try:
                shutil.copy2(src_file, dst_file)
                print(f"  ✓ {word}_{video_id}.mp4")
                copied += 1
            except Exception as e:
                print(f"  ✗ {word}_{video_id}.mp4 - {e}")
                failed += 1
        else:
            print(f"  ✗ {word}_{video_id}.mp4 - File not found")
            failed += 1

print(f"\n✓ Copied: {copied} videos")
if failed > 0:
    print(f"✗ Failed: {failed} videos")

print("\n" + "=" * 60)
print("Ready to extract signatures from copied videos")
print("=" * 60)
print(f"\nNext: python3 extract_signatures.py")
