"""
Qualcomm/Snapdragon NPU vision backend.

Intended model: Qwen3-VL-4B-Instruct, exported through Qualcomm AI Hub
(https://aihub.qualcomm.com/) to a QNN context binary and executed via
the Qualcomm AI Engine Direct (QNN) runtime on a Snapdragon NPU.

THIS CLASS DOES NOT FABRICATE INFERENCE. On any host where:
  - the OS/architecture is not Windows-on-ARM64, or
  - the `qai_hub` / `qai_hub_models` packages are not installed, or
  - the exported QNN model artifact is not present on disk,
`is_available()` returns False and `analyze()` raises
`QualcommBackendUnavailable` with the exact reason, so the caller
(backend/services/inference_manager.py) can fall back to the CPU
backend and the UI can display the true active backend.

See docs/qualcomm_deployment.md for the exact, verified steps to
prepare and run this backend on real Snapdragon hardware.
"""
from __future__ import annotations

import os

from backend.inference.base.vision import VisionBackend
from backend.inference.qualcomm.device_detection import device_detector
from backend.schemas.models import Experiment, VisualObservation


class QualcommBackendUnavailable(RuntimeError):
    pass


class QualcommVisionBackend(VisionBackend):
    name = "qualcomm-npu-qwen3vl"

    def __init__(self):
        self._model_path = os.environ.get("QUALCOMM_VISION_MODEL_PATH")

    def is_available(self) -> bool:
        device = device_detector.detect()
        if not device.is_windows_arm64:
            return False
        if not device.qai_hub_installed:
            return False
        if not self._model_path or not os.path.exists(self._model_path):
            return False
        return True

    def analyze(self, image_bytes: bytes, experiment: Experiment) -> VisualObservation:
        if not self.is_available():
            device = device_detector.detect()
            raise QualcommBackendUnavailable(
                "Qualcomm NPU vision backend is not available on this host. "
                f"Detected OS/arch: {device.os_name}/{device.machine}. "
                f"{device.backend_recommendation} "
                "Falling back to the CPU vision backend is expected behavior — "
                "see backend/services/inference_manager.py."
            )
        # On real Snapdragon hardware with the QNN runtime + exported
        # Qwen3-VL context binary present, inference would be dispatched
        # here via the qai_hub_models runtime API. Not implemented in
        # this development container because no Snapdragon NPU is present
        # and no model artifact can be downloaded in this network-restricted
        # environment. Implement per docs/qualcomm_deployment.md on target hardware.
        raise NotImplementedError(
            "QUALCOMM_VISION_MODEL_PATH is set, but on-device QNN inference is not implemented "
            "in this repository snapshot. Follow docs/qualcomm_deployment.md to wire up the "
            "qai_hub_models inference call on real Snapdragon hardware."
        )
