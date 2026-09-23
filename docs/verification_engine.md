# Verification Engine

`backend/verification/engine.py::verify()` is the deterministic core of
ANVEṢHA AI. Given an `Experiment`, a `VisualObservation`, and a list of
`SensorReading`s, it returns a `VerificationResult`.

## States

| State | Meaning |
|---|---|
| `PASS` | Every checked connection and measurement matched expectations. |
| `WARNING` | Some evidence was missing/low-confidence, but nothing contradicted the procedure. |
| `DEVIATION` | At least one connection or measurement actively contradicts the procedure. |
| `INSUFFICIENT_EVIDENCE` | No usable visual evidence at all (e.g. blurry/dark frame), or only warnings with zero verified steps. |

## Algorithm (connections)

For each expected `Connection` in the experiment:
1. Find the best-confidence `DetectedConnection` whose `from_component`/`from_pin`
   matches (case-insensitive).
2. If none found → `WARNING` ("not detected in current frame").
3. If found but confidence < `MIN_CONNECTION_CONFIDENCE` (0.55) → `WARNING`
   ("low-confidence detection").
4. If found, confident, and `to_component`/`to_pin` matches → `verified`.
5. If found, confident, and `to_component`/`to_pin` does NOT match → `failed`
   (`DEVIATION`), with an explicit expected-vs-observed pin pair and a
   recommended action.

## Algorithm (measurements)

For each `ExpectedMeasurement`, look up the most recent `SensorReading` for
that sensor:
- No reading → `WARNING`.
- Reading outside `[min_value, max_value]` → `failed` (`DEVIATION`).
- Reading inside range → `verified`. Simulated readings are tagged
  `(SIMULATED)` in the observed-value string so the UI (and a judge reading
  the report) can never mistake a simulated value for a real one.

## Rolling up to a single state

```
if any failed_steps:            DEVIATION
elif warnings and no verified:  INSUFFICIENT_EVIDENCE
elif warnings:                  WARNING
else:                           PASS
```

## Confidence score

`confidence = (verified_count + 0.5 * warning_count) / total_checks`,
halved again if the underlying `VisualObservation.sufficient_evidence` was
itself `False`. This is a simple, explainable heuristic — not a model
output — matching the project's "no fake AI" requirement: nothing in this
number is invented, it's a direct function of the counted evidence.

## Evidence trail

Every `VerificationResult.evidence` entry names its `source`
(`"vision"` / `"telemetry"` / `"procedure"`) and a one-line summary, so the
UI's evidence panel — and this document — can point to exactly why a given
verdict was reached, satisfying the "explain what was observed / expected /
why it matters / what to check next" requirement from the project brief.

## Tests

`tests/test_verification_engine.py` covers: a clean pass, a wrong-pin
deviation, an out-of-range measurement deviation, no-evidence and
low-confidence insufficient-evidence cases, missing-in-frame connections
producing warnings (not silent passes), and the full before/after
correction transition that the live demo is built around.
