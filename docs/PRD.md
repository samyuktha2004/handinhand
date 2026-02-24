# Product Requirements Document: LinguaSign AI (MVP)

## 1. Project Overview

**Goal:** A bidirectional Sign-to-Sign translator (eg: ASL <-> ISL) using 3D avatars.
**Innovation:** Gloss-free "Embedding Route" (Vector Mapping) to preserve Non-Manual Signals (NMS) and grammar.

## 2. Target Audience

- Deaf individuals communicating across different national sign languages.
- Novice developers building an ML prototype using open-source tools.

## 3. Technical Stack (The "How")

- **Vision:** MediaPipe Holistic (Landmark Extraction).
- **ML Logic:** Vector Cosine Similarity (Comparing current landmarks to saved JSON signatures).
- **Frontend:** React + Three.js + @pixiv/three-vrm.
- **Avatar:** VRoid Studio (.vrm models).
- **Communication:** Socket.io (Python Backend to React Frontend).

## 4. Roadmap (Unified Phases)

One phase structure, used across all docs.

| Phase | Name | Status | Delivers |
|-------|------|--------|----------|
| 1 | Foundation | ✅ Complete | WLASL pipeline, 3-tier quality system, 4 concepts × 2 languages |
| 2 | Recognition Engine | ✅ Complete | Embeddings, cosine matching, 4-tier validation, temporal smoothing |
| 3 | Rendering & Cleanup | 🔄 In Progress | Reference body, probe fixes, facial landmarks, codebase cleanup |
| 4 | Live Foundation | 📋 Next | Wire combined embeddings + live webcam test + Procrustes pilot validation |
| 5 | Temporal Foundation | 📋 Planned | Lightweight temporal encoding (positional + attention) — required before vocab scale |
| 6 | Avatar MVP | 📋 Planned | React + Three.js + VRM avatar, Socket.io — **first live demo** |
| 7 | Language & Scale | 📋 Future | 20+ concepts, JSL/CSL/LSF, Procrustes deployment, REST API |

**MVP success gate:** Phase 6 complete — a person signs ASL HELLO on webcam → avatar plays BSL HELLO.

**Why Phase 5 before Avatar:** Without temporal ordering, adding >20 signs creates ambiguity — the demo would fail as vocabulary grows. Temporal Foundation (lightweight attention over frames, ~50-100 lines) ensures the Phase 6 avatar is built on a foundation that scales.

## 5. Success Metrics

- System correctly recognizes "HELLO" and triggers the avatar animation within < 500ms.
- Project is fully local-first (no dependence on RPM/cloud servers).

## 6. Skeleton & Embedding (Summary)

Acceptance criteria (PRD-level):

Note: full technical change logs and engineering stack updates are kept in `docs/STACK_UPDATES.md`. The PRD contains a high-level summary only, not an exhaustive changelog.
