# Tech Stack — HandInHand

Last updated: 2026-02-26

This document is the authoritative reference for technology decisions across all phases. Each choice is validated against alternatives. Update when architectural decisions change.

---

## Validated Stack Decisions

### Vision & Pose Estimation — MediaPipe Holistic

**What it does:** Extracts skeleton landmarks in real time — 33 body, 21 per hand, 468 facemesh points. We select a compact 55-point subset: 6 body (shoulders/elbows/wrists) + 21 left hand + 21 right hand + 7 face.

**Why MediaPipe over alternatives:**

| Attribute | MediaPipe Holistic | OpenPose | MMPose |
|---|---|---|---|
| Speed | 30+ FPS on CPU | 5-15 FPS, GPU required | 10-25 FPS, GPU preferred |
| Hands (fingers) | Full 21 kp/hand | Not supported | Via separate model |
| Face | 468-point mesh, select any | Limited | Via separate model |
| Failure mode | Entire group missing at once | Individual keypoints missing | Varies |
| Setup | One pip install | CUDA + complex build | Research codebase |
| Maintenance | Google active | Community only (no new releases) | OpenMMLab active |
| Sign language use | Dominant in 2024-25 research | Legacy research only | Research/academic |

**Why the "entire hand missing" failure mode is acceptable:** Our Layer A embedding quality gate (Phase 4) suppresses recognition when >30% of window frames are zero. A catastrophic detection failure returns `None` instead of a spurious match. OpenPose's per-keypoint failures would silently corrupt embeddings with no way to detect them.

**Version pinning:** MediaPipe 0.10.x requires Python 3.12. Python 3.13 is incompatible.

---

### Embedding Engine — NumPy + SciPy (no ML framework)

**What it does:** 4-stream geometric embedding — joint coordinates, bone vectors, joint motion deltas, bone motion deltas — concatenated and pooled to 512 dimensions.

**Why no ML framework (PyTorch/TensorFlow):**

| Attribute | NumPy/SciPy (current) | PyTorch | TensorFlow |
|---|---|---|---|
| Install size | ~30 MB | ~1.5 GB | ~2 GB+ |
| Phase 5 temporal attention | Implementable in ~50 lines | Works but overkill | Overkill |
| Training support | None needed yet | Full | Full |
| Deployment | Simple pip install | CUDA management required | CUDA management required |

**When to add PyTorch:** Only if Phase 7 requires training a discriminative embedding model at >100-concept vocabulary. For Phases 1-5, NumPy/SciPy is correct.

**Phase 5 temporal attention:** The upgrade from Global Average Pooling to lightweight attention is implementable as pure NumPy — softmax over frame-level dot products. No new dependency.

---

### Recognition — Cosine Similarity via SciPy

**What it does:** `scipy.spatial.distance.cosine` scores each live embedding against all stored concept embeddings. Tier 4 validation then checks confidence threshold (0.80) and gap between best/second-best (0.15).

**Scalability:** Per-pair loop is adequate at 4-50 concepts (<1ms). At 100+ concepts, switch to `sklearn.metrics.pairwise.cosine_similarity` for vectorized matrix scoring — no new dependency, sklearn is already in the stack.

---

### Backend Server — FastAPI + python-socketio (Phase 6)

**What it does:** FastAPI serves REST endpoints; python-socketio handles real-time frame streaming from Python recognition engine to browser avatar.

**Why FastAPI over Flask:**

| Attribute | FastAPI | Flask |
|---|---|---|
| Async native | Yes (ASGI) | No (WSGI) |
| WebSocket | Yes (via Starlette) | Plugin required |
| Auto OpenAPI docs | Yes | No |
| Overhead | Low | Very low |

`python-socketio` is already in `pyproject.toml`. Add `fastapi` and `uvicorn` when Phase 6 begins.

**Socket.IO version alignment (critical):** `python-socketio 5.x` uses Socket.IO protocol v4. The JavaScript client must be `socket.io-client ^4.7.x`. Version 3.x is incompatible with the protocol.

---

### Frontend & Avatar — React + Three.js + @pixiv/three-vrm + Vite (Phase 6)

**What it does:** Browser-based signing avatar. Three.js renders the 3D scene; three-vrm provides humanoid bone control (fingers, wrists, face); Vite builds the frontend.

**Why this stack over alternatives:**

| Attribute | Three.js + three-vrm | Babylon.js | A-Frame | SMPL-X (research) |
|---|---|---|---|---|
| Humanoid avatar | VRM standard | Via glTF | VR-focused | Yes, but no web SDK |
| Full bone control | Fingers + wrists + face | Yes | Limited | Yes |
| Open format | VRM (open spec) | glTF | glTF | Proprietary mesh |
| VRoid Studio export | Direct VRM | Not supported | Not supported | Not supported |
| Web deployment | Production-ready | Production-ready | Production-ready | Requires custom shaders |

**Why not SMPL-X:** Used in ECCV 2024 sign language research for academic demos, but requires specialized WebGL shaders for the 10,475-vertex mesh. No web-deployable SDK exists. Three.js + VRM is the production-viable choice.

**Version spec (lock before Phase 6 starts):**

| Package | Version |
|---|---|
| three | ^0.169.0 |
| @pixiv/three-vrm | ^3.1.0 (peer dep: three r150+) |
| socket.io-client | ^4.7.5 (matches python-socketio 5.x) |
| react + react-dom | ^18.3.0 |
| Build tool | Vite ^6.x |
| TypeScript | ^5.x (required for three-vrm type safety) |
| Node.js | >=20 LTS |

---

### Cross-Lingual Alignment — Procrustes via SciPy (Phase 7)

**What it does:** `scipy.linalg.orthogonal_procrustes` finds the optimal rotation+scale transform aligning the ASL embedding space to the BSL embedding space using anchor concept pairs.

**Why Procrustes over NLP-style alignment (VecMap/MUSE):** NLP systems use 5,000 anchor pairs because word embedding spaces are arbitrary. Our embedding space is physically grounded in 3D body movement — the alignment transform is closer to a rigid rotation, so fewer anchors (10-15) should suffice.

**Validation requirement:** Pilot in Phase 4 with 4 anchor pairs. Test on held-out 5th concept. If generalization fails, expand to 10-15 anchors before Phase 7 deployment.

**No new dependency needed:** SciPy is already in the stack.

---

## Current Dependency Versions (pyproject.toml)

| Package | Current constraint | Notes |
|---|---|---|
| Python | `>=3.12,<3.13` | 3.13 incompatible with MediaPipe 0.10.x |
| mediapipe | `^0.10.14` | Pin minor — 0.10.x is tested on Python 3.12 |
| numpy | `^1.26.0,<2.0.0` | 1.26 is latest stable 1.x; 2.0 has breaking changes |
| opencv-python | `^4.8.0` | Stable for real-time frame processing |
| scipy | `^1.11.0` | Cosine similarity + Procrustes in Phase 7 |
| scikit-learn | `^1.3.0` | Future vectorized scoring at 100+ concepts |
| python-socketio | `^5.9.0` | Socket.IO protocol v4 — JS client must be 4.x |

**Phase 6 additions (add to pyproject.toml when starting Phase 6):**

| Package | Version |
|---|---|
| fastapi | `^0.115.0` |
| uvicorn[standard] | `^0.32.0` |

---

## Architecture Limitations & Upgrade Triggers

| Limitation | Impact | Phase 5 upgrade | Phase 7 upgrade |
|---|---|---|---|
| Global Average Pooling loses motion order | Vocabulary cap ~20-50 signs | Replace with NumPy attention (~50 lines) | — |
| Cosine similarity per-pair loop | Speed cap at ~100 concepts | — | Switch to sklearn matrix form |
| 4 anchor pairs for Procrustes | May not fully constrain rotation | Expand to 10-15 anchor pairs | — |
| face: 4 signatures (raw videos unavailable) | Missing 3 mouth landmarks in current embeddings | Re-extract when raw videos available | — |

---

## What HandInHand Does NOT Use (and Why)

| Technology | Why not used |
|---|---|
| OCR (text recognition) | Not applicable — this is pose estimation, not text processing |
| English gloss intermediary | Deliberately avoided — preserves NMS, facial grammar, spatial indexing |
| GPU / CUDA | Not required for MediaPipe at 30 FPS; adds deployment complexity |
| LSTM / RNN | Replaced by simpler GAP for MVP; attention is the Phase 5 upgrade |
| Cloud inference | All processing local — no server dependency, lower latency |
| Docker (current) | Not needed yet; add for Phase 6 deployment if multi-machine needed |
