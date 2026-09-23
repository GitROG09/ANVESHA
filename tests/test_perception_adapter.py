import pytest

from backend.experiments.engine import DEFAULT_EXPERIMENTS_DIR, ExperimentEngine
from backend.inference.perception_adapter import PerceptionOutputError, parse_perception_output
from backend.schemas.models import EvidenceStatus


experiment = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR).get("ldr_001")


def _payload(**overrides):
    payload = {
        "sufficient_evidence": True,
        "frame_quality": 0.9,
        "components": [
            {"label": "LDR", "confidence": 0.95, "status": "OBSERVED"},
            {"label": "Arduino", "confidence": 0.95, "status": "OBSERVED"},
        ],
        "pins": [{
            "component_label": "LDR", "pin_label": "OUT",
            "position": {"x": 0.2, "y": 0.3}, "confidence": 0.8,
        }],
        "wire_endpoints": [],
        "connections": [{
            "from_component": "LDR", "from_pin": "OUT",
            "to_component": "Arduino", "to_pin": "A0",
            "confidence": 0.91, "status": "OBSERVED",
        }],
    }
    payload.update(overrides)
    return payload


def test_adapter_preserves_correct_connection_and_structured_entities():
    observation = parse_perception_output(_payload(), experiment, backend_used="test-provider")
    assert observation.backend_used == "test-provider"
    assert observation.detected_components == ["LDR", "Arduino"]
    assert observation.detected_pins[0].pin_label == "OUT"
    assert observation.detected_connections[0].to_pin == "A0"
    assert observation.detected_connections[0].status == EvidenceStatus.OBSERVED


def test_unknown_endpoint_becomes_uncertain_without_guessing():
    observation = parse_perception_output(_payload(connections=[{
        "from_component": "LDR", "from_pin": "OUT", "to_component": "unknown",
        "to_pin": "unknown", "confidence": 0.9, "status": "OBSERVED",
    }]), experiment, backend_used="test-provider")
    connection = observation.detected_connections[0]
    assert connection.to_component is None
    assert connection.to_pin is None
    assert connection.status == EvidenceStatus.UNCERTAIN


@pytest.mark.parametrize("payload_change", [
    {"verdict": "PASS"},
    {"connections": [{
        "from_component": "LDR", "from_pin": "OUT", "to_component": "Arduino",
        "to_pin": "A0", "confidence": 1.2,
    }]},
    {"components": [{"label": "Camera", "confidence": 0.9}]},
    {"pins": [{"component_label": "LDR", "pin_label": "bad", "position": {"x": 0.1, "y": 0.1}, "confidence": 0.9}]},
    {"pins": [{"component_label": "LDR", "pin_label": "OUT", "position": {"x": 2, "y": 0.1}, "confidence": 0.9}]},
    {"components": [{"label": "LDR", "confidence": 0.9, "bounding_box": {"x": 0.8, "y": 0.1, "w": 0.4, "h": 0.2, "confidence": 0.9}}]},
])
def test_adapter_rejects_untrusted_provider_output(payload_change):
    payload = _payload()
    payload.update(payload_change)
    with pytest.raises(PerceptionOutputError):
        parse_perception_output(payload, experiment, backend_used="test-provider")


def test_adapter_rejects_duplicate_connections():
    connection = _payload()["connections"][0]
    with pytest.raises(PerceptionOutputError):
        parse_perception_output(_payload(connections=[connection, connection]), experiment, backend_used="test-provider")


def test_adapter_preserves_occlusion_and_uncertainty():
    observation = parse_perception_output(_payload(
        components=[{"label": "LDR", "confidence": 0.4, "status": "OCCLUDED"}],
        connections=[{
            "from_component": "LDR", "from_pin": "OUT", "to_component": "Arduino",
            "to_pin": "A0", "confidence": 0.4, "status": "UNCERTAIN",
        }],
    ), experiment, backend_used="test-provider")
    assert observation.component_observations[0].status == EvidenceStatus.OCCLUDED
    assert observation.detected_connections[0].status == EvidenceStatus.UNCERTAIN
