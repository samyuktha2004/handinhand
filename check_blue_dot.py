#!/usr/bin/env python3
"""Check for blue dot source - points near origin or missing joints."""

from skeleton_drawer import extract_landmarks_from_signature
import json
import numpy as np

# Check both ASL and BSL hello
for lang, path in [('ASL', 'assets/signatures/asl/hello_0.json'), ('BSL', 'assets/signatures/bsl/hello.json')]:
    with open(path) as f:
        sig = json.load(f)
    
    frames = extract_landmarks_from_signature(sig)
    print(f'=== {lang} ===')
    print(f'Frames: {len(frames)}')
    
    # Check first few frames for patterns
    anomaly_frames = []
    for i, frame in enumerate(frames):
        pose = frame.get('pose')
        lh = frame.get('left_hand')
        rh = frame.get('right_hand')
        
        # Check for points near origin (potential blue dot source)
        for name, arr in [('pose', pose), ('left_hand', lh), ('right_hand', rh)]:
            if arr is not None and len(arr) > 0:
                near_origin = np.sum((np.abs(arr[:, 0]) < 20) & (np.abs(arr[:, 1]) < 20))
                if near_origin > 0:
                    if i not in anomaly_frames:
                        anomaly_frames.append(i)
                    # Print ALL anomaly details
                    idx = np.where((np.abs(arr[:, 0]) < 20) & (np.abs(arr[:, 1]) < 20))[0]
                    print(f'  Frame {i}, {name}: {near_origin} points near (0,0)')
                    print(f'    Indices: {idx}')
                    print(f'    Values: {arr[idx, :2]}')
    
    if not anomaly_frames:
        print(f'  No anomalies found')
    
    # Check skeleton completeness
    f0 = frames[0]
    pose = f0.get('pose')
    if pose is not None:
        print(f'  Pose landmarks: {len(pose)} (expected 6 for partial, 33 for full)')
    
    print()
