#!/usr/bin/env python3
"""
Skeleton Drawer Utility
=======================
Converts MediaPipe landmarks (JSON) into 2D skeleton visualization using cv2.line.

Purpose:
- Debug signature preservation (body, hands, face movements)
- Verify normalization (body-centric positioning)
- Visual synchronization check (ASL vs BSL frame alignment)
- Confirm NMS preservation (hand shapes, body orientation)

Usage:
    from skeleton_drawer import draw_skeleton
    img_with_skeleton = draw_skeleton(frame, landmarks_dict, lang="ASL", mode="debug")
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Any, List, Optional


class SkeletonDrawer:
    """Draw 2D human skeleton from MediaPipe landmarks."""
    
    # MediaPipe Holistic landmark indices
    # Pose: 0-32 (33 total)
    # Left Hand: 0-20 (21 per hand, indexed from 0)
    # Right Hand: 0-20
    # Face: 0-467 (468 total)
    
    # Face anchor fallback chain for dynamic neck connection
    # Try in order: nose_tip(1) → glabella(168) → upper_lip(0) → chin(152)
    FACE_ANCHOR_FALLBACKS = [1, 168, 0, 152]
    
    # Pose connections (body chain)
    # NOTE: Signatures may have 6 landmarks (partial) instead of full 33
    # Connections only drawn if both indices exist and are valid
    POSE_CONNECTIONS = [
        # Full MediaPipe pose connections (if available)
        # Right arm: shoulder -> elbow -> wrist
        (12, 14), (14, 16),
        # Left arm: shoulder -> elbow -> wrist
        (11, 13), (13, 15),
        # Torso: shoulders to hips
        (11, 12),
        (11, 23), (12, 24),
        # Right leg: hip -> knee -> ankle
        (24, 26), (26, 28),
        # Left leg: hip -> knee -> ankle
        (23, 25), (25, 27),
        # Feet
        (28, 30), (28, 32),
        (27, 29), (27, 31),
        # Partial pose connections (for 6-landmark signatures)
        (0, 1), (0, 2), (1, 3), (2, 4), (3, 5),  # Basic skeleton (no wrist-to-wrist line)
    ]
    
    # Hand connections grouped by finger for color-coding
    # 0=wrist, 1-4=thumb, 5-8=index, 9-12=middle, 13-16=ring, 17-20=pinky
    FINGER_CONNECTIONS = {
        'thumb':  [(0, 1), (1, 2), (2, 3), (3, 4)],
        'index':  [(0, 5), (5, 6), (6, 7), (7, 8)],
        'middle': [(0, 9), (9, 10), (10, 11), (11, 12)],
        'ring':   [(0, 13), (13, 14), (14, 15), (15, 16)],
        'pinky':  [(0, 17), (17, 18), (18, 19), (19, 20)],
    }
    
    # Flat list for backwards compatibility
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),      # Index
        (0, 9), (9, 10), (10, 11), (11, 12), # Middle
        (0, 13), (13, 14), (14, 15), (15, 16), # Ring
        (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    ]
    
    # Finger colors (BGR) - distinct colors per finger
    FINGER_COLORS = {
        'thumb':  (0, 0, 255),     # Red
        'index':  (0, 165, 255),   # Orange
        'middle': (0, 255, 0),     # Green
        'ring':   (255, 0, 0),     # Blue
        'pinky':  (255, 0, 255),   # Purple/Magenta
    }
    
    # Colors for visualization (BGR)
    COLOR_POSE = (0, 255, 0)       # Green for body
    COLOR_NECK = (0, 200, 200)     # Cyan-yellow for neck
    COLOR_LEFT_HAND = (255, 0, 0)  # Blue for left hand (base)
    COLOR_RIGHT_HAND = (0, 0, 255) # Red for right hand (base)
    COLOR_JOINT = (0, 255, 255)    # Yellow for joints
    COLOR_JOINT_BORDER = (255, 255, 255)  # White border for joints
    
    THICKNESS_LINE = 2
    THICKNESS_JOINT = 4
    JOINT_RADIUS = 3
    JOINT_RADIUS_DEBUG = 5  # Larger dots in debug mode
    
    @staticmethod
    def _get_face_anchor(face_landmarks: np.ndarray, h: int, w: int) -> Optional[Tuple[int, int]]:
        """
        Get face anchor point for dynamic neck connection.
        Uses fallback chain: nose_tip(1) → glabella(168) → upper_lip(0) → chin(152)
        
        Args:
            face_landmarks: Face landmarks array (468 x 2/3)
            h, w: Frame dimensions for validation
        
        Returns:
            (x, y) tuple if valid anchor found, None otherwise
        """
        for idx in SkeletonDrawer.FACE_ANCHOR_FALLBACKS:
            if idx < len(face_landmarks):
                pt = face_landmarks[idx][:2]
                # Check if point is valid (not zero and within bounds)
                if pt[0] != 0 or pt[1] != 0:
                    pt_int = (int(pt[0]), int(pt[1]))
                    if SkeletonDrawer._is_valid_point(pt_int, h, w):
                        return pt_int
        return None
    
    @staticmethod
    def _get_shoulder_midpoint(pose: np.ndarray, h: int, w: int) -> Optional[Tuple[int, int]]:
        """
        Get shoulder midpoint for neck connection.
        
        Args:
            pose: Pose landmarks array
            h, w: Frame dimensions for validation
        
        Returns:
            (x, y) tuple if valid, None otherwise
        """
        # MediaPipe pose: 11 = left shoulder, 12 = right shoulder
        if len(pose) > 12:
            left_shoulder = pose[11][:2]
            right_shoulder = pose[12][:2]
            
            # Check both shoulders are valid
            if (left_shoulder[0] != 0 or left_shoulder[1] != 0) and \
               (right_shoulder[0] != 0 or right_shoulder[1] != 0):
                midpoint = ((left_shoulder[0] + right_shoulder[0]) / 2,
                           (left_shoulder[1] + right_shoulder[1]) / 2)
                pt_int = (int(midpoint[0]), int(midpoint[1]))
                if SkeletonDrawer._is_valid_point(pt_int, h, w):
                    return pt_int
        return None
    
    @staticmethod
    def _draw_hand_colored(
        frame: np.ndarray,
        hand_landmarks: np.ndarray,
        h: int, w: int,
        base_color: Tuple[int, int, int],
        mode: str = "debug",
        use_finger_colors: bool = True
    ) -> None:
        """
        Draw hand skeleton with color-coded fingers.
        
        Args:
            frame: Image to draw on (modified in place)
            hand_landmarks: Hand landmarks array (21 x 2/3)
            h, w: Frame dimensions
            base_color: Base color for the hand (used if use_finger_colors=False)
            mode: "debug" or "clean"
            use_finger_colors: If True, each finger gets distinct color
        """
        line_type = cv2.LINE_AA  # Anti-aliased lines
        
        # Draw connections (lines first, then points overlay)
        for finger_name, connections in SkeletonDrawer.FINGER_CONNECTIONS.items():
            color = SkeletonDrawer.FINGER_COLORS[finger_name] if use_finger_colors else base_color
            
            for idx1, idx2 in connections:
                if idx1 < len(hand_landmarks) and idx2 < len(hand_landmarks):
                    pt1 = tuple(map(int, hand_landmarks[idx1][:2]))
                    pt2 = tuple(map(int, hand_landmarks[idx2][:2]))
                    
                    # Both endpoints must be valid
                    if SkeletonDrawer._is_valid_point(pt1, h, w) and \
                       SkeletonDrawer._is_valid_point(pt2, h, w) and \
                       (pt1[0] != 0 or pt1[1] != 0) and \
                       (pt2[0] != 0 or pt2[1] != 0):
                        cv2.line(frame, pt1, pt2, color, 
                                SkeletonDrawer.THICKNESS_LINE, line_type)
        
        # Draw joints (after lines for visual overlay) - only in debug mode
        if mode == "debug":
            joint_radius = SkeletonDrawer.JOINT_RADIUS_DEBUG
            for i, point in enumerate(hand_landmarks):
                pt = tuple(map(int, point[:2]))
                if SkeletonDrawer._is_valid_point(pt, h, w) and \
                   (pt[0] != 0 or pt[1] != 0):
                    # White border first
                    cv2.circle(frame, pt, joint_radius + 1,
                              SkeletonDrawer.COLOR_JOINT_BORDER, -1, cv2.LINE_AA)
                    # Colored fill
                    cv2.circle(frame, pt, joint_radius,
                              SkeletonDrawer.COLOR_JOINT, -1, cv2.LINE_AA)
    
    @staticmethod
    def draw_skeleton(
        frame: np.ndarray,
        landmarks: Dict[str, np.ndarray],
        lang: str = "ASL",
        show_joints: bool = True,
        show_confidence: bool = False,
        mode: str = "debug"
    ) -> np.ndarray:
        """
        Draw 2D skeleton on frame from MediaPipe landmarks.
        
        Args:
            frame: Input image (OpenCV format)
            landmarks: Dict with keys 'pose', 'left_hand', 'right_hand'
                      Each is (N, 2) or (N, 3) array of x,y[,confidence]
            lang: Language label for display (ASL/BSL)
            show_joints: Draw circles at joint positions
            show_confidence: Print confidence scores (if available)
            mode: "debug" (dots + indices) or "clean" (smooth lines only)
        
        Returns:
            frame with skeleton drawn
        """
        frame = frame.copy()
        h, w = frame.shape[:2]
        line_type = cv2.LINE_AA  # Anti-aliased lines
        
        # Determine joint radius based on mode
        joint_radius = SkeletonDrawer.JOINT_RADIUS_DEBUG if mode == "debug" else SkeletonDrawer.JOINT_RADIUS
        
        # Draw pose skeleton (body) - lines first
        pose_joints_to_draw = []  # Collect joints to draw after lines
        if 'pose' in landmarks and landmarks['pose'] is not None:
            pose = landmarks['pose']
            for idx1, idx2 in SkeletonDrawer.POSE_CONNECTIONS:
                if idx1 < len(pose) and idx2 < len(pose):
                    pt1 = tuple(map(int, pose[idx1][:2]))
                    pt2 = tuple(map(int, pose[idx2][:2]))
                    
                    # Both endpoints must be valid (MediaPipe pattern)
                    if SkeletonDrawer._is_valid_point(pt1, h, w) and \
                       SkeletonDrawer._is_valid_point(pt2, h, w) and \
                       (pt1[0] != 0 or pt1[1] != 0) and \
                       (pt2[0] != 0 or pt2[1] != 0):
                        cv2.line(frame, pt1, pt2, 
                                SkeletonDrawer.COLOR_POSE, 
                                SkeletonDrawer.THICKNESS_LINE, line_type)
            
            # Dynamic neck connection: shoulder_midpoint → face_anchor
            shoulder_midpoint = SkeletonDrawer._get_shoulder_midpoint(pose, h, w)
            if shoulder_midpoint is not None:
                face_anchor = None
                if 'face' in landmarks and landmarks['face'] is not None:
                    face_anchor = SkeletonDrawer._get_face_anchor(landmarks['face'], h, w)
                
                if face_anchor is not None:
                    cv2.line(frame, shoulder_midpoint, face_anchor,
                            SkeletonDrawer.COLOR_NECK, 
                            SkeletonDrawer.THICKNESS_LINE, line_type)
            
            # Collect pose joints to draw
            if show_joints and mode == "debug":
                for point in pose:
                    pt = tuple(map(int, point[:2]))
                    if SkeletonDrawer._is_valid_point(pt, h, w) and \
                       (pt[0] != 0 or pt[1] != 0):
                        pose_joints_to_draw.append(pt)
        
        # Draw hands with color-coded fingers
        if 'left_hand' in landmarks and landmarks['left_hand'] is not None:
            SkeletonDrawer._draw_hand_colored(
                frame, landmarks['left_hand'], h, w,
                SkeletonDrawer.COLOR_LEFT_HAND, mode, use_finger_colors=True
            )
        
        if 'right_hand' in landmarks and landmarks['right_hand'] is not None:
            SkeletonDrawer._draw_hand_colored(
                frame, landmarks['right_hand'], h, w,
                SkeletonDrawer.COLOR_RIGHT_HAND, mode, use_finger_colors=True
            )
        
        # Draw pose joints AFTER lines (MediaPipe pattern - aesthetically better)
        if mode == "debug":
            for pt in pose_joints_to_draw:
                # White border first
                cv2.circle(frame, pt, joint_radius + 1,
                          SkeletonDrawer.COLOR_JOINT_BORDER, -1, line_type)
                # Colored fill
                cv2.circle(frame, pt, joint_radius,
                          SkeletonDrawer.COLOR_JOINT, -1, line_type)
        
        # Add language label
        cv2.putText(frame, lang, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   1.0, (255, 255, 255), 2, line_type)
        
        # Add mode indicator
        mode_label = "[DEBUG]" if mode == "debug" else "[CLEAN]"
        cv2.putText(frame, mode_label, (w - 100, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   0.5, (200, 200, 200), 1, line_type)
        
        return frame
    
    @staticmethod
    def _is_valid_point(pt: Tuple[int, int], h: int, w: int) -> bool:
        """Check if point is within frame bounds."""
        x, y = pt
        return 0 <= x < w and 0 <= y < h
    
    @staticmethod
    def normalize_landmarks(landmarks: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Apply body-centric normalization: center on shoulder midpoint.
        
        Args:
            landmarks: Dict with 'pose', 'left_hand', 'right_hand'
        
        Returns:
            Normalized landmarks (in-place modified copy)
        """
        result = {}
        
        if 'pose' in landmarks and landmarks['pose'] is not None:
            pose = landmarks['pose'].copy()
            
            # Shoulder indices: 11 (left), 12 (right)
            if len(pose) > 12:
                shoulder_left = pose[11][:2]
                shoulder_right = pose[12][:2]
                center = (shoulder_left + shoulder_right) / 2
                
                # Translate all pose landmarks
                pose[:, :2] = pose[:, :2] - center
                result['pose'] = pose
        
        # Translate hands relative to same center if available
        if 'left_hand' in landmarks and landmarks['left_hand'] is not None:
            left_hand = landmarks['left_hand'].copy()
            if 'pose' in result:
                pose = result['pose']
                if len(pose) > 15:  # Wrist index for left hand
                    wrist = pose[15][:2]
                    left_hand[:, :2] = left_hand[:, :2] - wrist
            result['left_hand'] = left_hand
        
        if 'right_hand' in landmarks and landmarks['right_hand'] is not None:
            right_hand = landmarks['right_hand'].copy()
            if 'pose' in result:
                pose = result['pose']
                if len(pose) > 16:  # Wrist index for right hand
                    wrist = pose[16][:2]
                    right_hand[:, :2] = right_hand[:, :2] - wrist
            result['right_hand'] = right_hand
        
        return result


def extract_landmarks_from_signature(sig_dict: Dict[str, Any], frame_width: int = 640, frame_height: int = 480) -> List:
    """
    Extract MediaPipe landmarks from signature JSON.
    
    Signature format (current):
    {
        "sign": "hello",
        "language": "ASL",
        "pose_data": [
            {
                "pose": [[x,y,z], ...],  # Normalized coordinates (0-1)
                "left_hand": [[x,y,z], ...],
                "right_hand": [[x,y,z], ...],
                "face": [[x,y,z], ...]
            },
            ...
        ]
    }
    
    Args:
        sig_dict: Signature JSON loaded as dict
        frame_width: Width to scale normalized coordinates to (default 640)
        frame_height: Height to scale normalized coordinates to (default 480)
    
    Returns:
        List of landmark dicts, one per frame
    """
    frames_data = []
    
    def _scale_landmarks(lm_array: np.ndarray, fw: int, fh: int) -> np.ndarray:
        """Scale normalized coordinates (0-1) to pixel coordinates."""
        result = lm_array.copy()
        # Scale x, y to frame size (keep z as-is for confidence/depth)
        result[:, 0] *= fw  # x
        result[:, 1] *= fh  # y
        return result
    
    # Check for 'pose_data' (current format)
    if 'pose_data' in sig_dict:
        for frame in sig_dict['pose_data']:
            landmarks = {}
            
            if 'pose' in frame and frame['pose']:
                pose_arr = np.array(frame['pose'], dtype=np.float32)
                landmarks['pose'] = _scale_landmarks(pose_arr, frame_width, frame_height)
            if 'left_hand' in frame and frame['left_hand']:
                lh_arr = np.array(frame['left_hand'], dtype=np.float32)
                landmarks['left_hand'] = _scale_landmarks(lh_arr, frame_width, frame_height)
            if 'right_hand' in frame and frame['right_hand']:
                rh_arr = np.array(frame['right_hand'], dtype=np.float32)
                landmarks['right_hand'] = _scale_landmarks(rh_arr, frame_width, frame_height)
            
            frames_data.append(landmarks)
    
    # Fallback to 'frames' (legacy format)
    elif 'frames' in sig_dict:
        for frame in sig_dict['frames']:
            landmarks = {}
            
            if 'pose' in frame and frame['pose']:
                pose_arr = np.array(frame['pose'], dtype=np.float32)
                landmarks['pose'] = _scale_landmarks(pose_arr, frame_width, frame_height)
            if 'left_hand' in frame and frame['left_hand']:
                lh_arr = np.array(frame['left_hand'], dtype=np.float32)
                landmarks['left_hand'] = _scale_landmarks(lh_arr, frame_width, frame_height)
            if 'right_hand' in frame and frame['right_hand']:
                rh_arr = np.array(frame['right_hand'], dtype=np.float32)
                landmarks['right_hand'] = _scale_landmarks(rh_arr, frame_width, frame_height)
            
            frames_data.append(landmarks)
    
    return frames_data


if __name__ == "__main__":
    print("Skeleton Drawer Utility Module")
    print("Import and use in skeleton_debugger.py")
