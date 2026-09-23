"""Explicit test-fixture provider; never selected for real application inference."""
from __future__ import annotations

from typing import Any

from backend.inference.base.vision import VisionBackend
from backend.inference.perception_adapter import parse_perception_output
from backend.schemas.models import Experiment, VisualObservation


class FixtureVisionBackend(VisionBackend):
    """Adapts labeled structured fixtures for deterministic pipeline tests."""

    name = "test-fixture-provider"

    def __init__(self, output: Any):
        self.output = output

    def is_available(self) -> bool:
        return True

    def analyze(self, image_bytes: bytes, experiment: Experiment) -> VisualObservation:
        del image_bytes
        return parse_perception_output(self.output, experiment, backend_used=self.name)
