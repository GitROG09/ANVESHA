# PROJECT_STATUS.md

## Current phase

Phase 2 — Objective 2 (real LDR vision perception & evaluation foundation)
— **foundation implemented; real perception pending data/model/hardware**.

## Objective 2 update

Implemented in the current repository:

- Structured component, pin, wire-endpoint, and conservative connection fields
  in `backend/schemas/models.py`.
- Strict provider-output adapter in `backend/inference/perception_adapter.py`.
  It validates JSON, labels, confidence, normalized coordinates, duplicate
  claims, endpoint references, and rejects provider-generated verdicts.
- Explicit `FixtureVisionBackend` for labeled structured tests only. It is not
  selected as a real inference backend.
- Lazy Qwen3-VL provider foundation in `backend/inference/qwen3vl_provider.py`:
  structured observation prompt, local-only loading boundary, strict adapter
  routing, and explicit unavailable behavior. It is not registered as an
  active backend and has not run model inference.
- Rule metadata through evidence fusion and explicit structured component
  claims participating in deterministic verification.
- Provenance-aware dataset contracts and eight structured golden fixtures in
  `datasets/ldr/`. No images are included.
- Deterministic evaluation helpers and `scripts/evaluate_vision.py`.
- Camera stream lifecycle and zero-sized-frame safeguards.
- Frontend source/evidence labeling, evidence-log rendering, and experiment-
  scoped demo scenarios.

Not implemented or available:

- Real LDR photographs, physical ground truth, or real-world metrics.
- Trained LDR component/pin/wire perception.
- Executable Qwen3-VL or Qualcomm QNN inference.
- Qwen3-VL weights and real-image perception validation.
- Real camera browser testing in this environment.

## Note on repository history

The task brief for this session described a prior Claude session that
had already audited the repo and partially implemented Objective 1
(structured evidence schema, fusion module, updated fallback vision
backend), stopped mid-work by a token limit. On inspection, the actual
repository contained a **single commit** (`chore: initial ANVESHA AI
baseline`), 28 passing tests matching the described "REAL/IMPLEMENTED"
baseline, and **no** evidence-fusion module, no `EvidenceStatus`
enum/schema, no `CLAUDE.md`/`PROJECT_STATUS.md`, and no uncommitted
working-tree changes. In other words: the baseline audit's findings
matched the repo, but the claimed "Objective 1 work already started" did
not exist here — this session implemented Objective 1 from that
baseline, not by continuing in-progress files. Recording this plainly so
nobody assumes lost work exists somewhere that needs recovering.

## Architectural correction (this session, after initial Objective 1 review)

`fuse_evidence()` originally discarded **all** structured evidence
(including telemetry) whenever `frame_suitable=False`. That was wrong:
telemetry is an independent evidence source and does not depend on the
camera. Corrected behavior:

- Measurement evidence is now fused from `readings` **unconditionally**,
  regardless of frame quality/availability.
- Connection and component evidence still require `frame_suitable=True`
  — visual claims still need a usable frame, and telemetry can never
  substitute for missing wiring evidence.
- `verify()`'s "frame not suitable" branch now rolls up whatever
  measurement evidence exists (via the same `_rollup_measurements` used
  in the normal path) into `verified_steps`/`failed_steps`/`warnings`/
  `evidence`, instead of returning an empty evidence log. The overall
  `experiment_state` in this branch is still always
  `INSUFFICIENT_EVIDENCE` — a real, valid measurement does not upgrade
  the result when the required visual connection evidence is missing —
  but it is no longer silently dropped from the bundle or the evidence
  log.
- `simulated` propagation was verified end-to-end for this path: a
  simulated reading fused during a bad-frame verification still reports
  `simulated=True` on both the `EvidenceBundle` and in the resulting
  evidence summary text.

Added 4 targeted tests in `tests/test_evidence_fusion.py`:
`test_bad_frame_with_real_telemetry_preserves_measurement_evidence`,
`test_bad_frame_without_telemetry_stays_insufficient_evidence`,
`test_good_frame_with_real_telemetry_has_both_evidence_sources`,
`test_good_frame_with_simulated_telemetry_preserves_simulated_flag`.
One existing test (`test_low_quality_frame_produces_no_structured_evidence`)
was renamed/updated to `test_low_quality_frame_produces_no_visual_structured_evidence`
since its old assertion (`structured_evidence == []`) was exactly the
behavior being corrected; it now asserts no connection/component evidence
while still allowing (and checking for) MISSING measurement evidence.

**48 passed, 0 failed** (44 prior + 4 new; net +4 since one test was
updated in place rather than duplicated).

## Completed this session

- Added `EvidenceStatus` enum (`OBSERVED / INFERRED / UNCERTAIN /
  OCCLUDED / MISSING`) to `backend/schemas/models.py`.
- Added `StructuredEvidence` and `EvidenceBundle` schemas — the
  per-claim evidence record (subject/relationship/expected/observed/
  status/confidence/source/timestamp) and its container.
- Added `frame_quality` (0–1 float) to `VisualObservation`, kept
  strictly separate from per-connection `confidence`.
- Added `status: EvidenceStatus` to `DetectedConnection` (defaults to
  `OBSERVED`, backward compatible with existing callers/tests).
- Implemented `backend/evidence/fusion.py`: a dedicated module that
  fuses vision + telemetry + the experiment spec into
  `list[StructuredEvidence]`, with no pass/fail decision made here.
  - Connections: OBSERVED (correct or wrong, reported as-is),
    UNCERTAIN (confidence < 0.55), INFERRED (propagated from backend),
    OCCLUDED (only on an explicit `bounding_boxes` occlusion signal —
    never inferred from absence alone), MISSING (no match, no signal).
  - Components: OBSERVED / OCCLUDED / MISSING, informational only.
  - Measurements: OBSERVED (raw reading, range-checked at verification
    time) / MISSING (no reading for that sensor).
- Rewrote `backend/verification/engine.py` as a thin deterministic
  rollup over `EvidenceBundle` (no vision/telemetry parsing logic left
  in the verification layer itself). Same public `verify()` signature
  and `VerificationResult` shape as before — no API or frontend
  contract changes required.
- Updated `backend/inference/fallback/vision_backend.py` to compute and
  report a real `frame_quality` score (sharpness + exposure heuristic,
  0–1) alongside the existing honest "empty `detected_connections`,
  never fabricated" behavior. Verified this score is never copied into
  any connection/component confidence value.
- Fixed the two known frontend bugs:
  - `frontend/src/pages/Home.tsx` now fetches `GET /api/runtime` and
    renders the actual active backend ("Qualcomm NPU (Snapdragon
    accelerated)" or "CPU fallback (local development)") instead of the
    hardcoded "Qualcomm Accelerated / Local Development" string.
  - `frontend/src/pages/LiveVerification.tsx`'s `runVerify()` no longer
    calls `api.simulateTelemetry()` on the camera/upload path. Real
    verification now sends only the actual analyzed frame and whatever
    real sensor readings exist (currently none from the frontend), so
    missing measurement evidence is honestly reported as a warning
    rather than backed by a fabricated reading. The "Demo Scenario"
    mode is unchanged and remains the only simulated-data path,
    labeled as such in the UI.
- Added `CLAUDE.md` and this file.
- Added `tests/test_evidence_fusion.py` (16 new tests) covering
  observed/inferred/uncertain/occluded/missing evidence, image-quality
  vs connection-confidence independence, conflicting evidence,
  insufficient-evidence-from-uncertainty-only, and the
  DEVIATION → PASS state transition through the new fusion layer.

## Partially completed

Nothing left mid-implementation. The scope defined for Objective 1 in
the task brief (structured evidence schema, fusion module, verification
engine as thin rollup, fallback vision backend emitting the new fields,
tests) is finished end to end.

## Objective 2 remaining work

- Collect and annotate real LDR photographs when physical hardware becomes
  available.
- Train or integrate a real component/pin/wire perception provider.
- Evaluate held-out real photographs without reporting synthetic fixtures as
  real-world results.
- Complete and validate Qualcomm/QNN execution on Snapdragon hardware.

## Known limitations (unchanged from prior audit, still accurate)

- Qualcomm vision/speech backends: implemented as interfaces + device
  detection; cannot execute without real Snapdragon hardware + AI Hub
  runtime.
- Fallback speech backend: honestly reports unavailable (no bundled
  model).
- Fallback vision backend: real OpenCV frame-quality + region-count
  heuristics only; cannot do pin-level connection tracing without a
  trained/loaded detection model — this is by design, not a bug, and is
  now made explicit at the schema level via `EvidenceStatus.MISSING`.

## REAL vs SIMULATED vs UNAVAILABLE

**REAL**
- Experiment schema + engine, 3 experiment definitions
- Deterministic verification engine (`backend/verification/engine.py`)
- Evidence fusion module (`backend/evidence/fusion.py`)
- FastAPI backend and its endpoints
- Fallback (OpenCV) vision backend: frame quality, region-count heuristic
- Runtime detection (`GET /api/runtime`, now also driving the frontend)

**SIMULATED (explicitly labeled end to end)**
- 4 demo scenarios in `backend/services/simulation.py`, reachable only
  via `/api/demo/*`
- `/api/telemetry/simulate` (still available as an API for explicit use;
  the frontend's real camera/upload path no longer calls it silently)

**UNAVAILABLE in this environment**
- Qualcomm vision backend (Qwen3-VL via QNN)
- Qualcomm speech backend (Whisper via QNN)
- Fallback speech backend (no bundled model)
- Any actual Snapdragon/NPU execution

## Tests

- 28 tests passing before this session's changes (baseline, unchanged
  in behavior — all still pass).
- Objective 2 adds adapter, evaluation, fixture-provider, and end-to-end
  pipeline tests.
- **94 passed, 0 failed** in the current backend suite.
- Frontend build/type-check remains environment-dependent; Node/npm were not
  available in the implementation shell.

## Next milestone

Acquire real LDR photographs and annotations, then implement and evaluate a
real perception provider. Keep all results provenance-labeled and do not
claim real-world accuracy until the held-out real-photo test split exists.
