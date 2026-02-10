# HandInHand — Functional Features Reference

This file documents features that are implemented and verified in the repository as of 2026-02-10. It is intentionally minimal: only fully functional features are included.

## Overview

- Purpose: Single-source reference for implemented capabilities, inputs/outputs, and acceptance criteria.

## Features

- **Skeleton Renderer (`skeleton_renderer.py`)**
  - Purpose: Render a fixed-proportion reference body and draw landmarks-driven poses.
  - Inputs: `landmarks` dict with `pose`, `left_hand`, `right_hand`, optional `face` arrays (pixel coordinates)
  - Outputs: RGB frame (numpy array)
  - Acceptance: Neutral fallback hand appears when hand data is missing; no hand/arm scale drift across probe motions; visual tests saved in `assets/test_render/`.

- **Skeleton Debugger (`skeleton_debugger.py`)**
  - Purpose: Interactive/snapshot viewer for comparing two signatures (or signature + probe).
  - Inputs: Signature JSON files in `assets/signatures/<lang>/<sig>.json` or built-in probe name via `--probe`
  - Outputs: OpenCV window or saved images (via `scripts/render_probe_frame.py`)
  - Acceptance: Toggle normalization (`n`) renders reference-aligned and raw views; side-by-side mode available (`--dual`).

- **Probe Generator (`generate_motion_probes.py`)**
  - Purpose: Generate diagnostic motion signatures (up/down/left/right/open/close/spread/pinch) for visual and embedding validation.
  - Outputs: JSON files in `assets/probes/probe_<name>.json`.
  - Acceptance: Probe frames render cleanly and preserve anatomical constraints.

- **Embedding Generator (multi-stream) (`generate_embeddings.py`)**
  - Purpose: Produce signature-level embeddings for recognition.
  - Streams: `joint` (flattened normalized joints), `combined` (joint + bone + joint_motion + bone_motion)
  - Outputs: Per-signature numpy files saved as `<concept>_joint.npy` and `<concept>_combined.npy`.
  - Acceptance: Embeddings are translation-invariant (validated by `scripts/check_embedding_invariance.py`).

- **Embedding Invariance Check (`scripts/check_embedding_invariance.py`)**
  - Purpose: Verify embedding pipeline is invariant to global translation and preserves missing-data masks.
  - Inputs: Probe JSON from `assets/probes`
  - Outputs: Console pass/fail and diagnostic values saved to stdout.
  - Acceptance: L2 difference ≈ 0 after translation; diagnostic printout present.

- **Embedding Ablation (`scripts/run_embedding_ablation.py`)**
  - Purpose: Compare ASL–BSL mean similarity using `joint` vs `combined` embeddings.
  - Inputs: Registry with generated `_joint` and `_combined` `.npy` files
  - Outputs: Mean similarity metrics printed to stdout for joint and combined embeddings.
  - Acceptance: Script runs and reports means when embeddings are present.

- **Utility render script (`scripts/render_probe_frame.py`)**
  - Purpose: Create static PNG of a probe frame for documentation and visual review.
  - Output: `assets/test_render/probe_<name>_frame0.png`

## Data Contracts

- Signature JSON: `pose_data` list of frames; each frame contains `pose` (6), `left_hand` (21), `right_hand` (21), `face` (4) in normalized coords (0..1) or pixel coords depending on loader.
- Embedding shapes: `_joint.npy` and `_combined.npy` are 512-d float vectors (padded/truncated as required).

## Validation & Tests (manual/automated)

- Visual: `assets/test_render/` contains probe renders and visual tests.
- Embedding: `scripts/check_embedding_invariance.py` ensures translation invariance.
- Ablation: `scripts/run_embedding_ablation.py` compares joint vs combined embeddings.


