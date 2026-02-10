#!/usr/bin/env python3
"""Run simple ablation: joint-only vs combined (joint+bone+motion).

Outputs mean ASL-BSL similarity for both embeddings.
"""
import os
import numpy as np
from pathlib import Path
from utils.registry_loader import RegistryLoader
from scipy.spatial.distance import cosine

loader = RegistryLoader()
asl_registry = loader.get_language_registry('asl')
bsl_registry = loader.get_language_registry('bsl')

joint_sims = []
combined_sims = []

for concept_id, concept_data in asl_registry.items():
    if concept_id.startswith('_'):
        continue
    if concept_id not in bsl_registry:
        continue

    asl_joint = concept_data.get('embedding_mean_file')
    if not asl_joint:
        continue

    asl_joint = Path(asl_joint).with_name(Path(asl_joint).name.replace('.npy', '_joint.npy'))
    asl_comb = Path(asl_joint).with_name(Path(asl_joint).name.replace('_joint.npy', '_combined.npy'))

    bsl_data = bsl_registry[concept_id]
    bsl_file = bsl_data.get('embedding_mean_file')
    if not bsl_file:
        continue
    bsl_joint = Path(bsl_file).with_name(Path(bsl_file).name.replace('.npy', '_joint.npy'))
    bsl_comb = Path(bsl_file).with_name(Path(bsl_file).name.replace('.npy', '_combined.npy'))

    if not asl_joint.exists() or not asl_comb.exists() or not bsl_joint.exists() or not bsl_comb.exists():
        continue

    a_j = np.load(asl_joint)
    a_c = np.load(asl_comb)
    b_j = np.load(bsl_joint)
    b_c = np.load(bsl_comb)

    # cosine similarity
    sj = 1 - cosine(a_j, b_j)
    sc = 1 - cosine(a_c, b_c)
    joint_sims.append(sj)
    combined_sims.append(sc)
    print(f"{concept_id}: joint={sj:.4f}, combined={sc:.4f}")

if joint_sims:
    print('\nMean joint similarity:', np.mean(joint_sims))
    print('Mean combined similarity:', np.mean(combined_sims))
else:
    print('No paired embeddings found for ablation. Run generate_embeddings.py first to produce _joint/_combined numpy files.')
