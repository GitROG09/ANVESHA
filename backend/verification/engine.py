"""
Verification Engine — the heart of ANVEṢHA AI.

This module answers the question the AI perception layer cannot:
"Does what I see satisfy the experiment?"

It is intentionally deterministic and rule-based. The vision/speech models
answer "what do I see / what did you say"; this engine compares that
evidence against the explicit experiment definition and produces a
verdict. Keeping this logic separate from the model calls is what makes
ANVEṢHA's verdicts auditable rather than an LLM's opinion.
"""
from __future__ import annotations

from backend.schemas.models import (
    DetectedConnection,
    Experiment,
    ExperimentState,
    EvidenceItem,
    SensorReading,
    StepResult,
    VerificationResult,
    VisualObservation,
)

# Minimum confidence for a detected connection to be trusted at all.
MIN_CONNECTION_CONFIDENCE = 0.55
# Minimum confidence for a detected connection to count as a firm match/mismatch
# rather than "uncertain".
CONFIDENT_MATCH_THRESHOLD = 0.65


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


def _check_connections(
    experiment: Experiment, observation: VisualObservation
) -> tuple[list[StepResult], list[StepResult], list[StepResult], list[EvidenceItem]]:
    """Compare expected connections against detected connections.

    Returns (verified, failed, warnings, evidence).
    """
    verified: list[StepResult] = []
    failed: list[StepResult] = []
    warnings: list[StepResult] = []
    evidence: list[EvidenceItem] = []

    for conn in experiment.connections:
        step_title = f"{conn.from_component} {conn.from_pin} -> {conn.to_component} {conn.to_pin}"
        match = _find_best_match(conn.from_component, conn.from_pin, observation.detected_connections)

        if match is None:
            warnings.append(
                StepResult(
                    step_id=f"conn_{conn.from_component}_{conn.from_pin}",
                    title=step_title,
                    status="warning",
                    expected=f"{conn.from_component} {conn.from_pin} -> {conn.to_component} {conn.to_pin}",
                    observed="Not detected in current frame",
                    why_it_matters="No visual evidence for this connection was found; it may be out of frame or occluded.",
                    recommended_action=f"Reposition the camera so {conn.from_component} {conn.from_pin} and its wire are clearly visible.",
                )
            )
            continue

        target_matches = (
            match.to_component.strip().lower() == conn.to_component.strip().lower()
            and match.to_pin.strip().lower() == conn.to_pin.strip().lower()
        )

        if match.confidence < MIN_CONNECTION_CONFIDENCE:
            warnings.append(
                StepResult(
                    step_id=f"conn_{conn.from_component}_{conn.from_pin}",
                    title=step_title,
                    status="warning",
                    expected=f"{conn.to_component} {conn.to_pin}",
                    observed=f"Low-confidence detection ({match.confidence:.0%})",
                    why_it_matters="Visual confidence is too low to trust this connection either way.",
                    recommended_action="Move the camera closer or improve lighting, then verify again.",
                )
            )
            continue

        if target_matches:
            verified.append(
                StepResult(
                    step_id=f"conn_{conn.from_component}_{conn.from_pin}",
                    title=step_title,
                    status="verified",
                    expected=f"{conn.to_component} {conn.to_pin}",
                    observed=f"{match.to_component} {match.to_pin}",
                )
            )
            evidence.append(
                EvidenceItem(source="vision", summary=f"Confirmed {step_title} (confidence {match.confidence:.0%})")
            )
        else:
            failed.append(
                StepResult(
                    step_id=f"conn_{conn.from_component}_{conn.from_pin}",
                    title=step_title,
                    status="failed",
                    expected=f"{conn.to_component} {conn.to_pin}",
                    observed=f"{match.to_component} {match.to_pin}",
                    why_it_matters=f"The experiment procedure expects {conn.from_component} {conn.from_pin} to reach "
                    f"{conn.to_component} {conn.to_pin}, but the camera shows it going to {match.to_component} {match.to_pin} instead.",
                    recommended_action=f"Move the {conn.from_component} {conn.from_pin} connection to {conn.to_component} {conn.to_pin}.",
                )
            )
            evidence.append(
                EvidenceItem(
                    source="vision",
                    summary=f"Deviation: {conn.from_component} {conn.from_pin} observed at "
                    f"{match.to_component} {match.to_pin}, expected {conn.to_component} {conn.to_pin}.",
                )
            )

    return verified, failed, warnings, evidence


def _check_measurements(
    experiment: Experiment, readings: list[SensorReading]
) -> tuple[list[StepResult], list[StepResult], list[StepResult], list[EvidenceItem]]:
    verified: list[StepResult] = []
    failed: list[StepResult] = []
    warnings: list[StepResult] = []
    evidence: list[EvidenceItem] = []

    readings_by_sensor: dict[str, SensorReading] = {}
    for r in readings:
        # keep the most recent reading per sensor
        existing = readings_by_sensor.get(r.sensor)
        if existing is None or r.timestamp >= existing.timestamp:
            readings_by_sensor[r.sensor] = r

    for expected in experiment.expected_measurements:
        step_id = f"measure_{expected.sensor}"
        title = f"{expected.sensor} measurement"
        reading = readings_by_sensor.get(expected.sensor)

        if reading is None:
            warnings.append(
                StepResult(
                    step_id=step_id,
                    title=title,
                    status="warning",
                    expected=f"{expected.min_value}-{expected.max_value} {expected.unit}",
                    observed="No reading available",
                    why_it_matters="Verification cannot confirm the electrical behavior without a measurement.",
                    recommended_action="Connect the sensor/telemetry link or enable simulation mode, then verify again.",
                )
            )
            continue

        in_range = expected.min_value <= reading.value <= expected.max_value
        sim_tag = " (SIMULATED)" if reading.simulated else ""
        if in_range:
            verified.append(
                StepResult(
                    step_id=step_id,
                    title=title,
                    status="verified",
                    expected=f"{expected.min_value}-{expected.max_value} {expected.unit}",
                    observed=f"{reading.value} {reading.unit}{sim_tag}",
                )
            )
            evidence.append(
                EvidenceItem(
                    source="telemetry",
                    summary=f"{expected.sensor} reading {reading.value} {reading.unit} is within expected range{sim_tag}.",
                )
            )
        else:
            failed.append(
                StepResult(
                    step_id=step_id,
                    title=title,
                    status="failed",
                    expected=f"{expected.min_value}-{expected.max_value} {expected.unit}",
                    observed=f"{reading.value} {reading.unit}{sim_tag}",
                    why_it_matters=f"{expected.description or 'The measurement is outside the expected operating range.'}",
                    recommended_action="Recheck wiring and component values, then take a new reading.",
                )
            )
            evidence.append(
                EvidenceItem(
                    source="telemetry",
                    summary=f"{expected.sensor} reading {reading.value} {reading.unit} is OUTSIDE expected range "
                    f"[{expected.min_value}, {expected.max_value}]{sim_tag}.",
                )
            )

    return verified, failed, warnings, evidence


def _compute_confidence(
    observation: VisualObservation | None,
    verified_count: int,
    failed_count: int,
    warning_count: int,
) -> float:
    total = verified_count + failed_count + warning_count
    if total == 0:
        return 0.0
    base = (verified_count + 0.5 * warning_count) / total
    # Penalize if the underlying visual evidence itself was weak.
    if observation is not None and not observation.sufficient_evidence:
        base *= 0.5
    return round(min(max(base, 0.0), 1.0), 2)


def verify(
    experiment: Experiment,
    observation: VisualObservation | None,
    readings: list[SensorReading],
) -> VerificationResult:
    """Fuse visual evidence + sensor telemetry against an experiment definition."""

    # Guard clause: no usable visual evidence at all.
    if observation is None or not observation.sufficient_evidence:
        return VerificationResult(
            experiment_id=experiment.experiment_id,
            experiment_state=ExperimentState.INSUFFICIENT_EVIDENCE,
            confidence=0.0,
            observations=[observation.notes] if observation and observation.notes else [
                "No visual evidence was provided or the frame did not contain a usable view of the setup."
            ],
            recommended_actions=[
                "Reposition the camera so all components and wires are clearly visible.",
                "Ensure adequate, even lighting on the breadboard.",
            ],
        )

    conn_verified, conn_failed, conn_warnings, conn_evidence = _check_connections(experiment, observation)
    meas_verified, meas_failed, meas_warnings, meas_evidence = _check_measurements(experiment, readings)

    verified_steps = conn_verified + meas_verified
    failed_steps = conn_failed + meas_failed
    warning_steps = conn_warnings + meas_warnings
    evidence = conn_evidence + meas_evidence

    # Any component present-in-procedure but never even attempted to detect
    missing_components = [c for c in experiment.components if c.lower() not in [d.lower() for d in observation.detected_components]]
    for mc in missing_components:
        evidence.append(EvidenceItem(source="vision", summary=f"Component '{mc}' was not identified in the frame."))

    if failed_steps:
        state = ExperimentState.DEVIATION
    elif warning_steps and not verified_steps:
        state = ExperimentState.INSUFFICIENT_EVIDENCE
    elif warning_steps:
        state = ExperimentState.WARNING
    else:
        state = ExperimentState.PASS

    confidence = _compute_confidence(observation, len(verified_steps), len(failed_steps), len(warning_steps))

    return VerificationResult(
        experiment_id=experiment.experiment_id,
        experiment_state=state,
        confidence=confidence,
        verified_steps=verified_steps,
        failed_steps=failed_steps,
        warnings=warning_steps,
        observations=[observation.notes] if observation.notes else [],
        expected=[f"{c.from_component} {c.from_pin} -> {c.to_component} {c.to_pin}" for c in experiment.connections],
        observed=[f"{d.from_component} {d.from_pin} -> {d.to_component} {d.to_pin} ({d.confidence:.0%})" for d in observation.detected_connections],
        recommended_actions=[s.recommended_action for s in failed_steps if s.recommended_action]
        + [s.recommended_action for s in warning_steps if s.recommended_action],
        evidence=evidence,
    )
