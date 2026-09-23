"""Abstract vision backend interface.

The UI and verification engine never talk to a concrete model. They talk
to this interface. Concrete implementations live in `fallback/` (CPU,
runs anywhere) and `qualcomm/` (Snapdragon NPU via Qualcomm AI Hub).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.models import Experiment, VisualObservation


class VisionBackend(ABC):
    """Contract every vision backend must implement."""

    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this backend can actually run on the current host."""

    @abstractmethod
    def analyze(self, image_bytes: bytes, experiment: Experiment) -> VisualObservation:
        """Analyze a single frame against an experiment's expected components/connections.

        Must NOT hallucinate connections it cannot support with evidence.
        If evidence is insufficient, return VisualObservation(sufficient_evidence=False, ...).
        """

    def describe(self) -> dict:
        return {"name": self.name, "available": self.is_available()}
