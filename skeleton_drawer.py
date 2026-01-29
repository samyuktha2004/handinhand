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

Reference Body Integration:
- All skeletons are scaled to REFERENCE_SHOULDER_WIDTH (100px)
- This ensures consistent body size across all signs
- Hands stay within frame bounds regardless of original video capture

Usage:
    from skeleton_drawer import draw_skeleton
    img_with_skeleton = draw_skeleton(frame, landmarks_dict, lang="ASL")
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Any, List

# Reference body constants (canonical coordinate system)
# All signatures are normalized to these proportions
REFERENCE_SHOULDER_WIDTH = 100  # Target shoulder span in pixels
REFERENCE_FRAME_WIDTH = 640
REFERENCE_FRAME_HEIGHT = 480


class SkeletonDrawer:
    """Draw 2D human skeleton from MediaPipe landmarks."""
    
    # MediaPipe Holistic landmark indices
    # Pose: 0-32 (33 total)
    # Left Hand: 0-20 (21 per hand, indexed from 0)
    # Right Hand: 0-20
    # Face: 0-467 (468 total, we'll skip detailed face for now)
    
    # Pose connections (body chain)
    # NOTE: Signatures may have 6 landmarks (partial) instead of full 33
    # Connections only drawn if both indices exist
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
    
    # Hand connections (per hand: 21 landmarks)
    # 0=wrist, 1-4=thumb, 5-8=index, 9-12=middle, 13-16=ring, 17-20=pinky
    HAND_CONNECTIONS = [
        # Thumb
        (0, 1), (1, 2), (2, 3), (3, 4),
        # Index
        (0, 5), (5, 6), (6, 7), (7, 8),
        # Middle
        (0, 9), (9, 10), (10, 11), (11, 12),
        # Ring
        (0, 13), (13, 14), (14, 15), (15, 16),
        # Pinky
        (0, 17), (17, 18), (18, 19), (19, 20),
    ]
    
    # Colors for visualization (BGR)
    COLOR_POSE = (0, 255, 0)      # Green for body
    COLOR_LEFT_HAND = (255, 0, 0)  # Blue for left hand
    COLOR_RIGHT_HAND = (0, 0, 255) # Red for right hand
    COLOR_JOINT = (0, 255, 255)    # Yellow for joints
    
    THICKNESS_LINE = 2
    THICKNESS_JOINT = 4
    JOINT_RADIUS = 3
    
    # Reference hand landmarks relative to wrist (0,0)
    # Generated from show_reference_body.py generate_hand_landmarks()
    # This is a neutral "open hand" pointing downward (+Y direction)
    # Will be rotated to match arm orientation
    # 
    # Key insight: When data is missing, we attach this to the wrist
    # and orient along the forearm direction. When data returns,
    # the transition is seamless because proportions match.
    @staticmethod
    def _generate_reference_hand(wrist_pos, arm_direction, is_left):
        """
        Generate reference hand landmarks attached to wrist.
        
        Uses the same proportions as show_reference_body.py for consistency.
        The hand is oriented along the arm direction (elbow → wrist).
        
        Args:
            wrist_pos: (x, y) wrist position in pixels
            arm_direction: (dx, dy) unit vector from elbow to wrist
            is_left: True for left hand
        
        Returns:
            np.array of shape (21, 3) - hand landmarks
        """
        import math
        
        wx, wy = wrist_pos
        
        # Segment lengths (matching reference body)
        seg = 10  # finger segment length
        palm_depth = 25  # wrist to MCP distance
        palm_width = 35  # width of palm at MCP level
        
        # Calculate rotation from arm direction
        dx, dy = arm_direction
        arm_angle = math.atan2(dy, dx)  # Angle from +X axis
        
        def rotate_point(x, y, angle, cx, cy):
            """Rotate point (x,y) around (cx,cy) by angle."""
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            x -= cx
            y -= cy
            rx = x * cos_a - y * sin_a + cx
            ry = x * sin_a + y * cos_a + cy
            return rx, ry
        
        landmarks = []
        
        # Mirror for left vs right hand
        mirror = -1 if is_left else 1
        
        # Build hand in "pointing right" orientation, then rotate
        # Local coordinates: +X = toward fingertips, +Y = toward pinky
        
        # 0: Wrist (at origin in local coords)
        local_points = [(0, 0)]
        
        # Thumb (angled outward)
        thumb_y = -18 * mirror  # thumb side offset
        local_points.append((3, thumb_y))  # CMC
        local_points.append((12, thumb_y - 8 * mirror))  # MCP
        local_points.append((20, thumb_y - 10 * mirror))  # IP
        local_points.append((26, thumb_y - 12 * mirror))  # TIP
        
        # Finger MCP positions (across palm width)
        mcp_y = {
            'index': -palm_width * 0.4 * mirror,
            'middle': -palm_width * 0.15 * mirror,
            'ring': palm_width * 0.15 * mirror,
            'pinky': palm_width * 0.45 * mirror,
        }
        
        # Finger lengths
        finger_lens = {
            'index': seg * 3.2,
            'middle': seg * 3.5,
            'ring': seg * 3.2,
            'pinky': seg * 2.8,
        }
        
        # Generate 4 fingers
        for finger in ['index', 'middle', 'ring', 'pinky']:
            base_x = palm_depth
            base_y = mcp_y[finger]
            length = finger_lens[finger]
            seg_len = length / 3
            
            local_points.append((base_x, base_y))  # MCP
            local_points.append((base_x + seg_len, base_y))  # PIP
            local_points.append((base_x + seg_len * 2, base_y))  # DIP
            local_points.append((base_x + seg_len * 3, base_y))  # TIP
        
        # Rotate all points by arm angle and translate to wrist
        for lx, ly in local_points:
            # Rotate around origin
            rx = lx * math.cos(arm_angle) - ly * math.sin(arm_angle)
            ry = lx * math.sin(arm_angle) + ly * math.cos(arm_angle)
            # Translate to wrist position
            landmarks.append([wx + rx, wy + ry, 0])
        
        return np.array(landmarks, dtype=np.float32)
    
    # Default face offsets relative to shoulder center
    # Face is above shoulders, centered
    DEFAULT_FACE_OFFSETS = np.array([
        [0, -80, 0],    # Nose tip (centered, above shoulders)
        [-25, -70, 0],  # Left eye
        [25, -70, 0],   # Right eye
        [0, -55, 0],    # Mouth center
    ], dtype=np.float32)
    
    @staticmethod
    def _is_hand_valid(hand: np.ndarray) -> bool:
        """Check if hand data is valid (not all zeros)."""
        if hand is None or len(hand) == 0:
            return False
        # Hand is invalid if all x,y coordinates are 0 or near 0
        coords = hand[:, :2]
        return not (np.abs(coords).max() < 1.0)
    
    @staticmethod
    def _is_face_valid(face: np.ndarray) -> bool:
        """Check if face data is valid (not all zeros)."""
        if face is None or len(face) == 0:
            return False
        coords = face[:, :2]
        return not (np.abs(coords).max() < 1.0)
    
    @staticmethod
    def _get_arm_vector(pose: np.ndarray, is_left: bool) -> Tuple[np.ndarray, np.ndarray]:
        """Get elbow and wrist positions for calculating arm direction.
        
        Returns:
            (elbow_pos, wrist_pos) as numpy arrays, or (None, None) if not available
        """
        if pose is None or len(pose) < 6:
            return None, None
        
        if len(pose) == 6:
            # Reduced pose: 2=left_elbow, 3=right_elbow, 4=left_wrist, 5=right_wrist
            elbow_idx = 2 if is_left else 3
            wrist_idx = 4 if is_left else 5
        else:
            # Full pose
            elbow_idx = 13 if is_left else 14
            wrist_idx = 15 if is_left else 16
        
        if elbow_idx < len(pose) and wrist_idx < len(pose):
            return pose[elbow_idx][:2].copy(), pose[wrist_idx][:2].copy()
        return None, None
    
    @staticmethod
    def _rotate_points(points: np.ndarray, angle: float, center: np.ndarray) -> np.ndarray:
        """Rotate points around a center by given angle (radians).
        
        Args:
            points: (N, 3) array of points
            angle: Rotation angle in radians
            center: (2,) center point for rotation
        
        Returns:
            Rotated points array
        """
        result = points.copy()
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        
        # Translate to origin
        result[:, 0] -= center[0]
        result[:, 1] -= center[1]
        
        # Rotate
        x_new = result[:, 0] * cos_a - result[:, 1] * sin_a
        y_new = result[:, 0] * sin_a + result[:, 1] * cos_a
        
        result[:, 0] = x_new + center[0]
        result[:, 1] = y_new + center[1]
        
        return result
    
    @staticmethod
    def _create_placeholder_hand(pose: np.ndarray, is_left: bool, scale: float = 1.0) -> np.ndarray:
        """Create placeholder hand using reference body proportions.
        
        The hand is attached to the wrist and oriented along the forearm
        direction (from elbow to wrist), creating a natural "relaxed" position.
        
        Uses the same proportions as show_reference_body.py for consistency,
        so when real data returns, the transition is seamless.
        
        Args:
            pose: Pose landmarks array
            is_left: True for left hand, False for right
            scale: Scale factor for hand size (1.0 = reference proportions)
        
        Returns:
            Hand landmarks array (21, 3) positioned and oriented correctly
        """
        elbow_pos, wrist_pos = SkeletonDrawer._get_arm_vector(pose, is_left)
        
        if wrist_pos is None:
            return None
        
        # Calculate arm direction (elbow → wrist)
        if elbow_pos is not None:
            arm_vec = wrist_pos - elbow_pos
            length = np.sqrt(arm_vec[0]**2 + arm_vec[1]**2)
            if length > 0:
                arm_direction = (arm_vec[0] / length, arm_vec[1] / length)
            else:
                arm_direction = (1, 0) if not is_left else (-1, 0)
        else:
            # Default direction when no elbow data
            arm_direction = (1, 0) if not is_left else (-1, 0)
        
        # Generate reference hand with correct orientation
        hand = SkeletonDrawer._generate_reference_hand(wrist_pos, arm_direction, is_left)
        
        # Apply scale if needed
        if scale != 1.0 and hand is not None:
            # Scale around wrist position
            wx, wy = wrist_pos
            hand[:, 0] = (hand[:, 0] - wx) * scale + wx
            hand[:, 1] = (hand[:, 1] - wy) * scale + wy
        
        return hand
    
    @staticmethod
    def _create_placeholder_face(pose: np.ndarray, scale: float = 1.0) -> np.ndarray:
        """Create placeholder face positioned above shoulders.
        
        Args:
            pose: Pose landmarks array  
            scale: Scale factor for face size
        
        Returns:
            Face landmarks array (4, 3) positioned correctly
        """
        if pose is None or len(pose) < 2:
            return None
        
        # Calculate shoulder center
        left_shoulder = pose[0][:2]
        right_shoulder = pose[1][:2]
        shoulder_center = (left_shoulder + right_shoulder) / 2
        
        # Create face at neutral position above shoulders
        face = SkeletonDrawer.DEFAULT_FACE_OFFSETS.copy() * scale
        face[:, 0] += shoulder_center[0]
        face[:, 1] += shoulder_center[1]
        
        return face
    
    @staticmethod
    def draw_skeleton(
        frame: np.ndarray,
        landmarks: Dict[str, np.ndarray],
        lang: str = "ASL",
        show_joints: bool = True,
        show_confidence: bool = False
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
        
        Returns:
            frame with skeleton drawn
        """
        frame = frame.copy()
        h, w = frame.shape[:2]
        
        # Draw pose skeleton (body)
        if 'pose' in landmarks and landmarks['pose'] is not None:
            pose = landmarks['pose']
            for idx1, idx2 in SkeletonDrawer.POSE_CONNECTIONS:
                if idx1 < len(pose) and idx2 < len(pose):
                    pt1 = tuple(map(int, pose[idx1][:2]))
                    pt2 = tuple(map(int, pose[idx2][:2]))
                    
                    # Validity check (ensure points are within frame)
                    if SkeletonDrawer._is_valid_point(pt1, h, w) and \
                       SkeletonDrawer._is_valid_point(pt2, h, w):
                        cv2.line(frame, pt1, pt2, 
                                SkeletonDrawer.COLOR_POSE, 
                                SkeletonDrawer.THICKNESS_LINE)
            
            # Draw joints
            if show_joints:
                for point in pose:
                    pt = tuple(map(int, point[:2]))
                    if SkeletonDrawer._is_valid_point(pt, h, w):
                        cv2.circle(frame, pt, SkeletonDrawer.JOINT_RADIUS,
                                  SkeletonDrawer.COLOR_JOINT, -1)
        
        # Get pose for placeholder generation (needed for arm-angle-aware hands)
        pose = landmarks.get('pose')
        
        # Draw left hand skeleton
        left_hand = landmarks.get('left_hand')
        if left_hand is not None or pose is not None:
            # Check if hand data is valid (not zeros)
            if left_hand is None or not SkeletonDrawer._is_hand_valid(left_hand):
                # Create placeholder hand oriented along arm direction
                left_hand = SkeletonDrawer._create_placeholder_hand(pose, is_left=True)
            
            if left_hand is not None:
                for idx1, idx2 in SkeletonDrawer.HAND_CONNECTIONS:
                    if idx1 < len(left_hand) and idx2 < len(left_hand):
                        pt1 = tuple(map(int, left_hand[idx1][:2]))
                        pt2 = tuple(map(int, left_hand[idx2][:2]))
                        
                        if SkeletonDrawer._is_valid_point(pt1, h, w) and \
                           SkeletonDrawer._is_valid_point(pt2, h, w):
                            cv2.line(frame, pt1, pt2,
                                    SkeletonDrawer.COLOR_LEFT_HAND,
                                    SkeletonDrawer.THICKNESS_LINE)
                
                if show_joints:
                    for point in left_hand:
                        pt = tuple(map(int, point[:2]))
                        if SkeletonDrawer._is_valid_point(pt, h, w):
                            cv2.circle(frame, pt, SkeletonDrawer.JOINT_RADIUS,
                                      SkeletonDrawer.COLOR_LEFT_HAND, -1)
        
        # Draw right hand skeleton
        right_hand = landmarks.get('right_hand')
        if right_hand is not None or pose is not None:
            # Check if hand data is valid (not zeros)
            if right_hand is None or not SkeletonDrawer._is_hand_valid(right_hand):
                # Create placeholder hand oriented along arm direction
                right_hand = SkeletonDrawer._create_placeholder_hand(pose, is_left=False)
            
            if right_hand is not None:
                for idx1, idx2 in SkeletonDrawer.HAND_CONNECTIONS:
                    if idx1 < len(right_hand) and idx2 < len(right_hand):
                        pt1 = tuple(map(int, right_hand[idx1][:2]))
                        pt2 = tuple(map(int, right_hand[idx2][:2]))
                        
                        if SkeletonDrawer._is_valid_point(pt1, h, w) and \
                           SkeletonDrawer._is_valid_point(pt2, h, w):
                            cv2.line(frame, pt1, pt2,
                                    SkeletonDrawer.COLOR_RIGHT_HAND,
                                    SkeletonDrawer.THICKNESS_LINE)
                
                if show_joints:
                    for point in right_hand:
                        pt = tuple(map(int, point[:2]))
                        if SkeletonDrawer._is_valid_point(pt, h, w):
                            cv2.circle(frame, pt, SkeletonDrawer.JOINT_RADIUS,
                                      SkeletonDrawer.COLOR_RIGHT_HAND, -1)
        
        # Add language label
        cv2.putText(frame, lang, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   1.0, (255, 255, 255), 2)
        
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

    @staticmethod
    def normalize_to_reference_body(
        landmarks: Dict[str, np.ndarray],
        frame_width: int = 640,
        frame_height: int = 480,
        target_shoulder_width: int = REFERENCE_SHOULDER_WIDTH
    ) -> Dict[str, np.ndarray]:
        """
        Normalize landmarks to reference body proportions.
        
        This ensures ALL skeletons have:
        - Consistent body size (shoulder width = target_shoulder_width)
        - Centered position in frame
        - Hands stay within frame bounds
        
        Args:
            landmarks: Dict with 'pose', 'left_hand', 'right_hand', 'face' (pixel coords)
            frame_width: Target frame width
            frame_height: Target frame height
            target_shoulder_width: Target shoulder width in pixels (default 100)
        
        Returns:
            Normalized landmarks dict (all components scaled uniformly)
        """
        result = {}
        
        # Get pose landmarks (required for normalization)
        pose = landmarks.get('pose')
        if pose is None or len(pose) < 2:
            # Can't normalize without shoulders, return as-is
            return landmarks
        
        pose = pose.copy()
        
        # Calculate current shoulder width (indices 0, 1 for reduced pose)
        left_shoulder = pose[0][:2]
        right_shoulder = pose[1][:2]
        current_shoulder_width = np.linalg.norm(right_shoulder - left_shoulder)
        
        if current_shoulder_width < 1:
            # Degenerate case, return as-is
            return landmarks
        
        # Calculate scale factor
        scale = target_shoulder_width / current_shoulder_width
        
        # Calculate shoulder center (this becomes frame center)
        shoulder_center = (left_shoulder + right_shoulder) / 2
        
        # First pass: scale all points to find bounds
        scaled_points = {}
        min_y = float('inf')
        max_y = float('-inf')
        
        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if landmarks.get(key) is not None and len(landmarks[key]) > 0:
                points = landmarks[key].copy()
                
                # Skip invalid hand data (all zeros)
                if key in ['left_hand', 'right_hand']:
                    if np.abs(points[:, :2]).max() < 1.0:
                        scaled_points[key] = points
                        continue
                
                # Translate: shoulder center to origin
                points[:, 0] -= shoulder_center[0]
                points[:, 1] -= shoulder_center[1]
                
                # Scale uniformly
                points[:, 0] *= scale
                points[:, 1] *= scale
                
                scaled_points[key] = points
                
                # Track Y bounds
                min_y = min(min_y, points[:, 1].min())
                max_y = max(max_y, points[:, 1].max())
        
        # Calculate target center with dynamic Y adjustment
        # Default: 40% from top (192px for 480px frame)
        # Adjust if content would go out of bounds
        target_x = frame_width / 2
        target_y = frame_height * 0.4
        
        # If min_y (after centering at target_y) would be < 10, shift down
        margin = 10  # Pixels from edge
        if min_y + target_y < margin:
            target_y = margin - min_y
        
        # If max_y would exceed frame, shift up (but not past margin)
        if max_y + target_y > frame_height - margin:
            target_y = frame_height - margin - max_y
            # But don't go too high
            if min_y + target_y < margin:
                target_y = margin - min_y
        
        target_center = np.array([target_x, target_y])
        
        # Second pass: translate to target center
        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if key in scaled_points:
                points = scaled_points[key]
                
                # Skip invalid hand data
                if key in ['left_hand', 'right_hand']:
                    if np.abs(points[:, :2]).max() < 1.0:
                        result[key] = points
                        continue
                
                points[:, 0] += target_center[0]
                points[:, 1] += target_center[1]
                
                result[key] = points
            else:
                result[key] = landmarks.get(key)
        
        return result


def extract_landmarks_from_signature(
    sig_dict: Dict[str, Any], 
    frame_width: int = 640, 
    frame_height: int = 480,
    normalize_to_reference: bool = True
) -> List:
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
        normalize_to_reference: If True, scale to reference body proportions
                               (SHOULDER_WIDTH=100px, centered in frame)
    
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
            if 'face' in frame and frame['face']:
                face_arr = np.array(frame['face'], dtype=np.float32)
                landmarks['face'] = _scale_landmarks(face_arr, frame_width, frame_height)
            
            # Apply reference body normalization if requested
            if normalize_to_reference:
                landmarks = SkeletonDrawer.normalize_to_reference_body(
                    landmarks, frame_width, frame_height
                )
            
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
            if 'face' in frame and frame['face']:
                face_arr = np.array(frame['face'], dtype=np.float32)
                landmarks['face'] = _scale_landmarks(face_arr, frame_width, frame_height)
            
            # Apply reference body normalization if requested
            if normalize_to_reference:
                landmarks = SkeletonDrawer.normalize_to_reference_body(
                    landmarks, frame_width, frame_height
                )
            
            frames_data.append(landmarks)
    
    return frames_data


if __name__ == "__main__":
    print("Skeleton Drawer Utility Module")
    print("Import and use in skeleton_debugger.py")
