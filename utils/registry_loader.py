#!/usr/bin/env python3
"""
Registry Loader Utility
=======================

Provides transparent access to language-specific and concept registries.
Supports both old (inline) and new (separate) formats for backward compatibility.

Usage:
    from utils.registry_loader import RegistryLoader
    
    loader = RegistryLoader()
    asl_data = loader.get_language_registry('asl')
    asl_signatures = loader.get_signatures('asl', 'C_GREETING_001')
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


class RegistryLoader:
    """Load and access concept/language registries transparently."""
    
    # Supported registry paths (in order of preference)
    REGISTRY_PATHS = {
        'concepts': 'translation_map.json',
        'asl': 'assets/registries/asl_registry.json',
        'bsl': 'assets/registries/bsl_registry.json',
        'jsl': 'assets/registries/jsl_registry.json',  # Future
        'csl': 'assets/registries/csl_registry.json',  # Future
        'lsf': 'assets/registries/lsf_registry.json',  # Future
    }
    
    def __init__(self, base_dir: str = '.'):
        """Initialize registry loader."""
        self.base_dir = base_dir
        self._cache = {}  # Cache loaded registries
    
    def _resolve_path(self, registry_type: str) -> str:
        """Resolve path for a registry type."""
        path = self.REGISTRY_PATHS.get(registry_type)
        if not path:
            raise ValueError(f"Unknown registry type: {registry_type}")
        return os.path.join(self.base_dir, path)
    
    def get_language_registry(self, language: str) -> Dict[str, Any]:
        """
        Load language-specific registry (ASL, BSL, etc).
        
        Args:
            language: Language code ('asl', 'bsl', etc)
        
        Returns:
            Dict with language data
        """
        if language in self._cache:
            return self._cache[language]
        
        path = self._resolve_path(language)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Registry not found: {path}")
        
        with open(path) as f:
            registry = json.load(f)
        
        self._cache[language] = registry
        return registry
    
    def get_concept_registry(self) -> Dict[str, Any]:
        """
        Load concept registry (concepts, metadata, language references).
        
        Returns:
            Dict with concept metadata
        """
        if 'concepts' in self._cache:
            return self._cache['concepts']
        
        path = self._resolve_path('concepts')
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Concept registry not found: {path}")
        
        with open(path) as f:
            registry = json.load(f)
        
        self._cache['concepts'] = registry
        return registry
    
    def get_signatures(self, language: str, concept_id: str) -> List[Dict]:
        """
        Get signatures for a concept in a specific language.
        
        Args:
            language: Language code ('asl', 'bsl')
            concept_id: Concept ID (e.g., 'C_GREETING_001')
        
        Returns:
            List of signature dicts
        """
        registry = self.get_language_registry(language)
        
        if concept_id not in registry:
            return []
        
        if language == 'bsl':
            # BSL has 'target' instead of 'signatures'
            target = registry[concept_id].get('target')
            return [target] if target else []
        else:
            # Other languages have 'signatures' array
            return registry[concept_id].get('signatures', [])
    
    def get_embedding_file(self, language: str, concept_id: str) -> Optional[str]:
        """
        Get embedding file path for a concept in a specific language.
        
        Args:
            language: Language code ('asl', 'bsl')
            concept_id: Concept ID
        
        Returns:
            Path to embedding mean file (e.g., 'assets/embeddings/asl/hello_mean.npy')
        """
        registry = self.get_language_registry(language)
        
        if concept_id not in registry:
            return None
        
        return registry[concept_id].get('embedding_mean_file')
    
    def get_concept_metadata(self, concept_id: str) -> Dict:
        """
        Get metadata for a concept (name, description, languages, difficulty).
        
        Args:
            concept_id: Concept ID
        
        Returns:
            Concept metadata dict
        """
        concepts = self.get_concept_registry()
        
        if concept_id not in concepts:
            return {}
        
        return concepts[concept_id]
    
    def list_concepts(self, language: Optional[str] = None) -> List[str]:
        """
        List all concepts, optionally filtered by language.
        
        Args:
            language: Optional language code to filter by ('asl', 'bsl', etc)
        
        Returns:
            List of concept IDs
        """
        if language:
            registry = self.get_language_registry(language)
            return [k for k in registry.keys() if not k.startswith('_')]
        else:
            concepts = self.get_concept_registry()
            return [k for k in concepts.keys() if not k.startswith('_')]
    
    def list_languages(self) -> List[str]:
        """Get list of available languages."""
        concepts = self.get_concept_registry()
        all_languages = set()
        
        for concept_id, data in concepts.items():
            if not concept_id.startswith('_'):
                all_languages.update(data.get('languages', []))
        
        return sorted(list(all_languages))
    
    def clear_cache(self):
        """Clear cached registries (useful for testing or reloading)."""
        self._cache.clear()


# Singleton instance for convenience
_loader = None

def get_loader(base_dir: str = '.') -> RegistryLoader:
    """Get or create singleton loader instance."""
    global _loader
    if _loader is None:
        _loader = RegistryLoader(base_dir)
    return _loader


# Convenience functions for common operations
def get_language_registry(language: str) -> Dict:
    """Load language registry."""
    return get_loader().get_language_registry(language)

def get_concept_registry() -> Dict:
    """Load concept registry."""
    return get_loader().get_concept_registry()

def get_signatures(language: str, concept_id: str) -> List[Dict]:
    """Get signatures for concept/language."""
    return get_loader().get_signatures(language, concept_id)

def get_embedding_file(language: str, concept_id: str) -> Optional[str]:
    """Get embedding file for concept/language."""
    return get_loader().get_embedding_file(language, concept_id)

def list_concepts(language: Optional[str] = None) -> List[str]:
    """List concepts, optionally by language."""
    return get_loader().list_concepts(language)

def list_languages() -> List[str]:
    """List available languages."""
    return get_loader().list_languages()
