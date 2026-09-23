# Experiment Engine

`backend/experiments/engine.py` loads experiment definitions from
`experiments/*.json` into validated Pydantic models
(`backend/schemas/models.py::Experiment`). This is plain data loading — no AI.

## Schema

```json
{
  "experiment_id": "ldr_001",
  "title": "LDR Light Sensor Calibration",
  "objective": "...",
  "difficulty": "beginner",
  "safety_notes": ["..."],
  "components": ["Arduino", "LDR", "resistor_10k", "breadboard", "jumper_wires"],
  "connections": [
    { "from": "LDR", "from_pin": "OUT", "to": "Arduino", "to_pin": "A0" }
  ],
  "steps": [
    { "step_id": "s1", "title": "...", "instruction": "...", "checks": ["r_ldr_to_a0"] }
  ],
  "expected_measurements": [
    { "sensor": "LDR", "unit": "ADC", "min_value": 200, "max_value": 800, "description": "..." }
  ],
  "validation_rules": [
    { "rule_id": "r_ldr_to_a0", "description": "...", "rule_type": "connection", "target": "LDR->Arduino", "severity": "deviation" }
  ],
  "troubleshooting": { "reading_always_0": "..." }
}
```

Note: `from_pin`/`to_pin` must be distinct JSON keys — an earlier draft of
these files used a duplicate `"pin"` key inside the same connection object,
which is invalid JSON-as-data (the second value silently overwrote the
first). This was caught by `tests/test_experiment_engine.py` and fixed; see
`docs/limitations.md` for the note.

## Currently supported experiments

| id | title | components |
|---|---|---|
| `ldr_001` | LDR Light Sensor Calibration | Arduino, LDR, 10k resistor, breadboard |
| `ultrasonic_001` | HC-SR04 Ultrasonic Distance Measurement | Arduino, HC-SR04, breadboard |
| `led_001` | LED Current-Limiting Resistor Circuit | Arduino, LED, 220Ω resistor, breadboard |

All three are low-voltage (5V logic), low-risk, and chosen specifically
because their expected connections and measurement ranges are easy to state
unambiguously — which matters for a system that must not guess.

## Adding a new experiment

1. Add a new `experiments/<name>.json` file following the schema above.
2. Run `pytest tests/test_experiment_engine.py` — it iterates over every
   file in the directory and validates the schema, so a malformed file
   fails CI immediately.
3. No code changes are required elsewhere: the API, verification engine,
   and frontend all discover experiments dynamically via
   `GET /api/experiments`.

## Loading procedures from PDFs / lab-sheet images (future work)

The project brief calls for optional PDF/image procedure upload in addition
to built-in experiments. This snapshot implements the built-in JSON path
only; PDF/image ingestion would parse an uploaded document into the same
`Experiment` schema (likely via the vision backend for image-based sheets,
or a text-extraction step for PDFs) rather than bypassing it — so the
verification engine never has to know whether an experiment definition came
from a built-in file or an uploaded document. See `docs/limitations.md`.
