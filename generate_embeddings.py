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
from utils.landmarks import (
    TOTAL_LANDMARKS, TOTAL_LANDMARKS_EMBED,
    LEFT_SHOULDER_IDX, RIGHT_SHOULDER_IDX,
    FACE_START, FACE_EMBED_OFFSETS,
)

# ============================================================================
# CONFIGURATION
# ============================================================================
REGISTRIES_DIR = "assets/registries"
EMBEDDINGS_DIR = "assets/embeddings"
SIGNATURES_DIR = "assets/signatures"

# Landmark indices for pose normalization (within compact 6-point pose array)
SHOULDER_CENTER_LEFT  = LEFT_SHOULDER_IDX   # 0 in compact pose, MediaPipe index 11
SHOULDER_CENTER_RIGHT = RIGHT_SHOULDER_IDX  # 1 in compact pose, MediaPipe index 12

# Embedding dimension (Global Average Pooling output)
EMBEDDING_DIM = 512


class EmbeddingGenerator:
    """Generate normalized embeddings from landmark sequences."""

    def __init__(self):
        """Initialize generator."""
        self.embeddings_dir = Path("assets/embeddings")
        self.loader = RegistryLoader()
        self.concept_registry = self.loader.get_concept_registry()
        self.asl_registry = self.loader.get_language_registry('asl')
        self.bsl_registry = self.loader.get_language_registry('bsl')
        self.embeddings_asl = {}
        self.embeddings_bsl = {}
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure embedding output directories exist."""
        for subdir in ['asl', 'bsl', 'concept']:
            path = self.embeddings_dir / subdir
            path.mkdir(parents=True, exist_ok=True)

    def _load_signature(self, sig_file: str) -> Optional[Dict]:
        """Load signature JSON file."""
        try:
            with open(sig_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"      ⚠️  Error loading {sig_file}: {str(e)[:50]}")
            return None

    def _normalize_landmarks(
        self,
        landmarks: List[List[float]],
        shoulder_center: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Normalize landmarks to be body-centric (relative to shoulder center).
        
        Process:
        1. Calculate shoulder center: mean of left (11) and right (12) shoulders
        2. Subtract center from all landmarks
        3. Return normalized array
        """
        landmarks = np.array(landmarks, dtype=np.float32)

        # If caller provided shoulder center, use it (common case)
        if shoulder_center is not None:
            landmarks_normalized = landmarks.copy()
            valid_mask = np.logical_not(
                (np.abs(landmarks_normalized[:, 0]) < 1e-6)
                & (np.abs(landmarks_normalized[:, 1]) < 1e-6)
            )
            landmarks_normalized[valid_mask, :2] -= shoulder_center[:2]
            return landmarks_normalized

        # Heuristics: detect shoulders from pose block (first two points if present)
        landmarks_normalized = landmarks.copy()
        if landmarks.shape[0] >= 2:
            left = landmarks[0][:2]
            right = landmarks[1][:2]
            # If coordinates look like normalized coords (0..1) or pixel coords (>1), both handled
            if (np.linalg.norm(left) > 0.0) and (np.linalg.norm(right) > 0.0):
                shoulder_center = (left + right) / 2.0
                valid_mask = np.logical_not(
                    (np.abs(landmarks_normalized[:, 0]) < 1e-6)
                    & (np.abs(landmarks_normalized[:, 1]) < 1e-6)
                )
                landmarks_normalized[valid_mask, :2] -= shoulder_center[:2]
                return landmarks_normalized

        # Fallback: if landmarks include full body ordering and known indices (legacy), try those
        if landmarks.shape[0] > max(SHOULDER_CENTER_LEFT, SHOULDER_CENTER_RIGHT):
            shoulder_left = landmarks[SHOULDER_CENTER_LEFT][:2]
            shoulder_right = landmarks[SHOULDER_CENTER_RIGHT][:2]
            shoulder_center = (shoulder_left + shoulder_right) / 2.0
            valid_mask = np.logical_not(
                (np.abs(landmarks_normalized[:, 0]) < 1e-6)
                & (np.abs(landmarks_normalized[:, 1]) < 1e-6)
            )
            landmarks_normalized[valid_mask, :2] -= shoulder_center[:2]
            return landmarks_normalized

        # Last resort: return as-is
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
        # Build joint array (pose + left_hand + right_hand + face) as before
        landmarks = []
        shoulder_center = None

        pose = frame_data.get('pose')
        if pose:
            pose_len = len(pose)
            if pose_len > 12:
                left = pose[SHOULDER_CENTER_LEFT]
                right = pose[SHOULDER_CENTER_RIGHT]
            elif pose_len >= 2:
                left = pose[0]
                right = pose[1]
            else:
                left = None
                right = None

            if left is not None and right is not None:
                left_arr = np.array(left, dtype=np.float32)
                right_arr = np.array(right, dtype=np.float32)
                if np.linalg.norm(left_arr[:2]) > 1.0 or np.linalg.norm(right_arr[:2]) > 1.0:
                    if np.linalg.norm(left_arr[:2] - right_arr[:2]) > 1.0:
                        shoulder_center = np.array(
                            [(left_arr[0] + right_arr[0]) / 2.0, (left_arr[1] + right_arr[1]) / 2.0, 0.0],
                            dtype=np.float32,
                        )

        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if key in frame_data and frame_data[key]:
                for pt in frame_data[key]:
                    if len(pt) == 2:
                        landmarks.append([pt[0], pt[1], 0.0])
                    else:
                        landmarks.append(pt[:3])

        if len(landmarks) == 0:
            return np.zeros(TOTAL_LANDMARKS_EMBED * 3, dtype=np.float32)

        landmarks = np.array(landmarks, dtype=np.float32)

        # Select embedding-relevant face points (FACE_INDICES_EMBED subset of FACE_INDICES_EXTRACT).
        # Keeps pose+hand (first FACE_START=48 pts) + 7 selected face pts = 55 pts total.
        # Handles face:4, face:7, and face:20 formats — missing offsets are zero-padded.
        if len(landmarks) > FACE_START:
            face_sub = landmarks[FACE_START:]
            embed_face = np.zeros((len(FACE_EMBED_OFFSETS), 3), dtype=np.float32)
            for i, off in enumerate(FACE_EMBED_OFFSETS):
                if off < len(face_sub):
                    embed_face[i] = face_sub[off]
            landmarks = np.vstack([landmarks[:FACE_START], embed_face])

        # Joint stream: body-centric normalized flattened joints
        joints_norm = self._normalize_landmarks(landmarks, shoulder_center=shoulder_center)
        joint_feat = joints_norm.flatten().astype(np.float32)

        return joint_feat

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
        
        # --- Multi-stream extraction: joint, bone, joint_motion, bone_motion ---
        joint_features = []
        bone_features = []
        joint_motion = []
        bone_motion = []

        prev_joints = None
        prev_bones = None

        for frame in frames:
            joints = self._frame_to_embedding(frame)
            joint_features.append(joints)

            # bone features: simple difference between consecutive landmarks
            # reshape joints into (N,3)
            num_coords = joints.shape[0] // 3
            joints_xy = joints.reshape((num_coords, 3))[:, :2]
            bones = (joints_xy[1:] - joints_xy[:-1]).flatten().astype(np.float32)
            bone_features.append(bones)

            if prev_joints is None:
                joint_motion.append(np.zeros_like(joints))
            else:
                joint_motion.append(joints - prev_joints)

            if prev_bones is None:
                bone_motion.append(np.zeros_like(bones))
            else:
                # pads/truncates to match
                minlen = min(len(bones), len(prev_bones))
                bm = np.zeros_like(bones)
                bm[:minlen] = bones[:minlen] - prev_bones[:minlen]
                bone_motion.append(bm)

            prev_joints = joints
            prev_bones = bones

        # Average each stream across frames
        joint_avg = np.mean(joint_features, axis=0)
        bone_avg = np.mean(bone_features, axis=0)
        jm_avg = np.mean(joint_motion, axis=0)
        bm_avg = np.mean(bone_motion, axis=0)

        # Concatenate streams (joint + bone + joint_motion + bone_motion)
        combined = np.concatenate([joint_avg, bone_avg, jm_avg, bm_avg])

        # Pad/reshape combined to EMBEDDING_DIM
        if len(combined) < EMBEDDING_DIM:
            combined = np.pad(combined, (0, EMBEDDING_DIM - len(combined)), mode='constant')
        else:
            combined = combined[:EMBEDDING_DIM]

        # Also return joint-only embedding for ablation comparison
        if len(joint_avg) < EMBEDDING_DIM:
            joint_emb = np.pad(joint_avg, (0, EMBEDDING_DIM - len(joint_avg)), mode='constant')
        else:
            joint_emb = joint_avg[:EMBEDDING_DIM]

        return {
            'joint': joint_emb.astype(np.float32),
            'combined': combined.astype(np.float32),
        }

    def _compute_aggregated_embedding(self, sig_files: List[str]) -> Optional[np.ndarray]:
        """
        Compute aggregated embedding across multiple instances.
        
        Process:
        1. For each signature file: compute individual embedding
        2. Average embeddings across all instances
        3. Return aggregated embedding (robust across signers/contexts)
        """
        # Return both joint-only and combined aggregated embeddings
        joint_embs = []
        combined_embs = []

        for sig_file in sig_files:
            res = self._compute_signature_embedding(sig_file)
            if res is not None:
                joint_embs.append(res['joint'])
                combined_embs.append(res['combined'])

        if not joint_embs:
            return None

        joint_agg = np.mean(joint_embs, axis=0)
        combined_agg = np.mean(combined_embs, axis=0)

        return {
            'joint': joint_agg.astype(np.float32),
            'combined': combined_agg.astype(np.float32),
        }

    def generate_embeddings(self):
        """Generate embeddings for all concepts in registries."""
        print("\n" + "=" * 60)
        print("🧮 Embedding Generation Pipeline")
        print("=" * 60)
        print(f"ASL Registry: {os.path.join(REGISTRIES_DIR, 'asl_registry.json')}")
        print(f"BSL Registry: {os.path.join(REGISTRIES_DIR, 'bsl_registry.json')}")
        print(f"Output dir: {EMBEDDINGS_DIR}/")
        print("=" * 60)
        
        # We'll compute both joint-only and combined embeddings and write both
        joint_map = {}
        combined_map = {}

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
                
                # Compute aggregated embeddings (joint + combined)
                asl_embs = self._compute_aggregated_embedding(asl_files)
                if asl_embs is not None:
                    # Save joint-only and combined embeddings to separate files
                    base_npy = concept_data.get("embedding_mean_file")
                    if base_npy:
                        os.makedirs(os.path.dirname(base_npy), exist_ok=True)
                        joint_path = base_npy.replace('.npy', '_joint.npy')
                        combined_path = base_npy.replace('.npy', '_combined.npy')
                        np.save(joint_path, asl_embs['joint'])
                        np.save(combined_path, asl_embs['combined'])
                        joint_map[concept_id] = joint_path
                        combined_map[concept_id] = combined_path
                        print(f"   ✅ ASL joint saved: {joint_path}")
                        print(f"   ✅ ASL combined saved: {combined_path}")
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
                    npy_path = concept_data.get("embedding_mean_file")
                    if npy_path:
                        os.makedirs(os.path.dirname(npy_path), exist_ok=True)
                        joint_path = npy_path.replace('.npy', '_joint.npy')
                        combined_path = npy_path.replace('.npy', '_combined.npy')
                        np.save(joint_path, bsl_embedding['joint'])
                        np.save(combined_path, bsl_embedding['combined'])
                        joint_map[concept_id] = joint_path
                        combined_map[concept_id] = combined_path
                        print(f"   ✅ BSL joint saved: {joint_path}")
                        print(f"   ✅ BSL combined saved: {combined_path}")
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
