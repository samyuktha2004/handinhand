#!/usr/bin/env python3
"""Debug hello_1 out of bounds issue."""
import json
import numpy as np
from skeleton_drawer import extract_landmarks_from_signature

with open('assets/signatures/asl/hello_1.json') as f:
    sig = json.load(f)

frames = extract_landmarks_from_signature(sig, normalize_to_reference=True)

# Check frame 1
lh = frames[0]['left_hand']
print('Frame 1 left_hand Y range:', lh[:,1].min(), 'to', lh[:,1].max())
print('Frame boundary: 0 to 480')
print()
if lh[:,1].min() < 0:
    print('Issue: Hands going ABOVE the frame (negative Y)')
    print('This is a source video issue - person was positioned too high')
    print('Solution: Need to clip or adjust the normalization center point')
