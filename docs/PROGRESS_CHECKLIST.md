# HandInHand Progress Checklist

**Last Updated**: 2026-02-10

---

## Reference Sources & Licensing

| Source                                     | License           | Can Use Code?              | Can Use Insights?              | Status      |
| ------------------------------------------ | ----------------- | -------------------------- | ------------------------------ | ----------- |
| **MediaPipe** (Google)                     | Apache 2.0        | ✅ Yes (with attribution)  | ✅ Yes                         | ✅ Reviewed |
| **pose-format**                            | MIT               | ✅ Yes (with attribution)  | ✅ Yes                         | ✅ Reviewed |
| **signwriting**                            | MIT               | ✅ Yes (with attribution)  | ✅ Yes                         | ⬜ Future   |
| **sign/translate**                         | CC BY-NC-SA 4.0   | ⚠️ Non-commercial only     | ✅ Insights only               | ✅ Reviewed |
| **RWTH-PHOENIX**                           | Academic          | ⬜ Check license           | ✅ Yes (cite paper)            | ⬜ Future   |
| **ASL-LEX**                                | Academic          | ⬜ Check license           | ✅ Yes                         | ⬜ Future   |
| **AndrewEntwistle Body Model** (Domestika) | Personal Use Only | ❌ No (proprietary ZBrush) | ✅ Architectural patterns only | ✅ Reviewed |

### Future Research TODOs

- **Body Model Integration (Post-MVP):** If advancing to realistic body meshes, contact Andrew Entwistle or Domestika (legal@domestika.org) for commercial usage rights. See [BODY_MODEL_INSIGHTS.md](BODY_MODEL_INSIGHTS.md) for details and [source link](https://www.domestika.org/en/blog/11350-free-library-of-resources-to-help-take-your-creature-design-to-the-next-level?exp_set=1).

## Development Strategy: Skeleton-First

**Principle:** Perfect the skeleton visualizer before adding avatars. The avatar is just "skin on skeleton."

- ✅ Recognition logic 100% independent of rendering
- ✅ Faster iteration (no VRM/3D complexity)
- ✅ Easier debugging (see exactly which landmarks are wrong)

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

### Files of Interest

- **Recognition engine implementation:** `recognition_engine.py` — core real-time capture/normalize/recognize loop (located in repo root). Status: production-ready for MVP, documented here for progress tracking.

### Docs & Stack

- **Stack updates summary:** `docs/STACK_UPDATES.md` (recent tech changes, CI recommendations)
- **Docs index:** `docs/README.md` — use this to find canonical docs. Keep `PROGRESS_CHECKLIST.md` as the engineering checklist; move long-form research to `docs/RESEARCH_INSIGHTS.md`.

---

## Recognition Engine Refactor ✅ COMPLETE

- [x] Created `recognition_base.py` (shared logic)
- [x] Refactored `recognition_engine.py` (524 → 183 lines)
- [x] Refactored `recognition_engine_ui.py` (850 → 561 lines)
- [x] Total: 1373 → 1011 lines (26% reduction)

---

## Phase 2: Reference Body & Scaling

- [x] Create reference body visualization (`show_reference_body.py`)
- [x] Define body proportions (SHOULDER_WIDTH=100, ARM_LENGTH=100)
- [x] Implement 21-point hand structure (MediaPipe compatible)
- [x] Add palm connections (MCP joints: 5→9→13→17)
- [x] Fix thumb positions (correct biological sides)
- [x] Fix arm ratios (anatomically accurate: upper 55%, forearm 45%)
- [x] Add "chest" position for signing near face/body
- [x] Add neck connection to head
- [x] Add oval face with simplified features (eyes, eyebrows, mouth)
- [x] Enforce elbow ROM + arm length constraints in reference body demo
- [x] Add hand pose modes in reference body demo (open/close/spread/pinch)
- [x] Clamp finger spread/spacing in reference body demo
- [x] Add finger coupling for pinch/close and thumb involvement
- [x] Add fist pose to reference body demo
- [x] Assess face embedding integration (see TECH_LEAD_ASSESSMENT.md Appendix B)
- [x] Document reference body purpose and integration points
- [x] **Apply reference body scaling** _(via skeleton_renderer.py)_
- [x] **SHOULDER_WIDTH normalization in skeleton_debugger.py** _(imports REFERENCE_SHOULDER_WIDTH)_
- [x] Verify all positions visually _(test_skeleton_renderer.py passes)_
- [x] Test with ASL signatures (hello, go, where, you) _(verified 2026-02-04)_
- [x] Test with BSL signatures _(verified 2026-02-04)_
- [x] Confirm hands stay in frame across all signs _(verified 2026-02-04)_
- [x] Switch finger colors to Wong palette (keep green body)
- [x] Align neutral hand to wrist/forearm angle (fallback should follow wrist direction)
- [x] Soften hand validation to avoid mid-frame dropouts (partial data should still render)
- [x] Dim gray segments/dots for incomplete fingers (no reconstruction)
- [ ] Add light-mode palette for accessibility (future)
- [ ] Optional: boxy/trapezoid torso (Sign-MT style) for reference body

### Handshape Priors (Merged)

- [x] Merge numeric handshape priors from Miozzo & Peressotti (2022) SI into project priors
  - File: `assets/handshape_priors/core_handshape_priors.json` (probabilities for ranks 1..35)
  - Loader helper: `scripts/priors_loader.py` (bias init, KL loss, sampler)
  - Status: merged for review — `h01..h35` kept as placeholder IDs; map to human labels later if desired

_Note: These priors are ready to be applied at model init (classifier bias) or as a training regularizer. If you prefer, I can add a small init/flag in `recognition_engine.py` to apply them non-invasively._

**Reference body hardening plan (execute before embedding work)**

- [x] Remove fixed neck length when face data exists (dynamic head/neck)
- [x] Enforce arm proportion checks using detected shoulder scale
- [x] Enforce palm width checks and guarantee connector continuity
- [x] Align neutral hand to wrist/forearm angle (fallback follows wrist)
- [x] Soften hand validation to avoid mid-frame dropouts

### Motion Probe Plan (start after reference body hardening)

- [x] Define probe set (up/down/left/right + open/close/spread/pinch)
- [x] Create probe generator script (`generate_motion_probes.py`)
- [x] Generate probe signatures (JSON in `assets/probes/`)
- [x] Run embeddings on probes (same pipeline as signatures)
- [x] Compare embedding deltas and flag inconsistencies
- [x] Refine probes to move limbs relative to shoulder center (avoid full-body translation)
- [x] Align probe directions to show_reference_body movements
- [ ] Increase hand-shape probe separation (open/close/spread/pinch)
- [ ] Add probe-only embedding mode (optional: disable shoulder centering)

### Phase 3: Embedding Normalization ✅ COMPLETE (Validation Pending)

- [x] Shoulder-width scaling in `generate_embeddings.py`
- [x] Shoulder-width scaling in `recognition_engine.py`
- [x] Regenerate embeddings after normalization updates
- [ ] Validate embedding stats (no extreme means) and re-check recognition quality
- [ ] Visual validation: skeleton render and hand continuity in mid-frames
- [ ] Later: ROM-based per-joint validation (score/reject frames, no reconstruction in renderer)

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

## Skeleton Visualizer Improvements ✅ COMPLETE (Rewrite)

**Last Updated:** 2026-02-03

### MAJOR REFACTOR: skeleton_renderer.py (NEW)

Created simpler architecture replacing complex `skeleton_drawer.py`:

**Design Principle:**

- Reference body provides FIXED PROPORTIONS (never scaled)
- Landmarks provide POSITIONS/ANGLES
- We MOVE reference body parts to match detected angles
- Missing parts use reference body defaults
- Out-of-bounds or biologically impossible points are flagged

**Key Changes:**

- [x] Created `skeleton_renderer.py` - simpler, cleaner approach
- [x] Fixed reference body constants (SHOULDER=100px, UPPER_ARM=55px, LOWER_ARM=45px)
- [x] Added `SkeletonDrawerCompat` compatibility layer for existing code
- [x] Updated `skeleton_debugger.py` to use new renderer
- [x] Updated `test_asl_vs_bsl.py` and `test_skeleton_render.py`
- [x] Generated 16 visual test images (all 4 signs × 2 languages × 2 frames)

**Previous Bugs - ALL RESOLVED:**

- [x] **Blue stub on missing hand** - FIXED
  - New renderer uses proper neutral hand with visible fingers
- [x] **Hand scaling inconsistency** - FIXED
  - New renderer uses FIXED hand proportions (never scales hands relative to body)
  - Finger lengths are constant, only ANGLES change based on detected data

- [x] **Dynamic neck connection** - FIXED
  - Head/neck positioned relative to shoulder center with fixed proportions
- [x] **Neutral rest hand for fallback** - FIXED
  - `_draw_neutral_hand()` generates anatomically correct relaxed hand

### Files Changed:

| File                        | Change                                |
| --------------------------- | ------------------------------------- |
| `skeleton_renderer.py`      | NEW - simpler reference body approach |
| `skeleton_debugger.py`      | Updated imports to use new renderer   |
| `test_asl_vs_bsl.py`        | Updated imports                       |
| `test_skeleton_render.py`   | Updated to use new renderer           |
| `test_skeleton_renderer.py` | NEW - comprehensive visual tests      |

### Visual Test Results (assets/test_render/):

- ASL_hello_0: ✓ Both hands visible
- BSL_hello: ✓ Both hands visible
- ASL_go_0: ✓ Both hands visible
- BSL_go: ✓ Both hands visible
- ASL_where_0: ✓ Fallback hands working
- BSL_where: ✓ Both hands visible
- ASL_you_0: ✓ Right hand visible, left fallback
- BSL_you: ✓ Both hands visible

---

## Previous Issues (HISTORICAL - RESOLVED)

### Critical Bugs (Priority 0 - BLOCKING) - ALL RESOLVED

- [x] **Blue stub on missing hand** - FIXED (2026-02-03)
  - Root cause: `generate_neutral_hand()` had finger_spacing too small (6px)
  - Hand was only 25px wide, appeared collapsed
  - Fix: Created new skeleton_renderer.py with proper proportions
- [x] **Hand scaling inconsistency** - FIXED (2026-02-03)
  - Root cause: Old code applied same scale factor to hands as body
  - When shoulder width is small, scale factor is large, making hands massive
  - Fix: New renderer uses FIXED hand proportions (no scaling)

### Completed Fixes ✅

- [x] **Dynamic neck connection** - Connect shoulder_midpoint → actual face landmark
  - Implemented in `ReferenceBody.draw_canvas()` with landmarks parameter
  - Fallback chain: nose_tip(1) → glabella(168) → upper_lip(0) → chin(152)
  - Dynamic head position based on face landmarks
  - Color indicates tracking: green=tracked, grey=fallback

- [x] **Neutral rest hand for fallback** - Generate linguistically unmarked hand shape
  - Implemented in `generate_neutral_hand()` function
  - Does NOT use previous frame's hand (would carry forward a sign)
  - Hands relaxed, fingers loosely curved downward
  - **Fixed finger spacing** (was 25px wide, now 53px wide)

- [x] **Reference body canvas** - Consistent coordinate system
  - `REFERENCE_SHOULDER_WIDTH = 100px` as normalization anchor
  - `normalize_to_reference()` scales all landmarks proportionally
  - Scale factor clamped to 0.3-3.0 range

### Known Issues Being Tracked

| Issue                                   | Root Cause                                              | Status                               |
| --------------------------------------- | ------------------------------------------------------- | ------------------------------------ |
| Blue stub for missing left hand         | Finger spacing too narrow (6px)                         | ✅ Fixed (now 15px spacing)          |
| Hands too large in some frames          | Scale factor applied to hands (should cap?)             | 🟡 May need hand-specific cap        |
| Missing hand in mid-frames              | Validation rejects partial hand data                    | 🔄 Soften fallback thresholds        |
| Palm connectors appear inconsistent     | MCP distribution/validation needs review                | 🔄 Visual validation required        |
| Neutral hand angle mismatch             | Fallback hand not aligned to wrist angle                | 🔄 Align to forearm vector           |
| Reference body scale mismatch in dual   | Any extra scaling/overlay drift                         | 🔄 Keep fixed reference scale only   |
| Double normalization risk               | `normalize_display` + `normalize_to_reference` conflict | ✅ Avoided (normalize_display=False) |
| `normalize_display` breaks 6-point pose | `normalize_landmarks()` expects 33 points               | ✅ By design (disabled)              |
| Colorful finger rendering               | Finger colors inconsistent per mode                     | 🔄 Verify all draw paths             |

### Debugging Insights (2026-02-03)

**Commit 4a8ed1fe was NOT relevant** - only deleted documentation files, no code changes.

**Key findings:**

1. Signatures are in normalized (0-1) coords, correctly scaled to pixels by `extract_landmarks_from_signature`
2. `normalize_to_reference` works correctly - scales proportionally to 100px shoulder width
3. Missing hands (MediaPipe zeros) trigger `generate_neutral_hand` - was too narrow, now fixed
4. Hand scaling uses same factor as body - may need independent cap for very large scale factors

### Critical Fixes (Priority 1) ✅ COMPLETE

- [x] **Dynamic neck connection** - ✅ DONE
- [x] Shoulder→elbow→wrist arm lines _(skeleton_renderer.py `_draw_arm()`)_
- [x] Both-endpoints-valid check before drawing any connection _(line 326: `if not all([shoulder, elbow, wrist]): return`)_

### Face Rendering (Priority 2)

- [ ] Draw face as shapes not dots (eyes with lids, eyebrows, lips contour)
- [ ] Nose outline (subtle, non-distracting)
- [ ] Eyebrow position/shape for non-manual markers
- [ ] Use FACEMESH_LIPS, FACEMESH_LEFT_EYE, etc. connection sets from MediaPipe

### Hand Rendering (Priority 2)

- [ ] Color-code each finger (thumb=red, index=orange, middle=green, ring=blue, pinky=purple)
- [ ] Draw palm→fingertip connecting lines for all 5 fingers
- [ ] Left hand / right hand base color distinction

### Body Rendering (Priority 3)

- [ ] Trapezoid torso option (simple, effective)
- [ ] Keep neck connection (we have it, they skip it—see tradeoffs below)

### Rendering Quality (Priority 3)

- [ ] Anti-aliased lines: `cv2.LINE_AA` flag for smooth rendering
- [ ] Draw points AFTER lines (MediaPipe pattern - "aesthetically better")
- [ ] White border on joint dots: Draw larger white circle first, then colored fill
- [ ] Larger joint dots during debug mode

### Debug/Clean Mode Toggle (Priority 3)

- [ ] Add `mode` parameter: `"debug"` vs `"clean"`
- [ ] Debug mode: Show dots + landmark indices + low-confidence highlights (red)
- [ ] Clean mode: Smooth lines only, no dots (Sign-MT style)
- [ ] Show skeleton connectivity issues visually (broken limbs = dashed lines?)

### MediaPipe Best Practices to Implement

| Pattern              | Description                                  | Status                                 |
| -------------------- | -------------------------------------------- | -------------------------------------- |
| Visibility threshold | Skip landmarks with visibility < 0.5         | ✅ In recognition_base.py              |
| Both endpoints check | Only draw connection if both endpoints valid | ✅ In skeleton_renderer.py `_draw_arm` |
| Points after lines   | Draw joints after skeleton lines             | ✅ In skeleton_renderer.py `_draw_arm` |
| DrawingSpec pattern  | Per-landmark color/thickness customization   | ⬜ Nice-to-have                        |

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

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Recognition Average (stored-to-stored, joint-only) | ≥0.70 | 0.7339 | ✅ (pre-Phase 4 baseline) |
| ASL-BSL 4-stream final baseline (3D bones, 654-dim) | <0.80 | **0.7178 mean** | ✅ |
| ASL-BSL per-concept: GREETING | — | 0.6932 | — |
| ASL-BSL per-concept: YOU | — | 0.8023 | — |
| ASL-BSL per-concept: GO | — | 0.4766 | — |
| ASL-BSL per-concept: WHERE | — | 0.8992 | — |
| Probe STRICT: up_vs_down | <0.90 | 0.6755 | ✅ |
| Probe STRICT: left_vs_right | <0.90 | 0.6932 | ✅ |
| Arm Length Consistency | ≤20px diff | 9px | ✅ |
| Blue Stub Bug | None | Fixed | ✅ |
| Scale normalization (÷ shoulder_width) | Implemented | ✅ Feb 26 | ✅ |
| Z-drop fix (3D bone vectors) | Implemented | ✅ Feb 26 | ✅ |
| EMBEDDING_DIM (natural, no truncation) | 654 | ✅ Feb 26 | ✅ |
| Hand skeleton display (full 21-pt topology) | Implemented | ✅ Feb 26 | ✅ |

---

## Terminal Guidelines

⚠️ **DO NOT USE**:

- Heredoc (`<< 'EOF'` or `<< SCRIPT`) - causes terminal corruption

---

## Handshape Insights: Miozzo & Peressotti (2022)

**Summary (kept minimal & model-relevant):**

- Corpus: >38,000 handshapes across 33 sign languages; 160 distinct handshapes observed; 35 handshapes occur in all languages (core set).
- Major finding: strong cross-linguistic similarity in which handshapes exist; main variation is in frequencies per language.
- Biomechanical constraints to encode: neighbor-finger coupling (adjacent fingers move/shape together), high individuation of thumb and index, frequent identical-shape across all digits.
- Fingerspelling distribution differs from natural signing; treat as a separate domain.

**Actionable checklist (for modelling & pipeline) — add/implement:**

- **Core handshape basis:** Adopt the ~35 common handshapes as an initial prototype label set. (If needed later, expand to full 160.)
- **Structured finger priors:** Implement a coupling prior/regularizer that enforces stronger coupling for adjacent fingers and allows greater independence for thumb/index.
- **Representation:** Represent handshape as per-digit states (e.g., folded/extended/curled/contacts) with an option to collapse to "identical-shape" for the frequent all-same configurations.
- **Augmentation strategy:** Augment training data with biomechanically plausible variations (neighbor coupling, increased thumb/index variance, identical-shape perturbations). Avoid unrealistic independent variations of non-adjacent fingers.
- **Domain split:** Treat fingerspelling as a separate class/distribution (separate head or domain-adapted layer) because its statistics differ from natural signing.
- **Language adaptation:** Implement language-specific reweighting over the shared handshape basis (fine-tune or apply frequency-based priors) rather than learning separate inventories per language.
- **Evaluation / metrics:** Track per-handshape frequency coverage, per-language KL divergence from corpus frequencies, and recognition accuracy on signs requiring multi-digit individuation.
- **Next data task:** Extract exact list of the 35 common handshapes + numeric frequency weights from the full paper (user to provide remaining pages or permission to fetch). Marked as TODO: `Extract numeric frequencies and full 35-handshape list` in project TODOs.

**Citation:** Miozzo & Peressotti, "How the hand has shaped sign languages", Scientific Reports (2022). DOI: 10.1038/s41598-022-15699-1

- Long inline Python with `-c` - escaping issues

✅ **DO USE**:

- Create `.py` script file, then run it
- Simple one-line commands only
