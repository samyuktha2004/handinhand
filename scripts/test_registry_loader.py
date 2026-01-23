#!/usr/bin/env python3
"""Test registry loader functionality"""

from utils.registry_loader import RegistryLoader

print("Testing Registry Loader...")
print("=" * 60)

try:
    loader = RegistryLoader()

    # Test loading registries
    concepts = loader.get_concept_registry()
    concept_count = len([k for k in concepts.keys() if not k.startswith('_')])
    print(f"✓ Concept registry loaded: {concept_count} concepts")

    asl_reg = loader.get_language_registry('asl')
    asl_count = len([k for k in asl_reg.keys() if not k.startswith('_')])
    print(f"✓ ASL registry loaded: {asl_count} concepts")

    bsl_reg = loader.get_language_registry('bsl')
    bsl_count = len([k for k in bsl_reg.keys() if not k.startswith('_')])
    print(f"✓ BSL registry loaded: {bsl_count} concepts")

    # Test utility functions
    print("\nTesting utility functions...")
    langs = loader.list_languages()
    print(f"✓ Available languages: {langs}")

    concept_list = loader.list_concepts()
    print(f"✓ All concepts: {len(concept_list)}")

    asl_sigs = loader.get_signatures('asl', 'C_GREETING_001')
    print(f"✓ ASL signatures for C_GREETING_001: {len(asl_sigs)} found")

    emb_file = loader.get_embedding_file('asl', 'C_GREETING_001')
    print(f"✓ ASL embedding file: {emb_file}")

    metadata = loader.get_concept_metadata('C_GREETING_001')
    print(f"✓ Concept metadata loaded: {metadata['concept_name']}")

    print("\n" + "=" * 60)
    print("✅ All registry loader tests passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
