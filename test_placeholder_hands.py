#!/usr/bin/env python3
"""Test arm-angle-aware placeholder hands."""
from skeleton_drawer import SkeletonDrawer
import numpy as np

# Test with a simple pose
pose = np.array([
    [370, 192, 0],  # Left shoulder
    [270, 192, 0],  # Right shoulder  
    [400, 280, 0],  # Left elbow
    [240, 280, 0],  # Right elbow
    [430, 350, 0],  # Left wrist (arm pointing down-right)
    [210, 350, 0],  # Right wrist (arm pointing down-left)
], dtype=np.float32)

# Create placeholder hands
left_hand = SkeletonDrawer._create_placeholder_hand(pose, is_left=True)
right_hand = SkeletonDrawer._create_placeholder_hand(pose, is_left=False)

print('Left hand wrist (should be at ~430, 350):')
print(f'  Wrist: ({left_hand[0, 0]:.1f}, {left_hand[0, 1]:.1f})')
print(f'  Middle tip: ({left_hand[12, 0]:.1f}, {left_hand[12, 1]:.1f})')

print()
print('Right hand wrist (should be at ~210, 350):')
print(f'  Wrist: ({right_hand[0, 0]:.1f}, {right_hand[0, 1]:.1f})')
print(f'  Middle tip: ({right_hand[12, 0]:.1f}, {right_hand[12, 1]:.1f})')

# Calculate arm angle
left_elbow = pose[2][:2]
left_wrist = pose[4][:2]
arm_vec = left_wrist - left_elbow
arm_angle = np.arctan2(arm_vec[0], arm_vec[1])
print(f'\nLeft arm angle: {np.degrees(arm_angle):.1f} degrees from vertical')

# Check that middle finger tip is in direction of arm
finger_vec = left_hand[12, :2] - left_hand[0, :2]
finger_angle = np.arctan2(finger_vec[0], finger_vec[1])
print(f'Left finger angle: {np.degrees(finger_angle):.1f} degrees from vertical')

print('\nHand should be oriented along arm direction!')
