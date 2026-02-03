#!/usr/bin/env python3
"""Test skeleton_debugger with all signs."""

from skeleton_debugger import SkeletonDebugger
from pathlib import Path
import cv2

# Test all 4 signs
signs = [
    ('hello_0', 'hello'),
    ('go_0', 'go'),
    ('where_0', 'where'),
    ('you_0', 'you'),
]

for asl_sig, bsl_sig in signs:
    sig1 = Path(f'assets/signatures/asl/{asl_sig}.json')
    sig2 = Path(f'assets/signatures/bsl/{bsl_sig}.json')
    
    if not sig1.exists() or not sig2.exists():
        print(f'❌ Missing: {asl_sig} or {bsl_sig}')
        continue
    
    debugger = SkeletonDebugger(str(sig1), str(sig2), 'ASL', 'BSL', side_by_side=False)
    
    # Test single mode
    frame = debugger._create_single()
    
    # Test side-by-side mode
    debugger.side_by_side = True
    frame_dual = debugger._create_side_by_side()
    
    # Save test frames
    cv2.imwrite(f'assets/test_render/debugger_{asl_sig}_single.png', frame)
    cv2.imwrite(f'assets/test_render/debugger_{asl_sig}_dual.png', frame_dual)
    
    print(f'✓ {asl_sig}: single={frame.shape}, dual={frame_dual.shape}')

print('\n✅ All skeleton_debugger modes working!')
