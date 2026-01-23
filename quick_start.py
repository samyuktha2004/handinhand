#!/usr/bin/env python3
"""
Quick Reference: Using Your Sign Language Recognition Pipeline
================================================================

After running the WLASL pipeline, you'll have:
  1. .json signatures in assets/signatures/
  2. translation_map.json linking videos to signatures
  3. Deleted all .mp4 files (space saved!)

Now visualize and verify your signatures:
"""

print("""
╔════════════════════════════════════════════════════════════════╗
║  VERIFY SIGNATURE QUALITY (3D ANIMATION + ANALYSIS)           ║
╚════════════════════════════════════════════════════════════════╝

Usage:
    python3 verify_signatures.py <signature.json> [--animate]

Examples:
    # Just get quality report (no animation)
    python3 verify_signatures.py assets/signatures/hello_0.json

    # Full 3D animation with frame-by-frame visualization
    python3 verify_signatures.py assets/signatures/hello_0.json --animate

    # Export animation as GIF (slow, saves to hello_0_animation.gif)
    python3 verify_signatures.py assets/signatures/hello_0.json --animate --gif

What it does:
    ✅ Loads JSON signature with 46 landmarks per frame
    ✅ Shows 3D interactive skeleton plot
    ✅ Detects missing hand/face detections (zero-filled frames)
    ✅ Quality scores: 0-100 (100 = perfect)
    ✅ Color-codes: Red=left_hand, Blue=right_hand, Green=pose, Orange=face


╔════════════════════════════════════════════════════════════════╗
║  DOWNLOAD & EXTRACT NEW SIGNS (SELF-CLEANING PIPELINE)       ║
╚════════════════════════════════════════════════════════════════╝

Usage:
    python3 wlasl_pipeline.py

What it does:
    1. Searches WLASL_v0.3.json for your TARGET_GLOSSES
    2. Downloads first N video instances from YouTube
    3. Extracts MediaPipe landmarks (ONLY sign frames, using frame_start/end)
    4. Saves as JSON signatures
    5. Automatically deletes .mp4 files
    6. Updates translation_map.json

To add new words:
    Edit wlasl_pipeline.py line 14:
    TARGET_GLOSSES = ["hello", "you", "go", "where"]  # Add more here!
    
    Then run:
    python3 wlasl_pipeline.py


╔════════════════════════════════════════════════════════════════╗
║  YOUR CURRENT SETUP STATUS                                    ║
╚════════════════════════════════════════════════════════════════╝
""")

import os
import json

# Check what you have
sig_dir = "assets/signatures"
sig_files = [f for f in os.listdir(sig_dir) if f.endswith('.json')]

print(f"\n📊 Signatures in assets/signatures/: {len(sig_files)}")
for sig in sorted(sig_files):
    size_kb = os.path.getsize(os.path.join(sig_dir, sig)) / 1024
    print(f"   • {sig} ({size_kb:.1f} KB)")

print(f"\n🗺️  Translation Map: translation_map.json")
if os.path.exists('translation_map.json'):
    with open('translation_map.json') as f:
        tmap = json.load(f)
    
    # Group by gloss
    glosses = {}
    for key, val in tmap.items():
        gloss = val.get('gloss') or key
        if gloss not in glosses:
            glosses[gloss] = []
        glosses[gloss].append(key)
    
    for gloss in sorted(glosses.keys()):
        print(f"   • {gloss.upper()}: {len(glosses[gloss])} instances")

print(f"""

╔════════════════════════════════════════════════════════════════╗
║  NEXT STEPS                                                   ║
╚════════════════════════════════════════════════════════════════╝

1. Verify your signatures:
   python3 verify_signatures.py assets/signatures/hello_0.json --animate

2. Add more words to pipeline:
   Edit TARGET_GLOSSES in wlasl_pipeline.py
   Run: python3 wlasl_pipeline.py

3. When you're ready to build a recognition model:
   You'll use the JSON signatures from assets/signatures/
   The translation_map.json tells you which signature is which word

╔════════════════════════════════════════════════════════════════╗
""")
