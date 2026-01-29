#!/usr/bin/env python3
"""
Skeleton Debugger: Dual-Signature Viewer
==========================================
Load two signatures (ASL + BSL for same concept) and visualize them side-by-side
as 2D skeletons. Verify:
- Frame synchronization (start/end alignment)
- Body-centric normalization (reference body scaling)
- Hand shape preservation (one-handed vs two-handed)
- Movement quality (no jitter, smooth trajectories)

Normalization:
    By default, all signatures are normalized to REFERENCE BODY proportions:
    - Shoulder width: 100px (consistent across all signs)
    - Body centered at frame center, 40% from top
    - All landmarks (pose, hands, face) scaled uniformly
    
    Press 'n' to toggle between NORMALIZED and RAW views.

Usage:
    python3 skeleton_debugger.py                                    # Default: Single-screen ASL hello_0
    python3 skeleton_debugger.py --dual                              # Side-by-side (WARNING: high CPU)
    python3 skeleton_debugger.py --lang1 asl --sig1 hello_0
    python3 skeleton_debugger.py --lang1 bsl --sig1 hello
    python3 skeleton_debugger.py --help

Controls:
    SPACE: Play/Pause
    LEFT/RIGHT ARROW: Previous/Next frame
    'n': Toggle normalization (NORMALIZED = reference body, RAW = original)
    'd': Toggle joint dots
    'q': Quit

RECOMMENDATIONS:
    1. Start with single-screen mode (default) to verify ASL accuracy
    2. Then test BSL separately
    3. Only use --dual after individual languages are verified (high CPU)
"""

import cv2
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from skeleton_drawer import SkeletonDrawer, extract_landmarks_from_signature


class SkeletonDebugger:
    """Dual-signature visualization and validation."""
    
    def __init__(self, 
                 sig1_path: str,
                 sig2_path: str,
                 lang1: str = "ASL",
                 lang2: str = "BSL",
                 side_by_side: bool = True):
        """
        Initialize debugger with two signatures.
        
        Args:
            sig1_path: Path to first signature JSON
            sig2_path: Path to second signature JSON
            lang1: Language label for first signature
            lang2: Language label for second signature
            side_by_side: Display side-by-side (True) or toggled (False)
        """
        self.sig1_path = Path(sig1_path)
        self.sig2_path = Path(sig2_path)
        self.lang1 = lang1
        self.lang2 = lang2
        self.side_by_side = side_by_side
        
        # Load signatures
        self.sig1_dict = self._load_signature(sig1_path)
        self.sig2_dict = self._load_signature(sig2_path)
        
        # Check data quality and warn if issues
        self.quality1 = self._assess_data_quality(self.sig1_dict, sig1_path)
        self.quality2 = self._assess_data_quality(self.sig2_dict, sig2_path)
        
        # Extract landmark frames - BOTH normalized and raw versions
        # Normalized: scaled to reference body (100px shoulders, centered)
        # Raw: original pixel coordinates from signature
        self.frames1_normalized = extract_landmarks_from_signature(self.sig1_dict, normalize_to_reference=True)
        self.frames1_raw = extract_landmarks_from_signature(self.sig1_dict, normalize_to_reference=False)
        self.frames2_normalized = extract_landmarks_from_signature(self.sig2_dict, normalize_to_reference=True)
        self.frames2_raw = extract_landmarks_from_signature(self.sig2_dict, normalize_to_reference=False)
        
        # Active frames (switched by 'n' key)
        self.frames1 = self.frames1_normalized
        self.frames2 = self.frames2_normalized
        
        # State
        self.current_frame = 0
        self.max_frame = max(len(self.frames1), len(self.frames2))
        self.is_playing = False
        self.show_normalization = True
        self.show_joints = True
        self.completed_lang1 = False  # Track if lang1 video finished
        self.completed_lang2 = False  # Track if lang2 video finished
        # Reference body normalization: ON by default
        # When ON: uses frames_normalized (100px shoulders, centered)
        # When OFF: uses frames_raw (original pixel coordinates)
        self.normalize_display = True
        
        # Get dimensions from metadata
        self.width = self.sig1_dict.get('metadata', {}).get('frame_width', 640)
        self.height = self.sig1_dict.get('metadata', {}).get('frame_height', 480)
    
    def _assess_data_quality(self, sig_dict: Dict, path: str) -> Dict:
        """
        Assess data quality of a signature and warn if issues detected.
        
        Returns dict with:
            - pose_pct: % frames with valid pose
            - hand_pct: % frames with at least one valid hand
            - status: 'good', 'warning', or 'corrupt'
        """
        pose_data = sig_dict.get('pose_data', [])
        if not pose_data:
            return {'pose_pct': 0, 'hand_pct': 0, 'status': 'corrupt'}
        
        good_pose = 0
        good_hand = 0
        
        for frame in pose_data:
            pose = frame.get('pose', [])
            left = frame.get('left_hand', [])
            right = frame.get('right_hand', [])
            
            # Check pose validity
            if pose and np.abs(np.array(pose)[:,:2]).max() > 0.01:
                good_pose += 1
            
            # Check hand validity (at least one)
            left_valid = left and np.abs(np.array(left)[:,:2]).max() > 0.01
            right_valid = right and np.abs(np.array(right)[:,:2]).max() > 0.01
            if left_valid or right_valid:
                good_hand += 1
        
        total = len(pose_data)
        pose_pct = 100 * good_pose // total
        hand_pct = 100 * good_hand // total
        
        # Determine status
        if pose_pct == 100 and hand_pct >= 50:
            status = 'good'
        elif pose_pct >= 80:
            status = 'warning'
        else:
            status = 'corrupt'
        
        # Print warning if not good
        sig_name = Path(path).stem
        if status == 'warning':
            print(f"⚠️  WARNING: {sig_name} has quality issues:")
            print(f"    Pose: {pose_pct}%, Hands: {hand_pct}%")
            print(f"    Some frames may display incorrectly.")
        elif status == 'corrupt':
            print(f"❌ CORRUPT: {sig_name} has severe data issues:")
            print(f"    Pose: {pose_pct}%, Hands: {hand_pct}%")
            print(f"    Consider re-extracting this signature.")
        
        return {'pose_pct': pose_pct, 'hand_pct': hand_pct, 'status': status}
    
    def _load_signature(self, path: str) -> Dict:
        """Load signature JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _create_blank_frame(self) -> np.ndarray:
        """Create blank frame for skeleton drawing."""
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)
    
    def _get_current_landmarks(self, frame_idx: int, sig_frames: List) -> Dict:
        """Get landmarks for frame, or empty dict if out of range.
        
        Note: Normalization is handled at load time by switching between
        frames_normalized and frames_raw based on normalize_display toggle.
        This method simply returns the appropriate frame data.
        """
        if 0 <= frame_idx < len(sig_frames):
            return sig_frames[frame_idx]
        return {}
    
    def _is_frame_corrupt(self, landmarks: Dict) -> bool:
        """Check if frame has no valid data (corrupt/empty).
        
        Returns True if:
        - No landmarks at all
        - Pose is all zeros
        - No valid body parts have data
        """
        if not landmarks:
            return True
        
        pose = landmarks.get('pose')
        left_hand = landmarks.get('left_hand')
        right_hand = landmarks.get('right_hand')
        
        # Check if pose exists and is not all zeros
        pose_valid = pose is not None and np.any(pose != 0)
        
        # Check if at least one hand has data
        left_valid = left_hand is not None and np.any(left_hand != 0)
        right_valid = right_hand is not None and np.any(right_hand != 0)
        
        # Frame is corrupt if no valid pose and no valid hands
        return not pose_valid and not left_valid and not right_valid
    
    def _draw_corrupt_warning(self, frame: np.ndarray) -> None:
        """Draw warning overlay for corrupt/empty frames."""
        h, w = frame.shape[:2]
        text = "NO DATA"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        
        # Get text size for centering
        (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
        x = (w - text_w) // 2
        y = (h + text_h) // 2
        
        # Draw red warning text
        cv2.putText(frame, text, (x, y), font, font_scale, (0, 0, 200), thickness)
    
    def _analyze_corruption(self, frames: List, sig_name: str) -> Dict:
        """Analyze all frames for corruption and return detailed report.
        
        Returns dict with:
            - corrupt_frames: list of 0-indexed corrupt frame numbers
            - corrupt_count: total corrupt frames
            - total_frames: total frames
            - corrupt_pct: percentage corrupt
            - status: 'good', 'warning', 'bad'
        """
        corrupt_frames = []
        for i, frame in enumerate(frames):
            if self._is_frame_corrupt(frame):
                corrupt_frames.append(i)
        
        total = len(frames)
        corrupt_count = len(corrupt_frames)
        corrupt_pct = (corrupt_count / total * 100) if total > 0 else 0
        
        # Determine status
        if corrupt_pct == 0:
            status = 'good'
        elif corrupt_pct < 20:
            status = 'warning'
        else:
            status = 'bad'
        
        return {
            'sig_name': sig_name,
            'corrupt_frames': corrupt_frames,
            'corrupt_count': corrupt_count,
            'total_frames': total,
            'corrupt_pct': corrupt_pct,
            'status': status
        }
    
    def _print_corruption_report(self) -> None:
        """Print detailed corruption report for all loaded signatures."""
        print(f"\n{'='*60}")
        print("DATA QUALITY REPORT")
        print(f"{'='*60}")
        
        reports = []
        
        # Analyze sig1 (use raw frames to avoid placeholder interference)
        report1 = self._analyze_corruption(self.frames1_raw, self.sig1_path.stem)
        reports.append(report1)
        
        # Analyze sig2 if different from sig1
        if self.sig2_path != self.sig1_path:
            report2 = self._analyze_corruption(self.frames2_raw, self.sig2_path.stem)
            reports.append(report2)
        
        quarantine_candidates = []
        
        for report in reports:
            status_icon = {'good': '✅', 'warning': '⚠️', 'bad': '❌'}[report['status']]
            print(f"\n{status_icon} {report['sig_name']}")
            print(f"   Total frames: {report['total_frames']}")
            print(f"   Corrupt frames: {report['corrupt_count']} ({report['corrupt_pct']:.1f}%)")
            
            if report['corrupt_frames']:
                # Show first 10 corrupt frame numbers (1-indexed for display)
                display_frames = [f+1 for f in report['corrupt_frames'][:10]]
                if len(report['corrupt_frames']) > 10:
                    print(f"   Frame numbers: {display_frames} ... (+{len(report['corrupt_frames'])-10} more)")
                else:
                    print(f"   Frame numbers: {display_frames}")
            
            if report['status'] in ['warning', 'bad']:
                quarantine_candidates.append(report['sig_name'])
        
        # Recommendation
        if quarantine_candidates:
            print(f"\n{'─'*60}")
            print("RECOMMENDED ACTIONS:")
            for sig in quarantine_candidates:
                print(f"  → Consider quarantining: {sig}")
            print(f"\nTo quarantine, run:")
            print(f"  python skeleton_debugger.py --quarantine <signature_name>")
        
        print(f"{'='*60}\n")
    
    def _draw_frame_info(self, frame: np.ndarray, frame_num: int, total: int, 
                        sig_name: str, lang: str) -> None:
        """Draw metadata on frame.
        
        Note: frame_num is 0-indexed internally, but displayed as 1-indexed.
        """
        h, w = frame.shape[:2]
        
        # Frame counter (display as 1-indexed: 1/55 to 55/55)
        display_frame = frame_num + 1
        text = f"{lang} | Frame {display_frame}/{total}"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   0.7, (200, 200, 200), 2)
        
        # Signature name
        cv2.putText(frame, f"Sig: {sig_name}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
    
    def _normalize_landmarks_to_bbox(self, landmarks: Dict, target_width: float = 0.8) -> Dict:
        """
        Normalize landmarks to fit in a standard bounding box.
        Ensures all skeletons are the same relative size regardless of original coordinate ranges.
        
        Args:
            landmarks: Dict with 'pose', 'left_hand', 'right_hand' arrays
            target_width: Target width as fraction of frame (0-1)
        
        Returns:
            Normalized landmarks dict
        """
        # Collect all points
        all_points = []
        if landmarks.get('pose') is not None:
            all_points.extend(landmarks['pose'][:, :2])
        if landmarks.get('left_hand') is not None:
            all_points.extend(landmarks['left_hand'][:, :2])
        if landmarks.get('right_hand') is not None:
            all_points.extend(landmarks['right_hand'][:, :2])
        
        if not all_points:
            return landmarks  # No points to normalize
        
        all_points = np.array(all_points)
        
        # Compute bounding box
        min_x, min_y = all_points.min(axis=0)
        max_x, max_y = all_points.max(axis=0)
        
        width = max_x - min_x
        height = max_y - min_y
        
        if width == 0 or height == 0:
            return landmarks  # Degenerate case
        
        # Compute scale factor
        scale = (self.width * target_width) / width
        
        # Normalize each component
        result = {}
        for key in landmarks:
            if landmarks[key] is not None:
                normalized = landmarks[key].copy()
                # Translate to origin
                normalized[:, 0] -= min_x
                normalized[:, 1] -= min_y
                # Scale
                normalized[:, :2] *= scale
                # Center vertically
                new_height = height * scale
                y_offset = (self.height - new_height) / 2
                normalized[:, 1] += y_offset
                result[key] = normalized
            else:
                result[key] = None
        
        return result
    
    def _draw_sync_info(self, frame: np.ndarray) -> None:
        """Draw synchronization info on frame."""
        h, w = frame.shape[:2]
        
        frame_diff = len(self.frames1) - len(self.frames2)
        status = "✓ SYNC" if frame_diff == 0 else f"⚠ DESYNC ({frame_diff} frames)"
        color = (0, 255, 0) if frame_diff == 0 else (0, 165, 255)
        
        cv2.putText(frame, status, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, color, 2)
    
    def _draw_normalization_info(self, frame: np.ndarray) -> None:
        """Draw normalization status."""
        h, w = frame.shape[:2]
        status = "NORMALIZED" if self.normalize_display else "RAW"
        color = (0, 255, 0) if self.normalize_display else (0, 165, 255)
        
        cv2.putText(frame, status, (w - 200, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, color, 2)
    
    def _create_output_frame(self) -> np.ndarray:
        """Create current output frame(s)."""
        if self.side_by_side:
            return self._create_side_by_side()
        else:
            return self._create_single()
    
    def _create_single(self) -> np.ndarray:
        """Create single-screen visualization (non-toggled).
        
        Shows one signature at a time. Use arrow keys to navigate.
        Use 's' to toggle between sig1/sig2.
        """
        frame_blank = self._create_blank_frame()
        
        # Show sig1
        lm = self._get_current_landmarks(self.current_frame, self.frames1)
        lang = self.lang1
        sig_name = self.sig1_path.stem
        total = len(self.frames1)
        
        if lm and not self._is_frame_corrupt(lm):
            frame_blank = SkeletonDrawer.draw_skeleton(
                frame_blank, lm, lang=lang,
                show_joints=self.show_joints
            )
        else:
            self._draw_corrupt_warning(frame_blank)
        
        self._draw_frame_info(frame_blank, self.current_frame, total,
                             sig_name, lang)
        self._draw_normalization_info(frame_blank)
        
        help_text = "SPACE:play/pause | </>:frame | n:normalize | d:dots | r:replay | q:quit"
        cv2.putText(frame_blank, help_text, (10, frame_blank.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        return frame_blank
    
    def _create_side_by_side(self) -> np.ndarray:
        """Create side-by-side visualization.
        
        Note: High CPU cost. Recommended to use single-screen mode first.
        """
        # Create full-size canvases for each skeleton
        frame1_blank = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame2_blank = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Get landmarks for current frame
        lm1 = self._get_current_landmarks(self.current_frame, self.frames1)
        lm2 = self._get_current_landmarks(self.current_frame, self.frames2)
        
        # Normalize both to standard bounding box (makes them same relative size)
        if lm1 and not self._is_frame_corrupt(lm1):
            lm1_normalized = self._normalize_landmarks_to_bbox(lm1, target_width=0.7)
            frame1_blank = SkeletonDrawer.draw_skeleton(
                frame1_blank, lm1_normalized, lang=self.lang1,
                show_joints=self.show_joints
            )
        elif self.current_frame < len(self.frames1):
            self._draw_corrupt_warning(frame1_blank)
        
        if lm2 and not self._is_frame_corrupt(lm2):
            lm2_normalized = self._normalize_landmarks_to_bbox(lm2, target_width=0.7)
            frame2_blank = SkeletonDrawer.draw_skeleton(
                frame2_blank, lm2_normalized, lang=self.lang2,
                show_joints=self.show_joints
            )
        elif self.current_frame < len(self.frames2):
            self._draw_corrupt_warning(frame2_blank)
        
        # Add info (normalized size)
        # Frame info with completion indicator for lang1
        lang1_indicator = "⏹" if self.completed_lang1 else "▶"
        cv2.putText(frame1_blank, f"{lang1_indicator} {self.lang1} | Frame {self.current_frame + 1}/{len(self.frames1)}", 
                   (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame1_blank, f"Sig: {self.sig1_path.stem}", 
                   (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        
        # Show "ended" if video is out of bounds
        if self.current_frame >= len(self.frames1):
            cv2.putText(frame1_blank, "[Video ended]", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        
        # Frame info with completion indicator for lang2
        lang2_indicator = "⏹" if self.completed_lang2 else "▶"
        cv2.putText(frame2_blank, f"{lang2_indicator} {self.lang2} | Frame {self.current_frame + 1}/{len(self.frames2)}", 
                   (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame2_blank, f"Sig: {self.sig2_path.stem}", 
                   (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        
        # Show "ended" if video is out of bounds
        if self.current_frame >= len(self.frames2):
            cv2.putText(frame2_blank, "[Video ended]", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
        
        # Combine side-by-side
        combined = np.hstack([frame1_blank, frame2_blank])
        
        # Add unified info
        self._draw_sync_info(combined)
        self._draw_normalization_info(combined)
        
        # Control help (smaller text to fit)
        help_text = "SPACE:play/pause | </>:frame | n:norm | d:dots | r:replay | q:quit | ⚠️ HIGH CPU"
        cv2.putText(combined, help_text, (10, combined.shape[0] - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 165, 255), 1)
        
        return combined
    
    def _create_toggled(self) -> np.ndarray:
        """Create toggled single-view visualization."""
        frame_blank = self._create_blank_frame()
        
        # Alternate between sig1 and sig2 every 30 frames
        show_sig1 = (self.current_frame % 60) < 30
        
        if show_sig1:
            lm = self._get_current_landmarks(self.current_frame, self.frames1)
            lang = self.lang1
            sig_name = self.sig1_path.stem
            total = len(self.frames1)
        else:
            lm = self._get_current_landmarks(self.current_frame, self.frames2)
            lang = self.lang2
            sig_name = self.sig2_path.stem
            total = len(self.frames2)
        
        if lm and not self._is_frame_corrupt(lm):
            frame_blank = SkeletonDrawer.draw_skeleton(
                frame_blank, lm, lang=lang,
                show_joints=self.show_joints
            )
        else:
            self._draw_corrupt_warning(frame_blank)
        
        self._draw_frame_info(frame_blank, self.current_frame, total,
                             sig_name, lang)
        self._draw_normalization_info(frame_blank)
        
        help_text = "SPACE:play/pause | </>:frame | n:normalize | s:toggle mode | q:quit"
        cv2.putText(frame_blank, help_text, (10, frame_blank.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        return frame_blank
    
    def run(self, fps: int = 15) -> None:
        """Run interactive debugger."""
        frame_delay = max(1, int(1000 / fps))
        window_name = "Skeleton Debugger"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        print(f"\n{'='*60}")
        print(f"Skeleton Debugger")
        print(f"{'='*60}")
        print(f"Signature 1: {self.sig1_path.stem} ({len(self.frames1)} frames)")
        print(f"Signature 2: {self.sig2_path.stem} ({len(self.frames2)} frames)")
        print(f"Display mode: {'Side-by-side' if self.side_by_side else 'Single'}")
        print(f"Normalization: {'REFERENCE BODY (100px shoulders)' if self.normalize_display else 'RAW'}")
        print(f"\nControls:")
        print(f"  SPACE: Play/Pause")
        print(f"  LEFT/RIGHT: Frame back/forward")
        print(f"  'n': Toggle normalization")
        print(f"  'd': Toggle joint dots")
        print(f"  'r': Replay from start")
        print(f"  's': Toggle side-by-side mode")
        print(f"  'q': Quit")
        print(f"{'='*60}\n")
        
        while True:
            # Render frame
            output = self._create_output_frame()
            cv2.imshow(window_name, output)
            
            # Handle input
            key = cv2.waitKey(frame_delay) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord(' '):  # Space: play/pause
                self.is_playing = not self.is_playing
            elif key == 81:  # LEFT arrow
                self.current_frame = max(0, self.current_frame - 1)
                self.is_playing = False
            elif key == 83:  # RIGHT arrow
                self.current_frame = min(self.max_frame - 1, self.current_frame + 1)
                self.is_playing = False
            elif key == ord('n'):  # Toggle normalization
                self.normalize_display = not self.normalize_display
                # Switch frame sources based on normalization mode
                if self.normalize_display:
                    self.frames1 = self.frames1_normalized
                    self.frames2 = self.frames2_normalized
                else:
                    self.frames1 = self.frames1_raw
                    self.frames2 = self.frames2_raw
                mode = 'REFERENCE BODY (100px shoulders)' if self.normalize_display else 'RAW (original)'
                print(f"Normalization: {mode}")
            elif key == ord('d'):  # Toggle dots
                self.show_joints = not self.show_joints
            elif key == ord('s'):  # Toggle side-by-side
                self.side_by_side = not self.side_by_side
            elif key == ord('r'):  # Replay from start
                self.current_frame = 0
                self.is_playing = True
                self.completed_lang1 = False
                self.completed_lang2 = False
                print("▶ Replay from start")
            
            # Auto-advance if playing
            if self.is_playing:
                # Check if either video has completed (for display indicators)
                if self.current_frame >= len(self.frames1):
                    self.completed_lang1 = True
                if self.current_frame >= len(self.frames2):
                    self.completed_lang2 = True
                
                # Advance to next frame if we haven't reached max yet
                if self.current_frame + 1 <= self.max_frame - 1:
                    self.current_frame += 1
                else:
                    # Both videos have finished
                    self.is_playing = False
                    print(f"⏹ Playback complete")
        
        cv2.destroyAllWindows()
        
        # Print corruption report on exit
        self._print_corruption_report()


def quarantine_signature(sig_name: str, lang: str) -> bool:
    """Move a problematic signature to quarantine folder.
    
    Args:
        sig_name: Name of signature (e.g., 'hello_1')
        lang: Language folder (e.g., 'asl', 'bsl')
    
    Returns:
        True if successful, False otherwise
    """
    import shutil
    
    assets_dir = Path('assets/signatures')
    quarantine_dir = Path('assets/signatures/_quarantine')
    
    source = assets_dir / lang.lower() / f"{sig_name}.json"
    dest_dir = quarantine_dir / lang.lower()
    dest = dest_dir / f"{sig_name}.json"
    
    if not source.exists():
        print(f"❌ Source not found: {source}")
        return False
    
    # Create quarantine directory if needed
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Move the file
    shutil.move(str(source), str(dest))
    print(f"✅ Quarantined: {source} → {dest}")
    print(f"   To restore: mv '{dest}' '{source}'")
    
    return True


def _extract_motion_trajectory(pose_data: List) -> np.ndarray:
    """Extract normalized motion trajectory from pose data.
    
    Returns an array of shape (n_frames, features) where features are:
    - Left hand centroid (x, y) relative to shoulder center
    - Right hand centroid (x, y) relative to shoulder center
    - Left hand velocity
    - Right hand velocity
    """
    trajectories = []
    
    prev_left = None
    prev_right = None
    
    for frame in pose_data:
        pose = frame.get('pose')
        lh = frame.get('left_hand')
        rh = frame.get('right_hand')
        
        # Get shoulder center for normalization
        shoulder_center = np.array([0.5, 0.3])  # Default center
        if pose is not None:
            pose = np.array(pose)
            if pose.shape[0] >= 12:  # Has shoulders
                left_shoulder = pose[11, :2]
                right_shoulder = pose[12, :2]
                if np.any(left_shoulder != 0) and np.any(right_shoulder != 0):
                    shoulder_center = (left_shoulder + right_shoulder) / 2
        
        # Left hand centroid
        left_centroid = np.array([0.0, 0.0])
        if lh is not None:
            lh = np.array(lh)
            if np.any(lh != 0):
                left_centroid = lh[:, :2].mean(axis=0) - shoulder_center
        
        # Right hand centroid
        right_centroid = np.array([0.0, 0.0])
        if rh is not None:
            rh = np.array(rh)
            if np.any(rh != 0):
                right_centroid = rh[:, :2].mean(axis=0) - shoulder_center
        
        # Velocity (change from previous frame)
        left_vel = np.linalg.norm(left_centroid - prev_left) if prev_left is not None else 0
        right_vel = np.linalg.norm(right_centroid - prev_right) if prev_right is not None else 0
        
        prev_left = left_centroid
        prev_right = right_centroid
        
        # Feature vector for this frame
        features = np.concatenate([
            left_centroid,   # 2 values
            right_centroid,  # 2 values
            [left_vel],      # 1 value
            [right_vel]      # 1 value
        ])
        trajectories.append(features)
    
    return np.array(trajectories)


def _dtw_distance(seq1: np.ndarray, seq2: np.ndarray) -> float:
    """Compute Dynamic Time Warping distance between two sequences.
    
    DTW handles different-length sequences by finding optimal alignment.
    """
    n, m = len(seq1), len(seq2)
    
    # Cost matrix
    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0, 0] = 0
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = np.linalg.norm(seq1[i-1] - seq2[j-1])
            dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
    
    # Normalize by path length
    return dtw[n, m] / (n + m)


def _compute_position_stats(pose_data: List) -> Dict:
    """Compute statistical summary of hand positions throughout the sign.
    
    Returns dict with:
    - mean_left: average left hand position
    - mean_right: average right hand position  
    - range_left: (min, max) bounding box of left hand
    - range_right: (min, max) bounding box of right hand
    - dominant_hand: 'left', 'right', or 'both'
    """
    left_positions = []
    right_positions = []
    
    for frame in pose_data:
        lh = frame.get('left_hand')
        rh = frame.get('right_hand')
        
        if lh is not None:
            lh = np.array(lh)
            if np.any(lh != 0):
                left_positions.append(lh[:, :2].mean(axis=0))
        
        if rh is not None:
            rh = np.array(rh)
            if np.any(rh != 0):
                right_positions.append(rh[:, :2].mean(axis=0))
    
    left_positions = np.array(left_positions) if left_positions else np.array([[0, 0]])
    right_positions = np.array(right_positions) if right_positions else np.array([[0, 0]])
    
    left_activity = len(left_positions)
    right_activity = len(right_positions)
    
    # Determine dominant hand
    if left_activity > right_activity * 1.5:
        dominant = 'left'
    elif right_activity > left_activity * 1.5:
        dominant = 'right'
    else:
        dominant = 'both'
    
    return {
        'mean_left': left_positions.mean(axis=0),
        'mean_right': right_positions.mean(axis=0),
        'std_left': left_positions.std(axis=0),
        'std_right': right_positions.std(axis=0),
        'range_left': (left_positions.min(axis=0), left_positions.max(axis=0)),
        'range_right': (right_positions.min(axis=0), right_positions.max(axis=0)),
        'dominant_hand': dominant,
        'left_activity': left_activity,
        'right_activity': right_activity
    }


def audit_word_variants(word: str, lang: str) -> None:
    """Audit all variants of a word for consistency using coordinate analysis.
    
    Detects outliers using:
    1. DTW distance between motion trajectories
    2. Statistical position analysis (mean, range, dominant hand)
    3. Velocity profile comparison
    """
    import glob
    
    assets_dir = Path('assets/signatures')
    pattern = str(assets_dir / lang.lower() / f"{word}_*.json")
    
    # Also check for base name without suffix
    base_file = assets_dir / lang.lower() / f"{word}.json"
    
    variants = sorted(glob.glob(pattern))
    if base_file.exists():
        variants.insert(0, str(base_file))
    
    # Filter to only base variants (not smoothed/mirrored/variation)
    base_variants = [v for v in variants if not any(x in Path(v).stem for x in ['smoothed', 'mirrored', 'variation'])]
    
    if len(base_variants) < 2:
        print(f"⚠️  Only {len(base_variants)} base variant(s) found for '{word}' in {lang}.")
        print(f"   Need at least 2 variants to compare.")
        return
    
    print(f"\n{'='*60}")
    print(f"WORD VARIANT AUDIT: '{word}' ({lang.upper()})")
    print(f"{'='*60}")
    print(f"Found {len(base_variants)} base variant(s)")
    
    # Load all variants
    trajectories = []
    stats_list = []
    valid_variants = []
    
    for v in base_variants:
        try:
            with open(v, 'r') as f:
                data = json.load(f)
            
            pose_data = data.get('pose_data', [])
            if not pose_data:
                print(f"   ⚠️  {Path(v).stem}: No pose data")
                continue
            
            traj = _extract_motion_trajectory(pose_data)
            stats = _compute_position_stats(pose_data)
            
            trajectories.append(traj)
            stats_list.append(stats)
            valid_variants.append(v)
            
        except Exception as e:
            print(f"   ❌ {Path(v).stem}: Error loading - {e}")
    
    if len(trajectories) < 2:
        print("   Not enough valid variants to compare.")
        return
    
    # Compute pairwise DTW distances
    n = len(trajectories)
    dtw_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i+1, n):
            dist = _dtw_distance(trajectories[i], trajectories[j])
            dtw_matrix[i, j] = dist
            dtw_matrix[j, i] = dist
    
    # Compute average DTW distance to all others
    avg_dtw = dtw_matrix.sum(axis=1) / (n - 1)
    
    # Also check for dominant hand consistency
    dominant_hands = [s['dominant_hand'] for s in stats_list]
    dominant_mode = max(set(dominant_hands), key=dominant_hands.count)
    
    # Check position consistency
    all_mean_left = np.array([s['mean_left'] for s in stats_list])
    all_mean_right = np.array([s['mean_right'] for s in stats_list])
    
    # Outlier detection
    median_dtw = np.median(avg_dtw)
    std_dtw = np.std(avg_dtw)
    
    print(f"\n📊 Position & Motion Analysis:")
    print(f"{'─'*60}")
    
    outliers = []
    issues = []
    
    for i, (v, dtw, stats) in enumerate(zip(valid_variants, avg_dtw, stats_list)):
        name = Path(v).stem
        status_parts = []
        is_outlier = False
        
        # Check DTW distance (motion pattern)
        dtw_zscore = (dtw - median_dtw) / std_dtw if std_dtw > 0 else 0
        if dtw_zscore > 2.0:
            status_parts.append(f"motion: VERY DIFFERENT (z={dtw_zscore:.1f})")
            is_outlier = True
        elif dtw_zscore > 1.5:
            status_parts.append(f"motion: different (z={dtw_zscore:.1f})")
        
        # Check dominant hand consistency
        if stats['dominant_hand'] != dominant_mode:
            status_parts.append(f"hand: uses {stats['dominant_hand']} (others use {dominant_mode})")
            is_outlier = True
        
        # Check position outlier (using mean position)
        left_dist = np.linalg.norm(stats['mean_left'] - all_mean_left.mean(axis=0))
        right_dist = np.linalg.norm(stats['mean_right'] - all_mean_right.mean(axis=0))
        left_std = np.linalg.norm(all_mean_left.std(axis=0))
        right_std = np.linalg.norm(all_mean_right.std(axis=0))
        
        if left_std > 0 and left_dist / left_std > 2.0:
            status_parts.append(f"left hand position: outlier")
        if right_std > 0 and right_dist / right_std > 2.0:
            status_parts.append(f"right hand position: outlier")
        
        # Format output
        if is_outlier:
            status = "❌ OUTLIER"
            outliers.append(name)
            issues.append((name, status_parts))
        elif status_parts:
            status = "⚠️  WARNING"
            issues.append((name, status_parts))
        else:
            status = "✅ OK"
        
        print(f"\n   {status} {name}")
        print(f"      DTW distance: {dtw:.4f} (z-score: {dtw_zscore:+.2f})")
        print(f"      Dominant hand: {stats['dominant_hand']}")
        print(f"      Left hand range: x=[{stats['range_left'][0][0]:.2f}, {stats['range_left'][1][0]:.2f}]")
        print(f"      Right hand range: x=[{stats['range_right'][0][0]:.2f}, {stats['range_right'][1][0]:.2f}]")
        if status_parts:
            for issue in status_parts:
                print(f"      ⚠️  {issue}")
    
    # Summary
    print(f"\n{'─'*60}")
    if outliers:
        print("DETECTED ISSUES:")
        for name, issue_list in issues:
            print(f"\n   ❌ {name}:")
            for issue in issue_list:
                print(f"      - {issue}")
        
        print(f"\nRECOMMENDED ACTIONS:")
        for sig in outliers:
            print(f"   python skeleton_debugger.py --quarantine {sig} --lang1 {lang}")
    else:
        print("✅ All variants appear consistent based on coordinate analysis.")
    
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Skeleton Debugger: Visualize dual signatures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 skeleton_debugger.py
  python3 skeleton_debugger.py --lang1 asl --sig1 hello_0 --lang2 bsl --sig2 hello
  python3 skeleton_debugger.py --mode toggled
  python3 skeleton_debugger.py --quarantine hello_1 --lang1 asl
  python3 skeleton_debugger.py --audit hello --lang1 asl
        """
    )
    
    parser.add_argument('--sig1', default='hello_0',
                       help='Signature 1 name (default: hello_0)')
    parser.add_argument('--lang1', default='ASL',
                       help='Language 1 label (default: ASL)')
    parser.add_argument('--sig2', default='hello',
                       help='Signature 2 name (default: hello)')
    parser.add_argument('--lang2', default='BSL',
                       help='Language 2 label (default: BSL)')
    parser.add_argument('--dual', action='store_true',
                       help='Display side-by-side (WARNING: high CPU). Default: single-screen.')
    parser.add_argument('--fps', type=int, default=15,
                       help='Playback FPS (default: 15)')
    parser.add_argument('--quarantine', metavar='SIG_NAME',
                       help='Move a problematic signature to quarantine folder')
    parser.add_argument('--audit', metavar='WORD',
                       help='Audit all variants of a word for consistency (e.g., --audit hello)')
    
    args = parser.parse_args()
    
    # Handle audit command
    if args.audit:
        audit_word_variants(args.audit, args.lang1)
        return
    
    # Handle quarantine command
    if args.quarantine:
        quarantine_signature(args.quarantine, args.lang1)
        return
    
    # Build paths
    assets_dir = Path('assets/signatures')
    sig1_path = assets_dir / args.lang1.lower() / f"{args.sig1}.json"
    sig2_path = assets_dir / args.lang2.lower() / f"{args.sig2}.json"
    
    # Verify paths exist
    if not sig1_path.exists():
        print(f"Error: Signature not found: {sig1_path}")
        return
    if not sig2_path.exists():
        print(f"Error: Signature not found: {sig2_path}")
        return
    
    # Run debugger
    debugger = SkeletonDebugger(
        str(sig1_path),
        str(sig2_path),
        lang1=args.lang1,
        lang2=args.lang2,
        side_by_side=args.dual  # Default False (single-screen), --dual enables side-by-side
    )
    
    debugger.run(fps=args.fps)


if __name__ == "__main__":
    main()
