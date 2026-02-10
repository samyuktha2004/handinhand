#!/usr/bin/env python3
import json
import numpy as np
from pathlib import Path

from generate_embeddings import EmbeddingGenerator

probe = 'up'
probe_path = Path('assets/probes') / f'probe_{probe}.json'
if not probe_path.exists():
    print('Probe not found:', probe_path)
    raise SystemExit(1)

sig = json.load(open(probe_path))
frames = sig.get('pose_data', [])
if not frames:
    print('No frames found')
    raise SystemExit(1)

# Use generator methods via instance
gen = EmbeddingGenerator()

# compute embedding for original signature
# We'll call the internal _frame_to_embedding to match pipeline
frame_embs = [gen._frame_to_embedding(f) for f in frames]
avg_emb = np.mean(frame_embs, axis=0)

# Create translated signature (translate all points by +50px x and +30px y)
translated_frames = []
for f in frames:
    new_f = {k: [] for k in ['pose','left_hand','right_hand','face']}
    for k in ['pose','left_hand','right_hand','face']:
        pts = f.get(k, [])
        new_pts = []
        for pt in pts:
            # Preserve zeros (missing data). Only translate valid points.
            if abs(pt[0]) < 1e-9 and abs(pt[1]) < 1e-9:
                if len(pt) >= 3:
                    new_pts.append([0.0, 0.0, pt[2] if len(pt) > 2 else 0.0])
                else:
                    new_pts.append([0.0, 0.0])
            else:
                x = pt[0] + 50.0 / sig['metadata']['frame_width']
                y = pt[1] + 30.0 / sig['metadata']['frame_height']
                if len(pt) >= 3:
                    new_pts.append([x,y,pt[2]])
                else:
                    new_pts.append([x,y])
        new_f[k] = new_pts
    translated_frames.append(new_f)

frame_embs_t = [gen._frame_to_embedding(f) for f in translated_frames]
avg_emb_t = np.mean(frame_embs_t, axis=0)

# Compare
from numpy.linalg import norm

diff = norm(avg_emb - avg_emb_t)
print(f"Embedding L2 difference after global translation: {diff:.6f}")
print("Avg emb first 8:", avg_emb[:8])
print("Translated avg emb first 8:", avg_emb_t[:8])
print("Diff first 8:", (avg_emb - avg_emb_t)[:8])
print("Mean diff:", np.mean((avg_emb - avg_emb_t)))
diff_vec = (avg_emb - avg_emb_t)
nz = np.where(np.abs(diff_vec) > 1e-8)[0]
print(f"Non-zero diff indices count: {len(nz)}")
if len(nz) > 0:
    for i in nz[:20]:
        print(i, diff_vec[i], avg_emb[i], avg_emb_t[i])
if diff < 1e-6:
    print('PASS: Embedding invariant to global translation (body-centric).')
else:
    print('WARNING: Embedding changed after translation — check normalization pipeline')
