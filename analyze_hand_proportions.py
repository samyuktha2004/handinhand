#!/usr/bin/env python3
"""Analyze hand proportions in actual signatures vs reference body."""

import json
import numpy as np

# Load a real signature
with open('assets/signatures/asl/hello_0.json') as f:
    sig = json.load(f)

frame = sig['pose_data'][0]
pose = np.array(frame['pose'])
rh = np.array(frame['right_hand']) if frame['right_hand'] else None

print('=== PROPORTION ANALYSIS ===')
print()

# Get shoulder width from pose (indices 0,1 in our reduced set)
shoulder_width = 0
if len(pose) >= 6:
    left_shoulder = pose[0][:2]
    right_shoulder = pose[1][:2]
    shoulder_width = np.linalg.norm(right_shoulder - left_shoulder)
    print(f'Shoulder width: {shoulder_width:.1f} units')
    
    # Upper arm
    left_elbow = pose[2][:2]
    upper_arm = np.linalg.norm(left_elbow - left_shoulder)
    print(f'Upper arm: {upper_arm:.1f} units')
    
    # Forearm
    left_wrist = pose[4][:2]
    forearm = np.linalg.norm(left_wrist - left_elbow)
    print(f'Forearm: {forearm:.1f} units')
    
    print(f'Arm ratio (upper/forearm): {upper_arm/forearm:.2f}')

if rh is not None and len(rh) >= 21:
    wrist = rh[0][:2]
    middle_tip = rh[12][:2]
    hand_length = np.linalg.norm(middle_tip - wrist)
    
    # Palm width (index MCP to pinky MCP)
    index_mcp = rh[5][:2]
    pinky_mcp = rh[17][:2]
    palm_width = np.linalg.norm(pinky_mcp - index_mcp)
    
    print()
    print(f'Hand length (wrist to middle tip): {hand_length:.1f} units')
    print(f'Palm width (index to pinky MCP): {palm_width:.1f} units')
    
    if shoulder_width > 0:
        hand_to_shoulder_ratio = hand_length / shoulder_width
        print()
        print(f'Hand/Shoulder ratio: {hand_to_shoulder_ratio:.2f}')
        print()
        print('=== REFERENCE BODY COMPARISON ===')
        print(f'Reference SHOULDER_WIDTH: 100px')
        print(f'Expected hand length: {100 * hand_to_shoulder_ratio:.0f}px')
        print()
        
        # Current reference body hand dimensions
        seg = 10  # finger segment
        palm_depth = 25
        current_hand_length = palm_depth + seg * 3.5  # palm + middle finger
        print(f'Current reference hand length: {current_hand_length:.0f}px')
        print(f'Current palm_width: 35px')
        print()
        
        # Calculate correct size
        correct_hand = 100 * hand_to_shoulder_ratio
        correct_palm_width = 100 * (palm_width / shoulder_width)
        
        print(f'Correct proportions:')
        print(f'  Hand length: {correct_hand:.0f}px')
        print(f'  Palm width: {correct_palm_width:.0f}px')
        print()
        
        if current_hand_length > correct_hand * 1.3:
            print('⚠️  Reference hands are TOO LARGE')
            scale_factor = correct_hand / current_hand_length
            print(f'   Need to scale down by: {scale_factor:.2f}x')
            print(f'   New seg: {seg * scale_factor:.0f}px')
            print(f'   New palm_depth: {palm_depth * scale_factor:.0f}px')
            print(f'   New palm_width: {35 * scale_factor:.0f}px')
        elif current_hand_length < correct_hand * 0.7:
            print('⚠️  Reference hands are TOO SMALL')
        else:
            print('✅ Reference hands are PROPORTIONAL')
else:
    print('No hand data available in this frame')
