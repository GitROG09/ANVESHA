from backend.experiments.engine import ExperimentEngine, DEFAULT_EXPERIMENTS_DIR
from backend.evidence.fusion import fuse_evidence
from backend.schemas.models import (
    BoundingBox,
    DetectedConnection,
    EvidenceStatus,
    ExperimentState,
    SensorReading,
    VisualObservation,
)
from backend.verification.engine import verify

engine = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR)


def _ldr_experiment():
    return engine.get("ldr_001")


def _base_connections(**overrides):
    conns = [
        DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A0", confidence=0.9),
        DetectedConnection(from_component="LDR", from_pin="VCC", to_component="Arduino", to_pin="5V", confidence=0.9),
        DetectedConnection(from_component="resistor_10k", from_pin="1", to_component="LDR", to_pin="OUT", confidence=0.9),
        DetectedConnection(from_component="resistor_10k", from_pin="2", to_component="Arduino", to_pin="GND", confidence=0.9),
    ]
    return conns


def _full_observation(**kwargs):
    defaults = dict(
        sufficient_evidence=True,
        detected_components=["Arduino", "LDR", "resistor_10k", "breadboard", "jumper_wires"],
        detected_connections=_base_connections(),
        notes="test frame",
        backend_used="test",
        frame_quality=0.9,
    )
    defaults.update(kwargs)
    return VisualObservation(**defaults)


# ---------------------------------------------------------------------------
# Structured evidence: status classification
# ---------------------------------------------------------------------------


def test_observed_evidence_for_correct_connection():
    exp = _ldr_experiment()
    obs = _full_observation()
    bundle = fuse_evidence(exp, obs, [])
    conn = next(e for e in bundle.structured_evidence if e.subject.startswith("LDR OUT"))
    assert conn.status == EvidenceStatus.OBSERVED
    assert conn.observed == "Arduino A0"
    assert conn.confidence == 0.9


def test_observed_evidence_for_wrong_connection_is_not_upgraded():
    """A confidently-observed WRONG connection stays OBSERVED, never silently fixed."""
    exp = _ldr_experiment()
    connections = _base_connections()
    connections[0] = DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A1", confidence=0.9)
    obs = _full_observation(detected_connections=connections)
    bundle = fuse_evidence(exp, obs, [])
    conn = next(e for e in bundle.structured_evidence if e.subject.startswith("LDR OUT"))
    assert conn.status == EvidenceStatus.OBSERVED
    assert conn.observed == "Arduino A1"
    assert conn.expected == "Arduino A0"


def test_missing_evidence_when_connection_never_detected():
    exp = _ldr_experiment()
    connections = _base_connections()[1:]  # drop LDR OUT -> A0 entirely
    obs = _full_observation(detected_connections=connections)
    bundle = fuse_evidence(exp, obs, [])
    conn = next(e for e in bundle.structured_evidence if e.subject.startswith("LDR OUT"))
    assert conn.status == EvidenceStatus.MISSING
    assert conn.observed is None
    assert conn.confidence is None


def test_uncertain_evidence_below_confidence_floor():
    exp = _ldr_experiment()
    connections = _base_connections()
    connections[0] = DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A0", confidence=0.3)
    obs = _full_observation(detected_connections=connections)
    bundle = fuse_evidence(exp, obs, [])
    conn = next(e for e in bundle.structured_evidence if e.subject.startswith("LDR OUT"))
    assert conn.status == EvidenceStatus.UNCERTAIN
    assert conn.confidence == 0.3


def test_inferred_evidence_status_propagates():
    exp = _ldr_experiment()
    connections = _base_connections()
    connections[0] = DetectedConnection(
        from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A0",
        confidence=0.7, status=EvidenceStatus.INFERRED,
    )
    obs = _full_observation(detected_connections=connections)
    bundle = fuse_evidence(exp, obs, [])
    conn = next(e for e in bundle.structured_evidence if e.subject.startswith("LDR OUT"))
    assert conn.status == EvidenceStatus.INFERRED


def test_occluded_evidence_requires_explicit_signal():
    exp = _ldr_experiment()
    connections = _base_connections()[1:]  # LDR OUT -> A0 not detected
    obs = _full_observation(
        detected_connections=connections,
        bounding_boxes=[BoundingBox(label="LDR", x=0, y=0, w=10, h=10, confidence=0.5, status="occluded")],
    )
    bundle = fuse_evidence(exp, obs, [])
    conn = next(e for e in bundle.structured_evidence if e.subject.startswith("LDR OUT"))
    assert conn.status == EvidenceStatus.OCCLUDED


def test_absence_alone_is_missing_not_occluded():
    """No bounding-box signal at all -> MISSING, never inferred as OCCLUDED."""
    exp = _ldr_experiment()
    connections = _base_connections()[1:]
    obs = _full_observation(detected_connections=connections)
    bundle = fuse_evidence(exp, obs, [])
    conn = next(e for e in bundle.structured_evidence if e.subject.startswith("LDR OUT"))
    assert conn.status == EvidenceStatus.MISSING


def test_image_quality_is_not_connection_confidence():
    """frame_quality and per-connection confidence are tracked independently."""
    exp = _ldr_experiment()
    obs = _full_observation(frame_quality=0.92)
    bundle = fuse_evidence(exp, obs, [])
    assert bundle.frame_quality == 0.92
    conn = next(e for e in bundle.structured_evidence if e.subject.startswith("LDR OUT"))
    assert conn.confidence == 0.9  # independent value, not copied from frame_quality


def test_missing_measurement_evidence():
    exp = _ldr_experiment()
    bundle = fuse_evidence(exp, _full_observation(), [])
    meas = next(e for e in bundle.structured_evidence if e.relationship == "measurement")
    assert meas.status == EvidenceStatus.MISSING


def test_observed_measurement_evidence():
    exp = _ldr_experiment()
    reading = [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]
    bundle = fuse_evidence(exp, _full_observation(), reading)
    meas = next(e for e in bundle.structured_evidence if e.relationship == "measurement")
    assert meas.status == EvidenceStatus.OBSERVED
    assert "512" in meas.observed


def test_low_quality_frame_produces_no_structured_evidence():
    exp = _ldr_experiment()
    obs = VisualObservation(sufficient_evidence=False, notes="too blurry", backend_used="test", frame_quality=0.1)
    bundle = fuse_evidence(exp, obs, [])
    assert bundle.frame_suitable is False
    assert bundle.structured_evidence == []
    assert bundle.frame_quality == 0.1


# ---------------------------------------------------------------------------
# Verification engine: consumes structured evidence via fusion
# ---------------------------------------------------------------------------


def test_verification_insufficient_evidence_when_only_uncertain():
    exp = _ldr_experiment()
    connections = [DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A0", confidence=0.2)]
    obs = _full_observation(detected_connections=connections)
    result = verify(exp, obs, [])
    # No verified steps at all, only warnings -> INSUFFICIENT_EVIDENCE
    assert result.experiment_state == ExperimentState.INSUFFICIENT_EVIDENCE


def test_verification_conflicting_evidence_is_deviation_not_pass():
    """One firm wrong connection must produce DEVIATION even if other evidence is fine."""
    exp = _ldr_experiment()
    connections = _base_connections()
    connections[0] = DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A1", confidence=0.95)
    obs = _full_observation(detected_connections=connections)
    readings = [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]
    result = verify(exp, obs, readings)
    assert result.experiment_state == ExperimentState.DEVIATION
    assert len(result.failed_steps) == 1


def test_verification_occluded_connection_produces_warning():
    exp = _ldr_experiment()
    connections = _base_connections()[1:]
    obs = _full_observation(
        detected_connections=connections,
        bounding_boxes=[BoundingBox(label="LDR", x=0, y=0, w=10, h=10, confidence=0.5, status="occluded")],
    )
    readings = [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]
    result = verify(exp, obs, readings)
    assert any("Occluded" in s.observed for s in result.warnings)


def test_verification_never_fabricates_pass_from_missing_evidence():
    """With every connection MISSING and no measurement, the engine must not claim PASS."""
    exp = _ldr_experiment()
    obs = _full_observation(detected_connections=[], detected_components=[])
    result = verify(exp, obs, [])
    assert result.experiment_state != ExperimentState.PASS


def test_verification_state_transition_deviation_to_pass():
    exp = _ldr_experiment()
    readings = [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]

    wrong = _base_connections()
    wrong[0] = DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A1", confidence=0.9)
    before = verify(exp, _full_observation(detected_connections=wrong), readings)
    assert before.experiment_state == ExperimentState.DEVIATION

    after = verify(exp, _full_observation(), readings)
    assert after.experiment_state == ExperimentState.PASS
