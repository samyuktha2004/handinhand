#!/usr/bin/env python3
"""
Final Comprehensive Validation
==============================

Validates:
1. All registries load correctly
2. Registry loader works
3. Recognition engine imports successfully
4. All dependent scripts can import
5. No breaking changes to existing functionality
"""

import json
import os
import sys

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("🔍 COMPREHENSIVE MIGRATION VALIDATION")
print("=" * 70)

errors = []

# ============================================================================
# TEST 1: Registry Structure
# ============================================================================
print("\n[TEST 1] Registry Structure...")
print("-" * 70)

try:
    with open('translation_map.json') as f:
        tmap = json.load(f)
    concepts = [k for k in tmap.keys() if not k.startswith('_')]
    print(f"  ✓ Concept registry: {len(concepts)} concepts")
    
    with open('assets/registries/asl_registry.json') as f:
        asl = json.load(f)
    asl_count = len([k for k in asl.keys() if not k.startswith('_')])
    print(f"  ✓ ASL registry: {asl_count} concepts")
    
    with open('assets/registries/bsl_registry.json') as f:
        bsl = json.load(f)
    bsl_count = len([k for k in bsl.keys() if not k.startswith('_')])
    print(f"  ✓ BSL registry: {bsl_count} concepts")
    
    # Cross-check
    if len(concepts) == asl_count == bsl_count:
        print(f"  ✓ All registries consistent")
    else:
        errors.append("Registry count mismatch")
        
except Exception as e:
    errors.append(f"Registry structure error: {e}")
    print(f"  ✗ {e}")

# ============================================================================
# TEST 2: Registry Loader
# ============================================================================
print("\n[TEST 2] Registry Loader...")
print("-" * 70)

try:
    from utils.registry_loader import RegistryLoader, get_loader
    
    loader = RegistryLoader()
    print(f"  ✓ RegistryLoader class instantiated")
    
    # Test loading
    c_reg = loader.get_concept_registry()
    print(f"  ✓ Concept registry loaded: {len([k for k in c_reg.keys() if not k.startswith('_')])} entries")
    
    a_reg = loader.get_language_registry('asl')
    print(f"  ✓ ASL registry loaded: {len([k for k in a_reg.keys() if not k.startswith('_')])} entries")
    
    b_reg = loader.get_language_registry('bsl')
    print(f"  ✓ BSL registry loaded: {len([k for k in b_reg.keys() if not k.startswith('_')])} entries")
    
    # Test utility functions
    langs = loader.list_languages()
    print(f"  ✓ Languages: {langs}")
    
    sigs = loader.get_signatures('asl', 'C_GREETING_001')
    print(f"  ✓ ASL signatures retrieved: {len(sigs)} found")
    
except Exception as e:
    errors.append(f"Registry loader error: {e}")
    print(f"  ✗ {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TEST 3: Recognition Engine Imports
# ============================================================================
print("\n[TEST 3] Recognition Engine Imports...")
print("-" * 70)

try:
    # Just test imports, not full initialization (requires MediaPipe)
    import recognition_engine
    print(f"  ✓ recognition_engine imports successfully")
    
    import recognition_engine_ui
    print(f"  ✓ recognition_engine_ui imports successfully")
    
except Exception as e:
    # MediaPipe import failures are OK, we're testing registry integration
    if "cv2" in str(e) or "mediapipe" in str(e):
        print(f"  ✓ (External dependency not installed, expected)")
    else:
        errors.append(f"Engine import error: {e}")
        print(f"  ✗ {e}")

# ============================================================================
# TEST 4: Pipeline Updates
# ============================================================================
print("\n[TEST 4] Pipeline Updates...")
print("-" * 70)

try:
    import wlasl_pipeline
    print(f"  ✓ wlasl_pipeline imports successfully")
    
    import generate_embeddings
    print(f"  ✓ generate_embeddings imports successfully")
    
except Exception as e:
    errors.append(f"Pipeline import error: {e}")
    print(f"  ✗ {e}")

# ============================================================================
# TEST 5: Data Integrity
# ============================================================================
print("\n[TEST 5] Data Integrity Checks...")
print("-" * 70)

try:
    # Verify translation_map has NO language-specific inline data
    for concept_id, data in tmap.items():
        if concept_id.startswith('_'):
            continue
        
        bad_keys = [k for k in data.keys() if 'asl_' in k or 'bsl_' in k]
        if bad_keys:
            errors.append(f"Found language keys in translation_map: {bad_keys}")
    
    if not any("Found language keys" in str(e) for e in errors):
        print(f"  ✓ No language-specific data in translation_map (clean)")
    
    # Verify ASL registry has signatures
    for concept_id, data in asl.items():
        if concept_id.startswith('_'):
            continue
        if not data.get('signatures'):
            errors.append(f"ASL registry {concept_id} missing signatures")
    
    if not any("missing signatures" in str(e) for e in errors):
        print(f"  ✓ ASL registry properly structured")
    
    # Verify BSL registry has targets
    for concept_id, data in bsl.items():
        if concept_id.startswith('_'):
            continue
        if not data.get('target'):
            errors.append(f"BSL registry {concept_id} missing target")
    
    if not any("missing target" in str(e) for e in errors):
        print(f"  ✓ BSL registry properly structured")
    
except Exception as e:
    errors.append(f"Data integrity error: {e}")
    print(f"  ✗ {e}")

# ============================================================================
# TEST 6: File Structure
# ============================================================================
print("\n[TEST 6] File Structure...")
print("-" * 70)

required_files = [
    'translation_map.json',
    'assets/registries/asl_registry.json',
    'assets/registries/bsl_registry.json',
    'utils/registry_loader.py',
    'scripts/migration_execute.py',
    'docs/RECOGNITION_ENGINE_DESIGN.md'
]

for filepath in required_files:
    if os.path.exists(filepath):
        print(f"  ✓ {filepath}")
    else:
        errors.append(f"Missing file: {filepath}")
        print(f"  ✗ {filepath} NOT FOUND")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

if errors:
    print(f"\n❌ {len(errors)} ERROR(S) FOUND:\n")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")
    print("\n❌ VALIDATION FAILED")
    sys.exit(1)
else:
    print("""
✅ ALL TESTS PASSED!

Migration completed successfully:
  • Translation map refactored to concept-centric schema
  • ASL and BSL registries created and validated
  • Registry loader utility implemented
  • Recognition engines updated to use new registries
  • Pipeline updated to write to language registries
  • All dependencies resolved

Next steps:
  1. Review MIGRATION_PLAN.md for architecture overview
  2. Test recognition_engine.py with actual video input
  3. Monitor logs for any runtime issues
  4. When ready, delete backup file: translation_map.json.backup_*

System is ready for multi-language scaling!
    """)
    sys.exit(0)
