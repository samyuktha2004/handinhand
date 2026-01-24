# Architecture Consolidation - Unified Pipeline

**Date:** January 24, 2026  
**Change:** Consolidated video extraction into single unified pipeline  
**Impact:** Cleaner codebase, no redundant scripts, consistent approach

---

## What Changed

### Before ❌

```
extract_signatures.py   # Generic signature extractor (hardcoded to BSL lexicon)
extract_where_reference.py  # Custom WHERE reference extraction (one-off script)
wlasl_pipeline.py       # WLASL-specific pipeline
```

**Problem:** Bespoke scripts for each extraction type, inconsistent patterns

### After ✅

```
extract_signatures.py   # Unified pipeline with CLI support
├── Single video extraction
├── Directory processing
├── WLASL lexicon (default)
├── Frame range extraction
└── Auto-cleanup
```

**Benefit:** One tool, many modes, consistent output

---

## Key Improvements

### 1. CLI Support Added to `extract_signatures.py`

```bash
# Reference videos (new)
python3 extract_signatures.py --video ref.mp4 --sign where --lang asl --delete

# Directory processing (new)
python3 extract_signatures.py --dir assets/raw_videos/custom --lang jsl --delete

# Frame range extraction (new)
python3 extract_signatures.py --video video.mp4 --sign hello --lang asl --start 10 --end 50

# Default behavior (unchanged)
python3 extract_signatures.py
```

### 2. Removed Redundant Script

- Deleted `extract_where_reference.py` (one-off custom script)
- WHERE reference extracted with unified pipeline instead
- Result still saved to `assets/signatures/asl/where_0.json` ✓

### 3. Language Code Support Added

```python
--lang {ASL, BSL, JSL, CSL, LSF}
```

Ready for Phase 5 multi-language expansion

### 4. Auto-Cleanup Integrated

```bash
--delete  # Automatically remove source video after extraction
```

Follows same pattern as wlasl_pipeline.py

---

## Validation

### WHERE Signature Verified ✓

```bash
$ head -5 assets/signatures/asl/where_0.json
{
  "sign": "where",
  "language": "asl",
  "pose_data": [
    {
```

### Recognition Tests Pass ✓

```
Average similarity: 0.7339 (< 0.80 threshold)
WHERE: 0.5931 ✅ (improved from 0.9819)
```

### CLI Help Works ✓

```bash
$ python3 extract_signatures.py --help
usage: extract_signatures.py [-h] [--video VIDEO] [--sign SIGN]
                             [--lang {ASL,BSL,JSL,CSL,LSF}]
                             [--dir DIR] [--start START] [--end END]
                             [--output-dir OUTPUT_DIR] [--delete]
```

---

## Migration Path for Future

When extracting new language references (Phase 5):

```bash
# Instead of creating new scripts, use:
python3 extract_signatures.py --video hello_jsl.mp4 --sign hello --lang jsl --delete
python3 extract_signatures.py --video where_jsl.mp4 --sign where --lang jsl --delete
python3 extract_signatures.py --video you_jsl.mp4 --sign you --lang jsl --delete
python3 extract_signatures.py --video go_jsl.mp4 --sign go --lang jsl --delete
```

Consistent, repeatable, no new scripts needed.

---

## Documentation

- **Pipeline Guide:** [docs/EXTRACTION_PIPELINE.md](EXTRACTION_PIPELINE.md)
- **WHERE Case Study:** [docs/WHERE_ANALYSIS.md](WHERE_ANALYSIS.md)
- **Source:** `extract_signatures.py` (argparse-based CLI)

---

## Benefits

| Aspect                       | Before                                                          | After                                  |
| ---------------------------- | --------------------------------------------------------------- | -------------------------------------- |
| **Scripts**                  | 3 (extract_signatures, extract_where_reference, wlasl_pipeline) | 2 (extract_signatures, wlasl_pipeline) |
| **Consistency**              | Different patterns for WLASL vs reference                       | Unified CLI for all sources            |
| **Reference video handling** | Custom script needed                                            | --video flag in unified tool           |
| **Frame range extraction**   | Only in wlasl_pipeline                                          | Available for all video sources        |
| **Phase 5 readiness**        | Low (new scripts each language)                                 | High (proven reusable pattern)         |
| **Auto-cleanup**             | Only in wlasl_pipeline                                          | Available everywhere via --delete      |

---

**Status:** ✅ Complete  
**Next Phase:** Live video recognition testing (Phase 4.2)  
**Documentation:** Updated and consolidated
