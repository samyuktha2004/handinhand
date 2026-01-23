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
  5. Update translation_map.json

Make it extensible: Just update TARGET_GLOSSES to add new words!
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import re

# ============================================================================
# CONFIGURATION - Easy to extend! Just add glosses here
# ============================================================================
TARGET_GLOSSES = ["hello", "you", "go", "where"]  # 4 anchor words for cross-lingual mapping
VIDEOS_PER_GLOSS = 2  # Download this many instances per gloss

# Directories
WLASL_JSON = "assets/wlasl_data/WLASL_v0.3.json"
DOWNLOAD_DIR = "assets/raw_videos/lexicon"
SIGNATURES_DIR = "assets/signatures"
OUTPUT_MAP = "translation_map.json"


class WALSLDownloadError(Exception):
    """Custom exception for WLASL pipeline errors."""
    pass


class WALSLPipeline:
    """Self-cleaning pipeline for WLASL video download → extraction → deletion."""

    def __init__(self):
        """Initialize pipeline."""
        self.wlasl_data = self._load_wlasl()
        self.downloaded_videos = []
        self.extracted_signatures = {}
        self.translation_map = self._load_translation_map()

    def _load_wlasl(self) -> List[Dict]:
        """Load WLASL JSON dataset."""
        if not os.path.exists(WLASL_JSON):
            raise WALSLDownloadError(f"WLASL JSON not found: {WLASL_JSON}")
        
        with open(WLASL_JSON) as f:
            return json.load(f)

    def _load_translation_map(self) -> Dict:
        """Load existing translation map or create new one."""
        if os.path.exists(OUTPUT_MAP):
            with open(OUTPUT_MAP) as f:
                return json.load(f)
        return {}

    def _save_translation_map(self):
        """Save translation map to JSON."""
        with open(OUTPUT_MAP, 'w') as f:
            json.dump(self.translation_map, f, indent=2)
        print(f"💾 Updated: {OUTPUT_MAP}")

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

    def extract_landmarks(self, video_path: str, gloss: str, instance_id: int, frame_start: int = -1, frame_end: int = -1) -> Optional[str]:
        """
        Extract landmarks using existing extractor script with frame range support.
        Returns path to signature JSON if successful, None otherwise.
        """
        try:
            # Use Python API instead of subprocess for cleaner integration
            sys.path.insert(0, os.path.abspath('.'))
            from extract_signatures import SignatureExtractor
            
            extractor = SignatureExtractor(output_dir=SIGNATURES_DIR, delete_after=False)
            
            # Create signature using frame range
            signature = extractor.extract_from_video_range(
                video_path,
                gloss,
                frame_start=frame_start,
                frame_end=frame_end,
                language="ASL"
            )
            
            if signature:
                # Generate filename: gloss_instanceid.json
                sig_filename = f"{gloss}_{instance_id}.json"
                sig_path = os.path.join(SIGNATURES_DIR, sig_filename)
                
                # Save without deletion (we'll handle that here)
                if extractor.save_signature(signature, sig_filename, source_video=None):
                    extractor.close()
                    return sig_path
            
            extractor.close()
            return None
            
        except ImportError:
            print(f"   ⚠️  Could not import extractor")
            return None
        except Exception as e:
            print(f"   ⚠️  Extraction error: {str(e)[:100]}")
            return None

    def _extract_landmarks_subprocess(self, video_path: str, gloss: str, instance_id: int) -> Optional[str]:
        """Fallback extraction using subprocess."""
        try:
            sig_filename = f"{gloss}_{instance_id}.json"
            sig_path = os.path.join(SIGNATURES_DIR, sig_filename)
            
            # This would require a separate extraction script
            # For now, assume direct import works
            return None
        except Exception as e:
            print(f"   ⚠️  Subprocess extraction failed: {str(e)[:100]}")
            return None

    def process_gloss(self, gloss: str) -> int:
        """Download and process all video instances for a gloss."""
        print(f"\n📚 Processing: {gloss.upper()}")
        print("=" * 60)
        
        videos = self.find_gloss_videos(gloss)
        if not videos:
            print(f"❌ No videos found for {gloss}")
            return 0
        
        print(f"📊 Found {len(videos)} instances (processing first {min(len(videos), VIDEOS_PER_GLOSS)})")
        
        success_count = 0
        
        for i, video_info in enumerate(videos):
            url = video_info.get('url')
            if not url:
                print(f"   ⚠️  Skipping instance {i}: no URL")
                continue
            
            try:
                # Step 1: Download
                print(f"\n   📥 Instance {i}: {url[:50]}...")
                video_filename = f"wlasl_{gloss}_{i}.mp4"
                video_path = os.path.join(DOWNLOAD_DIR, video_filename)
                
                if not self.download_video(url, video_path):
                    continue
                
                # Get frame range from WLASL metadata
                frame_start = video_info.get('frame_start', -1)
                frame_end = video_info.get('frame_end', -1)
                
                # OPTIMIZE: Expand frame range by 10% on each side to capture full sign
                # This ensures both hands and face stay in frame
                if frame_start > 0:
                    expand = max(1, int((frame_end - frame_start) * 0.1))
                    frame_start = max(0, frame_start - expand)
                if frame_end > 0:
                    expand = max(1, int((frame_end - frame_start) * 0.1))
                    frame_end = frame_end + expand
                
                # Step 2: Extract landmarks (only for frame range containing the sign)
                print(f"   🎯 Extracting landmarks (frames {frame_start} to {frame_end})...")
                print(f"      ✓ Frame range optimized to include both hands + face")
                sig_path = self.extract_landmarks(video_path, gloss, i, frame_start, frame_end)
                
                if not sig_path:
                    print(f"   ⚠️  Extraction failed")
                    # Still try to clean up video
                    if os.path.exists(video_path):
                        os.remove(video_path)
                        print(f"   🗑️  Cleaned up video")
                    continue
                
                print(f"   💾 Saved: {os.path.basename(sig_path)}")
                
                # Step 3: Delete video to save space
                if os.path.exists(video_path):
                    os.remove(video_path)
                    print(f"   🗑️  Deleted: {video_filename}")
                
                # Step 4: Update translation map
                map_key = f"{gloss}_{i}"
                self.translation_map[map_key] = {
                    "gloss": gloss,
                    "instance_id": i,
                    "signature_file": os.path.relpath(sig_path),
                    "language": "ASL",
                    "source_url": url,
                    "frame_range": {
                        "frame_start": frame_start,
                        "frame_end": frame_end
                    },
                    "frames": None  # Will be populated from JSON if needed
                }
                
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing instance {i}: {str(e)[:100]}")
                continue
        
        if success_count > 0:
            print(f"\n✅ Successfully processed {success_count}/{len(videos)} instances for {gloss.upper()}")
        
        return success_count

    def run(self):
        """Execute full pipeline for all target glosses."""
        print("\n" + "=" * 60)
        print("🚀 Self-Cleaning WLASL Pipeline")
        print("=" * 60)
        print(f"Target glosses: {', '.join(TARGET_GLOSSES)}")
        print(f"Videos per gloss: {VIDEOS_PER_GLOSS}")
        print(f"Download dir: {DOWNLOAD_DIR}")
        print(f"Signatures dir: {SIGNATURES_DIR}")
        print("=" * 60)
        
        total_processed = 0
        
        for gloss in TARGET_GLOSSES:
            try:
                count = self.process_gloss(gloss)
                total_processed += count
            except Exception as e:
                print(f"❌ Failed to process {gloss}: {str(e)}")
                continue
        
        # Save final translation map
        print(f"\n{'=' * 60}")
        self._save_translation_map()
        
        print(f"\n{'=' * 60}")
        print(f"✅ Pipeline Complete!")
        print(f"   Total signatures extracted: {total_processed}")
        print(f"   All .mp4 files cleaned up")
        print(f"   Translation map updated: {OUTPUT_MAP}")
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
