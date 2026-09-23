# PROJECT_STATUS.md

## Current phase

Phase 2 — Objective 1 (structured evidence + evidence fusion foundation)
— **complete**, as of commit built in this session.

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

## Remaining (explicitly out of scope for this session)

- Vision evaluation dataset (`docs/vision-evaluation.md` and the
  underlying labeled dataset) — not started, per instruction not to
  start it yet.
- Arduino hardware integration beyond the existing serial read path.
- Qualcomm/Snapdragon NPU execution — abstraction and device detection
  exist; no NPU execution is possible in this dev environment.
- Frontend redesign beyond the two targeted bug fixes above.
- `docs/qualcomm-integration.md` and `docs/benchmark-methodology.md` —
  the repo already has closely related docs (`docs/qualcomm_deployment.md`,
  `docs/benchmarking.md`); new dedicated files were not created since
  they weren't required to finish Objective 1 and doing so wasn't asked
  for beyond the doc list. Flagging for a decision next session: reuse/
  rename the existing docs, or add the new ones alongside them.

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
- 16 new tests added in `tests/test_evidence_fusion.py`.
- **44 passed, 0 failed**, full suite (`pytest -q` from repo root).
- Frontend: `tsc --noEmit` and `vite build` both succeed with the
  Home.tsx / LiveVerification.tsx changes.

## Next milestone

Review this evidence architecture (schema, fusion module, thin
verification rollup) before starting Phase 2, Objective 2. Objective 2
candidates, per the task brief, are: the vision evaluation dataset,
Arduino integration, Qualcomm integration, and the frontend redesign —
none of which have been started.
