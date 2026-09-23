"""
Qualcomm/Snapdragon NPU speech backend.

Intended model: Whisper-Small (quantized) exported via Qualcomm AI Hub
to run on the Snapdragon NPU through the QNN runtime, mirroring
`vision_backend.py`'s honesty contract: no fabricated transcripts, no
assumed hardware. See docs/qualcomm_deployment.md.
"""
from __future__ import annotations

import os

from backend.inference.base.speech import SpeechBackend
from backend.inference.qualcomm.device_detection import device_detector


class QualcommSpeechBackendUnavailable(RuntimeError):
    pass


class QualcommSpeechBackend(SpeechBackend):
    name = "qualcomm-npu-whisper-small"

    def __init__(self):
        self._model_path = os.environ.get("QUALCOMM_SPEECH_MODEL_PATH")

    def is_available(self) -> bool:
        device = device_detector.detect()
        if not device.is_windows_arm64 or not device.qai_hub_installed:
            return False
        return bool(self._model_path) and os.path.exists(self._model_path)

    def transcribe(self, audio_bytes: bytes) -> str:
        if not self.is_available():
            device = device_detector.detect()
            raise QualcommSpeechBackendUnavailable(
                "Qualcomm NPU speech backend is not available on this host "
                f"({device.os_name}/{device.machine}). {device.backend_recommendation}"
            )
        raise NotImplementedError(
            "QUALCOMM_SPEECH_MODEL_PATH is set, but on-device QNN speech inference is not "
            "implemented in this repository snapshot. Follow docs/qualcomm_deployment.md."
        )
