#!/usr/bin/env python3
"""
Embedding Generator for Sign Language Recognition
=================================================

Converts landmark sequences into fixed-size embedding vectors via:
1. Body-centric normalization (subtract shoulder center)
2. Frame flattening and averaging (Global Average Pooling)
3. Multi-instance aggregation (average across multiple signers)

Output: 512-dimensional embedding vectors saved to translation_map.json

Usage:
    python3 generate_embeddings.py
    
Result:
    - Updates translation_map.json with asl_embedding_mean and bsl_embedding_mean
    - Saves individual .npy files to assets/embeddings/{asl,bsl}/
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os

# ============================================================================
# CONFIGURATION
# ============================================================================
TRANSLATION_REGISTRY = "translation_map.json"
EMBEDDINGS_DIR = "assets/embeddings"
SIGNATURES_DIR = "assets/signatures"

# Landmark indices for pose normalization
SHOULDER_CENTER_LEFT = 11   # Left shoulder
SHOULDER_CENTER_RIGHT = 12  # Right shoulder

# Embedding dimension (Global Average Pooling output)
EMBEDDING_DIM = 512


class EmbeddingGenerator:
    """Generate normalized embeddings from landmark sequences."""

    def __init__(self):
        """Initialize generator."""
        self.registry = self._load_registry()
        self.embeddings_asl = {}
        self.embeddings_bsl = {}
        self._ensure_directories()

    def _ensure_directories(self):
        """Create embedding directories if they don't exist."""
        os.makedirs(os.path.join(EMBEDDINGS_DIR, "asl"), exist_ok=True)
        os.makedirs(os.path.join(EMBEDDINGS_DIR, "bsl"), exist_ok=True)

    def _load_registry(self) -> Dict:
        """Load translation registry."""
        if not os.path.exists(TRANSLATION_REGISTRY):
            raise FileNotFoundError(f"Registry not found: {TRANSLATION_REGISTRY}")
        
        with open(TRANSLATION_REGISTRY) as f:
            return json.load(f)

    def _load_signature(self, sig_file: str) -> Optional[Dict]:
        """Load signature JSON file."""
        try:
            with open(sig_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"      ⚠️  Error loading {sig_file}: {str(e)[:50]}")
            return None

    def _normalize_landmarks(self, landmarks: List[List[float]]) -> np.ndarray:
        """
        Normalize landmarks to be body-centric (relative to shoulder center).
        
        Process:
        1. Calculate shoulder center: mean of left (11) and right (12) shoulders
        2. Subtract center from all landmarks
        3. Return normalized array
        """
        landmarks = np.array(landmarks, dtype=np.float32)
        
        # Get shoulder center (average of indices 11 and 12)
        if landmarks.shape[0] > 12:
            shoulder_left = landmarks[SHOULDER_CENTER_LEFT]
            shoulder_right = landmarks[SHOULDER_CENTER_RIGHT]
            shoulder_center = (shoulder_left + shoulder_right) / 2.0
            
            # Normalize: subtract shoulder center from all points
            landmarks_normalized = landmarks - shoulder_center
        else:
            landmarks_normalized = landmarks
        
        return landmarks_normalized

    def _frame_to_embedding(self, frame_data: Dict) -> np.ndarray:
        """
        Convert single frame to embedding via Global Average Pooling.
        
        Process:
        1. Extract pose, left_hand, right_hand, face coordinates
        2. Flatten to 1D vector
        3. Normalize (body-centric)
        4. Return normalized vector
        """
        landmarks = []
        
        # Concatenate all landmark groups: pose + left_hand + right_hand + face
        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if key in frame_data and frame_data[key]:
                landmarks.extend(frame_data[key])
        
        landmarks = np.array(landmarks, dtype=np.float32)
        
        if len(landmarks) == 0:
            return np.zeros(52, dtype=np.float32)  # 52 = 6 pose + 21*2 hands + 4 face
        
        # Flatten and normalize
        landmarks_flat = self._normalize_landmarks(landmarks.reshape(-1, 3))
        return landmarks_flat.flatten().astype(np.float32)

    def _compute_signature_embedding(self, sig_file: str) -> Optional[np.ndarray]:
        """
        Compute embedding for a single signature (avg across all frames).
        
        Process:
        1. Load signature JSON
        2. For each frame: convert to embedding via Global Average Pooling
        3. Average embeddings across all frames
        4. Return averaged embedding (512-dim after padding/pooling)
        """
        signature = self._load_signature(sig_file)
        if not signature or 'pose_data' not in signature:
            return None
        
        frames = signature['pose_data']
        if not frames:
            return None
        
        # Compute embedding for each frame
        frame_embeddings = []
        for frame in frames:
            frame_embedding = self._frame_to_embedding(frame)
            frame_embeddings.append(frame_embedding)
        
        # Global Average Pooling: average embeddings across all frames
        avg_embedding = np.mean(frame_embeddings, axis=0)
        
        # Pad/reshape to EMBEDDING_DIM if needed
        if len(avg_embedding) < EMBEDDING_DIM:
            avg_embedding = np.pad(
                avg_embedding,
                (0, EMBEDDING_DIM - len(avg_embedding)),
                mode='constant',
                constant_values=0
            )
        else:
            avg_embedding = avg_embedding[:EMBEDDING_DIM]
        
        return avg_embedding.astype(np.float32)

    def _compute_aggregated_embedding(self, sig_files: List[str]) -> Optional[np.ndarray]:
        """
        Compute aggregated embedding across multiple instances.
        
        Process:
        1. For each signature file: compute individual embedding
        2. Average embeddings across all instances
        3. Return aggregated embedding (robust across signers/contexts)
        """
        embeddings = []
        
        for sig_file in sig_files:
            embedding = self._compute_signature_embedding(sig_file)
            if embedding is not None:
                embeddings.append(embedding)
        
        if not embeddings:
            return None
        
        # Average embeddings across all instances
        aggregated = np.mean(embeddings, axis=0)
        return aggregated.astype(np.float32)

    def generate_embeddings(self):
        """Generate embeddings for all concepts in registry."""
        print("\n" + "=" * 60)
        print("🧮 Embedding Generation Pipeline")
        print("=" * 60)
        print(f"Registry: {TRANSLATION_REGISTRY}")
        print(f"Output dir: {EMBEDDINGS_DIR}/")
        print("=" * 60)
        
        for concept_key, concept_data in self.registry.items():
            if concept_key.startswith("_"):
                continue  # Skip metadata entries
            
            concept_name = concept_data.get("concept_name", concept_key)
            print(f"\n📊 Processing: {concept_name}")
            print("-" * 60)
            
            # ===== ASL Embeddings =====
            asl_sigs = concept_data.get("asl_signatures", [])
            if asl_sigs:
                asl_files = [sig["signature_file"] for sig in asl_sigs]
                print(f"   🎯 ASL: {len(asl_files)} instance(s)")
                for i, f in enumerate(asl_files):
                    print(f"      {i+1}. {Path(f).name}")
                
                # Compute aggregated embedding
                asl_embedding = self._compute_aggregated_embedding(asl_files)
                if asl_embedding is not None:
                    # Save to .npy file
                    npy_path = concept_data.get("asl_embedding_mean_file")
                    if npy_path:
                        os.makedirs(os.path.dirname(npy_path), exist_ok=True)
                        np.save(npy_path, asl_embedding)
                        print(f"   ✅ ASL embedding saved: {npy_path}")
                        print(f"      Shape: {asl_embedding.shape}, Mean: {asl_embedding.mean():.4f}")
                        
                        # Update registry (serialize as list for JSON)
                        concept_data["asl_embedding_mean"] = asl_embedding.tolist()
                    else:
                        print(f"   ⚠️  No embedding file path specified")
                else:
                    print(f"   ⚠️  Failed to compute ASL embedding")
            
            # ===== BSL Embeddings =====
            bsl_target = concept_data.get("bsl_target", {})
            if bsl_target and bsl_target.get("signature_file"):
                bsl_file = bsl_target["signature_file"]
                print(f"   🎯 BSL: {Path(bsl_file).name}")
                
                # Compute embedding (single BSL target)
                bsl_embedding = self._compute_signature_embedding(bsl_file)
                if bsl_embedding is not None:
                    # Save to .npy file
                    npy_path = concept_data.get("bsl_embedding_mean_file")
                    if npy_path:
                        os.makedirs(os.path.dirname(npy_path), exist_ok=True)
                        np.save(npy_path, bsl_embedding)
                        print(f"   ✅ BSL embedding saved: {npy_path}")
                        print(f"      Shape: {bsl_embedding.shape}, Mean: {bsl_embedding.mean():.4f}")
                        
                        # Update registry
                        concept_data["bsl_embedding_mean"] = bsl_embedding.tolist()
                    else:
                        print(f"   ⚠️  No embedding file path specified")
                else:
                    print(f"   ⚠️  Failed to compute BSL embedding")

    def save_registry(self):
        """Save updated registry with embeddings back to JSON."""
        with open(TRANSLATION_REGISTRY, 'w') as f:
            json.dump(self.registry, f, indent=2)
        print(f"\n✅ Registry updated: {TRANSLATION_REGISTRY}")

    def compute_similarity_matrix(self) -> Optional[np.ndarray]:
        """
        Compute cosine similarity matrix between ASL and BSL embeddings.
        
        Returns: Matrix of shape (4, 4) showing similarity between each concept pair.
        """
        from scipy.spatial.distance import cosine
        
        print("\n" + "=" * 60)
        print("📊 Cosine Similarity Analysis")
        print("=" * 60)
        
        concepts = []
        asl_embeddings = []
        bsl_embeddings = []
        
        for concept_key, concept_data in self.registry.items():
            if concept_key.startswith("_"):
                continue
            
            asl_emb = concept_data.get("asl_embedding_mean")
            bsl_emb = concept_data.get("bsl_embedding_mean")
            
            if asl_emb and bsl_emb:
                concepts.append(concept_data["concept_name"])
                asl_embeddings.append(np.array(asl_emb))
                bsl_embeddings.append(np.array(bsl_emb))
        
        if not concepts:
            print("⚠️  No embeddings found for similarity analysis")
            return None
        
        # Compute ASL-BSL similarities (should be high for matching concepts)
        similarities = []
        for i, (concept, asl_emb, bsl_emb) in enumerate(zip(concepts, asl_embeddings, bsl_embeddings)):
            similarity = 1 - cosine(asl_emb, bsl_emb)  # Convert distance to similarity
            similarities.append(similarity)
            print(f"   {concept:25s}: {similarity:.4f}")
        
        print(f"\n   Mean ASL-BSL similarity: {np.mean(similarities):.4f}")
        print("   (Target: > 0.85 for good concept alignment)")
        
        return np.array(similarities)


def main():
    """Main entry point."""
    try:
        generator = EmbeddingGenerator()
        generator.generate_embeddings()
        generator.save_registry()
        generator.compute_similarity_matrix()
        
        print("\n" + "=" * 60)
        print("✅ Embedding Generation Complete!")
        print("=" * 60)
        print(f"   Output directory: {EMBEDDINGS_DIR}/")
        print(f"   Registry updated: {TRANSLATION_REGISTRY}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
