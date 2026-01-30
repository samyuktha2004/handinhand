#!/usr/bin/env python3
"""
Base Recognition Engine
=======================

Shared logic for sign language recognition:
- Landmark extraction (52 points: pose + hands + face)
- Body-centric normalization (shoulder center + width)
- Embedding computation (Global Average Pooling)
- Cosine similarity matching

Subclasses:
- RecognitionEngine: Basic CLI recognition
- RecognitionEngineUI: Full UI with dashboard, socket.io, cooldowns
"""

import numpy as np
import mediapipe as mp
import os
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass

from utils.registry_loader import RegistryLoader

# ============================================================================
# CONFIGURATION
# ============================================================================

# Recognition parameters
COSINE_SIM_THRESHOLD = 0.80
TIER_4_GAP_THRESHOLD = 0.15
WINDOW_SIZE = 30

# Quality filtering parameters
VISIBILITY_THRESHOLD = 0.5  # MediaPipe visibility score (0-1)
MIN_WINDOW_QUALITY = 0.7    # Require 70% of frames to have valid pose

# Landmark indices - MUST match extract_signatures.py
POSE_INDICES = [11, 12, 13, 14, 15, 16]  # Shoulders and arms (6)
FACE_INDICES = [70, 107, 300, 336]       # Eyebrows (4)

# Limb connections for skeleton validity checking
# Each tuple: (from_idx, to_idx) in combined landmark format
# Combined: pose[0:6] + left_hand[6:27] + right_hand[27:48] + face[48:52]
LIMB_CONNECTIONS = [
    # Pose: shoulders → elbows → wrists
    (0, 2),   # left_shoulder → left_elbow
    (2, 4),   # left_elbow → left_wrist
    (1, 3),   # right_shoulder → right_elbow
    (3, 5),   # right_elbow → right_wrist
    (0, 1),   # left_shoulder → right_shoulder
]

# In combined format: pose[0:6] + left_hand[6:27] + right_hand[27:48] + face[48:52]
SHOULDER_LEFT_IDX = 0   # First pose landmark
SHOULDER_RIGHT_IDX = 1  # Second pose landmark


@dataclass
class RecognitionResult:
    """Result of a recognition attempt."""
    concept_name: Optional[str]
    similarity_score: float
    confidence_level: str  # "high", "medium", "low"
    verification_status: str  # "verified", "low_confidence", "cross_concept_noise"
    all_scores: Dict[str, float]
    bsl_target_file: Optional[str] = None
    gap_to_second: float = 0.0


class BaseRecognitionEngine:
    """
    Base class with shared recognition logic.
    
    Subclass and override run() for different interfaces.
    """

    def __init__(self, language: str = 'asl'):
        """Initialize base engine components."""
        self.loader = RegistryLoader()
        self.concept_registry = self.loader.get_concept_registry()
        self.language_registry = self.loader.get_language_registry(language)
        self.embeddings = {}
        self.concept_names = []
        self.landmark_window = deque(maxlen=WINDOW_SIZE)
        
        # MediaPipe setup
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3,
        )
        
        # Load embeddings
        self._load_embeddings()
    
    def _load_embeddings(self) -> None:
        """Load embeddings from language registry."""
        for concept_id, concept_data in self.language_registry.items():
            if concept_id.startswith('_'):
                continue
            
            emb_file = concept_data.get("embedding_mean_file")
            if not emb_file or not os.path.exists(emb_file):
                continue
            
            try:
                concept_name = concept_data.get("concept_name")
                self.embeddings[concept_name] = np.load(emb_file)
                self.concept_names.append(concept_name)
            except Exception as e:
                print(f"⚠️  Failed to load {emb_file}: {e}")
        
        print(f"✅ Loaded {len(self.embeddings)} embeddings")
    
    def extract_landmarks(self, results) -> Optional[np.ndarray]:
        """
        Extract 52 landmarks from MediaPipe results with visibility filtering.
        
        Format: pose[6] + left_hand[21] + right_hand[21] + face[4] = 52
        
        Low-visibility landmarks are marked as [0, 0, 0] (missing).
        Returns None if pose is missing (can't normalize without shoulders).
        """
        if not results.pose_landmarks:
            return None
        
        landmarks = []
        visibility_mask = []  # Track which landmarks are valid
        
        # Pose (6 points: shoulders and arms)
        pose_full = results.pose_landmarks.landmark
        for idx in POSE_INDICES:
            lm = pose_full[idx]
            if lm.visibility >= VISIBILITY_THRESHOLD:
                landmarks.append([lm.x, lm.y, lm.z])
                visibility_mask.append(True)
            else:
                landmarks.append([0.0, 0.0, 0.0])
                visibility_mask.append(False)
        
        # Check that shoulders are valid (required for normalization)
        if not visibility_mask[SHOULDER_LEFT_IDX] or not visibility_mask[SHOULDER_RIGHT_IDX]:
            return None  # Can't normalize without both shoulders
        
        # Left hand (21 points or zeros)
        if results.left_hand_landmarks:
            for lm in results.left_hand_landmarks.landmark:
                # Hand landmarks don't have visibility, use presence check
                if hasattr(lm, 'visibility') and lm.visibility < VISIBILITY_THRESHOLD:
                    landmarks.append([0.0, 0.0, 0.0])
                else:
                    landmarks.append([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([[0.0, 0.0, 0.0]] * 21)
        
        # Right hand (21 points or zeros)
        if results.right_hand_landmarks:
            for lm in results.right_hand_landmarks.landmark:
                if hasattr(lm, 'visibility') and lm.visibility < VISIBILITY_THRESHOLD:
                    landmarks.append([0.0, 0.0, 0.0])
                else:
                    landmarks.append([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([[0.0, 0.0, 0.0]] * 21)
        
        # Face (4 points: eyebrows)
        if results.face_landmarks:
            face_full = results.face_landmarks.landmark
            for idx in FACE_INDICES:
                lm = face_full[idx]
                # Face landmarks don't have visibility, assume valid if present
                landmarks.append([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([[0.0, 0.0, 0.0]] * 4)
        
        return np.array(landmarks, dtype=np.float32)
    
    def is_frame_quality_good(self, landmarks: np.ndarray) -> bool:
        """
        Check if a frame has sufficient valid landmarks.
        
        A frame is considered good if:
        - Both shoulders are valid (for normalization)
        - At least one hand has some valid landmarks
        """
        if landmarks is None:
            return False
        
        # Check shoulders (indices 0, 1 in combined format)
        if np.allclose(landmarks[0], 0) or np.allclose(landmarks[1], 0):
            return False
        
        # Check that at least one hand has data
        left_hand = landmarks[6:27]  # Indices 6-26
        right_hand = landmarks[27:48]  # Indices 27-47
        
        left_valid = np.any(np.abs(left_hand) > 0.01)
        right_valid = np.any(np.abs(right_hand) > 0.01)
        
        return left_valid or right_valid
    
    def check_skeleton_connectivity(self, landmarks: np.ndarray) -> bool:
        """
        Check that connected limbs have valid endpoints.
        
        Returns True if skeleton is well-connected.
        """
        if landmarks is None:
            return False
        
        for from_idx, to_idx in LIMB_CONNECTIONS:
            from_valid = not np.allclose(landmarks[from_idx], 0)
            to_valid = not np.allclose(landmarks[to_idx], 0)
            
            # Both endpoints of a limb must be valid
            if not (from_valid and to_valid):
                return False
        
        return True
    
    def normalize_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Body-centric normalization.
        
        1. Center on shoulder midpoint (translation invariance)
        2. Scale by shoulder width (scale invariance)
        """
        if landmarks.shape[0] < 6:
            return landmarks
        
        # Shoulders are at indices 0 and 1 in combined format
        shoulder_left = landmarks[SHOULDER_LEFT_IDX][:2]
        shoulder_right = landmarks[SHOULDER_RIGHT_IDX][:2]
        shoulder_center = (shoulder_left + shoulder_right) / 2.0
        
        # Translation invariance
        normalized = landmarks.copy()
        normalized[:, :2] -= shoulder_center
        
        # Scale invariance
        shoulder_width = np.linalg.norm(shoulder_left - shoulder_right)
        if shoulder_width > 0.01:
            normalized[:, :2] /= shoulder_width
        
        return normalized
    
    def compute_embedding(self) -> Optional[np.ndarray]:
        """
        Compute embedding from landmark window using Global Average Pooling.
        
        Applies window quality gate: requires MIN_WINDOW_QUALITY (70%) of frames
        to have good quality landmarks.
        
        Uses masked averaging to ignore zero-valued (missing) landmarks.
        
        Returns 512-dim vector or None if window incomplete or low quality.
        """
        if len(self.landmark_window) < WINDOW_SIZE:
            return None
        
        # Window quality gate: check that enough frames have good landmarks
        good_frames = sum(1 for lm in self.landmark_window if self.is_frame_quality_good(lm))
        quality_ratio = good_frames / len(self.landmark_window)
        
        if quality_ratio < MIN_WINDOW_QUALITY:
            return None  # Window quality too low
        
        # Normalize and flatten each frame with masked averaging
        frame_features = []
        for landmarks in self.landmark_window:
            normalized = self.normalize_landmarks(landmarks)
            features = normalized.flatten().astype(np.float32)
            
            # Pad to 512 if needed
            if len(features) < 512:
                features = np.pad(features, (0, 512 - len(features)), mode='constant')
            
            frame_features.append(features[:512])
        
        # Convert to array for masked operations
        frame_array = np.array(frame_features, dtype=np.float32)
        
        # Create mask for zero values (missing landmarks)
        # Use masked array to ignore zeros in mean computation
        masked_frames = np.ma.masked_where(frame_array == 0, frame_array)
        
        # Global Average Pooling with masked mean
        embedding = np.ma.mean(masked_frames, axis=0).filled(0)
        
        return embedding.astype(np.float32)
    
    def match_embedding(self, live_embedding: np.ndarray) -> RecognitionResult:
        """
        Match live embedding against stored embeddings using cosine similarity.
        
        Applies Tier 4 validation:
        - Best match must exceed COSINE_SIM_THRESHOLD
        - Gap to second-best must exceed TIER_4_GAP_THRESHOLD
        """
        from scipy.spatial.distance import cosine
        
        # Score against all concepts
        scores = {}
        for concept_name, stored_embedding in self.embeddings.items():
            similarity = 1 - cosine(live_embedding, stored_embedding)
            scores[concept_name] = similarity
        
        if not scores:
            return RecognitionResult(
                concept_name=None,
                similarity_score=0.0,
                confidence_level="low",
                verification_status="no_embeddings",
                all_scores={},
            )
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_concept, best_score = sorted_scores[0]
        
        # Calculate gap to second-best
        gap = 0.0
        if len(sorted_scores) > 1:
            gap = best_score - sorted_scores[1][1]
        
        # Tier 4 validation
        if best_score < COSINE_SIM_THRESHOLD:
            status = "low_confidence"
        elif gap < TIER_4_GAP_THRESHOLD:
            status = "cross_concept_noise"
        else:
            status = "verified"
        
        # Confidence level
        if best_score >= 0.90:
            confidence = "high"
        elif best_score >= 0.80:
            confidence = "medium"
        else:
            confidence = "low"
        
        return RecognitionResult(
            concept_name=best_concept,
            similarity_score=best_score,
            confidence_level=confidence,
            verification_status=status,
            all_scores=scores,
            gap_to_second=gap,
        )
    
    def add_landmarks(self, landmarks: np.ndarray) -> None:
        """Add landmarks to sliding window."""
        self.landmark_window.append(landmarks)
    
    def reset_window(self) -> None:
        """Clear the landmark window."""
        self.landmark_window.clear()
    
    def close(self) -> None:
        """Release resources."""
        self.holistic.close()
