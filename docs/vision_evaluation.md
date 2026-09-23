# LDR Vision Evaluation

Objective 2 adds a strict perception adapter, structured component/pin/
endpoint fields, provenance-aware dataset contracts, labeled test fixtures,
and deterministic evaluation helpers.

## Current State

Implemented now:

- `backend/inference/perception_adapter.py` validates provider JSON and maps it
  into the shared `VisualObservation` contract.
- `backend/inference/fixture_provider.py` is an explicitly labeled provider for
  structured test fixtures only.
- `backend/evaluation/metrics.py` computes deterministic supplied-record
  metrics and reports real-world metrics as unavailable when no
  `provenance=real` records exist.
- `datasets/ldr/` contains annotation/split contracts and structured golden
  cases. It contains no fabricated photographs.

Not implemented or unavailable:

- No executable Qwen3-VL or Qualcomm QNN provider.
- No trained LDR detector.
- No real photographs or real ground truth.
- No real-world perception accuracy claim.

## Provenance

Every future record must be labeled `synthetic`, `test_fixture`, or `real`.
Synthetic and fixture results must never be reported as real-world evaluation.
Related captures from one setup/session must remain in one split to prevent
leakage. Real photographs remain pending physical hardware availability.

## Evaluation

Run the empty, honest evaluation report with:

```text
python scripts/evaluate_vision.py
```

Evaluate supplied labeled records with:

```text
python scripts/evaluate_vision.py --records path/to/records.json
```

Evaluate the repository's structured test fixtures explicitly with:

```text
python scripts/evaluate_vision.py --golden
```

This reports under `test_fixture`; it never treats fixture records as real
photographs or real-world performance.

The harness supports exact connection metrics, state classification metrics,
false PASS/deviation counts, abstention counts, provenance separation, and
normalized bounding-box IoU. It does not invent values when a dataset is
empty.

The final real-photo evaluation should additionally report component, pin,
endpoint, connection, evidence-status, and end-to-end verdict metrics. The
held-out real test split must remain untouched until that evaluation.
