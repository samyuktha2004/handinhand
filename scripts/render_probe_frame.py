#!/usr/bin/env python3
import json
from pathlib import Path
from skeleton_renderer import render_skeleton, extract_landmarks_from_signature
import cv2
import numpy as np

probe = 'up'
probe_path = Path('assets/probes') / f'probe_{probe}.json'
if not probe_path.exists():
    print('Probe not found:', probe_path)
    raise SystemExit(1)

sig = json.load(open(probe_path))
frames = extract_landmarks_from_signature(sig)
if not frames:
    print('No frames in probe')
    raise SystemExit(1)

frame0 = frames[0]
# Convert flat landmarks array to dict for renderer convenience
landmarks_dict = {}
if len(frame0) >= 6:
    landmarks_dict['pose'] = frame0[:6]
if len(frame0) >= 27:
    landmarks_dict['left_hand'] = frame0[6:27]
if len(frame0) >= 48:
    landmarks_dict['right_hand'] = frame0[27:48]

img = render_skeleton(landmarks_dict, width=640, height=480)
out_dir = Path('assets/test_render')
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / f'probe_{probe}_frame0.png'
cv2.imwrite(str(out_path), img)
print('Wrote', out_path)
