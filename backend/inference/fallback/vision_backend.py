"""
Fallback (CPU) vision backend.

This backend runs anywhere — no NPU, no GPU, no downloaded model weights.
It is intentionally honest about what it can and cannot do:

CAN do for real, using OpenCV:
  - Assess whether a frame is usable at all (blur / brightness / exposure)
    to decide `sufficient_evidence`.
  - Estimate how many distinct component-like regions are visible
    (contour heuristic) as a very rough proxy for "components present".

CANNOT do for real, without a trained/loaded detection model:
  - Reliable pin-level wire tracing (e.g. "this wire goes from LDR OUT to A0").

Because of that second limitation, this backend NEVER fabricates
`detected_connections`. Production pin-level connection detection is the
job of the Qwen3-VL-based backend (see `backend/inference/qualcomm/` and
its Snapdragon deployment doc) or, for demos without that model
available, the explicitly-labeled simulation service in
`backend/services/simulation.py`.
"""
from __future__ import annotations

import io

import numpy as np

from backend.inference.base.vision import VisionBackend
from backend.schemas.models import Experiment, VisualObservation

try:
    import cv2

    _HAS_CV2 = True
except ImportError:  # pragma: no cover - exercised only if opencv isn't installed
    _HAS_CV2 = False

BLUR_THRESHOLD = 50.0  # Laplacian variance below this = too blurry
MIN_BRIGHTNESS = 25.0  # mean pixel value below this = too dark
MAX_BRIGHTNESS = 235.0  # mean pixel value above this = blown out


class FallbackVisionBackend(VisionBackend):
    name = "fallback-cpu-opencv"

    def is_available(self) -> bool:
        return _HAS_CV2

    def _decode(self, image_bytes: bytes) -> "np.ndarray":
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes as a valid image.")
        return img

    def _assess_quality(self, img: "np.ndarray") -> tuple[bool, str, float]:
        """Returns (suitable_for_perception, note, frame_quality_score).

        frame_quality is a 0-1 heuristic score answering ONLY "is this
        frame usable at all" (sharpness + exposure). It is never reused as
        a stand-in for object/connection detection confidence — those are
        separate numbers with a separate meaning, computed (or explicitly
        withheld) per-connection, never derived from this score.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        brightness = float(gray.mean())

        # Normalize sharpness and brightness into independent 0-1 sub-scores,
        # then combine. This score never becomes a perception/connection
        # confidence value — see the module docstring.
        sharpness_component = min(blur_score / (BLUR_THRESHOLD * 4), 1.0)
        mid_brightness = (MIN_BRIGHTNESS + MAX_BRIGHTNESS) / 2
        half_range = (MAX_BRIGHTNESS - MIN_BRIGHTNESS) / 2
        brightness_component = max(0.0, 1.0 - abs(brightness - mid_brightness) / half_range)
        quality = round(min(max(0.5 * sharpness_component + 0.5 * brightness_component, 0.0), 1.0), 2)

        if blur_score < BLUR_THRESHOLD:
            return False, f"Frame appears too blurry (sharpness score {blur_score:.1f}). Hold the camera steady.", quality
        if brightness < MIN_BRIGHTNESS:
            return False, f"Frame is too dark (mean brightness {brightness:.1f}/255). Improve lighting.", quality
        if brightness > MAX_BRIGHTNESS:
            return False, f"Frame is overexposed (mean brightness {brightness:.1f}/255). Reduce direct glare.", quality
        return True, f"Frame quality OK (sharpness {blur_score:.1f}, brightness {brightness:.1f}).", quality

    def _estimate_component_regions(self, img: "np.ndarray") -> int:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape
        min_area = (h * w) * 0.001
        significant = [c for c in contours if cv2.contourArea(c) > min_area]
        return len(significant)

    def analyze(self, image_bytes: bytes, experiment: Experiment) -> VisualObservation:
        if not _HAS_CV2:
            raise RuntimeError("FallbackVisionBackend requires opencv-python-headless to be installed.")

        img = self._decode(image_bytes)
        ok, quality_note, frame_quality = self._assess_quality(img)

        if not ok:
            return VisualObservation(
                sufficient_evidence=False,
                notes=quality_note,
                backend_used=self.name,
                simulated=False,
                frame_quality=frame_quality,
            )

        region_count = self._estimate_component_regions(img)
        limitation_note = (
            f"{quality_note} Detected {region_count} distinct component-like regions via edge/contour "
            "heuristics. This CPU fallback cannot reliably trace individual wire-to-pin connections; "
            "pin-level connection verification requires the vision-language model backend "
            "(Qwen3-VL via Qualcomm AI Hub) or an explicitly labeled simulation."
        )

        return VisualObservation(
            sufficient_evidence=True,
            detected_components=[],  # honest: no reliable per-component labeling without a trained model
            detected_connections=[],  # honest: no fabricated pin-level connections
            bounding_boxes=[],
            notes=limitation_note,
            backend_used=self.name,
            simulated=False,
            # A good frame_quality score here says only "this image is
            # sharp and well-exposed" — it must NOT be read as confidence
            # that any particular component/connection was detected, since
            # detected_connections is (honestly) empty.
            frame_quality=frame_quality,
        )
