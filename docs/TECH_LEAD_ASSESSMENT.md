# Tech Lead Assessment: HandInHand Project

**Date:** January 30, 2026  
**Status:** Core System Working - Quality Filtering In Progress

---

## Current State Summary

| Component           | Status      | Notes                            |
| ------------------- | ----------- | -------------------------------- |
| Recognition Engine  | Working     | 0.7339 avg cosine similarity     |
| Landmark Extraction | Fixed       | Now matches signature format     |
| Normalization       | Fixed       | Scale invariance added           |
| Code Refactor       | Done        | Base class created (26% savings) |
| Quality Gates       | In Progress | Visibility filtering planned     |
| Documentation       | Complete    | PROJECT_OVERVIEW.md created      |

---

## Recognition Quality

| Word        | Score      | Status                            |
| ----------- | ---------- | --------------------------------- |
| hello       | 0.7148     | Good                              |
| where       | 0.5931     | Weakest - improvement opportunity |
| you         | 0.7763     | Good                              |
| go          | 0.8515     | Best                              |
| **Average** | **0.7339** | **Excellent**                     |

---

## Active Work: Landmark Quality Filtering

### Problem Statement

MediaPipe sometimes produces low-confidence landmarks that corrupt embeddings:

- Occluded hands detected in wrong position
- Fast movement causing detection lag
- Background objects misidentified as body parts

### Solution: 3-Phase Quality Filtering

#### Phase 1: Visibility Filtering (Current Sprint)

| Task | Description                                                    | Status     |
| ---- | -------------------------------------------------------------- | ---------- |
| 1.1  | Add `VISIBILITY_THRESHOLD = 0.5` constant                      | ✅ Done    |
| 1.2  | Filter landmarks with visibility < threshold → mark as [0,0,0] | ✅ Done    |
| 1.3  | Add `is_frame_quality_good()` method                           | ✅ Done    |
| 1.4  | Add `check_skeleton_connectivity()` method                     | ✅ Done    |
| 1.5  | Add window quality gate (70% good frames)                      | ✅ Done    |
| 1.6  | Use masked averaging in `compute_embedding()`                  | ✅ Done    |
| 1.7  | Update `generate_embeddings.py` for batch processing           | ⬜ Pending |

#### Phase 2: Skeleton Connectivity (Next Sprint)

| Task | Description                                            | Status  |
| ---- | ------------------------------------------------------ | ------- |
| 2.1  | Define `LIMB_CONNECTIONS` (shoulder↔elbow↔wrist, etc.) | ✅ Done |
| 2.2  | Add "both endpoints valid" check for each limb         | ✅ Done |
| 2.3  | Add window quality gate (require 70% good frames)      | ✅ Done |

#### Phase 3: Motion Validation (Future)

| Task | Description                                          | Status     |
| ---- | ---------------------------------------------------- | ---------- |
| 3.1  | Add velocity clipping (reject teleporting landmarks) | ⬜ Pending |
| 3.2  | Optional: Proportional neighbor distance check       | ⬜ Pending |

### Technical Approach

**MediaPipe provides visibility scores (0-1) per landmark.** Current implementation ignores these entirely.

```python
# Proposed change in extract_landmarks():
VISIBILITY_THRESHOLD = 0.5

if landmark.visibility < VISIBILITY_THRESHOLD:
    return [0, 0, 0]  # Mark as missing
```

**Masked averaging for mean embeddings:**

```python
# Instead of: np.mean(embeddings, axis=0)
# Use: np.ma.mean(np.ma.masked_where(embeddings == 0, embeddings), axis=0)
```

---

## Open Issues

### 1. WHERE Recognition (Low Priority)

- **Current:** 0.5931 (lowest)
- **Target:** 0.70+
- **Fix options:** Add more variants, improve quality filtering

### 2. Avatar Playback (Phase 3 - Not Started)

Architecture designed, implementation pending. Needs VRM + Three.js integration.

---

## Resolved Issues

| Issue                     | Resolution                               | Date   |
| ------------------------- | ---------------------------------------- | ------ |
| Recognition engine merge  | Created BaseRecognitionEngine (26% less) | Jan 30 |
| Landmark mismatch         | Fixed POSE_INDICES/FACE_INDICES          | Jan 29 |
| Scale invariance          | Added shoulder width normalization       | Jan 29 |
| Debug file pollution      | Deleted 17 files, archived 4             | Jan 29 |
| Missing utils/**init**.py | Created                                  | Jan 29 |
| Blue dot artifact         | Fixed with \_is_valid_point()            | Jan 28 |

---

## Codebase Health

**Line Count (Recognition):**
| File | Lines | Purpose |
|------|-------|---------|
| recognition_base.py | 267 | Shared base class |
| recognition_engine.py | 183 | CLI engine |
| recognition_engine_ui.py | 561 | UI dashboard |
| **Total** | **1011** | (was 1373, 26% reduction) |

**Core Files (10):** All working  
**Test Files (2):** All passing  
**Utils:** Complete with **init**.py

---

## Recommended Next Actions

1. **Current:** Implement Phase 1 visibility filtering
2. **Short term:** Phase 2 skeleton connectivity checks
3. **Medium term:** Begin avatar integration (Phase 3)

---

## Conclusion

**System is production-ready for MVP demo.**

- Recognition: 0.7339 average
- Code quality: Refactored, 26% line reduction
- Active work: Landmark quality filtering
