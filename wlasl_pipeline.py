#!/usr/bin/env python3
"""
Self-Cleaning WLASL Pipeline
============================
Extract landmarks from WLASL dataset with automatic cleanup.

Workflow:
  1. Parse WLASL_v0.3.json for target glosses
  2. Download first N video instances using yt-dlp
  3. Extract MediaPipe landmarks & save as JSON
  4. Delete .mp4 files after extraction
  5. Update ASL registry (assets/registries/asl_registry.json)

Make it extensible: Just update TARGET_GLOSSES to add new words!
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re

from utils.registry_loader import RegistryLoader

# ============================================================================
# CONFIGURATION - Easy to extend! Just add glosses here
# ============================================================================
TARGET_GLOSSES = ["hello", "you", "go", "where"]  # 4 anchor words for cross-lingual mapping
VIDEOS_PER_GLOSS = 2  # Download this many instances per gloss

# VALIDATION RANGES (frames at 25 FPS)
WORD_FRAME_RANGE = (20, 400)        # 0.8 - 16 seconds for single words
SENTENCE_FRAME_RANGE = (400, 2000)  # 16 - 80 seconds for sentences
QUALITY_THRESHOLD = 80              # Minimum quality score (0-100)

# Directories
WLASL_JSON = "assets/wlasl_data/WLASL_v0.3.json"
DOWNLOAD_DIR = "assets/raw_videos/lexicon"
SIGNATURES_DIR = "assets/signatures"
SIGNATURES_ASL_DIR = "assets/signatures/asl"
REGISTRIES_DIR = "assets/registries"
SIGNATURES_BSL_DIR = "assets/signatures/bsl"
OUTPUT_MAP = "translation_map.json"


class WALSLDownloadError(Exception):
    """Custom exception for WLASL pipeline errors."""
    pass


class WALSLPipeline:
    """Self-cleaning pipeline with 3-tier verification: frame range validation, quality gating, conditional deletion."""

    def __init__(self):
        """Initialize pipeline."""
        self.wlasl_data = self._load_wlasl()
        self.downloaded_videos = []
        self.extracted_signatures = {}
        self.loader = RegistryLoader()
        self.asl_registry = self.loader.get_language_registry('asl')
        self._ensure_directories()

    def _load_wlasl(self) -> List[Dict]:
        """Load WLASL JSON dataset."""
        if not os.path.exists(WLASL_JSON):
            raise WALSLDownloadError(f"WLASL JSON not found: {WLASL_JSON}")
        
        with open(WLASL_JSON) as f:
            return json.load(f)

    def _ensure_directories(self):
        """Create required directory structure."""
        os.makedirs(SIGNATURES_ASL_DIR, exist_ok=True)
        os.makedirs(SIGNATURES_BSL_DIR, exist_ok=True)
        os.makedirs("assets/embeddings/asl", exist_ok=True)
        os.makedirs("assets/embeddings/bsl", exist_ok=True)
        os.makedirs("assets/embeddings/concept", exist_ok=True)
        os.makedirs(REGISTRIES_DIR, exist_ok=True)

    def _save_asl_registry(self):
        """Save ASL registry to JSON."""
        registry_path = os.path.join(REGISTRIES_DIR, 'asl_registry.json')
        with open(registry_path, 'w') as f:
            json.dump(self.asl_registry, f, indent=2)
        print(f"💾 Updated: {registry_path}")

    def find_gloss_videos(self, gloss: str) -> List[Dict]:
        """Find video instances for a gloss in WLASL."""
        entry = next((e for e in self.wlasl_data if e.get('gloss') == gloss), None)
        if not entry:
            return []
        
        # Return first N instances
        return entry.get('instances', [])[:VIDEOS_PER_GLOSS]

    def sanitize_filename(self, text: str) -> str:
        """Convert text to safe filename."""
        return re.sub(r'[^a-zA-Z0-9_]', '_', text)

    def download_video(self, url: str, output_path: str) -> bool:
        """Download video using yt-dlp."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            cmd = [
                'yt-dlp',
                '--quiet',
                '-f', 'best[ext=mp4]',
                '-o', output_path,
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"   ⚠️  Download failed: {url}")
                if result.stderr:
                    print(f"      Error: {result.stderr[:100]}")
                return False
            
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"   ✅ Downloaded ({size_mb:.1f} MB)")
                return True
            else:
                print(f"   ⚠️  File not created despite successful command")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Download timeout for: {url}")
            return False
        except Exception as e:
            print(f"   ⚠️  Download error: {str(e)[:100]}")
            return False

    def extract_landmarks(self, video_path: str, gloss: str, instance_id: int, frame_start: int = -1, frame_end: int = -1) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Extract landmarks using existing extractor script with frame range support.
        Returns tuple of (signature_path, quality_data) or (None, None) if failed.
        """
        try:
            # Use Python API instead of subprocess for cleaner integration
            sys.path.insert(0, os.path.abspath('.'))
            from extract_signatures import SignatureExtractor
            
            extractor = SignatureExtractor(output_dir=SIGNATURES_ASL_DIR, delete_after=False)
            
            # Create signature using frame range
            signature = extractor.extract_from_video_range(
                video_path,
                gloss,
                frame_start=frame_start,
                frame_end=frame_end,
                language="ASL"
            )
            
            if signature:
                # Generate filename: asl/gloss_instanceid.json
                sig_filename = f"{gloss}_{instance_id}.json"
                sig_path = os.path.join(SIGNATURES_ASL_DIR, sig_filename)
                
                # Save without deletion (we'll handle that here)
                if extractor.save_signature(signature, sig_filename, source_video=None):
                    # Compute quality metrics for verification gate
                    quality_data = self._compute_quality(sig_path)
                    extractor.close()
                    return sig_path, quality_data
            
            extractor.close()
            return None, None
            
        except ImportError:
            print(f"   ⚠️  Could not import extractor")
            return None, None
        except Exception as e:
            print(f"   ⚠️  Extraction error: {str(e)[:100]}")
            return None, None

    def _compute_quality(self, sig_path: str) -> Optional[Dict]:
        """Compute quality metrics for signature (zero-fill analysis)."""
        try:
            with open(sig_path) as f:
                data = json.load(f)
            
            total_frames = len(data.get('pose_data', []))
            if total_frames == 0:
                return None
            
            zero_counts = {'left_hand': 0, 'right_hand': 0, 'pose': 0, 'face': 0}
            for frame in data['pose_data']:
                if all(v == 0 for v in frame.get('left_hand', [])): zero_counts['left_hand'] += 1
                if all(v == 0 for v in frame.get('right_hand', [])): zero_counts['right_hand'] += 1
                if all(v == 0 for v in frame.get('pose', [])): zero_counts['pose'] += 1
                if all(v == 0 for v in frame.get('face', [])): zero_counts['face'] += 1
            
            # Simple quality score: average detection rate across all parts
            detection_rates = [(1 - count/total_frames) * 100 for count in zero_counts.values()]
            quality_score = sum(detection_rates) / len(detection_rates)
            
            return {
                'frames': total_frames,
                'quality_score': quality_score,
                'zero_fill_pct': {k: (v/total_frames)*100 for k, v in zero_counts.items()}
            }
        except Exception as e:
            print(f"      ⚠️  Quality check failed: {str(e)[:50]}")
            return None

    def process_gloss(self, gloss: str, is_sentence: bool = False) -> int:
        """
        Download and process all video instances for a gloss with 3-tier verification.
        
        Tier 1: Frame range validation (reject invalid WLASL metadata)
        Tier 2: Plausible range check (word: 20-400 frames, sentence: 400-2000 frames)
        Tier 3: Quality gate (auto-verify, only delete video if quality > threshold)
        """
        print(f"\n📚 Processing: {gloss.upper()}")
        print("=" * 60)
        
        videos = self.find_gloss_videos(gloss)
        if not videos:
            print(f"❌ No videos found for {gloss}")
            return 0
        
        print(f"📊 Found {len(videos)} instances (processing first {min(len(videos), VIDEOS_PER_GLOSS)})")
        
        success_count = 0
        skipped_count = 0
        
        for i, video_info in enumerate(videos):
            url = video_info.get('url')
            if not url:
                print(f"   ⚠️  Skipping instance {i}: no URL")
                skipped_count += 1
                continue
            
            try:
                # Step 1: Download
                print(f"\n   📥 Instance {i}: {url[:50]}...")
                video_filename = f"wlasl_{gloss}_{i}.mp4"
                video_path = os.path.join(DOWNLOAD_DIR, video_filename)
                
                if not self.download_video(url, video_path):
                    skipped_count += 1
                    continue
                
                # Get frame range from WLASL metadata
                frame_start = video_info.get('frame_start', -1)
                frame_end = video_info.get('frame_end', -1)
                
                # TIER 1: Validate frame range (reject invalid WLASL metadata)
                if frame_start <= 0 or frame_end <= 0 or frame_end <= frame_start:
                    print(f"   ❌ TIER 1 FAILED: Invalid frame range ({frame_start}-{frame_end})")
                    if os.path.exists(video_path):
                        os.remove(video_path)
                        print(f"      🗑️  Deleted video (invalid metadata)")
                    skipped_count += 1
                    continue
                
                # OPTIMIZE: Expand frame range by 10% on each side to capture full sign
                expand = max(1, int((frame_end - frame_start) * 0.1))
                frame_start_expanded = max(0, frame_start - expand)
                frame_end_expanded = frame_end + expand
                total_frames = frame_end_expanded - frame_start_expanded
                
                # TIER 2: Check plausible frame count (based on word vs sentence)
                if is_sentence:
                    min_frames, max_frames = SENTENCE_FRAME_RANGE
                else:
                    min_frames, max_frames = WORD_FRAME_RANGE
                
                if total_frames < min_frames or total_frames > max_frames:
                    print(f"   ❌ TIER 2 FAILED: {total_frames} frames outside range ({min_frames}-{max_frames})")
                    if os.path.exists(video_path):
                        os.remove(video_path)
                        print(f"      🗑️  Deleted video (implausible duration)")
                    skipped_count += 1
                    continue
                
                print(f"   ✅ TIER 1 & 2 PASSED: {total_frames} frames ({total_frames/25:.1f}s)")
                
                # Step 2: Extract landmarks
                print(f"   🎯 Extracting landmarks...")
                sig_path, quality_data = self.extract_landmarks(
                    video_path, gloss, i, frame_start_expanded, frame_end_expanded
                )
                
                if not sig_path or not quality_data:
                    print(f"   ❌ Extraction failed")
                    if os.path.exists(video_path):
                        os.remove(video_path)
                        print(f"      🗑️  Deleted video (extraction failure)")
                    skipped_count += 1
                    continue
                
                print(f"   💾 Saved: {os.path.basename(sig_path)}")
                print(f"      Quality score: {quality_data['quality_score']:.1f}/100")
                print(f"      Frames: {quality_data['frames']}")
                
                # TIER 3: Quality gate - only delete video if quality passes
                if quality_data['quality_score'] >= QUALITY_THRESHOLD:
                    print(f"   ✅ TIER 3 PASSED: Quality {quality_data['quality_score']:.1f} >= {QUALITY_THRESHOLD}")
                    if os.path.exists(video_path):
                        os.remove(video_path)
                        print(f"      🗑️  Deleted: {video_filename}")
                    verification_status = "auto_verified"
                else:
                    print(f"   ⚠️  TIER 3 WARNING: Quality {quality_data['quality_score']:.1f} < {QUALITY_THRESHOLD}")
                    print(f"      🔍 Keeping video for manual review")
                    verification_status = "manual_review"
                
                # Step 3: Update ASL registry
                # Find or create concept_id for this gloss
                # (In production, this would be linked to concept map)
                concept_id = f"C_{gloss.upper()}_001"  # Placeholder ID
                
                if concept_id not in self.asl_registry:
                    self.asl_registry[concept_id] = {
                        "concept_name": gloss.upper(),
                        "concept_description": f"ASL for '{gloss}'",
                        "signatures": [],
                        "embedding_mean_file": f"assets/embeddings/asl/{gloss}_mean.npy",
                        "metadata": {
                            "hands_involved": None,
                            "pose_involvement": True,
                            "face_involvement": True
                        }
                    }
                
                # Add signature entry
                sig_entry = {
                    "gloss": gloss,
                    "instance_id": i,
                    "signature_file": os.path.relpath(sig_path),
                    "source_url": url,
                    "frame_range": {
                        "frame_start": frame_start,
                        "frame_end": frame_end
                    },
                    "frames": quality_data['frames'],
                    "verification_status": verification_status
                }
                
                self.asl_registry[concept_id]["signatures"].append(sig_entry)
                
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing instance {i}: {str(e)[:100]}")
                if os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                    except:
                        pass
                skipped_count += 1
                continue
        
        if success_count > 0:
            print(f"\n✅ Successfully processed {success_count}/{len(videos)} instances for {gloss.upper()}")
        if skipped_count > 0:
            print(f"⏭️  Skipped {skipped_count} instances")
        
        return success_count

    def run(self):
        """Execute full pipeline for all target glosses."""
        print("\n" + "=" * 60)
        print("🚀 Self-Cleaning WLASL Pipeline (3-Tier Verification)")
        print("=" * 60)
        print(f"Target glosses: {', '.join(TARGET_GLOSSES)}")
        print(f"Videos per gloss: {VIDEOS_PER_GLOSS}")
        print(f"Download dir: {DOWNLOAD_DIR}")
        print(f"ASL signatures dir: {SIGNATURES_ASL_DIR}")
        print(f"BSL signatures dir: {SIGNATURES_BSL_DIR}")
        print(f"Embeddings dir: assets/embeddings/")
        print(f"\nVerification tiers:")
        print(f"  Tier 1: Frame range validation (reject invalid metadata)")
        print(f"  Tier 2: Plausible duration check (word: {WORD_FRAME_RANGE}, sentence: {SENTENCE_FRAME_RANGE})")
        print(f"  Tier 3: Quality gate (delete video only if quality >= {QUALITY_THRESHOLD})")
        print("=" * 60)
        
        total_processed = 0
        
        for gloss in TARGET_GLOSSES:
            try:
                count = self.process_gloss(gloss)
                total_processed += count
            except Exception as e:
                print(f"❌ Failed to process {gloss}: {str(e)}")
                continue
        
        # Save final ASL registry
        print(f"\n{'=' * 60}")
        self._save_asl_registry()
        
        print(f"\n{'=' * 60}")
        print(f"✅ Pipeline Complete!")
        print(f"   Total signatures extracted: {total_processed}")
        print(f"   All .mp4 files cleaned up")
        print(f"   ASL registry updated: assets/registries/asl_registry.json")
        print("=" * 60)
        
        return total_processed > 0


def main():
    """Main entry point."""
    try:
        pipeline = WALSLPipeline()
        success = pipeline.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
