#!/usr/bin/env python3
"""
Skeleton Debugger: Dual-Signature Viewer
==========================================
Load two signatures (ASL + BSL for same concept) and visualize them side-by-side
as 2D skeletons. Verify:
- Frame synchronization (start/end alignment)
- Body-centric normalization (shoulder centering)
- Hand shape preservation (one-handed vs two-handed)
- Movement quality (no jitter, smooth trajectories)

Usage:
    python3 skeleton_debugger.py                                    # Default: Single-screen ASL hello_0
    python3 skeleton_debugger.py --dual                              # Side-by-side (WARNING: high CPU)
    python3 skeleton_debugger.py --lang1 asl --sig1 hello_0
    python3 skeleton_debugger.py --lang1 bsl --sig1 hello
    python3 skeleton_debugger.py --help

Controls:
    SPACE: Play/Pause
    LEFT/RIGHT ARROW: Previous/Next frame
    'n': Toggle normalization
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
# Use new simpler skeleton renderer with compatibility layer
from skeleton_renderer import (
    SkeletonDrawerCompat as SkeletonDrawer,
    extract_landmarks_from_signature,
    ReferenceBody,
    CENTER_X,
    CENTER_Y,
    REFERENCE_SHOULDER_WIDTH,
    COLOR_LEFT_ARM,
    COLOR_RIGHT_ARM,
)


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
        
        # Extract landmark frames
        self.frames1 = extract_landmarks_from_signature(self.sig1_dict)
        self.frames2 = extract_landmarks_from_signature(self.sig2_dict)
        
        # State
        self.current_frame = 0
        self.max_frame = max(len(self.frames1), len(self.frames2))
        self.is_playing = False
        self.show_normalization = True
        self.show_joints = True
        self.completed_lang1 = False  # Track if lang1 video finished
        self.completed_lang2 = False  # Track if lang2 video finished
        # Auto-normalize in dual/side-by-side mode: signers have different camera
        # positions and sizes, making RAW mode misleading for comparison.
        # Single-screen defaults OFF (raw view is useful for individual inspection).
        self.normalize_display = side_by_side
        
        # Get dimensions from metadata
        self.width = self.sig1_dict.get('metadata', {}).get('frame_width', 640)
        self.height = self.sig1_dict.get('metadata', {}).get('frame_height', 480)
        # Probe support: if sig2_path is a probe name, try assets/probes/probe_{name}.json
        if self.sig2_path and not Path(self.sig2_path).exists():
            probe_path = Path('assets/probes') / f"probe_{self.sig2_path}.json"
            if probe_path.exists():
                self.sig2_path = str(probe_path)
                self.sig2_dict = self._load_signature(self.sig2_path)
                self.frames2 = extract_landmarks_from_signature(self.sig2_dict)
    
    def _has_landmarks(self, lm) -> bool:
        """Check if landmarks data is valid (not None and has content)."""
        if lm is None:
            return False
        if isinstance(lm, np.ndarray):
            return lm.size > 0
        if isinstance(lm, dict):
            return len(lm) > 0
        if isinstance(lm, list):
            return len(lm) > 0
        return False
    
    def _load_signature(self, path: str) -> Dict:
        """Load signature JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _create_blank_frame(self) -> np.ndarray:
        """Create blank frame for skeleton drawing."""
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)
    
    def _get_current_landmarks(self, frame_idx: int, sig_frames: List) -> Optional[np.ndarray]:
        """Get landmarks array for frame. Freeze on last frame if out of range."""
        # Clamp to valid range - freeze on last frame when video ends
        if len(sig_frames) == 0:
            return None
        
        clamped_idx = max(0, min(frame_idx, len(sig_frames) - 1))
        return sig_frames[clamped_idx]  # Return array directly
    
    def _draw_frame_info(self, frame: np.ndarray, frame_num: int, total: int, 
                        sig_name: str, lang: str) -> None:
        """Draw metadata on frame."""
        h, w = frame.shape[:2]
        
        # Frame counter
        text = f"{lang} | Frame {frame_num}/{total}"
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

        frame_diff = abs(len(self.frames1) - len(self.frames2))
        if frame_diff == 0:
            status = "SYNC"
            color = (0, 255, 0)
        else:
            # Percentage-based sync is active: both signs advance at same relative rate
            status = f"% SYNC ({frame_diff}f diff)"
            color = (0, 255, 0)  # Green — handled

        cv2.putText(frame, status, (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, color, 2)
    
    def _draw_normalization_info(self, frame: np.ndarray) -> None:
        """Draw normalization status."""
        h, w = frame.shape[:2]
        status = "NORM" if self.normalize_display else "RAW"
        color = (0, 255, 0) if self.normalize_display else (0, 165, 255)

        cv2.putText(frame, status, (w - 80, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   0.6, color, 2)

    def _draw_legend(self, frame: np.ndarray) -> None:
        """Draw minimal legend for left/right arm colors."""
        x, y = 10, frame.shape[0] - 45
        cv2.line(frame, (x, y), (x + 20, y), COLOR_LEFT_ARM, 3, cv2.LINE_AA)
        cv2.putText(frame, "L arm", (x + 30, y + 5), cv2.FONT_HERSHEY_SIMPLEX,
                   0.45, (200, 200, 200), 1)
        cv2.line(frame, (x, y + 18), (x + 20, y + 18), COLOR_RIGHT_ARM, 3, cv2.LINE_AA)
        cv2.putText(frame, "R arm", (x + 30, y + 23), cv2.FONT_HERSHEY_SIMPLEX,
                   0.45, (200, 200, 200), 1)
    
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
        
        # Get landmarks as array
        lm = self._get_current_landmarks(self.current_frame, self.frames1)
        lang = self.lang1
        sig_name = self.sig1_path.stem
        total = len(self.frames1)
        
        # Use raw landmarks for angle extraction; renderer anchors to reference body
        lm_raw = lm if self._has_landmarks(lm) else None
        
        # Draw skeleton (reference body scale, angle-driven)
        if self._has_landmarks(lm_raw):
            lm_to_draw = lm_raw
            if self.normalize_display:
                try:
                    lm_to_draw = SkeletonDrawer.normalize_to_reference(lm_raw)
                except Exception:
                    lm_to_draw = lm_raw

            frame_blank = SkeletonDrawer.draw_skeleton(
                frame_blank, lm_to_draw, lang=lang,
                show_joints=self.show_joints
            )
        
        self._draw_frame_info(frame_blank, self.current_frame, total,
                             sig_name, lang)
        self._draw_normalization_info(frame_blank)
        self._draw_legend(frame_blank)
        
        help_text = "SPACE:play/pause | </>:frame | n:norm | d:dots | r:replay | q:quit"
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
        
        # Get landmarks as arrays (extract_landmarks_from_signature returns arrays)
        lm1 = None
        lm2 = None

        # Percentage-based frame sync: both signatures advance at the same relative
        # rate through their respective loops, regardless of absolute frame count.
        # Frame-count differences (e.g. ASL 69 vs BSL 32) are handled transparently.
        if len(self.frames1) > 0 and len(self.frames2) > 0 and len(self.frames1) != len(self.frames2):
            pct = self.current_frame / max(1, self.max_frame - 1)
            idx1 = min(int(pct * len(self.frames1)), len(self.frames1) - 1)
            idx2 = min(int(pct * len(self.frames2)), len(self.frames2) - 1)
        else:
            idx1 = max(0, min(self.current_frame, len(self.frames1) - 1)) if len(self.frames1) > 0 else 0
            idx2 = max(0, min(self.current_frame, len(self.frames2) - 1)) if len(self.frames2) > 0 else 0

        if len(self.frames1) > 0:
            lm1 = self.frames1[idx1]
        if len(self.frames2) > 0:
            lm2 = self.frames2[idx2]
        
        # Draw skeletons (reference body scale, angle-driven)
        if self._has_landmarks(lm1):
            lm1_draw = lm1
            if self.normalize_display:
                try:
                    lm1_draw = SkeletonDrawer.normalize_to_reference(lm1)
                except Exception:
                    lm1_draw = lm1

            frame1_blank = SkeletonDrawer.draw_skeleton(
                frame1_blank, lm1_draw, lang=self.lang1,
                show_joints=self.show_joints
            )

        if self._has_landmarks(lm2):
            lm2_draw = lm2
            if self.normalize_display:
                try:
                    lm2_draw = SkeletonDrawer.normalize_to_reference(lm2)
                except Exception:
                    lm2_draw = lm2

            frame2_blank = SkeletonDrawer.draw_skeleton(
                frame2_blank, lm2_draw, lang=self.lang2,
                show_joints=self.show_joints
            )
        
        # Add info (normalized size) — use idx1/idx2 not current_frame (% sync may diverge)
        pct1 = int(100 * idx1 / max(1, len(self.frames1) - 1)) if len(self.frames1) > 1 else 100
        pct2 = int(100 * idx2 / max(1, len(self.frames2) - 1)) if len(self.frames2) > 1 else 100

        lang1_indicator = "[DONE]" if self.completed_lang1 else "[PLAY]"
        cv2.putText(frame1_blank, f"{lang1_indicator} {self.lang1} | Frame {idx1+1}/{len(self.frames1)} ({pct1}%)",
                   (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame1_blank, f"Sig: {self.sig1_path.stem}",
                   (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)

        lang2_indicator = "[DONE]" if self.completed_lang2 else "[PLAY]"
        cv2.putText(frame2_blank, f"{lang2_indicator} {self.lang2} | Frame {idx2+1}/{len(self.frames2)} ({pct2}%)",
                   (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame2_blank, f"Sig: {self.sig2_path.stem}",
                   (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        
        # Combine side-by-side
        combined = np.hstack([frame1_blank, frame2_blank])
        
        # Add unified info
        self._draw_sync_info(combined)
        self._draw_normalization_info(combined)
        self._draw_legend(combined)
        
        # Control help (smaller text to fit)
        help_text = "SPACE:play/pause | </>:frame | n:norm | d:dots | r:replay | q:quit"
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
        
        # Normalize and draw
        if self._has_landmarks(lm):
            lm_normalized = SkeletonDrawer.normalize_to_reference(lm)
            frame_blank = SkeletonDrawer.draw_skeleton(
                frame_blank, lm_normalized, lang=lang,
                show_joints=self.show_joints
            )
        
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
        print(f"Display mode: {'Side-by-side' if self.side_by_side else 'Toggled'}")
        print(f"Normalization: {'ON' if self.normalize_display else 'OFF'}")
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
            elif key == ord('d'):  # Toggle dots
                self.show_joints = not self.show_joints
            elif key == ord('s'):  # Toggle side-by-side
                self.side_by_side = not self.side_by_side
            elif key == ord('r'):  # Replay from start
                self.current_frame = 0
                self.is_playing = True
                self.completed_lang1 = False
                self.completed_lang2 = False
                print("[PLAY] Replay from start")
            
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
                    print(f"[DONE] Playback complete")
        
        cv2.destroyAllWindows()
        print("\nDebugger closed.")


def main():
    parser = argparse.ArgumentParser(
        description="Skeleton Debugger: Visualize dual signatures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 skeleton_debugger.py
  python3 skeleton_debugger.py --lang1 asl --sig1 hello_0 --lang2 bsl --sig2 hello
  python3 skeleton_debugger.py --mode toggled
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
    parser.add_argument('--probe', default=None,
                       help='Load built-in probe by name (e.g. up, down, open) as sig2')
    parser.add_argument('--fps', type=int, default=15,
                       help='Playback FPS (default: 15)')
    
    args = parser.parse_args()
    
    # Build paths - detect if full path or shorthand name provided
    assets_dir = Path('assets/signatures')
    
    # Handle sig1 path
    if args.sig1.endswith('.json') or '/' in args.sig1:
        # Full path provided
        sig1_path = Path(args.sig1)
    else:
        # Shorthand name - build full path
        sig1_path = assets_dir / args.lang1.lower() / f"{args.sig1}.json"
    
    # Handle sig2 path
    if args.probe:
        # Use probe signature if requested
        probe_path = Path('assets/probes') / f"probe_{args.probe}.json"
        if probe_path.exists():
            sig2_path = probe_path
            args.lang2 = f"PROBE:{args.probe}"
        else:
            print(f"Probe not found: {probe_path}, falling back to --sig2")
            if args.sig2.endswith('.json') or '/' in args.sig2:
                sig2_path = Path(args.sig2)
            else:
                sig2_path = assets_dir / args.lang2.lower() / f"{args.sig2}.json"
    else:
        if args.sig2.endswith('.json') or '/' in args.sig2:
            # Full path provided
            sig2_path = Path(args.sig2)
        else:
            # Shorthand name - build full path
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
