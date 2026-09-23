# Architecture

## Overview

ANVEṢHA AI is split into three layers that are deliberately kept independent:

1. **Experiment Engine** — deterministic, data-driven. Loads `experiments/*.json`
   into validated Pydantic models. No AI involved.
2. **Inference Layer** — answers "what do I see / what did you say." Vision and
   speech backends behind a common interface (`backend/inference/base/`), with
   concrete implementations in `fallback/` (CPU, runs anywhere) and `qualcomm/`
   (Snapdragon NPU via Qualcomm AI Hub).
3. **Verification Engine** — answers "does what I see satisfy the experiment."
   Deterministic rule evaluation that fuses vision output + sensor telemetry
   against the experiment definition. This is the auditable core of the
   product; it never asks an LLM for a verdict.

```
┌─────────────┐   ┌──────────────────┐   ┌───────────────────┐
│  Frontend    │──▶│   FastAPI API     │──▶│  Experiment Engine │
│  (React/TS)  │   │  backend/api/     │   │  (JSON definitions)│
└─────────────┘   └──────────────────┘   └───────────────────┘
                          │      │
                          ▼      ▼
              ┌────────────────┐ ┌─────────────────────┐
              │ InferenceManager│ │  Verification Engine │
              │ (picks backend) │ │  (rule-based fusion)  │
              └────────────────┘ └─────────────────────┘
                    │        │
        ┌───────────┘        └───────────┐
        ▼                                 ▼
┌────────────────┐              ┌──────────────────────┐
│ Fallback (CPU)  │              │ Qualcomm (Snapdragon) │
│ OpenCV heuristic│              │ Qwen3-VL / Whisper     │
│ honesty-first    │              │ via QNN runtime        │
└────────────────┘              └──────────────────────┘
```

## Why the layers are separated

The project brief is explicit that the AI's job is "what do I see" and the
verification engine's job is "does what I see satisfy the experiment." Mixing
these into a single LLM call would make every verdict unauditable and would
make it trivial for the model to hallucinate a "PASS" on a genuinely broken
circuit. Keeping them separate means:

- The verification engine's output is fully explainable — every PASS,
  WARNING, or DEVIATION traces back to a specific rule and a specific piece
  of evidence (`VerificationResult.evidence`).
- Swapping vision backends (CPU heuristic → Qwen3-VL → Qualcomm NPU) never
  changes verification logic.
- Tests for the verification engine don't need a model at all (see
  `tests/test_verification_engine.py`), which makes CI fast and deterministic.

## The UI never talks to Qualcomm directly

`backend/services/inference_manager.py` is the only place that imports both
`fallback/*` and `qualcomm/*` backends. It exposes `get_vision_backend()` and
`get_speech_backend()`, always returning a working instance regardless of
which is actually running underneath. The API layer and frontend call the
manager, never a concrete backend class.

## Data flow of a single verification

1. Frontend captures/uploads a frame → `POST /api/vision/analyze` → active
   vision backend returns a `VisualObservation`.
2. Frontend (or backend, for demo scenarios) also gathers `SensorReading`s,
   real (Arduino serial) or simulated.
3. Frontend calls `POST /api/verify` with the experiment id, the
   `VisualObservation`, and the `SensorReading` list.
4. `backend/verification/engine.py::verify()` loads the experiment
   definition, compares expected vs. detected connections and measurements,
   and returns a `VerificationResult` with an explicit state, confidence,
   per-step results, and evidence trail.
5. The frontend renders that result directly — no re-interpretation.

## Repository layout

See the top-level `README.md` for the full directory tree.
