# HandInHand Progress Checklist

**Last Updated**: 2026-01-30

---

## Development Strategy: Skeleton-First

**Principle:** Perfect the skeleton visualizer before adding avatars. The avatar is just "skin on skeleton."

### Why Skeleton-First

- ✅ Recognition logic 100% independent of rendering
- ✅ Faster iteration (no VRM/3D complexity)
- ✅ Easier debugging (see exactly which landmarks are wrong)
- ✅ Lighter runtime (no Three.js, works on low-end devices)
- ✅ Avatar becomes swappable skin layer

### Risk Mitigations

| Risk                                 | Mitigation                                                  |
| ------------------------------------ | ----------------------------------------------------------- |
| Looks "unfinished" to stakeholders   | Label as "Developer Mode" / "Debug View" in UI              |
| Facial expressions harder to read    | Use landmark shapes + color coding (see Sign-MT approach)   |
| Avatar integration surprises         | Define adapter interface early (landmarks → bone rotations) |
| Occlusion/foreshortening differences | Test with 2D + 3D views before avatar integration           |

---

## Roadmap Overview

```
Phase 1: Perfect the skeleton ◄── YOU ARE HERE
├── Fix landmark connectivity
├── Draw all body segments properly
├── Ensure hands attach to wrists
├── Add Sign-MT style visualization
└── Smooth temporal jitter

Phase 2: Bidirectional translation
├── ASL ↔ BSL concept mapping
├── Embedding interpolation
└── Real-time pipeline

Phase 3: Avatar = "apply skin"
├── VRM loader
├── Retarget landmarks → bone rotations
└── Multiple avatar support
```

---

## Current Phase: Landmark Quality Filtering

### Landmark Quality Filtering 🔄 IN PROGRESS

#### Phase 1: Visibility Filtering ✅ COMPLETE

- [x] Add `VISIBILITY_THRESHOLD = 0.5` constant
- [x] Modify `extract_landmarks()` to check visibility
- [x] Mark low-visibility landmarks as `[0,0,0]`
- [x] Add `is_frame_quality_good()` method
- [x] Add `check_skeleton_connectivity()` method
- [x] Add window quality gate in `compute_embedding()` (70% good frames)
- [x] Use masked averaging (ignore zeros)
- [ ] Update `generate_embeddings.py` with same logic (optional)

#### Phase 2: Skeleton Connectivity ✅ COMPLETE

- [x] Define `LIMB_CONNECTIONS` constant (5 limb pairs)
- [x] Add "both endpoints valid" check per limb
- [x] Window quality gate integrated

#### Phase 3: Motion Validation (Future)

- [ ] Add velocity clipping on 3D coordinates
- [ ] Optional: Proportional neighbor distance check

---

## Core Recognition ✅ COMPLETE

- [x] MediaPipe landmark extraction
- [x] Signature storage (JSON format)
- [x] Embedding generation (Global Average Pooling)
- [x] Recognition engine (Cosine similarity)
- [x] Recognition quality: **0.7339 average** ✅

---

## Recognition Engine Refactor ✅ COMPLETE

- [x] Created `recognition_base.py` (shared logic)
- [x] Refactored `recognition_engine.py` (524 → 183 lines)
- [x] Refactored `recognition_engine_ui.py` (850 → 561 lines)
- [x] Total: 1373 → 1011 lines (26% reduction)

---

## Phase 2: Reference Body & Scaling ✅ MOSTLY COMPLETE

- [x] Create reference body visualization (`show_reference_body.py`)
- [x] Define body proportions (SHOULDER_WIDTH=100, ARM_LENGTH=100)
- [x] Implement 21-point hand structure (MediaPipe compatible)
- [x] Add palm connections (MCP joints: 5→9→13→17)
- [x] Fix thumb positions (correct biological sides)
- [x] Fix arm ratios (anatomically accurate: upper 55%, forearm 45%)
- [x] Add "chest" position for signing near face/body
- [x] Add neck connection to head
- [x] Add oval face with simplified features (eyes, eyebrows, mouth)
- [x] Assess face embedding integration (see TECH_LEAD_ASSESSMENT.md Appendix B)
- [x] Document reference body purpose and integration points
- [ ] **CRITICAL: Apply reference body scaling to `skeleton_drawer.py`**
- [ ] **CRITICAL: Update `skeleton_debugger.py` to use SHOULDER_WIDTH normalization**
- [ ] Verify all positions visually
- [ ] Test with ASL signatures (hello, go, where, you)
- [ ] Test with BSL signatures
- [ ] Confirm hands stay in frame across all signs

### Phase 3: Embedding Normalization ✅ COMPLETE

- [x] Shoulder-width scaling in `generate_embeddings.py`
- [x] Shoulder-width scaling in `recognition_engine.py`
- [x] Regenerate embeddings
- [x] Verify recognition quality unchanged (0.7339)

### Phase 4: Augmentation 🔄 PARTIAL

- [x] Create `augment_signatures.py`
- [x] Generate 15 augmented signatures (mirrored, variations)
- [ ] Integrate augmented signatures into embeddings
- [ ] Test recognition improvement

### Phase 5: Face & Expression (FUTURE)

- [ ] Add 468 face landmarks
- [ ] Assess impact on recognition
- [ ] Palm orientation indicator (Z-coordinate)

---

## Skeleton Visualizer Improvements 🔄 TODO

**Learnings from Sign-MT Reference:**

### Face Rendering

- [ ] Draw face as shapes not dots (eyes with lids, eyebrows, lips contour)
- [ ] Nose outline (subtle, non-distracting)
- [ ] Eyebrow position/shape for non-manual markers

### Hand Rendering

- [ ] Color-code each finger (5 distinct colors)
- [ ] Draw palm→fingertip connecting lines for all 5 fingers
- [ ] Left hand / right hand color distinction

### Body Rendering

- [ ] Trapezoid torso (simple, effective)
- [ ] Shoulder→elbow→wrist lines (currently missing!)
- [ ] Keep neck connection (we have it, they skip it—see tradeoffs below)

### Rendering Quality

- [ ] Anti-aliased lines (smooth, not jagged)
- [ ] Larger joint dots during debug mode
- [ ] Option to toggle "debug mode" vs "clean mode"

### Debug Mode Features

- [ ] Show landmark indices on hover/click
- [ ] Highlight low-confidence landmarks in red
- [ ] Show skeleton connectivity issues visually

### Design Tradeoffs: Our Choices vs Sign-MT

| Our Approach       | Sign-MT        | Why We Keep Ours                        | Why They Skipped                                         |
| ------------------ | -------------- | --------------------------------------- | -------------------------------------------------------- |
| Neck connection    | Floating face  | Anatomical accuracy, smooth transitions | No MediaPipe neck landmark; hides face↔pose misalignment |
| Debug dots         | Shapes only    | Essential during development            | End-user optimized                                       |
| Explicit arm lines | Trapezoid body | Clear arm position visibility           | Hides occlusion issues                                   |

### Potential Issues to Watch

- [ ] **Neck jitter** - Test fast head turns; may need smoothing or max-stretch clamp
- [ ] **Face-pose misalignment** - Test profile views; may need offset tolerance
- [ ] **Arm occlusion** - Test crossed arms/hands-on-face signs; may need Z-order or opacity
- [ ] **Fast motion jitter** - Test fingerspelling; add temporal smoothing if needed

---

## Quick Commands

```bash
# Verify recognition
python3 test_recognition_quality.py

# View reference body
python3 show_reference_body.py

# Test skeleton debugger
python3 skeleton_debugger.py --lang1 asl --sig1 hello_0 --lang2 bsl --sig2 hello --dual

# Regenerate embeddings (after changes)
python3 generate_embeddings.py
```

---

## Metrics to Track

| Metric                 | Target     | Current | Status        |
| ---------------------- | ---------- | ------- | ------------- |
| Recognition Average    | ≥0.70      | 0.7339  | ✅            |
| ASL-BSL Similarity     | ≥0.85      | 0.2973  | ⚠️ Needs work |
| Arm Length Consistency | ≤20px diff | 9px     | ✅            |
| Blue Dot               | None       | TBD     | 🔄            |

---

## Terminal Guidelines

⚠️ **DO NOT USE**:

- Heredoc (`<< 'EOF'` or `<< SCRIPT`) - causes terminal corruption
- Long inline Python with `-c` - escaping issues

✅ **DO USE**:

- Create `.py` script file, then run it
- Simple one-line commands only
