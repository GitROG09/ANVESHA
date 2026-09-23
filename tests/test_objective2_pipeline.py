from backend.experiments.engine import DEFAULT_EXPERIMENTS_DIR, ExperimentEngine
from backend.inference.fixture_provider import FixtureVisionBackend
from backend.schemas.models import SensorReading, VisualObservation
from backend.verification.engine import verify


experiment = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR).get("ldr_001")


def _full_connections(target_pin="A0"):
    return [
        {"from_component": "LDR", "from_pin": "OUT", "to_component": "Arduino", "to_pin": target_pin, "confidence": 0.95},
        {"from_component": "LDR", "from_pin": "VCC", "to_component": "Arduino", "to_pin": "5V", "confidence": 0.95},
        {"from_component": "resistor_10k", "from_pin": "1", "to_component": "LDR", "to_pin": "OUT", "confidence": 0.95},
        {"from_component": "resistor_10k", "from_pin": "2", "to_component": "Arduino", "to_pin": "GND", "confidence": 0.95},
    ]


def _payload(connections=None, components=None):
    return {
        "sufficient_evidence": True,
        "frame_quality": 0.9,
        "components": components or [
            {"label": name, "confidence": 0.95, "status": "OBSERVED"}
            for name in ["Arduino", "LDR", "resistor_10k", "breadboard", "jumper_wires"]
        ],
        "connections": _full_connections() if connections is None else connections,
    }


def _reading():
    return [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True)]


def test_fixture_provider_correct_a0_reaches_pass_through_real_pipeline():
    observation = FixtureVisionBackend(_payload()).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state == "PASS"


def test_fixture_provider_wrong_a1_reaches_deviation():
    observation = FixtureVisionBackend(_payload(connections=_full_connections("A1"))).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state == "DEVIATION"


def test_connection_comparison_is_case_insensitive_but_preserves_display_value():
    connections = _full_connections()
    connections[0]["to_component"] = "arduino"
    connections[0]["to_pin"] = "a0"
    observation = FixtureVisionBackend(_payload(connections=connections)).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state == "PASS"
    assert any("arduino a0" in item.summary for item in result.evidence)


def test_case_insensitive_comparison_does_not_hide_wrong_pin():
    connections = _full_connections("A1")
    connections[0]["to_component"] = "arduino"
    connections[0]["to_pin"] = "a1"
    observation = FixtureVisionBackend(_payload(connections=connections)).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state == "DEVIATION"


def test_unknown_endpoint_cannot_produce_pass():
    connections = _full_connections()
    connections[0] = {
        "from_component": "LDR", "from_pin": "OUT", "to_component": None,
        "to_pin": None, "confidence": 0.4, "status": "UNCERTAIN",
    }
    observation = FixtureVisionBackend(_payload(connections=connections)).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state != "PASS"
    assert any("Low-confidence" in step.observed for step in result.warnings)


def test_explicit_missing_component_is_rule_backed():
    components = [{"label": "LDR", "confidence": 0.9, "status": "MISSING"}]
    observation = FixtureVisionBackend(_payload(components=components)).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state == "DEVIATION"
    assert any(step.step_id == "component_LDR" for step in result.failed_steps)


def test_uncertain_component_is_warning_not_definite_deviation():
    components = [{"label": "LDR", "confidence": 0.4, "status": "UNCERTAIN"}] + [
        {"label": name, "confidence": 0.9, "status": "OBSERVED"}
        for name in ["Arduino", "resistor_10k", "breadboard", "jumper_wires"]
    ]
    observation = FixtureVisionBackend(_payload(components=components)).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state == "WARNING"
    assert any(step.step_id == "component_LDR" for step in result.warnings)
    assert not any(step.step_id == "component_LDR" for step in result.failed_steps)


def test_occluded_component_is_warning_not_definite_deviation():
    components = [{"label": "LDR", "confidence": 0.6, "status": "OCCLUDED"}] + [
        {"label": name, "confidence": 0.9, "status": "OBSERVED"}
        for name in ["Arduino", "resistor_10k", "breadboard", "jumper_wires"]
    ]
    observation = FixtureVisionBackend(_payload(components=components)).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state == "WARNING"
    assert any(step.step_id == "component_LDR" for step in result.warnings)


def test_warning_connection_rule_does_not_become_deviation():
    connections = _full_connections()
    connections[1]["to_pin"] = "GND"
    observation = FixtureVisionBackend(_payload(connections=connections)).analyze(b"fixture", experiment)
    result = verify(experiment, observation, _reading())
    assert result.experiment_state == "WARNING"
    assert not any(step.title.startswith("LDR VCC") for step in result.failed_steps)


def test_warning_measurement_rule_does_not_become_deviation():
    warning_experiment = experiment.model_copy(deep=True)
    for rule in warning_experiment.validation_rules:
        if rule.rule_id == "r_measurement_range":
            rule.severity = "warning"
    observation = FixtureVisionBackend(_payload()).analyze(b"fixture", warning_experiment)
    result = verify(warning_experiment, observation, [SensorReading(sensor="LDR", value=999, unit="ADC")])
    assert result.experiment_state == "WARNING"
    assert any(step.step_id == "measure_LDR" for step in result.warnings)


def test_fallback_observation_remains_non_perceptual():
    observation = VisualObservation(
        sufficient_evidence=True,
        detected_components=[],
        detected_connections=[],
        backend_used="fallback-cpu-opencv",
        simulated=False,
    )
    result = verify(experiment, observation, _reading())
    assert result.experiment_state != "PASS"
