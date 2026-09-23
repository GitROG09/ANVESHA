from backend.experiments.engine import ExperimentEngine, DEFAULT_EXPERIMENTS_DIR
from backend.schemas.models import DetectedConnection, ExperimentState, SensorReading, VisualObservation
from backend.verification.engine import verify

engine = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR)


def _ldr_experiment():
    return engine.get("ldr_001")


def _correct_observation():
    return VisualObservation(
        sufficient_evidence=True,
        detected_components=["Arduino", "LDR", "resistor_10k", "breadboard", "jumper_wires"],
        detected_connections=[
            DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A0", confidence=0.9),
            DetectedConnection(from_component="LDR", from_pin="VCC", to_component="Arduino", to_pin="5V", confidence=0.9),
            DetectedConnection(from_component="resistor_10k", from_pin="1", to_component="LDR", to_pin="OUT", confidence=0.9),
            DetectedConnection(from_component="resistor_10k", from_pin="2", to_component="Arduino", to_pin="GND", confidence=0.9),
        ],
        notes="test frame",
        backend_used="test",
    )


def test_pass_case():
    exp = _ldr_experiment()
    obs = _correct_observation()
    readings = [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]
    result = verify(exp, obs, readings)
    assert result.experiment_state == ExperimentState.PASS
    assert result.confidence > 0.8
    assert len(result.failed_steps) == 0


def test_deviation_case_wrong_pin():
    exp = _ldr_experiment()
    obs = _correct_observation()
    # Corrupt the OUT->A0 connection to OUT->A1
    obs.detected_connections[0] = DetectedConnection(
        from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A1", confidence=0.9
    )
    readings = [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]
    result = verify(exp, obs, readings)
    assert result.experiment_state == ExperimentState.DEVIATION
    assert len(result.failed_steps) == 1
    failed = result.failed_steps[0]
    assert "A0" in failed.expected
    assert "A1" in failed.observed


def test_deviation_case_measurement_out_of_range():
    exp = _ldr_experiment()
    obs = _correct_observation()
    readings = [SensorReading(sensor="LDR", value=999, unit="ADC", source="simulated", simulated=True)]
    result = verify(exp, obs, readings)
    assert result.experiment_state == ExperimentState.DEVIATION
    assert any(s.step_id == "measure_LDR" for s in result.failed_steps)


def test_insufficient_evidence_no_observation():
    exp = _ldr_experiment()
    result = verify(exp, None, [])
    assert result.experiment_state == ExperimentState.INSUFFICIENT_EVIDENCE
    assert result.confidence == 0.0


def test_insufficient_evidence_flagged_observation():
    exp = _ldr_experiment()
    obs = VisualObservation(sufficient_evidence=False, notes="too blurry", backend_used="test")
    result = verify(exp, obs, [])
    assert result.experiment_state == ExperimentState.INSUFFICIENT_EVIDENCE


def test_missing_connection_produces_warning_not_silent_pass():
    exp = _ldr_experiment()
    obs = _correct_observation()
    # remove one detected connection entirely (out of frame)
    obs.detected_connections = obs.detected_connections[1:]
    readings = [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]
    result = verify(exp, obs, readings)
    assert len(result.warnings) >= 1
    assert result.experiment_state in (ExperimentState.WARNING, ExperimentState.PASS, ExperimentState.INSUFFICIENT_EVIDENCE)


def test_before_after_correction_transition():
    """Simulates the core demo: DEVIATION -> user fixes wire -> VERIFIED."""
    exp = _ldr_experiment()

    # BEFORE: wrong pin
    before_obs = _correct_observation()
    before_obs.detected_connections[0] = DetectedConnection(
        from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A1", confidence=0.9
    )
    readings = [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]
    before_result = verify(exp, before_obs, readings)
    assert before_result.experiment_state == ExperimentState.DEVIATION

    # AFTER: corrected
    after_obs = _correct_observation()
    after_result = verify(exp, after_obs, readings)
    assert after_result.experiment_state == ExperimentState.PASS
