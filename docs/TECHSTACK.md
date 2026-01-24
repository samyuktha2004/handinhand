# Technical Stack Documentation

## Overview

This document outlines all technologies used in the HandInHand Sign Language Recognition system. Updated with each iteration alongside PRD and Progress docs.

**Review Cycle:** PRD → TECHSTACK → Progress (checked every iteration)

---

## ✅ IMPLEMENTED (Phase 1-2: Data Extraction & Recognition)

### 1. **Landmark Extraction & Pose Detection**

- **Webcam pose capture** — **MediaPipe Holistic**: Real-time performance, 33 body landmarks + hand + face keypoints, minimal latency for live recognition.
- **Frame processing** — **OpenCV (cv2)**: Industry-standard for video I/O, frame manipulation, pre-processing; seamless MediaPipe integration.
- **Image handling** — **Pillow**: Lightweight processing for signature visualization and thumbnail generation.

### 2. **Machine Learning & Embeddings**

- **Vector similarity matching** — **NumPy + SciPy**: Fast cosine similarity computation, efficient multi-dimensional array operations.
- **Dimensionality reduction** — **Scikit-Learn**: Standardization, normalization, potential PCA for embedding optimization.
- **Numerical computing** — **NumPy**: Foundation for all ML operations; optimized C-based linear algebra.
- **Statistical analysis** — **Pandas**: Dataset validation, concept mapping management, cross-lingual alignment tracking.

### 3. **Data & Signatures Management**

- **Signature storage** — **JSON**: Human-readable, auditable, version-controllable; stores MediaPipe landmarks as coordinate arrays.
- **Metadata tracking** — **JSON + Pandas**: Concept mappings, translation maps, frame ranges in structured, queryable format.
- **Embeddings storage** — **NumPy (.npy files)**: Binary format; fast load/save; preserves precision for cosine similarity.

### 4. **Video Data Pipeline**

- **YouTube dataset download** — **yt-dlp**: Maintained fork of youtube-dl; reliable WLASL dataset handling with automatic format selection.
- **Video parsing** — **OpenCV (cv2)**: Frame extraction, frame counting, video integrity verification.
- **Orchestration** — **Custom Python (wlasl_pipeline.py)**: Download → landmark extraction → signature generation in one workflow.

### 5. **Debug & Signature Verification (Phase 2A)**

- **Static analysis charts** — **Matplotlib**: Cosine similarity scores, embedding distributions for quick debugging.
- **Real-time skeleton overlay** — **OpenCV (cv2)**: Ghost visualization comparing live vs. stored pose in recognition engine debug mode.
- **2D Stickman Skeleton Debugger** — **OpenCV (cv2.line)**: `skeleton_drawer.py` + `skeleton_debugger.py` visualize body/hand motion; dual-signature player displays ASL vs BSL side-by-side or toggled; verifies frame synchronization, body-centric normalization, hand shapes, and movement quality; supports normalization toggle and joint visualization.

### 6. **Development & Execution**

- **Python version** — **Python 3.10+**: Type hint support, performance improvements; MediaPipe requires 3.8–3.12 (3.13+ needs workaround).
- **Dependency management** — **pip + requirements.txt + venv**: Lightweight, reproducible, isolated environments.
- **Project structure** — **pyproject.toml**: Modern Python packaging standard; centralizes build, test, metadata configs.

---

## 🚀 FUTURE (Phase 3+: Avatar Rendering & Real-Time Streaming)

### 7. **Real-Time Backend-to-Frontend Communication** (Phase 3)

- **Python-to-Frontend bridge** — **Socket.io (python-socketio)**: Event-driven architecture; bidirectional communication for live recognition results to React frontend.
- **Engine compatibility** — **Python-EngineIO**: Lower-level transport layer; enables polling and WebSocket fallbacks for reliability.

### 8. **Avatar Rendering & 3D Animation** (Phase 3)

- **Web 3D rendering** — **Three.js**: WebGL-based, performant avatar animation in browser; de facto web 3D standard.
- **VRM avatar models** — **@pixiv/three-vrm**: Standardized humanoid format; bone-rigging simplifies motion capture replay on 3D models.
- **Avatar design & creation** — **VRoid Studio**: Free, user-friendly VRM creation; produces optimized models for real-time web rendering.

### 9. **Frontend Application** (Phase 3+)

- **React framework**: Component-based UI for webcam input, recognition display, avatar visualization.
- **Styling/Build tools**: Vite or Webpack for fast build and HMR (Hot Module Reloading).

---

## Architecture Layers

### Current State (Phases 1-2)

```
Layer 1: DATA EXTRACTION ✅
  └─ WLASL_v0.3.json → yt-dlp → MediaPipe Holistic → JSON Signatures

Layer 2: CONCEPT MAPPING ✅
  └─ translation_map.json (concept IDs, semantic vectors, ASL↔BSL mappings)

Layer 3: RECOGNITION ENGINE ✅
  └─ Live webcam → Normalize → Embedding → Cosine Similarity → Match
```

### Future (Phase 3+)

```
Layer 4: REAL-TIME OUTPUT 🚀
  └─ Socket.io → React Frontend → Three.js + @pixiv/three-vrm Avatar
```

---

## Performance & Deployment Targets

| Aspect                  | Technology            | Target                                            |
| ----------------------- | --------------------- | ------------------------------------------------- |
| **Storage efficiency**  | JSON + .npy files     | ~20–100 KB per signature vs. 10 MB per raw video  |
| **Frame processing**    | MediaPipe + NumPy     | <50ms per frame on modern hardware                |
| **Recognition latency** | Cosine similarity     | <500ms end-to-end                                 |
| **Scalability**         | Python + JSON config  | Add new concepts without code changes             |
| **Deployment model**    | Local-first, no cloud | All processing on-device; no external ML services |

---

## Version History

| Date             | Changes                                                                                                                                                                                                                                                                                                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Jan 24, 2026** | **Phase 2A** — Skeleton Debugger implemented: `skeleton_drawer.py` (landmark→skeleton converter with body/hand connections, color-coded joints) + `skeleton_debugger.py` (dual-signature viewer with side-by-side/toggled display, frame sync verification, normalization toggle). Ready for visual validation of ASL/BSL signature pairs. |
| **Jan 2026**     | Phase 1-2 foundation (Landmark Extraction, Recognition Engine). Phase 3 (Avatar Rendering, Socket.io) moved to Future.                                                                                                                                                                                                                     |

---

## Future Tech Considerations

- **Linear Algebra** (Phase 4): Procrustes alignment for ASL↔ISL transformation matrix.
- **Edge Optimization** (Phase 4+): ONNX model export for lightweight deployment.
- **Testing Framework** (Phase 2+): pytest for automated validation of embeddings and cosine similarity thresholds.
- **Performance Profiling** (Phase 3+): Memory optimization for WebSocket streaming of live embeddings.
