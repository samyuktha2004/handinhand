# MVP Dashboard: Interactive Webcam UI

**File**: `recognition_engine_ui.py` (600+ lines)  
**Status**: ✅ Ready for testing  
**Date**: 23 January 2026

---

## 🎯 Why This Is MVP Success

Without the 3D avatar, seeing **"✅ VERIFIED: GREETING (0.92)"** pop up on your webcam feed proves:

1. ✅ **Body-centric normalization** is mathematically sound (position-independent)
2. ✅ **Cosine similarity** works in real-time (embedding comparison accurate)
3. ✅ **Tier 4 validation** prevents false positives (cross-concept gate active)
4. ✅ **The foundation is production-ready** (ready for avatar layer later)

---

## 🎬 Dashboard Features

### 1️⃣ **Confidence Bars** (Left side)

```
CONFIDENCE SCORES
GREETING    [=================] 0.75
YOU         [===]              0.15
GO          [========]         0.41
WHERE       [==]               0.12
```

**Color Coding**:

- 🟢 **Green** (≥ 0.80): High confidence → ready to trigger
- 🟠 **Orange** (0.50-0.80): Medium confidence → Tier 4 validation active
- 🔴 **Red** (< 0.50): Low confidence → won't trigger

**Why Bars?**:

- User sees real-time feedback as they sign
- Bars rise/fall with hand movement (proves algorithm tracking)
- Shows all 4 concepts simultaneously (easy comparison)

### 2️⃣ **Window Progress** (Top-right)

```
Window: 75%
```

Fills 0-100% as 30 frames accumulate. When 100%, embedding ready.

### 3️⃣ **Cooldown Timer** (Top-right, if cooldown active)

```
Cooldown: 1.8s
```

Prevents double-counting. Shows remaining time after a match.

### 4️⃣ **Status Badge** (Bottom-left, large)

```
✅ VERIFIED: GREETING (0.923)
```

Shows:

- Status: ✅ VERIFIED / ❌ LOW CONFIDENCE / ⚠️ AMBIGUOUS
- Concept name
- Exact cosine similarity score

### 5️⃣ **Ghost Skeleton Overlay** (Optional, `--debug` flag)

```
Live skeleton (bright green)
↓
Golden signature (faint grey)
↓ (You can see alignment!)
```

Visual debugging: Are your hand positions aligning with the stored signature?

---

## ⚙️ Architecture Optimizations

### Design Decision 1: Cooldown Strategy

**What**: After match, wait 2 seconds before next match can trigger Socket.io

**Why**:

- User signs once, system might see 3-4 frames where confidence > 0.80
- Without cooldown: Socket.io fires 3-4 times (avatar animates 3-4x)
- With cooldown: Only fires once per gesture

**How**:

```python
now_ms = time.time() * 1000
if now_ms - self.last_match_time > self.cooldown_ms:
    emit_socket(concept)  # Fire!
    self.last_match_time = now_ms  # Reset timer
```

**Recognition keeps running** (bars still update), only Socket.io waits.

### Design Decision 2: Socket.io Optional

**What**: `--socket-url` flag, disabled by default

**Why**:

- Test recognition without server running
- Easy to toggle for development
- No dependency errors if python-socketio not installed

**How**:

```bash
# Test locally (no Socket.io)
python3 recognition_engine_ui.py

# With Avatar server (eventual)
python3 recognition_engine_ui.py --socket-url http://localhost:5000
```

### Design Decision 3: Ghost Skeleton Cached

**What**: Load golden signatures once at startup

**Why**:

- Don't reload from disk every frame (expensive)
- Overlay stays responsive

**How**:

```python
def _load_golden_signatures():
    # Called once in __init__
    for concept_id in concepts:
        pose = load_json(asl_file)[0]  # First frame
        self.golden_signatures[concept_id] = pose
```

### Design Decision 4: Dashboard Over Console

**What**: All info on OpenCV window, NOT console

**Why**:

- **Interactive**: User sees feedback in real-time as they sign
- **Proves it works**: Bars rising/falling = algorithm tracking
- **No terminal needed**: Just show the window
- **Future-proof**: Avatar will replace window, same Socket.io emission works

### Design Decision 5: Separation of Concerns

**What**: Original `recognition_engine.py` unchanged, new `recognition_engine_ui.py` adds UI layer

**Why**:

- Recognition logic is pure (testable, verifiable)
- UI layer is orthogonal (can be swapped)
- Easy to add avatar later (just replace UI layer)

---

## 🚀 Usage Comparison

### Original (Recognition Only)

```bash
python3 recognition_engine.py --debug
```

Output: Console text + optional skeleton drawing

### MVP (With Dashboard)

```bash
python3 recognition_engine_ui.py
```

Output: Interactive bars + status badge + cooldown timer

### MVP (With Debug + Ghost Skeleton)

```bash
python3 recognition_engine_ui.py --debug
```

Output: All above + faint golden skeleton overlay

### MVP (With Avatar Socket.io Backend)

```bash
python3 recognition_engine_ui.py --socket-url http://avatar-server:5000
```

Output: Dashboard + Socket.io emissions to avatar

### Custom Configuration

```bash
# Longer cooldown (3 seconds)
python3 recognition_engine_ui.py --cooldown 3000

# Alternate camera
python3 recognition_engine_ui.py --camera 1

# Demo mode (5s per frame)
python3 recognition_engine_ui.py --delay 5000
```

---

## 📊 Dashboard Layout (On-Screen)

```
┌────────────────────────────────────────────────────────────────┐
│ CONFIDENCE SCORES                           Window: 100%       │
│ GREETING    [============================] 0.92                 │
│ YOU         [========]                    0.41                 │
│ GO          [=====]                       0.23                 │
│ WHERE       [==]                          0.08                 │
│                                           Cooldown: 1.5s       │
│                                                                │
│                                                                │
│        Live Video Feed                                         │
│        (Green skeleton overlay)                                │
│        (Grey golden signature - optional)                      │
│                                                                │
│                                                                │
│        ✅ VERIFIED: GREETING (0.923)                           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔌 Socket.io Integration

### Server Message Format

```python
# Python emits:
{
    "concept": "GREETING",      # Concept ID
    "score": 0.923,             # Exact cosine similarity
    "timestamp": 1674415200.123 # Unix timestamp
}
```

### React Avatar Listener (Example)

```javascript
// Future avatar will listen:
socket.on("sign_recognized", (data) => {
  console.log(`Recognized: ${data.concept} (${data.score})`);
  playAnimation(data.concept); // Play BSL animation
});
```

### Future Integration

```bash
# Terminal 1: Avatar server
python3 avatar_server.py  # Listens on http://localhost:5000

# Terminal 2: Recognition engine
python3 recognition_engine_ui.py --socket-url http://localhost:5000

# Result: Sign → Recognition → Bar feedback → Avatar animates
```

---

## ⏱️ Cooldown Behavior

### Scenario 1: User Signs Once

```
Frame 1: GREETING 0.78 (< 0.80, no trigger)
Frame 2: GREETING 0.85 (> 0.80, Tier 4 passes, cooldown=0, EMIT!) 🎯
         ^ Last match time = now
Frame 3: GREETING 0.82 (> 0.80, but cooldown_remaining=1995ms, NO emit)
Frame 4: GREETING 0.79 (< 0.80, no trigger)
Frame 5: YOU 0.92     (cooldown_remaining=1985ms, NO emit)
...
Frame 200 (2s later): YOU 0.90 (cooldown=0, EMIT!) 🎯
```

### Cooldown Reset Points

- ✅ When a verified match emits (Socket.io fires)
- ✅ When user clears the window (press 'r')
- ❌ When a low_confidence or ambiguous signal comes in

---

## 🛠️ Configuration Parameters

| Parameter              | Default   | Purpose               | Tunable             |
| ---------------------- | --------- | --------------------- | ------------------- |
| `COSINE_SIM_THRESHOLD` | 0.80      | Min score to consider | In code             |
| `TIER_4_GAP_THRESHOLD` | 0.15      | Min gap to verify     | In code             |
| `WINDOW_SIZE`          | 30 frames | Frames per embedding  | In code             |
| `cooldown_ms`          | 2000      | Cooldown after match  | `--cooldown` flag   |
| `socket_url`           | None      | Socket.io server      | `--socket-url` flag |
| `debug`                | False     | Ghost skeleton        | `--debug` flag      |
| `camera`               | 0         | Camera device         | `--camera` flag     |
| `delay`                | 1 ms      | Frame delay           | `--delay` flag      |

---

## 🎮 Keyboard Controls

| Key     | Action                                      |
| ------- | ------------------------------------------- |
| **ESC** | Quit application                            |
| **q**   | Quit application                            |
| **r**   | Reset landmark window (restart recognition) |

---

## 🧪 Test Protocol

### Test 1: Visual Feedback

1. Run: `python3 recognition_engine_ui.py --debug`
2. Sign HELLO (GREETING)
3. Observe:
   - GREETING bar rises to ~0.80+
   - Other bars stay low
   - Status shows "✅ VERIFIED: GREETING"
   - (Optional) Ghost skeleton shows golden HELLO overlaid

### Test 2: Cooldown Works

1. Run: `python3 recognition_engine_ui.py`
2. Sign HELLO → Status shows verified
3. Immediately sign HELLO again
4. Timer shows "Cooldown: 1.8s" (prevents immediate re-trigger)
5. Wait 2s
6. Sign HELLO → Triggers again ✅

### Test 3: Socket.io Integration

1. Terminal 1: Run a simple Socket.io server
   ```bash
   python3 -m http.server 5000
   ```
2. Terminal 2: Run with Socket.io
   ```bash
   python3 recognition_engine_ui.py --socket-url http://localhost:5000
   ```
3. Check server logs: `{"concept": "GREETING", "score": 0.92}` received ✅

### Test 4: All 4 Concepts

- Sign GREETING (YOU) → YOU bar rises
- Sign YOU (PRONOUN) → PRONOUN bar rises
- Sign GO (MOTION) → MOTION bar rises
- Sign WHERE (LOCATION) → LOCATION bar rises
- Verify accuracy > 95% ✅

---

## 📈 Performance Targets

| Metric       | Target  | Notes                  |
| ------------ | ------- | ---------------------- |
| **FPS**      | 30      | Smooth real-time       |
| **Latency**  | < 200ms | Embedding + scoring    |
| **Accuracy** | > 95%   | On 4 known concepts    |
| **Cooldown** | 2s      | User-configurable      |
| **Memory**   | ~200MB  | MediaPipe + embeddings |

---

## 🔧 Troubleshooting

### Bars Not Updating

- Check camera is working: `python3 recognition_engine_ui.py --camera 0`
- Try alternate camera: `--camera 1`
- Check lighting (MediaPipe needs good lighting)

### Socket.io Connection Fails

- Make sure python-socketio is installed:
  ```bash
  pip install python-socketio
  ```
- Check server URL is correct
- Check server is running on that port

### Ghost Skeleton Not Showing

- Ensure `--debug` flag is used
- Golden signatures must be in translation_map.json
- Check `.asl_target_file` paths are correct

### Low Recognition Accuracy

1. Improve lighting (MediaPipe detection needs brightness)
2. Slower, clearer hand movements
3. Adjust thresholds in code (COSINE_SIM_THRESHOLD, TIER_4_GAP_THRESHOLD)
4. Check embeddings were generated: `ls assets/embeddings/asl/`

---

## 🚀 Scaling Path

### Phase 2 (Current - MVP with Dashboard)

✅ Confidence bars  
✅ Ghost skeleton  
✅ Cooldown timer  
✅ Socket.io ready

### Phase 3 (Avatar Integration)

- Replace OpenCV window with animated avatar
- Same Socket.io message format (no changes needed!)
- Avatar receives `{"concept": "GREETING"}` and plays animation

### Phase 4 (Cross-Lingual Mapping)

- Add Procrustes transformation matrix
- Recognition in ASL → Transformation → Output BSL animation

---

## ✨ Summary

**Why This MVP Works**:

1. **Proof of Concept**: Bars + status badge show algorithm working in real-time
2. **Visual Feedback**: User sees recognition happening (highly engaging)
3. **Production Ready**: Cooldown + Socket.io ready for avatar integration
4. **Minimal Changes**: Only added UI layer, recognition engine unchanged
5. **Scalable**: Same architecture works for 4 concepts or 100+

**Next Step**: Test on live webcam → Observe bars rising as you sign → Watch the "✅ VERIFIED" badge appear → Congrats, you've built a working sign language recognizer!

---

**File**: [recognition_engine_ui.py](../recognition_engine_ui.py)  
**Usage**: `python3 recognition_engine_ui.py`  
**Status**: ✅ Ready for MVP testing
