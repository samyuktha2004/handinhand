#!/usr/bin/env python3
"""Verify all required packages are installed and working."""

import sys

print("Python version:", sys.version)
print("\n✅ Verifying package imports...\n")

packages = [
    ('cv2', 'opencv-python'),
    ('mediapipe', 'mediapipe'),
    ('numpy', 'numpy'),
    ('pandas', 'pandas'),
    ('sklearn', 'scikit-learn'),
    ('scipy', 'scipy'),
    ('matplotlib.pyplot', 'matplotlib'),
    ('PIL', 'Pillow'),
    ('socketio', 'python-socketio'),
]

failed = []
for import_name, display_name in packages:
    try:
        __import__(import_name)
        print(f"  ✅ {display_name}")
    except ImportError as e:
        print(f"  ❌ {display_name}: {e}")
        failed.append(display_name)

if failed:
    print(f"\n❌ Failed packages: {', '.join(failed)}")
    sys.exit(1)
else:
    print("\n🎉 All packages imported successfully!")
    print("\n✨ Your environment is ready to use!")
    sys.exit(0)
