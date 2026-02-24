# Recognition Engine Design Document

**File**: recognition_engine.py  
**Lines**: 380+  
**Status**: Phase 2 - Real-time Recognition Engine

---

## Strategic Assessment: What Goes Where

### ✅ **Features Implemented**

| Feature                        | Type         | Implementation                 | Production | Scales    |
| ------------------------------ | ------------ | ------------------------------ | ---------- | --------- |
| **Cosine Similarity**          | Core         | Real-time scoring (0.0-1.0)    | ✅ Yes     | ✅ Yes    |
| **Ghost Visualization**        | Debug        | Optional `--debug` flag        | ❌ No      | ❌ Manual |
| **Tier 4 Validation**          | Automation   | Cross-concept confidence check | ✅ Yes     | ✅ Yes    |
| **Body-Centric Normalization** | Foundational | Shoulder center subtraction    | ✅ Yes     | ✅ Yes    |

---

## ⚠️ Known Embedding Mismatch (Phase 4 Fix Required)

**Current state** (`recognition_engine.py`):
- Loads `hello_mean.npy` (joint-only, 156 dims zero-padded to 512)
- `_compute_live_embedding()` computes joint coordinates only — no bone vectors, no motion deltas

**Available but not yet connected** (`generate_embeddings.py` lines 203–247):
- Saves `hello_mean_combined.npy` — 4-stream: joint + bone vectors + joint motion + bone motion
- Combined dims: 156 + 102 + 156 + 102 = 516 → truncated to 512

**Impact:** Both sides are internally consistent (both joint-only), so the 0.7339 recognition score is stable. But the combined stream — which carries hand shape and motion direction information — is completely unused.

**Fix (Phase 4, item 4a):**
1. Update `embedding_mean_file` in `assets/registries/asl_registry.json` and `bsl_registry.json` to point to `*_combined.npy` paths
2. Update `_compute_live_embedding()` in `recognition_engine.py` to mirror the 4-stream logic from `generate_embeddings.py`
3. Verify: run `test_recognition_quality.py` — score must stay at 0.7339 or improve

---

## 4-Tier Recognition System

### **Tier 1: Frame Range Validation** (in wlasl_pipeline.py)

- Metadata quality: Check frame_start/end are valid
- Status: ✅ **Production - Phase 1**

### **Tier 2: Plausible Duration** (in wlasl_pipeline.py)

- Semantic validity: Word/sentence frame counts reasonable
- Status: ✅ **Production - Phase 1**

### **Tier 3: Detection Quality** (in wlasl_pipeline.py)

- Extraction quality: >= 80/100 quality score
- Status: ✅ **Production - Phase 1**

### **Tier 4: Cross-Concept Confidence** (NEW - in recognition_engine.py)

- **Purpose**: Automated verification that matched concept makes sense
- **Logic**:
  1. Compute cosine similarity against all stored ASL embeddings
  2. Find best match (highest score)
  3. Find second-best match
  4. Check: `best_score - second_best_score >= TIER_4_GAP_THRESHOLD` (0.15)
- **Decision Tree**:

  ```
  If best_score >= 0.80 AND gap >= 0.15:
      status = "verified" ✅
  Else if best_score < 0.80:
      status = "low_confidence" ⚠️
  Else if gap < 0.15:
      status = "cross_concept_noise" 🔴 (ambiguous - could be multiple signs)
  ```

- **Why This Scales**:
  - Works for N concepts (2, 4, 100, 1000)
  - No manual tuning per concept
  - Automated: No human inspection needed
  - Detects "noisy" signals automatically

- **Example**:

  ```
  User signs HELLO (but with poor form):

  Scenario A (Correct):
    GREETING:           0.87 ← Best
    LOCATION_QUESTION:  0.60 ← Gap: 0.27 ✅ VERIFIED

  Scenario B (Cross-concept noise):
    GREETING:           0.82 ← Best
    PRONOUN_SECOND:     0.79 ← Gap: 0.03 🔴 "cross_concept_noise"
    (Hands ambiguous - could be YOU too)

  Scenario C (Low signal):
    GREETING:           0.71 ← Below threshold ⚠️ "low_confidence"
  ```

---

## Cosine Similarity Scoring

### **Metric**: 0.0 to 1.0

- **1.0** = Perfect match (identical embeddings)
- **0.5** = Orthogonal (no relationship)
- **0.0** = Perfect opposites (rare in practice)

### **Production Thresholds**:

- **0.90+** = HIGH confidence (immediate trigger)
- **0.80-0.90** = MEDIUM confidence (needs Tier 4 validation)
- **< 0.80** = LOW confidence (requires review or retrying)

### **Trigger Logic**:

```python
if cosine_sim >= 0.80 AND gap >= 0.15:
    trigger_bsl_animation(result.bsl_target_file)
else:
    skip_or_request_retry()
```

---

## Body-Centric Normalization

### **Why Necessary**:

- Position-independence: Stand at different distances/positions
- Shoulder center = torso reference point (language-relevant)
- Removes extraneous variation (camera placement, room setup)

### **Algorithm**:

```python
shoulder_center = (landmark[11] + landmark[12]) / 2
normalized = landmarks - shoulder_center
```

### **Verification**:

- Same normalization in `generate_embeddings.py` and `recognition_engine.py`
- If not normalized in real-time: Cosine similarities drop by ~30%
- Easy to debug: Check if user's hand position changes score dramatically

---

## Ghost Visualization (Debug Only)

### **Feature**: Optional `--debug` flag

```bash
python3 recognition_engine.py --debug
```

### **What It Shows**:

1. **Live skeleton**: Bright green (real-time)
2. **Golden signature**: Faint grey (reference pose)
3. **Cosine similarity bar**: Per-concept scores (0.0-1.0)
4. **Tier 4 validation**: Status badge (verified/noise/low_conf)

### **Why Separate From Pipeline**:

- NOT for automated scaling
- Testing/debugging only
- Requires manual human judgment to evaluate hand alignment
- Can be turned on/off without affecting recognition logic

### **Usage**:

```bash
python3 recognition_engine.py --debug           # Normal timing
python3 recognition_engine.py --debug --delay 5000  # 5sec per frame (demo)
```

---

## Real-Time Recognition Pipeline

### **Input**: Live webcam feed

### **Processing Loop**:

```
1. Capture frame from webcam
   ↓
2. MediaPipe Holistic landmark extraction (52 points)
   ↓
3. Accumulate landmarks in sliding window (30 frames)
   ↓
4. When window full (30 frames):
   a. Body-centric normalization (shoulder center)
   b. Global Average Pooling (flatten + average)
   c. Compute live embedding (512-dim)
   ↓
5. Cosine similarity scoring:
   - Compare to all 4 stored ASL embeddings
   - Get scores for [GREETING, PRONOUN, MOTION, LOCATION]
   ↓
6. Tier 4 validation:
   - Best vs second-best score gap check
   - Cross-concept noise detection
   ↓
7. Decision:
   - If verified: Trigger BSL animation + BSL target filename
   - If noise: Show "ambiguous" warning
   - If low_conf: Request retry
   ↓
8. Display results + optional debug info
   ↓
9. Clear window, repeat
```

### **Performance**:

- **Latency**: ~100-200ms per frame (GPU: <50ms)
- **Memory**: ~200MB (MediaPipe + embeddings)
- **Accuracy**: Target > 95% on known 4 concepts

---

## Tier 4 Validation: Scaling Benefits

### **Without Tier 4** (naive cosine similarity):

```
User signs HELLO with poor form:
  GREETING:           0.82
  PRONOUN_SECOND:     0.80

Result: Ambiguous - which is it?
Action: Could trigger HELLO OR YOU randomly
```

### **With Tier 4** (cross-concept validation):

```
Gap = 0.82 - 0.80 = 0.02 < 0.15 threshold
Result: "cross_concept_noise" 🔴
Action: Request retry with clearer form
```

### **Why Scales**:

1. **Works for any N concepts**: Don't need per-concept tuning
2. **Automated**: No manual inspection of every sign
3. **Detects problems**: Noisy data flagged automatically
4. **Adaptive**: Can adjust TIER_4_GAP_THRESHOLD (0.15) globally for all concepts

### **Example: Scaling to 100 Concepts**:

```python
# NO changes needed to code:
TARGET_GLOSSES = ["hello", "you", "go", "where", ..., "bicycle", "computer", ...]
VIDEOS_PER_GLOSS = 2

# Just run pipeline:
python3 wlasl_pipeline.py  # Extracts all 100
python3 generate_embeddings.py  # Generates 100 embeddings
python3 recognition_engine.py  # Tier 4 validates all 100 without code change
```

---

## Detection Thresholds

| Parameter                        | Value     | Purpose                                         |
| -------------------------------- | --------- | ----------------------------------------------- |
| **COSINE_SIM_THRESHOLD**         | 0.80      | Minimum score to trigger recognition            |
| **TIER_4_GAP_THRESHOLD**         | 0.15      | Minimum gap between best and second-best        |
| **WINDOW_SIZE**                  | 30 frames | Frames to accumulate before computing embedding |
| **CONFIDENCE_DISPLAY_THRESHOLD** | 0.50      | Only show concepts > 50% in debug mode          |
| **min_detection_confidence**     | 0.3       | MediaPipe detection threshold                   |
| **min_tracking_confidence**      | 0.3       | MediaPipe tracking threshold                    |

---

## Error Handling & Status Codes

### **RecognitionResult.verification_status**:

| Status                | Meaning                   | Action                    |
| --------------------- | ------------------------- | ------------------------- |
| `verified`            | ✅ High confidence match  | **TRIGGER** BSL animation |
| `low_confidence`      | ⚠️ Score < 0.80           | Request retry             |
| `cross_concept_noise` | 🔴 Ambiguous (gap < 0.15) | Request clearer form      |

### **RecognitionResult.confidence_level**:

| Level    | Score Range | Interpretation                |
| -------- | ----------- | ----------------------------- |
| `high`   | 0.90+       | Confident, immediate trigger  |
| `medium` | 0.80-0.90   | Good, needs Tier 4 validation |
| `low`    | < 0.80      | Retry or manual inspection    |

---

## Usage Examples

### **Normal Recognition** (no debug):

```bash
python3 recognition_engine.py
```

Output: Only matched concept + BSL target filename

### **Debug Mode** (development/testing):

```bash
python3 recognition_engine.py --debug
```

Output:

```
Window: 100%
BEST: GREETING
[=============================] 0.87
Tier 4: verified
Scores:
  GREETING: 0.870
  PRONOUN_SECOND_PERSON: 0.620
  MOTION_AWAY: 0.450
  LOCATION_QUESTION: 0.380
✅ GREETING 0.870 (high) (verified)
```

### **Slow Replay** (demo/presentation):

```bash
python3 recognition_engine.py --debug --delay 5000
```

Each frame displays for 5 seconds (demo speed)

### **Alternate Camera**:

```bash
python3 recognition_engine.py --camera 1
```

Use device 1 instead of default camera

---

## Design Decisions

### **1. Why Global Average Pooling?**

- ✅ Simple, fast, deterministic
- ✅ Works for variable-length sequences
- ✅ Matches embedding generation exactly
- ❌ Could use LSTM for temporal awareness (future enhancement)

### **2. Why Tier 4 Over Threshold-Only?**

- ✅ Detects ambiguous signals automatically
- ✅ Scales without manual tuning
- ✅ Prevents false positives (best score might still be "wrong")
- ❌ Adds slight latency (negligible)

### **3. Why Shoulder Center Normalization?**

- ✅ Linguistically relevant (torso = body-centric reference)
- ✅ Position/distance independent
- ✅ Matches ASL/BSL linguistic structure
- ❌ Assumes upright pose (sitting cross-legged won't work)

### **4. Why Separate Debug Mode?**

- ✅ Keeps production code clean
- ✅ Easy to disable for performance
- ✅ Ghost visualization optional (not required for scaling)
- ❌ Requires separate `--debug` flag

---

## Limitations & Future Enhancements

### **Current Limitations**:

1. **Single user**: One person per frame (not multi-person)
2. **Full-body required**: Needs pose landmarks (shoulder down)
3. **Lighting dependent**: MediaPipe detection ~0.3 threshold in poor light
4. **Real-time only**: No batch processing
5. **Ghost visualization**: TODO (needs frame extraction from JSON)

### **Future Enhancements**:

1. **LSTM temporal model**: Capture motion dynamics better than GAP
2. **Multi-person**: Track multiple signers simultaneously
3. **Hand-only mode**: For close-range captures (hands only)
4. **Confidence calibration**: Learn optimal gap threshold per concept
5. **One-shot learning**: New sign from 1-2 examples
6. **Transformation matrix**: Cross-lingual mapping (Phase 3)

---

## Testing Checklist

- [ ] Run with `--debug` flag
- [ ] Sign HELLO - should match GREETING > 0.85
- [ ] Sign YOU - should match PRONOUN > 0.85
- [ ] Sign GO - should match MOTION > 0.85
- [ ] Sign WHERE - should match LOCATION > 0.85
- [ ] Sign HELLO poorly - should show "cross_concept_noise" if similar to YOU
- [ ] Measure latency per frame (target < 200ms)
- [ ] Verify Tier 4 validation catches ambiguous signals
- [ ] Test with `--delay 5000` (slow replay)

---

## Integration Points

### **Input Sources**:

- ✅ translation_map.json (registry + embeddings)
- ✅ assets/embeddings/asl/\*.npy (stored embeddings)
- ✅ Webcam (OpenCV)
- ✅ MediaPipe Holistic

### **Output Targets**:

- Console: Recognition result + status
- BSL animation trigger: assets/signatures/bsl/{concept}.json filename
- Debug visualization: Optional overlay on webcam feed

### **Next Phase Integration**:

- → Avatar rendering: Load {bsl_target_file} and animate
- → WebSocket: Send results to React frontend
- → Database: Log recognition attempts + confidence scores

---

**Version**: 1.0  
**Status**: Ready for testing  
**Last Updated**: 23 January 2026
