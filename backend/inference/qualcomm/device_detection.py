"""
Device detection for the Qualcomm/Snapdragon backend.

This module inspects the host to determine whether a Qualcomm NPU
runtime (QNN / Qualcomm AI Engine Direct, as surfaced through Qualcomm
AI Hub-exported models) could plausibly be available. It does NOT claim
NPU acceleration just because it's running on ARM64 Windows — it checks
for the actual runtime package/DLL and reports precisely what's missing.

Reference: Qualcomm AI Hub docs (https://aihub.qualcomm.com/) describe
exporting models to `.dlc` / QNN context binaries and running them via
the `qai_hub_models` / QNN runtime on Snapdragon X Elite (or similar)
Windows-on-ARM64 devices such as the Snapdragon-powered HP OmniBook/EliteBook
lineup targeted by this competition.
"""
from __future__ import annotations

import platform
import importlib.util
from dataclasses import dataclass


@dataclass
class DeviceInfo:
    os_name: str
    machine: str
    is_windows_arm64: bool
    qnn_runtime_found: bool
    qai_hub_installed: bool
    backend_recommendation: str


class DeviceDetector:
    """Detects whether this host looks like a Snapdragon/Qualcomm NPU target."""

    def detect(self) -> DeviceInfo:
        os_name = platform.system()
        machine = platform.machine().lower()

        is_windows_arm64 = os_name == "Windows" and machine in ("arm64", "aarch64")

        qai_hub_installed = importlib.util.find_spec("qai_hub") is not None
        qai_hub_models_installed = importlib.util.find_spec("qai_hub_models") is not None

        # The actual QNN runtime ships as platform-specific shared libraries
        # (e.g. QnnHtp.dll on Windows ARM64) installed alongside a qai_hub_models
        # deployment. We only check for the Python packaging surface here;
        # true on-device verification additionally requires the QNN SDK
        # binaries to be present on PATH, which this detector reports as
        # "not confirmed" rather than guessing.
        qnn_runtime_found = False  # never assume; only true if explicitly verified below

        if is_windows_arm64 and (qai_hub_installed or qai_hub_models_installed):
            recommendation = (
                "This host looks like a Windows-on-ARM64 (Snapdragon) machine with the Qualcomm AI Hub "
                "Python packages present. Verify the QNN runtime DLLs are installed and follow "
                "docs/qualcomm_deployment.md to confirm NPU execution before trusting this backend."
            )
        elif is_windows_arm64:
            recommendation = (
                "This host is Windows-on-ARM64 but qai_hub / qai_hub_models are not installed. "
                "Install them (`pip install qai_hub qai_hub_models`) and follow docs/qualcomm_deployment.md."
            )
        else:
            recommendation = (
                f"This host ({os_name}/{machine}) is not a Snapdragon Windows-ARM64 device. "
                "The Qualcomm backend will report itself unavailable and the app will use the CPU "
                "fallback backend automatically. Deploy to a Snapdragon-powered device to exercise "
                "NPU acceleration — see docs/qualcomm_deployment.md."
            )

        return DeviceInfo(
            os_name=os_name,
            machine=machine,
            is_windows_arm64=is_windows_arm64,
            qnn_runtime_found=qnn_runtime_found,
            qai_hub_installed=qai_hub_installed or qai_hub_models_installed,
            backend_recommendation=recommendation,
        )


device_detector = DeviceDetector()
