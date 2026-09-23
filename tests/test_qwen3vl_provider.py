import pytest

from backend.experiments.engine import DEFAULT_EXPERIMENTS_DIR, ExperimentEngine
from backend.inference.perception_adapter import PerceptionOutputError
from backend.inference.qwen3vl_provider import (
    QWEN3VL_MODEL_ID,
    Qwen3VLProviderUnavailable,
    Qwen3VLVisionProvider,
)
from backend.schemas.models import SensorReading
from backend.verification.engine import verify


experiment = ExperimentEngine(DEFAULT_EXPERIMENTS_DIR).get("ldr_001")
provider = Qwen3VLVisionProvider()


def _response(**overrides):
    response = {
        "sufficient_evidence": True,
        "frame_quality": 0.9,
        "components": [
            {"label": label, "confidence": 0.95, "status": "OBSERVED"}
            for label in ["Arduino", "LDR", "resistor_10k", "breadboard", "jumper_wires"]
        ],
        "pins": [],
        "wire_endpoints": [],
        "connections": [
            {"from_component": "LDR", "from_pin": "OUT", "to_component": "Arduino", "to_pin": "A0", "confidence": 0.95},
            {"from_component": "LDR", "from_pin": "VCC", "to_component": "Arduino", "to_pin": "5V", "confidence": 0.95},
            {"from_component": "resistor_10k", "from_pin": "1", "to_component": "LDR", "to_pin": "OUT", "confidence": 0.95},
            {"from_component": "resistor_10k", "from_pin": "2", "to_component": "Arduino", "to_pin": "GND", "confidence": 0.95},
        ],
        "notes": "mock structured response; not model inference",
    }
    response.update(overrides)
    return response


def test_provider_is_lazy_and_unavailable_without_local_weights():
    assert provider.model_id == QWEN3VL_MODEL_ID
    assert provider.is_available() is False
    with pytest.raises(Qwen3VLProviderUnavailable, match="weights unavailable"):
        provider.analyze(b"not-an-image", experiment)


def test_prompt_requests_observations_not_verdicts():
    prompt = provider.structured_prompt(experiment)
    assert "verdict" in prompt
    assert "visual-evidence schema" in prompt
    assert "LDR OUT" in prompt


def test_valid_qwen_style_response_is_accepted():
    observation = provider.observation_from_response(_response(), experiment)
    assert observation.backend_used == provider.name
    assert observation.detected_connections[0].to_pin == "A0"


@pytest.mark.parametrize("bad_response", [
    "{not-json",
    {**_response(), "verdict": "PASS"},
    {**_response(), "components": [{"label": "UnknownPart", "confidence": 0.9}]},
    {**_response(), "connections": [{**_response()["connections"][0], "confidence": 1.1}]},
    {**_response(), "components": [{"label": "LDR", "confidence": 0.9, "bounding_box": {"x": 0.8, "y": 0.1, "w": 0.4, "h": 0.2, "confidence": 0.9}}]},
    {**_response(), "connections": [_response()["connections"][0], _response()["connections"][0]]},
])
def test_invalid_qwen_style_responses_are_rejected(bad_response):
    with pytest.raises(PerceptionOutputError):
        provider.observation_from_response(bad_response, experiment)


def test_unknown_endpoint_is_preserved_as_uncertain():
    response = _response(connections=[{
        "from_component": "LDR",
        "from_pin": "OUT",
        "to_component": "unknown",
        "to_pin": "unknown",
        "confidence": 0.4,
    }])
    observation = provider.observation_from_response(response, experiment)
    connection = observation.detected_connections[0]
    assert connection.to_component is None
    assert connection.to_pin is None
    assert connection.status.value == "UNCERTAIN"


def test_mock_qwen_response_flows_through_existing_pipeline():
    """Contract/integration test only; this does not measure Qwen inference."""
    observation = provider.observation_from_response(_response(), experiment)
    result = verify(
        experiment,
        observation,
        [SensorReading(sensor="LDR", value=512, unit="ADC", simulated=True, source="simulated")],
    )
    assert result.experiment_state == "PASS"
    assert observation.backend_used == "qwen3vl-local"
