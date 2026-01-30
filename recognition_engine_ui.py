#!/usr/bin/env python3
"""
Enhanced Real-Time Sign Language Recognition Engine with UI Dashboard

MVP Features:
1. Real-time confidence bars (4 concepts)
2. Ghost skeleton overlay (golden signature alignment)
3. Cooldown timer (prevent double-counting)
4. Socket.io integration (future avatar connection)
5. Recognition verification with temporal smoothing

Usage:
    python3 recognition_engine_ui.py
    python3 recognition_engine_ui.py --debug
    python3 recognition_engine_ui.py --socket-url http://localhost:5000
    python3 recognition_engine_ui.py --cooldown 3000
"""

import cv2
import numpy as np
import json
import time
import sys
import threading
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass
from scipy.spatial.distance import cosine
from collections import defaultdict

from recognition_base import (
    BaseRecognitionEngine,
    WINDOW_SIZE,
    COSINE_SIM_THRESHOLD,
)

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
TIER_4_GAP_THRESHOLD = 0.15
DEFAULT_COOLDOWN_MS = 2000

# UI Colors
COLOR_LIVE = (0, 255, 0)
COLOR_GHOST = (100, 100, 100)
COLOR_BAR_LOW = (0, 0, 255)
COLOR_BAR_MED = (0, 165, 255)
COLOR_BAR_HIGH = (0, 255, 0)
COLOR_MATCH = (0, 255, 255)
COLOR_TEXT = (255, 255, 255)


# ============================================================================
# TEMPORAL SMOOTHING FILTER
# ============================================================================

class TemporalFilter:
    """Hysteresis filter: requires N consecutive frames above threshold."""
    
    def __init__(self, min_frames: int = 5, threshold: float = 0.80):
        self.min_frames = min_frames
        self.threshold = threshold
        self.frame_count = defaultdict(int)
        self.last_concept = None
        self.confirmed_concept = None
    
    def update(self, best_concept: str, similarity: float) -> Optional[str]:
        """Return confirmed concept if threshold met, else None."""
        if similarity >= self.threshold:
            if best_concept == self.last_concept:
                self.frame_count[best_concept] += 1
            else:
                self.frame_count = defaultdict(int)
                self.frame_count[best_concept] = 1
            
            if self.frame_count[best_concept] >= self.min_frames:
                self.confirmed_concept = best_concept
                return best_concept
        else:
            if self.last_concept:
                self.frame_count[self.last_concept] = 0
            self.confirmed_concept = None
        
        self.last_concept = best_concept
        return None
    
    def reset(self):
        self.frame_count = defaultdict(int)
        self.last_concept = None
        self.confirmed_concept = None


# ============================================================================
# UI RESULT DATA CLASS
# ============================================================================

@dataclass
class UIRecognitionResult:
    """Recognition result with UI-specific fields."""
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

class RecognitionEngineUI(BaseRecognitionEngine):
    """Real-time sign recognition with interactive dashboard UI."""

    def __init__(
        self,
        registry_path: str = "translation_map.json",
        debug: bool = False,
        socket_url: Optional[str] = None,
        cooldown_ms: int = DEFAULT_COOLDOWN_MS,
    ):
        super().__init__(language='asl')
        self.debug = debug
        self.registry_path = registry_path
        self.cooldown_ms = cooldown_ms

        # Concept names from embeddings
        self.concept_names = list(self.embeddings.keys())

        # Socket.io setup
        self.socket_url = socket_url
        self.sio = None
        self.socket_connected = False
        self._setup_socket_io()

        # Temporal smoothing filter
        self.temporal_filter = TemporalFilter(min_frames=5, threshold=0.80)

        # Cooldown state
        self.last_match_time = 0
        self.last_matched_concept = None

        # Golden signatures for ghost skeleton
        self.golden_signatures = {}
        self._load_golden_signatures()

        print(f"✅ Engine initialized")
        print(f"   Concepts: {len(self.concept_names)}")
        print(f"   Debug: {'ON' if self.debug else 'OFF'}")
        print(f"   Socket.io: {'ENABLED' if socket_url and HAS_SOCKETIO else 'DISABLED'}")
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

            threading.Thread(target=self._connect_socket, daemon=True).start()
        except Exception as e:
            print(f"❌ Socket.io setup failed: {e}")

    def _connect_socket(self):
        try:
            self.sio.connect(self.socket_url)
        except Exception as e:
            print(f"⚠️  Failed to connect Socket.io: {e}")

    def _load_golden_signatures(self):
        """Preload golden signature poses for ghost skeleton."""
        for concept_id, concept_data in self.language_registry.items():
            if concept_id.startswith('_'):
                continue
            
            signatures = concept_data.get("signatures", [])
            if not signatures:
                continue

            first_sig = signatures[0]
            sig_file = first_sig.get("signature_file")
            if not sig_file:
                continue

            try:
                with open(sig_file) as f:
                    data = json.load(f)
                    concept_name = concept_data.get("concept_name")
                    if isinstance(data, dict) and "frames" in data:
                        self.golden_signatures[concept_name] = data["frames"][0]
                    elif isinstance(data, list) and len(data) > 0:
                        self.golden_signatures[concept_name] = data[0]
            except Exception:
                pass

    def recognize_frame(self, frame: np.ndarray) -> UIRecognitionResult:
        """Process a single frame and return UI result."""
        # Extract landmarks using base class
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.holistic.process(rgb)
        
        landmarks = self.extract_landmarks(results)
        if landmarks is None:
            return UIRecognitionResult(
                concept=None, similarity_score=0.0, confidence_level="low",
                verification_status="low_confidence", all_scores={},
                bsl_target_file=None, gap_to_second=0.0, frame_window_complete=False
            )

        self.add_landmarks(landmarks)
        
        if len(self.landmark_window) < WINDOW_SIZE:
            return UIRecognitionResult(
                concept=None, similarity_score=0.0, confidence_level="low",
                verification_status="low_confidence", all_scores={},
                bsl_target_file=None, gap_to_second=0.0, frame_window_complete=False
            )

        # Compute embedding using base class
        live_embedding = self.compute_embedding()

        # Score all concepts
        scores = {}
        for concept in self.concept_names:
            stored_embedding = self.embeddings[concept]
            cosine_sim = 1 - cosine(live_embedding, stored_embedding)
            scores[concept] = cosine_sim

        # Tier 4 validation
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_concept, best_score = sorted_scores[0]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0
        gap_to_second = best_score - second_score

        # Temporal smoothing
        confirmed_concept = self.temporal_filter.update(best_concept, best_score)

        # Confidence level
        if best_score >= 0.90:
            confidence_level = "high"
        elif best_score >= 0.80:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Verification status
        if confirmed_concept is not None:
            verification_status = "verified"
        elif best_score >= COSINE_SIM_THRESHOLD and gap_to_second >= TIER_4_GAP_THRESHOLD:
            verification_status = "pending_confirmation"
        elif best_score < COSINE_SIM_THRESHOLD:
            verification_status = "low_confidence"
        else:
            verification_status = "cross_concept_noise"

        # BSL target
        bsl_target_file = None
        concept_data = self.language_registry.get(confirmed_concept or best_concept, {})
        bsl_target_file = concept_data.get("bsl_target_file")

        return UIRecognitionResult(
            concept=confirmed_concept or best_concept,
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
        """Draw large green text for confirmed match."""
        if not confirmed_concept:
            return frame
        
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_BOLD
        font_scale = 3.0
        thickness = 5
        
        text = f"✓ {confirmed_concept}"
        text_size, baseline = cv2.getTextSize(text, font, font_scale, thickness)
        x = (w - text_size[0]) // 2
        y = (h // 2) - 50
        
        box_margin = 20
        cv2.rectangle(frame, 
                     (x - box_margin, y - text_size[1] - box_margin),
                     (x + text_size[0] + box_margin, y + baseline + box_margin),
                     (0, 100, 0), -1)
        cv2.rectangle(frame,
                     (x - box_margin, y - text_size[1] - box_margin),
                     (x + text_size[0] + box_margin, y + baseline + box_margin),
                     (0, 255, 0), 2)
        
        cv2.putText(frame, text, (x, y), font, font_scale, (0, 255, 0), thickness)
        
        if bsl_target_path:
            bsl_name = Path(bsl_target_path).stem
            target_text = f"→ {bsl_name}"
            target_size = cv2.getTextSize(target_text, cv2.FONT_HERSHEY_SIMPLEX, 1.8, 2)[0]
            target_x = (w - target_size[0]) // 2
            cv2.putText(frame, target_text, (target_x, y + 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 255), 2)
        
        return frame

    def _draw_dashboard(self, frame: np.ndarray, result: UIRecognitionResult) -> np.ndarray:
        """Draw interactive dashboard on frame."""
        h, w = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX

        bar_y_start = 30
        bar_height = 20
        bar_spacing = 10
        bar_width = 200
        bar_x_left = 20

        cv2.putText(frame, "CONFIDENCE SCORES", (bar_x_left, bar_y_start - 10),
                   font, 0.7, COLOR_TEXT, 2)

        for idx, concept in enumerate(self.concept_names):
            score = result.all_scores.get(concept, 0.0)
            y_pos = bar_y_start + idx * (bar_height + bar_spacing)

            cv2.rectangle(frame, (bar_x_left, y_pos), 
                         (bar_x_left + bar_width, y_pos + bar_height), (30, 30, 30), -1)

            fill_width = int(bar_width * score)
            
            if concept == result.concept and result.verification_status == "verified":
                bar_color = (0, 255, 0)
            elif score >= 0.90:
                bar_color = COLOR_BAR_HIGH
            elif score >= 0.80:
                bar_color = (0, 200, 100)
            elif score >= 0.50:
                bar_color = COLOR_BAR_MED
            else:
                bar_color = COLOR_BAR_LOW

            cv2.rectangle(frame, (bar_x_left, y_pos), 
                         (bar_x_left + fill_width, y_pos + bar_height), bar_color, -1)

            threshold_x = bar_x_left + int(bar_width * COSINE_SIM_THRESHOLD)
            cv2.line(frame, (threshold_x, y_pos), (threshold_x, y_pos + bar_height), (255, 255, 255), 1)

            if concept == result.concept and result.verification_status == "verified":
                border_color, border_thickness = (0, 255, 0), 2
            else:
                border_color, border_thickness = COLOR_TEXT, 1
            cv2.rectangle(frame, (bar_x_left, y_pos), 
                         (bar_x_left + bar_width, y_pos + bar_height), border_color, border_thickness)

            label_text = f"{concept[:8]:8s} {score:.2f}"
            label_color = (0, 255, 0) if concept == result.concept and result.verification_status == "verified" else COLOR_TEXT
            cv2.putText(frame, label_text, (bar_x_left + bar_width + 10, y_pos + 15), 
                       font, 0.6, label_color, 1)

        window_pct = len(self.landmark_window) / WINDOW_SIZE * 100
        cv2.putText(frame, f"Window: {window_pct:.0f}%", (w - 180, 30), font, 0.5, COLOR_TEXT, 1)

        if result.frame_window_complete:
            now_ms = time.time() * 1000
            cooldown_remaining = max(0, self.cooldown_ms - (now_ms - self.last_match_time))
            if result.verification_status == "verified" and cooldown_remaining > 0:
                cv2.putText(frame, f"Cooldown: {cooldown_remaining / 1000:.1f}s",
                           (w - 180, 60), font, 0.5, COLOR_BAR_MED, 1)

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

            text_size = cv2.getTextSize(status_text, font, 0.6, 2)[0]
            cv2.rectangle(frame, (10, h - 30), (20 + text_size[0], h - 10), status_color, -1)
            cv2.rectangle(frame, (10, h - 30), (20 + text_size[0], h - 10), COLOR_TEXT, 1)
            cv2.putText(frame, status_text, (15, h - 15), font, 0.6, COLOR_TEXT, 2)

        return frame

    def _draw_ghost_skeleton(self, frame: np.ndarray, result: UIRecognitionResult) -> np.ndarray:
        """Draw golden signature skeleton overlay (debug mode)."""
        if not self.debug or not result.concept:
            return frame

        golden_pose = self.golden_signatures.get(result.concept)
        if not golden_pose:
            return frame

        h, w = frame.shape[:2]

        try:
            pose_landmarks = golden_pose.get("pose_landmarks", [])
            if not pose_landmarks:
                return frame

            pose_pixels = []
            for lm in pose_landmarks[:6]:
                x_pixel = int(lm["x"] * w)
                y_pixel = int(lm["y"] * h)
                pose_pixels.append((x_pixel, y_pixel))

            if len(pose_pixels) >= 4:
                connections = [(0, 1), (0, 2), (1, 3), (2, 4)]
                for start_idx, end_idx in connections:
                    if start_idx < len(pose_pixels) and end_idx < len(pose_pixels):
                        cv2.line(frame, pose_pixels[start_idx], pose_pixels[end_idx], COLOR_GHOST, 2)

            for pixel in pose_pixels:
                cv2.circle(frame, pixel, 3, COLOR_GHOST, -1)
        except Exception:
            pass

        return frame

    def _emit_socket(self, concept_id: str, score: float):
        """Emit recognition result via Socket.io."""
        if not self.socket_url or not self.sio or not self.socket_connected:
            return

        try:
            concept_data = self.concept_registry.get(concept_id, {})
            concept_name = concept_data.get("concept_name", concept_id)
            bsl_target_path = concept_data.get("bsl_target_file", "")
            
            self.sio.emit("sign_recognized", {
                "concept": concept_id,
                "score": float(score),
                "timestamp": time.time(),
            })
            
            self.sio.emit("translation_event", {
                "concept_id": concept_id,
                "concept_name": concept_name,
                "bsl_target_path": str(bsl_target_path) if bsl_target_path else None,
                "similarity_score": float(score),
                "timestamp": time.time(),
                "source": "recognition_engine_ui",
                "verification_status": "verified"
            })
            
            if self.debug:
                print(f"📡 Emitted: {concept_name}")
        except Exception as e:
            print(f"⚠️  Socket.io emit failed: {e}")

    def run(self, camera_id: int = 0, delay_ms: int = 1):
        """Main recognition loop."""
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Failed to open camera {camera_id}")
            return

        print(f"🎥 Camera opened. Press ESC or 'q' to quit, 'r' to reset window")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)

                result = self.recognize_frame(frame)

                frame = self._draw_dashboard(frame, result)

                if result.verification_status == "verified":
                    frame = self._draw_winner_display(frame, result.concept, result.bsl_target_file)

                if self.debug:
                    frame = self._draw_ghost_skeleton(frame, result)

                if result.frame_window_complete and result.verification_status == "verified":
                    now_ms = time.time() * 1000
                    if now_ms - self.last_match_time > self.cooldown_ms:
                        self._emit_socket(result.concept, result.similarity_score)
                        self.last_match_time = now_ms
                        self.last_matched_concept = result.concept

                cv2.imshow("Sign Language Recognition - MVP Dashboard", frame)

                key = cv2.waitKey(delay_ms) & 0xFF
                if key == 27 or key == ord("q"):
                    print("\n👋 Exiting...")
                    break
                elif key == ord("r"):
                    self.reset_window()
                    self.temporal_filter.reset()
                    print("🔄 Window and temporal filter reset")

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.close()
            if self.sio:
                try:
                    self.sio.disconnect()
                except Exception:
                    pass


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Real-time sign recognition with dashboard")
    parser.add_argument("--debug", action="store_true", help="Enable ghost skeleton overlay")
    parser.add_argument("--camera", type=int, default=0, help="Camera device ID")
    parser.add_argument("--delay", type=int, default=1, help="Frame delay in ms")
    parser.add_argument("--socket-url", type=str, help="Socket.io server URL")
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
