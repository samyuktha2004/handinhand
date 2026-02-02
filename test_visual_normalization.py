#!/usr/bin/env python3
"""Quick visual test of normalized skeleton."""
import cv2
import json
import numpy as np
from skeleton_drawer import SkeletonDrawer, extract_landmarks_from_signature

# Load signature with normalization
with open('assets/signatures/asl/hello_0.json') as f:
    sig = json.load(f)

# Extract with reference normalization (default=True now)
frames = extract_landmarks_from_signature(sig)

print(f'Loaded {len(frames)} frames')

# Draw first frame
frame = np.zeros((480, 640, 3), dtype=np.uint8)
frame[:] = (40, 40, 40)  # Dark gray

landmarks = frames[0]
SkeletonDrawer.draw_skeleton(frame, landmarks, lang="ASL", show_joints=True)

# Draw reference lines
# Center of frame
cv2.line(frame, (320, 0), (320, 480), (50, 50, 50), 1)  # Vertical center
cv2.line(frame, (0, 192), (640, 192), (50, 50, 50), 1)  # Shoulder height (480*0.4)

# Expected shoulder positions at 100px apart, centered
# Left shoulder: 320 - 50 = 270
# Right shoulder: 320 + 50 = 370
cv2.circle(frame, (270, 192), 5, (0, 100, 0), -1)  # Expected left shoulder
cv2.circle(frame, (370, 192), 5, (0, 100, 0), -1)  # Expected right shoulder

# Add text
cv2.putText(frame, "Reference Body Normalization Test", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
cv2.putText(frame, "Green dots = expected shoulder positions", (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# Show shoulder width
pose = landmarks['pose']
sw = np.linalg.norm(pose[1][:2] - pose[0][:2])
cv2.putText(frame, f"Shoulder width: {sw:.0f}px (target: 100px)", (10, 460),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

cv2.imshow("Normalized Skeleton Test", frame)
print("Press any key to close...")
cv2.waitKey(0)
cv2.destroyAllWindows()
