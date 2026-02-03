#!/usr/bin/env python3
"""
Test the new skeleton renderer with actual signatures.
"""

import sys
import json
import numpy as np
import cv2
from pathlib import Path
from skeleton_renderer import (
    SkeletonRenderer, 
    SkeletonDrawerCompat as SkeletonDrawer,
    ReferenceBody,
    extract_landmarks_from_signature
)

ASSETS = Path(__file__).parent / "assets"
SIGNATURES = ASSETS / "signatures"


def load_signature(path: Path) -> dict:
    """Load a signature JSON file."""
    with open(path) as f:
        return json.load(f)


def extract_landmarks(signature: dict, frame_idx: int = 0, frame_size: tuple = (640, 480)) -> dict:
    """
    Extract landmarks from signature for a specific frame.
    Converts normalized (0-1) coords to pixel coords.
    """
    # Try "pose_data" first (actual format), then "frames"
    frames = signature.get("pose_data", signature.get("frames", []))
    if not frames or frame_idx >= len(frames):
        return {}
    
    frame = frames[frame_idx]
    width, height = frame_size
    
    landmarks = {}
    
    # Pose (6 points) - may be under "pose" or constructed from body landmarks
    pose_data = frame.get("pose", [])
    if pose_data:
        pose = np.array(pose_data)
        if pose.shape[0] == 6:
            # Scale to pixels
            pose[:, 0] *= width
            pose[:, 1] *= height
            landmarks["pose"] = pose
    
    # Hands (21 points each)
    for hand in ["left_hand", "right_hand"]:
        hand_data = frame.get(hand, [])
        if hand_data:
            hand_arr = np.array(hand_data)
            if hand_arr.shape[0] == 21:
                hand_arr[:, 0] *= width
                hand_arr[:, 1] *= height
                landmarks[hand] = hand_arr
    
    return landmarks


def test_signature(sig_path: Path):
    """Test rendering a single signature."""
    print(f"\nTesting: {sig_path.name}")
    
    sig = load_signature(sig_path)
    frames = sig.get("pose_data", sig.get("frames", []))
    print(f"  Frames: {len(frames)}")
    
    if not frames:
        print("  No frames!")
        return
    
    # Test first, middle, and last frame
    test_indices = [0]
    if len(frames) > 1:
        test_indices.append(len(frames) // 2)
    if len(frames) > 2:
        test_indices.append(len(frames) - 1)
    
    renderer = SkeletonRenderer()
    
    for idx in test_indices:
        landmarks = extract_landmarks(sig, idx)
        
        # Debug info
        pose = landmarks.get("pose")
        lh = landmarks.get("left_hand")
        rh = landmarks.get("right_hand")
        
        print(f"  Frame {idx}:")
        if pose is not None:
            print(f"    Pose: {pose.shape}, range X:[{pose[:,0].min():.0f}-{pose[:,0].max():.0f}], Y:[{pose[:,1].min():.0f}-{pose[:,1].max():.0f}]")
        if lh is not None:
            max_val = np.abs(lh[:,:2]).max()
            print(f"    Left hand: max val = {max_val:.1f} (valid={max_val > 1})")
        if rh is not None:
            max_val = np.abs(rh[:,:2]).max()
            print(f"    Right hand: max val = {max_val:.1f} (valid={max_val > 1})")
        
        # Render
        frame = renderer.draw(landmarks, show_reference=False)
        
        # Save test image
        out_path = ASSETS / "test_render" / f"{sig_path.stem}_frame{idx}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), frame)
        print(f"    Saved: {out_path}")


def main():
    # Find all ASL signatures
    asl_sigs = sorted(SIGNATURES.glob("asl/*.json"))
    bsl_sigs = sorted(SIGNATURES.glob("bsl/*.json"))
    print(f"Found {len(asl_sigs)} ASL, {len(bsl_sigs)} BSL signatures")
    
    # Test key signs: hello, go, where, you
    key_signs = ['hello', 'go', 'where', 'you']
    
    print("\n=== Visual Validation: Key Signs ===")
    for sign in key_signs:
        # Find ASL signature
        asl_match = [s for s in asl_sigs if s.stem.startswith(sign) and '_smoothed' not in s.stem]
        if asl_match:
            test_signature_visual(asl_match[0], "ASL")
        
        # Find BSL signature
        bsl_match = [s for s in bsl_sigs if s.stem == sign]
        if bsl_match:
            test_signature_visual(bsl_match[0], "BSL")
    
    print("\n✓ Done! Check assets/test_render/ for output images")


def test_signature_visual(sig_path: Path, lang: str):
    """Generate visual test output for a signature."""
    print(f"\n{lang} {sig_path.stem}:")
    
    sig = load_signature(sig_path)
    frames = extract_landmarks_as_dicts(sig, frame_width=640, frame_height=480)
    
    if not frames:
        print("  No frames!")
        return
    
    # Test frame 0 and middle frame
    renderer = SkeletonRenderer()
    
    for idx in [0, len(frames) // 2]:
        if idx >= len(frames):
            continue
            
        frame_data = frames[idx]
        
        # Check hand validity
        lh = frame_data.get('left_hand')
        rh = frame_data.get('right_hand')
        lh_valid = lh is not None and np.abs(lh[:, :2]).max() > 1
        rh_valid = rh is not None and np.abs(rh[:, :2]).max() > 1
        
        print(f"  Frame {idx}: LH={'✓' if lh_valid else '○'} RH={'✓' if rh_valid else '○'}")
        
        # Render
        rendered = renderer.draw(frame_data, show_reference=False)
        
        # Save
        out_path = ASSETS / "test_render" / f"{lang}_{sig_path.stem}_frame{idx}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), rendered)


# Import extract_landmarks_as_dicts
from skeleton_renderer import extract_landmarks_as_dicts


if __name__ == "__main__":
    main()
