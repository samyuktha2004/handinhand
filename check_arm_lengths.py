#!/usr/bin/env python3
"""Check arm length consistency across all positions."""
import math

SHOULDER_WIDTH = 100
ARM_LENGTH = 100
UPPER_ARM = ARM_LENGTH // 2  # 50
LOWER_ARM = ARM_LENGTH // 2  # 50
CENTER_X = 320
CENTER_Y = 240
WIDTH = 640

left_shoulder = (CENTER_X - SHOULDER_WIDTH // 2, CENTER_Y)
right_shoulder = (CENTER_X + SHOULDER_WIDTH // 2, CENTER_Y)

def dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

print('ARM LENGTH ANALYSIS')
print('=' * 50)

# UP
left_elbow_up = (CENTER_X - SHOULDER_WIDTH // 2 - 5, CENTER_Y - UPPER_ARM)
left_wrist_up = (CENTER_X - SHOULDER_WIDTH // 2 - 10, CENTER_Y - UPPER_ARM - LOWER_ARM)
up_upper = dist(left_shoulder, left_elbow_up)
up_lower = dist(left_elbow_up, left_wrist_up)
print(f'UP:    upper={up_upper:.0f}, lower={up_lower:.0f}, total={up_upper+up_lower:.0f}')

# DOWN
left_elbow_down = (CENTER_X - SHOULDER_WIDTH // 2 - 10, CENTER_Y + UPPER_ARM)
left_wrist_down = (CENTER_X - SHOULDER_WIDTH // 2 - 15, CENTER_Y + UPPER_ARM + LOWER_ARM)
down_upper = dist(left_shoulder, left_elbow_down)
down_lower = dist(left_elbow_down, left_wrist_down)
print(f'DOWN:  upper={down_upper:.0f}, lower={down_lower:.0f}, total={down_upper+down_lower:.0f}')

# LEFT
left_elbow_left = (CENTER_X - SHOULDER_WIDTH // 2 - UPPER_ARM, CENTER_Y)
left_wrist_left = (CENTER_X - SHOULDER_WIDTH // 2 - UPPER_ARM - LOWER_ARM, CENTER_Y)
left_upper = dist(left_shoulder, left_elbow_left)
left_lower = dist(left_elbow_left, left_wrist_left)
print(f'LEFT:  upper={left_upper:.0f}, lower={left_lower:.0f}, total={left_upper+left_lower:.0f}')

# RIGHT (using right arm)
right_elbow_right = (CENTER_X + SHOULDER_WIDTH // 2 + UPPER_ARM, CENTER_Y)
right_wrist_right = (CENTER_X + SHOULDER_WIDTH // 2 + UPPER_ARM + LOWER_ARM, CENTER_Y)
right_upper = dist(right_shoulder, right_elbow_right)
right_lower = dist(right_elbow_right, right_wrist_right)
print(f'RIGHT: upper={right_upper:.0f}, lower={right_lower:.0f}, total={right_upper+right_lower:.0f}')

# NEUTRAL
left_elbow_neut = (CENTER_X - SHOULDER_WIDTH // 2 - 10, CENTER_Y + UPPER_ARM)
left_wrist_neut = (CENTER_X - SHOULDER_WIDTH // 2 - 20, CENTER_Y + UPPER_ARM + LOWER_ARM - 10)
neut_upper = dist(left_shoulder, left_elbow_neut)
neut_lower = dist(left_elbow_neut, left_wrist_neut)
print(f'NEUT:  upper={neut_upper:.0f}, lower={neut_lower:.0f}, total={neut_upper+neut_lower:.0f}')

print()
totals = {'UP': up_upper+up_lower, 'DOWN': down_upper+down_lower, 
          'LEFT': left_upper+left_lower, 'RIGHT': right_upper+right_lower,
          'NEUTRAL': neut_upper+neut_lower}
print(f'Range: {min(totals.values()):.0f} to {max(totals.values()):.0f}')
diff = max(totals.values()) - min(totals.values())
print(f'Diff: {diff:.0f}px')

if diff > 20:
    print()
    print('⚠️  INCONSISTENT arm lengths!')
    for pos, total in sorted(totals.items(), key=lambda x: x[1]):
        print(f'   {pos}: {total:.0f}')
else:
    print('✅ Arms are consistent (within 20px)')

