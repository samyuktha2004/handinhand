#!/usr/bin/env python3
"""
Single-Language Accuracy Test

Test one sign language at a time to verify skeleton extraction is accurate
before attempting dual-language comparison.

WORKFLOW:
    1. Test ASL alone
    2. Verify skeleton looks correct
    3. Test BSL alone
    4. Then try dual-screen (--dual flag)

OPTIMIZATION:
    - Frame decimation: Process every Nth frame to reduce CPU
    - Single skeleton stream (not dual)
    - Lightweight rendering

Usage:
    python3 test_single_accuracy.py asl hello_0              # Test ASL hello_0
    python3 test_single_accuracy.py bsl hello                # Test BSL hello
    python3 test_single_accuracy.py asl hello_1 --decimate 2 # Every 2nd frame
"""

import sys
import subprocess
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("""
╔════════════════════════════════════════════════════════════════╗
║     Single-Language Skeleton Accuracy Test                    ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
    python3 test_single_accuracy.py <lang> <signature> [--decimate N]

EXAMPLES:
    python3 test_single_accuracy.py asl hello_0
    python3 test_single_accuracy.py bsl hello
    python3 test_single_accuracy.py asl hello_1 --decimate 2

LANGUAGES:  asl, bsl
SIGNATURES: hello_0, hello_1, hello_2, where_0, you_0, you_1, you_2, go_0, go_1, go_2

WORKFLOW:
    Step 1: python3 test_single_accuracy.py asl hello_0
            → Verify ASL skeleton looks correct
    
    Step 2: python3 test_single_accuracy.py bsl hello
            → Verify BSL skeleton looks correct
    
    Step 3: python3 skeleton_debugger.py --dual
            → Try side-by-side (only after Step 1 & 2 pass)

WHY SINGLE-SCREEN FIRST?
    • Lower CPU (single skeleton stream)
    • Easier to spot errors (skeleton cut off, normalization wrong)
    • Verify each language independently
    • THEN combine them

CONTROLS:
    SPACE: Play/Pause
    </>:   Frame navigation
    n:     Toggle normalization
    d:     Toggle dots
    q:     Quit
""")
        return 1
    
    lang = sys.argv[1].lower()
    sig = sys.argv[2].lower()
    
    # Validate inputs
    valid_langs = ['asl', 'bsl']
    if lang not in valid_langs:
        print(f"❌ Invalid language: {lang}. Choose from: {', '.join(valid_langs)}")
        return 1
    
    # Check signature exists
    sig_path = Path(f"assets/signatures/{lang}/{sig}.json")
    if not sig_path.exists():
        print(f"❌ Signature not found: {sig_path}")
        print(f"\nAvailable signatures in assets/signatures/{lang}:")
        import os
        for f in sorted(os.listdir(f"assets/signatures/{lang}")):
            if f.endswith('.json'):
                print(f"    - {f[:-5]}")
        return 1
    
    # Build command
    cmd = [
        sys.executable,
        'skeleton_debugger.py',
        '--sig1', sig,
        '--lang1', lang.upper(),
        '--sig2', sig,  # Duplicate for debugger (won't be used in single-screen)
        '--lang2', lang.upper(),
        # NOT using --dual, so defaults to single-screen
    ]
    
    # Get FPS from args if provided
    if '--decimate' in sys.argv:
        idx = sys.argv.index('--decimate')
        if idx + 1 < len(sys.argv):
            decimate = int(sys.argv[idx + 1])
            fps = max(5, 15 // decimate)
            cmd.extend(['--fps', str(fps)])
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║     Testing: {lang.upper()} - {sig}
║     Mode: Single-Screen (Low CPU)
╚════════════════════════════════════════════════════════════════╝

Starting skeleton viewer...

WHAT TO CHECK:
    ✓ Skeleton visible and not cut off?
    ✓ Joints drawn correctly (circles at each point)?
    ✓ Hands connected to body?
    ✓ Smooth motion (no jitter)?
    ✓ Matches real hand movements?

CONTROLS:
    SPACE = Play/Pause
    <- / -> = Frame navigation
    n = Toggle normalization
    d = Toggle joint dots
    q = Quit

ISSUES?
    • Skeleton cut off? → Need to adjust viewport in skeleton_drawer.py
    • Jitter? → Check normalization
    • Missing hand? → Check MediaPipe extraction
""")
    
    try:
        subprocess.run(cmd, check=False)
        print("\n✓ Test complete!")
        return 0
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
