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


def _connection_rule(
    experiment: Experiment,
    from_component: str,
    from_pin: str,
    to_component: str,
    to_pin: str,
) -> tuple[str | None, str | None]:
    power_pins = {"vcc", "5v", "gnd", "ground"}
    if from_pin.strip().lower() in power_pins or to_pin.strip().lower() in power_pins:
        for rule in experiment.validation_rules:
            if rule.rule_type == "connection" and rule.target and rule.target.lower() == "power":
                return rule.rule_id, rule.severity
    target = f"{from_component}->{to_component}".lower()
    for rule in experiment.validation_rules:
        if rule.rule_type == "connection" and rule.target and rule.target.lower() == target:
            return rule.rule_id, rule.severity
    return None, None


def _component_rule(experiment: Experiment) -> tuple[str | None, str | None]:
    for rule in experiment.validation_rules:
        if rule.rule_type == "connection" and rule.target and rule.target.lower() == "components":
            return rule.rule_id, rule.severity
    return None, None


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
        rule_id, severity = _connection_rule(
            experiment,
            conn.from_component,
            conn.from_pin,
            conn.to_component,
            conn.to_pin,
        )
        match = _find_best_match(conn.from_component, conn.from_pin, observation.detected_connections)

        if match is None:
            status = EvidenceStatus.OCCLUDED if _is_occluded(conn.from_component, observation) else EvidenceStatus.MISSING
            items.append(
                StructuredEvidence(
                    subject=subject,
                    rule_id=rule_id,
                    relationship="connection",
                    expected=expected,
                    observed=None,
                    status=status,
                    confidence=None,
                    source="vision",
                    severity=severity,
                )
            )
            continue

        if match.to_component is None or match.to_pin is None:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    rule_id=rule_id,
                    relationship="connection",
                    expected=expected,
                    observed=None,
                    status=EvidenceStatus.UNCERTAIN,
                    confidence=match.confidence,
                    source="vision",
                    severity=severity,
                )
            )
            continue

        observed = f"{match.to_component} {match.to_pin}"

        if match.status == EvidenceStatus.INFERRED:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    rule_id=rule_id,
                    relationship="connection",
                    expected=expected,
                    observed=observed,
                    status=EvidenceStatus.INFERRED,
                    confidence=match.confidence,
                    source="vision",
                    severity=severity,
                )
            )
            continue

        if match.status in {EvidenceStatus.UNCERTAIN, EvidenceStatus.OCCLUDED, EvidenceStatus.MISSING}:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    rule_id=rule_id,
                    relationship="connection",
                    expected=expected,
                    observed=observed,
                    status=match.status,
                    confidence=match.confidence,
                    source="vision",
                    severity=severity,
                )
            )
            continue

        if match.confidence < MIN_CONNECTION_CONFIDENCE:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    rule_id=rule_id,
                    relationship="connection",
                    expected=expected,
                    observed=observed,
                    status=EvidenceStatus.UNCERTAIN,
                    confidence=match.confidence,
                    source="vision",
                    severity=severity,
                )
            )
            continue

        # Confident, direct observation — report it as-is, whether or not
        # it matches what was expected. Matching expectations is the
        # verification engine's decision, not evidence fusion's.
        items.append(
            StructuredEvidence(
                subject=subject,
                rule_id=rule_id,
                relationship="connection",
                expected=expected,
                observed=observed,
                status=EvidenceStatus.OBSERVED,
                confidence=match.confidence,
                source="vision",
                severity=severity,
            )
        )

    return items


def _fuse_component_evidence(
    experiment: Experiment, observation: VisualObservation
) -> list[StructuredEvidence]:
    items: list[StructuredEvidence] = []
    rule_id, severity = _component_rule(experiment)
    structured = {d.label.lower(): d for d in observation.component_observations}
    detected_lower = {d.lower() for d in observation.detected_components}
    structured_component_mode = bool(observation.component_observations)

    for component in experiment.components:
        subject = component
        expected = f"{component} present on breadboard"
        detected = structured.get(component.lower())
        if detected is not None:
            status = detected.status
            observed = component if status == EvidenceStatus.OBSERVED else None
            confidence = detected.confidence
        elif component.lower() in detected_lower:
            status = EvidenceStatus.OBSERVED
            observed = component
            confidence = None
        else:
            status = EvidenceStatus.OCCLUDED if _is_occluded(component, observation) else EvidenceStatus.MISSING
            observed = None
            confidence = None

        if status == EvidenceStatus.OBSERVED:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    rule_id=rule_id,
                    relationship="component",
                    expected=expected,
                    observed=observed,
                    status=status,
                    confidence=confidence,
                    source="vision",
                    severity=severity if structured_component_mode else None,
                )
            )
        else:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    rule_id=rule_id,
                    relationship="component",
                    expected=expected,
                    observed=None,
                    status=status,
                    confidence=confidence,
                    source="vision",
                    severity=severity if structured_component_mode else None,
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
        measurement_rule = next(
            (rule for rule in experiment.validation_rules if rule.rule_type == "measurement" and rule.target == expected_measurement.sensor),
            None,
        )
        reading = latest_by_sensor.get(expected_measurement.sensor)

        if reading is None:
            items.append(
                StructuredEvidence(
                    subject=subject,
                    rule_id=measurement_rule.rule_id if measurement_rule else None,
                    relationship="measurement",
                    expected=expected,
                    observed=None,
                    status=EvidenceStatus.MISSING,
                    confidence=None,
                    source="telemetry",
                    severity=measurement_rule.severity if measurement_rule else None,
                )
            )
            continue

        sim_tag = " (SIMULATED)" if reading.simulated else ""
        items.append(
            StructuredEvidence(
                subject=subject,
                rule_id=measurement_rule.rule_id if measurement_rule else None,
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
                severity=measurement_rule.severity if measurement_rule else None,
            )
        )

    return items


def fuse_evidence(
    experiment: Experiment,
    observation: VisualObservation | None,
    readings: list[SensorReading],
) -> EvidenceBundle:
    """Combine vision + telemetry + the experiment spec into structured evidence.

    Visual evidence (connections, components) REQUIRES a usable frame — if
    the frame itself was not suitable for perception (or no frame was
    provided at all), no connection/component evidence is fused, since
    there is nothing trustworthy to report there.

    Telemetry is a separate evidence source with its own provenance and is
    NOT gated on frame quality: a bad or missing camera frame must not
    discard a real (or explicitly simulated) sensor reading. The bundle
    always carries whatever measurement evidence exists, tagged
    accordingly, alongside frame_suitable/frame_quality so the
    verification engine can still correctly report INSUFFICIENT_EVIDENCE
    when the required visual wiring evidence is unavailable — telemetry on
    its own can never compensate for that, but it must remain visible in
    the evidence bundle and downstream evidence log rather than being
    silently discarded.
    """
    frame_suitable = observation is not None and observation.sufficient_evidence
    frame_quality = observation.frame_quality if observation is not None else None
    simulated = bool(observation and observation.simulated) or any(r.simulated for r in readings)

    structured_evidence: list[StructuredEvidence] = []

    # Telemetry evidence does not depend on the camera at all — fuse it
    # regardless of frame_suitable.
    structured_evidence += _fuse_measurement_evidence(experiment, readings)

    if frame_suitable:
        structured_evidence += _fuse_connection_evidence(experiment, observation)
        structured_evidence += _fuse_component_evidence(experiment, observation)

    return EvidenceBundle(
        experiment_id=experiment.experiment_id,
        frame_suitable=frame_suitable,
        frame_quality=frame_quality,
        structured_evidence=structured_evidence,
        simulated=simulated,
    )
