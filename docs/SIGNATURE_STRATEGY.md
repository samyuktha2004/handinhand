# Signature Strategy Analysis

**Last Updated:** January 25, 2026  
**Scope:** Decision framework for single-source vs. composite data strategies

---

## Quick Reference: Decision Framework

| Word      | Composite Issue  | Reference Quality       | Decision       | Similarity | Notes                 |
| --------- | ---------------- | ----------------------- | -------------- | ---------- | --------------------- |
| **WHERE** | ✅ Yes (mixed)   | ✅ High (clear)         | **REPLACE**    | 0.5931 ✅  | -40 pt improvement    |
| **GO**    | ❌ No (isolated) | ❌ Poor (low detection) | **KEEP WLASL** | 0.8515 ⚠️  | Marginal, needs faces |
| **HELLO** | ❌ Single source | N/A                     | **KEEP**       | 0.7148 ✅  | Good                  |
| **YOU**   | ❌ Single source | N/A                     | **KEEP**       | 0.7763 ✅  | Good                  |

---

## WHERE: Success Case (REPLACE Strategy)

### Problem

- **Original:** Composite extraction from 2-3 WLASL videos
- **Symptom:** ASL/BSL similarity too high (0.9819)
- **Root cause:** Inconsistent hand positioning across different recordings

### Solution

- Extracted clear YouTube reference video
- Single source = consistent spatial reference
- WHERE is spatial gesture (pointing/location) → reference clarity helps

### Result

- **Before:** 0.9819 ❌ (too similar)
- **After:** 0.5931 ✅ (clearly distinct)
- **Improvement:** 40 points

### Key Insight

Single-source references work when:

1. Composite data has conflicting quality/positioning
2. Gesture is spatial (needs clear reference frame)
3. Reference has better detection/clarity

---

## GO: Failure Case (KEEP WLASL Strategy)

### Problem

- **Attempted:** YouTube reference video to improve GO recognition
- **Current:** WLASL go_0 = 0.8515 (marginal)
- **Expected:** Reference would improve like WHERE

### Why It Failed

- **Poor hand detection:** Reference had only 27 hand points vs 58 in go_0
- **Different execution:** Reference interpreted GO differently than WLASL
- **Result:** 0.9480 (WORSE than WLASL 0.8515)

### Real Problem: Gesture Semantics

- GO is dynamic gesture (hand movement/direction)
- Easily confused with WHERE (pointing)
- Needs **facial features** to distinguish:
  - GO: raised eyebrows (emphasis)
  - WHERE: questioning eyebrows (location query)

### Key Insight

Single-source replacement fails when:

1. Existing isolated data already high quality
2. Reference has poor detection
3. Root cause is gesture ambiguity (not data quality)

---

## Current Recognition Status

```
hello        0.7148  ✅ GOOD - keep as is
where        0.5931  ✅ EXCELLENT - replaced composite
you          0.7763  ✅ GOOD - keep as is
go           0.8515  ⚠️ MARGINAL - needs facial features
─────────────────────────────
Average:     0.7339  ✅ EXCELLENT (< 0.80 threshold)
```

---

## Decision Framework

### Before Making Changes, Ask:

1. **Is current data isolated or composite?**
   - Composite + problems → Consider reference
   - Isolated + working → Keep it

2. **What's the actual problem?**
   - Data quality/consistency → Reference can help
   - Gesture ambiguity → Need additional features

3. **Does reference have good detection?**
   - Good detection + isolated gesture → Likely to help
   - Poor detection + ambiguous gesture → Likely to hurt

4. **Is gesture spatial or dynamic?**
   - Spatial (WHERE, HERE, THERE) → Reference clarity helps
   - Dynamic (GO, COME, TURN) → Facial features needed

### When to Replace

✅ Composite data + spatial gesture + clear reference + good detection

### When to Keep

✅ Isolated data + dynamic gesture + unclear reference + poor detection

---

## Implementation

### Test Recognition Quality

```bash
python3 test_recognition_quality.py
```

### Extract Reference Video (Best Practice)

```bash
# Use --delete to auto-cleanup source video
python3 extract_signatures.py --video ref.mp4 --sign word --lang ASL --delete
```

### Analyze Decision

- Run test_recognition_quality.py
- Compare before/after metrics
- Document decision and reasoning

---

## Future Work (Phase 4.2)

**Improve GO with Facial Features:**

1. Extract eyebrow landmarks (critical for GO emphasis)
2. Extract head position (spatial reference)
3. Re-extract all signatures with facial data
4. Expected: GO similarity drops below 0.80

---

## Files

- **Test tool:** test_recognition_quality.py (unified analyzer)
- **Pipeline:** extract_signatures.py (with --delete flag for cleanup)
- **Framework:** This document (decision guide)

---

**Philosophy:** Quality > Quantity; Strategic > Ad-hoc; Reusable > One-off
