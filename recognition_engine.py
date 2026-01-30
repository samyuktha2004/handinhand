#!/usr/bin/env python3
"""
Real-Time Sign Language Recognition Engine
===========================================

Lightweight CLI recognition engine using BaseRecognitionEngine.

Usage:
    python3 recognition_engine.py
    python3 recognition_engine.py --debug
    python3 recognition_engine.py --debug --delay 5000
"""

import cv2
import numpy as np
import sys
from typing import Optional, Tuple

from recognition_base import (
    BaseRecognitionEngine,
    RecognitionResult,
    WINDOW_SIZE,
    COSINE_SIM_THRESHOLD,
)

# Colors for visualization
COLOR_LIVE = (0, 255, 0)      # Green for live skeleton
COLOR_MATCHED = (0, 255, 255) # Cyan for matched concept


class RecognitionEngine(BaseRecognitionEngine):
    """Real-time sign language recognition with optional debug visualization."""

    def __init__(self, debug: bool = False):
        """Initialize recognition engine."""
        super().__init__(language='asl')
        self.debug = debug
        self.registry = self.language_registry  # Legacy compat
        
        if debug:
            print("🔍 DEBUG MODE ENABLED")

    def _draw_skeleton(self, frame: np.ndarray, landmarks: np.ndarray, 
                       color: Tuple, alpha: float = 1.0) -> np.ndarray:
        """Draw skeleton on frame."""
        if landmarks is None or len(landmarks) == 0:
            return frame
        
        h, w = frame.shape[:2]
        
        POSE_CONNECTIONS = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
        ]
        
        overlay = frame.copy()
        
        for start, end in POSE_CONNECTIONS:
            if start < len(landmarks) and end < len(landmarks):
                x1, y1 = int(landmarks[start][0] * w), int(landmarks[start][1] * h)
                x2, y2 = int(landmarks[end][0] * w), int(landmarks[end][1] * h)
                if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                    cv2.line(overlay, (x1, y1), (x2, y2), color, 2)
        
        for i, landmark in enumerate(landmarks[:25]):
            x, y = int(landmark[0] * w), int(landmark[1] * h)
            if 0 <= x < w and 0 <= y < h:
                cv2.circle(overlay, (x, y), 3, color, -1)
        
        return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    def _draw_debug_info(self, frame: np.ndarray, result: Optional[RecognitionResult]) -> np.ndarray:
        """Draw debug overlay."""
        if not self.debug:
            return frame
        
        y = 30
        fill_pct = (len(self.landmark_window) / WINDOW_SIZE) * 100
        cv2.putText(frame, f"Window: {fill_pct:.0f}%", (10, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        if result and result.concept_name:
            y += 30
            cv2.putText(frame, f"BEST: {result.concept_name}", (10, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_MATCHED, 2)
            
            y += 30
            bar_len = int(result.similarity_score * 300)
            color = (0, 255, 0) if result.similarity_score > 0.85 else (0, 165, 255)
            cv2.rectangle(frame, (10, y), (10 + bar_len, y + 20), color, -1)
            cv2.rectangle(frame, (10, y), (310, y + 20), (255, 255, 255), 1)
            cv2.putText(frame, f"{result.similarity_score:.3f}", (320, y + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            y += 40
            status_colors = {"verified": (0, 255, 0), "low_confidence": (0, 165, 255), 
                           "cross_concept_noise": (0, 0, 255)}
            cv2.putText(frame, f"Tier 4: {result.verification_status}", (10, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                       status_colors.get(result.verification_status, (255, 255, 255)), 1)
        
        return frame

    def run(self, camera_id: int = 0, delay: int = 1) -> bool:
        """Run live recognition loop."""
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print("❌ Failed to open camera")
            return False
        
        print(f"📹 Starting live recognition (ESC to quit)")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame = cv2.flip(frame, 1)
                h, w = frame.shape[:2]
                
                # Process with MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.holistic.process(rgb_frame)
                
                # Extract and add landmarks
                landmarks = self.extract_landmarks(results)
                if landmarks is not None:
                    self.add_landmarks(landmarks)
                
                # Attempt recognition
                result = None
                embedding = self.compute_embedding()
                if embedding is not None:
                    result = self.match_embedding(embedding)
                
                # Draw visualization
                if self.debug and results.pose_landmarks:
                    full_pose = np.array([[lm.x, lm.y, lm.z] 
                                         for lm in results.pose_landmarks.landmark])
                    frame = self._draw_skeleton(frame, full_pose, COLOR_LIVE, alpha=0.8)
                
                frame = self._draw_debug_info(frame, result)
                
                # Display result
                if result and result.verification_status == "verified":
                    cv2.putText(frame, f"✓ {result.concept_name}: {result.similarity_score:.3f}", 
                               (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow("Sign Language Recognition", frame)
                
                if cv2.waitKey(delay) & 0xFF == 27:
                    break
            
            return True
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time sign recognition")
    parser.add_argument("--debug", action="store_true", help="Enable debug visualization")
    parser.add_argument("--delay", type=int, default=1, help="Frame delay (ms)")
    parser.add_argument("--camera", type=int, default=0, help="Camera ID")
    
    args = parser.parse_args()
    
    try:
        engine = RecognitionEngine(debug=args.debug)
        return 0 if engine.run(camera_id=args.camera, delay=args.delay) else 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
