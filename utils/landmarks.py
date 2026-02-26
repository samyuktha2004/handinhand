"""
Landmark Configuration — Single Source of Truth
================================================

ALL landmark indices and derived counts live here.
No other file should hardcode face/pose/hand counts.

FACE ARCHITECTURE (Phase 3 update):
  Two-tier face landmark design — extract more than we embed:
  - FACE_INDICES_EXTRACT: what MediaPipe extracts and stores in signature JSON (20 pts)
  - FACE_INDICES_EMBED:   what is actually used in the 512-dim embedding (7 pts now)

  To ADD face features to the embedding in Phase 5/7:
    1. Add the index to FACE_INDICES_EMBED  (must already be in FACE_INDICES_EXTRACT)
    2. Regenerate embeddings only (no re-extraction needed)

  To ADD new face regions not yet captured:
    1. Add index to FACE_INDICES_EXTRACT
    2. Re-extract signatures (one-time)
    3. Also add to FACE_INDICES_EMBED if you want it in the embedding
"""

# ---------------------------------------------------------------------------
# MediaPipe Holistic landmark indices
# ---------------------------------------------------------------------------

# Compact pose: shoulders, elbows, wrists only (subset of MediaPipe's 33-point pose)
POSE_INDICES = [11, 12, 13, 14, 15, 16]   # L-shoulder, R-shoulder, L-elbow, R-elbow, L-wrist, R-wrist

# Hands: all 21 MediaPipe hand landmarks (same for left and right)
HAND_INDICES = list(range(21))


# ---------------------------------------------------------------------------
# Face NMS landmarks — TWO-TIER (extract vs embed)
# ---------------------------------------------------------------------------

# TIER 1: What gets EXTRACTED from MediaPipe and STORED in signature JSON
# 20 points covering all 8 Ding & Martinez (2009) Place of Articulation regions:
#   - Eyebrows (4): NMS — emphasis, wh-questions, conditionals
#   - Mouth (5): Mouthing, BSL non-manual signals, basic shape
#   - Nose (3): Place of articulation mid-face
#   - Cheeks (2): Side-location signs
#   - Jaw (2): Lower face location
#   - Temples (2): Side-location (ASL MOTHER, BSL signs)
#   - Forehead/chin extremes (2): Maximum POA range (FATHER=forehead, MOTHER=chin in ASL)
FACE_INDICES_EXTRACT = [
    # Eyebrows (4) — existing, confirmed NMS signals
    70, 107, 300, 336,
    # Mouth (5) — existing 3 + 2 new for better lip shape
    61, 291, 13, 14, 17,
    # Nose bridge + tip (3) — POA mid-face
    168, 6, 4,
    # Cheeks (2) — for side-location signs
    117, 346,
    # Jaw (2) — lower face POA
    172, 397,
    # Temples (2) — side-location signs
    54, 284,
    # Forehead center + chin center (2) — extreme vertical POA range
    10, 152,
]

# TIER 2: What gets USED in the 512-dim embedding (subset of FACE_INDICES_EXTRACT)
# Currently: the original 7 Phase-3 points (eyebrows + mouth corners + lip center)
# To expand: add indices from FACE_INDICES_EXTRACT to this list + regenerate embeddings
FACE_INDICES_EMBED = [70, 107, 300, 336, 61, 291, 13]

# Backward compatibility alias — code that imports FACE_INDICES gets the EXTRACT set
FACE_INDICES = FACE_INDICES_EXTRACT


# ---------------------------------------------------------------------------
# Derived counts — update automatically when indices change
# ---------------------------------------------------------------------------

NUM_POSE = len(POSE_INDICES)                # 6
NUM_HAND = len(HAND_INDICES)               # 21
NUM_FACE_EXTRACT = len(FACE_INDICES_EXTRACT)  # 20 — points stored in JSON
NUM_FACE_EMBED   = len(FACE_INDICES_EMBED)    # 7  — points used in embedding
NUM_FACE = NUM_FACE_EXTRACT                   # alias for downstream code (skeleton, probes)

# Positions of FACE_INDICES_EMBED within the FACE_INDICES_EXTRACT array
# Used by generate_embeddings.py to select embedding points from stored face sub-array
FACE_EMBED_OFFSETS = [FACE_INDICES_EXTRACT.index(idx) for idx in FACE_INDICES_EMBED]

# Full flat array sizes
TOTAL_LANDMARKS       = NUM_POSE + 2 * NUM_HAND + NUM_FACE_EXTRACT  # 68 — JSON/skeleton size
TOTAL_LANDMARKS_EMBED = NUM_POSE + 2 * NUM_HAND + NUM_FACE_EMBED     # 55 — embedding computation size


# ---------------------------------------------------------------------------
# Concatenated array layout: [pose | left_hand | right_hand | face]
# Slice boundaries for indexing into a flat EXTRACT landmark array (68 pts)
# ---------------------------------------------------------------------------

LEFT_HAND_START  = NUM_POSE                          # 6
RIGHT_HAND_START = NUM_POSE + NUM_HAND               # 27
FACE_START       = NUM_POSE + 2 * NUM_HAND           # 48

# Compact shoulder indices within the 6-point pose sub-array
LEFT_SHOULDER_IDX  = 0    # maps to MediaPipe index POSE_INDICES[0] = 11
RIGHT_SHOULDER_IDX = 1    # maps to MediaPipe index POSE_INDICES[1] = 12


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

# Face count before Phase 3 (eyebrows only, 4 points).
# Used as default in extract_landmarks_from_signature() when a signature's
# metadata.landmarks_per_frame.face field is absent (old format).
LEGACY_FACE_COUNT = 4
