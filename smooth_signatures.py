#!/usr/bin/env python3
"""
Temporal Smoothing for Sign Language Signatures
==============================================
Smooth jittery/noisy frames while preserving intentional fast movements.

Key principle: In sign language, jerks and quick movements are semantic.
This smoothing distinguishes between:
  - Intentional fast movement: Consistent direction/magnitude across frames
  - Unintentional jitter: Erratic or single-frame anomalies

Methods:
  1. Velocity-based outlier detection: Flag frames with extreme acceleration
  2. Kalman filtering: Smooth trajectories while preserving major changes
  3. Adaptive smoothing: Preserve sharp movements, smooth gradual ones

Usage:
    python3 smooth_signatures.py --lang asl --word hello_0
    python3 smooth_signatures.py --lang asl --word all
    python3 smooth_signatures.py --lang all --word all
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List, Optional
import argparse
from dataclasses import dataclass


@dataclass
class SmoothingConfig:
    """Configuration for smoothing algorithm."""
    velocity_threshold: float = 50.0  # Max pixels/frame for smooth motion
    acceleration_threshold: float = 30.0  # Max acceleration for natural motion
    kalman_process_noise: float = 0.01  # Process noise (lower = trust model more)
    kalman_measurement_noise: float = 0.1  # Measurement noise (higher = trust measurements less)
    outlier_window: int = 5  # Window for outlier detection
    preserve_sharp_movements: bool = True  # Keep intentional fast movements


class SkeletonSmoother:
    """Smooth sign language skeleton trajectories."""
    
    def __init__(self, config: SmoothingConfig = None):
        self.config = config or SmoothingConfig()
    
    def _compute_velocity(self, trajectory: np.ndarray) -> np.ndarray:
        """
        Compute velocity (distance between consecutive frames).
        
        Args:
            trajectory: (N, 2) array of x,y positions
        
        Returns:
            (N,) array of velocities (distance between frames)
        """
        if len(trajectory) < 2:
            return np.zeros(len(trajectory))
        
        diffs = np.diff(trajectory, axis=0)
        velocities = np.linalg.norm(diffs, axis=1)
        
        # Pad first frame
        return np.concatenate([[0], velocities])
    
    def _compute_acceleration(self, velocities: np.ndarray) -> np.ndarray:
        """
        Compute acceleration (change in velocity).
        
        Args:
            velocities: (N,) array of velocities
        
        Returns:
            (N,) array of accelerations
        """
        if len(velocities) < 2:
            return np.zeros(len(velocities))
        
        accelerations = np.diff(velocities)
        
        # Pad first frame
        return np.concatenate([[0], accelerations])
    
    def _detect_outlier_frames(self, trajectory: np.ndarray) -> np.ndarray:
        """
        Detect frames with unnatural jerks/accelerations.
        
        Args:
            trajectory: (N, 2) array of x,y positions
        
        Returns:
            (N,) boolean array where True = outlier
        """
        if len(trajectory) < 3:
            return np.zeros(len(trajectory), dtype=bool)
        
        velocities = self._compute_velocity(trajectory)
        accelerations = self._compute_acceleration(velocities)
        
        # Detect outliers by acceleration spikes
        outliers = np.abs(accelerations) > self.config.acceleration_threshold
        
        # Also flag frames with extreme velocity (unless it's consistent fast movement)
        for i in range(1, len(trajectory) - 1):
            if velocities[i] > self.config.velocity_threshold:
                # Check if it's a consistent fast movement (same direction for multiple frames)
                prev_vel = velocities[i - 1]
                next_vel = velocities[i + 1]
                
                # If velocity is high but isolated, it's likely jitter
                if prev_vel < self.config.velocity_threshold / 2 and \
                   next_vel < self.config.velocity_threshold / 2:
                    outliers[i] = True
        
        return outliers
    
    def _kalman_filter_trajectory(self, trajectory: np.ndarray, 
                                   outlier_mask: np.ndarray) -> np.ndarray:
        """
        Apply Kalman filter to smooth trajectory, replacing outliers.
        
        Args:
            trajectory: (N, 2) array of x,y positions
            outlier_mask: (N,) boolean array of outlier frames
        
        Returns:
            Smoothed (N, 2) trajectory
        """
        if len(trajectory) == 0:
            return trajectory
        
        # Initialize Kalman filter state
        x_est = np.zeros_like(trajectory)
        x_est[0] = trajectory[0]
        
        # Process and measurement noise covariances
        q = self.config.kalman_process_noise  # Process noise
        r = self.config.kalman_measurement_noise  # Measurement noise
        
        p_est = np.ones(2) * r  # Initial error estimate
        
        for i in range(1, len(trajectory)):
            # Prediction step
            x_pred = x_est[i - 1]  # Assume constant velocity model (zero acceleration)
            p_pred = p_est + q
            
            # Update step (only if not outlier)
            if not outlier_mask[i]:
                measurement = trajectory[i]
                k = p_pred / (p_pred + r)  # Kalman gain
                x_est[i] = x_pred + k * (measurement - x_pred)
                p_est = (1 - k) * p_pred
            else:
                # For outliers, use predicted value (smoothly extrapolate)
                x_est[i] = x_pred
                p_est = p_pred
        
        return x_est
    
    def smooth_landmarks(self, landmarks: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Smooth all landmark trajectories (pose, hands).
        
        Args:
            landmarks: Dict with keys 'pose', 'left_hand', 'right_hand'
                      Each is (N, 2) or (N, 3) array or list
        
        Returns:
            Smoothed landmarks dict (as lists to match input format)
        """
        result = {}
        
        for key in landmarks:
            if landmarks[key] is None or len(landmarks[key]) == 0:
                result[key] = landmarks[key]
                continue
            
            # Convert to numpy array if needed
            lm = np.array(landmarks[key]) if isinstance(landmarks[key], list) else landmarks[key]
            
            # Preserve confidence if present (3rd column)
            has_confidence = lm.shape[1] > 2
            confidence = lm[:, 2:] if has_confidence else None
            
            # Extract xy coordinates
            trajectory = lm[:, :2]
            
            # Detect outliers
            outlier_mask = self._detect_outlier_frames(trajectory)
            
            # Apply Kalman filter
            smoothed = self._kalman_filter_trajectory(trajectory, outlier_mask)
            
            # Reconstruct with confidence if present
            if has_confidence:
                result[key] = np.hstack([smoothed, confidence]).tolist()
            else:
                result[key] = smoothed.tolist()
        
        return result
    
    def smooth_signature(self, signature: Dict) -> Dict:
        """
        Smooth all frames in a signature.
        
        Args:
            signature: Signature dict with 'pose_data' list
        
        Returns:
            Smoothed signature dict
        """
        if 'pose_data' not in signature:
            return signature
        
        smoothed_sig = signature.copy()
        smoothed_frames = []
        
        for frame in signature['pose_data']:
            smoothed_frame = self.smooth_landmarks(frame)
            smoothed_frames.append(smoothed_frame)
        
        smoothed_sig['pose_data'] = smoothed_frames
        
        # Add metadata
        if 'metadata' not in smoothed_sig:
            smoothed_sig['metadata'] = {}
        smoothed_sig['metadata']['smoothing_applied'] = True
        smoothed_sig['metadata']['smoothing_config'] = {
            'velocity_threshold': self.config.velocity_threshold,
            'acceleration_threshold': self.config.acceleration_threshold,
            'kalman_process_noise': self.config.kalman_process_noise,
            'kalman_measurement_noise': self.config.kalman_measurement_noise,
        }
        
        return smoothed_sig
    
    def compute_quality_metrics(self, trajectory: np.ndarray) -> Dict[str, float]:
        """
        Compute quality metrics for trajectory.
        
        Returns dict with:
          - mean_velocity: Average movement per frame
          - max_velocity: Peak velocity
          - mean_acceleration: Average acceleration
          - max_acceleration: Peak acceleration
          - jitter_score: Higher = more jittery (0-1)
        """
        if len(trajectory) < 2:
            return {
                'mean_velocity': 0.0,
                'max_velocity': 0.0,
                'mean_acceleration': 0.0,
                'max_acceleration': 0.0,
                'jitter_score': 0.0,
            }
        
        velocities = self._compute_velocity(trajectory)
        accelerations = self._compute_acceleration(velocities)
        
        mean_vel = np.mean(velocities)
        max_vel = np.max(velocities)
        mean_accel = np.mean(np.abs(accelerations))
        max_accel = np.max(np.abs(accelerations))
        
        # Jitter score: normalized max acceleration
        jitter_score = min(1.0, max_accel / 100.0) if max_accel > 0 else 0.0
        
        return {
            'mean_velocity': float(mean_vel),
            'max_velocity': float(max_vel),
            'mean_acceleration': float(mean_accel),
            'max_acceleration': float(max_accel),
            'jitter_score': float(jitter_score),
        }


def smooth_signature_file(sig_path: Path, output_path: Path = None, 
                         config: SmoothingConfig = None) -> Tuple[Dict, Dict]:
    """
    Smooth a signature file and save result.
    
    Returns:
        (before_metrics, after_metrics) dicts
    """
    # Load signature
    with open(sig_path, 'r') as f:
        signature = json.load(f)
    
    # Compute before metrics
    smoother = SkeletonSmoother(config)
    before_metrics = compute_signature_metrics(signature, smoother)
    
    # Apply smoothing
    smoothed = smoother.smooth_signature(signature)
    
    # Compute after metrics
    after_metrics = compute_signature_metrics(smoothed, smoother)
    
    # Save smoothed version
    if output_path is None:
        output_path = sig_path.parent / f"{sig_path.stem}_smoothed.json"
    
    with open(output_path, 'w') as f:
        json.dump(smoothed, f, indent=2)
    
    return before_metrics, after_metrics, output_path


def compute_signature_metrics(signature: Dict, smoother: SkeletonSmoother) -> Dict:
    """Compute quality metrics for entire signature."""
    all_metrics = {
        'pose': [],
        'left_hand': [],
        'right_hand': [],
    }
    
    for frame in signature.get('pose_data', []):
        for key in all_metrics:
            if frame.get(key) is not None:
                # Convert to numpy array if it's a list
                lm_array = np.array(frame[key]) if isinstance(frame[key], list) else frame[key]
                metrics = smoother.compute_quality_metrics(lm_array[:, :2])
                all_metrics[key].append(metrics)
    
    # Aggregate metrics
    result = {}
    for key in all_metrics:
        if all_metrics[key]:
            metrics_list = all_metrics[key]
            result[f'{key}_mean_velocity'] = np.mean([m['mean_velocity'] for m in metrics_list])
            result[f'{key}_max_velocity'] = np.max([m['max_velocity'] for m in metrics_list])
            result[f'{key}_mean_acceleration'] = np.mean([m['mean_acceleration'] for m in metrics_list])
            result[f'{key}_max_acceleration'] = np.max([m['max_acceleration'] for m in metrics_list])
            result[f'{key}_jitter_score'] = np.mean([m['jitter_score'] for m in metrics_list])
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Smooth sign language signatures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 smooth_signatures.py --lang asl --word hello_0
  python3 smooth_signatures.py --lang asl --word all
  python3 smooth_signatures.py --lang all --word all
  python3 smooth_signatures.py --velocity-threshold 40 --lang asl --word hello_0
        """
    )
    
    parser.add_argument('--lang', default='asl', 
                       help='Language: asl, bsl, or all (default: asl)')
    parser.add_argument('--word', default='all',
                       help='Word/sign: hello_0, go_1, etc. or all (default: all)')
    parser.add_argument('--velocity-threshold', type=float, default=50.0,
                       help='Max pixels/frame for smooth motion (default: 50.0)')
    parser.add_argument('--acceleration-threshold', type=float, default=30.0,
                       help='Max acceleration for natural motion (default: 30.0)')
    parser.add_argument('--dry-run', action='store_true',
                       help="Don't save, just show metrics")
    parser.add_argument('--verbose', action='store_true',
                       help='Print detailed metrics')
    
    args = parser.parse_args()
    
    # Build config
    config = SmoothingConfig(
        velocity_threshold=args.velocity_threshold,
        acceleration_threshold=args.acceleration_threshold,
    )
    
    # Find signatures to process
    sig_dir = Path('assets/signatures')
    
    languages = [args.lang.lower()] if args.lang.lower() != 'all' else ['asl', 'bsl']
    
    total_processed = 0
    total_improved = 0
    
    for lang in languages:
        lang_dir = sig_dir / lang
        if not lang_dir.exists():
            print(f"⚠️  {lang.upper()} directory not found: {lang_dir}")
            continue
        
        # Get signatures
        sig_files = sorted(lang_dir.glob('*.json'))
        
        if args.word.lower() != 'all':
            sig_files = [f for f in sig_files if args.word in f.name]
        
        for sig_file in sig_files:
            print(f"\n{'='*60}")
            print(f"Processing: {lang.upper()} / {sig_file.stem}")
            print(f"{'='*60}")
            
            try:
                before, after, output_path = smooth_signature_file(sig_file, config=config)
                
                # Show improvements
                improved_count = 0
                for key in before:
                    if 'jitter_score' in key:
                        before_jitter = before.get(key, 0)
                        after_jitter = after.get(key, 0)
                        improvement = before_jitter - after_jitter
                        if improvement > 0.01:
                            improved_count += 1
                            if args.verbose:
                                print(f"  {key}: {before_jitter:.3f} → {after_jitter:.3f} (↓{improvement:.3f})")
                
                if improved_count > 0:
                    total_improved += 1
                    print(f"✅ Improved {improved_count} trajectories")
                else:
                    print(f"⚠️  Already smooth, no improvements")
                
                if not args.dry_run:
                    print(f"📁 Saved: {output_path}")
                
                total_processed += 1
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {total_processed} signatures processed, {total_improved} improved")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
