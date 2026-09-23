"""
Demo / Simulation service.

Provides the deterministic DEMO MODE required for presenting ANVEṢHA
without physical hardware or a webcam attached to the judging machine.
Every value produced here is explicitly tagged `simulated=True`. This
module is never used silently by the production `/verify` path — it is
only invoked through the separate `/api/demo/*` endpoints, so a judge
(or code reviewer) can see exactly where real inference stops and
scripted demonstration data begins.

Implements the four required scenarios:
  DEMO 1 - correct circuit                      -> PASS
  DEMO 2 - incorrect connection                  -> DEVIATION (connection)
  DEMO 3 - incorrect measurement                  -> DEVIATION (measurement)
  DEMO 4 - procedure/document mismatch (missing)  -> INSUFFICIENT_EVIDENCE
"""
from __future__ import annotations

from datetime import datetime, timezone

from backend.schemas.models import DetectedConnection, SensorReading, VisualObservation

DEMO_SCENARIOS = {
    "demo_1_correct": {
        "experiment_id": "ldr_001",
        "description": "Correct LDR circuit, wired exactly per procedure, normal indoor light.",
        "visual": VisualObservation(
            sufficient_evidence=True,
            detected_components=["Arduino", "LDR", "resistor_10k", "breadboard", "jumper_wires"],
            detected_connections=[
                DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A0", confidence=0.93),
                DetectedConnection(from_component="LDR", from_pin="VCC", to_component="Arduino", to_pin="5V", confidence=0.88),
                DetectedConnection(from_component="resistor_10k", from_pin="1", to_component="LDR", to_pin="OUT", confidence=0.81),
                DetectedConnection(from_component="resistor_10k", from_pin="2", to_component="Arduino", to_pin="GND", confidence=0.85),
            ],
            notes="[SIMULATED] Scripted demo frame: correctly wired LDR divider.",
            backend_used="demo-simulation",
            simulated=True,
        ),
        "readings": [SensorReading(sensor="LDR", value=512, unit="ADC", source="simulated", simulated=True, timestamp=datetime.now(timezone.utc))],
    },
    "demo_2_wrong_connection": {
        "experiment_id": "ldr_001",
        "description": "LDR output wired to A1 instead of A0 — the flagship 'wrong pin' demo.",
        "visual": VisualObservation(
            sufficient_evidence=True,
            detected_components=["Arduino", "LDR", "resistor_10k", "breadboard", "jumper_wires"],
            detected_connections=[
                DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A1", confidence=0.90),
                DetectedConnection(from_component="LDR", from_pin="VCC", to_component="Arduino", to_pin="5V", confidence=0.88),
                DetectedConnection(from_component="resistor_10k", from_pin="1", to_component="LDR", to_pin="OUT", confidence=0.80),
                DetectedConnection(from_component="resistor_10k", from_pin="2", to_component="Arduino", to_pin="GND", confidence=0.85),
            ],
            notes="[SIMULATED] Scripted demo frame: LDR OUT connected to A1 instead of A0.",
            backend_used="demo-simulation",
            simulated=True,
        ),
        "readings": [SensorReading(sensor="LDR", value=505, unit="ADC", source="simulated", simulated=True, timestamp=datetime.now(timezone.utc))],
    },
    "demo_2b_corrected": {
        "experiment_id": "ldr_001",
        "description": "Same setup as demo_2, after the user moves the wire back to A0 and re-verifies.",
        "visual": VisualObservation(
            sufficient_evidence=True,
            detected_components=["Arduino", "LDR", "resistor_10k", "breadboard", "jumper_wires"],
            detected_connections=[
                DetectedConnection(from_component="LDR", from_pin="OUT", to_component="Arduino", to_pin="A0", confidence=0.94),
                DetectedConnection(from_component="LDR", from_pin="VCC", to_component="Arduino", to_pin="5V", confidence=0.88),
                DetectedConnection(from_component="resistor_10k", from_pin="1", to_component="LDR", to_pin="OUT", confidence=0.83),
                DetectedConnection(from_component="resistor_10k", from_pin="2", to_component="Arduino", to_pin="GND", confidence=0.85),
            ],
            notes="[SIMULATED] Scripted demo frame: connection corrected to A0.",
            backend_used="demo-simulation",
            simulated=True,
        ),
        "readings": [SensorReading(sensor="LDR", value=498, unit="ADC", source="simulated", simulated=True, timestamp=datetime.now(timezone.utc))],
    },
    "demo_3_bad_measurement": {
        "experiment_id": "ultrasonic_001",
        "description": "Wiring is correct but the reported distance is out of the sensor's valid range.",
        "visual": VisualObservation(
            sufficient_evidence=True,
            detected_components=["Arduino", "HC-SR04", "breadboard", "jumper_wires"],
            detected_connections=[
                DetectedConnection(from_component="HC-SR04", from_pin="VCC", to_component="Arduino", to_pin="5V", confidence=0.9),
                DetectedConnection(from_component="HC-SR04", from_pin="TRIG", to_component="Arduino", to_pin="D9", confidence=0.87),
                DetectedConnection(from_component="HC-SR04", from_pin="ECHO", to_component="Arduino", to_pin="D10", confidence=0.86),
                DetectedConnection(from_component="HC-SR04", from_pin="GND", to_component="Arduino", to_pin="GND", confidence=0.9),
            ],
            notes="[SIMULATED] Scripted demo frame: wiring correct, but sensor reports an out-of-range distance.",
            backend_used="demo-simulation",
            simulated=True,
        ),
        "readings": [SensorReading(sensor="HC-SR04", value=650, unit="cm", source="simulated", simulated=True, timestamp=datetime.now(timezone.utc))],
    },
    "demo_4_insufficient_evidence": {
        "experiment_id": "led_001",
        "description": "Camera frame is too blurry/poorly lit to verify the LED circuit at all.",
        "visual": VisualObservation(
            sufficient_evidence=False,
            detected_components=[],
            detected_connections=[],
            notes="[SIMULATED] Scripted demo frame: frame too blurry/underexposed to identify components.",
            backend_used="demo-simulation",
            simulated=True,
        ),
        "readings": [],
    },
}


def get_scenario(name: str) -> dict:
    if name not in DEMO_SCENARIOS:
        raise KeyError(f"Unknown demo scenario: {name}. Available: {list(DEMO_SCENARIOS.keys())}")
    return DEMO_SCENARIOS[name]


def list_scenarios() -> list[dict]:
    return [{"id": k, "experiment_id": v["experiment_id"], "description": v["description"]} for k, v in DEMO_SCENARIOS.items()]
