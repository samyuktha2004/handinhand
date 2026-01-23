# MVP: Quick Start Guide

**Get the interactive dashboard running in < 2 minutes.**

---

## 🚀 30-Second Setup

```bash
cd /Users/supriyarao/visual\ studio/handinhand
source ./activate.sh
python3 recognition_engine_ui.py
```

**That's it.** A window opens with your webcam feed + confidence bars.

---

## 📊 What You'll See

```
┌─────────────────────────────────────┐
│ CONFIDENCE SCORES      Window: 45%  │
│ GREETING    [====]    0.45          │
│ YOU         [==]      0.12          │
│ GO          [===]     0.28          │
│ WHERE       [ ]       0.03          │
│                                     │
│  (Your webcam video here)           │
│                                     │
│  ⚠️ AMBIGUOUS (0.45)                 │
└─────────────────────────────────────┘
```

**As you sign**:

- Bars rise/fall in real-time ✨
- Window fills from 0 → 100%
- Status changes to ✅ VERIFIED when confident
- Cooldown timer appears for 2 seconds

---

## 🎮 Commands

### Basic

```bash
# Standard (with dashboard)
python3 recognition_engine_ui.py

# With ghost skeleton overlay (debug mode)
python3 recognition_engine_ui.py --debug

# With custom cooldown (in milliseconds)
python3 recognition_engine_ui.py --cooldown 3000

# Demo mode (5 seconds per frame)
python3 recognition_engine_ui.py --delay 5000
```

### With Socket.io (Future Avatar)

```bash
# Send "sign_recognized" events to server
python3 recognition_engine_ui.py --socket-url http://localhost:5000

# (Server receives: {"concept": "GREETING", "score": 0.92, "timestamp": ...})
```

### Keyboard

- **ESC** or **q** = Quit
- **r** = Reset window

---

## ✅ Test Sequence

### Test 1: Visual Feedback

1. Run: `python3 recognition_engine_ui.py --debug`
2. Slowly raise your hand → Watch GREETING bar rise
3. Lower hand → Watch bar drop
4. **Result**: Bars move = algorithm tracking ✅

### Test 2: Recognition

1. Run: `python3 recognition_engine_ui.py`
2. Make the HELLO sign (ASL wave)
3. Wait for window to fill (≈1 second of continuous gesture)
4. **Expected**: Status shows "✅ VERIFIED: GREETING (0.92)"
5. Repeat for YOU, GO, WHERE

### Test 3: Cooldown

1. Run: `python3 recognition_engine_ui.py`
2. Sign HELLO → Status shows "✅ VERIFIED"
3. Immediately sign HELLO again
4. Timer shows "Cooldown: 1.8s" (prevents re-trigger)
5. Wait 2 seconds → Can sign again
6. **Result**: Prevents accidental double-counting ✅

### Test 4: All 4 Concepts

| Concept      | Gesture             | Expected          | Status |
| ------------ | ------------------- | ----------------- | ------ |
| **GREETING** | Wave hand           | GREETING bar high | [ ]    |
| **YOU**      | Point gesture       | YOU bar high      | [ ]    |
| **GO**       | Moving away         | GO bar high       | [ ]    |
| **WHERE**    | Questioning gesture | WHERE bar high    | [ ]    |

**Target**: 95%+ accuracy on each

---

## 🐛 Troubleshooting

### Issue: Camera Not Opening

```bash
# Try alternate camera
python3 recognition_engine_ui.py --camera 1
```

### Issue: Bars Not Moving

- Check lighting (MediaPipe needs good brightness)
- Move hands closer to camera
- Verify camera is not blocked: `python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`

### Issue: Recognition Not Working

1. Run with debug to see ghost skeleton:
   ```bash
   python3 recognition_engine_ui.py --debug
   ```
2. Check if your gesture aligns with golden skeleton
3. Try more pronounced hand movements

### Issue: "ModuleNotFoundError: No module named 'socketio'"

- This is OK! Socket.io is optional.
- If you want it: `pip install python-socketio`
- Ignore if just testing locally

---

## 📈 Performance

| Metric       | Expected                        |
| ------------ | ------------------------------- |
| **FPS**      | 30 (smooth video)               |
| **Latency**  | < 200ms from sign to bar update |
| **Memory**   | ~200MB                          |
| **Accuracy** | > 95% on 4 concepts             |

---

## 🎯 Success Indicators

✅ **You know it's working when**:

- Bars rise/fall smoothly as you move hands
- Window fills to 100% after ~1 second of gesture
- Status changes to ✅ VERIFIED when you hold a sign
- Cooldown timer appears after each match
- No console errors

---

## 🚀 Next Steps

After confirming MVP works:

1. **Measure Accuracy** (15 min)
   - Sign each concept 20 times
   - Count correct recognitions
   - Target: > 95%

2. **Setup Avatar Server** (30 min)
   - Start local Socket.io server
   - Run: `python3 recognition_engine_ui.py --socket-url http://localhost:5000`
   - See events flowing to server

3. **Build Avatar (Phase 3)** (1-2 weeks)
   - React component that listens for `sign_recognized` events
   - Load BSL animation based on concept_id
   - Play animation on match

---

## 💡 Pro Tips

**For Best Recognition**:

- ✅ Good lighting (face the window)
- ✅ Clear, deliberate hand movements
- ✅ Wait for window to fill completely (100%)
- ✅ Hold gesture for 1-2 seconds

**For Debugging**:

- Use `--debug` to see ghost skeleton overlay
- Compare your hands to golden signature
- If misaligned, adjust gesture position

**For Demo**:

- Use `--delay 5000` for slow-motion (5s per frame)
- Easy to film/show others
- See algorithm thinking step-by-step

---

## 📊 Dashboard Reference

| Element               | Meaning                               |
| --------------------- | ------------------------------------- |
| **Green bar**         | High confidence (≥ 0.80)              |
| **Orange bar**        | Medium confidence (0.50-0.80)         |
| **Red bar**           | Low confidence (< 0.50)               |
| **Window: 75%**       | 75% of 30 frames accumulated          |
| **✅ VERIFIED**       | Recognition confirmed (Tier 4 passed) |
| **⚠️ AMBIGUOUS**      | Similar scores (need clearer gesture) |
| **❌ LOW CONFIDENCE** | Score too low                         |
| **Cooldown: 1.2s**    | Wait before next can trigger          |

---

## 🔧 Fine-Tuning

If recognition not accurate, edit `recognition_engine_ui.py` thresholds:

```python
# Line ~20-30
COSINE_SIM_THRESHOLD = 0.80      # Lower = more permissive (0.75)
TIER_4_GAP_THRESHOLD = 0.15      # Lower = less strict (0.10)
WINDOW_SIZE = 30                 # Longer = smoother (40)
```

Then rerun:

```bash
python3 recognition_engine_ui.py
```

---

## ✨ Summary

**MVP Dashboard is**:

- ✅ Simple (1 command to run)
- ✅ Visual (bars show what's happening)
- ✅ Accurate (Tier 4 validation)
- ✅ Ready (Socket.io for avatar later)
- ✅ Fast (30 FPS)

**Ready to test?**

```bash
python3 recognition_engine_ui.py --debug
```

Then sign a word and watch the bars move! 🎉

---

**File**: [recognition_engine_ui.py](../recognition_engine_ui.py)  
**Time to first run**: 30 seconds  
**Expected accuracy**: 95%+

Let's go! 🚀
