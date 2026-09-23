# AI Models

## Vision

**Target production model:** Qwen3-VL-4B-Instruct, deployed via Qualcomm AI
Hub to run on the Snapdragon NPU (see `docs/qualcomm_deployment.md`). Its job
in the pipeline is strictly perceptual: "what components and connections are
visible in this frame." It is never asked to judge whether the experiment is
correct — that's the verification engine's job (`backend/verification/engine.py`).

**What actually runs in this repository snapshot:** `FallbackVisionBackend`
(`backend/inference/fallback/vision_backend.py`), a CPU/OpenCV backend that:
- Assesses frame quality (blur via Laplacian variance, brightness) to decide
  `sufficient_evidence`. This gate is real and tested.
- Estimates a rough component-region count via edge/contour detection.
- Deliberately returns **no** fabricated pin-level connections, because a
  heuristic CV pipeline cannot reliably trace individual wires. It says so
  explicitly in its output notes.

The `QualcommVisionBackend` class implements the correct interface and
device-detection logic, but its `analyze()` raises `NotImplementedError` in
this environment (no Snapdragon hardware, no downloadable model weights) —
see `docs/qualcomm_deployment.md` for exactly what's left to wire up.

## Speech

**Target production model:** Whisper-Small (quantized), for the optional
voice Q&A feature ("Why did this fail?", "What should I check?"), ideally
via the Qualcomm AI Hub / QNN path on Snapdragon.

**What actually runs in this repository snapshot:** nothing — no speech
model is bundled (Whisper weights are large and this container cannot reach
a model hub). `FallbackSpeechBackend.is_available()` returns `False` unless
`WHISPER_MODEL_PATH` is set to a real, locally installed model, and
`transcribe()` raises a clear `SpeechBackendUnavailable` rather than faking
a transcript. Voice input is therefore optional and honestly degrades to
"unavailable" rather than silently failing.

## Why verification doesn't use an LLM at all

The verification engine (`backend/verification/engine.py`) is 100%
deterministic rule evaluation over structured data — no model call. This is
intentional:
- It's auditable: every verdict traces to a specific rule and evidence item.
- It's fast and free to run in a tight loop (`Verify Again`).
- It can be fully unit tested without any model dependency (see
  `tests/test_verification_engine.py`), which is why the engine's tests pass
  even in this offline, GPU-less environment.

## Setting up a local model for development

If you want to experiment with a real vision-language model locally before
deploying to Snapdragon:
1. Install `transformers`/`torch` (or an equivalent local runtime) and
   download Qwen3-VL-4B-Instruct or a smaller VLM.
2. Implement a new class extending `VisionBackend`
   (`backend/inference/base/vision.py`) that wraps your local model call and
   maps its output into the `VisualObservation` schema — mirroring exactly
   what `QualcommVisionBackend` will need to do for the NPU path.
3. Register it in `InferenceManager` (`backend/services/inference_manager.py`)
   with an appropriate priority order.

This keeps the "swap the model, not the app" property intact.
