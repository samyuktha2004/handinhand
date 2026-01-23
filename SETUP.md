# Setup & Usage Guide

## ✅ Environment Status

- **Python**: 3.12.12 ✅
- **Virtual Environment**: ./venv/ ✅
- **All Packages**: Installed ✅

## 🚀 Quick Start

### Activate Environment

```bash
./activate.sh
```

### Extract Signatures

```bash
python3 extract_signatures.py
```

### Verify Quality

```bash
python3 verify_signatures.py assets/signatures/HELLO.json --animate
```

### Deactivate

```bash
deactivate
```

---

## 📦 Installed Packages

| Package         | Version | Purpose                  |
| --------------- | ------- | ------------------------ |
| mediapipe       | 0.10.21 | Pose/Hand/Face Detection |
| opencv-python   | 4.13.0  | Video Processing         |
| numpy           | 1.26.4  | Numerical Computing      |
| scipy           | 1.17.0  | Cosine Similarity        |
| pandas          | 3.0.0   | Data Processing          |
| matplotlib      | 3.10.8  | Visualization            |
| scikit-learn    | 1.8.0   | ML Utilities             |
| Pillow          | 12.1.0  | Image Processing         |
| python-socketio | 5.16.0  | Real-time Communication  |

---

## 📁 Key Scripts

- `extract_signatures.py` - Extract MediaPipe landmarks from videos into JSON
- `verify_signatures.py` - Visualize and analyze extracted signatures
- `activate.sh` - Quick environment activation

## 🔧 Troubleshooting

**Python 3.13 Error**: MediaPipe requires Python 3.12 or lower. Already installed.

**Import Errors**: Ensure environment is activated: `./activate.sh`

**Package Issues**: Reinstall: `pip install -r requirements.txt --upgrade`

---

## 📚 Documentation

- `progress.md` - Project tracking and roadmap
- `README.md` - Project overview
- `PRD.md` - Product requirements
- `requirements.txt` - Package dependencies
- `pyproject.toml` - Poetry configuration

---

## ⚙️ Guidelines

- **No extra documentation** unless critical for understanding
- **Keep scripts focused** on single purpose
- **Update progress.md** for major milestones only
- **Use code comments** for complex logic, not separate docs
