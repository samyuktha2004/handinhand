#!/usr/bin/env python3
"""Test reference body normalization."""
import json
import numpy as np
from skeleton_drawer import extract_landmarks_from_signature, REFERENCE_SHOULDER_WIDTH

# Test with and without normalization
with open('assets/signatures/asl/hello_0.json') as f:
    sig = json.load(f)

print('=== REFERENCE BODY NORMALIZATION TEST ===')
print()

# Without normalization
frames_raw = extract_landmarks_from_signature(sig, normalize_to_reference=False)
pose_raw = frames_raw[0]['pose']
sw_raw = np.linalg.norm(pose_raw[1][:2] - pose_raw[0][:2])

print('WITHOUT normalization:')
print(f'  Shoulder width: {sw_raw:.1f}px')
print(f'  Shoulder center: ({(pose_raw[0][0] + pose_raw[1][0])/2:.1f}, {(pose_raw[0][1] + pose_raw[1][1])/2:.1f})')

# With normalization
frames_norm = extract_landmarks_from_signature(sig, normalize_to_reference=True)
pose_norm = frames_norm[0]['pose']
sw_norm = np.linalg.norm(pose_norm[1][:2] - pose_norm[0][:2])

print()
print('WITH normalization:')
print(f'  Shoulder width: {sw_norm:.1f}px (target: {REFERENCE_SHOULDER_WIDTH}px)')
print(f'  Shoulder center: ({(pose_norm[0][0] + pose_norm[1][0])/2:.1f}, {(pose_norm[0][1] + pose_norm[1][1])/2:.1f})')
print(f'  Target center: (320.0, 192.0)')  # 640/2, 480*0.4

# Check if hands are in frame
def check_bounds(landmarks, name):
    all_in = True
    for key in ['left_hand', 'right_hand']:
        if landmarks.get(key) is not None:
            pts = landmarks[key]
            min_x, min_y = pts[:, 0].min(), pts[:, 1].min()
            max_x, max_y = pts[:, 0].max(), pts[:, 1].max()
            if min_x < 0 or max_x > 640 or min_y < 0 or max_y > 480:
                print(f'  ⚠️ {key} OUT OF BOUNDS: x=[{min_x:.0f},{max_x:.0f}], y=[{min_y:.0f},{max_y:.0f}]')
                all_in = False
    if all_in:
        print(f'  ✅ All hands in frame (0-640, 0-480)')

print()
print('Bounds check (raw):')
check_bounds(frames_raw[0], 'raw')

print()
print('Bounds check (normalized):')
check_bounds(frames_norm[0], 'normalized')

# Verify face is also scaled
if frames_norm[0].get('face') is not None:
    face = frames_norm[0]['face']
    print()
    print(f'Face landmarks: {len(face)} points')
    print(f'  Y range: {face[:, 1].min():.1f} to {face[:, 1].max():.1f}')
    if face[:, 1].max() < pose_norm[0][1]:
        print(f'  ✅ Face is above shoulders')

print()
print('=== TEST COMPLETE ===')
if abs(sw_norm - REFERENCE_SHOULDER_WIDTH) < 1:
    print('✅ Normalization working correctly!')
else:
    print(f'⚠️ Shoulder width mismatch: {sw_norm:.1f} vs target {REFERENCE_SHOULDER_WIDTH}')
