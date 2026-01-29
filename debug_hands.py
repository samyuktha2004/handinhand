#!/usr/bin/env python3
"""Debug missing hand issue."""
import json
import numpy as np

with open('assets/signatures/asl/hello_0.json') as f:
    sig = json.load(f)

# Check frame 22 (index 21) for left hand data
frame_22 = sig['pose_data'][21]
left_hand = frame_22.get('left_hand', [])
right_hand = frame_22.get('right_hand', [])

print('Frame 22 analysis:')
print(f'  Left hand landmarks: {len(left_hand)}')
print(f'  Right hand landmarks: {len(right_hand)}')

if left_hand:
    lh = np.array(left_hand)
    print(f'  Left hand Y range: {lh[:,1].min():.3f} to {lh[:,1].max():.3f}')
    print(f'  Left hand off-screen (Y > 1)? {(lh[:,1] > 1).any()}')
    
if right_hand:
    rh = np.array(right_hand)
    print(f'  Right hand Y range: {rh[:,1].min():.3f} to {rh[:,1].max():.3f}')

# Compare frame 54 where both hands visible
frame_54 = sig['pose_data'][53]
left_hand_54 = frame_54.get('left_hand', [])
print(f'\nFrame 54 left hand landmarks: {len(left_hand_54)}')
if left_hand_54:
    lh54 = np.array(left_hand_54)
    print(f'  Left hand Y range: {lh54[:,1].min():.3f} to {lh54[:,1].max():.3f}')

# Check which frames have left hand data
frames_with_left = 0
frames_with_right = 0
for i, frame in enumerate(sig['pose_data']):
    if frame.get('left_hand'):
        frames_with_left += 1
    if frame.get('right_hand'):
        frames_with_right += 1

print(f'\nTotal frames: {len(sig["pose_data"])}')
print(f'Frames with left_hand: {frames_with_left}')
print(f'Frames with right_hand: {frames_with_right}')
