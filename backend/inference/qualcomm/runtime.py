"""
RuntimeDetector — decides which compute backend (CPU / GPU / Qualcomm NPU)
is actually active, for display in the UI's Settings/Runtime screen.

This is the single source of truth the API exposes at GET /api/runtime.
It never reports "Qualcomm NPU" unless device_detection has positively
confirmed a Snapdragon Windows-ARM64 host with the AI Hub packages
present; otherwise it reports the true active backend honestly.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

from backend.inference.qualcomm.device_detection import device_detector


@dataclass
class RuntimeStatus:
    active_backend: str  # "qualcomm-npu" | "cpu-fallback"
    vision_backend: str
    speech_backend: str
    device_os: str
    device_machine: str
    qualcomm_hardware_detected: bool
    notes: str

    def to_dict(self) -> dict:
        return asdict(self)


class RuntimeDetector:
    def status(
        self,
        vision_backend_name: str,
        speech_backend_name: str,
        *,
        qualcomm_inference_ready: bool = False,
    ) -> RuntimeStatus:
        device = device_detector.detect()
        active = "qualcomm-npu" if (
            vision_backend_name == "qualcomm-npu-qwen3vl"
            and qualcomm_inference_ready
            and device.is_windows_arm64
            and device.qai_hub_installed
            and device.qnn_runtime_found
        ) else "cpu-fallback"
        return RuntimeStatus(
            active_backend=active,
            vision_backend=vision_backend_name,
            speech_backend=speech_backend_name,
            device_os=device.os_name,
            device_machine=device.machine,
            qualcomm_hardware_detected=device.is_windows_arm64,
            notes=device.backend_recommendation,
        )


runtime_detector = RuntimeDetector()
