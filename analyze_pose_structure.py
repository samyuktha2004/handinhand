#!/usr/bin/env python3
"""Analyze pose structure in signatures."""
import json
import numpy as np

with open('assets/signatures/asl/hello_0.json') as f:
    sig = json.load(f)

frame = sig['pose_data'][0]
pose = np.array(frame['pose'])
face = np.array(frame['face'])

print('=== POSE (6 landmarks) ===')
labels = ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist']
for i, (label, pt) in enumerate(zip(labels, pose)):
    print(f'  {i}: {label} = ({pt[0]:.3f}, {pt[1]:.3f})')

# Calculate current shoulder width
sw = np.linalg.norm(pose[1][:2] - pose[0][:2])
print()
print(f'Shoulder width: {sw:.4f} (normalized units)')
print(f'In 640px frame: {sw * 640:.1f}px')
print(f'Target: 100px')
print(f'Scale factor needed: {100 / (sw * 640):.3f}')

print()
print('=== FACE (4 landmarks) ===')
for i, pt in enumerate(face):
    print(f'  {i}: ({pt[0]:.3f}, {pt[1]:.3f})')

# Check if face is within head region relative to shoulders
shoulder_center_y = (pose[0][1] + pose[1][1]) / 2
print()
print(f'Shoulder center Y: {shoulder_center_y:.3f}')
print(f'Face Y range: {face[:, 1].min():.3f} to {face[:, 1].max():.3f}')
if face[:, 1].max() < shoulder_center_y:
    print('✅ Face is above shoulders (as expected)')
