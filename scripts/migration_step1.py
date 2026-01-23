#!/usr/bin/env python3
"""
Migration Step 1: Extract ASL and BSL data into separate registries.
Keeps translation_map.json intact during extraction phase.
"""

import json
import os

def extract_language_registries():
    """Extract ASL and BSL registries from translation_map.json"""
    
    # Load current translation map
    with open('translation_map.json') as f:
        tmap = json.load(f)
    
    # Create registries
    asl_registry = {
        "_metadata": {
            "language": "asl",
            "purpose": "ASL signatures and embeddings for recognition",
            "version": "1.0",
            "last_updated": "2026-01-23",
            "description": "American Sign Language reference dataset"
        }
    }
    
    bsl_registry = {
        "_metadata": {
            "language": "bsl",
            "purpose": "BSL target signatures and embeddings for output",
            "version": "1.0",
            "last_updated": "2026-01-23",
            "description": "British Sign Language reference dataset"
        }
    }
    
    # Process each concept
    concepts = [k for k in tmap.keys() if not k.startswith('_')]
    print(f"Processing {len(concepts)} concepts...\n")
    
    for concept in concepts:
        c = tmap[concept]
        concept_id = c.get('concept_id')
        
        # Extract ASL data
        asl_registry[concept_id] = {
            "concept_name": c.get('concept_name'),
            "concept_description": c.get('concept_description'),
            "signatures": c.get('asl_signatures', []),
            "embedding_mean_file": c.get('asl_embedding_mean_file'),
            "metadata": {
                "hands_involved": c.get('hands_involved'),
                "pose_involvement": c.get('pose_involvement'),
                "face_involvement": c.get('face_involvement')
            }
        }
        
        # Extract BSL data
        bsl_registry[concept_id] = {
            "concept_name": c.get('concept_name'),
            "concept_description": c.get('concept_description'),
            "target": c.get('bsl_target'),
            "embedding_mean_file": c.get('bsl_embedding_mean_file'),
            "metadata": {
                "hands_involved": c.get('hands_involved'),
                "pose_involvement": c.get('pose_involvement'),
                "face_involvement": c.get('face_involvement')
            }
        }
        
        print(f"  ✓ {concept_id}: ASL + BSL extracted")
    
    print(f"\n✅ ASL Registry: {len(asl_registry)} entries (including metadata)")
    print(f"✅ BSL Registry: {len(bsl_registry)} entries (including metadata)")
    
    return asl_registry, bsl_registry

def create_refactored_translation_map():
    """Create concept-centric translation map without language-specific data"""
    
    with open('translation_map.json') as f:
        tmap = json.load(f)
    
    # Create new refactored map
    new_tmap = {
        "_metadata": tmap.get('_metadata')
    }
    
    # Keep only concept metadata
    concepts = [k for k in tmap.keys() if not k.startswith('_')]
    for concept in concepts:
        c = tmap[concept]
        concept_id = c.get('concept_id')
        
        # Determine available languages
        languages = []
        if c.get('asl_signatures'):
            languages.append('asl')
        if c.get('bsl_target'):
            languages.append('bsl')
        
        new_tmap[concept_id] = {
            "concept_id": concept_id,
            "concept_name": c.get('concept_name'),
            "concept_description": c.get('concept_description'),
            "semantic_concept_vector": c.get('semantic_concept_vector'),
            "languages": languages,
            "difficulty": c.get('difficulty'),
            "hands_involved": c.get('hands_involved'),
            "pose_involvement": c.get('pose_involvement'),
            "face_involvement": c.get('face_involvement'),
            "status": c.get('status'),
            "notes": c.get('notes')
        }
    
    return new_tmap

def verify_registries(asl_reg, bsl_reg):
    """Verify registry integrity"""
    
    asl_concepts = {k: v for k, v in asl_reg.items() if not k.startswith('_')}
    bsl_concepts = {k: v for k, v in bsl_reg.items() if not k.startswith('_')}
    
    print("\n🔍 Verifying registry integrity...")
    
    # Check all concepts have embeddings
    for cid, data in asl_concepts.items():
        if not data.get('embedding_mean_file'):
            print(f"  ⚠️  {cid}: Missing ASL embedding file")
        if not data.get('signatures'):
            print(f"  ⚠️  {cid}: Missing ASL signatures")
    
    for cid, data in bsl_concepts.items():
        if not data.get('embedding_mean_file'):
            print(f"  ⚠️  {cid}: Missing BSL embedding file")
        if not data.get('target'):
            print(f"  ⚠️  {cid}: Missing BSL target")
    
    print("✅ Registry verification complete")

if __name__ == '__main__':
    print("=" * 60)
    print("STEP 1: Extract Language Registries")
    print("=" * 60)
    
    # Extract
    asl_reg, bsl_reg = extract_language_registries()
    
    # Verify
    verify_registries(asl_reg, bsl_reg)
    
    # Create refactored map
    print("\n" + "=" * 60)
    print("STEP 2: Create Refactored translation_map.json")
    print("=" * 60)
    new_tmap = create_refactored_translation_map()
    print(f"\n✅ New translation_map.json prepared: {len(new_tmap)} entries")
    
    # Don't write yet - just prepare
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"ASL Registry concepts: {len([k for k in asl_reg.keys() if not k.startswith('_')])}")
    print(f"BSL Registry concepts: {len([k for k in bsl_reg.keys() if not k.startswith('_')])}")
    print(f"Refactored translation_map: {len([k for k in new_tmap.keys() if not k.startswith('_')])} concepts")
    print("\n✅ Ready to write files. Run with --commit to save.")
