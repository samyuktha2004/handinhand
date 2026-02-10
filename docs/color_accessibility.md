Color Accessibility Compliance Check (WCAG 2.1 + Colorblind Safe)

For long-running debug/visualization tools, checks:
1. Luminance contrast ratios (WCAG AA compliance: ≥4.5:1 for text, ≥3:1 for graphics)
2. Colorblind accessibility (Deuteranopia, Protanopia, Tritanopia, Achromatopsia)
3. Eye strain potential (saturation, brightness ranges)
4. Visibility on typical video backgrounds (often dark/varied)

================================================================================
COLOR DESIGN ASSESSMENT: HandInHand Skeleton Visualizer v1
================================================================================

## Research: How Other Models Use Colors

### pose-format (sign-language-processing/pose) - MIT License
- Uses per-limb colors stored in PoseHeaderComponent 
- hand_colors computed dynamically with formula: 
  `[math.floor(x + 35 * (i % 4)) for x in HAND_POINTS_COLOR[i // 4]]`
- Base colors: [[192, 0, 0], [0, 0, 192], [0, 192, 0], [0, 192, 192], [192, 127, 0], [127, 127, 127]]
- Overrides pinky "for accessibility" (orange variants: 255,128,0 / 255,153,51 / 255,178,102)
- Body/pose: single color (255, 0, 0) red
- Face: single color (128, 0, 0) dark red
- INSIGHT: They use SINGLE color per component, not per-finger. Simpler, less visual noise.

### Sign-MT Approach (from our earlier analysis)
- Eyes rendered as shapes with lids (not dots)
- Each finger different color (cyan, green, blue, orange, red)
- Left/right hand color distinction
- Anti-aliased smooth lines
- Clean, minimal aesthetic
- INSIGHT: They DO use color-coded fingers, similar to our approach

================================================================================
## COLORBLIND TOGGLE ASSESSMENT
================================================================================

### PROS of Colorblind Toggle:
1. ✅ Users can self-select based on their vision type
2. ✅ Reduces development burden of finding "universal" palette
3. ✅ Can optimize each palette for specific vision type
4. ✅ Industry standard for accessibility (games, design tools)
5. ✅ Future-proof: can add more palettes without breaking existing

### CONS of Colorblind Toggle:
1. ❌ Extra UI complexity (settings menu required)
2. ❌ Users may not know which type they need
3. ❌ Must maintain/test multiple palettes
4. ❌ Toggle state must persist across sessions

### MITIGATION STRATEGIES:
1. **Start with Wong Palette (universal colorblind-safe)**
   - Wong 2011 palette is optimized for ALL colorblind types
   - Eliminates need for toggle in v1
   - Can add toggle later as enhancement
   
2. **Auto-detect option (future)**
   - Browser APIs can sometimes detect color preferences
   - OS-level colorblind filters exist (macOS, Windows)
   
3. **Shape + Color redundancy**
   - Use both color AND shape/size to encode information
   - Even if colors are indistinguishable, shape differs
   
4. **Luminance variation**
   - Ensure different luminance values even if hues merge
   - Colorblind users can still see dark vs light

================================================================================
## WONG PALETTE ASSESSMENT (Nature Methods 2011)
================================================================================

Wong's 8-color palette optimized for all colorblindness types:
- Orange:      #E69F00 → RGB(230, 159, 0)   → BGR(0, 159, 230)
- Sky Blue:    #56B4E9 → RGB(86, 180, 233)  → BGR(233, 180, 86)
- Bluish Green:#009E73 → RGB(0, 158, 115)   → BGR(115, 158, 0)
- Yellow:      #F0E442 → RGB(240, 228, 66)  → BGR(66, 228, 240)
- Blue:        #0072B2 → RGB(0, 114, 178)   → BGR(178, 114, 0)
- Vermillion:  #D55E00 → RGB(213, 94, 0)    → BGR(0, 94, 213)
- Reddish Purple: #CC79A7 → RGB(204, 121, 167) → BGR(167, 121, 204)
- Black:       #000000 (for text/outlines)

### Proposed Wong-Based Finger Colors (user suggestion):
- Thumb:  Orange (#E69F00)      - Highly visible, warm
- Index:  Sky Blue (#56B4E9)    - Cool, distinct from orange
- Middle: Bluish Green (#009E73)- Distinct from blue, not pure green
- Ring:   Yellow (#F0E442)      - Brightest, high luminance
- Pinky:  Blue (#0072B2)        - Darker blue, distinct from sky blue

### Assessment of Wong for Fingers:
✅ PROS:
- Scientifically validated for all colorblindness types
- Good luminance spread (yellow=high, blue=low)
- No pure red (problematic for Protanopia)
- No pure green (problematic for Deuteranopia)
- Natural "temperature" gradient (warm→cool from thumb→pinky)

⚠️ CONCERNS:
- Yellow (#F0E442) on white/light backgrounds = poor contrast
- Bluish Green may be confused with Blue in some contexts
- Missing: red/vermillion for alerts/errors

### Recommended Adjustments for Skeleton Visualization:
1. Avoid Yellow for ring finger if backgrounds can be light
   - Alternative: Use Vermillion (#D55E00) for ring
2. Consider using Reddish Purple (#CC79A7) as accent color
3. For dark backgrounds (typical in video): Yellow is fine

================================================================================
## NON-NMS PARTS: SINGLE COLOR RECOMMENDATION
================================================================================

### What are Non-NMS Parts?
- Torso, hips, legs, shoulders, neck
- NOT directly relevant to sign recognition
- Provide context/grounding but not semantic info

### Recommendation: YES, use single muted color for non-NMS
PROS:
1. ✅ Reduces visual clutter
2. ✅ Draws attention to hands/face (NMS-critical)
3. ✅ Simpler for users to understand
4. ✅ Follows pose-format convention (single color per component)
5. ✅ Reduces eye strain (fewer competing colors)

CONS:
1. ❌ Harder to debug specific limb issues
2. ❌ Less informative for developers

### Proposed Color Scheme:
- Body (torso, hips, legs, shoulders): Muted gray-blue (#4A6B8A = BGR(138, 107, 74))
- Neck: Same as body OR slightly different shade
- Joints (non-hand): Same muted color, smaller radius

### Why Gray-Blue?
- High contrast on both dark and light backgrounds
- Doesn't compete with Wong finger colors
- "Background" feel - recedes visually
- Low saturation = low eye strain

================================================================================
## RECOMMENDED v1 COLOR PALETTE
================================================================================

### Finger Colors (Wong-Based, BGR):
FINGER_COLORS_V1 = {
    'thumb':  (0, 159, 230),    # Wong Orange - warm, prominent
    'index':  (233, 180, 86),   # Wong Sky Blue - cool, distinct
    'middle': (115, 158, 0),    # Wong Bluish Green - nature-like
    'ring':   (0, 94, 213),     # Wong Vermillion - distinct from orange
    'pinky':  (178, 114, 0),    # Wong Blue - dark, endpoint
}

### Body Colors (Muted, BGR):
COLOR_BODY = (138, 107, 74)     # Muted gray-blue for all non-NMS
COLOR_NECK = (138, 107, 74)     # Same as body (visual continuity)
COLOR_JOINT = (255, 255, 255)   # White for visibility
COLOR_JOINT_BORDER = (50, 50, 50)  # Dark gray border

### Left vs Right Hand Distinction:
- Option A: Same finger colors, different line thickness (L=2, R=3)
- Option B: Same finger colors, add "L"/"R" label near wrist
- Option C: Slightly desaturate left hand colors (recedes visually)

RECOMMENDATION: Option A (thickness) - simplest, no color conflicts

================================================================================
## EYE STRAIN OPTIMIZATION
================================================================================

### Key Principles:
1. No 100% saturation + 100% brightness combinations
2. Maximum brightness ≤ 240 (not 255)
3. Minimum brightness ≥ 40 (not 0 on colored)
4. Avoid flashing/rapid color changes
5. Use anti-aliased lines (cv2.LINE_AA)

### Wong Palette Eye Strain Check:
- Orange (230,159,0): Brightness=230 ✅ OK (not 255)
- Sky Blue (86,180,233): Brightness=233 ✅ OK
- Bluish Green (0,158,115): Brightness=158 ✅ OK
- Yellow (240,228,66): Brightness=240 ⚠️ Borderline
- Blue (0,114,178): Brightness=178 ✅ OK
- Vermillion (213,94,0): Brightness=213 ✅ OK

### Recommendation:
- Reduce Yellow brightness by 10-15% if used on light backgrounds
- Current dark-background use case: Wong palette is acceptable

================================================================================
## IMPLEMENTATION PLAN
================================================================================

### Phase 1 (v1): 
- Implement Wong-based finger colors
- Single muted body color
- No colorblind toggle (Wong is universal)
- Test on 5+ sample videos

### Phase 2 (Future):
- Add colorblind toggle in settings
- Presets: "Standard", "High Contrast", "Grayscale"
- Persist preference in config file

### Phase 3 (Future):
- Shape-based finger identification (not just color)
- User-customizable color palette
- Dark/light mode auto-detection
