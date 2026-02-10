#!/usr/bin/env python3
"""Generate motion probe signatures for embedding diagnostics.

Outputs JSON signatures in the same format as extracted signatures:
  - pose_data: list of frames
  - each frame has pose (6), left_hand (21), right_hand (21), face (4)

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

    mode: neutral | open | close | spread | pinch
    mirror: 1 (right hand) or -1 (left hand)
    """
    wx, wy = wrist
    points: List[Tuple[float, float]] = []

    # Wrist point
    points.append((wx, wy))

    # Hand shaping parameters
    spread = 1.0
    curl = 0.0
    length_scale = 1.0

    if mode == "open":
        spread = 1.2
        curl = 0.0
        length_scale = 1.0
    elif mode == "close":
        spread = 0.8
        curl = 0.35
        length_scale = 0.7
    elif mode == "spread":
        spread = 1.6
        curl = 0.0
        length_scale = 1.0
    elif mode == "pinch":
        spread = 1.0
        curl = 0.15
        length_scale = 0.9

    # Build each finger from base offsets
    finger_order = ["thumb", "index", "middle", "ring", "pinky"]
    base_angle = math.pi / 2  # down
    base_angle_variants = {
        "thumb": -0.55,
        "index": -0.12,
        "middle": 0.0,
        "ring": 0.12,
        "pinky": 0.28,
    }

    for finger_name in finger_order:
        dx = FINGER_BASE_OFFSETS[finger_name] * spread * mirror
        dy = PALM_LENGTH
        if finger_name == "thumb":
            dy = 5
            dx = abs(dx) * mirror

        base = (wx + dx, wy + dy)
        points.append(base)

        lengths = FINGER_LENGTHS[finger_name]
        angle = base_angle + base_angle_variants[finger_name] * mirror

        current = base
        for i, seg in enumerate(lengths[1:], start=1):
            seg_len = seg * length_scale
            seg_angle = angle + curl * i
            current = _point_at(current, seg_angle, seg_len)
            points.append(current)

    # Ensure 21 points
    if len(points) < 21:
        points.extend([points[-1]] * (21 - len(points)))
    points = points[:21]

    # Pinch: bring thumb + index tips together
    if mode == "pinch":
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
        "face": [[0.0, 0.0, 0.0] for _ in range(4)],
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

    if name in {"open", "close", "spread", "pinch"}:
        pose = _build_pose(shoulder_center, neutral_left, neutral_right)
        left_wrist = (pose[4][0] * WIDTH, pose[4][1] * HEIGHT)
        right_wrist = (pose[5][0] * WIDTH, pose[5][1] * HEIGHT)
        for _ in range(steps):
            left_hand = _build_hand(left_wrist, name, mirror=-1)
            right_hand = _build_hand(right_wrist, name, mirror=1)
            frames.append(_frame_dict(pose, left_hand, right_hand))

    return {
        "metadata": {
            "frame_width": WIDTH,
            "frame_height": HEIGHT,
            "probe_name": name,
        },
        "pose_data": frames,
    }


def main() -> None:
    probe_names = ["up", "down", "left", "right", "open", "close", "spread", "pinch"]
    for name in probe_names:
        signature = build_probe_sequence(name)
        out_path = f"assets/probes/probe_{name}.json"
        with open(out_path, "w") as f:
            json.dump(signature, f, indent=2)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
