#!/usr/bin/env bash

# Comprehensive setup script with troubleshooting for LinguaSign AI
# This script handles common issues with dependency installation

set -e

echo "🔧 LinguaSign AI - Advanced Setup with Troubleshooting"
echo "======================================================"
echo ""

# Check Python version
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo "✅ Found $PYTHON_VERSION"
echo ""

# Validate Python version is 3.8+
PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_MINOR" -lt 8 ]; then
    echo "❌ Python 3.8 or higher is required. Found Python 3.$PYTHON_MINOR"
    exit 1
fi

# Create virtual environment
VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  Virtual environment already exists."
    read -p "Do you want to remove and recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
fi

echo ""
echo "🚀 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo ""
echo "📥 Upgrading core tools..."
pip install --upgrade pip setuptools wheel --quiet

echo ""
echo "📊 Checking for dependency resolution issues..."

# Try to install with error handling
install_with_fallback() {
    echo ""
    echo "🔄 Attempting standard installation..."
    if pip install -r requirements.txt --upgrade 2>&1 | tee install.log; then
        echo "✅ Installation successful!"
        return 0
    else
        echo ""
        echo "⚠️  Standard installation encountered issues. Trying alternative approach..."
        echo ""
        
        # Try Poetry if available
        if command -v poetry &> /dev/null; then
            echo "📚 Poetry detected. Using Poetry for dependency resolution..."
            poetry install
            return 0
        fi
        
        # Fallback: Install packages individually with specific strategies
        echo "🔧 Installing packages individually with optimized settings..."
        
        # Core packages first
        echo "   Installing numpy..."
        pip install "numpy>=1.24.0,<2.0.0" --upgrade
        
        echo "   Installing scipy..."
        pip install "scipy>=1.11.0" --upgrade
        
        echo "   Installing pandas..."
        pip install "pandas>=2.0.0" --upgrade
        
        echo "   Installing scikit-learn..."
        pip install "scikit-learn>=1.3.0" --upgrade
        
        echo "   Installing matplotlib..."
        pip install "matplotlib>=3.7.0" --upgrade
        
        echo "   Installing Pillow..."
        pip install "Pillow>=10.0.0" --upgrade
        
        echo "   Installing opencv-python..."
        # OpenCV sometimes needs special handling
        pip install "opencv-python>=4.8.0" --upgrade --no-cache-dir
        
        echo "   Installing mediapipe..."
        # MediaPipe can be finicky; try prebuilt wheel
        pip install "mediapipe>=0.10.0" --upgrade --no-cache-dir
        
        echo "   Installing socketio packages..."
        pip install "python-socketio>=5.9.0" "python-engineio>=4.7.0" --upgrade
        
        echo ""
        echo "✅ Individual package installation complete!"
        return 0
    fi
}

install_with_fallback

echo ""
echo "✅ Verifying imports..."
python3 -c "
import sys
packages = ['cv2', 'mediapipe', 'numpy', 'pandas', 'sklearn', 'scipy', 'matplotlib']
failed = []

for package in packages:
    try:
        __import__(package)
        print(f'  ✅ {package}')
    except ImportError as e:
        print(f'  ❌ {package}: {e}')
        failed.append(package)

if failed:
    print()
    print(f'⚠️  Failed to import: {', '.join(failed)}')
    sys.exit(1)
else:
    print()
    print('✅ All imports successful!')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "🔧 Some packages failed to import. Running diagnostics..."
    echo ""
    pip list | grep -E "numpy|scipy|opencv|mediapipe|pandas|matplotlib|scikit-learn" || true
    echo ""
    echo "💡 Troubleshooting tips:"
    echo "   1. Check if you have enough disk space"
    echo "   2. Try: pip install --upgrade pip"
    echo "   3. Try: pip install --no-cache-dir -r requirements.txt"
    echo "   4. On macOS with M1/M2: brew install opencv might be needed"
    echo "   5. Consider using Poetry: pip install poetry && poetry install"
    exit 1
fi

echo ""
echo "======================================================"
echo "✅ Setup Complete! Environment is ready."
echo "======================================================"
echo ""
echo "🎯 Next steps:"
echo ""
echo "1. Activate environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Extract signatures from videos:"
echo "   python3 extract_signatures.py"
echo ""
echo "3. Verify signature quality:"
echo "   python3 verify_signatures.py assets/signatures/HELLO.json --animate"
echo ""
echo "📚 For more options:"
echo "   python3 verify_signatures.py --help"
echo "   python3 extract_signatures.py --help"
echo ""
echo "To deactivate: deactivate"
