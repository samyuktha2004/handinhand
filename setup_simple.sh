#!/usr/bin/env bash

# Simple, step-by-step setup for LinguaSign AI
# Designed to work around common platform-specific issues

set -e

echo "🔧 LinguaSign AI - Simple Setup"
echo "================================"
echo ""

# Check Python
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

echo "✅ Python: $($PYTHON_CMD --version)"
echo ""

# Create venv
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "📥 Installing dependencies..."
echo ""

# Upgrade tools
pip install --quiet --upgrade pip setuptools wheel

# Install numpy FIRST (foundation)
echo "1️⃣  Installing numpy..."
pip install --quiet "numpy>=1.24.0,<2.0.0"

# Core data science
echo "2️⃣  Installing scipy, pandas, scikit-learn..."
pip install --quiet "scipy>=1.11.0" "pandas>=2.0.0" "scikit-learn>=1.3.0" "Pillow>=10.0.0"

# Matplotlib
echo "3️⃣  Installing matplotlib..."
pip install --quiet "matplotlib>=3.7.0"

# OpenCV
echo "4️⃣  Installing opencv-python..."
pip install --quiet "opencv-python>=4.8.0" || pip install --quiet "opencv-python-headless>=4.8.0"

# Socket packages
echo "5️⃣  Installing socket libraries..."
pip install --quiet "python-socketio>=5.9.0" "python-engineio>=4.7.0"

# MediaPipe - try different approaches
echo "6️⃣  Installing mediapipe (this may take a moment)..."
if pip install --quiet "mediapipe>=0.10.0" 2>/dev/null; then
    echo "   ✅ Mediapipe installed"
else
    echo "   ⚠️  Standard mediapipe failed, trying alternative..."
    if pip install --quiet --no-binary mediapipe mediapipe 2>/dev/null; then
        echo "   ✅ Mediapipe installed from source"
    else
        echo "   ❌ Mediapipe installation failed - will need manual setup"
        echo "      For macOS M1/M2: brew install mediapipe"
        echo "      For others: pip install --no-cache-dir mediapipe"
    fi
fi

echo ""
echo "🔍 Verifying critical packages..."
$PYTHON_CMD << 'EOF'
import sys
packages = [
    ('numpy', 'numpy'),
    ('scipy', 'scipy'),
    ('pandas', 'pandas'),
    ('sklearn', 'scikit-learn'),
    ('matplotlib', 'matplotlib'),
    ('PIL', 'Pillow'),
    ('cv2', 'opencv-python'),
]

missing = []
for import_name, display_name in packages:
    try:
        __import__(import_name)
        print(f"✅ {display_name}")
    except ImportError:
        print(f"❌ {display_name}")
        missing.append(display_name)

if missing:
    print(f"\n⚠️  Missing: {', '.join(missing)}")
    sys.exit(1)

print("\n✅ Core packages verified!")
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Some core packages failed. Running full requirements..."
    pip install -r requirements.txt --no-cache-dir
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Verify everything works:"
echo "   python3 << EOF"
echo "   import cv2, numpy, scipy, matplotlib, pandas"
echo "   print('✅ All working!')"
echo "   EOF"
