"""Abstract speech backend interface (speech-to-text for voice Q&A)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class SpeechBackend(ABC):
    """Contract every speech backend must implement."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this backend can actually run on the current host."""

    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio to text. Must raise, not fabricate, on failure."""

    def describe(self) -> dict:
        return {"name": self.name, "available": self.is_available()}
