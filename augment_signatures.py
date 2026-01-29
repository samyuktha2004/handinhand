#!/usr/bin/env python3
"""
Data Augmentation for Sign Language Signatures
Addresses hand dropout issues by creating training variations.

Problem: hello_1 (74%), you_1/you_2 (39%), go_2 (42%), where_0 (42%) have hand dropouts
Root Cause: When right arm extended + hand at torso height, MediaPipe loses tracking
Solution: Create augmented variations to improve model generalization

Augmentation Techniques:
1. Rotation: ±15 degrees around shoulder midpoint (simulates camera angle)
2. Scaling: ±20% uniform scale (simulates distance from camera)
3. Mirroring: Swap left/right hands (doubles training data)
4. Noise: Gaussian jitter (simulates tracking variability)
"""

import json
import numpy as np
import copy
from pathlib import Path


class SignatureAugmentor:
    """Augment sign language signatures for improved training."""
    
    def __init__(self, output_dir: str = 'assets/signatures'):
        self.output_dir = Path(output_dir)
    
    def rotate_landmarks(self, landmarks_dict: dict, angle_deg: float) -> dict:
        """
        Rotate landmarks around shoulder midpoint.
        
        Args:
            landmarks_dict: Dict with 'pose', 'left_hand', 'right_hand', 'face'
            angle_deg: Rotation angle in degrees
        
        Returns:
            Rotated landmarks dict
        """
        rotated = copy.deepcopy(landmarks_dict)
        
        # Get shoulder center from pose (indices 0, 1 are left/right shoulders)
        pose = np.array(landmarks_dict.get('pose', []))
        if len(pose) < 2:
            return landmarks_dict  # Can't rotate without shoulders
        
        # Use only x, y (first 2 coords) for shoulder center
        shoulder_center = ((pose[0][:2] + pose[1][:2]) / 2.0)
        
        # Convert angle to radians
        angle_rad = np.radians(angle_deg)
        rot_matrix = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad)],
            [np.sin(angle_rad), np.cos(angle_rad)]
        ])
        
        # Apply rotation to each landmark group
        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if rotated[key] is not None and len(rotated[key]) > 0:
                points = np.array(rotated[key])
                
                # Rotate x, y (keep z as confidence)
                xy = points[:, :2]
                rotated_xy = (xy - shoulder_center) @ rot_matrix.T + shoulder_center
                points[:, :2] = rotated_xy
                
                rotated[key] = points.tolist()
        
        return rotated
    
    def scale_landmarks(self, landmarks_dict: dict, scale_factor: float) -> dict:
        """
        Uniformly scale landmarks around shoulder midpoint.
        
        Args:
            landmarks_dict: Dict with landmarks
            scale_factor: Scaling factor (1.0 = no change, 1.2 = 20% larger)
        
        Returns:
            Scaled landmarks dict
        """
        scaled = copy.deepcopy(landmarks_dict)
        
        # Get shoulder center
        pose = np.array(landmarks_dict.get('pose', []))
        if len(pose) < 2:
            return landmarks_dict
        
        # Use only x, y (first 2 coords) for shoulder center
        shoulder_center = ((pose[0][:2] + pose[1][:2]) / 2.0)
        
        # Apply scaling to each landmark group
        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if scaled[key] is not None and len(scaled[key]) > 0:
                points = np.array(scaled[key])
                
                # Scale around shoulder center
                xy = points[:, :2]
                scaled_xy = (xy - shoulder_center) * scale_factor + shoulder_center
                points[:, :2] = scaled_xy
                
                scaled[key] = points.tolist()
        
        return scaled
    
    def mirror_landmarks(self, landmarks_dict: dict) -> dict:
        """
        Mirror left/right hands (horizontal flip around shoulder midpoint).
        
        Args:
            landmarks_dict: Dict with landmarks
        
        Returns:
            Mirrored landmarks dict
        """
        mirrored = copy.deepcopy(landmarks_dict)
        
        # Get shoulder center X
        pose = np.array(landmarks_dict.get('pose', []))
        if len(pose) < 2:
            return landmarks_dict
        
        shoulder_center_x = (pose[0][0] + pose[1][0]) / 2.0
        
        # Mirror each component
        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if mirrored[key] is not None and len(mirrored[key]) > 0:
                points = np.array(mirrored[key])
                
                # Mirror x around shoulder center
                points[:, 0] = 2 * shoulder_center_x - points[:, 0]
                
                mirrored[key] = points.tolist()
        
        # Swap left and right hands
        mirrored['left_hand'], mirrored['right_hand'] = \
            mirrored['right_hand'], mirrored['left_hand']
        
        return mirrored
    
    def add_noise(self, landmarks_dict: dict, noise_level: float = 0.01) -> dict:
        """
        Add Gaussian noise to simulate tracking jitter.
        
        Args:
            landmarks_dict: Dict with landmarks
            noise_level: Standard deviation of noise
        
        Returns:
            Noisy landmarks dict
        """
        noisy = copy.deepcopy(landmarks_dict)
        
        for key in ['pose', 'left_hand', 'right_hand', 'face']:
            if noisy[key] is not None and len(noisy[key]) > 0:
                points = np.array(noisy[key])
                noise = np.random.normal(0, noise_level, points.shape)
                points = points + noise
                noisy[key] = points.tolist()
        
        return noisy
    
    def augment_signature(self, sig_dict: dict, num_variations: int = 2) -> dict:
        """
        Generate augmented versions of a signature.
        
        Args:
            sig_dict: Signature JSON dict
            num_variations: Number of variations per technique
        
        Returns:
            Dict of augmented signatures {'technique_n': augmented_sig}
        """
        augmented = {}
        
        pose_data = sig_dict.get('pose_data', [])
        if not pose_data:
            return {}
        
        # For each frame, generate augmented versions
        augmented_frames = [[] for _ in range(num_variations)]
        
        for frame_idx, frame in enumerate(pose_data):
            # Original frame
            original_frame = copy.deepcopy(frame)
            
            # Generate variations
            for var_idx in range(num_variations):
                # Rotation: random between -15 and 15 degrees
                angle = np.random.uniform(-15, 15)
                rotated = self.rotate_landmarks(original_frame, angle)
                
                # Scaling: random between 0.85 and 1.15
                scale = np.random.uniform(0.85, 1.15)
                scaled = self.scale_landmarks(rotated, scale)
                
                # Noise: add slight jitter
                noisy = self.add_noise(scaled, noise_level=0.01)
                
                augmented_frames[var_idx].append(noisy)
        
        # Create augmented signature dicts
        for var_idx, frames in enumerate(augmented_frames):
            aug_sig = copy.deepcopy(sig_dict)
            aug_sig['pose_data'] = frames
            augmented[f'variation_{var_idx+1}'] = aug_sig
        
        # Also create mirrored version
        mirrored_frames = []
        for frame in pose_data:
            mirrored_frames.append(self.mirror_landmarks(frame))
        
        aug_sig_mirrored = copy.deepcopy(sig_dict)
        aug_sig_mirrored['pose_data'] = mirrored_frames
        augmented['mirrored'] = aug_sig_mirrored
        
        return augmented
    
    def augment_and_save(self, sig_path: str, lang: str, num_variations: int = 2):
        """
        Load signature, augment it, and save variations.
        
        Args:
            sig_path: Path to signature JSON file
            lang: Language ('asl' or 'bsl')
            num_variations: Number of random variations to generate
        """
        sig_name = Path(sig_path).stem
        
        print(f"\n📊 Augmenting {sig_name}...")
        
        # Load
        with open(sig_path, 'r') as f:
            sig_dict = json.load(f)
        
        # Augment
        augmented = self.augment_signature(sig_dict, num_variations)
        
        # Save
        for aug_name, aug_sig in augmented.items():
            output_name = f"{sig_name}_{aug_name}.json"
            output_path = self.output_dir / lang / output_name
            
            # Validate frame structure before saving
            if 'pose_data' in aug_sig:
                for frame in aug_sig['pose_data']:
                    # Ensure all landmark groups exist and are lists
                    for key in ['pose', 'left_hand', 'right_hand', 'face']:
                        if key not in frame:
                            frame[key] = []
                        elif frame[key] is None:
                            frame[key] = []
                        # Convert any numpy arrays to lists
                        if isinstance(frame[key], np.ndarray):
                            frame[key] = frame[key].tolist()
            
            with open(output_path, 'w') as f:
                json.dump(aug_sig, f, indent=2)
            
            print(f"  ✅ Saved: {output_name}")
        
        return len(augmented)


def main():
    """Main augmentation workflow."""
    
    augmentor = SignatureAugmentor()
    
    # Problematic signatures (with high dropout rates)
    problem_signatures = [
        'assets/signatures/asl/hello_1.json',      # 74% dropouts
        'assets/signatures/asl/you_1.json',        # 39% dropouts
        'assets/signatures/asl/you_2.json',        # 39% dropouts
        'assets/signatures/asl/go_2.json',         # 42% dropouts
        'assets/signatures/asl/where_0.json',      # 42% dropouts
    ]
    
    print("="*70)
    print("DATA AUGMENTATION FOR HAND DROPOUT MITIGATION")
    print("="*70)
    print("\nAugmenting problematic signatures...")
    print("Techniques: Rotation (±15°), Scaling (0.85-1.15x), Mirroring, Noise")
    print()
    
    total_generated = 0
    for sig_path in problem_signatures:
        if Path(sig_path).exists():
            count = augmentor.augment_and_save(sig_path, 'asl', num_variations=2)
            total_generated += count
        else:
            print(f"  ⚠️  Not found: {sig_path}")
    
    print("\n" + "="*70)
    print(f"✅ Generated {total_generated} augmented signature variations")
    print("="*70)
    
    print("\n📝 NEXT STEPS:")
    print("1. Regenerate embeddings: python generate_embeddings.py")
    print("2. Test improvement: python test_recognition_quality.py")
    print("3. Check specific metrics:")
    print("   - hello recognition should improve (was 0.7148)")
    print("   - you recognition should improve (was 0.7763)")
    print("   - where recognition should improve (was 0.5931)")
    print("\n💡 If improvement < 5%:")
    print("   - Increase num_variations (try 4-5)")
    print("   - Increase rotation angle (try ±30°)")
    print("   - Increase noise level (try 0.02-0.03)")
    print("   - Re-film with better camera angles")


if __name__ == '__main__':
    main()
