#!/usr/bin/env python3
"""
Analyze signature quality and jitter patterns.
"""

import json
import numpy as np
from pathlib import Path
import argparse

def analyze_signature(sig_path):
    """Detailed analysis of signature quality."""
    
    with open(sig_path, 'r') as f:
        sig = json.load(f)
    
    print(f"\nAnalyzing: {sig_path.name}")
    print(f"Total frames: {len(sig['frames'])}")
    
    for key in ['pose', 'left_hand', 'right_hand']:
        print(f"\n{key.upper()}:")
        
        # Collect all frames for this landmark type
        trajectories = []
        for frame in sig['frames']:
            if frame.get(key) is not None:
                trajectories.append(frame[key][:, :2])  # Get only xy
        
        if not trajectories:
            print(f"  No data")
            continue
        
        # Analyze each landmark
        num_landmarks = trajectories[0].shape[0] if len(trajectories) > 0 else 0
        print(f"  Landmarks per frame: {num_landmarks}")
        
        # Compute velocity for each landmark
        for lm_idx in range(min(3, num_landmarks)):  # Just check first 3 landmarks
            velocities = []
            for i in range(1, len(trajectories)):
                diff = trajectories[i][lm_idx] - trajectories[i-1][lm_idx]
                vel = np.linalg.norm(diff)
                velocities.append(vel)
            
            velocities = np.array(velocities)
            
            # Compute jerk (change in velocity)
            jerks = np.diff(velocities)
            
            max_vel = np.max(velocities)
            mean_vel = np.mean(velocities)
            max_jerk = np.max(np.abs(jerks))
            mean_jerk = np.mean(np.abs(jerks))
            outliers = np.sum(np.abs(jerks) > 30)  # Count large jerks
            
            print(f"    Landmark {lm_idx}: vel={mean_vel:.1f}±{np.std(velocities):.1f} " + 
                  f"(max={max_vel:.1f}), jerk={mean_jerk:.1f}±{np.std(jerks):.1f} " +
                  f"(max={max_jerk:.1f}, outliers={outliers})")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='asl')
    parser.add_argument('--word', default='hello_0')
    args = parser.parse_args()
    
    sig_path = Path(f'assets/signatures/{args.lang.lower()}/{args.word}.json')
    if sig_path.exists():
        analyze_signature(sig_path)
    else:
        print(f"File not found: {sig_path}")
