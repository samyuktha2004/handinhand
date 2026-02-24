# HandInHand — What This Project Is and How It Works

**For:** Anyone who wants to understand this project — team members, collaborators, or curious readers
**Prepared:** February 24, 2026

---

## The Problem We're Solving

There are hundreds of sign languages in the world. American Sign Language (ASL) and British Sign Language (BSL) are completely different — a Deaf person from the US cannot automatically understand a Deaf person from the UK, even though both countries speak English. Today, there is no reliable technology that translates directly between sign languages in real time.

Most existing tools work like this: take a sign → convert it to written English → then try to produce the target sign. This approach loses critical meaning. Sign languages have their own grammar, expressed through facial expressions, head movements, and where in space you position your hands. None of that survives a round-trip through written English.

---

## The Big Idea

**HandInHand** skips the written-language detour entirely.

```
Person signs in ASL
        ↓
System reads body movement as coordinates
        ↓
Coordinates match to a concept (e.g., "GREETING")
        ↓
Concept maps to the equivalent BSL movement
        ↓
Animated avatar plays back the BSL sign
```

The technical term for this is **kinematics-to-kinematics translation**. The system talks directly between movement and movement, preserving the full richness of sign language — including facial expressions, head tilts, and hand shapes that carry grammatical meaning.

---

## How It Works — Step by Step

### Step 1: Capture movement
A regular webcam feeds into MediaPipe (a Google-built tool), which tracks 52 points on the person's body in real time:
- 21 points per hand (each finger joint)
- 6 body points (shoulders, elbows, wrists)
- 4 face points (eyebrows)

These are just (x, y, z) coordinates — pure numbers.

### Step 2: Create a fingerprint of each sign
Those coordinates get converted into a compact 512-number summary called an **embedding**. Think of it as a fingerprint for a sign. Every known sign has a pre-computed embedding stored in the system.

To make the fingerprint work across different body sizes and camera positions, all coordinates are first shifted so the shoulder center is at (0, 0, 0). This makes the fingerprint about the *shape and movement*, not the person's size or where they're standing.

### Step 3: Match the sign
When someone signs in front of the camera, the live coordinates become a new fingerprint. The system then asks: "Which stored fingerprint does this most closely resemble?" It uses a mathematical measure called **cosine similarity** to score every stored sign and find the best match.

### Step 4: Quality check (4-tier verification)
Before accepting a match, the system runs 4 quality gates:
1. Is the data format valid? (frame ranges make sense)
2. Is the duration realistic for a single sign? (20–400 frames)
3. Is the landmark detection quality high enough? (>80/100)
4. Is the best match clearly better than the second-best? (gap must be >0.15)

This prevents false positives and catches ambiguous detections before they cause errors.

### Step 5: Translate and play back
Once a match is confirmed, the system retrieves the BSL version of that sign and plays it back through an animated avatar.

---

## What's Been Built

### The Full Pipeline

```
YouTube (WLASL dataset — 2,000 sign library)
  ↓  wlasl_pipeline.py
Download video → extract only relevant frames → delete video (saves 98% storage)
  ↓  extract_signatures.py
MediaPipe landmarks → save as JSON "signature" (50–300 KB per sign)
  ↓  generate_embeddings.py
Normalize to shoulder center → average across frames → 512-dim vector (.npy file)
  ↓  recognition_engine.py
Live webcam → real-time matching → 4-tier validation → BSL concept identified
  ↓  skeleton_debugger.py / recognition_engine_ui.py
Visual display: side-by-side comparison of two signs
```

### Key Files

| File | What it does |
|------|-------------|
| `recognition_engine.py` | The brain — matches live signs to stored concepts |
| `generate_embeddings.py` | Converts landmark sequences into 512-dim fingerprints |
| `extract_signatures.py` | Reads body tracking data from videos |
| `wlasl_pipeline.py` | Downloads data, runs quality checks, organises files |
| `skeleton_renderer.py` | Draws an anatomically consistent body for visualization |
| `skeleton_debugger.py` | Side-by-side viewer to compare two signs |
| `translation_map.json` | Master list: ASL concept → BSL target |
| `assets/signatures/` | All stored sign fingerprint data (JSON) |
| `assets/embeddings/` | The numeric summaries (.npy files) |

### Current Vocabulary

| Sign | Concept | Languages | Status |
|------|---------|-----------|--------|
| HELLO | Greeting | ASL → BSL | Working ✅ |
| YOU | 2nd person pronoun | ASL → BSL | Working ✅ |
| WHERE | Location question | ASL → BSL | Working ✅ |
| GO | Directional motion | ASL → BSL | Marginal ⚠️ |

4 words. 2 languages. Recognition accuracy ~91%.

### Recognition Performance

| Concept | ASL vs BSL Similarity Score | Result |
|---------|----------------------------|--------|
| HELLO | 0.7148 | Languages are clearly distinct ✅ |
| YOU | 0.7763 | Languages are clearly distinct ✅ |
| WHERE | 0.5931 | Languages are clearly distinct ✅ |
| GO | 0.8515 | Borderline — watch for false positives ⚠️ |
| **Average** | **0.7339** | **Below the 0.80 threshold — good ✅** |

Lower score = better (means the two languages look more different from each other, so the system can tell them apart).

---

## Phase-by-Phase Progress

### ✅ Phase 1 — Foundation (Complete)
- Python environment set up with MediaPipe, NumPy, OpenCV, and all dependencies
- WLASL dataset integrated (access to 2,000 sign library)
- 4 concepts extracted across 2 languages (9 ASL instances + 4 BSL targets)
- 3-tier automated data quality verification system
- All signatures organized into language-specific folders

### ✅ Phase 2 — Recognition Engine (Complete)
- Real-time cosine similarity matching against stored embeddings
- 4-tier validation system (including cross-concept confidence gap)
- Temporal smoothing reduced false positives from 8% down to <1%
- Skeleton debugger visualization tool
- 6/6 automated tests passing

### 🔄 Phase 3 — Rendering & Cleanup (In Progress)
- Anatomically proportioned reference body renderer
- Motion probes for testing embedding quality
- Facial landmark integration in progress
- Codebase cleanup (30+ debug scripts to remove)
- Known issue: probe embeddings too similar (0.9983 open/close) — data problem: probes use full-body translation which shoulder-centering cancels. Fix in progress: regenerate probes with relative hand movement

### 📋 Phase 4 — Live Foundation (Next)
- Wire 4-stream combined embeddings into recognition engine (already coded, not yet connected)
- First live webcam test of the recognition engine
- Procrustes pilot: validate cross-lingual alignment on a held-out 5th concept

### 📋 Phase 5 — Temporal Foundation (Planned)
- Replace Global Average Pooling with lightweight temporal attention (~50-100 lines in generate_embeddings.py)
- Frame-level embeddings with positional encoding → attention pooling
- Required before vocabulary can scale reliably past 20 signs
- Learning from SAM-SLR: even simple temporal context improves accuracy 15%+

### 📋 Phase 6 — Avatar MVP (Planned)
- React + Three.js + VRM avatar in web browser
- Python backend → Socket.io → frontend
- Avatar bones driven by BSL JSON signatures
- **Milestone: sign ASL HELLO → avatar plays BSL HELLO**

### 📋 Phase 7 — Language & Scale (Future)
- Add JSL (Japanese), CSL (Chinese), LSF (French Sign Language)
- Expand vocabulary to 20+ then 100+ signs
- Full Procrustes deployment (10-15 anchor pairs, validated on held-out concepts)
- REST API + production deployment

---

## What the Research Says

This project has reviewed 10 academic papers on skeleton-based sign language recognition. Key findings:

**The approach is validated.** SAM-SLR (1st place at CVPR 2021 challenge) uses the same skeleton-embedding method and achieves 95% accuracy on 500+ signs.

**The main gap is temporal features.** The current system converts each sign to a single average vector (Global Average Pooling). This loses information about *how the sign moves through time*. Research shows that adding:
- **Bone vectors** (direction from joint to joint)
- **Motion deltas** (how each joint moved frame-to-frame)

...can lift accuracy from ~63% to 95%+ when vocabulary expands. This is the most important architectural upgrade needed before scaling.

**Landmark reduction helps.** SAM-SLR found that reducing from 133 landmarks to 27 key nodes improved accuracy dramatically. The current 52-node model is reasonable, but future optimization should focus on the most linguistically meaningful joints.

---

## Technical Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Vision | MediaPipe Holistic | Body tracking (52 landmarks) |
| Language | Python 3.12 | Core engine |
| Similarity | SciPy cosine similarity | Sign matching |
| Data | NumPy .npy files | Embedding storage |
| Video | OpenCV | Frame capture |
| Data source | WLASL + yt-dlp | Sign language dataset |
| Frontend (planned) | React + Three.js + VRM | Avatar display |
| Communication (planned) | Socket.io | Backend → frontend |

---

## What's Missing (Honest)

1. **No live webcam test yet.** The engine works on stored signatures. It has not been validated on a real webcam with a real signer in real conditions.

2. **Avatar frontend hasn't started.** The visible output that a user would see is completely missing. Right now the system prints text to a terminal.

3. **BSL data is thin.** Only 1 BSL signer per concept. Multiple ASL signers exist, but BSL targets are single instances.

4. **Codebase has accumulated clutter.** 30+ diagnostic and debug scripts from past iterations that need to be cleaned up.

5. **4-stream combined embedding not yet wired to recognition engine.** The upgrade is already coded in `generate_embeddings.py` (bone vectors + motion deltas save to `_combined.npy`), but `recognition_engine.py` still loads the old joint-only embeddings. Wiring this is the first Phase 4 task.

---

## What Needs to Happen Next

In order of priority:

1. **Codebase cleanup** — remove 30+ debug scripts, keep the 6 core files
2. **Fix visualization display** — one clean fix, then leave it alone
3. **Test live on a webcam** — this is the most critical missing validation
4. **Wire the combined embedding** — the 4-stream upgrade is already coded in `generate_embeddings.py`, just needs to be connected to `recognition_engine.py` (update registry + live embedding function)
5. **Build a minimal avatar frontend** — even a stick figure in the browser is a product
6. **Expand to 20 concepts** — the architecture is ready, just configuration changes
7. **Add more BSL signers** — improve translation ground truth

---

## The Core Assessment

The architecture is technically sound and grounded in peer-reviewed research. The data quality infrastructure is genuinely well-engineered. The documentation is thorough.

The main challenge going forward is focus: the project needs to move toward a user-visible live demonstration rather than continuing to refine the debugging tools. The single most valuable milestone is:

> A person signs HELLO in ASL in front of a webcam → the system recognises it → an avatar plays back the BSL equivalent.

Everything else — more words, better probes, cleaner display code — is secondary to achieving that first moment of working magic.

---

*Project: HandInHand / LinguaSign AI | Branch: feature/reference-body-improvements*
*Last reviewed: February 24, 2026*
