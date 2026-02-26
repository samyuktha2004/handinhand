#!/usr/bin/env python3
"""Validate and embed motion probe signatures.

Steps:
1) Integrity checks on probe JSON
2) Render first/last frames to PNG
3) Compute embeddings and cosine similarities
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

from generate_embeddings import EmbeddingGenerator
from skeleton_renderer import SkeletonDrawerCompat, extract_landmarks_from_signature
from utils.landmarks import NUM_POSE, NUM_HAND, NUM_FACE

PROBES_DIR = Path("assets/probes")
EMBED_DIR = PROBES_DIR / "embeddings"
RENDER_DIR = PROBES_DIR / "renders"

# STRICT_PAIR_CHECKS: pairs that MUST be distinct with current GAP embeddings.
# If any score > ALARM_THRESHOLD the pipeline exits with error — data or code bug.
ALARM_THRESHOLD = 0.90
STRICT_PAIR_CHECKS = [
    ("up", "down"),
    ("left", "right"),
]

# MONITORING_PAIR_CHECKS: pairs expected to be HIGH-similarity with GAP embeddings
# (Global Average Pooling averages neutral+target frames → handshapes look similar).
# These are LOGGED but do NOT cause exit(1). After Phase 5 (temporal attention),
# move these to STRICT_PAIR_CHECKS and expect scores to drop below ALARM_THRESHOLD.
MONITORING_PAIR_CHECKS = [
    ("open", "close_a"),       # open hand vs ASL-A fist
    ("open", "close_s"),       # open hand vs ASL-S fist
    ("spread", "close_s"),     # max spread vs closed fist
    ("pinch", "close_a"),      # fingertip contact vs full fist
    ("close_a", "close_s"),    # A-shape vs S-shape fist — thumb position differs
]

# All pairs for report output
PAIR_CHECKS = STRICT_PAIR_CHECKS + MONITORING_PAIR_CHECKS


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _check_frame(frame: Dict) -> List[str]:
    issues = []
    for key, expected in [("pose", NUM_POSE), ("left_hand", NUM_HAND), ("right_hand", NUM_HAND), ("face", NUM_FACE)]:
        pts = frame.get(key, [])
        if len(pts) != expected:
            issues.append(f"{key}={len(pts)}")
    return issues


def _render_frame(landmarks: np.ndarray, width: int, height: int) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    return SkeletonDrawerCompat.draw_skeleton(frame, landmarks, show_joints=True)


def main() -> None:
    EMBED_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)

    probe_files = sorted(
        path for path in PROBES_DIR.glob("probe_*.json")
        if path.stem != "probe_report"
    )
    if not probe_files:
        print("No probe JSON files found. Run generate_motion_probes.py first.")
        return

    generator = EmbeddingGenerator()
    summary = {"probes": {}, "pair_checks": {}}

    for probe_path in probe_files:
        with open(probe_path) as f:
            sig = json.load(f)

        frames = sig.get("pose_data", [])
        meta = sig.get("metadata", {})
        width = meta.get("frame_width", 640)
        height = meta.get("frame_height", 480)

        frame_issues = []
        for idx, frame in enumerate(frames):
            issues = _check_frame(frame)
            if issues:
                frame_issues.append({"frame": idx, "issues": issues})

        landmarks_frames = extract_landmarks_from_signature(sig, frame_width=width, frame_height=height)
        if landmarks_frames:
            first = _render_frame(landmarks_frames[0], width, height)
            last = _render_frame(landmarks_frames[-1], width, height)
            cv2.imwrite(str(RENDER_DIR / f"{probe_path.stem}_first.png"), first)
            cv2.imwrite(str(RENDER_DIR / f"{probe_path.stem}_last.png"), last)

        # _compute_signature_embedding returns {'joint': array, 'combined': array}
        # Use the combined stream — same 4-stream embedding the recognition engine will use
        result = generator._compute_signature_embedding(str(probe_path))
        embedding = result['combined'] if result is not None else None
        if embedding is not None:
            np.save(EMBED_DIR / f"{probe_path.stem}.npy", embedding)

        summary["probes"][probe_path.stem] = {
            "frames": len(frames),
            "issues": frame_issues,
            "embedding_saved": embedding is not None,
        }

    # Pairwise checks — Layer C: collect strict alarm pairs as we go
    strict_alarm_pairs: List[Tuple[str, str, float]] = []
    monitoring_high_pairs: List[Tuple[str, str, float]] = []
    strict_set = set(STRICT_PAIR_CHECKS)

    for a, b in PAIR_CHECKS:
        a_path = EMBED_DIR / f"probe_{a}.npy"
        b_path = EMBED_DIR / f"probe_{b}.npy"
        if a_path.exists() and b_path.exists():
            a_vec = np.load(a_path)
            b_vec = np.load(b_path)
            score = _cosine(a_vec, b_vec)
            summary["pair_checks"][f"{a}_vs_{b}"] = float(score)
            if score > ALARM_THRESHOLD:
                if (a, b) in strict_set:
                    strict_alarm_pairs.append((a, b, score))
                else:
                    monitoring_high_pairs.append((a, b, score))
        else:
            missing = [p.stem for p in (a_path, b_path) if not p.exists()]
            print(f"  ⚠  Skipping {a}_vs_{b}: embedding(s) not found: {missing}")

    with open(PROBES_DIR / "probe_report.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Probe evaluation complete.")
    print(f"Report: {PROBES_DIR / 'probe_report.json'}")

    # Monitoring pairs — high similarity expected with GAP (known Phase 5 limitation)
    if monitoring_high_pairs:
        print("\n📊 Monitoring pairs (high similarity expected with GAP — will improve in Phase 5):")
        for a, b, sim in monitoring_high_pairs:
            print(f"   {a} ↔ {b}: {sim:.4f}")

    # Layer C: Strict alarm — exit if directional probes are indistinguishable (data/code bug)
    if strict_alarm_pairs:
        print("\n⚠️  PROBE SIMILARITY ALARM — strict pairs score >{:.0%} (MUST be distinct):".format(ALARM_THRESHOLD))
        for a, b, sim in strict_alarm_pairs:
            print(f"   {a} ↔ {b}: {sim:.4f}")
        print("Re-examine these probe shapes — they should produce clearly different embeddings.")
        sys.exit(1)


if __name__ == "__main__":
    main()
