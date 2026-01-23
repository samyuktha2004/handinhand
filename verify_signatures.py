#!/usr/bin/env python3
"""
Signature Quality Verification Script

Loads JSON golden signatures and:
- Animates 3D landmarks frame-by-frame
- Color-codes by landmark type
- Detects zero-filled frames (missing detections)
- Generates quality report
- Exports animation as video (optional)
"""

# Configure matplotlib backend for interactive 3D visualization on macOS
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 for interactive 3D plots (requires PyQt5)

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import argparse
from typing import Dict, Tuple
import warnings

warnings.filterwarnings("ignore")


class SignatureVerifier:
    """Verify quality of extracted signatures."""

    # Colors for different landmark types
    COLORS = {
        "left_hand": "red",
        "right_hand": "blue",
        "pose": "green",
        "face": "orange",
    }

    # Size multipliers for better visibility
    SIZES = {
        "left_hand": 30,
        "right_hand": 30,
        "pose": 60,
        "face": 40,
    }

    def __init__(self, json_path: str):
        """Load signature JSON file."""
        self.json_path = Path(json_path)
        if not self.json_path.exists():
            raise FileNotFoundError(f"File not found: {json_path}")

        with open(json_path, "r") as f:
            self.signature = json.load(f)

        self.sign_name = self.signature.get("sign", "unknown")
        self.language = self.signature.get("language", "unknown")
        self.pose_data = self.signature.get("pose_data", [])
        self.metadata = self.signature.get("metadata", {})

        print(f"✅ Loaded signature: {self.sign_name} ({self.language})")
        print(f"   Total frames: {len(self.pose_data)}")

    def _is_frame_zero_filled(self, frame: Dict) -> bool:
        """Check if entire frame is zero-filled (no detection)."""
        for landmark_group in frame.values():
            for point in landmark_group:
                if any(coord != 0.0 for coord in point):
                    return False
        return True

    def _count_zero_points(self, frame: Dict) -> Tuple[int, int]:
        """Count zero vs non-zero points in a frame."""
        zero_count = 0
        total_count = 0

        for landmark_group in frame.values():
            for point in landmark_group:
                total_count += 1
                if all(coord == 0.0 for coord in point):
                    zero_count += 1

        return zero_count, total_count

    def analyze_quality(self) -> Dict:
        """Analyze signature quality and return statistics."""
        print("\n" + "=" * 60)
        print("📊 Quality Analysis")
        print("=" * 60)

        # Count frames with detection issues
        fully_zero_frames = sum(1 for frame in self.pose_data if self._is_frame_zero_filled(frame))
        zero_percentage = (fully_zero_frames / len(self.pose_data) * 100) if self.pose_data else 0

        print(f"\n🔍 Detection Integrity:")
        print(f"   Total frames: {len(self.pose_data)}")
        print(f"   Fully zero-filled frames: {fully_zero_frames} ({zero_percentage:.1f}%)")

        # Per-landmark-group analysis
        print(f"\n📍 Per-Landmark Analysis:")
        landmark_groups = ["left_hand", "right_hand", "pose", "face"]
        group_stats = {}

        for group_name in landmark_groups:
            zero_points = 0
            total_points = 0

            for frame in self.pose_data:
                if group_name in frame:
                    for point in frame[group_name]:
                        total_points += 1
                        if all(coord == 0.0 for coord in point):
                            zero_points += 1

            if total_points > 0:
                group_pct = (zero_points / total_points) * 100
                group_stats[group_name] = group_pct
                status = "⚠️ " if group_pct > 20 else "✅"
                print(f"   {status} {group_name:12}: {group_pct:5.1f}% zero-filled")
            else:
                group_stats[group_name] = 0

        # Quality assessment
        print(f"\n⭐ Quality Assessment:")
        if zero_percentage > 20:
            print(f"   🔴 WARNING: {zero_percentage:.1f}% of frames are zero-filled!")
            print(f"   💡 Suggestions:")
            print(f"      - Check lighting conditions")
            print(f"      - Ensure clear hand visibility")
            print(f"      - Try recording in better lighting")
            print(f"      - Check video resolution/quality")
            quality_score = max(0, 100 - (zero_percentage * 2))
        else:
            print(f"   ✅ Good detection quality ({100-zero_percentage:.1f}% frames detected)")
            quality_score = 100 - (zero_percentage * 2)

        # Check for specific problem areas
        problematic_groups = [g for g, pct in group_stats.items() if pct > 15]
        if problematic_groups:
            print(f"\n   ⚠️ Problem areas detected: {', '.join(problematic_groups)}")
            print(f"   Consider re-recording with better positioning for these parts")

        print(f"\n   📈 Overall Quality Score: {quality_score:.1f}/100")

        return {
            "total_frames": len(self.pose_data),
            "zero_frames": fully_zero_frames,
            "zero_percentage": zero_percentage,
            "group_stats": group_stats,
            "quality_score": quality_score,
        }

    def create_animation(
        self, save_video: bool = False, max_frames: int = None, interval: int = 50
    ):
        """
        Create 3D animation of landmarks.

        Args:
            save_video: Whether to save animation as MP4
            max_frames: Limit animation to first N frames (for preview)
            interval: Milliseconds between frames
        """
        frames_to_show = self.pose_data
        if max_frames:
            frames_to_show = frames_to_show[:max_frames]

        print(f"\n🎬 Creating animation ({len(frames_to_show)} frames)...")

        # Create figure with 3D plot + statistics
        fig = plt.figure(figsize=(16, 6))
        ax_3d = fig.add_subplot(121, projection="3d")
        ax_stats = fig.add_subplot(122)

        # Initialize plots
        scatter_plots = {group: None for group in self.COLORS.keys()}

        # Flatten plot for statistics
        ax_stats.axis("off")

        def update_frame(frame_idx):
            ax_3d.clear()
            frame = frames_to_show[frame_idx]

            # Plot each landmark group
            for group_name, color in self.COLORS.items():
                if group_name in frame:
                    points = np.array(frame[group_name])
                    # Filter out zero points for cleaner visualization
                    non_zero = points[~(points == 0).all(axis=1)]
                    if len(non_zero) > 0:
                        ax_3d.scatter(
                            non_zero[:, 0],
                            non_zero[:, 1],
                            non_zero[:, 2],
                            c=color,
                            s=self.SIZES[group_name],
                            label=group_name,
                            alpha=0.7,
                        )

            # Set labels and limits
            ax_3d.set_xlabel("X")
            ax_3d.set_ylabel("Y")
            ax_3d.set_zlabel("Z")
            ax_3d.set_xlim([0, 1])
            ax_3d.set_ylim([0, 1])
            ax_3d.set_zlim([0, 1])
            ax_3d.legend(loc="upper right", fontsize=8)
            ax_3d.set_title(f"{self.sign_name} - Frame {frame_idx + 1}/{len(frames_to_show)}", fontsize=12, fontweight="bold")

            # Update statistics panel
            ax_stats.clear()
            ax_stats.axis("off")

            # Calculate per-frame stats
            zero_count, total_count = self._count_zero_points(frame)
            zero_pct = (zero_count / total_count * 100) if total_count > 0 else 0

            # Display stats
            stats_text = f"""
FRAME STATISTICS
{'─' * 40}

Frame:  {frame_idx + 1} / {len(frames_to_show)}
Progress: {'█' * int((frame_idx + 1) / len(frames_to_show) * 20):<20}

Zero Points: {zero_count:3d} / {total_count:3d} ({zero_pct:5.1f}%)

Sign: {self.sign_name}
Language: {self.language}

{'─' * 40}
Landmark Breakdown:
"""

            for group_name in self.COLORS.keys():
                if group_name in frame:
                    points = np.array(frame[group_name])
                    zeros = (points == 0).all(axis=1).sum()
                    total = len(points)
                    pct = (zeros / total * 100) if total > 0 else 0
                    stats_text += f"\n{group_name:15}: {zeros:2d}/{total:2d} ({pct:5.1f}%)"

            ax_stats.text(
                0.05,
                0.95,
                stats_text,
                transform=ax_stats.transAxes,
                fontsize=10,
                verticalalignment="top",
                fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
            )

        # Create animation
        anim = FuncAnimation(
            fig,
            update_frame,
            frames=len(frames_to_show),
            interval=interval,
            repeat=True,
            repeat_delay=1000,
        )

        if save_video:
            output_path = self.json_path.parent / f"{self.sign_name}_preview.gif"
            print(f"💾 Saving animation to: {output_path}")
            writer = PillowWriter(fps=20)
            anim.save(output_path, writer=writer)
            print(f"✅ Animation saved!")

        plt.tight_layout()
        plt.show()

    def generate_report(self, output_file: str = None):
        """Generate detailed quality report."""
        stats = self.analyze_quality()

        report = f"""
{'=' * 70}
SIGNATURE QUALITY REPORT
{'=' * 70}

📋 METADATA
  Sign: {self.sign_name}
  Language: {self.language}
  Total Frames: {stats['total_frames']}
  FPS: {self.metadata.get('fps', 'N/A')}

📊 DETECTION QUALITY
  Fully Zero-Filled Frames: {stats['zero_frames']} ({stats['zero_percentage']:.1f}%)
  
  Per-Landmark Analysis:
{chr(10).join([f"    {group:15}: {pct:5.1f}% zero-filled" for group, pct in stats['group_stats'].items()])}

⭐ OVERALL QUALITY SCORE: {stats['quality_score']:.1f}/100

🔍 RECOMMENDATION:
"""

        if stats["quality_score"] >= 80:
            report += "  ✅ Excellent! Ready for recognition pipeline.\n"
        elif stats["quality_score"] >= 60:
            report += "  ⚠️  Acceptable, but consider re-recording with better lighting.\n"
        else:
            report += "  🔴 Poor quality. Strongly recommend re-recording.\n"

        report += "\n" + "=" * 70

        print(report)

        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            print(f"\n💾 Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Verify quality of signature JSON files"
    )
    parser.add_argument("json_file", help="Path to signature JSON file")
    parser.add_argument(
        "--animate",
        action="store_true",
        help="Show 3D animation of landmarks",
    )
    parser.add_argument(
        "--save-gif",
        action="store_true",
        help="Save animation as GIF file",
    )
    parser.add_argument(
        "--preview-frames",
        type=int,
        default=None,
        help="Limit animation to first N frames (for faster preview)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=50,
        help="Milliseconds between frames in animation",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Save quality report to file",
    )

    args = parser.parse_args()

    try:
        verifier = SignatureVerifier(args.json_file)
        verifier.generate_report(output_file=args.report)

        if args.animate:
            verifier.create_animation(
                save_video=args.save_gif,
                max_frames=args.preview_frames,
                interval=args.interval,
            )

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
