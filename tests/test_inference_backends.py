import io

import numpy as np
import pytest

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from backend.experiments.engine import ExperimentEngine, DEFAULT_EXPERIMENTS_DIR
from backend.inference.fallback.vision_backend import FallbackVisionBackend
from backend.inference.fallback.speech_backend import FallbackSpeechBackend, SpeechBackendUnavailable
from backend.inference.qualcomm.vision_backend import QualcommVisionBackend, QualcommBackendUnavailable
from backend.inference.qualcomm.device_detection import device_detector

engine = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR)


def _make_test_jpeg(color=(120, 120, 120), size=(200, 200)) -> bytes:
    img = np.full((size[1], size[0], 3), color, dtype=np.uint8)
    # add some edges so contour heuristic has something to find
    cv2.rectangle(img, (30, 30), (80, 80), (255, 255, 255), -1)
    cv2.rectangle(img, (120, 120), (170, 170), (0, 0, 0), -1)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


@pytest.mark.skipif(not HAS_CV2, reason="opencv not installed")
def test_fallback_vision_backend_available():
    backend = FallbackVisionBackend()
    assert backend.is_available() is True


@pytest.mark.skipif(not HAS_CV2, reason="opencv not installed")
def test_fallback_vision_sufficient_evidence_on_decent_frame():
    backend = FallbackVisionBackend()
    exp = engine.get("ldr_001")
    image_bytes = _make_test_jpeg()
    obs = backend.analyze(image_bytes, exp)
    assert obs.sufficient_evidence is True
    assert obs.detected_connections == []  # honest: no fabricated connections
    assert obs.simulated is False


@pytest.mark.skipif(not HAS_CV2, reason="opencv not installed")
def test_fallback_vision_rejects_dark_frame():
    backend = FallbackVisionBackend()
    exp = engine.get("ldr_001")
    dark_bytes = _make_test_jpeg(color=(2, 2, 2))
    obs = backend.analyze(dark_bytes, exp)
    assert obs.sufficient_evidence is False
    assert "dark" in obs.notes.lower()


def test_fallback_speech_unavailable_by_default():
    backend = FallbackSpeechBackend()
    assert backend.is_available() is False
    with pytest.raises(SpeechBackendUnavailable):
        backend.transcribe(b"fake-audio")


def test_qualcomm_backend_reports_unavailable_off_snapdragon():
    device = device_detector.detect()
    backend = QualcommVisionBackend()
    if device.is_windows_arm64:
        pytest.skip("Running on a Windows-ARM64 host; unavailability assumption doesn't apply here.")
    assert backend.is_available() is False
    exp = engine.get("ldr_001")
    with pytest.raises(QualcommBackendUnavailable):
        backend.analyze(b"irrelevant", exp)
