#!/usr/bin/env python3
"""
Extract Golden Signatures from videos using MediaPipe Holistic.
Saves landmark data as JSON files for later recognition tasks.

Usage:
    python3 extract_signatures.py                    # Default: BSL lexicon + benchmarks
    python3 extract_signatures.py --video video.mp4 --sign hello --lang asl
    python3 extract_signatures.py --dir assets/raw_videos/custom --lang asl --delete
"""

import cv2
import mediapipe as mp
import json
import os
import argparse
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

    def __init__(self, output_dir: str = "assets/signatures", delete_after: bool = False):
        """Initialize MediaPipe Holistic detector.
        
        Args:
            output_dir: Directory to save signatures
            delete_after: Delete source video files after processing
        """
        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.3,  # LOWERED from 0.5 - catch more detections
            min_tracking_confidence=0.3,   # LOWERED from 0.5 - better temporal tracking
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delete_after = delete_after
        self.translation_map = {}  # Track video -> signature mappings
        self.last_valid_frame = {}  # Cache for interpolation
        print(f"✅ MediaPipe Holistic initialized")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"   Detection thresholds: confidence=0.3 (optimized for sign language)")
        if delete_after:
            print(f"🗑️  Will delete .mp4 files after processing")

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

    def _interpolate_landmarks(self, pose_data: List[Dict]) -> List[Dict]:
        """
        Post-process: Fill small gaps in missing detections using temporal interpolation.
        Helps recover from brief detection failures (1-2 frame gaps).
        
        Strategy: If a landmark is zero-filled for N frames, try to interpolate from
        surrounding non-zero frames. Only interpolate small gaps (1-3 frames).
        """
        max_gap = 3  # Only fill gaps of 3 frames or less
        
        for landmark_type in ["left_hand", "right_hand", "pose", "face"]:
            # Extract all frames for this landmark type
            frames = [frame[landmark_type] for frame in pose_data]
            
            for point_idx in range(len(frames[0])):
                # Get all values for this point across all frames
                point_values = [frames[f][point_idx] for f in range(len(frames))]
                
                # Find zero-filled sequences
                frame_idx = 0
                while frame_idx < len(point_values):
                    if point_values[frame_idx] == [0.0, 0.0, 0.0]:
                        # Found start of zero sequence
                        gap_start = frame_idx
                        gap_size = 0
                        
                        # Count gap size
                        while frame_idx < len(point_values) and point_values[frame_idx] == [0.0, 0.0, 0.0]:
                            gap_size += 1
                            frame_idx += 1
                        
                        # Try to interpolate if gap is small and bounded by valid data
                        if gap_size <= max_gap and gap_start > 0 and frame_idx < len(point_values):
                            before = point_values[gap_start - 1]
                            after = point_values[frame_idx]
                            
                            # Only interpolate if surrounding frames have valid data
                            if before != [0.0, 0.0, 0.0] and after != [0.0, 0.0, 0.0]:
                                # Linear interpolation
                                for i in range(gap_size):
                                    alpha = (i + 1) / (gap_size + 1)
                                    interpolated = [
                                        before[j] + alpha * (after[j] - before[j])
                                        for j in range(3)
                                    ]
                                    point_values[gap_start + i] = interpolated
                    else:
                        frame_idx += 1
                
                # Update pose_data with interpolated values
                for f in range(len(frames)):
                    pose_data[f][landmark_type][point_idx] = point_values[f]
        
        return pose_data

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

        # Post-processing: Fill gaps in missing detections
        print(f"   🔧 Post-processing: Interpolating missing frames...")
        pose_data = self._interpolate_landmarks(pose_data)

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

    def extract_from_video_range(
        self,
        video_path: str,
        sign_name: str,
        frame_start: int = -1,
        frame_end: int = -1,
        language: str = "BSL",
    ) -> Optional[Dict]:
        """
        Extract landmarks from a specific frame range in a video.
        Optimized for WLASL dataset where only certain frames contain the sign.

        Args:
            video_path: Path to video file
            sign_name: Name of the sign
            frame_start: Starting frame number (uses first frame if -1)
            frame_end: Ending frame number (uses last frame if -1)
            language: Language code

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
        
        # Handle frame range
        if frame_start == -1:
            frame_start = 0
        if frame_end == -1 or frame_end > total_frames:
            frame_end = total_frames

        print(f"   FPS: {fps}, Total Frames: {total_frames}")
        print(f"   Processing frames {frame_start}-{frame_end} (sign movement only)")

        # Seek to starting frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_start)

        pose_data = []
        frame_count = 0
        current_frame = frame_start

        while current_frame < frame_end:
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
            current_frame += 1

            if frame_count % 30 == 0:
                print(f"   ✓ Processed {frame_count}/{frame_end - frame_start} frames")

        cap.release()

        # Post-processing: Fill gaps in missing detections
        print(f"   🔧 Post-processing: Interpolating missing frames...")
        pose_data = self._interpolate_landmarks(pose_data)

        # Create signature JSON with frame range metadata
        signature = {
            "sign": sign_name,
            "language": language,
            "pose_data": pose_data,
            "metadata": {
                "fps": fps,
                "total_frames": frame_count,
                "frame_start": frame_start,
                "frame_end": frame_end,
                "landmarks_per_frame": {
                    "left_hand": 21,
                    "right_hand": 21,
                    "pose": len(self.POSE_INDICES),
                    "face": len(self.FACE_INDICES),
                },
            },
        }

        print(f"   ✅ Extracted {frame_count} frames (from range {frame_start}-{frame_end})")
        return signature

    def save_signature(self, signature: Dict, filename: Optional[str] = None, source_video: Optional[str] = None) -> bool:
        """
        Save signature to JSON file and delete source video if requested.

        Args:
            signature: Dictionary with signature data
            filename: Output filename (default: uses sign name)
            source_video: Path to source video file (will be deleted if delete_after=True)

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
            
            # Track in translation map
            self.translation_map[signature['sign']] = {
                "signature_file": str(output_path),
                "language": signature.get('language', 'unknown'),
                "frames": signature['metadata']['total_frames']
            }
            
            # Delete source video if requested
            if self.delete_after and source_video and os.path.exists(source_video):
                try:
                    os.remove(source_video)
                    print(f"   🗑️  Deleted: {source_video}")
                except Exception as e:
                    print(f"   ⚠️  Could not delete {source_video}: {e}")
            
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
                if self.save_signature(signature, source_video=str(video_file)):
                    success_count += 1

        return success_count
    
    def save_translation_map(self, filepath: str = "translation_map.json") -> bool:
        """Save translation map (signature file mappings) to JSON.
        
        Args:
            filepath: Output file path
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(filepath, "w") as f:
                json.dump(self.translation_map, f, indent=2)
            print(f"\n📋 Translation map saved: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving translation map: {e}")
            return False

    def close(self):
        """Close MediaPipe resources."""
        self.holistic.close()


def main():
    """Main extraction workflow with CLI support."""
    parser = argparse.ArgumentParser(
        description="Extract sign language signatures from videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: Process BSL lexicon directory
  python3 extract_signatures.py
  
  # Extract single reference video
  python3 extract_signatures.py --video where_ref.mp4 --sign where --lang asl
  
  # Process directory of videos
  python3 extract_signatures.py --dir assets/raw_videos/custom --lang asl --delete
  
  # Extract with frame range (for WLASL context cleanup)
  python3 extract_signatures.py --video video.mp4 --sign hello --lang asl --start 10 --end 50
        """
    )
    
    parser.add_argument("--video", help="Path to single video file")
    parser.add_argument("--sign", default="unknown", help="Sign name for JSON output")
    parser.add_argument("--lang", default="BSL", choices=["ASL", "BSL", "JSL", "CSL", "LSF"], 
                        help="Language code (default: BSL)")
    parser.add_argument("--dir", help="Directory containing multiple videos to process")
    parser.add_argument("--start", type=int, default=-1, help="Start frame (for frame range extraction)")
    parser.add_argument("--end", type=int, default=-1, help="End frame (for frame range extraction)")
    parser.add_argument("--output-dir", default="assets/signatures", help="Output directory for JSON files")
    parser.add_argument("--delete", action="store_true", help="Delete source videos after processing")
    parser.add_argument("--default-behavior", action="store_true", help="Run default BSL lexicon + benchmark processing")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 Golden Signature Extractor")
    print("=" * 60)

    extractor = SignatureExtractor(output_dir=args.output_dir, delete_after=args.delete)

    # Mode 1: Single video extraction
    if args.video:
        print(f"\n📹 Extracting single video...")
        if args.start > 0 or args.end > 0:
            signature = extractor.extract_from_video_range(
                args.video, args.sign, args.start, args.end, language=args.lang
            )
        else:
            signature = extractor.extract_from_video(
                args.video, args.sign, language=args.lang
            )
        
        if signature:
            extractor.save_signature(signature, source_video=args.video if args.delete else None)
            print(f"✅ Successfully extracted: {args.sign}")
        else:
            print(f"❌ Failed to extract: {args.video}")

    # Mode 2: Directory processing
    elif args.dir:
        print(f"\n📂 Processing directory: {args.dir}")
        count = extractor.process_directory(args.dir, language=args.lang)
        print(f"✅ Successfully processed {count} videos")

    # Mode 3: Default behavior (BSL lexicon + benchmarks)
    else:
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
                extractor.save_signature(signature, source_video=benchmark_video)
                print("✅ Successfully processed benchmark video")
        else:
            print(f"⚠️  Benchmark video not found: {benchmark_video}")

    # Save translation map
    extractor.save_translation_map("translation_map.json")
    
    extractor.close()

    print("\n" + "=" * 60)
    print("✅ Extraction Complete!")
    print(f"📁 Signatures saved to: {args.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
