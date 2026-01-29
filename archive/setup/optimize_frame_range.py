#!/usr/bin/env python3
"""
Frame Range Optimizer for Sign Language Videos
===============================================

Analyzes a video to find the best frame range that includes:
- Both hands (left_hand AND right_hand detected)
- Face (for NMS - Non-Maximum Suppression cleanup)
- Minimal idle/zero frames

Usage:
    python3 optimize_frame_range.py <video_path> [--preview]
"""

import cv2
import mediapipe as mp
import argparse
from pathlib import Path
from typing import Tuple, List


class FrameRangeOptimizer:
    """Find optimal frame ranges for sign extraction."""

    def __init__(self, video_path: str):
        """Initialize with video path."""
        self.video_path = video_path
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.3,  # Lower threshold to catch more
            min_tracking_confidence=0.3,
        )

    def analyze_video(self) -> Tuple[List[dict], int]:
        """
        Scan entire video and report detection quality per frame.
        
        Returns:
            (list of frame stats, total frames)
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"❌ Could not open: {self.video_path}")
            return [], 0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"\n📊 Analyzing video: {Path(self.video_path).name}")
        print(f"   Total frames: {total_frames}, FPS: {fps:.1f}")
        print(f"   Duration: {total_frames / fps:.1f}s\n")

        frame_stats = []
        frame_num = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.holistic.process(rgb_frame)

            # Check what was detected
            has_left_hand = results.left_hand_landmarks is not None
            has_right_hand = results.right_hand_landmarks is not None
            has_face = results.face_landmarks is not None

            # Calculate hand presence (% of landmarks with valid data)
            left_hand_strength = self._hand_strength(results.left_hand_landmarks)
            right_hand_strength = self._hand_strength(results.right_hand_landmarks)

            stats = {
                "frame": frame_num,
                "time": frame_num / fps,
                "left_hand": has_left_hand,
                "right_hand": has_right_hand,
                "face": has_face,
                "left_strength": left_hand_strength,
                "right_strength": right_hand_strength,
                "both_hands": has_left_hand and has_right_hand,
                "complete": has_left_hand and has_right_hand and has_face,
            }

            frame_stats.append(stats)
            frame_num += 1

            if frame_num % 60 == 0:
                print(f"   Analyzed {frame_num}/{total_frames} frames...")

        cap.release()
        self.holistic.close()

        return frame_stats, total_frames

    def _hand_strength(self, hand_landmarks) -> float:
        """Calculate hand detection strength (0-1)."""
        if hand_landmarks is None:
            return 0.0
        
        # Count non-zero landmarks
        valid_count = sum(
            1 for lm in hand_landmarks.landmark
            if lm.x > 0 and lm.y > 0 and lm.z > -1
        )
        return valid_count / 21.0

    def find_optimal_range(self, frame_stats: List[dict]) -> Tuple[int, int]:
        """
        Find the best frame range with:
        1. Both hands detected
        2. Face detected (for NMS)
        3. Longest continuous sequence
        """
        best_start = -1
        best_end = -1
        best_length = 0

        # Find all sequences with complete detection
        current_start = -1
        for i, stats in enumerate(frame_stats):
            if stats["complete"]:  # Has left_hand + right_hand + face
                if current_start == -1:
                    current_start = i
            else:
                if current_start != -1:
                    length = i - current_start
                    if length > best_length:
                        best_length = length
                        best_start = current_start
                        best_end = i
                    current_start = -1

        # Check last sequence
        if current_start != -1:
            length = len(frame_stats) - current_start
            if length > best_length:
                best_length = length
                best_start = current_start
                best_end = len(frame_stats)

        # If no complete sequence, find longest sequence with both hands
        if best_start == -1:
            current_start = -1
            for i, stats in enumerate(frame_stats):
                if stats["both_hands"]:
                    if current_start == -1:
                        current_start = i
                else:
                    if current_start != -1:
                        length = i - current_start
                        if length > best_length:
                            best_length = length
                            best_start = current_start
                            best_end = i
                        current_start = -1

            if current_start != -1:
                length = len(frame_stats) - current_start
                if length > best_length:
                    best_length = length
                    best_start = current_start
                    best_end = len(frame_stats)

        return best_start, best_end

    def print_report(self, frame_stats: List[dict], total_frames: int):
        """Print comprehensive analysis report."""
        print("\n" + "=" * 70)
        print("📋 FRAME RANGE ANALYSIS REPORT")
        print("=" * 70)

        # Count detection types
        has_left = sum(1 for s in frame_stats if s["left_hand"])
        has_right = sum(1 for s in frame_stats if s["right_hand"])
        has_face = sum(1 for s in frame_stats if s["face"])
        has_both_hands = sum(1 for s in frame_stats if s["both_hands"])
        has_complete = sum(1 for s in frame_stats if s["complete"])

        print(f"\n🎯 Detection Summary:")
        print(f"   Left hand detected:      {has_left:4d} frames ({100*has_left/len(frame_stats):5.1f}%)")
        print(f"   Right hand detected:     {has_right:4d} frames ({100*has_right/len(frame_stats):5.1f}%)")
        print(f"   Face detected:           {has_face:4d} frames ({100*has_face/len(frame_stats):5.1f}%)")
        print(f"   ✅ Both hands detected:   {has_both_hands:4d} frames ({100*has_both_hands/len(frame_stats):5.1f}%)")
        print(f"   ✅ Complete (both+face): {has_complete:4d} frames ({100*has_complete/len(frame_stats):5.1f}%)")

        # Find optimal range
        best_start, best_end = self.find_optimal_range(frame_stats)

        if best_start != -1:
            best_stats = frame_stats[best_start:best_end]
            best_fps = frame_stats[0]["time"] if frame_stats else 30
            if best_end > best_start:
                best_fps = (best_end - best_start) / (frame_stats[best_end-1]["time"] - frame_stats[best_start]["time"]) if best_end > best_start and frame_stats[best_end-1]["time"] > frame_stats[best_start]["time"] else 30

            print(f"\n🎬 RECOMMENDED FRAME RANGE:")
            print(f"   Start frame:  {best_start}")
            print(f"   End frame:    {best_end}")
            print(f"   Duration:     {(best_end - best_start) / 30:.2f}s (assumes 30 FPS)")
            print(f"   Quality:      {100*has_complete/len(frame_stats):.0f}% complete detection")
            
            print(f"\n💡 How to use:")
            print(f"   1. Update wlasl_pipeline.py TARGET_GLOSSES")
            print(f"   2. Re-run extraction with these frame ranges")
            print(f"   3. Both hands + face will be captured!")

        else:
            print(f"\n⚠️  WARNING: No frames found with both hands + face detected")
            print(f"   The hand might be going out of frame or face might be turned away")
            print(f"   Try with lower detection confidence or longer frame range")

        print("\n" + "=" * 70)

    def preview_frames(self, frame_stats: List[dict], num_samples: int = 5):
        """Show sample frames with detection info."""
        print(f"\n📸 Frame Quality Samples:")
        print("=" * 70)
        
        # Sample every N frames
        step = max(1, len(frame_stats) // num_samples)
        
        for i in range(0, len(frame_stats), step):
            stats = frame_stats[i]
            frame_num = stats["frame"]
            
            left_str = "✅" if stats["left_hand"] else "❌"
            right_str = "✅" if stats["right_hand"] else "❌"
            face_str = "✅" if stats["face"] else "❌"
            
            print(f"   Frame {frame_num:4d} ({stats['time']:6.2f}s): "
                  f"Left{left_str} Right{right_str} Face{face_str}")


def main():
    parser = argparse.ArgumentParser(description="Optimize frame ranges for sign extraction")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--preview", action="store_true", help="Show frame samples")
    
    args = parser.parse_args()
    
    optimizer = FrameRangeOptimizer(args.video)
    frame_stats, total_frames = optimizer.analyze_video()
    
    if frame_stats:
        optimizer.print_report(frame_stats, total_frames)
        if args.preview:
            optimizer.preview_frames(frame_stats)


if __name__ == "__main__":
    main()
