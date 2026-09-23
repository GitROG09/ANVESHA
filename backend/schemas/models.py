"""
Core data models for ANVEṢHA AI.

These schemas are the contract between every subsystem: experiment
definitions, camera observations, sensor telemetry, and the verification
engine's output. Nothing downstream should invent fields that aren't
defined here — this keeps the "evidence fusion" step honest and testable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Experiment definition (static, loaded from experiments/*.json)
# ---------------------------------------------------------------------------

class Connection(BaseModel):
    from_component: str = Field(..., alias="from")
    from_pin: str
    to_component: str = Field(..., alias="to")
    to_pin: str
    model_config = {"populate_by_name": True}


class ExpectedMeasurement(BaseModel):
    sensor: str
    unit: str
    min_value: float
    max_value: float
    description: str = ""


class ValidationRule(BaseModel):
    rule_id: str
    description: str
    # "connection" | "measurement"
    rule_type: str
    # for connection rules: which connection (by from_component/to_component) this checks
    target: Optional[str] = None
    severity: str = "deviation"  # "deviation" | "warning"


class ExperimentStep(BaseModel):
    step_id: str
    title: str
    instruction: str
    checks: list[str] = Field(default_factory=list)  # rule_ids relevant to this step


class Experiment(BaseModel):
    experiment_id: str
    title: str
    objective: str
    difficulty: str = "beginner"
    safety_notes: list[str] = Field(default_factory=list)
    components: list[str]
    connections: list[Connection]
    steps: list[ExperimentStep]
    expected_measurements: list[ExpectedMeasurement]
    validation_rules: list[ValidationRule]
    troubleshooting: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Visual observation (produced by the vision backend)
# ---------------------------------------------------------------------------

class DetectedConnection(BaseModel):
    from_component: str
    from_pin: str
    to_component: str
    to_pin: str
    confidence: float


class BoundingBox(BaseModel):
    label: str
    x: float
    y: float
    w: float
    h: float
    confidence: float
    status: str = "uncertain"  # "verified" | "uncertain" | "deviation"


class VisualObservation(BaseModel):
    sufficient_evidence: bool
    detected_components: list[str] = Field(default_factory=list)
    detected_connections: list[DetectedConnection] = Field(default_factory=list)
    bounding_boxes: list[BoundingBox] = Field(default_factory=list)
    notes: str = ""
    backend_used: str = "unknown"
    simulated: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Sensor telemetry
# ---------------------------------------------------------------------------

class SensorReading(BaseModel):
    sensor: str
    value: float
    unit: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "arduino"  # "arduino" | "simulated"
    simulated: bool = False


# ---------------------------------------------------------------------------
# Verification engine output
# ---------------------------------------------------------------------------

class ExperimentState(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    DEVIATION = "DEVIATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceItem(BaseModel):
    source: str  # "vision" | "telemetry" | "procedure"
    summary: str


class StepResult(BaseModel):
    step_id: str
    title: str
    status: str  # "verified" | "failed" | "warning" | "pending"
    expected: str = ""
    observed: str = ""
    why_it_matters: str = ""
    recommended_action: str = ""


class VerificationResult(BaseModel):
    experiment_id: str
    experiment_state: ExperimentState
    confidence: float
    verified_steps: list[StepResult] = Field(default_factory=list)
    failed_steps: list[StepResult] = Field(default_factory=list)
    warnings: list[StepResult] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    expected: list[str] = Field(default_factory=list)
    observed: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VerificationRequest(BaseModel):
    experiment_id: str
    visual_observation: Optional[VisualObservation] = None
    sensor_readings: list[SensorReading] = Field(default_factory=list)
    user_note: Optional[str] = None
