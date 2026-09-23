# Qualcomm AI Hub Deployment Guide

This document describes the **verified, real** deployment path for running
ANVEṢHA AI's vision and speech backends on Snapdragon NPU hardware via
Qualcomm AI Hub. It is written from Qualcomm's public documentation
(`aihub.qualcomm.com`, `github.com/qualcomm/ai-hub-models`,
`docs.qualcomm.com`) as of this writing. **This repository's development
container has no Snapdragon hardware and no network access to Qualcomm AI
Hub or Hugging Face, so none of the steps below have been executed as part
of building this snapshot** — `backend/inference/qualcomm/*` implements the
correct abstraction and fails loudly and honestly instead of pretending to
run on the NPU. This guide is what a developer with real Snapdragon
hardware needs to complete the integration.

## 1. Supported hardware

- Snapdragon X Elite / X2 Elite / X Plus (Windows-on-ARM64) laptops —
  this includes the Snapdragon-powered HP devices this competition targets.
- Qualcomm profiles and validates against cloud-hosted reference devices too
  (e.g. "Snapdragon X Elite CRD"), useful for testing before you have
  physical hardware.

## 2. Required software

- **Python.** Important gotcha confirmed in Qualcomm's own docs: on
  Snapdragon X Elite / X2 Elite Windows machines, `qai_hub_models` currently
  requires **AMD64 (x64) Python**, not ARM64 Python — installation fails
  under Windows ARM64 Python. Install x64 Python via the standard
  python.org installer (it runs under emulation for the Python interpreter
  itself; the exported model still executes natively on the NPU at
  inference time).
- **Qualcomm AI Hub account.** Sign up at https://myaccount.qualcomm.com/signup
  to get Qualcomm AI Hub Workbench access (needed for model compilation and
  cloud device profiling).
- **Packages:**
  ```bash
  pip install qai_hub qai_hub_models
  ```
- **Qualcomm AI Runtime (QNN) / on-device runtime.** For local execution on
  a physical Snapdragon device, install the runtime components documented
  under "Qualcomm AI Runtime" on the Windows on Snapdragon developer docs
  (`docs.qualcomm.com`, topic id 80-62010-1). This provides the QNN
  execution provider used by ONNX Runtime or the native QNN context-binary
  loader.

## 3. AI Hub model preparation

Qualcomm AI Hub Models publishes a catalog of pre-optimized models runnable
via `python -m qai_hub_models.models.<model_id>.export`. The exact model ids
for **Qwen3-VL-4B-Instruct** and **Whisper-Small** should be confirmed
against the live catalog at deployment time (`qai-hub-models models` CLI or
https://aihub.qualcomm.com/models) since catalog contents change. The
general export workflow (shown here using the pattern Qualcomm documents for
their LLM models, e.g. Llama 3.2) is:

```bash
python -m qai_hub_models.models.<model_id>.export \
  --device "Snapdragon X Elite CRD" \
  --target-runtime qnn \
  --output-dir ./models/qualcomm
```

This will, per Qualcomm's documented flow:
1. Compile the model for the chosen device/runtime.
2. Quantize it if applicable.
3. Profile it on a real cloud-hosted Snapdragon device and report latency
   and memory.
4. Run inference on that hosted device and compare against the reference
   (PyTorch) output for a correctness check.
5. Download the compiled artifact (a QNN context binary `.bin`, a `.dlc`,
   or an ONNX graph with QNN execution provider, depending on target
   runtime) to `./models/qualcomm`.

Large multimodal/LLM-class models can take a long time to upload/compile in
this pipeline (Qualcomm's own docs note this step "can take several
hours" for models like Llama 3.2 3B) — budget development time accordingly.

## 4. Model installation

Copy the downloaded artifact into a path on the target device and point the
backend at it via environment variables (see `backend/inference/qualcomm/`):

```bash
setx QUALCOMM_VISION_MODEL_PATH "C:\anvesha\models\qwen3vl\model.bin"
setx QUALCOMM_SPEECH_MODEL_PATH "C:\anvesha\models\whisper_small\model.bin"
```

## 5. Backend configuration

`backend/inference/qualcomm/device_detection.py` checks:
- OS is Windows and machine architecture is ARM64.
- `qai_hub` / `qai_hub_models` are importable.
- The model path env vars point at files that actually exist.

Only if all three are true does `QualcommVisionBackend.is_available()` /
`QualcommSpeechBackend.is_available()` return `True`. Otherwise
`InferenceManager` (in `backend/services/inference_manager.py`) silently
falls back to the CPU backend and the UI's runtime status shows
"CPU Fallback."

**Remaining implementation work on real hardware:** the `analyze()` /
`transcribe()` methods in `backend/inference/qualcomm/vision_backend.py` and
`speech_backend.py` currently raise `NotImplementedError` once a model path
is configured — the actual QNN context-binary load-and-run call
(via `qai_hub_models`' runtime helpers, or a direct QNN Python binding) needs
to be written on the target machine, following the specific model's export
README for its expected input/output tensor format.

## 6. Running ANVEṢHA

```bash
# Terminal 1 — backend
cd anvesha-ai
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — frontend
cd anvesha-ai/frontend
npm install
npm run dev
```

Open the printed local URL. The Settings screen will show
`Qualcomm NPU` as the active backend only once steps 1-5 above are
genuinely complete on that machine.

## 7. NPU verification

Confirm you're really on the NPU, not silently falling back to CPU/GPU
execution paths inside the QNN runtime, by checking the "Compute Units"
field Qualcomm AI Hub reports during profiling (e.g. `Compute Units: NPU
(285) | Total (285)` in AI Hub's own export logs) and by checking
Qualcomm's QAIRT/QNN profiling tools (`QAIRT Optrace`, mentioned in the
Qualcomm AI Runtime docs) for a production deployment.

## 8. Benchmarking

Use `benchmarks/benchmark.py` for the CPU-side, in-repo measurements.
For NPU numbers, use the `on-device profiling` step AI Hub performs
automatically during `export` (see step 3) — that is Qualcomm's own,
independently measured figure for your exact model/device pair, and is
what `benchmarks/results/benchmark_report.md`'s "Qualcomm AI Hub Reference
Metrics" section should be filled in with once available. Never copy those
numbers into the "local measurement" section — keep the two clearly
separated, as the report template already does.

## 9. Troubleshooting

- **`pip install qai_hub_models` fails on Windows ARM64** — you're using
  ARM64 Python; switch to x64 Python (see §2).
- **Export step hangs or is very slow** — large model uploads/compiles on
  AI Hub's cloud devices can legitimately take a long time; this is
  documented Qualcomm behavior, not a bug in this repo.
- **`QualcommVisionBackend.is_available()` returns `False` even with a
  model path set** — check `device_detection.py`'s three conditions
  individually; the most common miss is `qai_hub_models` being installed
  under the wrong (ARM64) Python interpreter.
- **Compute Units report includes CPU fallback ops** — some ops in a graph
  may not have an NPU (HTP) kernel and fall back to CPU within the QNN
  graph itself; check AI Hub's per-op profiling breakdown.

## 10. Sources

- https://github.com/qualcomm/ai-hub-models
- https://aihub.qualcomm.com/
- https://docs.qualcomm.com/bundle/publicresource/topics/80-62010-1/ai-hub.html
- https://docs.qualcomm.com/bundle/publicresource/topics/80-62010-1/qnn.html
- https://onnxruntime.ai/docs/genai/howto/build-models-for-snapdragon.html
