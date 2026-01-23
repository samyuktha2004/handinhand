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

## 4. Key Features (MVP Scope)
### Phase 1: Mocap & Embedding
- Capture (x, y, z) landmarks from webcam.
- Save "Golden Signatures" of 4 ASL and 4 ISL sentences as JSON files.

### Phase 2: Real-time Recognition
- Compare live webcam landmarks against JSON library.
- Use Cosine Similarity threshold (e.g., > 0.90) to trigger a match.

### Phase 3: Avatar Rendering
- Load a VRM character in a web browser.
- "Drive" the character's bones using coordinates from the JSON files.

## 5. Success Metrics
- System correctly recognizes "HELLO" and triggers the avatar animation within < 500ms.
- Project is fully local-first (no dependence on RPM/cloud servers).