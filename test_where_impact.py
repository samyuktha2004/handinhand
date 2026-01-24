#!/usr/bin/env python3
"""Test where reference impact on recognition."""

import json
import numpy as np
from scipy.spatial.distance import cosine

def load_sig(path):
    """Load signature with padded embeddings."""
    with open(path) as f:
        sig = json.load(f)
    
    all_landmarks = []
    for frame in sig.get('pose_data', []):
        pose = np.array(frame.get('pose', []))
        left_hand = np.array(frame.get('left_hand', []))
        right_hand = np.array(frame.get('right_hand', []))
        
        if pose.size > 0:
            parts = [pose.flatten()]
            if left_hand.size > 0:
                parts.append(left_hand.flatten())
            if right_hand.size > 0:
                parts.append(right_hand.flatten())
            
            combined = np.concatenate(parts)
            all_landmarks.append(combined)
    
    if not all_landmarks:
        return None
    
    # Pad to consistent size
    max_len = max(len(x) for x in all_landmarks)
    padded = []
    for x in all_landmarks:
        p = np.zeros(max_len)
        p[:len(x)] = x
        padded.append(p)
    
    emb = np.mean(padded, axis=0)
    return emb / np.linalg.norm(emb)

print("\n" + "="*70)
print("Recognition Test: WITH NEW WHERE REFERENCE")
print("="*70 + "\n")

results = {
    'hello': load_sig('assets/signatures/asl/hello_0.json'),
    'where': load_sig('assets/signatures/asl/where_0.json'),
    'you': load_sig('assets/signatures/asl/you_0.json'),
    'go': load_sig('assets/signatures/asl/go_0.json'),
}

bsl_sigs = {
    'hello': load_sig('assets/signatures/bsl/hello.json'),
    'where': load_sig('assets/signatures/bsl/where.json'),
    'you': load_sig('assets/signatures/bsl/you.json'),
    'go': load_sig('assets/signatures/bsl/go.json'),
}

threshold = 0.80
similarities = []

for word in ['hello', 'where', 'you', 'go']:
    if results[word] is not None and bsl_sigs[word] is not None:
        sim = 1 - cosine(results[word], bsl_sigs[word])
        similarities.append(sim)
        status = "✅" if sim < threshold else "❌"
        print(f"{word:<12} {sim:.4f}  {status}")
    else:
        print(f"{word:<12} MISSING")

print(f"\n{'='*70}")
print(f"Average: {np.mean(similarities):.4f}")
print(f"Target:  < {threshold}")
if np.mean(similarities) < threshold:
    print("✅ EXCELLENT - Languages clearly distinct")
else:
    print(f"⚠️  MARGINAL - Average above threshold")
print(f"{'='*70}\n")
