#!/usr/bin/env python3
"""
Reference Body - Canonical Coordinate System
=============================================

PURPOSE:
    Defines the STANDARD SCALE and POSITION for all skeleton visualizations.
    All signatures should be normalized to these proportions to ensure:
    1. Consistent body size across all signs
    2. Hands stay within frame bounds  
    3. Comparable visual appearance between ASL/BSL pairs

CRITICAL CONSTANTS (used by skeleton_drawer/debugger):
    SHOULDER_WIDTH = 100px  → Target shoulder span for normalization
    ARM_LENGTH = 100px      → Total arm length (shoulder to wrist)
    UPPER_ARM = 55px        → Shoulder to elbow (anatomically accurate)
    LOWER_ARM = 45px        → Elbow to wrist
    
    These define the TARGET coordinate space that signatures are scaled TO.

HOW IT WORKS:
    1. MediaPipe extracts landmarks in 0-1 normalized space
    2. skeleton_drawer scales these to pixel coordinates
    3. Reference body defines WHERE those pixels should land
    4. If signature's shoulder width = 0.3, and we want 100px:
       → scale factor = 100 / (0.3 * frame_width) 

INTEGRATION STATUS:
    ⚠️  skeleton_drawer.py  - Uses bounding box, NOT reference proportions
    ⚠️  skeleton_debugger.py - Uses bounding box, NOT reference proportions
    
    TODO: Update normalization to use SHOULDER_WIDTH constant as reference
    This will ensure all rendered skeletons have consistent proportions.

HAND PROPORTION NOTES:
    Hand size is intentionally larger (35px vs 17px palm width) for visibility.
    For v1.0 PoC, this is acceptable since skeleton_drawer uses actual
    MediaPipe data. For consistent avatar rendering, hands should also
    be scaled to match reference proportions.

Shows reference body with hands in 6 positions: neutral, up, down, left, right, chest.
Uses exact MediaPipe landmark structure: 33 pose + 21 per hand.
"""
import cv2
import numpy as np
import math

# Frame dimensions
WIDTH = 640
HEIGHT = 480

# Reference body proportions (normalized to shoulder_width = 1.0)
# Only upper body needed for sign language recognition
SHOULDER_WIDTH = 100  # pixels - the reference scale (compact)
ARM_LENGTH = 100      # shoulder to wrist (total)

# Anatomically accurate arm segment ratios:
# Upper arm (humerus) is slightly longer than forearm (radius/ulna)
# Forearm is ~83% of upper arm length → upper arm = 55%, forearm = 45% of total
UPPER_ARM = 55  # shoulder to elbow (55% of ARM_LENGTH)
LOWER_ARM = 45  # elbow to wrist (45% of ARM_LENGTH)

# Head dimensions - oval shape (industry standard for sign language visualization)
# Taller than wide to match natural face proportions
HEAD_WIDTH = 50   # horizontal diameter
HEAD_HEIGHT = 70  # vertical diameter

# Center of frame - positioned to allow movement in all directions
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2  # True center for balanced reach

# Drawing colors (BGR format)
BODY_COLOR = (0, 255, 0)        # Green - body outline
LEFT_ARM_COLOR = (0, 94, 213)   # Wong Vermillion
RIGHT_ARM_COLOR = (233, 180, 86)  # Wong Sky Blue
JOINT_COLOR = (0, 255, 255)     # Yellow - joints
NECK_COLOR = (0, 200, 0)        # Darker green - neck

# Finger colors (Wong palette, BGR)
FINGER_COLORS = {
    'thumb': (0, 159, 230),   # Orange
    'index': (233, 180, 86),  # Sky blue
    'middle': (115, 158, 0),  # Bluish green
    'ring': (0, 94, 213),     # Vermillion
    'pinky': (178, 114, 0),   # Blue
}

# Hand pose spread/curl limits (for demo only)
MIN_SPREAD = 0.7
MAX_SPREAD = 1.6
MIN_CURL = 0.0
MAX_CURL = 0.6

# ROM limits (degrees)
ELBOW_MIN_DEG = 10
ELBOW_MAX_DEG = 170

# Hand connections (21 landmarks per hand)
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
    # Palm connections (across MCP joints)
    (5, 9), (9, 13), (13, 17),
]


def _angle_between(v1, v2):
    """Return angle between two vectors in radians."""
    norm1 = math.hypot(v1[0], v1[1])
    norm2 = math.hypot(v2[0], v2[1])
    if norm1 == 0 or norm2 == 0:
        return 0.0
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    cosang = max(-1.0, min(1.0, dot / (norm1 * norm2)))
    return math.acos(cosang)


def _apply_arm_constraints(shoulder, elbow, wrist):
    """Normalize arm lengths and clamp elbow angle within ROM limits."""
    sx, sy = shoulder
    ex, ey = elbow
    wx, wy = wrist

    # Normalize upper arm length
    upper_angle = math.atan2(ey - sy, ex - sx)
    ex = int(sx + UPPER_ARM * math.cos(upper_angle))
    ey = int(sy + UPPER_ARM * math.sin(upper_angle))

    # Normalize lower arm length
    lower_angle = math.atan2(wy - ey, wx - ex)
    wx = int(ex + LOWER_ARM * math.cos(lower_angle))
    wy = int(ey + LOWER_ARM * math.sin(lower_angle))

    # Clamp elbow angle
    v1 = (sx - ex, sy - ey)
    v2 = (wx - ex, wy - ey)
    angle = _angle_between(v1, v2)
    min_ang = math.radians(ELBOW_MIN_DEG)
    max_ang = math.radians(ELBOW_MAX_DEG)

    if angle < min_ang or angle > max_ang:
        base_angle = math.atan2(v1[1], v1[0])
        v2_angle = math.atan2(v2[1], v2[0])
        delta = v2_angle - base_angle
        # Normalize to [-pi, pi]
        while delta > math.pi:
            delta -= 2 * math.pi
        while delta < -math.pi:
            delta += 2 * math.pi

        clamped = max(min(delta, max_ang), min_ang) if delta >= 0 else min(max(delta, -max_ang), -min_ang)
        new_angle = base_angle + clamped
        wx = int(ex + LOWER_ARM * math.cos(new_angle))
        wy = int(ey + LOWER_ARM * math.sin(new_angle))

    return (ex, ey), (wx, wy)

def generate_hand_landmarks(wrist_pos, hand_direction="down", is_left=True, hand_pose="neutral"):
    """
    Generate 21 hand landmarks with proper palm structure.
    
    MediaPipe hand landmarks:
    0: WRIST
    1-4: THUMB (CMC, MCP, IP, TIP)
    5-8: INDEX (MCP, PIP, DIP, TIP)
    9-12: MIDDLE (MCP, PIP, DIP, TIP)
    13-16: RING (MCP, PIP, DIP, TIP)
    17-20: PINKY (MCP, PIP, DIP, TIP)
    """
    import math
    
    landmarks = []
    wx, wy = wrist_pos
    
    # Segment lengths
    seg = 10  # finger segment length
    palm_depth = 25  # wrist to MCP distance
    palm_width = 35  # width of palm at MCP level

    # Hand pose controls (demo only)
    spread_scale = 1.0
    curl = 0.0
    per_finger_curl = {
        'index': 0.0,
        'middle': 0.0,
        'ring': 0.0,
        'pinky': 0.0,
        'thumb': 0.0,
    }
    if hand_pose == "open":
        spread_scale = 1.2
        curl = 0.0
    elif hand_pose == "close":
        spread_scale = 0.8
        curl = 0.4
        per_finger_curl = {
            'index': 0.10,
            'middle': 0.15,
            'ring': 0.25,
            'pinky': 0.30,
            'thumb': 0.20,
        }
    elif hand_pose == "fist":
        spread_scale = 0.75
        curl = 0.6
        per_finger_curl = {
            'index': 0.20,
            'middle': 0.30,
            'ring': 0.40,
            'pinky': 0.45,
            'thumb': 0.35,
        }
    elif hand_pose == "spread":
        spread_scale = 1.6
        curl = 0.0
    elif hand_pose == "pinch":
        spread_scale = 1.0
        curl = 0.3
        per_finger_curl = {
            'index': 0.15,
            'middle': 0.20,
            'ring': 0.30,
            'pinky': 0.35,
            'thumb': 0.20,
        }

    spread_scale = max(MIN_SPREAD, min(MAX_SPREAD, spread_scale))
    curl = max(MIN_CURL, min(MAX_CURL, curl))
    
    # Direction multipliers
    if hand_direction == "up":
        dx, dy = 0, -1
    elif hand_direction == "down":
        dx, dy = 0, 1
    elif hand_direction == "left":
        dx, dy = -1, 0
    else:  # right
        dx, dy = 1, 0
    
    # Mirror for left vs right hand
    mirror = -1 if is_left else 1
    
    # 0: Wrist
    landmarks.append((wx, wy))
    
    # Palm center (for positioning MCP joints)
    palm_cx = wx + dx * palm_depth
    palm_cy = wy + dy * palm_depth
    
    # Finger angles (fan out from palm) - in radians from palm direction
    # Negative = toward thumb side, Positive = toward pinky side
    finger_angles = {
        'index': -0.15 * mirror,
        'middle': 0.0,
        'ring': 0.15 * mirror,
        'pinky': 0.30 * mirror,
    }
    
    # Finger lengths (middle longest)
    finger_lengths = {
        'index': seg * 3.2,
        'middle': seg * 3.5,
        'ring': seg * 3.2,
        'pinky': seg * 2.8,
    }
    
    # MCP positions across palm (arc from index to pinky)
    mcp_offsets = {
        'index': -palm_width * 0.4 * mirror,
        'middle': -palm_width * 0.15 * mirror,
        'ring': palm_width * 0.15 * mirror,
        'pinky': palm_width * 0.45 * mirror,
    }
    
    # 1-4: THUMB (angled to the side - toward index finger)
    # Left hand: thumb on RIGHT side (positive X)
    # Right hand: thumb on LEFT side (negative X)
    thumb_side = 1 if is_left else -1  # Left hand thumb goes RIGHT (+), Right hand thumb goes LEFT (-)
    
    # Thumb base position (CMC - at side of palm)
    thumb_base_x = wx + thumb_side * 18
    thumb_base_y = wy + dy * 3
    
    landmarks.append((int(thumb_base_x), int(thumb_base_y)))  # 1: CMC

    # Thumb direction with curl (length stays constant)
    base_dir = math.atan2(dy, dx) if (dx != 0 or dy != 0) else math.pi / 2
    thumb_angle = base_dir + (thumb_side * 0.6) + per_finger_curl.get('thumb', 0.0)
    t_dx = math.cos(thumb_angle) * seg * 0.9
    t_dy = math.sin(thumb_angle) * seg * 0.9
    landmarks.append((int(thumb_base_x + t_dx), int(thumb_base_y + t_dy)))  # 2: MCP
    landmarks.append((int(thumb_base_x + t_dx * 1.8), int(thumb_base_y + t_dy * 1.8)))  # 3: IP
    landmarks.append((int(thumb_base_x + t_dx * 2.5), int(thumb_base_y + t_dy * 2.5)))  # 4: TIP
    
    # Generate fingers: index, middle, ring, pinky
    for finger, mcp_idx in [('index', 5), ('middle', 9), ('ring', 13), ('pinky', 17)]:
        offset = mcp_offsets[finger] * spread_scale
        max_offset = palm_width * 0.5
        if offset > max_offset:
            offset = max_offset
        if offset < -max_offset:
            offset = -max_offset
        angle = finger_angles[finger] + per_finger_curl.get(finger, 0.0) + curl
        length = finger_lengths[finger]
        
        # MCP position (base of finger on palm)
        if dy != 0:  # vertical hand
            mcp_x = palm_cx + offset
            mcp_y = palm_cy
        else:  # horizontal hand
            mcp_x = palm_cx
            mcp_y = palm_cy + offset
        
        # Finger direction with curl offset (direction changes, length constant)
        base_dir = math.atan2(dy, dx) if (dx != 0 or dy != 0) else math.pi / 2
        finger_dir = base_dir + angle
        f_dx = math.cos(finger_dir) * length / 3
        f_dy = math.sin(finger_dir) * length / 3
        
        # 4 points per finger: MCP, PIP, DIP, TIP
        landmarks.append((int(mcp_x), int(mcp_y)))  # MCP
        landmarks.append((int(mcp_x + f_dx), int(mcp_y + f_dy)))  # PIP
        landmarks.append((int(mcp_x + f_dx * 2), int(mcp_y + f_dy * 2)))  # DIP
        landmarks.append((int(mcp_x + f_dx * 3), int(mcp_y + f_dy * 3)))  # TIP
    
    if hand_pose == "pinch":
        thumb_tip = 4
        index_tip = 8
        mid_x = int((landmarks[thumb_tip][0] + landmarks[index_tip][0]) / 2)
        mid_y = int((landmarks[thumb_tip][1] + landmarks[index_tip][1]) / 2)
        landmarks[thumb_tip] = (mid_x, mid_y)
        landmarks[index_tip] = (mid_x + (2 * mirror), mid_y)

    return landmarks

def draw_hand(frame, landmarks, color):
    """Draw hand skeleton from 21 landmarks."""
    finger_connections = {
        'thumb': [(0, 1), (1, 2), (2, 3), (3, 4)],
        'index': [(0, 5), (5, 6), (6, 7), (7, 8)],
        'middle': [(0, 9), (9, 10), (10, 11), (11, 12)],
        'ring': [(0, 13), (13, 14), (14, 15), (15, 16)],
        'pinky': [(0, 17), (17, 18), (18, 19), (19, 20)],
    }
    palm_connections = [(5, 9), (9, 13), (13, 17)]
    
    # Draw palm connections
    for idx1, idx2 in palm_connections:
        pt1 = landmarks[idx1]
        pt2 = landmarks[idx2]
        cv2.line(frame, pt1, pt2, BODY_COLOR, 2)
    
    # Draw fingers with per-finger colors
    for finger_name, connections in finger_connections.items():
        finger_color = FINGER_COLORS[finger_name]
        for idx1, idx2 in connections:
            pt1 = landmarks[idx1]
            pt2 = landmarks[idx2]
            cv2.line(frame, pt1, pt2, finger_color, 2)
    
    # Draw joints
    for i, pt in enumerate(landmarks):
        radius = 4 if i == 0 else 3  # Wrist larger
        cv2.circle(frame, pt, radius, (0, 255, 255), -1)


def draw_face(frame, center, expression="neutral"):
    """
    Draw oval face with simplified facial features (industry standard).
    
    Based on sign-language-processing Pose Stream visualization:
    - Oval face shape (taller than wide)
    - Simplified eyebrows (curved lines - can show raised/lowered)
    - Simple eyes (small filled circles)
    - Mouth curve (arc - can show smile/neutral/frown)
    
    Args:
        frame: CV2 image to draw on
        center: (x, y) tuple for face center
        expression: "neutral", "raised_eyebrows", "questioning" for future extension
    """
    cx, cy = center
    
    # Draw oval face outline
    # cv2.ellipse params: (center, (width/2, height/2), angle, start_angle, end_angle, color, thickness)
    cv2.ellipse(frame, (cx, cy), (HEAD_WIDTH // 2, HEAD_HEIGHT // 2), 0, 0, 360, BODY_COLOR, 3)
    
    # === Facial Features (simplified icons matching industry standard) ===
    
    # Eye positions: roughly 1/3 down from top, 1/4 in from sides
    eye_y = cy - HEAD_HEIGHT // 6  # slightly above center
    left_eye_x = cx - HEAD_WIDTH // 4
    right_eye_x = cx + HEAD_WIDTH // 4
    eye_radius = 4
    
    # Draw eyes as filled circles
    cv2.circle(frame, (left_eye_x, eye_y), eye_radius, BODY_COLOR, -1)
    cv2.circle(frame, (right_eye_x, eye_y), eye_radius, BODY_COLOR, -1)
    
    # Eyebrow positions: above eyes
    eyebrow_y = eye_y - 10
    eyebrow_width = 12
    eyebrow_thickness = 2
    
    # Eyebrow height offset based on expression
    if expression == "raised_eyebrows" or expression == "questioning":
        eyebrow_y -= 4  # Raised eyebrows
    
    # Draw eyebrows as short curved lines (arcs)
    # Left eyebrow - slight curve up
    cv2.ellipse(frame, (left_eye_x, eyebrow_y + 5), (eyebrow_width, 6), 0, 200, 340, BODY_COLOR, eyebrow_thickness)
    # Right eyebrow - slight curve up  
    cv2.ellipse(frame, (right_eye_x, eyebrow_y + 5), (eyebrow_width, 6), 0, 200, 340, BODY_COLOR, eyebrow_thickness)
    
    # Mouth position: 1/4 up from bottom of face
    mouth_y = cy + HEAD_HEIGHT // 4
    mouth_width = HEAD_WIDTH // 3
    
    # Draw mouth as curved line (neutral = slight smile)
    # cv2.ellipse for a smile arc
    cv2.ellipse(frame, (cx, mouth_y - 3), (mouth_width // 2, 5), 0, 10, 170, BODY_COLOR, 2)

def draw_reference_body(frame, hand_position="neutral"):
    """Draw reference body with hands in specified position. Upper body only."""
    
    # Shoulder positions
    left_shoulder = (CENTER_X - SHOULDER_WIDTH // 2, CENTER_Y)
    right_shoulder = (CENTER_X + SHOULDER_WIDTH // 2, CENTER_Y)
    
    # Neck (connects shoulders to head)
    neck_top = (CENTER_X, CENTER_Y - 35)
    neck_bottom = (CENTER_X, CENTER_Y)
    
    # Head - oval face (50x70px) with simplified facial features
    # Position: neck_top (35px above shoulders) + half head height (35px) = 70px above shoulders
    head_center = (CENTER_X, CENTER_Y - 70)
    
    # Torso bottom (just below shoulders, no full hip)
    torso_bottom = (CENTER_X, CENTER_Y + 60)
    
    # Arm segment lengths use global constants (anatomically accurate 55/45 ratio)
    # UPPER_ARM = 55px (shoulder to elbow), LOWER_ARM = 45px (elbow to wrist)
    
    if hand_position == "up":
        # Arms go UP, elbows stay close to body
        left_elbow = (CENTER_X - SHOULDER_WIDTH // 2 - 5, CENTER_Y - UPPER_ARM)
        right_elbow = (CENTER_X + SHOULDER_WIDTH // 2 + 5, CENTER_Y - UPPER_ARM)
        left_wrist = (CENTER_X - SHOULDER_WIDTH // 2 - 10, CENTER_Y - UPPER_ARM - LOWER_ARM)
        right_wrist = (CENTER_X + SHOULDER_WIDTH // 2 + 10, CENTER_Y - UPPER_ARM - LOWER_ARM)
        hand_dir = "up"
    elif hand_position == "down":
        # Arms hang down naturally
        left_elbow = (CENTER_X - SHOULDER_WIDTH // 2 - 10, CENTER_Y + UPPER_ARM)
        right_elbow = (CENTER_X + SHOULDER_WIDTH // 2 + 10, CENTER_Y + UPPER_ARM)
        left_wrist = (CENTER_X - SHOULDER_WIDTH // 2 - 15, CENTER_Y + UPPER_ARM + LOWER_ARM)
        right_wrist = (CENTER_X + SHOULDER_WIDTH // 2 + 15, CENTER_Y + UPPER_ARM + LOWER_ARM)
        hand_dir = "down"
    elif hand_position == "left":
        # Both arms reaching left - consistent lengths
        left_elbow = (CENTER_X - SHOULDER_WIDTH // 2 - UPPER_ARM, CENTER_Y)
        right_elbow = (CENTER_X - UPPER_ARM // 2, CENTER_Y)
        left_wrist = (CENTER_X - SHOULDER_WIDTH // 2 - UPPER_ARM - LOWER_ARM, CENTER_Y)
        right_wrist = (CENTER_X - UPPER_ARM // 2 - LOWER_ARM, CENTER_Y)
        hand_dir = "left"
    elif hand_position == "right":
        # Both arms reaching right - consistent lengths
        left_elbow = (CENTER_X + UPPER_ARM // 2, CENTER_Y)
        right_elbow = (CENTER_X + SHOULDER_WIDTH // 2 + UPPER_ARM, CENTER_Y)
        left_wrist = (CENTER_X + UPPER_ARM // 2 + LOWER_ARM, CENTER_Y)
        right_wrist = (CENTER_X + SHOULDER_WIDTH // 2 + UPPER_ARM + LOWER_ARM, CENTER_Y)
        hand_dir = "right"
    else:  # neutral - relaxed pose, arms slightly forward (ready position)
        left_elbow = (CENTER_X - SHOULDER_WIDTH // 2 - 25, CENTER_Y + 20)
        right_elbow = (CENTER_X + SHOULDER_WIDTH // 2 + 25, CENTER_Y + 20)
        left_wrist = (CENTER_X - SHOULDER_WIDTH // 2 - 50, CENTER_Y + 50)
        right_wrist = (CENTER_X + SHOULDER_WIDTH // 2 + 50, CENTER_Y + 50)
        hand_dir = "down"
    
    # Override for chest position - hands in front of body (signing space)
    if hand_position == "chest":
        # Elbows bent, hands in front of chest - common signing position
        left_elbow = (CENTER_X - SHOULDER_WIDTH // 2 - 30, CENTER_Y + 10)
        right_elbow = (CENTER_X + SHOULDER_WIDTH // 2 + 30, CENTER_Y + 10)
        left_wrist = (CENTER_X - 40, CENTER_Y - 20)
        right_wrist = (CENTER_X + 40, CENTER_Y - 20)
        hand_dir = "up"
    
    # Enforce arm proportions and elbow ROM (keeps movements intact)
    left_elbow, left_wrist = _apply_arm_constraints(left_shoulder, left_elbow, left_wrist)
    right_elbow, right_wrist = _apply_arm_constraints(right_shoulder, right_elbow, right_wrist)

    # Draw spine (short - just upper body)
    cv2.line(frame, (CENTER_X, CENTER_Y), torso_bottom, BODY_COLOR, 3)
    
    # Draw neck (connects shoulder line to head)
    cv2.line(frame, neck_bottom, neck_top, NECK_COLOR, 3)
    
    # Draw shoulders
    cv2.line(frame, left_shoulder, right_shoulder, BODY_COLOR, 3)
    
    # Draw arms
    cv2.line(frame, left_shoulder, left_elbow, LEFT_ARM_COLOR, 3)
    cv2.line(frame, left_elbow, left_wrist, LEFT_ARM_COLOR, 3)
    cv2.line(frame, right_shoulder, right_elbow, RIGHT_ARM_COLOR, 3)
    cv2.line(frame, right_elbow, right_wrist, RIGHT_ARM_COLOR, 3)
    
    # Draw face (oval with simplified facial features - industry standard)
    draw_face(frame, head_center, expression="neutral")
    
    # Draw arm joints
    for joint in [left_shoulder, right_shoulder, left_elbow, right_elbow]:
        cv2.circle(frame, joint, 8, JOINT_COLOR, -1)
    
    # Hand pose override (same arm positions)
    hand_pose = "neutral"
    if hand_position in {"open", "close", "spread", "pinch", "fist"}:
        hand_pose = hand_position

    # Generate and draw hands with 21 landmarks each
    left_hand = generate_hand_landmarks(left_wrist, hand_dir, is_left=True, hand_pose=hand_pose)
    right_hand = generate_hand_landmarks(right_wrist, hand_dir, is_left=False, hand_pose=hand_pose)
    
    draw_hand(frame, left_hand, LEFT_ARM_COLOR)
    draw_hand(frame, right_hand, RIGHT_ARM_COLOR)
    
    # Check if ALL hand landmarks are in bounds
    in_bounds = True
    margin = 15
    for hand_pts, name in [(left_hand, "LEFT"), (right_hand, "RIGHT")]:
        for pt in hand_pts:
            x, y = pt
            if x < margin or x > WIDTH - margin or y < margin or y > HEIGHT - margin:
                cv2.putText(frame, f"{name} OUT OF BOUNDS!", (10, 30 if name == "LEFT" else 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                in_bounds = False
                break  # Only report once per hand
    
    # Show landmark counts
    cv2.putText(frame, f"Left hand: 21 pts | Right hand: 21 pts", (10, HEIGHT - 50),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    return in_bounds

def main():
    positions = ["neutral", "up", "down", "left", "right", "chest", "open", "close", "spread", "pinch", "fist"]
    current_pos = 0
    
    print("Reference Body Viewer")
    print("=====================")
    print("Press SPACE to cycle: neutral → up → down → left → right → chest → open → close → spread → pinch → fist")
    print("Press Q to quit")
    print()
    
    while True:
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        frame[:] = (40, 40, 40)  # Dark gray background
        
        pos = positions[current_pos]
        in_bounds = draw_reference_body(frame, pos)
        
        # Draw title
        status = "IN FRAME" if in_bounds else "OUT OF BOUNDS"
        color = (0, 255, 0) if in_bounds else (0, 0, 255)
        cv2.putText(frame, f"Hands: {pos.upper()} - {status}", (10, HEIGHT - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Draw frame boundary
        cv2.rectangle(frame, (5, 5), (WIDTH - 5, HEIGHT - 5), (100, 100, 100), 1)
        
        cv2.imshow("Reference Body", frame)
        
        key = cv2.waitKey(100) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            current_pos = (current_pos + 1) % len(positions)
            print(f"Position: {positions[current_pos]}")
    
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
