#!/usr/bin/env python3
"""Verify refactored file structure"""

import json
import os

print("=" * 60)
print("VERIFYING FILE STRUCTURE")
print("=" * 60)

# Check translation_map.json structure
print("\n1. Checking translation_map.json (concept-centric)...")
with open('translation_map.json') as f:
    tmap = json.load(f)

concepts = [k for k in tmap.keys() if not k.startswith('_')]
print(f"   ✓ {len(concepts)} concepts")

# Verify no language-specific data in translation_map
sample = tmap[concepts[0]]
bad_keys = [k for k in sample.keys() if 'asl_' in k or 'bsl_' in k]
if bad_keys:
    print(f"   ✗ ERROR: Found language-specific keys: {bad_keys}")
else:
    print(f"   ✓ No language-specific inline data (clean!)")

# Check required keys
required = ['concept_id', 'concept_name', 'languages', 'status']
missing = [k for k in required if k not in sample]
if missing:
    print(f"   ✗ Missing required keys: {missing}")
else:
    print(f"   ✓ All required keys present")

# Check ASL registry
print("\n2. Checking assets/registries/asl_registry.json...")
if not os.path.exists('assets/registries/asl_registry.json'):
    print(f"   ✗ File not found!")
else:
    with open('assets/registries/asl_registry.json') as f:
        asl = json.load(f)
    asl_concepts = [k for k in asl.keys() if not k.startswith('_')]
    print(f"   ✓ {len(asl_concepts)} concepts")
    
    # Verify structure
    sample_asl = asl[asl_concepts[0]]
    if 'signatures' in sample_asl and 'embedding_mean_file' in sample_asl:
        print(f"   ✓ Proper structure (signatures + embedding)")
    else:
        print(f"   ✗ Invalid structure")

# Check BSL registry
print("\n3. Checking assets/registries/bsl_registry.json...")
if not os.path.exists('assets/registries/bsl_registry.json'):
    print(f"   ✗ File not found!")
else:
    with open('assets/registries/bsl_registry.json') as f:
        bsl = json.load(f)
    bsl_concepts = [k for k in bsl.keys() if not k.startswith('_')]
    print(f"   ✓ {len(bsl_concepts)} concepts")
    
    # Verify structure
    sample_bsl = bsl[bsl_concepts[0]]
    if 'target' in sample_bsl and 'embedding_mean_file' in sample_bsl:
        print(f"   ✓ Proper structure (target + embedding)")
    else:
        print(f"   ✗ Invalid structure")

# Cross-reference check
print("\n4. Cross-referencing registries...")
tmap_ids = set(concepts)
asl_ids = set(asl_concepts)
bsl_ids = set(bsl_concepts)

if tmap_ids == asl_ids == bsl_ids:
    print(f"   ✓ All registries have identical concept IDs")
else:
    missing_asl = tmap_ids - asl_ids
    missing_bsl = tmap_ids - bsl_ids
    if missing_asl:
        print(f"   ✗ Missing in ASL: {missing_asl}")
    if missing_bsl:
        print(f"   ✗ Missing in BSL: {missing_bsl}")

print("\n" + "=" * 60)
print("✅ FILE STRUCTURE VERIFICATION COMPLETE")
print("=" * 60)
