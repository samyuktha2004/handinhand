#!/usr/bin/env python3
"""Debug normalized skeleton rendering."""
import cv2
import json
import numpy as np
from skeleton_drawer import SkeletonDrawer, extract_landmarks_from_signature

# Load signature
with open('assets/signatures/asl/hello_0.json') as f:
    sig = json.load(f)

# Extract with normalization
frames = extract_landmarks_from_signature(sig)

print(f'Loaded {len(frames)} frames')
print(f'\nFrame 0 landmark keys: {frames[0].keys()}')

for key, val in frames[0].items():
    if val is not None:
        arr = np.array(val)
        print(f'  {key}: shape={arr.shape}')
        print(f'    X range: {arr[:,0].min():.1f} to {arr[:,0].max():.1f}')
        print(f'    Y range: {arr[:,1].min():.1f} to {arr[:,1].max():.1f}')

# Check pose specifically
pose = frames[0]['pose']
print(f'\nPose landmarks (6 points):')
for i, p in enumerate(pose):
    print(f'  {i}: ({p[0]:.1f}, {p[1]:.1f})')

# Shoulder width after normalization
sw = np.linalg.norm(pose[1][:2] - pose[0][:2])
print(f'\nShoulder width: {sw:.1f}px (target: 100px)')
