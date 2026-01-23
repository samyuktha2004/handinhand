# LinguaSign AI - Development Progress

**Project**: Sign Language Kinematics-to-Kinematics Translation Tool  
**Last Updated**: 23 January 2026  
**Status**: 🟡 In Progress - Phase 1: Mocap & Embedding  
**Note**: ⚠️ Python 3.13 detected. MediaPipe requires Python 3.12 or lower. See SETUP_GUIDE.md

---

## ✅ Completed Tasks

### 1. Python Environment Setup

- **File**: [requirements.txt](requirements.txt)
- **Status**: ✅ Complete
- **Details**:
  - Created requirements.txt with all dependencies
  - Included MediaPipe, OpenCV, scikit-learn, pandas, numpy
  - Added scipy for cosine similarity calculations
  - Added matplotlib for visualization
  - Added python-socketio/engineio for frontend communication
  - Pinned all package versions for consistency

### 2. Automated Environment Setup Script

- **File**: [setup_env.sh](setup_env.sh)
- **Status**: ✅ Complete
- **Details**:
  - Bash script to automate venv creation
  - Automatic pip upgrade
  - Guided user setup with clear instructions
  - Made executable (chmod +x)

### 3. Golden Signature Extraction Script

- **File**: [extract_signatures.py](extract_signatures.py)
- **Status**: ✅ Complete
- **Details**:
  - MediaPipe Holistic integration (static_image_mode=False)
  - Extracts 21 landmarks from each hand
  - Extracts 6 pose landmarks (shoulders/arms: indices 11-16)
  - Extracts 4 face landmarks (eyebrows: indices 70, 107, 300, 336)
  - Zero-filling for missed detections
  - Processes individual words from `assets/raw_videos/lexicon/`
  - Processes benchmark sentence: `bsl_hello_where_are_you_going.mp4`
  - Outputs JSON with structure: `{sign, language, pose_data[], metadata}`
  - Frame-by-frame progress tracking
  - Error handling for missing files

### 4. Signature Quality Verification Script

- **File**: [verify_signatures.py](verify_signatures.py)
- **Status**: ✅ Complete
- **Details**:
  - Loads and analyzes extracted signature JSON files
  - 3D animation of landmarks with color-coding (Red=Left Hand, Blue=Right Hand, Green=Pose, Orange=Face)
  - Detects zero-filled frames (missing detections)
  - Quality score calculation (0-100)
  - Generates detailed quality report with recommendations
  - Per-landmark-group analysis (which parts have detection issues)
  - Statistics overlay on animation (frame count, zero percentage)
  - Optional GIF export for visual inspection
  - Warnings when detection quality is poor (>20% zero-filled frames)
  - Identifies specific problem areas for re-recording

### 5. Dependency Management & Setup

- **Files**: [requirements.txt](requirements.txt), [pyproject.toml](pyproject.toml), [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Status**: ✅ Complete
- **Details**:
  - Flexible version requirements for better compatibility
  - Poetry support for reproducible environments
  - Multiple setup scripts with error handling
  - Comprehensive troubleshooting guide
  - ⚠️ **Note**: MediaPipe requires Python 3.8-3.12 (Python 3.13 not yet supported)

---

## 🟡 In Progress / Next Steps

### Phase 1: Mocap & Embedding

- [ ] **Test Signature Extraction**
  - Run extract_signatures.py with sample videos
  - Verify JSON output structure and data quality
  - Debug any MediaPipe detection issues
- [x] **Visualization/Debugging**
  - ✅ Use matplotlib to plot landmarks with animation
  - ✅ Verify signatures look correct visually
  - ✅ Automated data quality analysis

### Phase 2: Real-time Recognition

- [ ] **Build Recognition Pipeline**
  - Create webcam capture script using OpenCV
  - Implement cosine similarity comparison (scipy.spatial.distance.cosine)
  - Set threshold for match detection (target: > 0.90)
  - Real-time landmark comparison against JSON library

- [ ] **Socket.io Backend**
  - Set up Python backend with python-socketio
  - Implement live frame processing
  - Send recognition results to React frontend

### Phase 3: Avatar Rendering

- [ ] **VRM Avatar Integration**
  - Load VRM character from Vroid Studio
  - Map extracted landmarks to character bones
  - Implement animation driver
  - Connect to React frontend via Socket.io

---

## 📋 Project Structure

```
handinhand/
├── README.md                    # Project overview
├── PRD.md                       # Product requirements
├── progress.md                  # This file - progress tracking
├── requirements.txt             # Python dependencies
├── setup_env.sh                 # Environment setup script (executable)
├── extract_signatures.py        # Golden signature extraction script
├── verify_signatures.py         # Signature quality verification & visualization
├── venv/                        # Virtual environment (created by setup_env.sh)
└── assets/
    ├── signatures/              # Output: Golden signature JSON files
    ├── raw_videos/
    │   ├── lexicon/             # Individual word videos
    │   └── benchmarks/
    │       └── bsl_hello_where_are_you_going.mp4
    ├── animations/
    ├── wlasl_data/
    └── ...
```

---

## 🎯 Key Technologies

| Component     | Technology                          | Status        |
| ------------- | ----------------------------------- | ------------- |
| Vision        | MediaPipe Holistic                  | ✅ Integrated |
| ML Logic      | scipy.spatial.distance.cosine       | ✅ Ready      |
| Data Format   | JSON (landmarks)                    | ✅ Designed   |
| Frontend      | React + Three.js + @pixiv/three-vrm | ⏳ Next       |
| Communication | Socket.io (Python ↔ React)          | ✅ Installed  |
| Avatar        | VRM (.vrm models)                   | ⏳ Next       |

---

## 📊 Success Metrics (MVP)

- [ ] System correctly recognizes "HELLO" within < 500ms
- [ ] Cosine similarity threshold (> 0.90) triggers accurate matches
- [ ] All processing is local-first (no cloud dependencies)
- [ ] VRM avatar responds to recognized signs

---

## 🔧 Quick Commands

```bash
# ⚠️ FIRST: Ensure you're using Python 3.12 or lower
# See SETUP_GUIDE.md for Python 3.13+ users

# Setup environment
./setup_simple.sh

# Activate environment
source venv/bin/activate

# Run signature extraction
python3 extract_signatures.py

# Verify signature quality (with animation)
python3 verify_signatures.py assets/signatures/HELLO.json --animate

# Verify and save quality report
python3 verify_signatures.py assets/signatures/HELLO.json --report quality_report.txt

# Preview first 60 frames as animation
python3 verify_signatures.py assets/signatures/HELLO.json --animate --preview-frames 60

# Save animation as GIF
python3 verify_signatures.py assets/signatures/HELLO.json --animate --save-gif

# Deactivate environment
deactivate
```

---

## 📝 Notes

- All landmarks stored as (x, y, z) coordinates (normalized: 0-1 range)
- Zero-filling ensures consistent array shapes for ML pipeline
- Frame-by-frame processing enables temporal tracking
- Socket.io bridges Python backend and React frontend for real-time communication
