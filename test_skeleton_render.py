#!/usr/bin/env python3
"""
Test skeleton rendering WITHOUT GUI.
Loads signature and tries to draw skeleton to verify it works.
"""

import json
import numpy as np
import cv2
from pathlib import Path
from skeleton_renderer import SkeletonRenderer, extract_landmarks_as_dicts

def test_render():
    # Load signature
    sig_path = Path("assets/signatures/asl/hello_0.json")
    if not sig_path.exists():
        print(f"❌ Signature not found: {sig_path}")
        return False
    
    with open(sig_path) as f:
        sig = json.load(f)
    
    print(f"✓ Loaded signature: {sig['sign']} ({len(sig['pose_data'])} frames)")
    
    # Extract landmarks (as dict format)
    frames = extract_landmarks_as_dicts(sig, frame_width=640, frame_height=480)
    print(f"✓ Extracted {len(frames)} frames")
    
    # Get first frame
    frame_0 = frames[0]
    print(f"✓ Frame 0 keys: {list(frame_0.keys())}")
    
    # Check what we have
    for key in ['pose', 'left_hand', 'right_hand']:
        if key in frame_0 and frame_0[key] is not None:
            data = frame_0[key]
            print(f"  {key}: {data.shape[0]} points, range X: {data[:, 0].min():.0f}-{data[:, 0].max():.0f}, Y: {data[:, 1].min():.0f}-{data[:, 1].max():.0f}")
    
    # Try to draw on blank canvas using new SkeletonRenderer
    print("\nAttempting to render...")
    renderer = SkeletonRenderer()
    
    try:
        rendered = renderer.draw(frame_0, show_reference=False)
        
        # Count non-zero pixels (skeleton drawn)
        non_zero = np.count_nonzero(rendered)
        print(f"✓ Skeleton rendered: {non_zero} pixels drawn")
        
        if non_zero > 100:
            print("✅ SUCCESS: Skeleton visible!")
            # Save test image
            cv2.imwrite("/tmp/skeleton_test.png", rendered)
            print("   Saved to /tmp/skeleton_test.png")
            return True
        else:
            print("❌ FAIL: Very few pixels drawn (<100)")
            return False
            
    except Exception as e:
        print(f"❌ Error during rendering: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_render()
    exit(0 if result else 1)
