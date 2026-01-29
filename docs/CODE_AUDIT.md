# HandInHand Code Audit Report

**Date:** January 29, 2026  
**Branch:** `feature/reference-body-improvements`

---

## 📊 Executive Summary

| Category              | Count | Action                      |
| --------------------- | ----- | --------------------------- |
| **Core Files**        | 8     | Keep & maintain             |
| **Debug/Test Files**  | 14    | Archive or delete           |
| **Migration Scripts** | 6     | Delete (migration complete) |
| **Utility Files**     | 3     | Keep                        |
| **Documentation**     | 3     | Update                      |

**Total Python files:** 41 (including scripts/)  
**Recommended cleanup:** 20 files (49%)

---

## 🟢 CORE FILES (Keep & Maintain)

### 1. `skeleton_drawer.py` (871 lines)

**Purpose:** Renders 2D skeletons from MediaPipe landmarks  
**Dependencies:** cv2, numpy  
**Used by:** skeleton_debugger.py, recognition_engine.py, recognition_engine_ui.py  
**Status:** ✅ Active, core component  
**Notes:**

- Contains `SkeletonDrawer` class and `extract_landmarks_from_signature()` helper
- Handles reference body normalization (100px shoulders)
- Placeholder hands for missing data

### 2. `skeleton_debugger.py` (1039 lines)

**Purpose:** Dual-signature viewer + quality audit tools  
**Dependencies:** skeleton_drawer.py, cv2, numpy  
**Status:** ✅ Active, recently enhanced  
**Features:**

- `--audit` mode for DTW-based variant consistency checking
- `--quarantine` to move bad signatures
- Corruption report on close
- NO DATA overlay for corrupt frames

### 3. `recognition_engine.py` (476 lines)

**Purpose:** Real-time sign recognition (headless/debug mode)  
**Dependencies:** utils/registry_loader.py, mediapipe, numpy  
**Status:** ✅ Active  
**Notes:**

- Tier 4 validation (cosine threshold + gap)
- Sliding window embedding computation

### 4. `recognition_engine_ui.py` (832 lines)

**Purpose:** Recognition engine with visual dashboard  
**Dependencies:** recognition_engine.py (shared logic), socket.io  
**Status:** ✅ Active, main user-facing engine  
**⚠️ Issue:** Duplicates ~40% of recognition_engine.py logic  
**Recommendation:** Consider merging or sharing base class

### 5. `generate_embeddings.py` (536 lines)

**Purpose:** Generate 512-dim embeddings from signatures  
**Dependencies:** utils/registry_loader.py, numpy  
**Status:** ✅ Active, recently enhanced with quality gates  
**Notes:**

- 4-layer quality gate system
- Saves to assets/embeddings/{lang}/

### 6. `extract_signatures.py` (547 lines)

**Purpose:** Extract MediaPipe landmarks from video files  
**Dependencies:** cv2, mediapipe  
**Status:** ✅ Active  
**Notes:**

- Core extraction logic
- Used by wlasl_pipeline.py

### 7. `wlasl_pipeline.py` (421 lines)

**Purpose:** Self-cleaning WLASL download + extraction pipeline  
**Dependencies:** extract_signatures.py, utils/registry_loader.py  
**Status:** ✅ Active  
**Notes:**

- Downloads from YouTube, extracts landmarks, deletes MP4s
- Updates ASL registry

### 8. `utils/registry_loader.py` (220 lines)

**Purpose:** Transparent access to language/concept registries  
**Dependencies:** None (core utility)  
**Used by:** recognition_engine.py, generate_embeddings.py, wlasl_pipeline.py  
**Status:** ✅ Core utility, keep

---

## 🟡 AUGMENTATION FILES (Keep, Low Priority)

### 9. `augment_signatures.py` (314 lines)

**Purpose:** Data augmentation (rotation, scaling, mirroring)  
**Status:** ⚠️ Not currently integrated into pipeline  
**Recommendation:** Keep, but add to generate_embeddings.py workflow

### 10. `smooth_signatures.py` (435 lines)

**Purpose:** Kalman filtering for jittery trajectories  
**Status:** ⚠️ Creates `*_smoothed.json` variants  
**Recommendation:** Keep, but assess if smoothed variants help recognition

---

## 🔴 DEBUG FILES (Archive or Delete)

These were created during development for one-off debugging. They should be archived or deleted.

| File                          | Purpose                       | Lines | Status    |
| ----------------------------- | ----------------------------- | ----- | --------- |
| `debug_hands.py`              | Debug missing hand in hello_0 | 48    | ❌ DELETE |
| `debug_hello1.py`             | Debug hello_1 normalization   | 39    | ❌ DELETE |
| `debug_hello1_bounds.py`      | Debug hello_1 bounds issue    | 17    | ❌ DELETE |
| `debug_normalization.py`      | Debug normalized rendering    | 44    | ❌ DELETE |
| `analyze_hand_proportions.py` | Extract hand offsets          | 39    | ❌ DELETE |
| `analyze_pose_structure.py`   | Analyze pose structure        | 37    | ❌ DELETE |
| `check_arm_lengths.py`        | Verify arm length math        | 73    | ❌ DELETE |
| `check_blue_dot.py`           | Find blue dot origin issue    | 44    | ❌ DELETE |

**Total:** 8 files, 341 lines → DELETE

---

## 🔴 TEST FILES (Consolidate)

These test files have overlapping functionality. Consolidate into a single test suite.

| File                              | Purpose                          | Lines | Recommendation           |
| --------------------------------- | -------------------------------- | ----- | ------------------------ |
| `test_all_signatures.py`          | Test all sigs for normalization  | 132   | Keep (main test)         |
| `test_placeholder_hands.py`       | Test placeholder hand generation | 43    | ❌ DELETE (covered)      |
| `test_recognition_quality.py`     | Cross-language similarity        | 95    | Keep (useful)            |
| `test_reference_normalization.py` | Test ref body normalization      | 71    | ❌ DELETE (covered)      |
| `test_visual_normalization.py`    | Quick visual skeleton test       | 51    | ❌ DELETE (use debugger) |
| `test_frame_range_extraction.py`  | Test BSL frame extraction        | 119   | ❌ DELETE (one-off)      |

**Recommendation:** Keep `test_all_signatures.py` and `test_recognition_quality.py`, delete rest.

---

## 🔴 MIGRATION SCRIPTS (Delete - Migration Complete)

These scripts were used to migrate from inline to separate registries. Migration is done.

| File                              | Purpose            | Lines | Status    |
| --------------------------------- | ------------------ | ----- | --------- |
| `scripts/migration_step1.py`      | Extract registries | 168   | ❌ DELETE |
| `scripts/migration_execute.py`    | Full migration     | 247   | ❌ DELETE |
| `scripts/verify_migration.py`     | Verify structure   | 88    | ❌ DELETE |
| `scripts/final_validation.py`     | Comprehensive test | 232   | ❌ DELETE |
| `scripts/test_registry_loader.py` | Test loader        | 48    | ❌ DELETE |

**Total:** 5 files, 783 lines → DELETE

---

## 🟡 REFERENCE/SETUP FILES (Keep)

| File                     | Purpose                            | Lines | Status                 |
| ------------------------ | ---------------------------------- | ----- | ---------------------- |
| `show_reference_body.py` | Visual reference for normalization | 431   | ✅ KEEP (reference)    |
| `verify_installation.py` | Check package imports              | 37    | ✅ KEEP                |
| `verify_signatures.py`   | 3D signature quality viewer        | 377   | ✅ KEEP                |
| `quick_start.py`         | Usage documentation                | 115   | ⚠️ Update or delete    |
| `ARCHITECTURE.py`        | Architecture overview              | 180   | ⚠️ Convert to markdown |

---

## 🔴 DATASET SETUP FILES (Archive)

These were used for initial dataset setup. Rarely needed now.

| File                      | Purpose                 | Lines | Recommendation                  |
| ------------------------- | ----------------------- | ----- | ------------------------------- |
| `setup_dataset.py`        | Extract WLASL videos    | 126   | Archive                         |
| `extract_wlasl_videos.py` | Copy WLASL videos       | 97    | Archive (wlasl_pipeline covers) |
| `create_test_videos.py`   | Create synthetic videos | 71    | Archive                         |
| `optimize_frame_range.py` | Find optimal frames     | 255   | Archive                         |

---

## 🟡 SOCKET.IO TEST SERVER

| File                            | Purpose                 | Lines | Status                       |
| ------------------------------- | ----------------------- | ----- | ---------------------------- |
| `scripts/test_socket_server.py` | Test Socket.io emission | 237   | ✅ KEEP (useful for testing) |

---

## ⚠️ VARIABLE NAMING INCONSISTENCIES

| Variable                 | Location 1                   | Location 2                      | Issue          |
| ------------------------ | ---------------------------- | ------------------------------- | -------------- |
| `SHOULDER_CENTER_LEFT`   | recognition_engine.py (=11)  | generate_embeddings.py (=11)    | OK, matches    |
| `COSINE_SIM_THRESHOLD`   | recognition_engine.py (0.80) | recognition_engine_ui.py (same) | OK, matches    |
| `normalize_to_reference` | skeleton_drawer.py           | skeleton_debugger.py            | OK, consistent |
| `pose_data`              | All signature files          | All loaders                     | OK, consistent |

**No major naming inconsistencies found.**

---

## � CODE QUALITY IMPROVEMENTS (Future)

### 1. Merge Recognition Engines

`recognition_engine.py` and `recognition_engine_ui.py` share ~40% code.

**Proposal:**

- Create `RecognitionEngineBase` class in `recognition_engine.py`
- `recognition_engine_ui.py` extends base with UI overlay

---

## 📊 FILE DEPENDENCY GRAPH

```
                    translation_map.json
                           │
                    ┌──────┴──────┐
                    ▼             ▼
         utils/registry_loader.py
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
recognition_   generate_      wlasl_
engine.py      embeddings.py  pipeline.py
     │              │              │
     ▼              │              ▼
recognition_       │         extract_
engine_ui.py       │         signatures.py
     │              │              │
     └──────────────┼──────────────┘
                    ▼
             skeleton_drawer.py
                    │
                    ▼
            skeleton_debugger.py
```

---

## 🔜 REMAINING TASKS

- [ ] Merge recognition engine base class (optional refactor)
- [ ] Regenerate embeddings with quality gates
- [ ] Commit and push cleanup
