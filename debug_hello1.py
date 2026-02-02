#!/usr/bin/env python3
"""Debug hello_1 normalization issue."""
import json
import numpy as np
from skeleton_drawer import extract_landmarks_from_signature

# Test hello_1 normalization
with open('assets/signatures/asl/hello_1.json') as f:
    sig = json.load(f)

# Raw extraction
frames_raw = extract_landmarks_from_signature(sig, normalize_to_reference=False)
# Normalized extraction
frames_norm = extract_landmarks_from_signature(sig, normalize_to_reference=True)

# Compare frame 0
pose_raw = frames_raw[0]['pose']
pose_norm = frames_norm[0]['pose']

sw_raw = np.linalg.norm(pose_raw[1][:2] - pose_raw[0][:2])
sw_norm = np.linalg.norm(pose_norm[1][:2] - pose_norm[0][:2])

print(f'hello_1 Frame 0:')
print(f'  Raw shoulder width: {sw_raw:.1f}px')
print(f'  Normalized shoulder width: {sw_norm:.1f}px (target: 100px)')
print(f'  Scale factor applied: {100/sw_raw:.2f}x')
print()
print(f'  Raw left shoulder: ({pose_raw[0][0]:.1f}, {pose_raw[0][1]:.1f})')
print(f'  Norm left shoulder: ({pose_norm[0][0]:.1f}, {pose_norm[0][1]:.1f})')
print(f'  Raw right shoulder: ({pose_raw[1][0]:.1f}, {pose_raw[1][1]:.1f})')
print(f'  Norm right shoulder: ({pose_norm[1][0]:.1f}, {pose_norm[1][1]:.1f})')

# Compare with hello_0
with open('assets/signatures/asl/hello_0.json') as f:
    sig0 = json.load(f)

frames0_norm = extract_landmarks_from_signature(sig0, normalize_to_reference=True)
pose0_norm = frames0_norm[0]['pose']
sw0_norm = np.linalg.norm(pose0_norm[1][:2] - pose0_norm[0][:2])
print(f'\nhello_0 normalized shoulder width: {sw0_norm:.1f}px')
