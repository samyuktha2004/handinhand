#!/usr/bin/env python3
"""
Enhanced Real-Time Sign Language Recognition Engine with UI Dashboard

MVP Features:
1. Real-time confidence bars (4 concepts)
2. Ghost skeleton overlay (golden signature alignment)
3. Cooldown timer (prevent double-counting)
4. Socket.io integration (future avatar connection)
5. Recognition verification (Tier 4 validation)

Usage:
    # Standard (with dashboard)
    python3 recognition_engine_ui.py

    # With debug overlay
    python3 recognition_engine_ui.py --debug

    # With Socket.io emission
    python3 recognition_engine_ui.py --socket-url http://localhost:5000

    # With custom cooldown
    python3 recognition_engine_ui.py --cooldown 3000

Command Reference:
    ESC or q = quit
    r = reset landmark window
"""

import cv2
import numpy as np
import json
import mediapipe as mp
import os
import sys
import time
import threading
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy.spatial.distance import cosine
from collections import defaultdict

# Import registry loader for new multi-language structure
from utils.registry_loader import RegistryLoader

# Socket.io optional import
try:
    import socketio
    HAS_SOCKETIO = True
except ImportError:
    HAS_SOCKETIO = False
    print("⚠️  Socket.io not installed. Install with: pip install python-socketio")

# ============================================================================
# CONFIGURATION
# ============================================================================

TRANSLATION_REGISTRY = "translation_map.json"
EMBEDDINGS_DIR = "assets/embeddings"
SIGNATURES_DIR = "assets/signatures"

# Recognition parameters
COSINE_SIM_THRESHOLD = 0.80
TIER_4_GAP_THRESHOLD = 0.15
WINDOW_SIZE = 30
CONFIDENCE_DISPLAY_THRESHOLD = 0.50
DEFAULT_COOLDOWN_MS = 2000  # Prevent double-counting

# Landmark indices
SHOULDER_LEFT = 11
SHOULDER_RIGHT = 12

# UI Colors
COLOR_LIVE = (0, 255, 0)           # Green: live skeleton
COLOR_GHOST = (100, 100, 100)      # Grey: golden signature
COLOR_BAR_LOW = (0, 0, 255)        # Red: low confidence
COLOR_BAR_MED = (0, 165, 255)      # Orange: medium
COLOR_BAR_HIGH = (0, 255, 0)       # Green: high
COLOR_MATCH = (0, 255, 255)        # Cyan: matched
COLOR_TEXT = (255, 255, 255)       # White: text


# ============================================================================
# TEMPORAL SMOOTHING FILTER (Hysteresis for Stable Recognition)
# ============================================================================

class TemporalFilter:
    """
    Hysteresis filter for stable recognition.
    Requires N consecutive frames above threshold before confirming match.
    
    Problem: Webcam jitter causes frame-to-frame variation (0.81 → 0.79 → 0.81)
    Solution: Only confirm when same concept stays >0.80 for 5 consecutive frames (~167ms @ 30fps)
    """
    
    def __init__(self, min_frames: int = 5, threshold: float = 0.80):
        """
        Args:
            min_frames: Frames needed to confirm (5 frames @ 30fps = 167ms)
            threshold: Similarity threshold for counting
        """
        self.min_frames = min_frames
        self.threshold = threshold
        self.frame_count = defaultdict(int)
        self.last_concept = None
        self.confirmed_concept = None
    
    def update(self, best_concept: str, similarity: float) -> Optional[str]:
        """
        Process recognition result with temporal smoothing.
        
        Returns:
            Confirmed concept if >= min_frames above threshold, else None
        """
        if similarity >= self.threshold:
            # Same concept as last frame: increment counter
            if best_concept == self.last_concept:
                self.frame_count[best_concept] += 1
            else:
                # Concept changed: reset counters
                self.frame_count = defaultdict(int)
                self.frame_count[best_concept] = 1
            
            # Check if confirmed
            if self.frame_count[best_concept] >= self.min_frames:
                self.confirmed_concept = best_concept
                return best_concept
        else:
            # Below threshold: reset
            if self.last_concept:
                self.frame_count[self.last_concept] = 0
            self.confirmed_concept = None
        
        self.last_concept = best_concept
        return None
    
    def reset(self):
        """Reset filter state."""
        self.frame_count = defaultdict(int)
        self.last_concept = None
        self.confirmed_concept = None


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class RecognitionResult:
    """Encapsulates recognition output."""
    concept: Optional[str]
    similarity_score: float
    confidence_level: str
    verification_status: str
    all_scores: Dict[str, float]
    bsl_target_file: Optional[str]
    gap_to_second: float
    frame_window_complete: bool


# ============================================================================
# RECOGNITION ENGINE WITH UI
# ============================================================================

class RecognitionEngineUI:
    """Real-time sign recognition with interactive dashboard UI."""

    def __init__(
        self,
        registry_path: str = TRANSLATION_REGISTRY,
        debug: bool = False,
        socket_url: Optional[str] = None,
        cooldown_ms: int = DEFAULT_COOLDOWN_MS,
    ):
        """
        Initialize engine.

        Args:
            registry_path: Path to translation_map.json
            debug: Enable debug visualization
            socket_url: Socket.io server URL (e.g., http://localhost:5000)
            cooldown_ms: Milliseconds to wait after match before next emission
        """
        self.debug = debug
        self.registry_path = registry_path
        self.loader = RegistryLoader()
        self.concept_registry = self.loader.get_concept_registry()
        self.asl_registry = self.loader.get_language_registry('asl')
        self.bsl_registry = self.loader.get_language_registry('bsl')
        self.registry = {}  # Legacy compatibility
        self.embeddings = {}
        self.concept_names = []
        self.cooldown_ms = cooldown_ms

        # Socket.io setup
        self.socket_url = socket_url
        self.sio = None
        self.socket_connected = False
        self._setup_socket_io()

        # Temporal smoothing filter (5 frames @ 0.80+)
        self.temporal_filter = TemporalFilter(min_frames=5, threshold=0.80)

        # Cooldown state machine
        self.last_match_time = 0
        self.last_matched_concept = None

        # MediaPipe setup
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3,
        )

        # Sliding window
        self.landmark_window = []
        self.golden_signatures = {}  # Cached golden poses

        # Load data
        self._load_embeddings()
        self._load_golden_signatures()

        print(f"✅ Engine initialized")
        print(f"   Concepts: {len(self.concept_names)}")
        print(f"   Debug: {'ON' if self.debug else 'OFF'}")
        print(
            f"   Socket.io: {'ENABLED' if socket_url and HAS_SOCKETIO else 'DISABLED'}"
        )
        print(f"   Cooldown: {cooldown_ms}ms")

    def _setup_socket_io(self):
        """Setup Socket.io client (optional)."""
        if not self.socket_url or not HAS_SOCKETIO:
            return

        try:
            self.sio = socketio.Client(reconnection=True, reconnection_attempts=5)

            @self.sio.on("connect")
            def on_connect():
                self.socket_connected = True
                print(f"✅ Socket.io connected to {self.socket_url}")

            @self.sio.on("disconnect")
            def on_disconnect():
                self.socket_connected = False
                print(f"⚠️  Socket.io disconnected")

            # Connect in background thread
            threading.Thread(
                target=self._connect_socket, daemon=True
            ).start()
        except Exception as e:
            print(f"❌ Socket.io setup failed: {e}")

    def _connect_socket(self):
        """Connect to Socket.io server (background thread)."""
        try:
            self.sio.connect(self.socket_url)
        except Exception as e:
            print(f"⚠️  Failed to connect Socket.io: {e}")

    def _load_embeddings(self):
        """Load ASL embeddings from ASL registry."""
        for concept_id, concept_data in self.asl_registry.items():
            if concept_id.startswith('_'):
                continue
                
            emb_file = concept_data.get("embedding_mean_file")
            if not emb_file:
                continue

            try:
                embedding = np.load(emb_file)
                concept_name = concept_data.get("concept_name")
                self.embeddings[concept_name] = embedding
                self.concept_names.append(concept_name)
            except FileNotFoundError:
                print(f"⚠️  Embedding not found: {emb_file}")

    def _load_golden_signatures(self):
        """Preload golden signature poses for ghost skeleton from ASL registry."""
        for concept_id, concept_data in self.asl_registry.items():
            if concept_id.startswith('_'):
                continue
            
            signatures = concept_data.get("signatures", [])
            if not signatures:
                continue

            # Use first signature as golden reference
            first_sig = signatures[0]
            sig_file = first_sig.get("signature_file")
            
            if not sig_file:
                continue

            try:
                with open(sig_file) as f:
                    data = json.load(f)
                    # Extract first frame's pose (has highest detail)
                    if isinstance(data, dict) and "frames" in data:
                        concept_name = concept_data.get("concept_name")
                        self.golden_signatures[concept_name] = data["frames"][0]
                    elif isinstance(data, list) and len(data) > 0:
                        concept_name = concept_data.get("concept_name")
                        self.golden_signatures[concept_name] = data[0]
            except Exception:
                pass  # Silent fail for missing signatures

    def _normalize_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """Body-centric normalization (subtract shoulder center)."""
        shoulder_center = (landmarks[SHOULDER_LEFT] + landmarks[SHOULDER_RIGHT]) / 2
        return landmarks - shoulder_center

    def _extract_frame_features(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Extract 52 landmarks from frame."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.holistic.process(rgb)

        if not results.pose_landmarks:
            return None

        landmarks = []

        # Pose (6 points)
        if results.pose_landmarks:
            for lm in results.pose_landmarks.landmark[:6]:
                landmarks.append([lm.x, lm.y, lm.z if hasattr(lm, "z") else 0.0])

        # Left hand (21 points)
        if results.left_hand_landmarks:
            for lm in results.left_hand_landmarks.landmark:
                landmarks.append([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([[0, 0, 0]] * 21)

        # Right hand (21 points)
        if results.right_hand_landmarks:
            for lm in results.right_hand_landmarks.landmark:
                landmarks.append([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([[0, 0, 0]] * 21)

        # Face (4 points: nose, left eye, right eye, mouth)
        if results.face_landmarks:
            for idx in [0, 33, 263, 13]:
                lm = results.face_landmarks.landmark[idx]
                landmarks.append([lm.x, lm.y, lm.z])
        else:
            landmarks.extend([[0, 0, 0]] * 4)

        landmarks = np.array(landmarks)
        return self._normalize_landmarks(landmarks)

    def _compute_live_embedding(self) -> Optional[np.ndarray]:
        """Compute embedding from landmark window."""
        if len(self.landmark_window) < WINDOW_SIZE:
            return None

        window_stack = np.array(self.landmark_window[-WINDOW_SIZE:])
        window_flat = window_stack.reshape(WINDOW_SIZE, -1)
        embedding = np.mean(window_flat, axis=0)

        if len(embedding) < 512:
            embedding = np.pad(embedding, (0, 512 - len(embedding)))

        return embedding[:512]

    def recognize(self, frame: np.ndarray) -> RecognitionResult:
        """Main recognition method."""
        landmarks = self._extract_frame_features(frame)
        if landmarks is None:
            return RecognitionResult(
                concept=None,
                similarity_score=0.0,
                confidence_level="low",
                verification_status="low_confidence",
                all_scores={},
                bsl_target_file=None,
                gap_to_second=0.0,
                frame_window_complete=False,
            )

        self.landmark_window.append(landmarks)
        if len(self.landmark_window) > WINDOW_SIZE:
            self.landmark_window.pop(0)

        if len(self.landmark_window) < WINDOW_SIZE:
            return RecognitionResult(
                concept=None,
                similarity_score=0.0,
                confidence_level="low",
                verification_status="low_confidence",
                all_scores={},
                bsl_target_file=None,
                gap_to_second=0.0,
                frame_window_complete=False,
            )

        live_embedding = self._compute_live_embedding()

        # Score all concepts
        scores = {}
        for concept in self.concept_names:
            stored_embedding = self.embeddings[concept]
            cosine_dist = cosine(live_embedding, stored_embedding)
            cosine_sim = 1 - cosine_dist
            scores[concept] = cosine_sim

        # Tier 4 validation
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_concept, best_score = sorted_scores[0]
        second_concept, second_score = sorted_scores[1] if len(sorted_scores) > 1 else (None, 0.0)
        gap_to_second = best_score - second_score

        # PHASE 3: Apply temporal smoothing filter (hysteresis for stable recognition)
        confirmed_concept = self.temporal_filter.update(best_concept, best_score)

        # Confidence level
        if best_score >= 0.90:
            confidence_level = "high"
        elif best_score >= 0.80:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Verification status (now with temporal smoothing)
        if confirmed_concept is not None:
            # Concept confirmed by temporal filter
            verification_status = "verified"
        elif best_score >= COSINE_SIM_THRESHOLD and gap_to_second >= TIER_4_GAP_THRESHOLD:
            # High score but not yet confirmed
            verification_status = "pending_confirmation"
        elif best_score < COSINE_SIM_THRESHOLD:
            verification_status = "low_confidence"
        else:
            verification_status = "cross_concept_noise"

        # BSL target
        bsl_target_file = None
        if confirmation_concept := (confirmed_concept or best_concept):
            concept_data = self.registry.get(confirmation_concept, {})
            bsl_target_file = concept_data.get("bsl_target_file")

        return RecognitionResult(
            concept=confirmed_concept or best_concept,  # Use confirmed concept if available
            similarity_score=best_score,
            confidence_level=confidence_level,
            verification_status=verification_status,
            all_scores=scores,
            bsl_target_file=bsl_target_file,
            gap_to_second=gap_to_second,
            frame_window_complete=True,
        )

    def _draw_winner_display(self, frame: np.ndarray, confirmed_concept: str,
                              bsl_target_path: Optional[str] = None) -> np.ndarray:
        """
        Draw large green text for confirmed match (PHASE 3).
        
        Shows:
        1. Large "✓ CONCEPT" in bright green
        2. Optional: "→ bsl_target_name" in cyan below
        """
        if not confirmed_concept:
            return frame
        
        h, w, _ = frame.shape
        
        # Large GREEN centered text
        font = cv2.FONT_HERSHEY_BOLD
        font_scale = 3.0
        thickness = 5
        color_green = (0, 255, 0)        # Bright green for winner
        color_cyan = (0, 255, 255)       # Cyan for BSL target
        
        # Main winner text
        text = f"✓ {confirmed_concept}"
        text_size, baseline = cv2.getTextSize(text, font, font_scale, thickness)
        x = (w - text_size[0]) // 2
        y = (h // 2) - 50
        
        # Draw winner text with semi-transparent background box
        box_margin = 20
        cv2.rectangle(frame, 
                     (x - box_margin, y - text_size[1] - box_margin),
                     (x + text_size[0] + box_margin, y + baseline + box_margin),
                     (0, 100, 0),    # Dark green background
                     -1)
        cv2.rectangle(frame,
                     (x - box_margin, y - text_size[1] - box_margin),
                     (x + text_size[0] + box_margin, y + baseline + box_margin),
                     color_green,    # Green border
                     2)
        
        # Draw winner text
        cv2.putText(frame, text, (x, y), font, font_scale, color_green, thickness)
        
        # Optional: BSL target name below
        if bsl_target_path:
            bsl_name = Path(bsl_target_path).stem  # Get filename without extension
            target_text = f"→ {bsl_name}"
            target_size, _ = cv2.getTextSize(target_text, cv2.FONT_HERSHEY_SIMPLEX, 1.8, 2)
            target_x = (w - target_size[0]) // 2
            cv2.putText(frame, target_text, (target_x, y + 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.8, color_cyan, 2)
        
        return frame

    def _draw_dashboard(self, frame: np.ndarray, result: RecognitionResult) -> np.ndarray:
        """Draw interactive dashboard on frame."""
        h, w, _ = frame.shape
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 1

        # Bar dimensions
        bar_y_start = 30
        bar_height = 20
        bar_spacing = 10
        bar_width = 200
        bar_x_left = 20

        # Title
        cv2.putText(
            frame,
            "CONFIDENCE SCORES",
            (bar_x_left, bar_y_start - 10),
            font,
            0.7,
            COLOR_TEXT,
            2,
        )

        # Draw bars for each concept
        for idx, concept in enumerate(self.concept_names):
            score = result.all_scores.get(concept, 0.0)
            y_pos = bar_y_start + idx * (bar_height + bar_spacing)

            # Bar background (dark)
            cv2.rectangle(frame, (bar_x_left, y_pos), (bar_x_left + bar_width, y_pos + bar_height), (30, 30, 30), -1)

            # Bar fill (colored based on score)
            fill_width = int(bar_width * score)
            
            # PHASE 3: Enhanced color coding
            # Confirmed concept gets bright green
            if concept == result.concept and result.verification_status == "verified":
                bar_color = (0, 255, 0)  # Bright GREEN for confirmed
            elif score >= 0.90:
                bar_color = COLOR_BAR_HIGH  # Green for high score
            elif score >= 0.80:
                bar_color = (0, 200, 100)  # Dark green for medium-high
            elif score >= 0.50:
                bar_color = COLOR_BAR_MED  # Orange for medium
            elif score >= 0.20:
                bar_color = (0, 100, 200)  # Light orange for low
            else:
                bar_color = COLOR_BAR_LOW  # Red for very low

            cv2.rectangle(frame, (bar_x_left, y_pos), (bar_x_left + fill_width, y_pos + bar_height), bar_color, -1)

            # Threshold line (0.80) - shows confirmation threshold
            threshold_x = bar_x_left + int(bar_width * COSINE_SIM_THRESHOLD)
            cv2.line(frame, (threshold_x, y_pos), (threshold_x, y_pos + bar_height), (255, 255, 255), 1)

            # Border (brighter for confirmed)
            if concept == result.concept and result.verification_status == "verified":
                border_color = (0, 255, 0)  # GREEN border for confirmed
                border_thickness = 2
            else:
                border_color = COLOR_TEXT
                border_thickness = 1
            cv2.rectangle(frame, (bar_x_left, y_pos), (bar_x_left + bar_width, y_pos + bar_height), 
                         border_color, border_thickness)

            # Label + score (brighter for confirmed)
            label_text = f"{concept[:8]:8s} {score:.2f}"
            if concept == result.concept and result.verification_status == "verified":
                label_color = (0, 255, 0)  # GREEN text for confirmed
                label_thickness = 2
            else:
                label_color = COLOR_TEXT
                label_thickness = thickness
            cv2.putText(frame, label_text, (bar_x_left + bar_width + 10, y_pos + 15), 
                       font, font_scale, label_color, label_thickness)

        # Window progress indicator
        window_pct = len(self.landmark_window) / WINDOW_SIZE * 100
        cv2.putText(
            frame,
            f"Window: {window_pct:.0f}%",
            (w - 180, 30),
            font,
            0.5,
            COLOR_TEXT,
            1,
        )

        # Cooldown timer
        if result.frame_window_complete:
            now_ms = time.time() * 1000
            cooldown_remaining_ms = max(0, self.cooldown_ms - (now_ms - self.last_match_time))
            if result.verification_status == "verified" and cooldown_remaining_ms > 0:
                timer_text = f"Cooldown: {cooldown_remaining_ms / 1000:.1f}s"
                cv2.putText(
                    frame,
                    timer_text,
                    (w - 180, 60),
                    font,
                    0.5,
                    COLOR_BAR_MED,
                    1,
                )

        # Status badge (bottom-left)
        if result.frame_window_complete:
            if result.verification_status == "verified":
                status_color = COLOR_BAR_HIGH
                status_text = f"✅ VERIFIED: {result.concept} ({result.similarity_score:.3f})"
            elif result.verification_status == "low_confidence":
                status_color = COLOR_BAR_LOW
                status_text = f"❌ LOW CONFIDENCE ({result.similarity_score:.3f})"
            else:
                status_color = COLOR_BAR_MED
                status_text = f"⚠️  AMBIGUOUS ({result.similarity_score:.3f})"

            # Status background box
            text_size = cv2.getTextSize(status_text, font, 0.6, 2)[0]
            box_coords = (10, h - 30, 20 + text_size[0], h - 10)
            cv2.rectangle(frame, box_coords[:2], box_coords[2:], status_color, -1)
            cv2.rectangle(frame, box_coords[:2], box_coords[2:], COLOR_TEXT, 1)

            cv2.putText(frame, status_text, (15, h - 15), font, 0.6, COLOR_TEXT, 2)

        return frame

    def _draw_ghost_skeleton(self, frame: np.ndarray, result: RecognitionResult) -> np.ndarray:
        """Draw golden signature skeleton overlay (debug mode)."""
        if not self.debug or not result.concept:
            return frame

        golden_pose = self.golden_signatures.get(result.concept)
        if not golden_pose:
            return frame

        h, w, _ = frame.shape

        try:
            # Extract landmarks from golden pose
            pose_landmarks = golden_pose.get("pose_landmarks", [])
            if not pose_landmarks:
                return frame

            # Convert from normalized to pixel coordinates
            pose_pixels = []
            for lm in pose_landmarks[:6]:  # Only pose
                x_pixel = int(lm["x"] * w)
                y_pixel = int(lm["y"] * h)
                pose_pixels.append((x_pixel, y_pixel))

            # Draw ghost skeleton (faint grey)
            # Connect shoulders -> hips
            if len(pose_pixels) >= 4:
                connections = [(0, 1), (0, 2), (1, 3), (2, 4)]  # Simplified pose connections
                for start_idx, end_idx in connections:
                    if start_idx < len(pose_pixels) and end_idx < len(pose_pixels):
                        start = pose_pixels[start_idx]
                        end = pose_pixels[end_idx]
                        cv2.line(frame, start, end, COLOR_GHOST, 2)

            # Draw joints as small circles
            for pixel in pose_pixels:
                cv2.circle(frame, pixel, 3, COLOR_GHOST, -1)

        except Exception:
            pass  # Silent fail if ghost skeleton data malformed

        return frame

    def _emit_socket(self, concept_id: str, score: float):
        """Emit recognition result via Socket.io.
        
        PHASE 3: Enhanced emission with translation_event structure
        
        Emits two complementary events:
        1. 'sign_recognized' - Legacy (backward compatible)
        2. 'translation_event' - New (Phase 3, with full metadata)
        """
        if not self.socket_url or not self.sio or not self.socket_connected:
            return

        try:
            # Get concept metadata
            concept_data = self.concept_registry.get(concept_id, {})
            concept_name = concept_data.get("concept_name", concept_id)
            bsl_target_path = concept_data.get("bsl_target_file", "")
            
            # Legacy event (backward compatible)
            legacy_payload = {
                "concept": concept_id,
                "score": float(score),
                "timestamp": time.time(),
            }
            self.sio.emit("sign_recognized", legacy_payload)
            
            # Phase 3: translation_event (full metadata)
            translation_payload = {
                "concept_id": concept_id,
                "concept_name": concept_name,
                "bsl_target_path": str(bsl_target_path) if bsl_target_path else None,
                "similarity_score": float(score),
                "timestamp": time.time(),
                "source": "recognition_engine_ui",
                "verification_status": "verified"
            }
            self.sio.emit("translation_event", translation_payload)
            
            if self.debug:
                print(f"📡 Emitted translation_event: {concept_name} → {Path(bsl_target_path).name if bsl_target_path else 'N/A'}")
        except Exception as e:
            print(f"⚠️  Socket.io emit failed: {e}")

    def run(self, camera_id: int = 0, delay_ms: int = 1):
        """Main recognition loop."""
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Failed to open camera {camera_id}")
            return

        print(f"🎥 Camera opened. Press ESC or 'q' to quit, 'r' to reset window")
        print(f"🔄 Temporal smoothing: {self.temporal_filter.min_frames} frames @ {self.temporal_filter.threshold:.2f}+ threshold")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)  # Selfie view

                # Recognize
                result = self.recognize(frame)

                # Draw dashboard
                frame = self._draw_dashboard(frame, result)

                # PHASE 3: Draw winner display if verified
                if result.verification_status == "verified":
                    frame = self._draw_winner_display(frame, result.concept, result.bsl_target_file)

                # Draw ghost skeleton (if debug + verified)
                if self.debug:
                    frame = self._draw_ghost_skeleton(frame, result)

                # Handle verification + cooldown + Socket.io
                if result.frame_window_complete and result.verification_status == "verified":
                    now_ms = time.time() * 1000
                    if now_ms - self.last_match_time > self.cooldown_ms:
                        # Emit and reset cooldown
                        self._emit_socket(result.concept, result.similarity_score)
                        self.last_match_time = now_ms
                        self.last_matched_concept = result.concept

                # Display
                cv2.imshow("Sign Language Recognition - MVP Dashboard", frame)

                # Keyboard input
                key = cv2.waitKey(delay_ms) & 0xFF
                if key == 27 or key == ord("q"):  # ESC or q
                    print("\n👋 Exiting...")
                    break
                elif key == ord("r"):  # r
                    self.landmark_window = []
                    self.temporal_filter.reset()
                    print("🔄 Window and temporal filter reset")

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.holistic.close()
            if self.sio:
                try:
                    self.sio.disconnect()
                except Exception:
                    pass


# ============================================================================
# MAIN
# ============================================================================


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Real-time sign recognition with interactive dashboard"
    )
    parser.add_argument("--debug", action="store_true", help="Enable ghost skeleton overlay")
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID")
    parser.add_argument("--delay", type=int, default=1, help="Frame delay in ms")
    parser.add_argument("--socket-url", type=str, help="Socket.io server URL (e.g., http://localhost:5000)")
    parser.add_argument("--cooldown", type=int, default=DEFAULT_COOLDOWN_MS, help="Cooldown after match (ms)")

    args = parser.parse_args()

    try:
        engine = RecognitionEngineUI(
            debug=args.debug,
            socket_url=args.socket_url,
            cooldown_ms=args.cooldown,
        )
        engine.run(camera_id=args.camera, delay_ms=args.delay)
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
