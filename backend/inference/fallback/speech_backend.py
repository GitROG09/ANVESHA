"""
Fallback speech backend.

There is no bundled speech model in this repository (Whisper-Small
weights are ~150MB+ and are not vendored here, and this development
container has no network access to a model hub). Rather than fabricate
a transcript, this backend honestly reports itself unavailable and
raises a clear, typed error if `transcribe` is called anyway.

To make voice actually work:
  1. Install a local Whisper runtime, e.g. `pip install faster-whisper`
     or `openai-whisper`, and download `whisper-small` (or a quantized
     variant) weights onto the host.
  2. Point WHISPER_MODEL_PATH at the downloaded weights.
  3. On Snapdragon, prefer `backend/inference/qualcomm/speech_backend.py`,
     which documents the Qualcomm AI Hub deployment path instead.
"""
from __future__ import annotations

import os

from backend.inference.base.speech import SpeechBackend


class SpeechBackendUnavailable(RuntimeError):
    pass


class FallbackSpeechBackend(SpeechBackend):
    name = "fallback-cpu-whisper"

    def __init__(self):
        self._model_path = os.environ.get("WHISPER_MODEL_PATH")

    def is_available(self) -> bool:
        # Only "available" if a local whisper model has actually been
        # installed and pointed to via WHISPER_MODEL_PATH. We do not
        # silently pretend a model is loaded.
        return bool(self._model_path) and os.path.exists(self._model_path)

    def transcribe(self, audio_bytes: bytes) -> str:
        if not self.is_available():
            raise SpeechBackendUnavailable(
                "No local speech model is installed. Set WHISPER_MODEL_PATH to a downloaded "
                "whisper-small (or quantized) model, or use text input instead of voice. "
                "See docs/ai_models.md for setup instructions."
            )
        # If a model were installed, this is where faster-whisper / whisper
        # inference would run. Left unimplemented rather than faked because
        # no model is bundled with this environment.
        raise NotImplementedError(
            "A WHISPER_MODEL_PATH was set but local inference is not wired up in this "
            "development environment. Implement the faster-whisper call here."
        )
