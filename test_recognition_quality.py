#!/usr/bin/env python3
"""
Unified Recognition Analysis Tool

Replaces multiple one-off test scripts:
- Analyzes all word signatures
- Tests cross-language similarity
- Provides decision recommendations
"""

import json
import numpy as np
from pathlib import Path
from scipy.spatial.distance import cosine
from typing import Dict, Tuple

class RecognitionAnalyzer:
    """Analyze recognition quality across languages and words."""
    
    def __init__(self):
        self.asl_sigs = {}
        self.bsl_sigs = {}
        self.words = ['hello', 'where', 'you', 'go']
        
    def load_signatures(self):
        """Load all language signatures."""
        for word in self.words:
            # Load ASL
            asl_path = Path(f'assets/signatures/asl/{word}_0.json')
            if asl_path.exists():
                with open(asl_path) as f:
                    self.asl_sigs[word] = json.load(f)
            
            # Load BSL
            bsl_path = Path(f'assets/signatures/bsl/{word}.json')
            if bsl_path.exists():
                with open(bsl_path) as f:
                    self.bsl_sigs[word] = json.load(f)
    
    def extract_embedding(self, sig: Dict) -> np.ndarray:
        """Convert pose_data to flat embedding."""
        pose_data = sig['pose_data']
        embeddings = []
        
        for frame in pose_data:
            pose = np.array(frame['pose']).flatten()
            left_hand = np.array(frame['left_hand']).flatten()
            right_hand = np.array(frame['right_hand']).flatten()
            frame_emb = np.concatenate([pose, left_hand, right_hand])
            embeddings.append(frame_emb)
        
        return np.mean(embeddings, axis=0)
    
    def compare_signatures(self, asl_sig: Dict, bsl_sig: Dict) -> float:
        """Compute cosine similarity."""
        asl_emb = self.extract_embedding(asl_sig)
        bsl_emb = self.extract_embedding(bsl_sig)
        
        max_len = max(len(asl_emb), len(bsl_emb))
        asl_padded = np.zeros(max_len)
        bsl_padded = np.zeros(max_len)
        
        asl_padded[:len(asl_emb)] = asl_emb
        bsl_padded[:len(bsl_emb)] = bsl_emb
        
        return 1 - cosine(asl_padded, bsl_padded)
    
    def analyze(self):
        """Run full analysis."""
        self.load_signatures()
        
        print("\n" + "=" * 70)
        print("RECOGNITION ANALYSIS - All Words")
        print("=" * 70)
        
        results = {}
        for word in self.words:
            if word in self.asl_sigs and word in self.bsl_sigs:
                similarity = self.compare_signatures(self.asl_sigs[word], self.bsl_sigs[word])
                results[word] = similarity
                
                status = "✅" if similarity < 0.80 else "⚠️"
                print(f"{word:10s}  {similarity:.4f}  {status}")
        
        avg = np.mean(list(results.values()))
        print("-" * 70)
        print(f"{'Average':10s}  {avg:.4f}  {'✅ EXCELLENT' if avg < 0.80 else '⚠️ MARGINAL'}")
        print("=" * 70 + "\n")
        
        return results

if __name__ == '__main__':
    analyzer = RecognitionAnalyzer()
    analyzer.analyze()
