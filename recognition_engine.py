#!/usr/bin/env python3
"""
Real-Time Sign Language Recognition Engine
===========================================

Pipeline:
1. Capture live webcam → MediaPipe Holistic landmarks
2. Normalize landmarks (body-centric: shoulder center)
3. Compute embedding (Global Average Pooling over sliding window)
4. Score against all stored ASL embeddings via Cosine Similarity
5. Apply Tier 4 validation: Best match must exceed threshold
6. Output: Recognized concept + confidence score + BSL target

Optional Debug Mode:
- Ghost visualization: Live skeleton + golden signature skeleton
- Cosine similarity bar chart (per-concept scores)
- Body-centric normalization verification

Usage:
    python3 recognition_engine.py
    python3 recognition_engine.py --debug
    python3 recognition_engine.py --debug --delay 5000  (5s delay for demo)
"""

import cv2
import numpy as np
import json
import mediapipe as mp
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import deque
from dataclasses import dataclass
import sys

# ============================================================================
# CONFIGURATION
# ============================================================================
TRANSLATION_REGISTRY = "translation_map.json"
EMBEDDINGS_DIR = "assets/embeddings"
SIGNATURES_DIR = "assets/signatures"

# Recognition parameters
COSINE_SIM_THRESHOLD = 0.80  # Tier 4: Must exceed this to trigger
TIER_4_GAP_THRESHOLD = 0.15  # Second-best must be 15+ points lower
WINDOW_SIZE = 30             # Frames to accumulate before computing embedding
CONFIDENCE_DISPLAY_THRESHOLD = 0.50  # Only show concepts > this in debug

# Landmark indices
SHOULDER_CENTER_LEFT = 11
SHOULDER_CENTER_RIGHT = 12
NOSE = 0

# Colors for visualization
COLOR_LIVE = (0, 255, 0)      # Bright green for live
COLOR_GHOST = (100, 100, 100) # Faint grey for golden signature
COLOR_MATCHED = (0, 255, 255) # Cyan for matched concept


@dataclass
class RecognitionResult:
    """Result of a recognition attempt."""
    concept_name: str
    cosine_similarity: float
    confidence_level: str  # "high" (0.90+), "medium" (0.80-0.90), "low" (< 0.80)
    all_scores: Dict[str, float]  # All concept scores
    bsl_target_file: str
    verification_status: str  # "verified", "low_confidence", "cross_concept_noise"
    
    def __str__(self):
        return f"{self.concept_name}: {self.cosine_similarity:.3f} ({self.confidence_level})"


class RecognitionEngine:
    """Real-time sign language recognition with Tier 4 validation."""

    def __init__(self, debug: bool = False):
        """Initialize recognition engine."""
        self.debug = debug
        self.registry = self._load_registry()
        self.embeddings = self._load_embeddings()
        self.landmark_window = deque(maxlen=WINDOW_SIZE)
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        
        # MediaPipe setup
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        
        if debug:
            print("🔍 DEBUG MODE ENABLED")
            print("   - Ghost visualization: ON (live + golden signature)")
            print("   - Cosine similarity scores: VISIBLE (per-concept)")
            print("   - Tier 4 validation: ACTIVE (cross-concept check)")

    def _load_registry(self) -> Dict:
        """Load translation registry."""
        if not os.path.exists(TRANSLATION_REGISTRY):
            raise FileNotFoundError(f"Registry not found: {TRANSLATION_REGISTRY}")
        
        with open(TRANSLATION_REGISTRY) as f:
            return json.load(f)

    def _load_embeddings(self) -> Dict[str, np.ndarray]:
        """Load all ASL embeddings from .npy files."""
        embeddings = {}
        
        for concept_key, concept_data in self.registry.items():
            if concept_key.startswith("_"):
                continue
            
            concept_name = concept_data.get("concept_name")
            emb_file = concept_data.get("asl_embedding_mean_file")
            
            if emb_file and os.path.exists(emb_file):
                embeddings[concept_name] = np.load(emb_file)
        
        print(f"✅ Loaded {len(embeddings)} concept embeddings")
        return embeddings

    def _normalize_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Normalize landmarks to be body-centric (relative to shoulder center).
        
        Same normalization as used in embedding generation.
        """
        if landmarks.shape[0] <= 12:
            return landmarks
        
        # Get shoulder center (indices 11 and 12)
        shoulder_left = landmarks[SHOULDER_CENTER_LEFT][:2]  # x, y only
        shoulder_right = landmarks[SHOULDER_CENTER_RIGHT][:2]
        shoulder_center = (shoulder_left + shoulder_right) / 2.0
        
        # Normalize: subtract shoulder center from all points (x, y only)
        landmarks_normalized = landmarks.copy()
        landmarks_normalized[:, :2] -= shoulder_center
        
        return landmarks_normalized

    def _extract_frame_features(self, frame_idx: int) -> Optional[np.ndarray]:
        """
        Extract features from current window of landmarks.
        
        Process:
        1. Get latest 52 landmarks (pose + hands + face) from window
        2. Normalize (body-centric)
        3. Flatten to 1D vector
        """
        if len(self.landmark_window) == 0:
            return None
        
        # Use latest frame in window
        landmarks = self.landmark_window[-1]
        
        # Normalize (body-centric)
        landmarks_norm = self._normalize_landmarks(landmarks)
        
        # Flatten
        features = landmarks_norm.flatten().astype(np.float32)
        
        # Pad to 512 if needed (same as embedding generation)
        if len(features) < 512:
            features = np.pad(features, (0, 512 - len(features)), mode='constant')
        
        return features[:512]

    def _compute_live_embedding(self) -> Optional[np.ndarray]:
        """
        Compute embedding from accumulated window.
        
        Global Average Pooling: average all frames in window.
        """
        if len(self.landmark_window) == 0:
            return None
        
        # Extract features for each frame in window
        frame_features = []
        for i in range(len(self.landmark_window)):
            # Get landmarks for frame i
            landmarks = self.landmark_window[i]
            landmarks_norm = self._normalize_landmarks(landmarks)
            features = landmarks_norm.flatten().astype(np.float32)
            
            # Pad to 512
            if len(features) < 512:
                features = np.pad(features, (0, 512 - len(features)), mode='constant')
            
            frame_features.append(features[:512])
        
        # Global Average Pooling: average across all frames in window
        live_embedding = np.mean(frame_features, axis=0)
        return live_embedding.astype(np.float32)

    def recognize(self) -> Optional[RecognitionResult]:
        """
        Attempt recognition using Cosine Similarity + Tier 4 validation.
        
        Tier 4: Cross-concept confidence validation
        - Best match must exceed COSINE_SIM_THRESHOLD
        - Second-best must be TIER_4_GAP_THRESHOLD lower
        - Prevents "noisy" signals matching wrong concepts
        """
        if len(self.landmark_window) < WINDOW_SIZE:
            return None  # Need full window to recognize
        
        # Compute live embedding
        live_embedding = self._compute_live_embedding()
        if live_embedding is None:
            return None
        
        # Score against all concepts via Cosine Similarity
        from scipy.spatial.distance import cosine
        
        scores = {}
        for concept_name, stored_embedding in self.embeddings.items():
            # Cosine similarity = 1 - cosine distance
            similarity = 1 - cosine(live_embedding, stored_embedding)
            scores[concept_name] = similarity
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_concept, best_score = sorted_scores[0]
        
        # Tier 4: Cross-concept validation
        if best_score < COSINE_SIM_THRESHOLD:
            status = "low_confidence"
        elif len(sorted_scores) > 1:
            second_concept, second_score = sorted_scores[1]
            gap = best_score - second_score
            
            if gap < TIER_4_GAP_THRESHOLD:
                status = "cross_concept_noise"  # Ambiguous match
            else:
                status = "verified"
        else:
            status = "verified"
        
        # Determine confidence level
        if best_score >= 0.90:
            confidence_level = "high"
        elif best_score >= 0.80:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Get BSL target
        bsl_target = "unknown.json"
        for concept_key, concept_data in self.registry.items():
            if concept_data.get("concept_name") == best_concept:
                bsl_target = concept_data.get("bsl_target", {}).get("signature_file", "unknown.json")
                break
        
        return RecognitionResult(
            concept_name=best_concept,
            cosine_similarity=best_score,
            confidence_level=confidence_level,
            all_scores=scores,
            bsl_target=bsl_target,
            verification_status=status
        )

    def _draw_skeleton(self, frame: np.ndarray, landmarks: np.ndarray, color: Tuple, alpha: float = 1.0) -> np.ndarray:
        """Draw skeleton on frame (live or ghost)."""
        if landmarks is None or len(landmarks) == 0:
            return frame
        
        h, w = frame.shape[:2]
        
        # Draw pose connections
        POSE_CONNECTIONS = [
            (11, 12),  # shoulders
            (11, 13), (13, 15),  # left arm
            (12, 14), (14, 16),  # right arm
            (11, 23), (12, 24),  # torso to hips
        ]
        
        # Draw hand connections (simplified - just wrists + fingers)
        HAND_WRISTS = [(16, 18), (15, 17)]  # wrists to elbows
        
        # Create overlay for alpha blending
        overlay = frame.copy()
        
        # Draw pose
        for connection in POSE_CONNECTIONS:
            start, end = connection
            if start < len(landmarks) and end < len(landmarks):
                x1, y1 = int(landmarks[start][0] * w), int(landmarks[start][1] * h)
                x2, y2 = int(landmarks[end][0] * w), int(landmarks[end][1] * h)
                
                if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                    cv2.line(overlay, (x1, y1), (x2, y2), color, 2)
        
        # Draw hand wrists
        for connection in HAND_WRISTS:
            start, end = connection
            if start < len(landmarks) and end < len(landmarks):
                x1, y1 = int(landmarks[start][0] * w), int(landmarks[start][1] * h)
                x2, y2 = int(landmarks[end][0] * w), int(landmarks[end][1] * h)
                
                if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                    cv2.line(overlay, (x1, y1), (x2, y2), color, 1)
        
        # Draw joints (circles)
        for landmark in landmarks[:25]:  # Just pose landmarks
            x, y = int(landmark[0] * w), int(landmark[1] * h)
            if 0 <= x < w and 0 <= y < h:
                cv2.circle(overlay, (x, y), 3, color, -1)
        
        # Blend with original frame
        result = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        return result

    def _draw_debug_info(self, frame: np.ndarray, result: Optional[RecognitionResult]) -> np.ndarray:
        """Draw debug information on frame."""
        if not self.debug:
            return frame
        
        h, w = frame.shape[:2]
        y_offset = 30
        
        # Window fill indicator
        fill_pct = (len(self.landmark_window) / WINDOW_SIZE) * 100
        cv2.putText(frame, f"Window: {fill_pct:.0f}%", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        if result:
            # Best match
            y_offset += 30
            cv2.putText(frame, f"BEST: {result.concept_name}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_MATCHED, 2)
            
            # Score bar
            y_offset += 30
            bar_length = int(result.cosine_similarity * 300)
            color = (0, 255, 0) if result.cosine_similarity > 0.85 else (0, 165, 255)
            cv2.rectangle(frame, (10, y_offset), (10 + bar_length, y_offset + 20), color, -1)
            cv2.rectangle(frame, (10, y_offset), (310, y_offset + 20), (255, 255, 255), 1)
            cv2.putText(frame, f"{result.cosine_similarity:.3f}", (320, y_offset + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Status
            y_offset += 40
            status_colors = {
                "verified": (0, 255, 0),
                "low_confidence": (0, 165, 255),
                "cross_concept_noise": (0, 0, 255)
            }
            status_color = status_colors.get(result.verification_status, (255, 255, 255))
            cv2.putText(frame, f"Tier 4: {result.verification_status}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 1)
            
            # All scores (concepts > threshold only)
            y_offset += 30
            cv2.putText(frame, "Scores:", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            
            for i, (concept, score) in enumerate(sorted(result.all_scores.items(), 
                                                        key=lambda x: x[1], reverse=True)):
                if score > CONFIDENCE_DISPLAY_THRESHOLD:
                    y_offset += 20
                    cv2.putText(frame, f"  {concept[:20]}: {score:.3f}", 
                               (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return frame

    def run(self, camera_id: int = 0, delay: int = 1):
        """Run live recognition."""
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print("❌ Failed to open camera")
            return False
        
        print(f"📹 Starting live recognition (ESC to quit)")
        if self.debug:
            print(f"🔍 Debug mode: Ghost visualization + scores visible")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame = cv2.flip(frame, 1)  # Mirror for selfie view
                h, w = frame.shape[:2]
                
                # MediaPipe processing
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.holistic.process(rgb_frame)
                
                # Extract landmarks
                if results.pose_landmarks:
                    landmarks = np.array([
                        [lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark
                    ])
                    self.landmark_window.append(landmarks)
                
                # Attempt recognition
                result = self.recognize()
                
                # Draw debug visualization (if enabled)
                if self.debug and results.pose_landmarks:
                    landmarks = np.array([
                        [lm.x, lm.y, lm.z] for lm in results.pose_landmarks.landmark
                    ])
                    
                    # Draw live skeleton (bold green)
                    frame = self._draw_skeleton(frame, landmarks, COLOR_LIVE, alpha=0.8)
                    
                    # TODO: Draw ghost skeleton (golden signature)
                    # Would require loading signature JSON and extracting pose at specific frame
                    # For now, just show live + scores
                
                # Draw debug info
                frame = self._draw_debug_info(frame, result)
                
                # Display result
                if result and result.verification_status == "verified":
                    status_text = f"✅ {result} ({result.verification_status})"
                    cv2.putText(frame, status_text, (10, h - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                elif result:
                    status_text = f"⚠️ {result} ({result.verification_status})"
                    cv2.putText(frame, status_text, (10, h - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                
                # Show frame
                cv2.imshow("Sign Language Recognition", frame)
                
                # Check for exit
                if cv2.waitKey(delay) & 0xFF == 27:  # ESC
                    break
            
            return True
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.holistic.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time sign language recognition")
    parser.add_argument("--debug", action="store_true", help="Enable debug visualization (ghost + scores)")
    parser.add_argument("--delay", type=int, default=1, help="Webcam delay (1=normal, 5000=5sec for demo)")
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID (default: 0)")
    
    args = parser.parse_args()
    
    try:
        engine = RecognitionEngine(debug=args.debug)
        success = engine.run(camera_id=args.camera, delay=args.delay)
        return 0 if success else 1
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
