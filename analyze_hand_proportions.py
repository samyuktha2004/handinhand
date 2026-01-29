#!/usr/bin/env python3
"""Analyze real hand proportions from signature data."""
import json
import numpy as np

with open('assets/signatures/asl/hello_0.json') as f:
    sig = json.load(f)

# Find a frame with valid right hand data
for i, frame in enumerate(sig['pose_data']):
    rh = frame.get('right_hand', [])
    if rh and np.abs(np.array(rh)).max() > 0.01:
        rh = np.array(rh)
        print(f'Frame {i} - Valid right hand found')
        
        wrist = rh[0][:2]
        middle_tip = rh[12][:2]
        
        # Hand span in normalized and pixel coords
        span = np.linalg.norm(middle_tip - wrist)
        print(f'Wrist-to-middle span: {span:.4f} normalized = {span * 640:.1f}px')
        
        # Finger spread
        index_tip = rh[8][:2]
        pinky_tip = rh[20][:2]
        spread = np.linalg.norm(index_tip - pinky_tip)
        print(f'Finger spread (index-pinky): {spread:.4f} normalized = {spread * 640:.1f}px')
        
        # Print offsets from wrist in PIXELS (for DEFAULT_HAND_OFFSETS)
        print('\n--- Hand offsets from wrist (in pixels, for 640x480) ---')
        print('Copy these to DEFAULT_HAND_OFFSETS:')
        for j in range(21):
            offset = (rh[j][:2] - wrist) * 640  # Scale to pixels
            print(f'    [{offset[0]:6.1f}, {offset[1]:6.1f}, 0],  # {j}')
        
        break
