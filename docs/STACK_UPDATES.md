# Stack Updates — HandInHand

Last updated: 2026-02-10

Overview

- Core runtime: Python 3.10+ (venv). Primary libs: `numpy`, `opencv-python`, `scipy`, `mediapipe` for landmark extraction.
- Embedding & storage: JSON signatures in `assets/signatures/` and `.npy` embeddings in `assets/embeddings/`.
- Frontend (planned): React + Three.js + three-vrm; Socket.io for comms.

Recent updates (actions taken)

- Introduced multi-stream embeddings (`joint` and `combined`) in `generate_embeddings.py`.
- Aligned normalization heuristics between `generate_embeddings.py` and `recognition_engine.py` (use first-two pose points as shoulder center, fallback to legacy indices).
- Tightened renderer biological checks in `skeleton_renderer.py` (elbow min, length ratios, palm validation).
- Added probe generation (`scripts/generate_motion_probes.py`) and visual checks (`scripts/render_probe_frame.py`).
- Added ablation script (`scripts/run_embedding_ablation.py`) to compare `_joint.npy` vs `_combined.npy`.

Recommended next infra updates

- Pin dependency versions (create `requirements-lock.txt` or use `pip freeze`) for reproducibility.
- Add lightweight CI job that runs:
  - `scripts/check_embedding_invariance.py`
  - `scripts/render_probe_frame.py` (smoke test)
- Consider exporting registries/embeddings to a small DB (sqlite/LMDB) for faster lookup in production.
- If training GCNs: add `torch` and GPU-aware tooling; consider ONNX export for inference.

Notes

- Keep MediaPipe as capture engine for MVP — best tradeoff for speed and robustness.
- No need for heavy infra until we determine model training requirements; keep stack lean for now.
