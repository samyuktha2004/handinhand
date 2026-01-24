# 🔧 Skeleton Debugger - Coordinate Scaling Fix

## Problem Identified

The skeleton debugger was only showing tiny dots instead of full skeletons because:

**Root Cause**: Signature JSON stores coordinates in **normalized 0-1 range**, but the drawer was treating them as pixel coordinates directly.

Example:

- Stored coordinate: `0.654` (normalized)
- Directly converted to int: `0` (wrong!)
- Should be scaled: `0.654 × 640 = 418` (correct pixel position)

## Solution Implemented

### 1. **Updated `extract_landmarks_from_signature()` in skeleton_drawer.py**

**Before**:

```python
landmarks['pose'] = np.array(frame['pose'], dtype=np.float32)
# Coordinates still in 0-1 range
```

**After**:

```python
def _scale_landmarks(lm_array: np.ndarray, fw: int, fh: int) -> np.ndarray:
    """Scale normalized coordinates (0-1) to pixel coordinates."""
    result = lm_array.copy()
    result[:, 0] *= fw  # x coordinate
    result[:, 1] *= fh  # y coordinate
    return result

landmarks['pose'] = _scale_landmarks(pose_arr, frame_width, frame_height)
# Now in pixel coordinates (0-640, 0-480)
```

### 2. **Updated POSE_CONNECTIONS to handle 6-landmark partial poses**

**Before**: Only full 33-landmark MediaPipe connections (which don't apply)

**After**: Added both full connections AND partial 6-landmark connections

```python
POSE_CONNECTIONS = [
    # Full MediaPipe connections (indices 11-32)
    (12, 14), (14, 16), ...
    # Partial pose connections (for 6-landmark signatures)
    (0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5),
]
```

This allows the drawer to work with both full and partial skeleton data.

## What Changed

| Aspect                | Before          | After                         |
| --------------------- | --------------- | ----------------------------- |
| **Coordinates**       | 0-1 normalized  | 0-640, 0-480 pixels           |
| **Visible landmarks** | 1 tiny dot each | Full hand + body skeletons    |
| **Pose landmarks**    | Not drawn       | 6 key points + connections    |
| **Hand landmarks**    | Invisible       | 21 per hand (clearly visible) |

## Testing Results

✅ **Coordinate scaling verified**:

- Pose X: 154-495 pixels (was 0.24-0.77)
- Pose Y: 224-404 pixels (was 0.47-0.84)
- Left hand: 275-347 X, 237-345 Y
- Right hand: 259-374 X, 186-234 Y

✅ **Skeleton rendering verified**:

- Green pixels (body): 3,109
- Blue pixels (left hand): 1,828
- Red pixels (right hand): 1,867
- Total: 6,804 colored pixels

## Files Modified

- `skeleton_drawer.py` — Updated `extract_landmarks_from_signature()` and `POSE_CONNECTIONS`

## How to Test

```bash
# Simple test
python3 test_skeleton_debugger.py

# Full interactive test
python3 skeleton_debugger.py
```

**Expected Output**:

- Two side-by-side skeletons with proper coloring
- ASL: 55 frames (one-handed hello)
- BSL: 36 frames (hello gesture)
- Green body lines, Blue/Red hand dots
- Status shows desync (19 frame difference)

## Next Steps

1. ✅ Coordinate scaling fixed
2. ✅ Skeleton visibility working
3. 🔄 Test with live playback
4. 🔄 Verify normalization toggle
5. 🔄 Check frame sync detection

---

**Status**: Skeletons now visible and properly scaled ✅
