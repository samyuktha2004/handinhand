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
        
        # Extract landmark frames
        self.frames1 = extract_landmarks_from_signature(self.sig1_dict)
        self.frames2 = extract_landmarks_from_signature(self.sig2_dict)
        
        # State
        self.current_frame = 0
        self.max_frame = max(len(self.frames1), len(self.frames2))
        self.is_playing = False
        self.show_normalization = True
        self.show_joints = True
        self.normalize_display = True
        
        # Get dimensions from metadata
        self.width = self.sig1_dict.get('metadata', {}).get('frame_width', 640)
        self.height = self.sig1_dict.get('metadata', {}).get('frame_height', 480)
    
    def _load_signature(self, path: str) -> Dict:
        """Load signature JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _create_blank_frame(self) -> np.ndarray:
        """Create blank frame for skeleton drawing."""
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)
    
    def _get_current_landmarks(self, frame_idx: int, sig_frames: List) -> Dict:
        """Get landmarks for frame, or empty dict if out of range."""
        if 0 <= frame_idx < len(sig_frames):
            landmarks = sig_frames[frame_idx]
            
            if self.normalize_display:
                # Apply body-centric normalization for visual comparison
                landmarks = SkeletonDrawer.normalize_landmarks(landmarks)
                
                # Translate back to frame center for visibility
                center_x = self.width // 2
                center_y = self.height // 2
                
                normalized = {}
                for key in landmarks:
                    if landmarks[key] is not None:
                        points = landmarks[key].copy()
                        points[:, 0] += center_x  # Translate X
                        points[:, 1] += center_y  # Translate Y
                        normalized[key] = points
                
                return normalized
            else:
                return landmarks
        
        return {}
    
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
        
        if lm:
            frame_blank = SkeletonDrawer.draw_skeleton(
                frame_blank, lm, lang=lang,
                show_joints=self.show_joints
            )
        
        self._draw_frame_info(frame_blank, self.current_frame, total,
                             sig_name, lang)
        self._draw_normalization_info(frame_blank)
        
        help_text = "SPACE:play/pause | </>:frame | n:normalize | d:dots | q:quit"
        cv2.putText(frame_blank, help_text, (10, frame_blank.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        return frame_blank
    
    def _create_side_by_side(self) -> np.ndarray:
        """Create side-by-side visualization.
        
        Note: High CPU cost. Recommended to use single-screen mode first.
        """
        # Scale down individual frames to fit horizontally
        scale = 0.45  # Each frame is 45% of full width
        scaled_h = int(self.height * scale)
        scaled_w = int(self.width * scale)
        
        frame1_blank = np.zeros((scaled_h, scaled_w, 3), dtype=np.uint8)
        frame2_blank = np.zeros((scaled_h, scaled_w, 3), dtype=np.uint8)
        
        # Get landmarks for current frame
        lm1 = self._get_current_landmarks(self.current_frame, self.frames1)
        lm2 = self._get_current_landmarks(self.current_frame, self.frames2)
        
        # Scale landmarks for smaller frames
        if lm1:
            lm1_scaled = {}
            for key, val in lm1.items():
                if val is not None:
                    val_scaled = val.copy()
                    val_scaled[:, 0] *= scale
                    val_scaled[:, 1] *= scale
                    lm1_scaled[key] = val_scaled
            frame1_blank = SkeletonDrawer.draw_skeleton(
                frame1_blank, lm1_scaled, lang=self.lang1,
                show_joints=self.show_joints
            )
        
        if lm2:
            lm2_scaled = {}
            for key, val in lm2.items():
                if val is not None:
                    val_scaled = val.copy()
                    val_scaled[:, 0] *= scale
                    val_scaled[:, 1] *= scale
                    lm2_scaled[key] = val_scaled
            frame2_blank = SkeletonDrawer.draw_skeleton(
                frame2_blank, lm2_scaled, lang=self.lang2,
                show_joints=self.show_joints
            )
        
        # Add info (scaled)
        cv2.putText(frame1_blank, f"{self.lang1} | Frame {self.current_frame}/{len(self.frames1)}", 
                   (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame1_blank, f"Sig: {self.sig1_path.stem}", 
                   (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        
        cv2.putText(frame2_blank, f"{self.lang2} | Frame {self.current_frame}/{len(self.frames2)}", 
                   (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame2_blank, f"Sig: {self.sig2_path.stem}", 
                   (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
        
        # Combine side-by-side
        combined = np.hstack([frame1_blank, frame2_blank])
        
        # Add unified info
        self._draw_sync_info(combined)
        self._draw_normalization_info(combined)
        
        # Control help (smaller text to fit)
        help_text = "SPACE:play/pause | </>:frame | n:norm | d:dots | q:quit | ⚠️ HIGH CPU"
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
        
        if lm:
            frame_blank = SkeletonDrawer.draw_skeleton(
                frame_blank, lm, lang=lang,
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
            
            # Auto-advance if playing
            if self.is_playing:
                self.current_frame = (self.current_frame + 1) % self.max_frame
        
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
    parser.add_argument('--fps', type=int, default=15,
                       help='Playback FPS (default: 15)')
    
    args = parser.parse_args()
    
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
