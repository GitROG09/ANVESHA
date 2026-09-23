# Benchmarking

## Running the benchmark

```bash
cd anvesha-ai
python benchmarks/benchmark.py --runs 30
```

Writes `benchmarks/results/benchmark_report.json` and `.md`, and is also
served by the backend at `GET /api/benchmarks` for the Performance screen.

## What is actually measured (local)

On whatever machine runs the script, using the CPU fallback vision backend
and a synthetically generated 640x480 test frame:
- Backend construction ("load") time
- First (cold) inference latency
- Vision backend latency: mean, p50, p95, min, max over N runs
- Verification engine latency: mean, p50, p95 (pure rule evaluation, no I/O)
- End-to-end latency: vision + verification combined
- Peak/current Python heap memory during the vision loop (`tracemalloc`)

Example run in this development container (x86_64 CPU, no NPU) — 30 runs,
640×480 frames:

| Metric | Value |
|---|---|
| Load time | see `benchmarks/results/benchmark_report.md` (generated) |
| First inference latency | see generated report |
| Vision latency (p50 / p95) | see generated report |
| Verification engine latency (mean) | see generated report |
| End-to-end latency (p50 / p95) | see generated report |
| Peak memory | see generated report |

(The actual numbers are written fresh on every run and are not
hand-copied into this document, to guarantee they're never stale or faked —
see the generated `benchmark_report.md` / `.json` for the current numbers.)

## What is NOT measured here

Qualcomm NPU inference numbers. No Snapdragon hardware is available in this
development environment. `benchmarks/benchmark.py` explicitly does not
attempt to measure the Qualcomm backend and instead emits a placeholder
`qualcomm_ai_hub_reference_metrics` block pointing at where real numbers
should come from: Qualcomm AI Hub's own on-device profiling step (which
runs automatically during `python -m qai_hub_models.models.<id>.export`,
see `docs/qualcomm_deployment.md` §3 and §8). Those numbers are Qualcomm's
own measurement of their exported model on real hardware — not ours — and
must stay labeled as such if reported anywhere (README, submission
materials, pitch deck).

## CPU vs. Qualcomm/NPU comparison

Only to be filled in once both numbers exist for the same task, image size,
and model, per the project brief. As of this snapshot, only the CPU-side
number exists (and it isn't even the same model — the CPU fallback is an
OpenCV heuristic, not Qwen3-VL). Reporting a CPU-vs-NPU speedup claim would
require the *same* Qwen3-VL model running through both paths; that
comparison cannot honestly be made until the Qualcomm backend is completed
per `docs/qualcomm_deployment.md` on real hardware.
