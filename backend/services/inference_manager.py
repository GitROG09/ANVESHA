"""
InferenceManager — the only place that knows about concrete backend
implementations. The API layer asks this manager for "the vision
backend" / "the speech backend" and gets whichever one is actually
usable on this host, in priority order: Qualcomm NPU > CPU fallback.

This is what makes the UI's "not directly depend on Qualcomm APIs"
requirement true in practice.
"""
from __future__ import annotations

from backend.inference.base.speech import SpeechBackend
from backend.inference.base.vision import VisionBackend
from backend.inference.fallback.speech_backend import FallbackSpeechBackend
from backend.inference.fallback.vision_backend import FallbackVisionBackend
from backend.inference.qualcomm.runtime import runtime_detector
from backend.inference.qualcomm.speech_backend import QualcommSpeechBackend
from backend.inference.qualcomm.vision_backend import QualcommVisionBackend


class InferenceManager:
    def __init__(self):
        self._qualcomm_vision = QualcommVisionBackend()
        self._fallback_vision = FallbackVisionBackend()
        self._qualcomm_speech = QualcommSpeechBackend()
        self._fallback_speech = FallbackSpeechBackend()

    def get_vision_backend(self) -> VisionBackend:
        if self._qualcomm_vision.is_available() and self._qualcomm_vision.is_executable():
            return self._qualcomm_vision
        return self._fallback_vision

    def get_speech_backend(self) -> SpeechBackend:
        if self._qualcomm_speech.is_available():
            return self._qualcomm_speech
        return self._fallback_speech

    def runtime_status(self) -> dict:
        vision = self.get_vision_backend()
        speech = self.get_speech_backend()
        return runtime_detector.status(
            vision.name,
            speech.name,
            qualcomm_inference_ready=vision is self._qualcomm_vision and self._qualcomm_vision.is_executable(),
        ).to_dict()


inference_manager = InferenceManager()
