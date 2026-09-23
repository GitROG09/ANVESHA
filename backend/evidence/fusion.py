"""
Evidence Fusion — combines raw perception and telemetry into structured,
per-claim evidence, before any verdict is decided.

This module answers "what do we actually know, and how sure are we,
about each individual thing the experiment cares about?" It does NOT
decide PASS/WARNING/DEVIATION — that is the verification engine's job
(backend/verification/engine.py), which consumes the EvidenceBundle this
module produces and applies deterministic pass/fail rules to it.

Inputs fused here:
  - vision:      VisualObservation (detected components/connections,
                  frame quality)
  - telemetry:   SensorReading list (real Arduino or simulated, always
                  tagged)
  - the experiment specification (what SHOULD be true)

Every output item is a StructuredEvidence record carrying an
EvidenceStatus (OBSERVED / INFERRED / UNCERTAIN / OCCLUDED / MISSING).
Nothing here ever upgrades a MISSING or UNCERTAIN item into an OBSERVED
one just because it matches what the experiment expects — that would be
exactly the "model opinion instead of evidence" failure mode ANVEṢHA
exists to avoid. A wrong-but-confidently-observed connection is reported
as OBSERVED with its actual (wrong) target; the verification engine is
what turns that into a DEVIATION.
"""
from __future__ import annotations

from backend.schemas.models import (
    DetectedConnection,
    EvidenceBundle,
    EvidenceStatus,
    Experiment,
    SensorReading,
    StructuredEvidence,
    VisualObservation,
)

# Below this, a detected connection is too shaky to trust as OBSERVED in
# either direction (correct or wrong) — it becomes UNCERTAIN instead.
MIN_CONNECTION_CONFIDENCE = 0.55


def _norm(component: str, pin: str) -> str:
    return f"{component.strip().lower()}::{pin.strip().lower()}"


def _find_best_match(
    expected_from: str,
    expected_from_pin: str,
    detected: list[DetectedConnection],
) -> DetectedConnection | None:
    """Find the detected connection most likely describing the same wire."""
    key = _norm(expected_from, expected_from_pin)
    candidates = [d for d in detected if _norm(d.from_component, d.from_pin) == key]
    if not candidates:
        return None
    return max(candidates, key=lambda d: d.confidence)


def _is_occluded(component: str, observation: VisualObservation) -> bool:
    """True only if the backend explicitly flagged this component as occluded.

    We never infer occlusion from absence alone — absence with no
    supporting signal is MISSING, not OCCLUDED. Claiming OCCLUDED without
    positive evidence would itself be a small fabrication.
    """
    comp_lower = component.strip().lower()
    return any(
        bb.label.strip().lower() == comp_lower and bb.status == "occluded"
        for bb in observation.bounding_boxes
    )


def _fuse_connection_evidence(
    experiment: Experiment, observation: VisualObservation
) -> list[StructuredEvidence]:
    items: list[StructuredEvidence] = []

    for conn in experiment.connections:
        subject = f"{conn.from_component} {conn.from_pin} -> {conn.to_component} {conn.to_pin}"
        expected = f"{conn.to_component} {conn.to_pin}"
        match = _find_best_match(conn.from_component, conn.from_pin, observation.detected_connections)

        if match is None:
            status = EvidenceStatus.OCCLUDED if _is_occluded(conn.from_component, observation) else EvidenceStatus.MISSING
            items.append(
                StructuredEvidence(
                    subject=subject,
                    relationship="connection",
                    expected=expected,
                    observed=None,
                    status=status,
                    confidence=None,
                    source="vision",
                )
            )
            continue

        observed = f"{match.to_component} {match.to_pin}"

        if match.status == EvidenceStatus.INFERRED:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    relationship="connection",
                    expected=expected,
                    observed=observed,
                    status=EvidenceStatus.INFERRED,
                    confidence=match.confidence,
                    source="vision",
                )
            )
            continue

        if match.confidence < MIN_CONNECTION_CONFIDENCE:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    relationship="connection",
                    expected=expected,
                    observed=observed,
                    status=EvidenceStatus.UNCERTAIN,
                    confidence=match.confidence,
                    source="vision",
                )
            )
            continue

        # Confident, direct observation — report it as-is, whether or not
        # it matches what was expected. Matching expectations is the
        # verification engine's decision, not evidence fusion's.
        items.append(
            StructuredEvidence(
                subject=subject,
                relationship="connection",
                expected=expected,
                observed=observed,
                status=EvidenceStatus.OBSERVED,
                confidence=match.confidence,
                source="vision",
            )
        )

    return items


def _fuse_component_evidence(
    experiment: Experiment, observation: VisualObservation
) -> list[StructuredEvidence]:
    items: list[StructuredEvidence] = []
    detected_lower = {d.lower() for d in observation.detected_components}

    for component in experiment.components:
        subject = component
        expected = f"{component} present on breadboard"
        if component.lower() in detected_lower:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    relationship="component",
                    expected=expected,
                    observed=component,
                    status=EvidenceStatus.OBSERVED,
                    confidence=None,
                    source="vision",
                )
            )
        else:
            status = EvidenceStatus.OCCLUDED if _is_occluded(component, observation) else EvidenceStatus.MISSING
            items.append(
                StructuredEvidence(
                    subject=subject,
                    relationship="component",
                    expected=expected,
                    observed=None,
                    status=status,
                    confidence=None,
                    source="vision",
                )
            )

    return items


def _fuse_measurement_evidence(
    experiment: Experiment, readings: list[SensorReading]
) -> list[StructuredEvidence]:
    items: list[StructuredEvidence] = []

    latest_by_sensor: dict[str, SensorReading] = {}
    for r in readings:
        existing = latest_by_sensor.get(r.sensor)
        if existing is None or r.timestamp >= existing.timestamp:
            latest_by_sensor[r.sensor] = r

    for expected_measurement in experiment.expected_measurements:
        subject = f"{expected_measurement.sensor} measurement"
        expected = f"{expected_measurement.min_value}-{expected_measurement.max_value} {expected_measurement.unit}"
        reading = latest_by_sensor.get(expected_measurement.sensor)

        if reading is None:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    relationship="measurement",
                    expected=expected,
                    observed=None,
                    status=EvidenceStatus.MISSING,
                    confidence=None,
                    source="telemetry",
                )
            )
            continue

        sim_tag = " (SIMULATED)" if reading.simulated else ""
        items.append(
            StructuredEvidence(
                subject=subject,
                relationship="measurement",
                expected=expected,
                observed=f"{reading.value} {reading.unit}{sim_tag}",
                # A raw sensor reading is a direct observation, not a
                # perception judgement call — it has no separate
                # "confidence" of its own; whether it satisfies the
                # experiment is a verification-time range check.
                status=EvidenceStatus.OBSERVED,
                confidence=None,
                source="telemetry",
            )
        )

    return items


def fuse_evidence(
    experiment: Experiment,
    observation: VisualObservation | None,
    readings: list[SensorReading],
) -> EvidenceBundle:
    """Combine vision + telemetry + the experiment spec into structured evidence.

    Returns an EvidenceBundle. If the frame itself was not suitable for
    perception (or no frame was provided at all), the bundle carries no
    structured evidence — there is nothing trustworthy to fuse — and
    frame_suitable=False signals the verification engine to report
    INSUFFICIENT_EVIDENCE outright, rather than silently treating "no
    evidence" as "nothing wrong".
    """
    frame_suitable = observation is not None and observation.sufficient_evidence
    frame_quality = observation.frame_quality if observation is not None else None
    simulated = bool(observation and observation.simulated) or any(r.simulated for r in readings)

    if not frame_suitable:
        return EvidenceBundle(
            experiment_id=experiment.experiment_id,
            frame_suitable=False,
            frame_quality=frame_quality,
            structured_evidence=[],
            simulated=simulated,
        )

    structured_evidence: list[StructuredEvidence] = []
    structured_evidence += _fuse_connection_evidence(experiment, observation)
    structured_evidence += _fuse_component_evidence(experiment, observation)
    structured_evidence += _fuse_measurement_evidence(experiment, readings)

    return EvidenceBundle(
        experiment_id=experiment.experiment_id,
        frame_suitable=True,
        frame_quality=frame_quality,
        structured_evidence=structured_evidence,
        simulated=simulated,
    )
