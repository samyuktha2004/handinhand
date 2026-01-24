#!/usr/bin/env python3
"""
Quick test of skeleton debugger with fixed coordinate scaling.
Run this to verify the debugger works with the hello signatures.
"""

import sys
import subprocess

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║         Skeleton Debugger Test                                ║
║         Testing ASL hello_0 vs BSL hello                      ║
╚════════════════════════════════════════════════════════════════╝

Starting debugger with fixed coordinate scaling...
    
Expected:
  ✓ Two side-by-side skeletons (left: ASL, right: BSL)
  ✓ Green lines for body, Blue for left hand, Red for right hand
  ✓ Frame counts: ASL 0/55, BSL 0/36
  ✓ Sync status should show "??? DESYNC (19 frames)"

Controls:
  SPACE: Play/Pause
  ←/→: Frame navigation
  'n': Toggle normalization
  'd': Toggle joint dots
  'q': Quit

Press SPACE to start playback, then 'q' to quit test.
""")
    
    try:
        # Run the debugger
        subprocess.run([sys.executable, 'skeleton_debugger.py'], check=False)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    
    print("\n✓ Test complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
