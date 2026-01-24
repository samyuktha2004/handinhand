# Skeleton Debugger Guide

## Purpose

Verify that your signature JSON files correctly preserve the **Non-Manual Signals (NMS)** and hand shapes by visualizing them as 2D skeletons. Before you sign to the camera, make sure the extracted "DNA" actually looks like a human signing.

---

## Components

### 1. `skeleton_drawer.py` — Landmark Visualization Engine

**What it does:**

- Converts MediaPipe landmarks (x, y, z coordinates) into 2D skeleton drawings
- Uses `cv2.line()` to connect joints into a recognizable human shape
- Color-codes body parts for clarity:
  - 🟢 **Green**: Body skeleton (shoulders, arms, legs)
  - 🔵 **Blue**: Left hand (5 fingers)
  - 🔴 **Red**: Right hand (5 fingers)
  - 🟡 **Yellow**: Joint dots (optional visualization)

**Key Functions:**

```python
from skeleton_drawer import SkeletonDrawer

# Draw skeleton on frame
skeleton_img = SkeletonDrawer.draw_skeleton(
    frame=cv2_image,
    landmarks={'pose': pose_array, 'left_hand': lh_array, 'right_hand': rh_array},
    lang="ASL"
)

# Apply body-centric normalization
normalized = SkeletonDrawer.normalize_landmarks(landmarks_dict)
```

**Connections Made:**

- **Body**: Shoulders → Elbows → Wrists → Hips → Knees → Ankles
- **Left Hand**: Wrist → Thumb/Index/Middle/Ring/Pinky (5 chains)
- **Right Hand**: Same as left

---

### 2. `skeleton_debugger.py` — Dual-Signature Player

**What it does:**

- Loads two signature JSON files (e.g., ASL "hello_0" + BSL "hello_target")
- Displays them side-by-side as animated skeletons
- Lets you step through frame-by-frame
- Verifies frame synchronization and normalization

**Usage:**

```bash
# Default: ASL hello_0 vs BSL hello_target (side-by-side)
python3 skeleton_debugger.py

# Custom signatures
python3 skeleton_debugger.py --sig1 where_0 --sig2 where_target --lang1 asl --lang2 bsl

# Toggled mode (alternate between signatures)
python3 skeleton_debugger.py --mode toggled

# Different frame rate
python3 skeleton_debugger.py --fps 20
```

**Interactive Controls:**

| Key       | Action                                            |
| --------- | ------------------------------------------------- |
| **SPACE** | Play/Pause                                        |
| **←/→**   | Previous/Next frame                               |
| **n**     | Toggle **Normalization** (body-centric centering) |
| **d**     | Toggle **Joint dots** visualization               |
| **s**     | Toggle **Side-by-side** mode                      |
| **q**     | Quit                                              |

---

## Verification Checklist

Use the skeleton debugger to validate:

### ✅ **1. Hand Shape Preservation**

| What to Check                 | Why                                    | Good Sign                                                        |
| ----------------------------- | -------------------------------------- | ---------------------------------------------------------------- |
| ASL "Hello" is one-handed     | ASL uses different hand shape than BSL | Right hand is extended (fingers spread); left hand rests at side |
| BSL "Hello" may be two-handed | BSL grammar often uses symmetry        | Both hands move together, mirror positions                       |
| Fingers remain spread/curled  | Fist vs open hand matters for meaning  | Finger positions change smoothly, don't snap                     |

**Test**: Run `skeleton_debugger.py` and watch the hand skeletons. Do the fingers move like a human signing, or do they jitter/disappear?

### ✅ **2. Body-Centric Normalization**

**What it checks:** Does the skeleton stay centered regardless of the original video framing?

**How to verify:**

1. Press **'n'** to toggle normalization
2. Look at the shoulder position (should be at center when normalized)
3. Compare ASL and BSL versions — they should both be centered the same way

**Expected result**: Both skeletons have shoulders at the same pixel position regardless of where the signer was in the original video.

### ✅ **3. Frame Synchronization**

**What it checks:** Do ASL and BSL start/end at the same logical moment?

**Watch for:**

- Frame counter at top of each skeleton (e.g., "Frame 5/42" vs "Frame 5/52")
- Sync status at bottom ("✓ SYNC" or "⚠ DESYNC")

**Expected result**:

- Same number of frames (or within 1-2 frames)
- Hand movements start/end together
- Body posture is similar at frame 0 and final frame

### ✅ **4. Movement Quality (Jitter & Continuity)**

**What to watch:**

- Do joints move smoothly, or do they jump around?
- Do hands disappear/reappear mid-motion?
- Is the skeleton recognizable as a human?

**If you see jitter:**

- The video might have been low quality
- MediaPipe lost tracking for a frame
- Consider re-extracting from a different video instance

---

## Example Workflow

```bash
# 1. Run the debugger
python3 skeleton_debugger.py

# 2. Step through frames slowly (use arrow keys)
# → Watch for one-handed motion in ASL
# → Watch for correct hand position relative to body

# 3. Toggle normalization (press 'n')
# → Verify shoulders stay centered
# → Compare both signatures

# 4. Play at 15fps (default) or slower
# → Does the overall motion look natural?
# → Could you recognize the sign from the skeleton alone?

# 5. If satisfied, commit the signature to version control
# → These JSON files are the "DNA" for recognition
```

---

## Understanding Signature Structure

Your signature JSON looks like:

```json
{
  "metadata": {
    "gloss": "hello",
    "source_video": "wlasl_hello_0.mp4",
    "frame_width": 640,
    "frame_height": 480,
    "total_frames": 42
  },
  "frames": [
    {
      "pose": [[x1, y1, conf1], [x2, y2, conf2], ...],
      "left_hand": [[x1, y1, conf1], ...],
      "right_hand": [[x1, y1, conf1], ...]
    },
    ...
  ]
}
```

The skeleton debugger extracts `pose` + `left_hand` + `right_hand` and draws lines between landmarks.

---

## Troubleshooting

| Problem                         | Cause                                     | Solution                                                        |
| ------------------------------- | ----------------------------------------- | --------------------------------------------------------------- |
| **"Signature not found" error** | File path incorrect                       | Ensure signatures are in `assets/signatures/{lang}/{name}.json` |
| **Skeleton looks broken**       | Missing landmarks (MediaPipe failed)      | Re-extract from a better quality video                          |
| **Hands invisible**             | Frame out of range or landmarks are [0,0] | Check signature has valid left_hand/right_hand data             |
| **Slow playback**               | FPS too low or computer slow              | Try `--fps 10` or reduce resolution                             |

---

## Next Steps (Phase 2B)

Once body/hand skeletons look good:

1. Compare stickman against original video side-by-side (eye verification)
2. Add optional "face zoom" mode for eyebrow/mouth detail
3. Measure confidence scores (MediaPipe gives each landmark a confidence value)
4. Test on real webcam input

---

## References

- **MediaPipe Holistic**: 33 pose + 21 left hand + 21 right hand + 468 face landmarks
- **Skeleton Connections**: Defined in `skeleton_drawer.py` as `POSE_CONNECTIONS` and `HAND_CONNECTIONS`
- **Color Coding**: Green (body), Blue (left), Red (right) for fast visual parsing
