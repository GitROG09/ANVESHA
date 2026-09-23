"""
ANVEṢHA AI benchmark harness.

Measures REAL latency/memory numbers for the CPU fallback vision backend
and the verification engine on whatever machine this script is run on.
It does not measure the Qualcomm NPU backend, because no Snapdragon NPU
is present in this development environment — that section of the report
is filled with Qualcomm AI Hub's *published reference figures* only, and
is clearly labeled as such, never merged with our own measurements.

Usage:
    python benchmarks/benchmark.py --runs 30
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import cv2

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.experiments.engine import ExperimentEngine, DEFAULT_EXPERIMENTS_DIR
from backend.inference.fallback.vision_backend import FallbackVisionBackend
from backend.schemas.models import DetectedConnection, SensorReading, VisualObservation
from backend.verification.engine import verify

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def _make_test_frame(resolution=(640, 480)) -> bytes:
    w, h = resolution
    img = np.random.randint(60, 200, (h, w, 3), dtype=np.uint8)
    cv2.rectangle(img, (w // 6, h // 6), (w // 3, h // 3), (255, 255, 255), -1)
    cv2.rectangle(img, (w // 2, h // 2), (2 * w // 3, 2 * h // 3), (10, 10, 10), -1)
    ok, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * (p / 100)
    f, c = int(k), min(int(k) + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


def run_benchmark(n_runs: int, resolution=(640, 480)) -> dict:
    engine = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR)
    experiment = engine.get("ldr_001")
    vision_backend = FallbackVisionBackend()
    frame_bytes = _make_test_frame(resolution)

    # --- model/backend "load time": constructing the backend object.
    t0 = time.perf_counter()
    _ = FallbackVisionBackend()
    load_time_ms = (time.perf_counter() - t0) * 1000

    # --- first inference latency (cold)
    t0 = time.perf_counter()
    vision_backend.analyze(frame_bytes, experiment)
    first_inference_ms = (time.perf_counter() - t0) * 1000

    # --- vision inference latency over n_runs
    vision_latencies = []
    tracemalloc.start()
    for _ in range(n_runs):
        t0 = time.perf_counter()
        vision_backend.analyze(frame_bytes, experiment)
        vision_latencies.append((time.perf_counter() - t0) * 1000)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- verification engine latency (deterministic rule evaluation, no I/O)
    obs = VisualObservation(
        sufficient_evidence=True,
        detected_components=["Arduino", "LDR", "resistor_10k"],
        detected_connections=[
            DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A0", confidence=0.9),
            DetectedConnection(from_component="LDR", from_pin="VCC", to_component="Arduino", to_pin="5V", confidence=0.9),
            DetectedConnection(from_component="resistor_10k", from_pin="1", to_component="LDR", to_pin="OUT", confidence=0.9),
            DetectedConnection(from_component="resistor_10k", from_pin="2", to_component="Arduino", to_pin="GND", confidence=0.9),
        ],
        backend_used="benchmark",
    )
    readings = [SensorReading(sensor="LDR", value=500, unit="ADC", source="simulated", simulated=True)]
    verify_latencies = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        verify(experiment, obs, readings)
        verify_latencies.append((time.perf_counter() - t0) * 1000)

    end_to_end_latencies = [v + e for v, e in zip(vision_latencies, verify_latencies)]

    report = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backend": vision_backend.name,
            "model": "opencv-heuristic (no VLM weights available in this environment)",
            "image_resolution": f"{resolution[0]}x{resolution[1]}",
            "number_of_runs": n_runs,
            "measurement_type": "LOCAL_MEASUREMENT",
            "host": "development container (CPU only, x86_64) — NOT Snapdragon hardware",
        },
        "load_time_ms": round(load_time_ms, 3),
        "first_inference_latency_ms": round(first_inference_ms, 3),
        "vision_latency_ms": {
            "mean": round(statistics.mean(vision_latencies), 3),
            "p50": round(_percentile(vision_latencies, 50), 3),
            "p95": round(_percentile(vision_latencies, 95), 3),
            "min": round(min(vision_latencies), 3),
            "max": round(max(vision_latencies), 3),
        },
        "verification_engine_latency_ms": {
            "mean": round(statistics.mean(verify_latencies), 3),
            "p50": round(_percentile(verify_latencies, 50), 3),
            "p95": round(_percentile(verify_latencies, 95), 3),
        },
        "end_to_end_latency_ms": {
            "mean": round(statistics.mean(end_to_end_latencies), 3),
            "p50": round(_percentile(end_to_end_latencies, 50), 3),
            "p95": round(_percentile(end_to_end_latencies, 95), 3),
        },
        "memory_usage_kb": {
            "current": round(current / 1024, 1),
            "peak": round(peak / 1024, 1),
        },
        "qualcomm_ai_hub_reference_metrics": {
            "measurement_type": "AI_HUB_REFERENCE_METRIC — NOT measured on this machine",
            "note": (
                "No Snapdragon NPU hardware is available in this development environment, and Whisper/"
                "Qwen3-VL weights could not be downloaded here (network restricted to package registries). "
                "Do not treat these as our benchmark; they are placeholders to be replaced with figures read "
                "directly from https://aihub.qualcomm.com/ model profiling pages for the specific exported "
                "model + device once run on real hardware, per docs/qualcomm_deployment.md."
            ),
            "value": None,
        },
    }
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    args = parser.parse_args()

    report = run_benchmark(args.runs, (args.width, args.height))

    json_path = RESULTS_DIR / "benchmark_report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    md_path = RESULTS_DIR / "benchmark_report.md"
    with open(md_path, "w") as f:
        f.write("# ANVEṢHA AI — Benchmark Report\n\n")
        f.write(f"Generated: {report['meta']['timestamp']}\n\n")
        f.write("## Local Measurements (CPU fallback backend, this machine)\n\n")
        f.write(f"- Host: {report['meta']['host']}\n")
        f.write(f"- Backend: `{report['meta']['backend']}`\n")
        f.write(f"- Model: {report['meta']['model']}\n")
        f.write(f"- Image resolution: {report['meta']['image_resolution']}\n")
        f.write(f"- Runs: {report['meta']['number_of_runs']}\n\n")
        f.write(f"- Load time: {report['load_time_ms']} ms\n")
        f.write(f"- First inference latency: {report['first_inference_latency_ms']} ms\n")
        f.write(f"- Vision latency — mean: {report['vision_latency_ms']['mean']} ms, "
                f"p50: {report['vision_latency_ms']['p50']} ms, p95: {report['vision_latency_ms']['p95']} ms\n")
        f.write(f"- Verification engine latency — mean: {report['verification_engine_latency_ms']['mean']} ms, "
                f"p50: {report['verification_engine_latency_ms']['p50']} ms, p95: {report['verification_engine_latency_ms']['p95']} ms\n")
        f.write(f"- End-to-end latency — mean: {report['end_to_end_latency_ms']['mean']} ms, "
                f"p50: {report['end_to_end_latency_ms']['p50']} ms, p95: {report['end_to_end_latency_ms']['p95']} ms\n")
        f.write(f"- Memory — current: {report['memory_usage_kb']['current']} KB, peak: {report['memory_usage_kb']['peak']} KB\n\n")
        f.write("## Qualcomm AI Hub Reference Metrics\n\n")
        f.write("**Not measured on this machine.** " + report["qualcomm_ai_hub_reference_metrics"]["note"] + "\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
