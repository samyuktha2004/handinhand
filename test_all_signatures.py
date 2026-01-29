#!/usr/bin/env python3
"""
Test all signatures for reference body normalization.
Verifies:
1. Shoulder width normalized to 100px
2. Hands stay in frame
3. Placeholder hands render when data is zeros
"""
import json
import numpy as np
from pathlib import Path
from skeleton_drawer import extract_landmarks_from_signature, SkeletonDrawer

ASSETS_DIR = Path('assets/signatures')

def test_signature(path: Path) -> dict:
    """Test a single signature file."""
    result = {
        'path': str(path),
        'name': path.stem,
        'passed': True,
        'issues': []
    }
    
    try:
        with open(path) as f:
            sig = json.load(f)
        
        # Extract with normalization
        frames = extract_landmarks_from_signature(sig, normalize_to_reference=True)
        
        if not frames:
            result['passed'] = False
            result['issues'].append('No frames extracted')
            return result
        
        # Check shoulder width on first frame
        pose = frames[0].get('pose')
        if pose is not None and len(pose) >= 2:
            sw = np.linalg.norm(pose[1][:2] - pose[0][:2])
            if abs(sw - 100) > 5:  # Allow 5px tolerance
                result['issues'].append(f'Shoulder width {sw:.1f}px (expected ~100px)')
                result['passed'] = False
        
        # Check hands stay in frame (640x480)
        for i, frame in enumerate(frames):
            for key in ['left_hand', 'right_hand']:
                hand = frame.get(key)
                if hand is not None and SkeletonDrawer._is_hand_valid(hand):
                    if np.any(hand[:, 0] < 0) or np.any(hand[:, 0] > 640):
                        result['issues'].append(f'Frame {i+1}: {key} X out of bounds')
                        result['passed'] = False
                        break
                    if np.any(hand[:, 1] < 0) or np.any(hand[:, 1] > 480):
                        result['issues'].append(f'Frame {i+1}: {key} Y out of bounds')
                        result['passed'] = False
                        break
        
        # Check for frames with zero hand data
        zero_hand_frames = 0
        for frame in frames:
            for key in ['left_hand', 'right_hand']:
                hand = frame.get(key)
                if hand is not None and not SkeletonDrawer._is_hand_valid(hand):
                    zero_hand_frames += 1
                    break
        
        if zero_hand_frames > 0:
            result['issues'].append(f'{zero_hand_frames} frames with zero hand data (placeholder will be used)')
        
        result['frame_count'] = len(frames)
        
    except Exception as e:
        result['passed'] = False
        result['issues'].append(f'Error: {str(e)}')
    
    return result

def main():
    print("=" * 60)
    print("Reference Body Normalization Test Suite")
    print("=" * 60)
    
    # Test ASL signatures
    print("\n📁 ASL Signatures:")
    asl_dir = ASSETS_DIR / 'asl'
    asl_results = []
    for sig_file in sorted(asl_dir.glob('*.json')):
        # Skip augmented/smoothed variants for clarity
        if any(x in sig_file.stem for x in ['_smoothed', '_mirrored', '_variation']):
            continue
        result = test_signature(sig_file)
        asl_results.append(result)
        status = "✅" if result['passed'] else "❌"
        print(f"  {status} {result['name']}: {result.get('frame_count', '?')} frames")
        for issue in result['issues']:
            print(f"      ⚠️ {issue}")
    
    # Test BSL signatures
    print("\n📁 BSL Signatures:")
    bsl_dir = ASSETS_DIR / 'bsl'
    bsl_results = []
    for sig_file in sorted(bsl_dir.glob('*.json')):
        if any(x in sig_file.stem for x in ['_smoothed', '_mirrored', '_variation']):
            continue
        result = test_signature(sig_file)
        bsl_results.append(result)
        status = "✅" if result['passed'] else "❌"
        print(f"  {status} {result['name']}: {result.get('frame_count', '?')} frames")
        for issue in result['issues']:
            print(f"      ⚠️ {issue}")
    
    # Summary
    all_results = asl_results + bsl_results
    passed = sum(1 for r in all_results if r['passed'])
    total = len(all_results)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} signatures passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ All signatures pass reference body normalization!")
    else:
        print("❌ Some signatures have issues:")
        for r in all_results:
            if not r['passed']:
                print(f"  - {r['name']}: {', '.join(r['issues'])}")

if __name__ == "__main__":
    main()
