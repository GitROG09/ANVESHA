"""Strict adapter from provider output to the shared VisualObservation contract."""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from backend.schemas.models import (
    BoundingBox,
    DetectedComponent,
    DetectedConnection,
    DetectedPin,
    EvidenceStatus,
    Experiment,
    Point2D,
    VisualObservation,
    WireEndpoint,
)


class PerceptionOutputError(ValueError):
    """Raised when a provider response cannot be trusted as visual evidence."""


class _Box(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    w: float = Field(..., gt=0.0, le=1.0)
    h: float = Field(..., gt=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.OBSERVED

    @model_validator(mode="after")
    def stays_inside_image(self) -> "_Box":
        if self.x + self.w > 1.0 or self.y + self.h > 1.0:
            raise ValueError("Bounding box must remain inside normalized image coordinates.")
        return self


class _Component(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: Optional[_Box] = None
    status: EvidenceStatus = EvidenceStatus.OBSERVED


class _Pin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    component_label: str
    pin_label: str
    position: Point2D
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.OBSERVED


class _Endpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    wire_id: str
    position: Point2D
    component_label: Optional[str] = None
    pin_label: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.OBSERVED


class _Connection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_component: str
    from_pin: str
    to_component: Optional[str] = None
    to_pin: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    wire_id: Optional[str] = None


class _ProviderOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sufficient_evidence: bool
    frame_quality: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    components: list[_Component] = Field(default_factory=list)
    pins: list[_Pin] = Field(default_factory=list)
    wire_endpoints: list[_Endpoint] = Field(default_factory=list)
    connections: list[_Connection] = Field(default_factory=list)
    notes: str = ""
    simulated: bool = False


def _load_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise PerceptionOutputError("Provider output is not valid JSON.") from exc
    elif isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PerceptionOutputError("Provider output is not valid JSON.") from exc
    if not isinstance(raw, dict):
        raise PerceptionOutputError("Provider output must be a JSON object.")
    forbidden = {"verdict", "experiment_state", "pass", "warning", "deviation"}
    if forbidden.intersection(raw):
        raise PerceptionOutputError("Provider output must contain observations, not a verification verdict.")
    return raw


def _allowed_labels(experiment: Experiment) -> tuple[set[str], set[str]]:
    components = {name.lower() for name in experiment.components}
    pins = {pin.lower() for connection in experiment.connections for pin in (
        connection.from_pin, connection.to_pin
    )}
    pins.update({f"a{i}" for i in range(6)})
    return components, pins


def _normalise_unknown(value: Optional[str]) -> Optional[str]:
    if value is None or value.strip().lower() in {"", "unknown", "unresolved", "none"}:
        return None
    return value.strip()


def parse_perception_output(
    raw: Any,
    experiment: Experiment,
    *,
    backend_used: str,
) -> VisualObservation:
    """Validate and normalize provider JSON without making a verdict."""
    payload = _load_payload(raw)
    try:
        parsed = _ProviderOutput.model_validate(payload)
    except ValidationError as exc:
        raise PerceptionOutputError(str(exc)) from exc

    allowed_components, allowed_pins = _allowed_labels(experiment)
    components: list[DetectedComponent] = []
    detected_components: list[str] = []
    for component in parsed.components:
        if component.label.lower() not in allowed_components:
            raise PerceptionOutputError(f"Unknown component label: {component.label}")
        box = None
        if component.bounding_box:
            box = BoundingBox(
                label=component.label,
                x=component.bounding_box.x,
                y=component.bounding_box.y,
                w=component.bounding_box.w,
                h=component.bounding_box.h,
                confidence=component.bounding_box.confidence,
                status=component.bounding_box.status.value.lower(),
            )
        components.append(DetectedComponent(
            label=component.label,
            confidence=component.confidence,
            bounding_box=box,
            status=component.status,
        ))
        if component.status == EvidenceStatus.OBSERVED:
            detected_components.append(component.label)

    pins: list[DetectedPin] = []
    for pin in parsed.pins:
        if pin.component_label.lower() not in allowed_components:
            raise PerceptionOutputError(f"Unknown pin component: {pin.component_label}")
        if pin.pin_label.lower() not in allowed_pins:
            raise PerceptionOutputError(f"Unknown pin label: {pin.pin_label}")
        pins.append(DetectedPin(
            component_label=pin.component_label,
            pin_label=pin.pin_label,
            position=pin.position,
            confidence=pin.confidence,
            status=pin.status,
        ))

    endpoints = [WireEndpoint(**endpoint.model_dump()) for endpoint in parsed.wire_endpoints]
    endpoint_ids = {endpoint.wire_id for endpoint in endpoints}
    connections: list[DetectedConnection] = []
    seen: set[tuple[str, str, Optional[str], Optional[str]]] = set()
    for connection in parsed.connections:
        if connection.from_component.lower() not in allowed_components:
            raise PerceptionOutputError(f"Unknown connection source: {connection.from_component}")
        if connection.from_pin.lower() not in allowed_pins:
            raise PerceptionOutputError(f"Unknown connection source pin: {connection.from_pin}")
        to_component = _normalise_unknown(connection.to_component)
        to_pin = _normalise_unknown(connection.to_pin)
        if to_component is not None and to_component.lower() not in allowed_components:
            raise PerceptionOutputError(f"Unknown connection target: {to_component}")
        if to_pin is not None and to_pin.lower() not in allowed_pins:
            raise PerceptionOutputError(f"Unknown connection target pin: {to_pin}")
        if connection.wire_id is not None and connection.wire_id not in endpoint_ids:
            raise PerceptionOutputError(f"Connection references unknown wire endpoint: {connection.wire_id}")
        if to_component is None or to_pin is None:
            if connection.status in {EvidenceStatus.OBSERVED, EvidenceStatus.INFERRED}:
                status = EvidenceStatus.UNCERTAIN
            else:
                status = connection.status
        else:
            status = connection.status
        key = (connection.from_component.lower(), connection.from_pin.lower(),
               to_component.lower() if to_component else None,
               to_pin.lower() if to_pin else None)
        if key in seen:
            raise PerceptionOutputError("Duplicate connection claim.")
        seen.add(key)
        connections.append(DetectedConnection(
            from_component=connection.from_component,
            from_pin=connection.from_pin,
            to_component=to_component,
            to_pin=to_pin,
            confidence=connection.confidence,
            status=status,
        ))

    return VisualObservation(
        sufficient_evidence=parsed.sufficient_evidence,
        detected_components=detected_components,
        component_observations=components,
        detected_pins=pins,
        wire_endpoints=endpoints,
        detected_connections=connections,
        notes=parsed.notes,
        backend_used=backend_used,
        simulated=parsed.simulated,
        frame_quality=parsed.frame_quality,
    )
