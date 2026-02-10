#!/usr/bin/env python3
"""
Skeleton Renderer - Reference Body Based
=========================================

DESIGN PRINCIPLE:
- Reference body provides FIXED PROPORTIONS (never scaled)
- Landmarks provide POSITIONS/ANGLES
- We MOVE reference body parts to match detected angles
- Missing parts use reference body defaults
- Out-of-bounds or biologically impossible points are flagged

This is simpler and more robust than scaling everything.

Usage:
    from skeleton_renderer import SkeletonRenderer
    
    renderer = SkeletonRenderer()
    frame = renderer.draw(landmarks)
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional, List
import math


# =============================================================================
# REFERENCE BODY CONSTANTS (FIXED - NEVER SCALED)
# =============================================================================

# Frame
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CENTER_X = 320
CENTER_Y = 200  # Shoulder line position

# Fixed proportions (biological reference)
SHOULDER_WIDTH = 100       # Distance between shoulders
UPPER_ARM = 55             # Shoulder to elbow
LOWER_ARM = 45             # Elbow to wrist
NECK_LENGTH = 35           # Shoulder center to chin
HEAD_WIDTH = 50
HEAD_HEIGHT = 70

# Hand proportions (fixed)
PALM_LENGTH = 20           # Wrist to MCP line
PALM_WIDTH = 24            # Width across knuckles (MCP line)

FINGER_LENGTHS = {
    'thumb':  [8, 6, 5, 4],       # CMC→MCP→IP→TIP
    'index':  [0, 12, 8, 6],      # MCP→PIP→DIP→TIP (0 = palm connection)
    'middle': [0, 14, 9, 7],
    'ring':   [0, 12, 8, 6],
    'pinky':  [0, 10, 6, 5],
}

# Finger base positions (horizontal offset from palm center at MCP line)
# Distributed across palm width like real hand anatomy
FINGER_BASE_OFFSETS = {
    'thumb':  -14,   # Offset from wrist (outside palm)
    'index':  -9,    # Left of center
    'middle': 0,     # Center
    'ring':   9,     # Right of center
    'pinky':  14,    # Far right
}

# Finger spread angles (radians from palm centerline, pointing down)
# Biologically accurate for relaxed neutral hand position
FINGER_ANGLES = {
    'thumb':  -0.70,   # ~40 degrees abducted (natural thumb splay)
    'index':  -0.12,   # ~7 degrees from center
    'middle': 0.0,     # Center reference
    'ring':   0.12,    # ~7 degrees from center
    'pinky':  0.28,    # ~16 degrees (fingers naturally splay more)
}

# Colors (BGR)
COLOR_BODY = (0, 255, 0)          # Green (reference body)
COLOR_LEFT_ARM = (0, 94, 213)     # Wong Vermillion (left arm)
COLOR_RIGHT_ARM = (233, 180, 86)  # Wong Sky Blue (right arm)
COLOR_LEFT_HAND = (255, 100, 0)   # Blue-ish
COLOR_RIGHT_HAND = (0, 100, 255)  # Red-ish
COLOR_HEAD = (100, 180, 100)      # Light green
COLOR_REFERENCE = (60, 60, 60)    # Dark grey
COLOR_JOINT = (0, 255, 255)       # Yellow
COLOR_ERROR = (0, 165, 255)       # Orange
COLOR_MISSING_SEGMENT = (120, 120, 120)  # Dim gray
COLOR_MISSING_DOT = (180, 180, 180)      # Light gray

# Finger colors
FINGER_COLORS = {
    # Wong palette (colorblind-safe) in BGR
    'thumb':  (0, 159, 230),   # Orange
    'index':  (233, 180, 86),  # Sky blue
    'middle': (115, 158, 0),   # Bluish green
    'ring':   (0, 94, 213),    # Vermillion
    'pinky':  (178, 114, 0),   # Blue
}

# Biological limits (radians)
ELBOW_MIN = 0.0           # Straight arm
ELBOW_MAX = 2.6           # ~150 degrees flexion

# Re-export for compatibility with skeleton_drawer imports
REFERENCE_SHOULDER_WIDTH = SHOULDER_WIDTH


class SkeletonRenderer:
    """
    Render skeleton using FIXED reference body proportions.
    
    The reference body is the "ground truth" for sizes.
    Landmarks only tell us WHERE to position these fixed-size parts.
    """
    
    def __init__(self, width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT):
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2  # Match reference body center
        self.current_scale = 1.0
        
        # Reference positions (defaults when no data)
        self.ref_positions = self._compute_reference_positions()
    
    def _compute_reference_positions(self) -> Dict[str, Tuple[int, int]]:
        """Compute default reference body positions."""
        cx, cy = self.center_x, self.center_y
        
        return {
            'left_shoulder': (cx - SHOULDER_WIDTH // 2, cy),
            'right_shoulder': (cx + SHOULDER_WIDTH // 2, cy),
            'left_elbow': (cx - SHOULDER_WIDTH // 2 - 20, cy + UPPER_ARM - 10),
            'right_elbow': (cx + SHOULDER_WIDTH // 2 + 20, cy + UPPER_ARM - 10),
            'left_wrist': (cx - SHOULDER_WIDTH // 2 - 35, cy + UPPER_ARM + LOWER_ARM - 20),
            'right_wrist': (cx + SHOULDER_WIDTH // 2 + 35, cy + UPPER_ARM + LOWER_ARM - 20),
            'head_center': (cx, cy - NECK_LENGTH - HEAD_HEIGHT // 2),
            'neck_top': (cx, cy - NECK_LENGTH),
        }
    
    def draw(self, landmarks: Dict[str, np.ndarray], show_reference: bool = True) -> np.ndarray:
        """
        Draw skeleton on blank frame using reference body proportions.
        
        Args:
            landmarks: Dict with 'pose', 'left_hand', 'right_hand' arrays
            show_reference: Whether to show reference body outline
            
        Returns:
            Frame with skeleton drawn
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Extract key positions from landmarks
        positions = self._extract_positions(landmarks)
        
        # Draw reference body outline first (background)
        if show_reference:
            self._draw_reference_outline(frame)
        
        # Draw shoulder line (connecting shoulders)
        left_shoulder = positions.get('left_shoulder')
        right_shoulder = positions.get('right_shoulder')
        if left_shoulder and right_shoulder:
            cv2.line(frame, left_shoulder, right_shoulder, COLOR_BODY, 2, cv2.LINE_AA)
        
        # Draw head/neck
        self._draw_head_neck(frame, positions)
        
        # Draw arms (fixed length, positioned by landmarks)
        self._draw_arm(frame, positions, 'left')
        self._draw_arm(frame, positions, 'right')
        
        # Draw hands
        self._draw_hand(
            frame,
            landmarks.get('left_hand'),
            positions.get('left_wrist'),
            'left',
            positions.get('left_wrist_angle'),
        )
        self._draw_hand(
            frame,
            landmarks.get('right_hand'),
            positions.get('right_wrist'),
            'right',
            positions.get('right_wrist_angle'),
        )
        
        return frame
    
    def _extract_positions(self, landmarks: Dict[str, np.ndarray]) -> Dict[str, Tuple[int, int]]:
        """
        Extract key joint positions from landmarks.
        Falls back to reference positions if missing/invalid.
        """
        positions = {}
        
        pose = landmarks.get('pose')
        if pose is not None and len(pose) >= 6:
            # 6-point pose: 0=left_shoulder, 1=right_shoulder, 2=left_elbow,
            #               3=right_elbow, 4=left_wrist, 5=right_wrist
            
            # Keep shoulders fixed to reference body
            positions['left_shoulder'] = self.ref_positions['left_shoulder']
            positions['right_shoulder'] = self.ref_positions['right_shoulder']
            positions['shoulder_center'] = (self.center_x, self.center_y)
            
            # Raw detected points (for angle extraction only)
            left_shoulder_raw = self._to_point(pose[0])
            right_shoulder_raw = self._to_point(pose[1])
            left_elbow_raw = self._to_point(pose[2])
            right_elbow_raw = self._to_point(pose[3])
            left_wrist_raw = self._to_point(pose[4])
            right_wrist_raw = self._to_point(pose[5])

            # Scale factor based on detected shoulder width (for proportion checks)
            scale = 1.0
            if left_shoulder_raw and right_shoulder_raw:
                detected_width = self._distance(left_shoulder_raw, right_shoulder_raw)
                if detected_width > 1.0:
                    scale = detected_width / SHOULDER_WIDTH
            scale = max(0.3, min(3.0, scale))
            self.current_scale = scale

            expected_upper = UPPER_ARM * scale
            expected_lower = LOWER_ARM * scale
            
            # Elbows - follow detected angles from raw pose, fixed segment length
            if left_shoulder_raw and left_elbow_raw and self._is_reasonable_length(
                self._distance(left_shoulder_raw, left_elbow_raw),
                expected_upper,
            ):
                left_angle = self._angle_to(left_shoulder_raw, left_elbow_raw)
                positions['left_elbow'] = self._point_at_angle(
                    positions['left_shoulder'],
                    left_angle,
                    UPPER_ARM,
                )
            else:
                positions['left_elbow'] = self.ref_positions['left_elbow']
            
            if right_shoulder_raw and right_elbow_raw and self._is_reasonable_length(
                self._distance(right_shoulder_raw, right_elbow_raw),
                expected_upper,
            ):
                right_angle = self._angle_to(right_shoulder_raw, right_elbow_raw)
                positions['right_elbow'] = self._point_at_angle(
                    positions['right_shoulder'],
                    right_angle,
                    UPPER_ARM,
                )
            else:
                positions['right_elbow'] = self.ref_positions['right_elbow']
            
            # Wrists - follow detected angles from raw pose, fixed segment length
            if left_elbow_raw and left_wrist_raw and self._is_reasonable_length(
                self._distance(left_elbow_raw, left_wrist_raw),
                expected_lower,
            ):
                left_wrist_angle = self._angle_to(left_elbow_raw, left_wrist_raw)
                positions['left_wrist_angle'] = left_wrist_angle
                positions['left_wrist'] = self._point_at_angle(
                    positions['left_elbow'],
                    left_wrist_angle,
                    LOWER_ARM,
                )
            else:
                positions['left_wrist'] = self.ref_positions['left_wrist']
            
            if right_elbow_raw and right_wrist_raw and self._is_reasonable_length(
                self._distance(right_elbow_raw, right_wrist_raw),
                expected_lower,
            ):
                right_wrist_angle = self._angle_to(right_elbow_raw, right_wrist_raw)
                positions['right_wrist_angle'] = right_wrist_angle
                positions['right_wrist'] = self._point_at_angle(
                    positions['right_elbow'],
                    right_wrist_angle,
                    LOWER_ARM,
                )
            else:
                positions['right_wrist'] = self.ref_positions['right_wrist']

            # Face center for dynamic head/neck (optional)
            face = landmarks.get('face')
            if face is not None and len(face) > 0:
                face_points = []
                for point in face:
                    pt = self._to_point(point)
                    if pt:
                        face_points.append(pt)
                if face_points:
                    avg_x = int(sum(p[0] for p in face_points) / len(face_points))
                    avg_y = int(sum(p[1] for p in face_points) / len(face_points))
                    positions['face_center'] = (avg_x, avg_y)
        else:
            # No pose data - use all reference positions
            positions.update(self.ref_positions)
            positions['shoulder_center'] = (self.center_x, self.center_y)
        
        return positions
    
    def _to_point(self, arr: np.ndarray) -> Optional[Tuple[int, int]]:
        """Convert array to (x, y) tuple if valid."""
        if arr is None:
            return None
        x, y = int(arr[0]), int(arr[1])
        # Check for zeros (invalid detection) and bounds
        if (x == 0 and y == 0) or not self._in_bounds(x, y):
            return None
        return (x, y)
    
    def _in_bounds(self, x: int, y: int, margin: int = 10) -> bool:
        """Check if point is within frame bounds."""
        return margin <= x < self.width - margin and margin <= y < self.height - margin
    
    def _distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Euclidean distance between two points."""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

    def _is_reasonable_length(
        self,
        length: float,
        expected: float,
        min_ratio: float = 0.35,
        max_ratio: float = 2.0,
    ) -> bool:
        if expected <= 0.0:
            return False
        return (expected * min_ratio) <= length <= (expected * max_ratio)
    
    def _angle_to(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Angle from p1 to p2 in radians."""
        return math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    
    def _point_at_angle(self, origin: Tuple[int, int], angle: float, distance: float) -> Tuple[int, int]:
        """Get point at given angle and distance from origin."""
        x = origin[0] + distance * math.cos(angle)
        y = origin[1] + distance * math.sin(angle)
        return (int(x), int(y))
    
    def _draw_reference_outline(self, frame: np.ndarray) -> None:
        """Draw faint reference body outline."""
        ref = self.ref_positions
        color = COLOR_REFERENCE
        
        # Head
        head = ref['head_center']
        cv2.ellipse(frame, head, (HEAD_WIDTH // 2, HEAD_HEIGHT // 2), 0, 0, 360, color, 1)
        
        # Neck
        cv2.line(frame, ref['neck_top'], (self.center_x, self.center_y), color, 1)
        
        # Shoulders
        cv2.line(frame, ref['left_shoulder'], ref['right_shoulder'], color, 1)
    
    def _draw_head_neck(self, frame: np.ndarray, positions: Dict) -> None:
        """Draw head and neck."""
        shoulder_center = positions.get('shoulder_center', (self.center_x, self.center_y))

        face_center = positions.get('face_center')
        if face_center:
            # Clamp head x near shoulders to avoid large offsets
            max_dx = SHOULDER_WIDTH // 2
            head_x = max(shoulder_center[0] - max_dx, min(face_center[0], shoulder_center[0] + max_dx))
            head_center = (head_x, face_center[1])

            desired_neck_top_y = head_center[1] + (HEAD_HEIGHT // 2)
            neck_top_y = min(desired_neck_top_y, shoulder_center[1] - 5)
            neck_top = (head_x, neck_top_y)
        else:
            # Fallback to fixed neck length
            neck_top = (shoulder_center[0], shoulder_center[1] - NECK_LENGTH)
            head_center = (shoulder_center[0], neck_top[1] - HEAD_HEIGHT // 2)
        
        # Draw
        cv2.line(frame, shoulder_center, neck_top, COLOR_HEAD, 2, cv2.LINE_AA)
        cv2.ellipse(frame, head_center, (HEAD_WIDTH // 2, HEAD_HEIGHT // 2), 
                   0, 0, 360, COLOR_HEAD, 2, cv2.LINE_AA)
        
        # Simple face
        self._draw_simple_face(frame, head_center)
    
    def _draw_simple_face(self, frame: np.ndarray, center: Tuple[int, int]) -> None:
        """Draw simplified face features."""
        cx, cy = center
        color = COLOR_HEAD
        
        # Eyes
        eye_y = cy - 5
        cv2.circle(frame, (cx - 10, eye_y), 3, color, -1)
        cv2.circle(frame, (cx + 10, eye_y), 3, color, -1)
        
        # Mouth
        cv2.ellipse(frame, (cx, cy + 15), (8, 4), 0, 10, 170, color, 1)
    
    def _draw_arm(self, frame: np.ndarray, positions: Dict, side: str) -> None:
        """Draw arm with fixed proportions at detected angles."""
        shoulder = positions.get(f'{side}_shoulder')
        elbow = positions.get(f'{side}_elbow')
        wrist = positions.get(f'{side}_wrist')
        
        if not all([shoulder, elbow, wrist]):
            return
        
        arm_color = COLOR_LEFT_ARM if side == 'left' else COLOR_RIGHT_ARM

        # Draw upper arm (shoulder → elbow)
        cv2.line(frame, shoulder, elbow, arm_color, 2, cv2.LINE_AA)
        
        # Draw lower arm (elbow → wrist)
        cv2.line(frame, elbow, wrist, arm_color, 2, cv2.LINE_AA)
        
        # Draw joints
        for pt in [shoulder, elbow, wrist]:
            cv2.circle(frame, pt, 4, COLOR_JOINT, -1, cv2.LINE_AA)
    
    def _draw_hand(
        self,
        frame: np.ndarray,
        hand_data: Optional[np.ndarray],
        wrist_pos: Optional[Tuple[int, int]],
        side: str,
        wrist_angle: Optional[float] = None,
    ) -> None:
        """Draw hand with fixed proportions."""
        if wrist_pos is None:
            return
        
        is_left = (side == 'left')
        base_color = COLOR_LEFT_HAND if is_left else COLOR_RIGHT_HAND
        mirror = -1 if is_left else 1
        
        # Check if we have valid hand data
        has_valid_hand = False
        if hand_data is not None:
            max_val = np.abs(hand_data[:, :2]).max()
            wrist_val = np.abs(hand_data[0, :2]).max() if len(hand_data) > 0 else 0.0
            valid_points = int(np.sum(np.abs(hand_data[:, :2]).max(axis=1) > 1.0))
            # Allow partial hand data; still require a valid wrist
            has_valid_hand = (max_val > 1.0) and (wrist_val > 1.0) and (valid_points >= 3)
        
        if has_valid_hand:
            # Draw actual hand data with fixed-size fingers
            self._draw_hand_from_data(frame, hand_data, wrist_pos, side)
        else:
            # Draw neutral reference hand
            self._draw_neutral_hand(frame, wrist_pos, side, wrist_angle, use_missing_style=True)
    
    def _draw_hand_from_data(self, frame: np.ndarray, hand_data: np.ndarray,
                             wrist_pos: Tuple[int, int], side: str) -> None:
        """Draw hand using actual landmark data with validation."""
        is_left = (side == 'left')
        
        # Get wrist from data
        data_wrist = hand_data[0][:2]
        if np.abs(data_wrist).max() <= 1.0:
            # Missing wrist data - fallback to neutral hand
            self._draw_neutral_hand(frame, wrist_pos, side)
            return
        
        # Calculate offset to align with our wrist position
        offset_x = wrist_pos[0] - data_wrist[0]
        offset_y = wrist_pos[1] - data_wrist[1]
        
        # Maximum reasonable hand span (wrist to fingertip)
        max_hand_span = 150 * self.current_scale  # pixels
        
        # Finger landmark indices (MediaPipe hand model)
        finger_indices = {
            'thumb':  [0, 1, 2, 3, 4],
            'index':  [0, 5, 6, 7, 8],
            'middle': [0, 9, 10, 11, 12],
            'ring':   [0, 13, 14, 15, 16],
            'pinky':  [0, 17, 18, 19, 20],
        }
        
        def hand_point(idx: int) -> Tuple[int, int]:
            return (
                int(hand_data[idx][0] + offset_x),
                int(hand_data[idx][1] + offset_y),
            )
        
        def expected_lengths(name: str) -> List[float]:
            if name == 'thumb':
                return FINGER_LENGTHS[name]
            return [PALM_LENGTH] + FINGER_LENGTHS[name][1:]
        
        # Draw palm connectors (wrist -> MCPs, plus MCP chain)
        mcp_indices = [5, 9, 13, 17]
        mcp_points = []
        for idx in mcp_indices:
            if idx < len(hand_data):
                pt = hand_point(idx)
                if self._in_bounds(pt[0], pt[1]):
                    mcp_points.append(pt)
                    cv2.line(frame, wrist_pos, pt, COLOR_BODY, 1, cv2.LINE_AA)
        for i in range(len(mcp_points) - 1):
            cv2.line(frame, mcp_points[i], mcp_points[i + 1], COLOR_BODY, 1, cv2.LINE_AA)

        # Palm width validation (index MCP to pinky MCP)
        if len(mcp_points) >= 2:
            palm_span = self._distance(mcp_points[0], mcp_points[-1])
            expected_palm = PALM_WIDTH * self.current_scale
            if not self._is_reasonable_length(palm_span, expected_palm, min_ratio=0.5, max_ratio=2.0):
                self._draw_neutral_hand(frame, wrist_pos, side)
                return
        
        segments_drawn = 0
        for finger_name, indices in finger_indices.items():
            color = FINGER_COLORS[finger_name]
            lengths = expected_lengths(finger_name)
            
            # Collect finger segments with validation
            prev_valid = True
            finger_segments_drawn = 0
            finger_incomplete = False
            segments = []
            for i in range(len(indices) - 1):
                idx1, idx2 = indices[i], indices[i + 1]
                
                if not prev_valid:
                    break
                
                if idx1 < len(hand_data) and idx2 < len(hand_data):
                    pt1 = hand_point(idx1)
                    pt2 = hand_point(idx2)
                    
                    # Validate points are in bounds
                    if not (self._in_bounds(pt1[0], pt1[1]) and self._in_bounds(pt2[0], pt2[1])):
                        prev_valid = False
                        finger_incomplete = True
                        break
                    
                    # Validate points are reasonable distance from wrist (no floating points)
                    dist1 = self._distance(wrist_pos, pt1)
                    dist2 = self._distance(wrist_pos, pt2)
                    if dist1 > max_hand_span or dist2 > max_hand_span:
                        prev_valid = False
                        finger_incomplete = True
                        break
                    
                    # Validate segment length against expected proportions
                    expected = lengths[i] if i < len(lengths) else 0.0
                    if expected > 0.0:
                        seg_len = self._distance(pt1, pt2)
                        min_len = expected * 0.35
                        max_len = expected * 2.0
                        if not (min_len <= seg_len <= max_len):
                            prev_valid = False
                            finger_incomplete = True
                            break

                        segments.append((pt1, pt2))
                        segments_drawn += 1
                        finger_segments_drawn += 1

            draw_color = COLOR_MISSING_SEGMENT if finger_incomplete else color
            for pt1, pt2 in segments:
                cv2.line(frame, pt1, pt2, draw_color, 2, cv2.LINE_AA)
            
            # Draw fingertip dot with validation
            tip_idx = indices[-1]
            if tip_idx < len(hand_data):
                tip = (int(hand_data[tip_idx][0] + offset_x),
                       int(hand_data[tip_idx][1] + offset_y))
                dist = math.sqrt((tip[0] - wrist_pos[0])**2 + (tip[1] - wrist_pos[1])**2)
                
                if finger_segments_drawn > 0 and self._in_bounds(tip[0], tip[1]) and dist <= max_hand_span:
                    tip_color = COLOR_MISSING_DOT if finger_incomplete else color
                    cv2.circle(frame, tip, 3, tip_color, -1, cv2.LINE_AA)

        if segments_drawn == 0:
            self._draw_neutral_hand(frame, wrist_pos, side, use_missing_style=True)
    
    def _draw_neutral_hand(
        self,
        frame: np.ndarray,
        wrist_pos: Tuple[int, int],
        side: str,
        wrist_angle: Optional[float] = None,
        use_missing_style: bool = False,
    ) -> None:
        """Draw neutral/rest hand when no data available with proper palm structure."""
        is_left = (side == 'left')
        mirror = -1 if is_left else 1
        
        wx, wy = wrist_pos
        
        # Validate wrist position is in bounds
        if not self._in_bounds(wx, wy):
            return
        
        # Draw palm structure: wrist to distributed finger bases
        base_down_angle = math.pi / 2
        rotation = (wrist_angle - base_down_angle) if wrist_angle is not None else 0.0
        cos_r = math.cos(rotation)
        sin_r = math.sin(rotation)
        palm_bases = {}
        for finger_name, x_offset in FINGER_BASE_OFFSETS.items():
            if finger_name == 'thumb':
                # Thumb base is at wrist level, offset to side
                dx, dy = (mirror * abs(x_offset), 5)
            else:
                # Other fingers: base at MCP line (knuckles), horizontally distributed
                dx, dy = (mirror * x_offset, PALM_LENGTH)

            # Rotate base offset to align with wrist direction
            rot_x = int(dx * cos_r - dy * sin_r)
            rot_y = int(dx * sin_r + dy * cos_r)
            base = (wx + rot_x, wy + rot_y)
            
            palm_bases[finger_name] = base
            
            # Draw connector from wrist to finger base (palm structure)
            if self._in_bounds(base[0], base[1]):
                cv2.line(frame, (wx, wy), base, COLOR_BODY, 1, cv2.LINE_AA)
        
        # Draw each finger from its base position
        for finger_name, base_angle in FINGER_ANGLES.items():
            color = COLOR_MISSING_SEGMENT if use_missing_style else FINGER_COLORS[finger_name]
            lengths = FINGER_LENGTHS[finger_name]
            start = palm_bases[finger_name]
            
            # Validate start point
            if not self._in_bounds(start[0], start[1]):
                continue
            
            # Mirror angle for left hand
            angle = base_angle * mirror + (wrist_angle if wrist_angle is not None else base_down_angle)
            
            # Draw finger segments with validation
            current = start
            prev_valid = True
            
            for i, seg_length in enumerate(lengths):
                if seg_length == 0:
                    continue
                
                if not prev_valid:  # Skip if previous segment went out of bounds
                    break
                    
                # Slight angle variation per segment (natural curl)
                seg_angle = angle + 0.05 * i
                
                next_pt = self._point_at_angle(current, seg_angle, seg_length)
                
                # Validate point is reasonable distance from wrist (no floating points)
                dist_from_wrist = math.sqrt((next_pt[0] - wx)**2 + (next_pt[1] - wy)**2)
                max_finger_reach = PALM_LENGTH + sum(lengths)  # Wrist to fingertip
                
                if self._in_bounds(next_pt[0], next_pt[1]) and dist_from_wrist <= max_finger_reach * 1.5:
                    cv2.line(frame, current, next_pt, color, 2, cv2.LINE_AA)
                    current = next_pt
                else:
                    prev_valid = False
                    break
            
            # Fingertip dot (only if last segment was valid)
            if prev_valid and self._in_bounds(current[0], current[1]):
                dot_color = COLOR_MISSING_DOT if use_missing_style else color
                cv2.circle(frame, current, 2, dot_color, -1)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def render_skeleton(landmarks: Dict[str, np.ndarray], 
                    width: int = 640, height: int = 480) -> np.ndarray:
    """
    Render skeleton with fixed reference body proportions.
    
    Args:
        landmarks: Dict with 'pose', 'left_hand', 'right_hand'
        width, height: Frame dimensions
        
    Returns:
        Frame with skeleton rendered
    """
    renderer = SkeletonRenderer(width, height)
    return renderer.draw(landmarks)


# =============================================================================
# COMPATIBILITY LAYER (for skeleton_drawer.py replacement)
# =============================================================================

class ReferenceBody:
    """Compatibility: Draw reference body canvas."""
    
    SHOULDER_WIDTH = SHOULDER_WIDTH
    UPPER_ARM = UPPER_ARM
    LOWER_ARM = LOWER_ARM
    
    @staticmethod
    def draw_canvas(
        frame: np.ndarray,
        landmarks: np.ndarray = None,
        draw_head: bool = True,
    ) -> np.ndarray:
        """Draw reference body outline on frame."""
        renderer = SkeletonRenderer(frame.shape[1], frame.shape[0])
        renderer._draw_reference_outline(frame)
        if draw_head:
            renderer._draw_head_neck(frame, renderer.ref_positions)
        return frame


class SkeletonDrawerCompat:
    """
    Compatibility class to replace skeleton_drawer.SkeletonDrawer.
    
    Provides same interface but uses simple reference body approach.
    """
    
    # Colors for compatibility
    COLOR_POSE = COLOR_BODY
    COLOR_LEFT_HAND = COLOR_LEFT_HAND
    COLOR_RIGHT_HAND = COLOR_RIGHT_HAND
    COLOR_JOINT = COLOR_JOINT
    
    @staticmethod
    def normalize_to_reference(
        landmarks: np.ndarray,
        last_frame_landmarks: np.ndarray = None,
        center: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        """
        Convert landmarks to reference-body-aligned coordinates.
        
        SIMPLIFIED: Just center on shoulder midpoint, don't scale proportions.
        The renderer handles proper sizing.
        """
        if landmarks is None or len(landmarks) == 0:
            return landmarks
        
        # landmarks: [pose(6), left_hand(21), right_hand(21), face(4)] = 52 points
        # pose: left_shoulder(0), right_shoulder(1), ...
        
        if len(landmarks) < 6:
            return landmarks
        
        # Get shoulder center
        left_shoulder = landmarks[0][:2]
        right_shoulder = landmarks[1][:2]
        shoulder_center = (left_shoulder + right_shoulder) / 2
        
        # Calculate detected shoulder width
        detected_width = np.linalg.norm(right_shoulder - left_shoulder)
        
        # Scale factor to normalize to reference
        if detected_width > 1:
            scale = REFERENCE_SHOULDER_WIDTH / detected_width
        else:
            scale = 1.0
        
        # Clamp scale to reasonable range
        scale = max(0.3, min(3.0, scale))
        
        # Apply: center at (CENTER_X, CENTER_Y), scale to reference
        normalized = landmarks.copy()
        
        if center is None:
            center_x, center_y = CENTER_X, CENTER_Y
        else:
            center_x, center_y = center

        # Only transform non-zero data (zeros indicate missing/invalid data)
        # Check left hand (indices 6:27) - keep zeros if original is all zeros
        left_hand_valid = np.abs(landmarks[6:27, :2]).max() > 0.001 if len(landmarks) > 27 else True
        right_hand_valid = np.abs(landmarks[27:48, :2]).max() > 0.001 if len(landmarks) > 48 else True
        
        # Transform all points
        normalized[:, 0] = (normalized[:, 0] - shoulder_center[0]) * scale + center_x
        normalized[:, 1] = (normalized[:, 1] - shoulder_center[1]) * scale + center_y
        
        # Restore zeros for invalid hands (so _draw_hand can detect them)
        if not left_hand_valid and len(landmarks) > 27:
            normalized[6:27, :2] = 0.0
        if not right_hand_valid and len(landmarks) > 48:
            normalized[27:48, :2] = 0.0
        
        return normalized
    
    @staticmethod
    def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
        """Legacy method: Same as normalize_to_reference."""
        return SkeletonDrawerCompat.normalize_to_reference(landmarks)
    
    @staticmethod
    def draw_skeleton(frame: np.ndarray, landmarks: np.ndarray, 
                      lang: str = "ASL", show_joints: bool = True) -> np.ndarray:
        """
        Draw skeleton on frame using reference body proportions.
        """
        if landmarks is None or len(landmarks) == 0:
            return frame
        
        h, w = frame.shape[:2]
        renderer = SkeletonRenderer(w, h)
        
        # Convert flat landmarks array to dict format
        # Expected: pose(6) + left_hand(21) + right_hand(21) + face(4) = 52
        landmarks_dict = {}
        
        if len(landmarks) >= 6:
            landmarks_dict['pose'] = landmarks[:6]
        
        if len(landmarks) >= 27:  # 6 + 21
            landmarks_dict['left_hand'] = landmarks[6:27]
        
        if len(landmarks) >= 48:  # 6 + 21 + 21
            landmarks_dict['right_hand'] = landmarks[27:48]

        if len(landmarks) >= 52:  # 6 + 21 + 21 + 4
            landmarks_dict['face'] = landmarks[48:52]
        
        # Use renderer but draw on existing frame (not blank)
        positions = renderer._extract_positions(landmarks_dict)
        
        # Draw shoulder line (connecting shoulders)
        left_shoulder = positions.get('left_shoulder')
        right_shoulder = positions.get('right_shoulder')
        if left_shoulder and right_shoulder:
            cv2.line(frame, left_shoulder, right_shoulder, COLOR_BODY, 2, cv2.LINE_AA)
        
        # Draw head/neck
        renderer._draw_head_neck(frame, positions)
        
        # Draw arms
        renderer._draw_arm(frame, positions, 'left')
        renderer._draw_arm(frame, positions, 'right')
        
        # Draw hands
        renderer._draw_hand(
            frame,
            landmarks_dict.get('left_hand'),
            positions.get('left_wrist'),
            'left',
            positions.get('left_wrist_angle'),
        )
        renderer._draw_hand(
            frame,
            landmarks_dict.get('right_hand'),
            positions.get('right_wrist'),
            'right',
            positions.get('right_wrist_angle'),
        )
        
        return frame


def extract_landmarks_from_signature(signature: dict, 
                                     frame_size: tuple = (640, 480),
                                     frame_width: int = None,
                                     frame_height: int = None) -> List[np.ndarray]:
    """
    Extract all frames of landmarks from a signature file.
    
    Args:
        signature: Loaded signature dict with 'pose_data' key
        frame_size: (width, height) for scaling normalized coords
        frame_width, frame_height: Alternative way to specify size (for compatibility)
        
    Returns:
        List of landmark arrays, one per frame
        Each array: [pose(6), left_hand(21), right_hand(21), face(4)] = 52 points
    """
    # Handle alternate argument style
    if frame_width is not None and frame_height is not None:
        frame_size = (frame_width, frame_height)
    
    frames = signature.get('pose_data', signature.get('frames', []))
    width, height = frame_size
    
    result = []
    for frame in frames:
        landmarks = []
        
        # Pose (6 points): shoulders, elbows, wrists
        pose = frame.get('pose', [])
        if pose and len(pose) >= 6:
            for pt in pose[:6]:
                landmarks.append([pt[0] * width, pt[1] * height, pt[2] if len(pt) > 2 else 0])
        else:
            # Fallback: use zeros
            for _ in range(6):
                landmarks.append([0, 0, 0])
        
        # Left hand (21 points)
        left_hand = frame.get('left_hand', [])
        if left_hand and len(left_hand) == 21:
            for pt in left_hand:
                landmarks.append([pt[0] * width, pt[1] * height, pt[2] if len(pt) > 2 else 0])
        else:
            for _ in range(21):
                landmarks.append([0, 0, 0])
        
        # Right hand (21 points)
        right_hand = frame.get('right_hand', [])
        if right_hand and len(right_hand) == 21:
            for pt in right_hand:
                landmarks.append([pt[0] * width, pt[1] * height, pt[2] if len(pt) > 2 else 0])
        else:
            for _ in range(21):
                landmarks.append([0, 0, 0])
        
        # Face (4 points)
        face = frame.get('face', [])
        if face and len(face) >= 4:
            for pt in face[:4]:
                landmarks.append([pt[0] * width, pt[1] * height, pt[2] if len(pt) > 2 else 0])
        else:
            for _ in range(4):
                landmarks.append([0, 0, 0])
        
        result.append(np.array(landmarks))
    
    return result


def extract_landmarks_as_dicts(signature: dict,
                               frame_width: int = 640,
                               frame_height: int = 480) -> List[Dict[str, np.ndarray]]:
    """
    Extract landmarks as list of dicts (legacy format for test_skeleton_render).
    
    Returns:
        List of dicts, each with 'pose', 'left_hand', 'right_hand' as arrays
    """
    frames = signature.get('pose_data', signature.get('frames', []))
    
    def _scale(arr, fw, fh):
        result = np.array(arr, dtype=np.float32)
        result[:, 0] *= fw
        result[:, 1] *= fh
        return result
    
    result = []
    for frame in frames:
        landmarks = {}
        
        if 'pose' in frame and frame['pose']:
            landmarks['pose'] = _scale(frame['pose'], frame_width, frame_height)
        if 'left_hand' in frame and frame['left_hand']:
            landmarks['left_hand'] = _scale(frame['left_hand'], frame_width, frame_height)
        if 'right_hand' in frame and frame['right_hand']:
            landmarks['right_hand'] = _scale(frame['right_hand'], frame_width, frame_height)
        
        result.append(landmarks)
    
    return result


if __name__ == "__main__":
    # Test
    print("Skeleton Renderer - Reference Body Based")
    print("Use: from skeleton_renderer import SkeletonRenderer")
    print("Or:  from skeleton_renderer import SkeletonDrawerCompat as SkeletonDrawer")
