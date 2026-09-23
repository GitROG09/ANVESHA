"""Lazy Qwen3-VL provider foundation.

This module defines the future local Transformers integration without loading
or downloading model weights at import time. It is intentionally not
registered in InferenceManager until executable inference is implemented and
validated on a supported runtime.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from backend.inference.base.vision import VisionBackend
from backend.inference.perception_adapter import parse_perception_output
from backend.schemas.models import Experiment, VisualObservation


QWEN3VL_MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"


class Qwen3VLProviderUnavailable(RuntimeError):
    """Raised when local Qwen3-VL inference cannot execute."""


class Qwen3VLVisionProvider(VisionBackend):
    """Model-agnostic ANVEṢHA adapter for a future local Qwen3-VL runtime."""

    name = "qwen3vl-local"

    def __init__(self, model_id: str = QWEN3VL_MODEL_ID):
        self.model_id = model_id
        self._processor: Any = None
        self._model: Any = None

    @staticmethod
    def structured_prompt(experiment: Experiment) -> str:
        """Build a perception-only prompt; no experiment verdict is requested."""
        components = ", ".join(experiment.components)
        connections = "; ".join(
            f"{connection.from_component} {connection.from_pin} -> "
            f"{connection.to_component} {connection.to_pin}"
            for connection in experiment.connections
        )
        return f"""You are a visual evidence extractor for ANVESHA AI.

Return ONLY one JSON object matching the supplied visual-evidence schema.
Describe observations from the image; never return a verdict or decide whether
an experiment passes. Do not include keys named verdict, experiment_state,
pass, warning, or deviation.

Use only these evidence statuses: OBSERVED, INFERRED, UNCERTAIN, OCCLUDED,
MISSING. If a component, pin, endpoint, or target cannot be established,
leave it unresolved and use UNCERTAIN, OCCLUDED, or MISSING as appropriate.
Never guess an endpoint or connection because it is expected by the procedure.
Coordinates and bounding boxes must be normalized to [0, 1]. Confidence must
be in [0, 1].

Expected component labels: {components}
Expected connection context: {connections}

JSON shape:
{{
  "sufficient_evidence": true,
  "frame_quality": 0.0,
  "components": [],
  "pins": [],
  "wire_endpoints": [],
  "connections": [],
  "notes": ""
}}
"""

    def is_available(self) -> bool:
        """Report only local dependency and weight availability, never capability by hope."""
        if importlib.util.find_spec("torch") is None or importlib.util.find_spec("transformers") is None:
            return False
        try:
            from transformers import AutoProcessor
            from transformers import Qwen3VLForConditionalGeneration
        except ImportError:
            return False
        del AutoProcessor, Qwen3VLForConditionalGeneration
        return self._local_model_files_exist()

    def _local_model_files_exist(self) -> bool:
        """Check common local paths without contacting a model hub."""
        candidate = Path(self.model_id)
        if candidate.is_dir():
            return (candidate / "config.json").exists()
        return False

    def _load_model(self) -> tuple[Any, Any]:
        """Lazily load only local files; this method never downloads weights."""
        if self._processor is not None and self._model is not None:
            return self._processor, self._model
        if not self._local_model_files_exist():
            raise Qwen3VLProviderUnavailable(
                f"Qwen3-VL weights unavailable locally for {self.model_id}. "
                "No model download is attempted by this provider."
            )
        try:
            from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
            self._processor = AutoProcessor.from_pretrained(self.model_id, local_files_only=True)
            self._model = Qwen3VLForConditionalGeneration.from_pretrained(
                self.model_id,
                local_files_only=True,
            )
        except Exception as exc:
            self._processor = None
            self._model = None
            raise Qwen3VLProviderUnavailable(
                f"Qwen3-VL local loading is unavailable for {self.model_id}: {exc}"
            ) from exc
        return self._processor, self._model

    def observation_from_response(self, response: str | bytes | dict[str, Any], experiment: Experiment) -> VisualObservation:
        """Convert a mocked/provider JSON response through the shared strict adapter."""
        return parse_perception_output(response, experiment, backend_used=self.name)

    def _generate_structured_response(
        self,
        image_bytes: bytes,
        experiment: Experiment,
        processor: Any,
        model: Any,
    ) -> str:
        """Reserved for the version-specific Transformers generation call."""
        del image_bytes, experiment, processor, model
        raise Qwen3VLProviderUnavailable(
            "Qwen3-VL weights are present, but the version-specific image/message "
            "generation call is not implemented in this provider foundation."
        )

    def analyze(self, image_bytes: bytes, experiment: Experiment) -> VisualObservation:
        processor, model = self._load_model()
        response = self._generate_structured_response(image_bytes, experiment, processor, model)
        return self.observation_from_response(response, experiment)

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model_id": self.model_id,
            "available": self.is_available(),
            "weights_loaded": self._model is not None,
            "inference_validated": False,
        }
