#!/usr/bin/env python3
"""
Quick Start: Skeleton Debugger
===============================
Run this script to test the skeleton debugger immediately.
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Skeleton Debugger Quick Start                        ║
║   Verify ASL/BSL signature preservation visually            ║
╚══════════════════════════════════════════════════════════════╝

This will launch the skeleton debugger with:
  • Signature 1: ASL hello_0 (one-handed greeting)
  • Signature 2: BSL hello (target translation)
  
The debugger will display two skeletons side-by-side.

What to verify:
  ✓ ASL skeleton shows one-handed motion
  ✓ BSL skeleton shows correct hand position for that language
  ✓ Both skeletons stay centered (normalization working)
  ✓ Movements are smooth (no jitter or frame drops)
  ✓ Hand shapes are clear (fingers spread/curled as needed)

Controls:
  SPACE: Play/Pause
  ←/→: Navigate frames
  'n': Toggle normalization
  'd': Toggle joint dots
  's': Toggle side-by-side mode
  'q': Quit

""")
    
    # Check if signatures exist
    asl_path = Path("assets/signatures/asl/hello_0.json")
    bsl_path = Path("assets/signatures/bsl/hello.json")
    
    if not asl_path.exists():
        print(f"❌ ERROR: ASL signature not found at {asl_path}")
        print("   Run: python3 wlasl_pipeline.py (to extract signatures)")
        return 1
    
    if not bsl_path.exists():
        print(f"⚠️  WARNING: BSL signature not found at {bsl_path}")
        print("   Using ASL hello_0 for both displays")
        cmd = ["python3", "skeleton_debugger.py", "--sig1", "hello_0", "--sig2", "hello_0", "--lang1", "asl", "--lang2", "asl"]
    else:
        cmd = ["python3", "skeleton_debugger.py"]
    
    print("Launching debugger...\n")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nDebugger closed by user.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running debugger: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
