#!/usr/bin/env python3
"""
Full Migration Script: Extract, Refactor, and Update All Code
=========================================================

This script:
1. Creates asset/registries/ directory
2. Writes asl_registry.json and bsl_registry.json
3. Refactors translation_map.json to concept-centric schema
4. Backs up original translation_map.json
5. Tests all registries load correctly
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime

def backup_original():
    """Create backup of original translation_map.json"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"translation_map.json.backup_{timestamp}"
    
    if os.path.exists('translation_map.json'):
        shutil.copy('translation_map.json', backup_path)
        print(f"✓ Backup created: {backup_path}")
        return backup_path
    return None

def extract_and_write():
    """Extract registries and write all files"""
    
    # Load original
    with open('translation_map.json') as f:
        original_tmap = json.load(f)
    
    # Create registries
    asl_registry = {
        "_metadata": {
            "language": "asl",
            "purpose": "ASL signatures and embeddings for recognition",
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "description": "American Sign Language reference dataset - extracted from translation_map.json"
        }
    }
    
    bsl_registry = {
        "_metadata": {
            "language": "bsl",
            "purpose": "BSL target signatures and embeddings for output",
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "description": "British Sign Language reference dataset - extracted from translation_map.json"
        }
    }
    
    # Process concepts
    concepts = [k for k in original_tmap.keys() if not k.startswith('_')]
    print(f"\nExtracting {len(concepts)} concepts...")
    
    for concept in concepts:
        c = original_tmap[concept]
        concept_id = c.get('concept_id')
        
        # ASL registry entry
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
        
        # BSL registry entry
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
        
        print(f"  ✓ {concept_id}")
    
    # Create new translation_map with concept metadata only
    new_tmap = {
        "_metadata": {
            **original_tmap.get('_metadata', {}),
            "description": "Translation Registry: Concept Metadata (Language data in assets/registries/)",
            "version": "2.1-refactored",
            "last_updated": datetime.now().isoformat(),
            "notes": "Language-specific data moved to assets/registries/{asl,bsl}_registry.json for scalability"
        }
    }
    
    for concept in concepts:
        c = original_tmap[concept]
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
    
    return new_tmap, asl_registry, bsl_registry

def write_registries():
    """Write all registry files"""
    
    new_tmap, asl_registry, bsl_registry = extract_and_write()
    
    # Create registries directory
    registries_dir = 'assets/registries'
    os.makedirs(registries_dir, exist_ok=True)
    
    # Write ASL registry
    asl_path = os.path.join(registries_dir, 'asl_registry.json')
    with open(asl_path, 'w') as f:
        json.dump(asl_registry, f, indent=2)
    print(f"\n✓ Wrote ASL registry: {asl_path}")
    
    # Write BSL registry
    bsl_path = os.path.join(registries_dir, 'bsl_registry.json')
    with open(bsl_path, 'w') as f:
        json.dump(bsl_registry, f, indent=2)
    print(f"✓ Wrote BSL registry: {bsl_path}")
    
    # Write refactored translation_map.json
    with open('translation_map.json', 'w') as f:
        json.dump(new_tmap, f, indent=2)
    print(f"✓ Wrote refactored translation_map.json")
    
    return asl_registry, bsl_registry

def test_registries():
    """Test that all registries load correctly"""
    
    print("\n" + "=" * 60)
    print("TESTING REGISTRIES")
    print("=" * 60)
    
    # Load and validate each registry
    try:
        with open('translation_map.json') as f:
            tmap = json.load(f)
        concepts = len([k for k in tmap.keys() if not k.startswith('_')])
        print(f"✓ translation_map.json loaded: {concepts} concepts")
    except Exception as e:
        print(f"✗ Error loading translation_map.json: {e}")
        return False
    
    try:
        with open('assets/registries/asl_registry.json') as f:
            asl_reg = json.load(f)
        asl_concepts = len([k for k in asl_reg.keys() if not k.startswith('_')])
        print(f"✓ asl_registry.json loaded: {asl_concepts} concepts")
    except Exception as e:
        print(f"✗ Error loading asl_registry.json: {e}")
        return False
    
    try:
        with open('assets/registries/bsl_registry.json') as f:
            bsl_reg = json.load(f)
        bsl_concepts = len([k for k in bsl_reg.keys() if not k.startswith('_')])
        print(f"✓ bsl_registry.json loaded: {bsl_concepts} concepts")
    except Exception as e:
        print(f"✗ Error loading bsl_registry.json: {e}")
        return False
    
    # Validate cross-references
    tmap_ids = set(k for k in tmap.keys() if not k.startswith('_'))
    asl_ids = set(k for k in asl_reg.keys() if not k.startswith('_'))
    bsl_ids = set(k for k in bsl_reg.keys() if not k.startswith('_'))
    
    missing_asl = tmap_ids - asl_ids
    missing_bsl = tmap_ids - bsl_ids
    
    if missing_asl:
        print(f"✗ Missing in ASL registry: {missing_asl}")
        return False
    if missing_bsl:
        print(f"✗ Missing in BSL registry: {missing_bsl}")
        return False
    
    print(f"✓ All {len(tmap_ids)} concepts present in both registries")
    print("✓ Cross-reference validation passed")
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("FULL MIGRATION: Extract & Refactor Registries")
    print("=" * 60)
    
    # Step 1: Backup
    print("\n[STEP 1] Backing up original...")
    backup = backup_original()
    
    # Step 2: Extract and write
    print("\n[STEP 2] Extracting and writing registries...")
    asl_reg, bsl_reg = write_registries()
    
    # Step 3: Test
    print("\n[STEP 3] Testing registries...")
    if test_registries():
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE - All registries created and validated!")
        print("=" * 60)
        print(f"\nNew files created:")
        print(f"  • assets/registries/asl_registry.json")
        print(f"  • assets/registries/bsl_registry.json")
        print(f"  • translation_map.json (refactored)")
        print(f"\nBackup:")
        print(f"  • {backup}")
        print(f"\nNext steps:")
        print(f"  1. Test recognition_engine.py")
        print(f"  2. Update recognition_engine_ui.py")
        print(f"  3. Update wlasl_pipeline.py")
    else:
        print("\n✗ Migration failed - see errors above")
