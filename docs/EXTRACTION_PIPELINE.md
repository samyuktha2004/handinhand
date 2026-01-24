# Unified Signature Extraction Pipeline

**Status:** ✅ Consolidated  
**Scope:** Reference videos, WLASL videos, uploaded videos  
**Tool:** `extract_signatures.py` with CLI support

---

## Overview

There is **ONE extraction pipeline** for all video sources:

```bash
python3 extract_signatures.py [options]
```

**Why unified?**

- Same MediaPipe Holistic landmark extraction
- Consistent JSON output format
- Automatic cleanup (delete source video after extraction)
- Works for uploaded/reference videos AND WLASL dataset
- Integrates with signature registry

---

## Usage

### Default Behavior: BSL Lexicon Processing

```bash
python3 extract_signatures.py
```

- Processes all videos in `assets/raw_videos/lexicon/`
- Saves to `assets/signatures/bsl/`
- Auto-deletes .mp4 files

### Single Video Extraction (Reference Videos) ⭐ BEST PRACTICE

```bash
python3 extract_signatures.py --video video.mp4 --sign where --lang asl --delete
```

**Breakdown:**

- `--video`: Path to input video file
- `--sign`: Name for output JSON (e.g., "where", "hello_ref")
- `--lang`: Language code (ASL, BSL, JSL, CSL, LSF)
- `--delete`: ⭐ **ALWAYS use** - Auto-cleanup source video after extraction

**Why `--delete`?**

- Keeps workspace clean (saves disk space)
- Follows automatic cleanup pattern (consistent with wlasl_pipeline.py)
- Prevents orphaned video files
- Pipeline takes 2 steps: extract → cleanup

### Directory Processing (Custom Videos)

```bash
python3 extract_signatures.py --dir assets/raw_videos/custom --lang asl --delete
```

**Result:** Extracts all .mp4/.avi/.mov/.mkv files in directory

### Frame Range Extraction (WLASL Context Cleanup)

```bash
python3 extract_signatures.py --video video.mp4 --sign word --lang asl --start 10 --end 50
```

**Use case:** Extract only frames 10-50 (skip intro/outro context in WLASL)

### Custom Output Directory

```bash
python3 extract_signatures.py --video ref.mp4 --sign hello --lang asl --output-dir assets/signatures --delete
```

---

## Output Format

All signatures stored as JSON with consistent structure:

```json
{
  "sign": "where",
  "language": "asl",
  "pose_data": [
    {
      "pose": [[x, y, z], ...],        // 6 pose points × 3D
      "left_hand": [[x, y, z], ...],   // 21 hand points × 3D
      "right_hand": [[x, y, z], ...],  // 21 hand points × 3D
      "face": [[x, y, z], ...]         // 4 eye/brow points × 3D
    },
    ...
  ],
  "metadata": {
    "fps": 29,
    "total_frames": 84,
    "landmarks_per_frame": {
      "pose": 6,
      "left_hand": 21,
      "right_hand": 21,
      "face": 4
    }
  }
}
```

**Total embedding size:** 144 dimensions per frame (6×3 + 21×3 + 21×3 + 4×3)

---

## Implementation Notes

### MediaPipe Configuration

- **Model complexity:** 1 (balanced accuracy/speed)
- **Detection confidence:** 0.3 (optimized for sign language)
- **Tracking confidence:** 0.3 (better temporal continuity)
- **Landmark smoothing:** Enabled (reduces jitter)

### Post-Processing

**Interpolation:** Auto-fills small gaps (≤3 frames) in missing detections

- Only fills gaps bounded by valid data
- Uses linear interpolation between valid frames
- Preserves detection failures when unbounded

### Automatic Cleanup

**With `--delete` flag:**

1. Extracts landmarks → JSON
2. Deletes source video
3. Frees disk space automatically

**Status:** Logged to console:

```
✅ Extracted [N] frames
💾 Saved to: assets/signatures/asl/where.json
🗑️  Deleted: where_ref_yt.mp4
```

---

## Language Support

| Code | Language               | Status     | Notes                          |
| ---- | ---------------------- | ---------- | ------------------------------ |
| ASL  | American Sign Language | ✅ Active  | 4 words: hello, where, you, go |
| BSL  | British Sign Language  | ✅ Active  | Reference set uploaded         |
| JSL  | Japanese Sign Language | 📋 Planned | Phase 5                        |
| CSL  | Chinese Sign Language  | 📋 Planned | Phase 5                        |
| LSF  | French Sign Language   | 📋 Planned | Phase 5                        |

---

## Workflow Examples

### Adding a Reference Video (Best Practice)

1. **Obtain clear reference video** (YouTube, institutional archive)
   - Full gesture (no clipping)
   - Clear lighting
   - Single source (not composite)

2. **Place in raw_videos**

   ```bash
   cp reference_video.mp4 assets/raw_videos/lexicon/
   ```

3. **Extract using unified pipeline**

   ```bash
   python3 extract_signatures.py --video reference_video.mp4 --sign where --lang asl --delete
   ```

4. **Verify output**

   ```bash
   ls -la assets/signatures/asl/where.json
   ```

5. **Test recognition**

   ```bash
   python3 test_recognition_quality.py
   ```

6. **Analyze decision** (replace vs keep)
   - Check similarity metrics in output
   - Compare before/after if replacing existing data
   - See: [docs/SIGNATURE_STRATEGY.md](SIGNATURE_STRATEGY.md) for decision framework

### Multi-Language Expansion (Future)

For each new language:

```bash
# 1. Extract reference videos
python3 extract_signatures.py --video hello_ref_jsl.mp4 --sign hello --lang jsl --delete
python3 extract_signatures.py --video where_ref_jsl.mp4 --sign where --lang jsl --delete
python3 extract_signatures.py --video you_ref_jsl.mp4 --sign you --lang jsl --delete
python3 extract_signatures.py --video go_ref_jsl.mp4 --sign go --lang jsl --delete

# 2. Validate cross-language similarity
python3 test_recognition_smoothed.py  # Run recognition tests
```

---

## Troubleshooting

### Video Not Found

```
❌ Video file not found: /path/to/video.mp4
```

**Solution:** Verify file exists and path is correct

### No Landmarks Detected

```
✅ Extracted 0 frames
```

**Cause:** Video too dark/blurry or hand/pose not visible  
**Solution:** Use clearer reference video

### Permission Denied on Delete

```
⚠️  Could not delete video.mp4: Permission denied
```

**Solution:** Check file permissions or omit `--delete` flag

### Low Frame Count

```
✅ Extracted 12 frames
```

**Note:** Short videos are OK for reference; WLASL target is 20-400 frames for single words

---

## Related Files

- **Core:** `extract_signatures.py` - Unified extraction engine
- **Test tool:** `test_recognition_quality.py` - Analyze all word similarities
- **Strategy guide:** `docs/SIGNATURE_STRATEGY.md` - Decision framework for replace vs keep
- **Smoothing:** `smooth_signatures.py` - Apply temporal filtering (optional)

---

## Cleanup Philosophy

**Automatic cleanup via --delete flag:**

```bash
python3 extract_signatures.py --video video.mp4 --sign word --lang ASL --delete
# Extracts → Saves JSON → Deletes video (all in one command)
```

**Why automatic cleanup?**

- Prevents orphaned video files
- Saves disk space (videos are large)
- Consistent with wlasl_pipeline.py pattern
- Encourages developers to always cleanup

**When to use --delete:**

- ✅ Always for reference videos (extract once, don't need source)
- ✅ Always for testing/analysis videos
- ❌ Only skip if you need to re-extract with different settings

---

## Architecture Philosophy

**Single source > Composite sources**

- Clear reference video > Multiple WLASL videos
- Consistent landmarks > Averaged landmarks
- Simple data > Complex algorithms

**Unified pipeline > Bespoke scripts**

- Reusable CLI tool
- Consistent output format
- Maintenance burden reduced
- Extensible to new languages

**Test systematically, not ad-hoc**

- Use `test_recognition_quality.py` for all analysis
- No one-off test files per word
- Decisions documented in SIGNATURE_STRATEGY.md

---

**Last Updated:** 2026-01-24  
**Status:** ✅ Production Ready
