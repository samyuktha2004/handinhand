# LinguaSign AI - Installation & Setup Guide

## ⚠️ Important: Python Version Requirement

**MediaPipe currently supports Python 3.8 - 3.12 ONLY**

Your system: Python 3.13.2

### Solution: Switch to Python 3.12

#### Option A: Using Homebrew (macOS)

```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Option B: Using pyenv (Recommended for multiple Python versions)

```bash
# Install pyenv
brew install pyenv

# Install Python 3.12
pyenv install 3.12.0

# Use Python 3.12 for this project
pyenv local 3.12.0

# Then run setup
./setup_simple.sh
```

#### Option C: Using Python.org

1. Download Python 3.12 from https://www.python.org/downloads/
2. Install it
3. Use it to create the venv:

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Quick Start (After Python 3.12 is set up)

```bash
# Use the simple setup script (works best)
./setup_simple.sh
```

This script will:

- ✅ Create and activate a virtual environment
- ✅ Install all dependencies
- ✅ Verify core packages work
- ✅ Report any issues

---

## Installation Methods

### Option 1: Advanced Setup Script (RECOMMENDED)

**Best for**: Most users, handles errors gracefully

```bash
./setup_env_advanced.sh
```

### Option 2: Poetry (BEST for reproducibility)

**Best for**: Production environments, team collaboration

Poetry ensures exact dependency versions across all machines.

```bash
# Install Poetry if needed
pip install poetry

# Create environment and install dependencies
poetry install

# Activate Poetry environment
poetry shell
```

**Why Poetry?**

- ✅ Locks exact versions (reproducible across machines)
- ✅ Better dependency conflict resolution
- ✅ Simpler to manage and update packages
- ✅ Creates `poetry.lock` file for reproducibility

### Option 3: Manual pip Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade tools
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
```

---

## Troubleshooting

### Issue: `ERROR: Could not find a version that satisfies mediapipe`

**Cause**: You're using Python 3.13+, but MediaPipe only supports Python 3.8-3.12

**Solution**: Switch to Python 3.12 using the methods above

```bash
# Quick check of your Python version
python3 --version

# If it says 3.13.x, you need to switch to 3.12
```

---

### Issue: `ModuleNotFoundError: No module named 'matplotlib'`

```bash
pip install --no-cache-dir -r requirements.txt
```

**Solution 2: Install packages individually**

```bash
pip install --upgrade numpy scipy pandas scikit-learn matplotlib Pillow
pip install --no-cache-dir opencv-python mediapipe
pip install --upgrade python-socketio python-engineio
```

**Solution 3: Use Poetry**

```bash
pip install poetry
poetry install
poetry shell
```

---

### Issue: `ERROR: Could not find a version that satisfies the requirement`

**Cause**: Version conflicts between packages

**Solution**: Update requirements.txt to use flexible versions (already done):

```bash
# Old (pinned versions - often conflicts)
matplotlib==3.8.2

# New (flexible versions - better compatibility)
matplotlib>=3.7.0
```

---

### Issue: MediaPipe installation fails

**macOS with M1/M2 chips:**

```bash
# Install via Homebrew first
brew install opencv

# Then install via pip
pip install --no-cache-dir mediapipe opencv-python
```

**Linux/Windows:**

```bash
pip install --upgrade mediapipe --no-cache-dir
```

---

### Issue: Virtual environment activation fails

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# If still failing, recreate:
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

---

## Verifying Installation

After installation, verify everything works:

```bash
# Check all imports
python3 << EOF
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import sklearn
import scipy
import matplotlib.pyplot as plt
import socketio
print("✅ All imports successful!")
EOF

# Or use the provided script
./setup_env_advanced.sh  # Runs verification automatically
```

---

## Using Poetry (Recommended for Teams)

### Setup Poetry once:

```bash
pip install poetry
```

### Then, to set up the project:

```bash
poetry install
poetry shell  # Activates the environment
```

### To add a new package:

```bash
poetry add package-name
```

### To update all packages:

```bash
poetry update
```

### Lock exact versions:

```bash
poetry lock  # Creates poetry.lock file
```

Share `pyproject.toml` and `poetry.lock` with your team for identical environments.

---

## Project Files

| File                    | Purpose                                          |
| ----------------------- | ------------------------------------------------ |
| `requirements.txt`      | Flexible pip dependencies (good for quick setup) |
| `pyproject.toml`        | Poetry configuration (reproducible environments) |
| `poetry.lock`           | Locked versions (when using Poetry)              |
| `setup_env_advanced.sh` | Automated setup with troubleshooting             |
| `setup_env.sh`          | Simple setup script                              |

---

## Next Steps

Once installation is complete:

```bash
# Activate environment
source venv/bin/activate  # or `poetry shell` if using Poetry

# Extract signatures from your videos
python3 extract_signatures.py

# Verify signature quality
python3 verify_signatures.py assets/signatures/HELLO.json --animate
```

---

## Dependencies Overview

| Package         | Version | Purpose                        |
| --------------- | ------- | ------------------------------ |
| numpy           | ^1.24.0 | Numerical computing            |
| opencv-python   | ^4.8.0  | Video processing               |
| mediapipe       | ^0.10.0 | Pose/hand/face detection       |
| scipy           | ^1.11.0 | Cosine similarity calculations |
| matplotlib      | ^3.7.0  | Visualization & debugging      |
| pandas          | ^2.0.0  | Data manipulation              |
| scikit-learn    | ^1.3.0  | ML utilities                   |
| Pillow          | ^10.0.0 | Image processing               |
| python-socketio | ^5.9.0  | Real-time communication        |
| python-engineio | ^4.7.0  | Socket.io backend              |

---

## Common Commands

```bash
# Activate environment
source venv/bin/activate

# List installed packages
pip list

# Check specific package version
pip show matplotlib

# Update all packages
pip install --upgrade -r requirements.txt

# Verify imports work
python3 -c "import cv2, mediapipe, matplotlib, scipy; print('✅ OK')"

# Deactivate environment
deactivate
```

---

## Need Help?

If you encounter issues:

1. **Run the advanced setup**: `./setup_env_advanced.sh`
2. **Check Python version**: `python3 --version` (should be 3.8+)
3. **Check disk space**: `df -h` (ensure 2GB+ available)
4. **Try Poetry**: `pip install poetry && poetry install`
5. **Review the logs**: Check `install.log` created by setup script

For platform-specific issues:

- **macOS M1/M2**: See MediaPipe section above
- **Windows**: Use Windows PowerShell, not cmd
- **Linux**: May need `python3-dev` package
