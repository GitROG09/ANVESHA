# Limitations

This is an honest accounting of what this repository snapshot does and does
not actually do, per the project's own "no fake AI, no fabricated
benchmarks" requirement.

## Vision

- The production-path vision model (Qwen3-VL-4B-Instruct via Qualcomm AI
  Hub) is **not implemented or executable** in this environment. No
  Snapdragon NPU is present, and the model weights cannot be downloaded
  here (network restricted to package registries).
- The CPU fallback vision backend is real but deliberately narrow: it can
  assess frame quality (blur/brightness) and roughly count component-like
  regions via edge detection, but it **cannot reliably trace individual
  wire-to-pin connections**. It never fabricates connection data — see
  `backend/inference/fallback/vision_backend.py`.
- Practical effect: real connection-level DEVIATION/PASS verdicts from a
  live, uploaded photo are not currently produced by the CPU backend; they
  are demonstrated instead through the clearly-labeled scripted demo
  scenarios (`backend/services/simulation.py`) or will work once the
  Qualcomm/Qwen3-VL backend is completed on real hardware.
- Bounding-box visualization is implemented in the schema
  (`VisualObservation.bounding_boxes`) and the frontend evidence types are
  ready to render it, but no backend currently populates real coordinates
  (the CPU fallback returns none rather than inventing boxes).

## Speech / voice

- Not implemented. `FallbackSpeechBackend` and `QualcommSpeechBackend` both
  honestly report themselves unavailable and raise clear errors rather than
  fabricate a transcript. See `docs/ai_models.md` for what's needed to wire
  up a real local or Qualcomm speech model.
- The frontend does not yet have a microphone-capture UI; only the backend
  contract exists.

## Qualcomm / Snapdragon

- No Snapdragon hardware was available to build or test on. The entire
  `backend/inference/qualcomm/` package is a correct, honest abstraction
  (device detection, runtime status, backend classes) that reports
  unavailability accurately and documents the exact remaining
  implementation work in `docs/qualcomm_deployment.md`. It has not been
  exercised end-to-end on real hardware.
- No Qualcomm AI Hub API calls, model exports, or NPU inferences have
  actually been executed as part of building this project. Every claim in
  `docs/qualcomm_deployment.md` is sourced from Qualcomm's public
  documentation, not from having run it here.

## Hardware / Arduino

- `backend/telemetry/service.py` implements a real serial-line protocol
  (`<sensor>,<value>,<unit>\n` at 115200 baud) and uses `pyserial`, but no
  physical Arduino was connected while building this project, so the
  hardware path (`read_hardware`) is implemented and unit-testable for its
  failure modes but not verified against a real board. An example Arduino
  sketch implementing this protocol should be added under
  `scripts/arduino/` before a hardware demo (not yet created in this
  snapshot).

## Benchmarking

- Only CPU-side, local numbers are real measurements, taken in this
  development container (not Snapdragon hardware). See
  `benchmarks/results/benchmark_report.md` for the actual numbers from the
  most recent run.
- No NPU numbers exist anywhere in this repository. The benchmark report
  format reserves a clearly-separated section for Qualcomm AI Hub's own
  reference profiling output, explicitly marked as not our measurement,
  with `value: null` until someone fills it in from real hardware.

## Frontend

- Camera capture uses the browser `getUserMedia` API, which requires a
  secure context and camera permission; in this sandboxed development
  environment there is no camera device to test against, so the camera
  path is implemented but only manually reviewed, not exercised against a
  live camera. The Upload Frame and Demo Scenario paths were tested against
  the live backend.
- PDF/image procedure upload (mentioned as optional in the project brief)
  is not implemented; only built-in JSON experiment definitions are
  supported in this snapshot.
- No automated frontend (component/e2e) tests were written; only a
  successful `tsc -b && vite build` was verified, plus manual review of the
  API contract against `tests/test_api.py`.

## Experiment coverage

- Three experiments are implemented (LDR, HC-SR04 ultrasonic, LED/resistor),
  matching the brief's "2-4 well-defined experiments" guidance. The schema
  is designed to be extensible (see `docs/experiment_engine.md`) but no
  additional experiments were authored.

## What IS real and tested in this snapshot

- The experiment schema, loader, and all three experiment definitions.
- The verification engine's rule-based evidence fusion (28 automated tests,
  all passing, covering pass/deviation/insufficient-evidence/before-after
  cases).
- The FastAPI backend, booted and manually smoke-tested live (not just via
  TestClient) with `curl`.
- The CPU fallback vision backend's frame-quality gating.
- The telemetry simulation path and its explicit `simulated` tagging.
- The four scripted demo scenarios end-to-end through the real verification
  engine.
- The React/TypeScript frontend, which builds cleanly and implements all
  ten screens named in the project brief (Home, Experiment Selection,
  Procedure, Live Verification, Evidence [folded into Live Verification's
  result panel], Measurements [folded into the same panel], Verification
  Result, Performance, Settings/Runtime — Experiment Report is not a
  separate screen in this snapshot, see below).
- The benchmark harness and its real local numbers.

## Not yet built

- A dedicated **Experiment Report** screen/export (PDF or shareable
  summary of a completed verification session) — the project brief lists
  this as Screen 8. The verification result is currently only shown live in
  the Live Verification screen and not persisted/exported.
- Bounding-box overlay rendering in the frontend (schema/types are ready;
  no backend currently emits real coordinates to render).
- Voice UI (microphone capture + playback of answers).
- Arduino sketch file and an actual hardware-in-the-loop test run.
