#!/usr/bin/env python3
"""
ASL vs BSL Recognition Test
============================

Compare embeddings/similarity scores for the same word in two languages.
Verifies that recognition engine can distinguish between ASL and BSL.

Usage:
    python3 test_asl_vs_bsl.py hello    # Compare ASL hello vs BSL hello
    python3 test_asl_vs_bsl.py where    # Compare ASL where vs BSL where
"""

import sys
import json
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cosine
from skeleton_drawer import extract_landmarks_from_signature
from utils.registry_loader import RegistryLoader


def load_signature(lang: str, sig_name: str):
    """Load signature and extract embeddings."""
    sig_path = Path(f"assets/signatures/{lang.lower()}/{sig_name}.json")
    if not sig_path.exists():
        print(f"❌ Not found: {sig_path}")
        return None
    
    with open(sig_path) as f:
        sig = json.load(f)
    
    frames = extract_landmarks_from_signature(sig)
    return {
        'sig': sig,
        'frames': frames,
        'path': sig_path,
        'name': sig_name
    }


def compute_embedding(frames, use_pose=True, use_hands=True):
    """
    Compute average embedding from frames.
    Concatenates pose + hand landmarks into single vector.
    """
    embeddings = []
    
    for frame in frames:
        feature_vec = []
        
        if use_pose and 'pose' in frame and frame['pose'] is not None:
            pose = frame['pose'].flatten()
            feature_vec.extend(pose)
        
        if use_hands:
            if 'left_hand' in frame and frame['left_hand'] is not None:
                lh = frame['left_hand'].flatten()
                feature_vec.extend(lh)
            
            if 'right_hand' in frame and frame['right_hand'] is not None:
                rh = frame['right_hand'].flatten()
                feature_vec.extend(rh)
        
        if feature_vec:
            embeddings.append(np.array(feature_vec, dtype=np.float32))
    
    if not embeddings:
        return None
    
    # Average across frames
    return np.mean(embeddings, axis=0)


def main():
    if len(sys.argv) < 2:
        print("""
╔════════════════════════════════════════════════════════════════╗
║     ASL vs BSL Recognition Test                              ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
    python3 test_asl_vs_bsl.py <word>

EXAMPLES:
    python3 test_asl_vs_bsl.py hello
    python3 test_asl_vs_bsl.py where

WHAT THIS TESTS:
    1. Loads ASL and BSL signatures for same word
    2. Computes embedding (pose + hands averaged)
    3. Calculates cosine similarity
    4. Verifies they're different enough (< 0.8 = different)

SUCCESS CRITERIA:
    • ASL-to-BSL similarity < 0.80 (should be distinct)
    • Within-language similarity > 0.85 (consistent)
""")
        return 1
    
    word = sys.argv[1].lower()
    
    print(f"\n{'='*60}")
    print(f"Testing: {word.upper()}")
    print(f"{'='*60}\n")
    
    # Load signatures
    print(f"Loading ASL '{word}'...")
    asl_data = load_signature('asl', f"{word}_0")
    if not asl_data:
        print(f"❌ ASL not found. Available: hello_0, hello_1, where_0, you_0, go_0")
        return 1
    
    print(f"✓ ASL: {len(asl_data['frames'])} frames")
    
    print(f"\nLoading BSL '{word}'...")
    bsl_data = load_signature('bsl', word)
    if not bsl_data:
        print(f"❌ BSL not found. Available: hello, where, you, go")
        return 1
    
    print(f"✓ BSL: {len(bsl_data['frames'])} frames")
    
    # Compute embeddings
    print(f"\nComputing embeddings...")
    asl_emb = compute_embedding(asl_data['frames'])
    bsl_emb = compute_embedding(bsl_data['frames'])
    
    if asl_emb is None or bsl_emb is None:
        print("❌ Failed to compute embeddings")
        return 1
    
    print(f"✓ ASL embedding: {asl_emb.shape}")
    print(f"✓ BSL embedding: {bsl_emb.shape}")
    
    # Compute similarity
    similarity = 1 - cosine(asl_emb, bsl_emb)
    
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"\nASL vs BSL similarity: {similarity:.3f}")
    
    if similarity < 0.80:
        print(f"✅ PASS: Languages are distinct (< 0.80)")
        status = "GOOD"
    else:
        print(f"⚠️  WARNING: Languages too similar (>= 0.80)")
        status = "NEEDS REVIEW"
    
    # Compare within-language variations
    print(f"\n--- Within-Language Consistency ---\n")
    
    # Try to find another ASL variant
    for variant in ['hello_1', 'hello_2']:
        alt_data = load_signature('asl', variant)
        if alt_data:
            alt_emb = compute_embedding(alt_data['frames'])
            if alt_emb is not None:
                within_sim = 1 - cosine(asl_emb, alt_emb)
                print(f"ASL hello_0 vs {variant}: {within_sim:.3f}")
    
    print(f"\n{'='*60}")
    print(f"INTERPRETATION")
    print(f"{'='*60}")
    print(f"""
Similarity ranges:
  1.0   = Identical
  0.85+ = Very similar
  0.80  = Recognition threshold
  <0.80 = Different enough to distinguish
  0.0   = Completely different

Your result ({similarity:.3f}):""")
    
    if similarity > 0.90:
        print("""  ⚠️ VERY SIMILAR
  → Languages too close to distinguish reliably
  → Consider adding facial features or more body points
  → May need HMM or temporal patterns for better separation""")
    elif similarity > 0.80:
        print("""  ⚠️ BORDERLINE
  → Similar enough to cause false positives
  → Need careful threshold tuning
  → Facial features will help""")
    else:
        print("""  ✅ DISTINCT
  → Recognition should work well
  → Low false positive risk
  → Good foundation for expansion""")
    
    print(f"\nStatus: {status}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
