#!/usr/bin/env python3
"""
Test frame range extraction with your existing 4 lexicon videos.
This demonstrates the optimized extraction: only the sign movement frames.
"""

import json
import os
from extract_signatures import SignatureExtractor

# Your existing test videos (already have frame data from WLASL)
TEST_VIDEOS = {
    "bsl_hello": {
        "path": "assets/raw_videos/lexicon/bsl_hello.mp4",
        "frame_start": 5,
        "frame_end": 25,
    },
    "bsl_you": {
        "path": "assets/raw_videos/lexicon/bsl_you.mp4",
        "frame_start": 3,
        "frame_end": 22,
    },
    "bsl_go": {
        "path": "assets/raw_videos/lexicon/bsl_go.mp4",
        "frame_start": 2,
        "frame_end": 28,
    },
    "bsl_where": {
        "path": "assets/raw_videos/lexicon/bsl_where.mp4",
        "frame_start": 4,
        "frame_end": 26,
    },
}


def test_frame_range_extraction():
    """Test extraction with frame ranges."""
    print("=" * 70)
    print("🧪 Testing Frame Range Extraction")
    print("=" * 70)
    print("\nThis demonstrates extracting ONLY the sign movement frames,")
    print("not the entire video. This is optimal for sign language recognition.\n")

    extractor = SignatureExtractor(output_dir="assets/signatures")
    translation_map = {}

    for sign_name, video_info in TEST_VIDEOS.items():
        video_path = video_info["path"]
        frame_start = video_info["frame_start"]
        frame_end = video_info["frame_end"]

        if not os.path.exists(video_path):
            print(f"⚠️  Skipping {sign_name}: video not found at {video_path}")
            continue

        print(f"\n📹 Extracting: {sign_name}")
        print(f"   Video: {video_path}")
        print(f"   Frame range: {frame_start} - {frame_end} (only sign movement)")

        # Extract using frame range
        signature = extractor.extract_from_video_range(
            video_path,
            sign_name,
            frame_start=frame_start,
            frame_end=frame_end,
            language="BSL",
        )

        if signature:
            # Save signature
            filename = f"{sign_name}_frame_range.json"
            if extractor.save_signature(signature, filename, source_video=None):
                # Track in translation map
                sig_path = os.path.join("assets/signatures", filename)
                translation_map[sign_name] = {
                    "signature_file": sig_path,
                    "language": "BSL",
                    "frames_extracted": signature["metadata"]["total_frames"],
                    "frame_range": {
                        "frame_start": frame_start,
                        "frame_end": frame_end,
                    },
                }

                print(f"   ✅ Success! Extracted {signature['metadata']['total_frames']} frames")
                print(
                    f"      (Range: {frame_end - frame_start} frames requested, "
                    f"{signature['metadata']['total_frames']} actual)"
                )
        else:
            print(f"   ❌ Extraction failed")

    # Save translation map
    print(f"\n{'=' * 70}")
    with open("translation_map_frame_test.json", "w") as f:
        json.dump(translation_map, f, indent=2)
    print(f"✅ Translation map saved: translation_map_frame_test.json")

    # Print summary
    print(f"\n{'=' * 70}")
    print("📊 Summary:")
    print(f"   Signatures extracted: {len(translation_map)}")

    total_frames = sum(v["frames_extracted"] for v in translation_map.values())
    print(f"   Total frames extracted: {total_frames}")
    print(f"\n💡 Key benefit: By using frame ranges, we've dramatically reduced")
    print(f"   file sizes by extracting ONLY the sign movement, not idle frames.\n")
    print("=" * 70)

    extractor.close()
    return len(translation_map) > 0


if __name__ == "__main__":
    import sys

    success = test_frame_range_extraction()
    sys.exit(0 if success else 1)
