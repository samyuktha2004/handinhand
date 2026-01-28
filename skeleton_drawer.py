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
        
        # Draw left hand skeleton
        if 'left_hand' in landmarks and landmarks['left_hand'] is not None:
            left_hand = landmarks['left_hand']
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
        if 'right_hand' in landmarks and landmarks['right_hand'] is not None:
            right_hand = landmarks['right_hand']
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
        
        # Target center (middle of frame, slightly above center for signing space)
        target_center = np.array([frame_width / 2, frame_height * 0.4])
        
        # Transform each component: translate to origin, scale, translate to target
        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if landmarks.get(key) is not None and len(landmarks[key]) > 0:
                points = landmarks[key].copy()
                
                # Translate: shoulder center to origin
                points[:, 0] -= shoulder_center[0]
                points[:, 1] -= shoulder_center[1]
                
                # Scale uniformly
                points[:, 0] *= scale
                points[:, 1] *= scale
                
                # Translate: origin to target center
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
