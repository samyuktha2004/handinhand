# HandInHand Progress Checklist

**Last Updated**: 2026-02-02

---

## Open-Source Anatomy Resources (Feb 2, 2026)

### Optimization Checklist

- [ ] Download Z-Anatomy Blender files for skeletal reference (CC BY-SA 4.0)
- [ ] Extract proportional data (arm lengths, joint angles) from Z-Anatomy
- [ ] Cross-reference with MediaPipe landmark indices
- [ ] Create proportional validation script
- [ ] Document arm/leg length ratios for normalization

### Verified Resources (No Commercial Restrictions)

| Resource             | License       | Use              |
| -------------------- | ------------- | ---------------- |
| Z-Anatomy            | CC BY-SA 4.0  | 3D models ✅     |
| Open Anatomy Project | Open (NIH)    | Brain atlases ✅ |
| AnatomyTOOL          | CC (per-item) | Bone scans ✅    |
| Wikimedia Commons    | CC0/CC BY-SA  | SVG diagrams ✅  |
| OpenStax A&P         | CC BY 4.0     | Textbook ✅      |

See [BODY_MODEL_INSIGHTS.md](BODY_MODEL_INSIGHTS.md) for Andrew Entwistle model analysis.

---

## Current Phase: Phase 2 - Reference Body & Scaling

### Phase 1: Core Recognition ✅ COMPLETE

- [x] MediaPipe landmark extraction
- [x] Signature storage (JSON format)
- [x] Embedding generation (Global Average Pooling)
- [x] Recognition engine (Cosine similarity)
- [x] Recognition quality: **0.7339 average** ✅

### Phase 2: Reference Body & Scaling 🔄 IN PROGRESS

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
