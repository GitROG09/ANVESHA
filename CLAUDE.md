# CLAUDE.md

Guidance for any Claude session (or human) picking up this repository.

## Core principle — read this first

> **Evidence fusion, not model opinion.**

The AI perception layer (vision/speech) is only allowed to answer "what
did I observe, and how sure am I". It must never decide the final
PASS/WARNING/DEVIATION/INSUFFICIENT_EVIDENCE verdict. That decision is
made exclusively by the deterministic verification engine
(`backend/verification/engine.py`), applying fixed rules to structured
evidence produced by `backend/evidence/fusion.py`.

Two rules follow directly from this and must never be violated:

1. **No fabrication.** A vision/speech backend that cannot determine
   something must say so (`MISSING` / `UNCERTAIN` / `OCCLUDED`), never
   invent a plausible-looking answer because it matches what the
   experiment expects.
2. **No silent simulation.** Simulated/demo data must always be tagged
   `simulated=True` end-to-end (schema, evidence, UI) and must never be
   used inside a code path that claims to be verifying a real camera
   frame or a real sensor reading. `/api/demo/*` is the only sanctioned
   entry point for scripted data.

## Architecture map

```
backend/
  schemas/models.py       Pydantic contracts — EvidenceStatus, StructuredEvidence,
                           EvidenceBundle, VisualObservation, VerificationResult, ...
  evidence/fusion.py       Evidence fusion: vision + telemetry + experiment spec
                           -> list[StructuredEvidence]. Never decides pass/fail.
  verification/engine.py   Thin deterministic rollup over StructuredEvidence
                           -> VerificationResult (PASS/WARNING/DEVIATION/
                           INSUFFICIENT_EVIDENCE). No model calls here.
  inference/
    base/                  VisionBackend / SpeechBackend abstract interfaces
    fallback/               Real OpenCV frame-quality + region-count backend.
                            Never fabricates per-component/connection detections.
    qualcomm/               Device detection + Snapdragon/QNN backends (honestly
                            report unavailable off real Snapdragon hardware).
  services/
    inference_manager.py   Picks Qualcomm NPU backend if actually detected, else
                            CPU fallback. This is the only place that decides
                            "which backend is active" — /api/runtime reports it.
    simulation.py           4 explicitly-labeled demo scenarios. Only reachable
                            via /api/demo/*, never from /api/verify or
                            /api/vision/analyze.
  experiments/engine.py     Loads experiments/*.json
  telemetry/service.py      Arduino serial read, or explicitly-tagged simulated read
```

## Evidence status vocabulary

`EvidenceStatus` (in `backend/schemas/models.py`):

| Status      | Meaning                                                             |
|-------------|----------------------------------------------------------------------|
| OBSERVED    | Directly perceived with usable confidence — report the real value, even if it's wrong relative to spec. |
| INFERRED    | Not directly seen, implied by other evidence (e.g. adjacency).      |
| UNCERTAIN   | Perceived, but confidence too low to trust in either direction.     |
| OCCLUDED    | Explicitly known to be blocked from view (must have a positive signal — never inferred from absence alone). |
| MISSING     | No evidence at all — not detected, not attempted.                   |

Three confidence-like numbers exist in this codebase and must **stay
separate**:

- `VisualObservation.frame_quality` — is the frame itself usable for
  perception at all (blur/brightness heuristic)?
- `DetectedConnection.confidence` / `StructuredEvidence.confidence` —
  how sure is the perception layer about *this one* claim?
- `VerificationResult.confidence` — how much of the *required evidence*
  came back verified (a rollup statistic), computed in
  `verify._compute_confidence`.

Do not let one leak into another. A sharp, well-lit frame with zero
reliable detections is a real and expected state, not a bug.

## Working conventions

- Run `pytest -q` (from repo root, with `backend/`, `experiments/` on the
  path — see `pytest.ini`) before and after any change. Do not weaken or
  delete existing assertions to make the suite pass.
- Every new evidence-producing code path needs deterministic tests
  covering at least: OBSERVED (correct), OBSERVED (wrong ->
  DEVIATION), UNCERTAIN, OCCLUDED, MISSING, and the resulting
  VerificationResult state.
- `frontend/src/pages/Home.tsx` reports the AI runtime dynamically via
  `GET /api/runtime` — do not hardcode a runtime label again.
- `frontend/src/pages/LiveVerification.tsx`'s camera/upload path must
  never call `api.simulateTelemetry()` or any other simulated-data
  helper. Only the "Demo Scenario" mode (`api.runDemoScenario`) may use
  simulated data, and it must stay visibly labeled SIMULATED in the UI.
- Keep `PROJECT_STATUS.md` current — REAL vs SIMULATED vs UNAVAILABLE,
  updated whenever a capability's status actually changes. Do not use
  marketing language to round up a capability's status.

## Current phase

Phase 2, Objective 1 (structured evidence + evidence fusion) is
complete as of this session. See `PROJECT_STATUS.md` for the full
breakdown and the next milestone. Do not start Objective 2 (vision
evaluation dataset, Arduino integration, Qualcomm integration, frontend
redesign) without explicit instruction.
