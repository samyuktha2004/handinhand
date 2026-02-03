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
- All skeletons normalized to REFERENCE_SHOULDER_WIDTH (100px)
- Reference body provides background canvas (head, neck, torso)
- MediaPipe landmarks overlay onto reference body
- Missing parts attach to parent connector or use fallback

Usage:
    from skeleton_drawer import SkeletonDrawer, ReferenceBody
    
    # Draw with reference body background
    frame = ReferenceBody.draw_canvas(frame)
    frame = SkeletonDrawer.draw_skeleton(frame, landmarks)
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Any, List, Optional


# =============================================================================
# REFERENCE BODY CONSTANTS (Canonical Coordinate System)
# =============================================================================

# Frame dimensions
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CENTER_X = FRAME_WIDTH // 2   # 320
CENTER_Y = FRAME_HEIGHT // 2  # 240

# Reference body proportions (zoom-invariant anchor)
REFERENCE_SHOULDER_WIDTH = 100  # pixels - THE normalization anchor
UPPER_ARM_LENGTH = 55           # shoulder to elbow (55% of arm)
LOWER_ARM_LENGTH = 45           # elbow to wrist (45% of arm)
TOTAL_ARM_LENGTH = UPPER_ARM_LENGTH + LOWER_ARM_LENGTH  # 100px

# Head and neck
HEAD_WIDTH = 50
HEAD_HEIGHT = 70
NECK_LENGTH = 35

# Torso
TORSO_LENGTH = 60  # below shoulders

# Colors (BGR)
REFERENCE_COLOR = (80, 80, 80)    # Dark grey for reference body outline
BODY_COLOR = (0, 255, 0)          # Green for active pose
LEFT_HAND_COLOR = (255, 0, 0)     # Blue for left hand
RIGHT_HAND_COLOR = (0, 0, 255)    # Red for right hand
JOINT_COLOR = (0, 255, 255)       # Yellow for joints
FALLBACK_COLOR = (128, 128, 128)  # Grey for fallback/placeholder
ERROR_COLOR = (0, 165, 255)       # Orange for validation errors

# Validation thresholds
PROPORTION_TOLERANCE = 0.3   # 30% deviation allowed
BOUNDS_MARGIN = 10           # pixels from edge

# Default hand size for fallback (when MediaPipe loses tracking)
FALLBACK_HAND_SIZE = 40  # pixels from wrist to fingertip


def generate_neutral_hand(wrist_pos: np.ndarray, is_left: bool = True) -> np.ndarray:
    """
    Generate a NEUTRAL REST hand shape attached to the given wrist position.
    
    CRITICAL: This must be a linguistically UNMARKED position that doesn't
    form any sign. Hands relaxed at sides, fingers loosely extended downward.
    
    This is the "rest position" in sign language - it means nothing.
    Do NOT use handshapes that could be interpreted as letters or signs.
    
    Args:
        wrist_pos: (x, y) position of the wrist
        is_left: True for left hand, False for right
        
    Returns:
        21x3 array of hand landmarks in neutral rest position
    """
    hand = np.zeros((21, 3), dtype=np.float32)
    wx, wy = wrist_pos[0], wrist_pos[1]
    
    # Neutral rest: hand hangs loosely downward, fingers slightly curved
    # This is explicitly NOT a flat hand (which could be B handshape)
    seg = FALLBACK_HAND_SIZE / 4  # segment length = 10px
    palm_depth = seg * 2  # 20px from wrist to MCP
    
    # Mirror for left vs right
    mirror = -1 if is_left else 1
    
    # Finger spacing - WIDER for visibility (was 0.6, now 1.5)
    # Total hand width should be ~60px for visibility
    finger_spacing = seg * 1.5  # 15px between fingers
    
    # 0: Wrist
    hand[0] = [wx, wy, 0.5]
    
    # Thumb (1-4): angled outward, relaxed
    thumb_x = wx + mirror * seg * 2.0  # Thumb spread wider
    hand[1] = [thumb_x, wy + seg * 0.3, 0.5]
    hand[2] = [thumb_x + mirror * seg * 0.5, wy + seg * 0.8, 0.5]
    hand[3] = [thumb_x + mirror * seg * 0.7, wy + seg * 1.3, 0.5]
    hand[4] = [thumb_x + mirror * seg * 0.8, wy + seg * 1.7, 0.5]
    
    # Fingers loosely curved (relaxed, not extended or fisted)
    # All fingers point generally downward with slight natural curl
    mcp_y = wy + palm_depth
    
    # Fingers slightly spread, naturally curved
    for i, (base_idx, x_offset) in enumerate([(5, -1.5), (9, -0.5), (13, 0.5), (17, 1.5)]):
        fx = wx + mirror * finger_spacing * x_offset
        # Natural slight curl (not straight, not fisted)
        curl = 0.15 * (i + 1)  # Increasing curl toward pinky
        hand[base_idx] = [fx, mcp_y, 0.5]  # MCP
        hand[base_idx + 1] = [fx + curl * seg, mcp_y + seg * 0.9, 0.5]  # PIP
        hand[base_idx + 2] = [fx + curl * seg * 1.5, mcp_y + seg * 1.6, 0.5]  # DIP
        hand[base_idx + 3] = [fx + curl * seg * 1.8, mcp_y + seg * 2.1, 0.5]  # TIP
    
    return hand


class ReferenceBody:
    """
    Reference body canvas - provides consistent background for all visualizations.
    
    The reference body establishes:
    - Canonical proportions (100px shoulder width)
    - Dynamic head/neck based on actual landmarks
    - NO default hands (to avoid 4-hands bug)
    
    Design choice: We draw head/neck DYNAMICALLY from landmarks when available,
    rather than as a static grey overlay. This follows Sign-MT's approach
    of keeping the face connected to actual tracking data.
    """
    
    @staticmethod
    def draw_canvas(
        frame: np.ndarray,
        center_x: int = CENTER_X,
        center_y: int = CENTER_Y,
        show_outline: bool = True,
        landmarks: Optional[Dict[str, np.ndarray]] = None
    ) -> np.ndarray:
        """
        Draw reference body outline as background canvas.
        
        If landmarks are provided, head/neck are drawn dynamically.
        Otherwise, falls back to static reference position.
        
        Args:
            frame: Input image
            center_x: X position for body center
            center_y: Y position for shoulder line
            show_outline: Whether to draw the reference outline
            landmarks: Optional dict with 'pose' and 'face' for dynamic positioning
            
        Returns:
            Frame with reference body outline
        """
        if not show_outline:
            return frame
            
        frame = frame.copy()
        
        # Calculate shoulder center from landmarks if available
        shoulder_center = (center_x, center_y)
        if landmarks and 'pose' in landmarks and landmarks['pose'] is not None:
            pose = landmarks['pose']
            if len(pose) >= 2:
                # 6-point pose: 0=left shoulder, 1=right shoulder
                left_sh = pose[0][:2]
                right_sh = pose[1][:2]
                shoulder_center = tuple(((left_sh + right_sh) / 2).astype(int))
        
        # Get head position dynamically from face landmarks if available
        head_pos = ReferenceBody._get_dynamic_head_position(landmarks, shoulder_center)
        
        # Draw dynamic neck (from shoulder midpoint to head)
        neck_bottom = shoulder_center
        neck_top = (head_pos[0], head_pos[1] + HEAD_HEIGHT // 2)  # Bottom of head
        
        # Draw head (oval) - use actual color based on whether it's tracked
        head_color = (100, 180, 100) if landmarks and 'face' in landmarks else REFERENCE_COLOR
        cv2.ellipse(frame, head_pos, 
                   (HEAD_WIDTH // 2, HEAD_HEIGHT // 2),
                   0, 0, 360, head_color, 2)
        
        # Draw face features at actual head position
        ReferenceBody._draw_face_features(frame, head_pos, head_color)
        
        # Draw neck connecting shoulder center to head bottom
        cv2.line(frame, neck_bottom, neck_top, head_color, 2)
        
        # NOTE: Do NOT draw shoulders, arms, or torso - these come from MediaPipe data
        # Only head and neck are drawn as reference elements
        
        return frame
    
    @staticmethod
    def _get_dynamic_head_position(
        landmarks: Optional[Dict[str, np.ndarray]],
        shoulder_center: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Get head position from face landmarks, with fallback chain.
        
        Fallback chain (per PROGRESS_CHECKLIST.md):
        1. nose_tip (index 1) - most reliable
        2. glabella (index 168) - between eyebrows  
        3. upper_lip (index 0) - if nose not detected
        4. chin (index 152) - last resort
        5. Static offset from shoulder center
        
        Args:
            landmarks: Dict with optional 'face' key
            shoulder_center: Shoulder midpoint for fallback
            
        Returns:
            (x, y) position for head center
        """
        if landmarks and 'face' in landmarks and landmarks['face'] is not None:
            face = landmarks['face']
            # Try fallback chain
            for idx in [1, 168, 0, 152]:
                if idx < len(face):
                    point = face[idx]
                    # Validate point is not zeros
                    if abs(point[0]) > 0.001 or abs(point[1]) > 0.001:
                        # Adjust to head center (nose is at bottom of head)
                        head_x = int(point[0])
                        head_y = int(point[1] - HEAD_HEIGHT // 3)  # Shift up from nose
                        return (head_x, head_y)
        
        # Static fallback: use reference position above shoulders
        return (shoulder_center[0], shoulder_center[1] - NECK_LENGTH - HEAD_HEIGHT // 2)
    
    @staticmethod
    def _draw_face_features(
        frame: np.ndarray, 
        head_center: Tuple[int, int],
        color: Tuple[int, int, int] = REFERENCE_COLOR
    ) -> None:
        """Draw simplified face features (eyes, eyebrows, mouth)."""
        cx, cy = head_center
        
        # Eyes
        eye_y = cy - HEAD_HEIGHT // 8
        left_eye_x = cx - HEAD_WIDTH // 5
        right_eye_x = cx + HEAD_WIDTH // 5
        cv2.circle(frame, (left_eye_x, eye_y), 3, color, -1)
        cv2.circle(frame, (right_eye_x, eye_y), 3, color, -1)
        
        # Eyebrows (short arcs above eyes)
        eyebrow_y = eye_y - 8
        cv2.line(frame, (left_eye_x - 8, eyebrow_y), (left_eye_x + 8, eyebrow_y), color, 2)
        cv2.line(frame, (right_eye_x - 8, eyebrow_y), (right_eye_x + 8, eyebrow_y), color, 2)
        
        # Mouth (small arc)
        mouth_y = cy + HEAD_HEIGHT // 4
        cv2.ellipse(frame, (cx, mouth_y), (10, 4), 0, 10, 170, color, 1)
    
    @staticmethod
    def get_reference_positions(center_x: int = CENTER_X, center_y: int = CENTER_Y) -> Dict[str, Tuple[int, int]]:
        """
        Get reference positions for all body parts.
        Used as fallback when MediaPipe data is missing.
        
        Returns:
            Dict mapping part names to (x, y) positions
        """
        left_shoulder = (center_x - REFERENCE_SHOULDER_WIDTH // 2, center_y)
        right_shoulder = (center_x + REFERENCE_SHOULDER_WIDTH // 2, center_y)
        
        # Default arm positions (slightly down and out)
        left_elbow = (left_shoulder[0] - 20, left_shoulder[1] + UPPER_ARM_LENGTH - 20)
        left_wrist = (left_elbow[0] - 15, left_elbow[1] + LOWER_ARM_LENGTH - 15)
        
        right_elbow = (right_shoulder[0] + 20, right_shoulder[1] + UPPER_ARM_LENGTH - 20)
        right_wrist = (right_elbow[0] + 15, right_elbow[1] + LOWER_ARM_LENGTH - 15)
        
        head_center = (center_x, center_y - NECK_LENGTH - HEAD_HEIGHT // 2)
        
        return {
            'left_shoulder': left_shoulder,
            'right_shoulder': right_shoulder,
            'left_elbow': left_elbow,
            'right_elbow': right_elbow,
            'left_wrist': left_wrist,
            'right_wrist': right_wrist,
            'head_center': head_center,
            'neck_top': (center_x, center_y - NECK_LENGTH),
            'neck_bottom': (center_x, center_y),
        }


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
    def normalize_to_reference(
        landmarks: Dict[str, np.ndarray],
        target_shoulder_width: int = REFERENCE_SHOULDER_WIDTH,
        target_center: Tuple[int, int] = (CENTER_X, CENTER_Y),
        last_frame_landmarks: Optional[Dict[str, np.ndarray]] = None
    ) -> Dict[str, np.ndarray]:
        """
        Normalize landmarks to reference body proportions.
        
        This ensures:
        1. Consistent shoulder width (100px) regardless of video zoom
        2. Body centered in frame
        3. Missing parts use fallback (last frame or reference default)
        
        Args:
            landmarks: Dict with 'pose', 'left_hand', 'right_hand'
            target_shoulder_width: Target width for shoulders (default 100px)
            target_center: Target position for shoulder center
            last_frame_landmarks: Previous frame's landmarks for fallback
            
        Returns:
            Normalized landmarks in pixel coordinates
        """
        result = {}
        scale_factor = 1.0
        shoulder_center = np.array(target_center, dtype=np.float32)
        
        # Get reference positions for fallback
        ref_positions = ReferenceBody.get_reference_positions(target_center[0], target_center[1])
        
        if 'pose' in landmarks and landmarks['pose'] is not None:
            pose = landmarks['pose'].copy()
            
            # Detect shoulder width from landmarks
            # For 6-point pose: indices 0, 1 are shoulders
            # For 33-point pose: indices 11, 12 are shoulders
            if len(pose) >= 2:
                if len(pose) <= 6:
                    # 6-point pose: 0=left shoulder, 1=right shoulder
                    left_shoulder = pose[0][:2]
                    right_shoulder = pose[1][:2]
                else:
                    # 33-point pose: 11=left shoulder, 12=right shoulder
                    left_shoulder = pose[11][:2]
                    right_shoulder = pose[12][:2]
                
                # Calculate detected shoulder width
                detected_width = np.linalg.norm(right_shoulder - left_shoulder)
                
                if detected_width > 10:  # Valid detection
                    # Calculate scale factor to normalize to reference width
                    scale_factor = target_shoulder_width / detected_width
                    
                    # Clamp scale factor to prevent extreme scaling
                    # Min 0.3 (shoulders were huge), Max 3.0 (shoulders were tiny)
                    scale_factor = max(0.3, min(3.0, scale_factor))
                    
                    # Calculate current shoulder center
                    current_center = (left_shoulder + right_shoulder) / 2
                    shoulder_center = current_center
            
            # Apply normalization: translate to origin, scale, translate to target
            for i in range(len(pose)):
                # Translate relative to shoulder center
                point = pose[i][:2] - shoulder_center
                # Scale to reference proportions
                point = point * scale_factor
                # Translate to target center
                point = point + np.array(target_center, dtype=np.float32)
                pose[i, 0] = point[0]
                pose[i, 1] = point[1]
            
            result['pose'] = pose
        else:
            # No pose data - use fallback
            if last_frame_landmarks and 'pose' in last_frame_landmarks:
                result['pose'] = last_frame_landmarks['pose'].copy()
            # Otherwise, no pose data available
        
        # Normalize hands using same scale factor
        for hand_key, ref_wrist_key in [('left_hand', 'left_wrist'), ('right_hand', 'right_wrist')]:
            is_left = (hand_key == 'left_hand')
            wrist_idx = 4 if is_left else 5  # For 6-point pose
            
            # Get wrist position from normalized pose (needed for fallback hand)
            wrist_pos = None
            if 'pose' in result and result['pose'] is not None:
                pose = result['pose']
                if len(pose) <= 6:
                    wrist_idx = 4 if is_left else 5
                else:
                    wrist_idx = 15 if is_left else 16
                
                if wrist_idx < len(pose):
                    wrist_pos = pose[wrist_idx][:2].copy()
            
            if wrist_pos is None:
                wrist_pos = np.array(ref_positions[ref_wrist_key], dtype=np.float32)
            
            # Check if we have valid hand data
            has_valid_hand = False
            if hand_key in landmarks and landmarks[hand_key] is not None:
                hand = landmarks[hand_key].copy()
                hand_max = np.abs(hand[:, :2]).max()
                has_valid_hand = (hand_max > 0.001)
            
            if has_valid_hand:
                # Valid hand data - normalize and attach to wrist
                hand_wrist = hand[0][:2].copy()
                
                for i in range(len(hand)):
                    offset = hand[i][:2] - hand_wrist
                    offset = offset * scale_factor
                    new_pos = offset + wrist_pos
                    hand[i, 0] = new_pos[0]
                    hand[i, 1] = new_pos[1]
                
                result[hand_key] = hand
            else:
                # Invalid/missing hand - use NEUTRAL REST position
                # CRITICAL: Do NOT use previous frame's hand shape!
                # That would carry forward a sign and could corrupt meaning.
                # Always use linguistically unmarked neutral rest position.
                result[hand_key] = generate_neutral_hand(wrist_pos, is_left=is_left)
        
        return result

    @staticmethod
    def validate_landmarks(
        landmarks: Dict[str, np.ndarray],
        frame_width: int = FRAME_WIDTH,
        frame_height: int = FRAME_HEIGHT
    ) -> Dict[str, List[str]]:
        """
        Validate landmarks for errors (out of bounds, missing connectors, bad proportions).
        
        Returns:
            Dict with 'errors' list and 'warnings' list
        """
        errors = []
        warnings = []
        
        # Check bounds
        for key in ['pose', 'left_hand', 'right_hand']:
            if key in landmarks and landmarks[key] is not None:
                for i, point in enumerate(landmarks[key]):
                    x, y = point[:2]
                    if x < BOUNDS_MARGIN or x > frame_width - BOUNDS_MARGIN:
                        warnings.append(f"{key}[{i}] X out of bounds: {x:.1f}")
                    if y < BOUNDS_MARGIN or y > frame_height - BOUNDS_MARGIN:
                        warnings.append(f"{key}[{i}] Y out of bounds: {y:.1f}")
        
        # Check pose proportions (if we have 6-point pose)
        if 'pose' in landmarks and landmarks['pose'] is not None:
            pose = landmarks['pose']
            if len(pose) >= 6:
                # Check shoulder width
                shoulder_width = np.linalg.norm(pose[1][:2] - pose[0][:2])
                expected = REFERENCE_SHOULDER_WIDTH
                if abs(shoulder_width - expected) / expected > PROPORTION_TOLERANCE:
                    warnings.append(f"Shoulder width {shoulder_width:.1f} deviates from {expected}")
                
                # Check arm lengths (left: 0->2->4, right: 1->3->5)
                for side, indices in [('left', [0, 2, 4]), ('right', [1, 3, 5])]:
                    upper_arm = np.linalg.norm(pose[indices[1]][:2] - pose[indices[0]][:2])
                    lower_arm = np.linalg.norm(pose[indices[2]][:2] - pose[indices[1]][:2])
                    
                    if upper_arm > 0 and lower_arm > 0:
                        ratio = upper_arm / lower_arm
                        expected_ratio = UPPER_ARM_LENGTH / LOWER_ARM_LENGTH  # 55/45 ≈ 1.22
                        if abs(ratio - expected_ratio) / expected_ratio > PROPORTION_TOLERANCE:
                            warnings.append(f"{side} arm ratio {ratio:.2f} deviates from {expected_ratio:.2f}")
        
        return {'errors': errors, 'warnings': warnings}


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
