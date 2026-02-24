# Reference Body Integration Specification

**Created:** February 3, 2026  
**Status:** Implementation In Progress

---

## Overview

The reference body provides a **canonical coordinate system** for all skeleton visualizations. It ensures consistent proportions, handles missing data gracefully, and remains zoom-invariant.

---

## Core Principles

### 1. Reference Body is the DEFAULT Canvas

- Every frame starts with the reference body drawn as background
- MediaPipe landmarks are **overlaid** onto this canvas
- The reference body provides visual continuity when landmarks are missing

### 2. Proportions are CONSTANT

- Shoulder width: **100px** (normalization anchor)
- Upper arm: **55px** (55% of arm length)
- Forearm: **45px** (45% of arm length)
- Head: **50×70px** oval
- Neck: **35px** vertical connector

### 3. Every Point has ONE Connector

- No orphan points (points without a parent)
- No duplicate connections
- Invalid connections are flagged, not silently dropped

### 4. Missing Parts Stay Attached

- If a part is missing, it attaches to nearest available parent
- Example: Hand missing → placeholder at wrist position
- Example: Wrist missing → use last known position or reference default

### 5. Zoom-Invariant Scaling

- All landmarks normalized to reference shoulder width (100px)
- Video zoom level doesn't break proportions
- Scale factor = `100 / detected_shoulder_width`

---

## Reference Body Dimensions

```
                    ┌─────────────┐
                    │   HEAD      │  50×70px oval
                    │  (face)     │
                    └──────┬──────┘
                           │         35px neck
                    ┌──────┴──────┐
        SHOULDER ───┤             ├─── SHOULDER
        (left)      │   TORSO     │    (right)
           │        │             │       │
           │        └──────┬──────┘       │
        55px               │           55px
        (upper arm)        │        (upper arm)
           │               │              │
        ELBOW              │           ELBOW
           │               │              │
        45px               │           45px
        (forearm)          │        (forearm)
           │               │              │
        WRIST              │           WRIST
           │               │              │
        HAND               │           HAND
       (21 pts)            │         (21 pts)
                           │
                      ─────┴─────
                        100px
                    (shoulder width)
```

---

## Landmark Mapping

### Pose Landmarks (6-point signatures)

| Index | Body Part      | Parent Connector | Notes                         |
| ----- | -------------- | ---------------- | ----------------------------- |
| 0     | Left Shoulder  | Neck (implicit)  | Anchor point                  |
| 1     | Right Shoulder | Neck (implicit)  | Anchor point                  |
| 2     | Left Elbow     | Left Shoulder    | Must be within arm length     |
| 3     | Right Elbow    | Right Shoulder   | Must be within arm length     |
| 4     | Left Wrist     | Left Elbow       | Must be within forearm length |
| 5     | Right Wrist    | Right Elbow      | Must be within forearm length |

### Hand Landmarks (21-point per hand)

| Index | Finger | Joint           | Parent Connector    |
| ----- | ------ | --------------- | ------------------- |
| 0     | -      | Wrist           | Pose wrist (4 or 5) |
| 1-4   | Thumb  | CMC→MCP→IP→TIP  | Sequential chain    |
| 5-8   | Index  | MCP→PIP→DIP→TIP | Sequential chain    |
| 9-12  | Middle | MCP→PIP→DIP→TIP | Sequential chain    |
| 13-16 | Ring   | MCP→PIP→DIP→TIP | Sequential chain    |
| 17-20 | Pinky  | MCP→PIP→DIP→TIP | Sequential chain    |

### Face Landmarks (4-point minimal)

| Index | Feature       | Parent      | Notes               |
| ----- | ------------- | ----------- | ------------------- |
| 0     | Left Eyebrow  | Head center | Grammatical markers |
| 1     | Right Eyebrow | Head center | Grammatical markers |
| 2     | Left Eye      | Head center | Optional            |
| 3     | Right Eye     | Head center | Optional            |

---

## Validation Rules

### Rule 1: Connector Validation

```python
# Every non-root point must have exactly one parent
def validate_connectors(landmarks):
    errors = []
    for point_idx, parent_idx in CONNECTIONS:
        if parent_idx is None:
            continue  # Root points (shoulders) have no parent
        if landmarks[parent_idx] is None:
            errors.append(f"Point {point_idx} missing parent {parent_idx}")
    return errors
```

### Rule 2: Proportion Validation

```python
# Segment lengths must be within tolerance of reference
TOLERANCE = 0.3  # 30% deviation allowed

def validate_proportions(landmarks, reference):
    errors = []
    for segment, expected_length in SEGMENT_LENGTHS.items():
        actual = distance(landmarks[segment.start], landmarks[segment.end])
        if abs(actual - expected_length) / expected_length > TOLERANCE:
            errors.append(f"{segment} out of proportion: {actual} vs {expected_length}")
    return errors
```

### Rule 3: Bounds Validation

```python
# All points must be within frame bounds (with margin)
MARGIN = 10  # pixels

def validate_bounds(landmarks, frame_width, frame_height):
    errors = []
    for idx, point in enumerate(landmarks):
        if point[0] < MARGIN or point[0] > frame_width - MARGIN:
            errors.append(f"Point {idx} X out of bounds: {point[0]}")
        if point[1] < MARGIN or point[1] > frame_height - MARGIN:
            errors.append(f"Point {idx} Y out of bounds: {point[1]}")
    return errors
```

---

## Missing Data Handling

### Strategy: Neutral Rest Position

**CRITICAL DESIGN DECISION:** When hand data is missing, we do NOT use the previous frame's hand shape. This would carry forward a sign and corrupt meaning.

Instead, we use a **linguistically neutral rest position** - hands relaxed at sides, fingers loosely curved downward. This is an **unmarked** position that means nothing in sign language.

| Missing Part         | Fallback Behavior                                      |
| -------------------- | ------------------------------------------------------ |
| Hand (all 21 points) | Generate neutral rest hand at wrist position           |
| Wrist                | Use reference default position                         |
| Elbow                | Interpolate from shoulder + wrist (or reference)       |
| Shoulder             | Use reference body position (critical anchor)          |
| Face                 | Draw reference face at dynamic position from landmarks |

### Neutral Rest Hand Design

The neutral rest hand is explicitly **not** any handshape:

- NOT a flat hand (B handshape)
- NOT a fist (S handshape)
- NOT any letter or numeral

It has:

- Fingers loosely curved (relaxed, not extended or fisted)
- Thumb slightly tucked
- Hand pointing generally downward
- Natural slight spread between fingers

```python
def generate_neutral_hand(wrist_pos, is_left):
    """
    NEUTRAL REST position - linguistically unmarked.
    Fingers loosely curved, thumb tucked, pointing down.
    """
    # Fingers have natural curl (not straight, not fisted)
    # Each finger slightly more curled toward pinky
    for finger in [index, middle, ring, pinky]:
        curl = 0.15 * finger_index  # Increasing curl
        # Apply curl to PIP, DIP, TIP joints
```

### Implementation Priority

```python
def get_fallback_position(part, landmarks, reference):
    # For hands: ALWAYS use neutral rest position
    # Do NOT use previous frame's hand shape - it carries a sign
    if part in ['left_hand', 'right_hand']:
        return generate_neutral_hand(wrist_pos, is_left)

    # For pose: can use previous frame
    if last_frame_landmarks and last_frame_landmarks[part] is not None:
        return last_frame_landmarks[part]

    # Use reference body default
    return reference[part]
```

---

## Dynamic Head/Neck Connection

### Design Philosophy

The head and neck are drawn **dynamically** based on actual face landmarks, not as a static grey overlay. This follows Sign-MT's approach of keeping visual elements connected to actual tracking data.

### Fallback Chain for Head Position

When face landmarks are available, we use them. When missing, we fall back:

1. **nose_tip** (index 1) - most reliable face landmark
2. **glabella** (index 168) - between eyebrows
3. **upper_lip** (index 0) - if nose not detected
4. **chin** (index 152) - last resort
5. **Static offset** from shoulder center

### Visual Indicators

| State            | Head/Neck Color       |
| ---------------- | --------------------- |
| Face tracked     | Green (100, 180, 100) |
| Face not tracked | Grey (reference)      |

---

## Normalization Algorithm

### Step 1: Detect Shoulder Width

```python
left_shoulder = pose_landmarks[0]
right_shoulder = pose_landmarks[1]
detected_width = distance(left_shoulder, right_shoulder)
```

### Step 2: Calculate Scale Factor

```python
REFERENCE_SHOULDER_WIDTH = 100  # pixels
scale_factor = REFERENCE_SHOULDER_WIDTH / detected_width
```

### Step 3: Find Shoulder Center

```python
shoulder_center = (left_shoulder + right_shoulder) / 2
```

### Step 4: Normalize All Points

```python
for point in all_landmarks:
    # Translate to shoulder-center origin
    point = point - shoulder_center
    # Scale to reference proportions
    point = point * scale_factor
    # Translate to frame center
    point = point + frame_center
```

---

## Drawing Order (Z-Index)

1. **Background**: Black/dark frame
2. **Reference Body Outline**: Faint grey (head, neck, torso outline)
3. **Pose Skeleton**: Green lines (shoulders, arms)
4. **Hands**: Blue (left) / Red (right) with finger details
5. **Face Features**: On head position (eyebrows, eyes)
6. **Debug Overlays**: Optional (joint numbers, validation errors)

---

## Implementation Phases

### Phase 1: Reference Body Canvas ✅

- Draw head oval, neck line, shoulder line, torso outline
- NO default hands (to avoid 4-hands bug)
- This is the background layer

### Phase 2: Landmark Overlay

- Normalize MediaPipe landmarks to reference scale
- Draw pose skeleton on top of reference body
- Draw hands attached to wrist positions

### Phase 3: Missing Data Handling

- Implement fallback logic for missing parts
- Use last-known-position interpolation
- Show reference defaults for completely missing data

### Phase 4: Validation & Flagging

- Implement connector validation
- Implement proportion validation
- Implement bounds checking
- Visual indicators for invalid points (different color/shape)

### Phase 5: Polish

- Smooth transitions between frames
- Color accessibility (Wong palette for fingers)
- Performance optimization

---

## Error Indicators

| Error Type                    | Visual Indicator            |
| ----------------------------- | --------------------------- |
| Orphan point (no connector)   | Orange circle with X        |
| Out of bounds                 | Red circle, clamped to edge |
| Proportion violation          | Yellow dashed line          |
| Missing data (using fallback) | Grey/faded color            |

---

## Constants Reference

```python
# Frame
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CENTER_X = 320
CENTER_Y = 240

# Reference Body
SHOULDER_WIDTH = 100
UPPER_ARM = 55
LOWER_ARM = 45
HEAD_WIDTH = 50
HEAD_HEIGHT = 70
NECK_LENGTH = 35
TORSO_LENGTH = 60

# Colors (BGR)
BODY_COLOR = (0, 255, 0)       # Green
LEFT_HAND_COLOR = (255, 0, 0)  # Blue
RIGHT_HAND_COLOR = (0, 0, 255) # Red
REFERENCE_COLOR = (60, 60, 60) # Dark grey (background)
ERROR_COLOR = (0, 165, 255)    # Orange

# Validation
PROPORTION_TOLERANCE = 0.3    # 30% deviation allowed
BOUNDS_MARGIN = 10            # pixels from edge
```

---

## Testing Checklist

- [ ] Reference body displays as background (head, neck, torso)
- [ ] MediaPipe landmarks overlay correctly
- [ ] Zoom in/out doesn't break proportions
- [ ] Missing hand shows placeholder at wrist
- [ ] Missing wrist uses last known position
- [ ] Out-of-bounds points are clamped and flagged
- [ ] No "4 hands" bug (only signature hands, no default hands)
- [ ] Frame-to-frame transitions are smooth

---

## Appendix A: Color Accessibility Specification

**Standard:** WCAG 2.1 + colorblind-safe (Deuteranopia, Protanopia, Tritanopia, Achromatopsia)
**Palette:** Wong 2011 (Nature Methods) — validated for all colorblindness types. No per-user toggle required for v1.

### Finger Colors (BGR)

| Finger | Color Name      | BGR            | Notes                      |
|--------|-----------------|----------------|----------------------------|
| Thumb  | Wong Orange     | (0, 159, 230)  | Warm, prominent            |
| Index  | Wong Sky Blue   | (233, 180, 86) | Cool, distinct from orange |
| Middle | Wong Blue-Green | (115, 158, 0)  | Distinct, nature-like      |
| Ring   | Wong Vermillion | (0, 94, 213)   | Distinct from orange       |
| Pinky  | Wong Blue       | (178, 114, 0)  | Dark, clear endpoint       |

### Body Colors (BGR)

| Part         | Color                  | Rationale                               |
|--------------|------------------------|-----------------------------------------|
| Body/pose    | Gray-blue (138, 107, 74) | Low saturation, recedes behind hands  |
| Neck         | Same as body           | Visual continuity                       |
| Joint dots   | White (255, 255, 255)  | Maximum visibility                      |
| Joint border | Dark gray (50, 50, 50) | Separation from background              |

### Design Decisions

1. **Wong palette is universal** — no colorblind toggle needed for v1.
2. **Left vs right hand**: Same finger colors, different line thickness (Left=2px, Right=3px).
3. **Body muted, hands prominent** — reduces visual clutter, draws attention to NMS-critical regions.
4. **Anti-aliased lines** — use `cv2.LINE_AA` to reduce eye strain in long debug sessions.
5. **Avoid Yellow (#F0E442) on light backgrounds** — use Vermillion for ring finger if background is uncertain.

### Future

- Colorblind toggle presets ("Standard", "High Contrast", "Grayscale") — Phase 5+
- Shape-based finger identification (redundant encoding, not just color) — Phase 5+
