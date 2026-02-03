# HandInHand Progress Checklist

**Last Updated**: 2026-02-03

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
- [ ] Add palm connections (MCP joints: 5→9→13→17)
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
| Double normalization risk               | `normalize_display` + `normalize_to_reference` conflict | ✅ Avoided (normalize_display=False) |
| `normalize_display` breaks 6-point pose | `normalize_landmarks()` expects 33 points               | ✅ By design (disabled)              |
| Colorful finger rendering               | Code not in current draw_skeleton                       | 🟡 Not implemented yet               |

### Debugging Insights (2026-02-03)

**Commit 4a8ed1fe was NOT relevant** - only deleted documentation files, no code changes.

**Key findings:**

1. Signatures are in normalized (0-1) coords, correctly scaled to pixels by `extract_landmarks_from_signature`
2. `normalize_to_reference` works correctly - scales proportionally to 100px shoulder width
3. Missing hands (MediaPipe zeros) trigger `generate_neutral_hand` - was too narrow, now fixed
4. Hand scaling uses same factor as body - may need independent cap for very large scale factors

### Critical Fixes (Priority 1)

- [x] **Dynamic neck connection** - ✅ DONE
- [ ] Shoulder→elbow→wrist arm lines (verify rendering)
- [ ] Both-endpoints-valid check before drawing any connection (MediaPipe pattern)

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

| Pattern              | Description                                  | Status                    |
| -------------------- | -------------------------------------------- | ------------------------- |
| Visibility threshold | Skip landmarks with visibility < 0.5         | ✅ In recognition_base.py |
| Both endpoints check | Only draw connection if both endpoints valid | ⬜ TODO                   |
| Points after lines   | Draw joints after skeleton lines             | ⬜ TODO                   |
| DrawingSpec pattern  | Per-landmark color/thickness customization   | ⬜ TODO                   |

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
