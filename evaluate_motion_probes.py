#!/usr/bin/env python3
"""Validate and embed motion probe signatures.

Steps:
1) Integrity checks on probe JSON
2) Render first/last frames to PNG
3) Compute embeddings and cosine similarities
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

from generate_embeddings import EmbeddingGenerator
from skeleton_renderer import SkeletonDrawerCompat, extract_landmarks_from_signature

PROBES_DIR = Path("assets/probes")
EMBED_DIR = PROBES_DIR / "embeddings"
RENDER_DIR = PROBES_DIR / "renders"

PAIR_CHECKS = [
    ("up", "down"),
    ("left", "right"),
    ("open", "close"),
    ("spread", "close"),
    ("pinch", "close"),
]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _check_frame(frame: Dict) -> List[str]:
    issues = []
    for key, expected in [("pose", 6), ("left_hand", 21), ("right_hand", 21), ("face", 4)]:
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

        embedding = generator._compute_signature_embedding(str(probe_path))
        if embedding is not None:
            np.save(EMBED_DIR / f"{probe_path.stem}.npy", embedding)

        summary["probes"][probe_path.stem] = {
            "frames": len(frames),
            "issues": frame_issues,
            "embedding_saved": embedding is not None,
        }

    # Pairwise checks
    for a, b in PAIR_CHECKS:
        a_path = EMBED_DIR / f"probe_{a}.npy"
        b_path = EMBED_DIR / f"probe_{b}.npy"
        if a_path.exists() and b_path.exists():
            a_vec = np.load(a_path)
            b_vec = np.load(b_path)
            summary["pair_checks"][f"{a}_vs_{b}"] = _cosine(a_vec, b_vec)

    with open(PROBES_DIR / "probe_report.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Probe evaluation complete.")
    print(f"Report: {PROBES_DIR / 'probe_report.json'}")


if __name__ == "__main__":
    main()
