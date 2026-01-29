#!/usr/bin/env python3
"""
Embedding Generator for Sign Language Recognition
=================================================

Converts landmark sequences into fixed-size embedding vectors via:
1. Body-centric normalization (subtract shoulder center)
2. Frame flattening and averaging (Global Average Pooling)
3. Multi-instance aggregation (average across multiple signers)

Output: 512-dimensional embedding vectors saved to language registries

Usage:
    python3 generate_embeddings.py
    
Result:
    - Updates assets/registries/{asl,bsl}_registry.json with embedding means
    - Saves individual .npy files to assets/embeddings/{asl,bsl}/
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os

# Import registry loader for new structure
from utils.registry_loader import RegistryLoader

# ============================================================================
# CONFIGURATION
# ============================================================================
REGISTRIES_DIR = "assets/registries"
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
        self.loader = RegistryLoader()
        self.concept_registry = self.loader.get_concept_registry()
        self.asl_registry = self.loader.get_language_registry('asl')
        self.bsl_registry = self.loader.get_language_registry('bsl')
        self.embeddings_asl = {}
        self.embeddings_bsl = {}
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(EMBEDDINGS_DIR).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(EMBEDDINGS_DIR, 'asl')).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(EMBEDDINGS_DIR, 'bsl')).mkdir(parents=True, exist_ok=True)
        Path(REGISTRIES_DIR).mkdir(parents=True, exist_ok=True)

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
        Normalize landmarks to be body-centric and scale-invariant.
        
        Process:
        1. Calculate shoulder center: mean of left (11) and right (12) shoulders
        2. Subtract center from all landmarks (translation invariance)
        3. Divide by shoulder width (scale invariance)
        
        Result: All bodies normalized to shoulder_width = 1.0
        """
        landmarks = np.array(landmarks, dtype=np.float32)
        
        # Get shoulder center (average of indices 11 and 12)
        if landmarks.shape[0] > 12:
            shoulder_left = landmarks[SHOULDER_CENTER_LEFT]
            shoulder_right = landmarks[SHOULDER_CENTER_RIGHT]
            shoulder_center = (shoulder_left + shoulder_right) / 2.0
            
            # Step 1: Translation invariance - center on shoulders
            landmarks_normalized = landmarks - shoulder_center
            
            # Step 2: Scale invariance - normalize by shoulder width
            shoulder_width = np.linalg.norm(shoulder_left[:2] - shoulder_right[:2])
            if shoulder_width > 0.01:  # Avoid division by zero
                landmarks_normalized = landmarks_normalized / shoulder_width
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
        """Generate embeddings for all concepts in registries."""
        print("\n" + "=" * 60)
        print("🧮 Embedding Generation Pipeline")
        print("=" * 60)
        print(f"ASL Registry: {os.path.join(REGISTRIES_DIR, 'asl_registry.json')}")
        print(f"BSL Registry: {os.path.join(REGISTRIES_DIR, 'bsl_registry.json')}")
        print(f"Output dir: {EMBEDDINGS_DIR}/")
        print("=" * 60)
        
        for concept_id, concept_data in self.asl_registry.items():
            if concept_id.startswith("_"):
                continue  # Skip metadata entries
            
            concept_name = concept_data.get("concept_name", concept_id)
            print(f"\n📊 Processing: {concept_name}")
            print("-" * 60)
            
            # ===== ASL Embeddings =====
            asl_sigs = concept_data.get("signatures", [])
            if asl_sigs:
                asl_files = [sig["signature_file"] for sig in asl_sigs]
                print(f"   🎯 ASL: {len(asl_files)} instance(s)")
                for i, f in enumerate(asl_files):
                    print(f"      {i+1}. {Path(f).name}")
                
                # Compute aggregated embedding
                asl_embedding = self._compute_aggregated_embedding(asl_files)
                if asl_embedding is not None:
                    # Save to .npy file
                    npy_path = concept_data.get("embedding_mean_file")
                    if npy_path:
                        os.makedirs(os.path.dirname(npy_path), exist_ok=True)
                        np.save(npy_path, asl_embedding)
                        print(f"   ✅ ASL embedding saved: {npy_path}")
                        print(f"      Shape: {asl_embedding.shape}, Mean: {asl_embedding.mean():.4f}")
                    else:
                        print(f"   ⚠️  No embedding file path specified")
                else:
                    print(f"   ⚠️  Failed to compute ASL embedding")
        
        # ===== BSL Embeddings =====
        for concept_id, concept_data in self.bsl_registry.items():
            if concept_id.startswith("_"):
                continue
            
            concept_name = concept_data.get("concept_name", concept_id)
            bsl_target = concept_data.get("target")
            
            if bsl_target and bsl_target.get("signature_file"):
                bsl_file = bsl_target["signature_file"]
                print(f"\n   🎯 BSL {concept_name}: {Path(bsl_file).name}")
                
                # Compute embedding (single BSL target)
                bsl_embedding = self._compute_signature_embedding(bsl_file)
                if bsl_embedding is not None:
                    # Save to .npy file
                    npy_path = concept_data.get("embedding_mean_file")
                    if npy_path:
                        os.makedirs(os.path.dirname(npy_path), exist_ok=True)
                        np.save(npy_path, bsl_embedding)
                        print(f"   ✅ BSL embedding saved: {npy_path}")
                        print(f"      Shape: {bsl_embedding.shape}, Mean: {bsl_embedding.mean():.4f}")
                    else:
                        print(f"   ⚠️  No embedding file path specified")
                else:
                    print(f"   ⚠️  Failed to compute BSL embedding")

    def save_registry(self):
        """Save updated registries with embeddings back to JSON."""
        asl_path = os.path.join(REGISTRIES_DIR, 'asl_registry.json')
        bsl_path = os.path.join(REGISTRIES_DIR, 'bsl_registry.json')
        
        with open(asl_path, 'w') as f:
            json.dump(self.asl_registry, f, indent=2)
        print(f"\n✅ ASL registry updated: {asl_path}")
        
        with open(bsl_path, 'w') as f:
            json.dump(self.bsl_registry, f, indent=2)
        print(f"✅ BSL registry updated: {bsl_path}")

    def compute_similarity_matrix(self) -> Optional[np.ndarray]:
        """
        Compute cosine similarity matrix between ASL and BSL embeddings.

        Returns: Matrix showing similarity between each concept pair.
        """
        print("\n" + "=" * 60)
        print("📈 ASL-BSL Similarity Analysis")
        print("=" * 60)
        
        from scipy.spatial.distance import cosine
        
        concepts = []
        asl_embeddings = []
        bsl_embeddings = []
        
        # Load embeddings from registries
        for concept_id in self.asl_registry.keys():
            if concept_id.startswith('_'):
                continue
            
            if concept_id not in self.bsl_registry:
                continue
            
            asl_file = self.asl_registry[concept_id].get("embedding_mean_file")
            bsl_file = self.bsl_registry[concept_id].get("embedding_mean_file")
            
            try:
                if asl_file and os.path.exists(asl_file):
                    asl_emb = np.load(asl_file)
                else:
                    continue
                
                if bsl_file and os.path.exists(bsl_file):
                    bsl_emb = np.load(bsl_file)
                else:
                    continue
                
                concepts.append(self.asl_registry[concept_id].get("concept_name"))
                asl_embeddings.append(asl_emb)
                bsl_embeddings.append(bsl_emb)
            except Exception as e:
                print(f"   ⚠️  Error loading embeddings for {concept_id}: {e}")
        
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
        print(f"   ASL registry: {os.path.join(REGISTRIES_DIR, 'asl_registry.json')}")
        print(f"   BSL registry: {os.path.join(REGISTRIES_DIR, 'bsl_registry.json')}")
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
