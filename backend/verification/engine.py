"""
Verification Engine — the heart of ANVEṢHA AI.

This module answers the question the AI perception layer cannot:
"Does what I see satisfy the experiment?"

It is intentionally deterministic and rule-based, and deliberately thin:
all the work of figuring out what was actually observed lives in
`backend/evidence/fusion.py`. This engine's only job is to take the
resulting StructuredEvidence and apply fixed rules — never model
opinion — to reach PASS / WARNING / DEVIATION / INSUFFICIENT_EVIDENCE.
Keeping this separate from the model calls is what makes ANVEṢHA's
verdicts auditable rather than an LLM's opinion.

Evidence status -> outcome mapping (per connection/measurement claim):
  OBSERVED, matches expectation      -> verified
  OBSERVED, does NOT match           -> failed / deviation
  INFERRED                            -> warning (not directly observed)
  UNCERTAIN                           -> warning (confidence too low to trust)
  OCCLUDED                            -> warning (known to be blocked from view)
  MISSING                             -> warning (no evidence at all)

Component-level evidence is informational only (it never blocks a PASS
on its own) — it becomes plain evidence-log entries rather than
verified/failed/warning steps, matching how the experiment specs use
connections and measurements, not raw component presence, as the actual
pass/fail criteria.
"""
from __future__ import annotations

from backend.evidence.fusion import fuse_evidence
from backend.schemas.models import (
    Experiment,
    EvidenceItem,
    EvidenceStatus,
    SensorReading,
    StepResult,
    StructuredEvidence,
    VerificationResult,
    ExperimentState,
    VisualObservation,
)


def _normalised_endpoint(value: str | None) -> str:
    """Normalize an endpoint for comparison while retaining raw display text."""
    return " ".join((value or "").strip().lower().split())


def _is_definite_failure(item: StructuredEvidence) -> bool:
    """Only definite, observed contradictions can become rule failures."""
    return item.status == EvidenceStatus.OBSERVED and item.severity == "deviation"


def _rollup_connections(evidence: list[StructuredEvidence]) -> tuple[list[StepResult], list[StepResult], list[StepResult], list[EvidenceItem]]:
    verified: list[StepResult] = []
    failed: list[StepResult] = []
    warnings: list[StepResult] = []
    evidence_log: list[EvidenceItem] = []

    for item in [e for e in evidence if e.relationship == "connection"]:
        step_id = "conn_" + item.subject.split(" -> ")[0].replace(" ", "_")

        if item.status == EvidenceStatus.OBSERVED:
            if _normalised_endpoint(item.observed) == _normalised_endpoint(item.expected):
                verified.append(
                    StepResult(
                        step_id=step_id,
                        title=item.subject,
                        status="verified",
                        expected=item.expected,
                        observed=item.observed or "",
                    )
                )
                evidence_log.append(
                    EvidenceItem(
                        source="vision",
                        summary=f"Confirmed {item.subject}: observed {item.observed} (confidence {item.confidence:.0%}).",
                    )
                )
            elif _is_definite_failure(item):
                failed.append(
                    StepResult(
                        step_id=step_id,
                        title=item.subject,
                        status="failed",
                        expected=item.expected,
                        observed=item.observed or "",
                        why_it_matters=(
                            f"The experiment procedure expects {item.expected}, but the camera shows it going to "
                            f"{item.observed} instead."
                        ),
                        recommended_action=f"Move the {item.subject.split(' -> ')[0]} connection to {item.expected}.",
                    )
                )
                evidence_log.append(
                    EvidenceItem(
                        source="vision",
                        summary=f"Deviation: {item.subject.split(' -> ')[0]} observed at {item.observed}, expected {item.expected}.",
                    )
                )
            else:
                warnings.append(
                    StepResult(
                        step_id=step_id,
                        title=item.subject,
                        status="warning",
                        expected=item.expected,
                        observed=item.observed or "",
                        why_it_matters="The observed connection does not satisfy the procedure, but this rule is advisory.",
                        recommended_action=f"Review the {item.subject.split(' -> ')[0]} connection against {item.expected}.",
                    )
                )
                evidence_log.append(
                    EvidenceItem(
                        source="vision",
                        summary=f"Warning: {item.subject.split(' -> ')[0]} observed at {item.observed}, expected {item.expected}.",
                    )
                )
            continue

        if item.status == EvidenceStatus.UNCERTAIN:
            warnings.append(
                StepResult(
                    step_id=step_id,
                    title=item.subject,
                    status="warning",
                    expected=item.expected,
                    observed=f"Low-confidence detection ({item.confidence:.0%})" if item.confidence is not None else "Low-confidence detection",
                    why_it_matters="Visual confidence is too low to trust this connection either way.",
                    recommended_action="Move the camera closer or improve lighting, then verify again.",
                )
            )
            continue

        if item.status == EvidenceStatus.INFERRED:
            warnings.append(
                StepResult(
                    step_id=step_id,
                    title=item.subject,
                    status="warning",
                    expected=item.expected,
                    observed=f"Inferred (not directly observed): {item.observed}" if item.observed else "Inferred, not directly observed",
                    why_it_matters="This connection was inferred from surrounding context, not directly seen.",
                    recommended_action="Capture a frame that shows this wire and pin directly.",
                )
            )
            continue

        if item.status == EvidenceStatus.OCCLUDED:
            warnings.append(
                StepResult(
                    step_id=step_id,
                    title=item.subject,
                    status="warning",
                    expected=item.expected,
                    observed="Occluded — component partially blocked from view",
                    why_it_matters="Part of the setup is blocked from the camera's view, so this connection cannot be confirmed.",
                    recommended_action="Remove obstructions or reposition the camera for a clear view.",
                )
            )
            continue

        # MISSING
        warnings.append(
            StepResult(
                step_id=step_id,
                title=item.subject,
                status="warning",
                expected=item.expected,
                observed="Not detected in current frame",
                why_it_matters="No visual evidence for this connection was found; it may be out of frame or occluded.",
                recommended_action=f"Reposition the camera so {item.subject.split(' -> ')[0]} and its wire are clearly visible.",
            )
        )

    return verified, failed, warnings, evidence_log


def _rollup_measurements(evidence: list[StructuredEvidence]) -> tuple[list[StepResult], list[StepResult], list[StepResult], list[EvidenceItem]]:
    verified: list[StepResult] = []
    failed: list[StepResult] = []
    warnings: list[StepResult] = []
    evidence_log: list[EvidenceItem] = []

    for item in [e for e in evidence if e.relationship == "measurement"]:
        sensor = item.subject.replace(" measurement", "")
        step_id = f"measure_{sensor}"

        if item.status == EvidenceStatus.MISSING:
            warnings.append(
                StepResult(
                    step_id=step_id,
                    title=item.subject,
                    status="warning",
                    expected=item.expected,
                    observed="No reading available",
                    why_it_matters="Verification cannot confirm the electrical behavior without a measurement.",
                    recommended_action="Connect the sensor/telemetry link or enable simulation mode, then verify again.",
                )
            )
            continue

        # OBSERVED: range-check the raw value against the experiment spec.
        min_v, max_v = (float(x) for x in item.expected.split(" ")[0].split("-"))
        try:
            value = float(item.observed.split(" ")[0]) if item.observed else None
        except ValueError:
            value = None

        in_range = value is not None and min_v <= value <= max_v
        if in_range:
            verified.append(
                StepResult(step_id=step_id, title=item.subject, status="verified", expected=item.expected, observed=item.observed or "")
            )
            evidence_log.append(
                EvidenceItem(source="telemetry", summary=f"{sensor} reading {item.observed} is within expected range.")
            )
        elif item.severity == "deviation":
            failed.append(
                StepResult(
                    step_id=step_id,
                    title=item.subject,
                    status="failed",
                    expected=item.expected,
                    observed=item.observed or "",
                    why_it_matters="The measurement is outside the expected operating range.",
                    recommended_action="Recheck wiring and component values, then take a new reading.",
                )
            )
            evidence_log.append(
                EvidenceItem(
                    source="telemetry",
                    summary=f"{sensor} reading {item.observed} is OUTSIDE expected range [{item.expected}].",
                )
            )
        else:
            warnings.append(
                StepResult(
                    step_id=step_id,
                    title=item.subject,
                    status="warning",
                    expected=item.expected,
                    observed=item.observed or "",
                    why_it_matters="The measurement is outside the expected range, but this rule is advisory.",
                    recommended_action="Recheck wiring and component values, then take a new reading.",
                )
            )
            evidence_log.append(
                EvidenceItem(
                    source="telemetry",
                    summary=f"Warning: {sensor} reading {item.observed} is outside expected range [{item.expected}].",
                )
            )

    return verified, failed, warnings, evidence_log


def _component_evidence_log(evidence: list[StructuredEvidence]) -> list[EvidenceItem]:
    """Keep component observations visible; rule severity controls missing claims."""
    log: list[EvidenceItem] = []
    for item in [e for e in evidence if e.relationship == "component"]:
        if item.status != EvidenceStatus.OBSERVED:
            log.append(EvidenceItem(source="vision", summary=f"Component '{item.subject}' was not identified in the frame."))
    return log


def _rollup_components(evidence: list[StructuredEvidence]) -> tuple[list[StepResult], list[StepResult], list[EvidenceItem]]:
    failed: list[StepResult] = []
    warnings: list[StepResult] = []
    evidence_log: list[EvidenceItem] = []
    for item in [e for e in evidence if e.relationship == "component" and e.status != EvidenceStatus.OBSERVED and e.severity]:
        is_definite_missing = item.status == EvidenceStatus.MISSING
        step = StepResult(
            step_id=f"component_{item.subject}",
            title=item.subject,
            status="failed" if is_definite_missing and item.severity == "deviation" else "warning",
            expected=item.expected,
            observed=("Occluded" if item.status == EvidenceStatus.OCCLUDED else item.status.value.title()),
            why_it_matters="The required component could not be confirmed in the frame.",
            recommended_action="Reposition the camera and ensure the component is visible.",
        )
        if is_definite_missing and item.severity == "deviation":
            failed.append(step)
        else:
            warnings.append(step)
        evidence_log.append(EvidenceItem(source="vision", summary=f"Component '{item.subject}' status: {item.status.value}."))
    return failed, warnings, evidence_log


def _compute_confidence(
    frame_suitable: bool,
    verified_count: int,
    failed_count: int,
    warning_count: int,
) -> float:
    """Verification certainty — how confident the ROLLUP is, not a perception score.

    Deliberately distinct from image quality (frame_suitable/frame_quality)
    and from any individual connection's detection confidence; this number
    only reflects how much of the required evidence came back verified.
    """
    total = verified_count + failed_count + warning_count
    if total == 0:
        return 0.0
    base = (verified_count + 0.5 * warning_count) / total
    if not frame_suitable:
        base *= 0.5
    return round(min(max(base, 0.0), 1.0), 2)


def verify(
    experiment: Experiment,
    observation: VisualObservation | None,
    readings: list[SensorReading],
) -> VerificationResult:
    """Fuse visual evidence + sensor telemetry against an experiment definition."""

    bundle = fuse_evidence(experiment, observation, readings)

    if not bundle.frame_suitable:
        # Required visual wiring evidence is unavailable, so the overall
        # result must stay INSUFFICIENT_EVIDENCE — telemetry can never
        # compensate for missing connection evidence. But telemetry is an
        # independent evidence source: any measurement evidence fusion
        # already collected (real or simulated) must still be surfaced
        # here, not silently dropped just because the camera failed.
        meas_verified, meas_failed, meas_warnings, meas_evidence = _rollup_measurements(bundle.structured_evidence)
        observations = [observation.notes] if observation and observation.notes else [
            "No visual evidence was provided or the frame did not contain a usable view of the setup."
        ]
        return VerificationResult(
            experiment_id=experiment.experiment_id,
            experiment_state=ExperimentState.INSUFFICIENT_EVIDENCE,
            confidence=0.0,
            verified_steps=meas_verified,
            failed_steps=meas_failed,
            warnings=meas_warnings,
            observations=observations,
            recommended_actions=[
                "Reposition the camera so all components and wires are clearly visible.",
                "Ensure adequate, even lighting on the breadboard.",
            ]
            + [s.recommended_action for s in meas_failed if s.recommended_action]
            + [s.recommended_action for s in meas_warnings if s.recommended_action],
            evidence=meas_evidence,
        )

    conn_verified, conn_failed, conn_warnings, conn_evidence = _rollup_connections(bundle.structured_evidence)
    meas_verified, meas_failed, meas_warnings, meas_evidence = _rollup_measurements(bundle.structured_evidence)
    component_evidence = _component_evidence_log(bundle.structured_evidence)
    component_failed, component_warnings, component_log = _rollup_components(bundle.structured_evidence)

    verified_steps = conn_verified + meas_verified
    failed_steps = conn_failed + meas_failed + component_failed
    warning_steps = conn_warnings + meas_warnings + component_warnings
    evidence = conn_evidence + meas_evidence + component_evidence + component_log

    if failed_steps:
        state = ExperimentState.DEVIATION
    elif warning_steps and not verified_steps:
        state = ExperimentState.INSUFFICIENT_EVIDENCE
    elif warning_steps:
        state = ExperimentState.WARNING
    else:
        state = ExperimentState.PASS

    confidence = _compute_confidence(bundle.frame_suitable, len(verified_steps), len(failed_steps), len(warning_steps))

    conn_items = [e for e in bundle.structured_evidence if e.relationship == "connection"]

    return VerificationResult(
        experiment_id=experiment.experiment_id,
        experiment_state=state,
        confidence=confidence,
        verified_steps=verified_steps,
        failed_steps=failed_steps,
        warnings=warning_steps,
        observations=[observation.notes] if observation and observation.notes else [],
        expected=[item.expected for item in conn_items],
        observed=[
            f"{item.observed} ({item.confidence:.0%})" if item.confidence is not None and item.observed else (item.observed or "not observed")
            for item in conn_items
        ],
        recommended_actions=[s.recommended_action for s in failed_steps if s.recommended_action]
        + [s.recommended_action for s in warning_steps if s.recommended_action],
        evidence=evidence,
    )
