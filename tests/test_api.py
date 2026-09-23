from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_runtime_status():
    r = client.get("/api/runtime")
    assert r.status_code == 200
    body = r.json()
    assert body["active_backend"] in ("qualcomm-npu", "cpu-fallback")
    assert "vision_backend" in body


def test_list_experiments():
    r = client.get("/api/experiments")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 3


def test_get_experiment_404():
    r = client.get("/api/experiments/does_not_exist")
    assert r.status_code == 404


def test_demo_scenarios_listed():
    r = client.get("/api/demo/scenarios")
    assert r.status_code == 200
    ids = {s["id"] for s in r.json()}
    assert "demo_1_correct" in ids
    assert "demo_2_wrong_connection" in ids
    assert "demo_3_bad_measurement" in ids
    assert "demo_4_insufficient_evidence" in ids


def test_demo_1_passes():
    r = client.post("/api/demo/demo_1_correct/verify")
    assert r.status_code == 200
    assert r.json()["experiment_state"] == "PASS"


def test_demo_2_deviation_then_corrected():
    r1 = client.post("/api/demo/demo_2_wrong_connection/verify")
    assert r1.json()["experiment_state"] == "DEVIATION"

    r2 = client.post("/api/demo/demo_2b_corrected/verify")
    assert r2.json()["experiment_state"] == "PASS"


def test_demo_3_measurement_deviation():
    r = client.post("/api/demo/demo_3_bad_measurement/verify")
    assert r.json()["experiment_state"] == "DEVIATION"


def test_demo_4_insufficient_evidence():
    r = client.post("/api/demo/demo_4_insufficient_evidence/verify")
    assert r.json()["experiment_state"] == "INSUFFICIENT_EVIDENCE"


def test_verify_endpoint_direct():
    payload = {
        "experiment_id": "ldr_001",
        "visual_observation": {
            "sufficient_evidence": True,
            "detected_components": ["Arduino", "LDR", "resistor_10k"],
            "detected_connections": [
                {"from_component": "LDR", "from_pin": "OUT", "to_component": "Arduino", "to_pin": "A0", "confidence": 0.9},
                {"from_component": "LDR", "from_pin": "VCC", "to_component": "Arduino", "to_pin": "5V", "confidence": 0.9},
                {"from_component": "resistor_10k", "from_pin": "1", "to_component": "LDR", "to_pin": "OUT", "confidence": 0.9},
                {"from_component": "resistor_10k", "from_pin": "2", "to_component": "Arduino", "to_pin": "GND", "confidence": 0.9},
            ],
            "backend_used": "test",
        },
        "sensor_readings": [{"sensor": "LDR", "value": 500, "unit": "ADC", "source": "arduino", "simulated": False}],
    }
    r = client.post("/api/verify", json=payload)
    assert r.status_code == 200
    assert r.json()["experiment_state"] == "PASS"


def test_verify_endpoint_rejects_simulated_telemetry_outside_demo_path():
    r = client.post(
        "/api/verify",
        json={
            "experiment_id": "ldr_001",
            "sensor_readings": [{"sensor": "LDR", "value": 500, "unit": "ADC", "source": "simulated", "simulated": True}],
        },
    )
    assert r.status_code == 400
    assert "explicit /api/demo/*" in r.json()["detail"]
