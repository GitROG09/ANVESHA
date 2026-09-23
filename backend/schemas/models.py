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
# Evidence status — the core "how sure are we, and why" vocabulary shared
# by every layer downstream of raw perception. This is deliberately kept
# separate from any single confidence float: STATUS answers "what kind of
# evidence is this", CONFIDENCE (where applicable) answers "how strong is
# it". A MISSING or OCCLUDED item has no meaningful confidence at all.
# ---------------------------------------------------------------------------

class EvidenceStatus(str, Enum):
    OBSERVED = "OBSERVED"      # directly perceived with usable confidence
    INFERRED = "INFERRED"      # not directly seen, but reasonably implied by other evidence
    UNCERTAIN = "UNCERTAIN"    # perceived, but confidence too low to trust either way
    OCCLUDED = "OCCLUDED"      # known to be blocked from view / partially hidden
    MISSING = "MISSING"        # no evidence at all — not detected, not attempted, not present


# ---------------------------------------------------------------------------
# Visual observation (produced by the vision backend)
# ---------------------------------------------------------------------------

class DetectedConnection(BaseModel):
    from_component: str
    from_pin: str
    to_component: Optional[str] = None
    to_pin: Optional[str] = None
    # Perception-level confidence for THIS connection only. This is never
    # the same number as frame/image quality, and never the same number as
    # the verification engine's overall certainty — see VisualObservation
    # .frame_quality and VerificationResult.confidence respectively.
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.OBSERVED


class Point2D(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)


class DetectedComponent(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: Optional["BoundingBox"] = None
    status: EvidenceStatus = EvidenceStatus.OBSERVED


class DetectedPin(BaseModel):
    component_label: str
    pin_label: str
    position: Point2D
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.OBSERVED


class WireEndpoint(BaseModel):
    wire_id: str
    position: Point2D
    component_label: Optional[str] = None
    pin_label: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.OBSERVED


class BoundingBox(BaseModel):
    label: str
    x: float
    y: float
    w: float
    h: float
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: str = "uncertain"  # "verified" | "uncertain" | "deviation" | "occluded"


class VisualObservation(BaseModel):
    sufficient_evidence: bool
    detected_components: list[str] = Field(default_factory=list)
    component_observations: list[DetectedComponent] = Field(default_factory=list)
    detected_pins: list[DetectedPin] = Field(default_factory=list)
    wire_endpoints: list[WireEndpoint] = Field(default_factory=list)
    detected_connections: list[DetectedConnection] = Field(default_factory=list)
    bounding_boxes: list[BoundingBox] = Field(default_factory=list)
    notes: str = ""
    backend_used: str = "unknown"
    simulated: bool = False
    # Image-quality confidence: "is this frame suitable for perception at
    # all?" (blur/brightness/exposure heuristics). Deliberately a distinct
    # field from any per-connection confidence — a sharp, well-lit frame
    # (frame_quality near 1.0) can still yield zero reliable connection
    # detections, and a backend must never let a good frame_quality score
    # leak into individual connection/component confidence values.
    frame_quality: Optional[float] = None
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
# Evidence fusion output
#
# This is the structured, per-claim record the evidence-fusion module
# (backend/evidence/fusion.py) produces by combining vision + telemetry +
# the experiment specification. The verification engine consumes THIS,
# not raw VisualObservation/SensorReading data, so the "does this satisfy
# the experiment" logic never has to re-derive what was actually observed.
# ---------------------------------------------------------------------------

class StructuredEvidence(BaseModel):
    # What this piece of evidence is about, e.g. "LDR OUT -> Arduino A0"
    # or "LDR measurement".
    subject: str
    rule_id: Optional[str] = None
    # "connection" | "measurement" | "component"
    relationship: str
    # What the experiment specification requires here.
    expected: str
    # What was actually observed/measured, if anything. None when status
    # is MISSING (there is nothing to report).
    observed: Optional[str] = None
    status: EvidenceStatus
    # Perception/measurement confidence for THIS item alone. None when not
    # applicable (MISSING has no confidence to report). Never conflated
    # with image quality or with the eventual verification certainty.
    confidence: Optional[float] = None
    source: str  # "vision" | "telemetry" | "procedure"
    severity: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceBundle(BaseModel):
    """All structured evidence fused for one verification pass."""

    experiment_id: str
    # Whether the underlying frame was even suitable for perception. When
    # False, no per-connection evidence below should be trusted regardless
    # of individual status/confidence values.
    frame_suitable: bool
    frame_quality: Optional[float] = None
    structured_evidence: list[StructuredEvidence] = Field(default_factory=list)
    simulated: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


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
