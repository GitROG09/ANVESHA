# ANVEṢHA AI — Benchmark Report

Generated: 2026-09-23T04:32:39.991126+00:00

## Local Measurements (CPU fallback backend, this machine)

- Host: development container (CPU only, x86_64) — NOT Snapdragon hardware
- Backend: `fallback-cpu-opencv`
- Model: opencv-heuristic (no VLM weights available in this environment)
- Image resolution: 640x480
- Runs: 30

- Load time: 0.002 ms
- First inference latency: 35.651 ms
- Vision latency — mean: 30.851 ms, p50: 29.95 ms, p95: 37.353 ms
- Verification engine latency — mean: 0.033 ms, p50: 0.027 ms, p95: 0.064 ms
- End-to-end latency — mean: 30.884 ms, p50: 29.976 ms, p95: 37.464 ms
- Memory — current: 1.3 KB, peak: 6066.6 KB

## Qualcomm AI Hub Reference Metrics

**Not measured on this machine.** No Snapdragon NPU hardware is available in this development environment, and Whisper/Qwen3-VL weights could not be downloaded here (network restricted to package registries). Do not treat these as our benchmark; they are placeholders to be replaced with figures read directly from https://aihub.qualcomm.com/ model profiling pages for the specific exported model + device once run on real hardware, per docs/qualcomm_deployment.md.
