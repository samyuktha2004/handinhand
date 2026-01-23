#!/usr/bin/env python3
"""
Create synthetic test videos for sign language words.
Used to test the extraction and verification pipeline without needing full dataset.
"""

import cv2
import numpy as np
from pathlib import Path

# Target words
TARGET_WORDS = ['HELLO', 'YOU', 'GO', 'WHERE']
OUTPUT_DIR = Path('assets/raw_videos/lexicon')

# Video parameters
FPS = 30
DURATION = 2  # seconds
FRAME_COUNT = FPS * DURATION
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

print("=" * 60)
print("Test Video Generator")
print("=" * 60)

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"\n📁 Creating videos in: {OUTPUT_DIR.absolute()}")

# Create one test video per word
for word in TARGET_WORDS:
    filename = OUTPUT_DIR / f"{word}_test_001.mp4"
    
    print(f"\n🎬 Creating {word}...")
    
    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(filename), fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT))
    
    # Generate frames with moving elements to simulate sign language
    for frame_idx in range(FRAME_COUNT):
        # Create blank frame
        frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        frame[:] = (240, 240, 240)  # Light gray background
        
        # Add text label
        cv2.putText(frame, word, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        
        # Add moving circles to simulate hand movement
        x = int(200 + 100 * np.sin(frame_idx / 10))
        y = int(250 + 80 * np.cos(frame_idx / 10))
        cv2.circle(frame, (x, y), 30, (0, 0, 255), -1)  # Right hand (red)
        
        x2 = int(400 + 100 * np.cos(frame_idx / 10))
        y2 = int(250 + 80 * np.sin(frame_idx / 10))
        cv2.circle(frame, (x2, y2), 30, (255, 0, 0), -1)  # Left hand (blue)
        
        # Add frame counter
        cv2.putText(frame, f"Frame: {frame_idx + 1}/{FRAME_COUNT}", (20, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
        
        out.write(frame)
    
    out.release()
    print(f"  ✓ Created: {filename.name} ({FRAME_COUNT} frames)")

print("\n" + "=" * 60)
print("Test videos created successfully!")
print("=" * 60)
print("\nNext: python3 extract_signatures.py")
