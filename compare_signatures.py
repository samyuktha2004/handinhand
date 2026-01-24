#!/usr/bin/env python3
"""
Compare original vs smoothed signatures for quality differences.
"""

import json
import numpy as np
from pathlib import Path
from recognition_engine import RecognitionEngine
import argparse

def compute_embeddings_from_signature(sig_path, engine):
    """Extract embeddings from a signature file."""
    with open(sig_path, 'r') as f:
        sig = json.load(f)
    
    # Extract all pose landmarks
    all_landmarks = []
    for frame in sig.get('pose_data', []):
        pose = np.array(frame.get('pose', []))
        left_hand = np.array(frame.get('left_hand', []))
        right_hand = np.array(frame.get('right_hand', []))
        
        if pose.size > 0:
            all_landmarks.append(pose.flatten())
    
    if not all_landmarks:
        return None
    
    # Average embedding
    embedding = np.mean(all_landmarks, axis=0)
    return embedding / np.linalg.norm(embedding)  # Normalize

def main():
    parser = argparse.ArgumentParser(description="Compare original vs smoothed signatures")
    parser.add_argument('--lang', default='asl')
    parser.add_argument('--word', default='hello_0')
    args = parser.parse_args()
    
    # Load signatures
    orig_path = Path(f'assets/signatures/{args.lang}/{args.word}.json')
    smooth_path = Path(f'assets/signatures/{args.lang}/{args.word}_smoothed.json')
    
    if not orig_path.exists():
        print(f"❌ Original not found: {orig_path}")
        return
    
    if not smooth_path.exists():
        print(f"❌ Smoothed not found: {smooth_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"Comparing: {args.lang.upper()} / {args.word}")
    print(f"{'='*60}\n")
    
    # Load JSONs
    with open(orig_path) as f:
        orig_sig = json.load(f)
    with open(smooth_path) as f:
        smooth_sig = json.load(f)
    
    print(f"Original frames: {len(orig_sig['pose_data'])}")
    print(f"Smoothed frames: {len(smooth_sig['pose_data'])}")
    
    # Compute embeddings
    engine = RecognitionEngine()
    orig_emb = compute_embeddings_from_signature(orig_path, engine)
    smooth_emb = compute_embeddings_from_signature(smooth_path, engine)
    
    if orig_emb is None or smooth_emb is None:
        print("❌ Could not compute embeddings")
        return
    
    # Compare embeddings
    similarity = np.dot(orig_emb, smooth_emb)
    print(f"\n{'='*60}")
    print(f"Embedding Similarity (orig vs smooth): {similarity:.4f}")
    print(f"{'='*60}\n")
    
    if similarity > 0.99:
        print("✅ Embeddings nearly identical - smoothing preserved semantics")
        print("   This suggests data was already smooth at the source level")
    elif similarity > 0.95:
        print("✅ Embeddings very similar - minimal semantic change")
        print("   Smoothing made small adjustments")
    else:
        print("⚠️  Embeddings differ - smoothing may have changed semantics")
        print("   Consider adjusting smoothing parameters")
    
    # Analyze frame-by-frame differences
    print(f"\nFrame-by-frame comparison:")
    pose_diffs = []
    hand_diffs = []
    
    for i, (orig_frame, smooth_frame) in enumerate(zip(orig_sig['pose_data'], smooth_sig['pose_data'])):
        if orig_frame.get('pose') and smooth_frame.get('pose'):
            orig_pose = np.array(orig_frame['pose'])
            smooth_pose = np.array(smooth_frame['pose'])
            diff = np.mean(np.linalg.norm(orig_pose - smooth_pose, axis=1))
            pose_diffs.append(diff)
        
        if orig_frame.get('left_hand') and smooth_frame.get('left_hand'):
            orig_hand = np.array(orig_frame['left_hand'])
            smooth_hand = np.array(smooth_frame['left_hand'])
            diff = np.mean(np.linalg.norm(orig_hand - smooth_hand, axis=1))
            hand_diffs.append(diff)
    
    if pose_diffs:
        print(f"  Pose - mean diff: {np.mean(pose_diffs):.2f}px, max: {np.max(pose_diffs):.2f}px")
    if hand_diffs:
        print(f"  Hands - mean diff: {np.mean(hand_diffs):.2f}px, max: {np.max(hand_diffs):.2f}px")

if __name__ == '__main__':
    main()
