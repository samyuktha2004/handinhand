#!/usr/bin/env python3
"""
Test ASL vs BSL recognition with both original and smoothed signatures.
"""

import json
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cosine

def load_signature_embeddings(sig_path):
    """Load a signature and compute its embedding using pose only for consistency."""
    with open(sig_path, 'r') as f:
        sig = json.load(f)
    
    # Extract all pose landmarks only (for consistency across variable-length hands)
    all_embeddings = []
    for frame in sig.get('pose_data', []):
        pose = np.array(frame.get('pose', []))
        left_hand = np.array(frame.get('left_hand', []))
        right_hand = np.array(frame.get('right_hand', []))
        
        if pose.size > 0:
            # Combine pose + hands, handling variable lengths
            combined_parts = [pose.flatten()]
            
            if left_hand.size > 0:
                combined_parts.append(left_hand.flatten())
            if right_hand.size > 0:
                combined_parts.append(right_hand.flatten())
            
            # Flatten all parts
            combined = np.concatenate(combined_parts)
            all_embeddings.append(combined)
    
    if not all_embeddings:
        return None
    
    # Use only pose for consistency (6x3 per frame)
    pose_only = []
    for frame in sig.get('pose_data', []):
        pose = np.array(frame.get('pose', []))
        if pose.size > 0:
            pose_only.append(pose.flatten())
    
    if not pose_only:
        return None
    
    # Average embedding across frames
    embedding = np.mean(pose_only, axis=0)
    return embedding / np.linalg.norm(embedding)  # Normalize

def test_asl_vs_bsl(asl_word, bsl_word, use_smoothed=False):
    """Test ASL vs BSL similarity."""
    suffix = '_smoothed' if use_smoothed else ''
    
    asl_path = Path(f'assets/signatures/asl/{asl_word}{suffix}.json')
    bsl_path = Path(f'assets/signatures/bsl/{bsl_word}{suffix}.json')
    
    if not asl_path.exists() or not bsl_path.exists():
        return None
    
    asl_emb = load_signature_embeddings(asl_path)
    bsl_emb = load_signature_embeddings(bsl_path)
    
    if asl_emb is None or bsl_emb is None:
        return None
    
    # Compute similarity
    similarity = 1 - cosine(asl_emb, bsl_emb)
    return similarity

def main():
    # Mapping: (asl_word, bsl_word)
    word_pairs = [
        ('hello_0', 'hello'),
        ('where_0', 'where'),
        ('you_0', 'you'),
        ('go_0', 'go'),
    ]
    threshold = 0.80
    
    print(f"\n{'='*70}")
    print(f"Cross-Language Recognition Test: ASL vs BSL")
    print(f"{'='*70}\n")
    
    print(f"{'Word':<20} {'Original':<15} {'Smoothed':<15} {'Change':<15} Status")
    print(f"{'-'*70}")
    
    orig_results = []
    smooth_results = []
    
    for asl_word, bsl_word in word_pairs:
        orig_sim = test_asl_vs_bsl(asl_word, bsl_word, use_smoothed=False)
        smooth_sim = test_asl_vs_bsl(asl_word, bsl_word, use_smoothed=True)
        
        if orig_sim is None or smooth_sim is None:
            continue
        
        orig_results.append(orig_sim)
        smooth_results.append(smooth_sim)
        
        change = smooth_sim - orig_sim
        change_str = f"{change:+.4f}"
        
        # Check if both pass threshold
        orig_pass = "✅" if orig_sim < threshold else "❌"
        smooth_pass = "✅" if smooth_sim < threshold else "❌"
        status = f"{orig_pass} → {smooth_pass}"
        
        pair_name = f"{asl_word}/{bsl_word}"
        print(f"{pair_name:<20} {orig_sim:.4f}         {smooth_sim:.4f}         {change_str:<15} {status}")
    
    print(f"\n{'='*70}")
    
    if orig_results and smooth_results:
        avg_orig = np.mean(orig_results)
        avg_smooth = np.mean(smooth_results)
        avg_change = avg_smooth - avg_orig
        
        print(f"Average Similarity:")
        print(f"  Original:  {avg_orig:.4f}")
        print(f"  Smoothed:  {avg_smooth:.4f}")
        print(f"  Change:    {avg_change:+.4f}")
        print(f"\nThreshold for recognition: < {threshold}")
        
        if avg_smooth < threshold:
            print(f"✅ Both datasets suitable for recognition")
        else:
            print(f"⚠️  Average similarity above threshold - may cause false positives")
    
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
