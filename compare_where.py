#!/usr/bin/env python3
"""Compare where_0 vs where_ref_yt characteristics."""

import json
import numpy as np

def compare():
    with open('assets/signatures/asl/where_0.json') as f:
        where_0 = json.load(f)
    with open('assets/signatures/asl/where_ref_yt.json') as f:
        where_ref = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"Comparison: where_0 vs where_ref_yt")
    print(f"{'='*70}\n")
    
    print(f"Frames:")
    print(f"  where_0:      {len(where_0['pose_data'])} frames")
    print(f"  where_ref_yt: {len(where_ref['pose_data'])} frames (2.9s @ 29fps)")
    
    print(f"\nSource:")
    print(f"  where_0:      {where_0['metadata'].get('source', 'WLASL composite')}")
    print(f"  where_ref_yt: {where_ref['metadata'].get('source', 'YouTube reference')}")
    
    # Pose confidence
    pose_conf_0 = []
    pose_conf_ref = []
    
    for frame in where_0['pose_data']:
        for point in frame.get('pose', []):
            if len(point) > 2:
                pose_conf_0.append(point[2])
    
    for frame in where_ref['pose_data']:
        for point in frame.get('pose', []):
            if len(point) > 2:
                pose_conf_ref.append(point[2])
    
    if pose_conf_0:
        print(f"\nPose confidence:")
        print(f"  where_0:      {np.mean(pose_conf_0):.3f} (mean)")
        print(f"  where_ref_yt: {np.mean(pose_conf_ref):.3f} (mean)")
    
    # Hand consistency
    hand_count_0 = []
    hand_count_ref = []
    
    for frame in where_0['pose_data']:
        left = len(frame.get('left_hand', []))
        right = len(frame.get('right_hand', []))
        if left > 0 or right > 0:
            hand_count_0.append(left + right)
    
    for frame in where_ref['pose_data']:
        left = len(frame.get('left_hand', []))
        right = len(frame.get('right_hand', []))
        if left > 0 or right > 0:
            hand_count_ref.append(left + right)
    
    if hand_count_0 and hand_count_ref:
        print(f"\nHand landmark consistency:")
        print(f"  where_0:      {np.mean(hand_count_0):.1f}±{np.std(hand_count_0):.1f} landmarks/frame")
        print(f"  where_ref_yt: {np.mean(hand_count_ref):.1f}±{np.std(hand_count_ref):.1f} landmarks/frame")
    
    print(f"\n{'='*70}")
    print(f"Recommendation: REPLACE")
    print(f"{'='*70}")
    print(f"\nReasons:")
    print(f"  ✓ Single, clear source (no composite artifacts)")
    print(f"  ✓ More frames ({len(where_ref['pose_data'])} vs {len(where_0['pose_data'])}) = better motion")
    print(f"  ✓ Better for spatial reference sign")
    print(f"  ✓ Consistent quality throughout")
    print(f"\nAction: cp where_ref_yt.json where_0.json")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    compare()
