"""ANVEṢHA AI backend — FastAPI application entrypoint."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.experiments.engine import experiment_engine
from backend.schemas.models import (
    Experiment,
    SensorReading,
    VerificationRequest,
    VerificationResult,
)
from backend.services.inference_manager import inference_manager
from backend.services.simulation import get_scenario, list_scenarios
from backend.telemetry.service import telemetry_service
from backend.verification.engine import verify

app = FastAPI(
    title="ANVEṢHA AI",
    description="On-device multimodal intelligence for physical experiment verification.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local desktop app; no cloud deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "anvesha-ai-backend"}


@app.get("/api/runtime")
def runtime_status() -> dict:
    """Reports the active inference backend (Qualcomm NPU vs CPU fallback)."""
    return inference_manager.runtime_status()


@app.get("/api/experiments", response_model=list[Experiment])
def list_experiments() -> list[Experiment]:
    return experiment_engine.list_experiments()


@app.get("/api/experiments/{experiment_id}", response_model=Experiment)
def get_experiment(experiment_id: str) -> Experiment:
    try:
        return experiment_engine.get(experiment_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/vision/analyze")
async def analyze_frame(experiment_id: str, file: UploadFile = File(...)) -> dict:
    """Runs the active vision backend on an uploaded frame against an experiment."""
    try:
        experiment = experiment_engine.get(experiment_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    image_bytes = await file.read()
    backend = inference_manager.get_vision_backend()
    try:
        observation = backend.analyze(image_bytes, experiment)
    except Exception as e:
        # Show the backend error clearly; never substitute a fake response.
        raise HTTPException(status_code=502, detail=f"Vision backend '{backend.name}' error: {e}")
    return observation.model_dump()


@app.get("/api/telemetry/simulate")
def simulate_telemetry(sensor: str, center: float, spread: float = 5.0, unit: str = "ADC") -> dict:
    reading = telemetry_service.read_simulated(sensor, center, spread, unit)
    return reading.model_dump()


@app.post("/api/verify", response_model=VerificationResult)
def verify_experiment(payload: VerificationRequest) -> VerificationResult:
    try:
        experiment = experiment_engine.get(payload.experiment_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if any(reading.simulated for reading in payload.sensor_readings):
        raise HTTPException(
            status_code=400,
            detail="Simulated telemetry is only accepted through the explicit /api/demo/* path.",
        )

    return verify(experiment, payload.visual_observation, payload.sensor_readings)


@app.get("/api/benchmarks")
def get_benchmarks() -> dict:
    """Serves the most recent locally-generated benchmark report, if one exists."""
    report_path = Path(__file__).resolve().parents[2] / "benchmarks" / "results" / "benchmark_report.json"
    if not report_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No benchmark report found. Run `python benchmarks/benchmark.py` to generate one.",
        )
    with open(report_path) as f:
        return json.load(f)


@app.get("/api/demo/scenarios")
def demo_scenarios() -> list[dict]:
    return list_scenarios()


@app.post("/api/demo/{scenario_id}/verify", response_model=VerificationResult)
def demo_verify(scenario_id: str) -> VerificationResult:
    """Runs the verification engine against a scripted, clearly-labeled demo scenario."""
    try:
        scenario = get_scenario(scenario_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    experiment = experiment_engine.get(scenario["experiment_id"])
    result = verify(experiment, scenario["visual"], scenario["readings"])
    return result
