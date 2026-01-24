# Testing & Running Guide

Quick reference for manually testing and running the sign language recognition system.

## Skeleton Viewer (skeleton_debugger.py)

### Dual-Display Mode (ASL vs BSL)

Compare two signatures side-by-side with synchronized frame navigation.

**Using full paths (recommended) NOT FUNCTIONAL CHECK THIS:**

```bash
# Hello sign (ASL vs BSL)
python skeleton_debugger.py --sig1 assets/signatures/asl/hello_0.json --sig2 assets/signatures/bsl/hello.json --dual

# Where sign
python skeleton_debugger.py --sig1 assets/signatures/asl/where_0.json --sig2 assets/signatures/bsl/where.json --dual

# You sign
python skeleton_debugger.py --sig1 assets/signatures/asl/you_0.json --sig2 assets/signatures/bsl/you.json --dual

# Go sign
python skeleton_debugger.py --sig1 assets/signatures/asl/go_0.json --sig2 assets/signatures/bsl/go.json --dual
```

**Using signature names (shorthand) WORKING:**

```bash
# Hello sign (ASL vs BSL)
python skeleton_debugger.py --lang1 asl --sig1 hello_0 --lang2 bsl --sig2 hello --dual

# Where sign
python skeleton_debugger.py --lang1 asl --sig1 where_0 --lang2 bsl --sig2 where --dual

# You sign
python skeleton_debugger.py --lang1 asl --sig1 you_0 --lang2 bsl --sig2 you --dual

# Go sign
python skeleton_debugger.py --lang1 asl --sig1 go_0 --lang2 bsl --sig2 go --dual
```

#### Options

- `--no-joints` - Hide skeleton joint circles (cleaner visualization)
- `--dual` - Side-by-side display (required for comparison)
- `--fps N` - Set playback speed (default: 15)

#### Controls (while viewer is running)

- **Arrow Keys Left/Right**: Navigate frames
- **Arrow Keys Up/Down**: Adjust playback speed
- **s**: Toggle between sig1 and sig2 (single-screen mode)
- **Esc/q**: Quit

### Single-Display Mode

View one signature at a time.

**Using full paths:**

```bash
# ASL hello
python skeleton_debugger.py --sig1 assets/signatures/asl/hello_0.json

# BSL hello
python skeleton_debugger.py --sig1 assets/signatures/bsl/hello.json

# BSL go (full signature)
python skeleton_debugger.py --sig1 assets/signatures/bsl/go.json
```

**Or using signature names:**

```bash
# ASL hello
python skeleton_debugger.py --lang1 asl --sig1 hello_0

# BSL hello
python skeleton_debugger.py --lang1 bsl --sig1 hello

# BSL go
python skeleton_debugger.py --lang1 bsl --sig1 go
```

#### Options

- `--no-joints` - Hide skeleton joint circles
- `--fps N` - Set playback speed (default: 15)

## Recognition Engine

### Live Recognition Testing

Test real-time recognition on webcam.

```bash
# Start recognition UI (live webcam)
python recognition_engine_ui.py
```

**Controls:**

- **Spacebar**: Start/stop recording gesture
- **g**: Recognize (compare against signatures)
- **s**: Show/hide skeleton
- **n**: Show/hide joint numbers
- **ESC**: Quit

### Test Recognition Quality

Batch test recognition accuracy across all test words.

```bash
# Run comprehensive recognition test
python test_recognition_quality.py
```

**Output:** Accuracy metrics for ASL and BSL across all test words (hello, you, go, where)

## Data Management

### Extract Signatures from Video

Extract and save gesture landmarks from video files.

```bash
# Extract from single video
python extract_signatures.py --video video.mp4 --sign hello --lang asl

# Extract from directory
python extract_signatures.py --dir assets/raw_videos/custom --lang asl

# Extract and delete source videos after processing
python extract_signatures.py --dir assets/raw_videos/lexicon --lang asl --delete
```

### Verify Installation

Check that all dependencies and data are properly installed.

```bash
# Verify system setup
python verify_installation.py

# Verify extracted signatures
python verify_signatures.py
```

## Performance & Debugging

### Frame Range Optimization Test

Test optimal frame range extraction for gestures.

```bash
# Analyze frame ranges for better extraction
python test_frame_range_extraction.py
```

### Embedding Generation

Generate or regenerate embeddings for recognition.

```bash
# Generate all embeddings
python generate_embeddings.py
```

## Common Workflows

### Quick Visual Check

Compare ASL and BSL hello gestures side-by-side:

```bash
# With full paths
python skeleton_debugger.py --sig1 assets/signatures/asl/hello_0.json --sig2 assets/signatures/bsl/hello.json --dual --no-joints

# Or shorthand
python skeleton_debugger.py --lang1 asl --sig1 hello_0 --lang2 bsl --sig2 hello --dual --no-joints
```

### Full Test Suite

Run complete validation:

```bash
python verify_installation.py
python test_recognition_quality.py
```

### Live Testing

Test recognition on real gestures:

```bash
python recognition_engine_ui.py
```

### Data Extraction Workflow

Process new videos:

```bash
# 1. Extract signatures
python extract_signatures.py --dir /path/to/videos --lang asl

# 2. Verify extraction
python verify_signatures.py

# 3. Generate embeddings
python generate_embeddings.py

# 4. Test recognition
python test_recognition_quality.py
```

## File Locations

### Signatures (Read-Only in Tests)

```
assets/signatures/
├── asl/
│   ├── hello_0.json, hello_1.json
│   ├── you_0.json, you_1.json, you_2.json
│   ├── go_0.json, go_1.json, go_2.json
│   └── where_0.json
└── bsl/
    ├── hello.json
    ├── you.json
    ├── go.json
    ├── where.json
    └── hello_where_are_you_going.json (compound)
```

### Embeddings (Generated)

```
assets/embeddings/
├── asl/
│   ├── hello_mean.npy
│   ├── you_mean.npy
│   ├── go_mean.npy
│   └── where_mean.npy
└── bsl/
    ├── hello_mean.npy
    ├── you_mean.npy
    ├── go_mean.npy
    └── where_mean.npy
```

### Raw Videos (Optional)

```
assets/raw_videos/
├── lexicon/          # WLASL dataset (partial)
└── benchmarks/       # Test videos
```

## Troubleshooting

### If Skeleton Viewer Crashes

- Ensure JSON files exist and are valid: `python verify_signatures.py`
- Check frame width/height in metadata match screen resolution
- Try `--no-joints` flag for reduced rendering load

### If Recognition Fails

- Regenerate embeddings: `python generate_embeddings.py`
- Verify signatures extracted correctly: `python verify_signatures.py`
- Check camera/video input is working: `python recognition_engine_ui.py`

### If Embedding Generation Hangs

- Verify all signatures have valid landmarks: `python verify_signatures.py`
- Check disk space for .npy files (~5MB each)
- Ensure venv is activated: `source venv/bin/activate`

## Performance Notes

- **Dual-display**: Higher CPU usage (~60-70%) due to simultaneous rendering
- **Single-display**: Lower CPU usage (~20-30%)
- **Live recognition**: ~30-50ms per frame on modern CPU
- Frame rate auto-adjusts based on rendering speed

## Next Steps

- Phase 4.2: Live facial features (eyebrows, head orientation)
- Phase 5: Multi-language expansion (JSL, CSL, LSF)
- Avatar stitching from recognized signatures
