#!/usr/bin/env python3
"""
Extract Golden Signatures from videos using MediaPipe Holistic.
Saves landmark data as JSON files for later recognition tasks.
"""

import cv2
import mediapipe as mp
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np


class SignatureExtractor:
    """Extract pose/hand/face landmarks from sign language videos."""

    # Landmark indices to extract
    LEFT_HAND_INDICES = list(range(21))  # 0-20
    RIGHT_HAND_INDICES = list(range(21))  # 0-20
    POSE_INDICES = [11, 12, 13, 14, 15, 16]  # Shoulders and arms
    FACE_INDICES = [70, 107, 300, 336]  # Eyebrows (left: 70,107; right: 300,336)

    def __init__(self, output_dir: str = "assets/signatures"):
        """Initialize MediaPipe Holistic detector."""
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ MediaPipe Holistic initialized")
        print(f"📁 Output directory: {self.output_dir}")

    def _extract_landmarks(self, results) -> Dict:
        """Extract specific landmarks from MediaPipe results."""
        frame_data = {
            "left_hand": self._get_hand_landmarks(results.left_hand_landmarks),
            "right_hand": self._get_hand_landmarks(results.right_hand_landmarks),
            "pose": self._get_pose_landmarks(results.pose_landmarks),
            "face": self._get_face_landmarks(results.face_landmarks),
        }
        return frame_data

    def _get_hand_landmarks(self, hand_landmarks) -> List[List[float]]:
        """Extract 21 hand landmarks (x, y, z)."""
        if hand_landmarks is None:
            # Return zeros if hand not detected
            return [[0.0, 0.0, 0.0] for _ in range(21)]

        landmarks = []
        for landmark in hand_landmarks.landmark:
            landmarks.append([landmark.x, landmark.y, landmark.z])
        return landmarks

    def _get_pose_landmarks(self, pose_landmarks) -> List[List[float]]:
        """Extract specific pose landmarks (shoulders and arms)."""
        if pose_landmarks is None:
            return [[0.0, 0.0, 0.0] for _ in self.POSE_INDICES]

        landmarks = []
        for idx in self.POSE_INDICES:
            if idx < len(pose_landmarks.landmark):
                lm = pose_landmarks.landmark[idx]
                landmarks.append([lm.x, lm.y, lm.z])
            else:
                landmarks.append([0.0, 0.0, 0.0])
        return landmarks

    def _get_face_landmarks(self, face_landmarks) -> List[List[float]]:
        """Extract specific face landmarks (eyebrows)."""
        if face_landmarks is None:
            return [[0.0, 0.0, 0.0] for _ in self.FACE_INDICES]

        landmarks = []
        for idx in self.FACE_INDICES:
            if idx < len(face_landmarks.landmark):
                lm = face_landmarks.landmark[idx]
                landmarks.append([lm.x, lm.y, lm.z])
            else:
                landmarks.append([0.0, 0.0, 0.0])
        return landmarks

    def extract_from_video(
        self, video_path: str, sign_name: str, language: str = "BSL"
    ) -> Optional[Dict]:
        """
        Extract landmarks from a single video file.

        Args:
            video_path: Path to video file
            sign_name: Name of the sign (used in JSON output)
            language: Language code (default: BSL)

        Returns:
            Dictionary with signature data, or None if extraction failed
        """
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return None

        print(f"\n📹 Processing: {sign_name}")
        print(f"   File: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"   FPS: {fps}, Total Frames: {total_frames}")

        pose_data = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.holistic.process(rgb_frame)

            # Extract landmarks
            frame_landmarks = self._extract_landmarks(results)
            pose_data.append(frame_landmarks)
            frame_count += 1

            if frame_count % 30 == 0:
                print(f"   ✓ Processed {frame_count}/{total_frames} frames")

        cap.release()

        # Create signature JSON
        signature = {
            "sign": sign_name,
            "language": language,
            "pose_data": pose_data,
            "metadata": {
                "fps": fps,
                "total_frames": frame_count,
                "landmarks_per_frame": {
                    "left_hand": 21,
                    "right_hand": 21,
                    "pose": len(self.POSE_INDICES),
                    "face": len(self.FACE_INDICES),
                },
            },
        }

        print(f"   ✅ Extracted {frame_count} frames")
        return signature

    def save_signature(self, signature: Dict, filename: Optional[str] = None) -> bool:
        """
        Save signature to JSON file.

        Args:
            signature: Dictionary with signature data
            filename: Output filename (default: uses sign name)

        Returns:
            True if saved successfully, False otherwise
        """
        if filename is None:
            filename = f"{signature['sign']}.json"

        output_path = self.output_dir / filename
        try:
            with open(output_path, "w") as f:
                json.dump(signature, f, indent=2)
            print(f"   💾 Saved to: {output_path}")
            return True
        except Exception as e:
            print(f"   ❌ Error saving file: {e}")
            return False

    def process_directory(self, input_dir: str, language: str = "BSL") -> int:
        """
        Process all videos in a directory.

        Args:
            input_dir: Directory containing video files
            language: Language code for all videos

        Returns:
            Number of successfully processed videos
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            print(f"❌ Directory not found: {input_dir}")
            return 0

        video_extensions = {".mp4", ".avi", ".mov", ".mkv"}
        video_files = [
            f
            for f in input_path.iterdir()
            if f.suffix.lower() in video_extensions
        ]

        if not video_files:
            print(f"⚠️  No video files found in: {input_dir}")
            return 0

        print(f"\n📂 Found {len(video_files)} video(s) in {input_dir}")

        success_count = 0
        for video_file in sorted(video_files):
            sign_name = video_file.stem  # Filename without extension
            signature = self.extract_from_video(
                str(video_file), sign_name, language
            )

            if signature:
                if self.save_signature(signature):
                    success_count += 1

        return success_count

    def close(self):
        """Close MediaPipe resources."""
        self.holistic.close()


def main():
    """Main extraction workflow."""
    print("=" * 60)
    print("🎬 Golden Signature Extractor")
    print("=" * 60)

    extractor = SignatureExtractor(output_dir="assets/signatures")

    # Process individual words from lexicon
    lexicon_dir = "assets/raw_videos/lexicon"
    if os.path.exists(lexicon_dir):
        print("\n" + "=" * 60)
        print("Processing LEXICON videos (individual words)...")
        print("=" * 60)
        lexicon_count = extractor.process_directory(lexicon_dir, language="BSL")
        print(f"\n✅ Successfully processed {lexicon_count} lexicon videos")
    else:
        print(f"⚠️  Lexicon directory not found: {lexicon_dir}")

    # Process benchmark sentence
    benchmark_video = "assets/raw_videos/benchmarks/bsl_hello_where_are_you_going.mp4"
    if os.path.exists(benchmark_video):
        print("\n" + "=" * 60)
        print("Processing BENCHMARK sentence...")
        print("=" * 60)
        signature = extractor.extract_from_video(
            benchmark_video, "bsl_hello_where_are_you_going", language="BSL"
        )
        if signature:
            extractor.save_signature(signature)
            print("✅ Successfully processed benchmark video")
    else:
        print(f"⚠️  Benchmark video not found: {benchmark_video}")

    extractor.close()

    print("\n" + "=" * 60)
    print("✅ Extraction Complete!")
    print(f"📁 Signatures saved to: assets/signatures/")
    print("=" * 60)


if __name__ == "__main__":
    main()
