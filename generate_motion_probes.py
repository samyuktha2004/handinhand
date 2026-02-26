#!/usr/bin/env python3
"""Generate motion probe signatures for embedding diagnostics.

Outputs JSON signatures in the same format as extracted signatures:
  - pose_data: list of frames
  - each frame has pose (NUM_POSE), left_hand (NUM_HAND), right_hand (NUM_HAND), face (NUM_FACE)

These are control motions (not signs) for embedding sanity checks.
"""
import json
import math
from typing import Dict, List, Tuple

from skeleton_renderer import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
    SHOULDER_WIDTH,
    UPPER_ARM,
    LOWER_ARM,
    PALM_LENGTH,
    FINGER_LENGTHS,
    FINGER_BASE_OFFSETS,
)
from utils.landmarks import NUM_POSE, NUM_HAND, NUM_FACE


WIDTH = FRAME_WIDTH
HEIGHT = FRAME_HEIGHT


def _norm_pt(pt: Tuple[float, float]) -> List[float]:
    return [pt[0] / WIDTH, pt[1] / HEIGHT, 0.0]


def _point_at(origin: Tuple[float, float], angle: float, dist: float) -> Tuple[float, float]:
    return (origin[0] + dist * math.cos(angle), origin[1] + dist * math.sin(angle))


def _build_pose(shoulder_center: Tuple[float, float], left_angle: float, right_angle: float) -> List[List[float]]:
    """Return 6 pose points: LS, RS, LE, RE, LW, RW in normalized coords."""
    cx, cy = shoulder_center
    left_shoulder = (cx - SHOULDER_WIDTH / 2, cy)
    right_shoulder = (cx + SHOULDER_WIDTH / 2, cy)

    left_elbow = _point_at(left_shoulder, left_angle, UPPER_ARM)
    right_elbow = _point_at(right_shoulder, right_angle, UPPER_ARM)

    left_wrist = _point_at(left_elbow, left_angle, LOWER_ARM)
    right_wrist = _point_at(right_elbow, right_angle, LOWER_ARM)

    return [
        _norm_pt(left_shoulder),
        _norm_pt(right_shoulder),
        _norm_pt(left_elbow),
        _norm_pt(right_elbow),
        _norm_pt(left_wrist),
        _norm_pt(right_wrist),
    ]


def _build_hand(wrist: Tuple[float, float], mode: str, mirror: int) -> List[List[float]]:
    """Build a 21-point hand in local coordinates.

    Handshape coverage (ASL/BSL phonemic space — combinations cover all signs):

      Closed fist group:
        close_a   — ASL "A": fist, thumb ALONGSIDE fingers (A, N, T signs)
        close_s   — ASL "S": fist, thumb OVER index/middle fingers (S, E, M signs)

      Extended finger group:
        open      — ASL "B" spread: fingers extended, moderate spread
        flat_b    — ASL "B" flat: fingers extended, TOGETHER, thumb tucked
        spread    — ASL "5": fingers extended and maximally spread

      Curved group:
        curved_c  — ASL "C": curved as if holding a ball (C, G entry position)
        o_shape   — ASL "O": all fingertips touch thumb, circular aperture

      Selective extension group (per-finger control):
        point     — ASL "1"/"G"/"D": index extended, others closed
        v_shape   — ASL "V"/"2"/"U": index+middle extended, others closed
        l_shape   — ASL "L": index pointing up, thumb extended out 90°
        y_shape   — ASL "Y": thumb+pinky extended, middle fingers closed

      Contact group:
        pinch     — ASL "F"/"8": thumb tip meets index tip
        neutral   — resting hand (used as inter-probe baseline)

    mirror: 1 = right hand, -1 = left hand
    """
    wx, wy = wrist
    points: List[Tuple[float, float]] = []
    points.append((wx, wy))  # Wrist (landmark 0)

    finger_order = ["thumb", "index", "middle", "ring", "pinky"]

    # Canonical finger base angles (radians from straight-down = π/2).
    # Aligned with skeleton_renderer.py FINGER_ANGLES constant.
    # Thumb: -0.70 rad = 40° natural abduction (PMC 2013 clinical ref).
    _BASE_ANGLES = {
        "thumb": -0.70, "index": -0.12, "middle": 0.0, "ring": 0.12, "pinky": 0.28,
    }

    # Per-finger curl (radians added per joint position, uniform within a finger).
    # Closed = 0.52 (tip at ~89° from base, correct front-view fist).
    # Extended = 0.0.
    FIST_CURL = 0.52

    # Default: all fingers extended, natural spread, thumb natural
    finger_curls = {f: 0.0 for f in finger_order}
    finger_length_scales = {f: 1.0 for f in finger_order}
    spread = 1.0
    thumb_abduction = _BASE_ANGLES["thumb"]  # default

    # ----------------------------------------------------------------
    # Closed fist group
    # ----------------------------------------------------------------
    if mode in ("close_a", "close_s"):
        spread = 0.6
        finger_curls = {f: FIST_CURL for f in finger_order}
        finger_length_scales = {f: 0.7 for f in finger_order}
        # Thumb: adducted alongside fist for both A and S (thumb angle toward fingers)
        thumb_abduction = -0.30  # ~17° — thumb pressed alongside, less abducted in fist

    # ----------------------------------------------------------------
    # Extended finger group
    # ----------------------------------------------------------------
    elif mode == "open":
        spread = 1.2
        finger_curls = {f: 0.0 for f in finger_order}

    elif mode == "flat_b":
        spread = 0.55  # fingers tight together
        finger_curls = {f: 0.0 for f in finger_order}
        thumb_abduction = -0.15  # tucked, barely abducted

    elif mode == "spread":
        spread = 1.6
        finger_curls = {f: 0.0 for f in finger_order}

    # ----------------------------------------------------------------
    # Curved group
    # ----------------------------------------------------------------
    elif mode == "curved_c":
        spread = 1.1
        # C-shape: moderate curl, MCP≈30°, PIP≈45°, DIP≈10°
        # Represented as uniform curl ≈ 0.22 (13°/joint, cumulative 39° at DIP)
        finger_curls = {f: 0.22 for f in finger_order}
        thumb_abduction = -0.55  # partially abducted to complete the C

    elif mode == "o_shape":
        spread = 0.7
        # O-shape: fingertips curl significantly toward thumb tip
        # High curl brings all tips toward center; post-processing meets them
        finger_curls = {f: 0.42 for f in finger_order}
        finger_length_scales = {f: 0.85 for f in finger_order}
        thumb_abduction = -0.40  # thumb bends into the circle

    # ----------------------------------------------------------------
    # Selective extension group (per-finger)
    # ----------------------------------------------------------------
    elif mode == "point":
        spread = 0.8
        finger_curls = {
            "thumb": 0.25,   # alongside fist
            "index": 0.0,    # EXTENDED — pointing
            "middle": FIST_CURL,
            "ring": FIST_CURL,
            "pinky": FIST_CURL,
        }
        finger_length_scales = {
            "thumb": 0.85, "index": 1.0, "middle": 0.7, "ring": 0.7, "pinky": 0.7,
        }
        thumb_abduction = -0.30  # tucked alongside

    elif mode == "v_shape":
        spread = 1.0
        finger_curls = {
            "thumb": 0.25,
            "index": 0.0,    # EXTENDED
            "middle": 0.0,   # EXTENDED
            "ring": FIST_CURL,
            "pinky": FIST_CURL,
        }
        finger_length_scales = {
            "thumb": 0.85, "index": 1.0, "middle": 1.0, "ring": 0.7, "pinky": 0.7,
        }
        thumb_abduction = -0.30

    elif mode == "l_shape":
        spread = 0.9
        finger_curls = {
            "thumb": 0.0,    # EXTENDED outward — but we rotate thumb angle separately
            "index": 0.0,    # EXTENDED pointing up
            "middle": FIST_CURL,
            "ring": FIST_CURL,
            "pinky": FIST_CURL,
        }
        finger_length_scales = {
            "thumb": 1.0, "index": 1.0, "middle": 0.7, "ring": 0.7, "pinky": 0.7,
        }
        # Thumb perpendicular to index: -1.40 rad ≈ -80° (nearly 90° from middle finger)
        thumb_abduction = -1.40

    elif mode == "y_shape":
        spread = 1.0
        finger_curls = {
            "thumb": 0.0,    # EXTENDED
            "index": FIST_CURL,
            "middle": FIST_CURL,
            "ring": FIST_CURL,
            "pinky": 0.0,    # EXTENDED
        }
        finger_length_scales = {
            "thumb": 1.0, "index": 0.7, "middle": 0.7, "ring": 0.7, "pinky": 1.0,
        }
        thumb_abduction = -0.85  # more abducted for Y shape

    # ----------------------------------------------------------------
    # Contact group
    # ----------------------------------------------------------------
    elif mode == "pinch":
        spread = 1.0
        finger_curls = {
            "thumb": 0.20,
            "index": 0.20,   # slight curl to bring tip toward thumb
            "middle": 0.18, "ring": 0.18, "pinky": 0.18,
        }
        finger_length_scales = {f: 0.9 for f in finger_order}

    # ----------------------------------------------------------------
    # Neutral (default): natural relaxed signing hand
    # No override needed — zero curl with natural spread represents
    # the probes' "start" frame; full cascade handled in renderer.
    # ----------------------------------------------------------------

    # Build base angle map with resolved thumb abduction
    base_angle_map = dict(_BASE_ANGLES)
    base_angle_map["thumb"] = thumb_abduction

    # ----------------------------------------------------------------
    # Build finger geometry
    # ----------------------------------------------------------------
    base_angle_down = math.pi / 2  # pointing down in image space

    for finger_name in finger_order:
        dx = FINGER_BASE_OFFSETS[finger_name] * spread * mirror
        dy = PALM_LENGTH
        if finger_name == "thumb":
            dy = 5
            dx = abs(dx) * mirror

        base = (wx + dx, wy + dy)
        points.append(base)  # MCP (or CMC for thumb)

        lengths = FINGER_LENGTHS[finger_name]
        angle = base_angle_down + base_angle_map[finger_name] * mirror
        curl = finger_curls[finger_name]
        lscale = finger_length_scales[finger_name]

        current = base
        for i, seg in enumerate(lengths[1:], start=1):
            seg_len = seg * lscale
            seg_angle = angle + curl * i
            current = _point_at(current, seg_angle, seg_len)
            points.append(current)

    # Ensure exactly 21 points
    if len(points) < 21:
        points.extend([points[-1]] * (21 - len(points)))
    points = points[:21]

    # ----------------------------------------------------------------
    # Post-processing for specific shapes
    # ----------------------------------------------------------------

    # close_s: thumb tip wraps OVER index/middle fingers (ASL "S" dorsal wrap)
    if mode == "close_s":
        index_mcp = points[5]
        thumb_tip_idx = 4
        tx = points[thumb_tip_idx][0] * 0.4 + index_mcp[0] * 0.6
        ty = points[thumb_tip_idx][1] * 0.4 + index_mcp[1] * 0.6
        points[thumb_tip_idx] = (tx, ty)

    # o_shape: pull all fingertips toward thumb tip to close the circle
    elif mode == "o_shape":
        thumb_tip = points[4]
        # index, middle, ring, pinky tips are at indices 8, 12, 16, 20
        for tip_idx in [8, 12, 16, 20]:
            tx = points[tip_idx][0] * 0.5 + thumb_tip[0] * 0.5
            ty = points[tip_idx][1] * 0.5 + thumb_tip[1] * 0.5
            points[tip_idx] = (tx, ty)

    # pinch: bring thumb + index tips together
    elif mode == "pinch":
        thumb_tip = 4
        index_tip = 8
        mid_x = (points[thumb_tip][0] + points[index_tip][0]) / 2
        mid_y = (points[thumb_tip][1] + points[index_tip][1]) / 2
        points[thumb_tip] = (mid_x, mid_y)
        points[index_tip] = (mid_x + 1 * mirror, mid_y)

    return [_norm_pt(pt) for pt in points]


def _frame_dict(pose: List[List[float]], left_hand: List[List[float]], right_hand: List[List[float]]) -> Dict:
    return {
        "pose": pose,
        "left_hand": left_hand,
        "right_hand": right_hand,
        "face": [[0.0, 0.0, 0.0] for _ in range(NUM_FACE)],
    }


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def build_probe_sequence(name: str, steps: int = 12) -> Dict:
    """Create a probe signature by name."""
    shoulder_center = (WIDTH / 2, HEIGHT / 2)
    neutral_left = math.radians(120)
    neutral_right = math.radians(60)

    left_shoulder = (shoulder_center[0] - SHOULDER_WIDTH / 2, shoulder_center[1])
    right_shoulder = (shoulder_center[0] + SHOULDER_WIDTH / 2, shoulder_center[1])

    def _angles_for_direction(direction: str) -> Tuple[float, float]:
        if direction == "up":
            left_elbow = (left_shoulder[0] - 5, left_shoulder[1] - UPPER_ARM)
            right_elbow = (right_shoulder[0] + 5, right_shoulder[1] - UPPER_ARM)
        elif direction == "down":
            left_elbow = (left_shoulder[0] - 10, left_shoulder[1] + UPPER_ARM)
            right_elbow = (right_shoulder[0] + 10, right_shoulder[1] + UPPER_ARM)
        elif direction == "left":
            left_elbow = (left_shoulder[0] - UPPER_ARM, left_shoulder[1])
            right_elbow = (left_shoulder[0] + SHOULDER_WIDTH / 2, right_shoulder[1])
        else:  # right
            left_elbow = (right_shoulder[0] - SHOULDER_WIDTH / 2, left_shoulder[1])
            right_elbow = (right_shoulder[0] + UPPER_ARM, right_shoulder[1])

        left_angle = math.atan2(left_elbow[1] - left_shoulder[1], left_elbow[0] - left_shoulder[0])
        right_angle = math.atan2(right_elbow[1] - right_shoulder[1], right_elbow[0] - right_shoulder[0])
        return left_angle, right_angle

    frames = []

    if name in {"up", "down", "left", "right"}:
        left_target, right_target = _angles_for_direction(name)

        for i in range(steps):
            t = i / max(steps - 1, 1)
            left_angle = _lerp(neutral_left, left_target, t)
            right_angle = _lerp(neutral_right, right_target, t)
            pose = _build_pose(shoulder_center, left_angle, right_angle)
            left_wrist = (pose[4][0] * WIDTH, pose[4][1] * HEIGHT)
            right_wrist = (pose[5][0] * WIDTH, pose[5][1] * HEIGHT)
            left_hand = _build_hand(left_wrist, "neutral", mirror=-1)
            right_hand = _build_hand(right_wrist, "neutral", mirror=1)
            frames.append(_frame_dict(pose, left_hand, right_hand))

    _HAND_SHAPE_PROBES = {
        "open", "flat_b", "spread",          # extended group
        "close_a", "close_s",                # fist group
        "curved_c", "o_shape",               # curved group
        "point", "v_shape", "l_shape", "y_shape",  # selective extension group
        "pinch",                             # contact group
    }

    if name in _HAND_SHAPE_PROBES:
        pose = _build_pose(shoulder_center, neutral_left, neutral_right)
        left_wrist = (pose[4][0] * WIDTH, pose[4][1] * HEIGHT)
        right_wrist = (pose[5][0] * WIDTH, pose[5][1] * HEIGHT)
        # Animate: first half neutral, second half target shape.
        # GAP will average the transition → embedding is distinct from static poses.
        # This also matches real signing: hand transitions into shape, not teleports.
        half = steps // 2
        for i in range(steps):
            frame_mode = "neutral" if i < half else name
            left_hand = _build_hand(left_wrist, frame_mode, mirror=-1)
            right_hand = _build_hand(right_wrist, frame_mode, mirror=1)
            frames.append(_frame_dict(pose, left_hand, right_hand))

    return {
        "metadata": {
            "frame_width": WIDTH,
            "frame_height": HEIGHT,
            "probe_name": name,
            "landmarks_per_frame": {
                "pose": NUM_POSE,
                "left_hand": NUM_HAND,
                "right_hand": NUM_HAND,
                "face": NUM_FACE,
            },
        },
        "pose_data": frames,
    }


def main() -> None:
    probe_names = [
        # Arm direction probes (body position)
        "up", "down", "left", "right",
        # Extended finger group
        "open",       # ASL B-spread: fingers extended, moderate spread
        "flat_b",     # ASL B-flat: fingers together, thumb tucked
        "spread",     # ASL 5: fingers maximally spread
        # Fist group
        "close_a",    # ASL A: fist, thumb alongside
        "close_s",    # ASL S: fist, thumb over fingers
        # Curved group
        "curved_c",   # ASL C: curved like holding a ball
        "o_shape",    # ASL O: all tips touch thumb
        # Selective extension (per-finger)
        "point",      # ASL 1/G/D: index pointing
        "v_shape",    # ASL V/2: index+middle extended
        "l_shape",    # ASL L: index up, thumb out
        "y_shape",    # ASL Y: thumb+pinky extended
        # Contact
        "pinch",      # ASL F/8: thumb-index contact
    ]
    for name in probe_names:
        signature = build_probe_sequence(name)
        out_path = f"assets/probes/probe_{name}.json"
        with open(out_path, "w") as f:
            json.dump(signature, f, indent=2)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
