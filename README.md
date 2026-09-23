# ANVEṢHA AI

**Observe. Investigate. Verify.**

On-device multimodal intelligence for physical experiment verification.
Built for the **Snapdragon AI Lab Build & Present Challenge**.

> "Anveṣha" comes from the Sanskrit for inquiry, investigation, seeking
> understanding — the loop this product runs on: **OBSERVE → INVESTIGATE →
> VERIFY.**

---

## The problem

Engineering students follow lab manuals to build circuits, but nothing
checks whether the physical setup actually matches the procedure. A wire on
the wrong pin, a reversed component, an out-of-range reading — today these
are caught by a TA walking the room, or by hours of trial and error.
Digital lab material tells students what to do; it never verifies what they
actually did. See `docs/problem_statement.md` for the full case.

## The solution

ANVEṢHA fuses three evidence sources against an explicit experiment
definition:

```
VISUAL EVIDENCE + PROCEDURAL EVIDENCE + MEASUREMENT EVIDENCE = EXPERIMENT STATE
```

and reports **PASS / WARNING / DEVIATION / INSUFFICIENT_EVIDENCE**, with a
plain-language explanation of what was observed, what was expected, why it
matters, and what to check next. Fix the issue, press **Verify Again**, and
watch the state flip from `DEVIATION` to `PASS` live — that before/after
moment is the core of the product.

The verdict comes from a deterministic, auditable **verification engine**
(`backend/verification/engine.py`) — not an LLM's opinion. Vision/speech
models answer "what do I see/hear"; the engine answers "does that satisfy
the experiment."

## Why on-device / why Snapdragon

Privacy (experiment data never leaves the device), low latency (a tight
capture → verify → correct loop), and offline operation are core to the
product, not marketing lines — see `backend/services/inference_manager.py`
and `docs/qualcomm_deployment.md` for how the vision/speech backends are
structured so the same app runs on CPU today and on a Snapdragon NPU via
Qualcomm AI Hub once deployed to real hardware.

## Models

| Modality | Target production model | Status in this repo |
|---|---|---|
| Vision | Qwen3-VL-4B-Instruct via Qualcomm AI Hub / QNN | Lazy provider foundation and strict adapter path implemented; weights and actual inference unavailable — see `docs/ai_models.md` |
| Vision (fallback) | OpenCV heuristics (frame quality + region count) | **Real, implemented, tested** |
| Speech | Whisper-Small (quantized) via Qualcomm AI Hub / QNN, or local fallback | Interface implemented; no model bundled — honestly reports unavailable |

**No cloud AI APIs are used anywhere** — no OpenAI, Gemini, or Claude API
calls for inference. See `docs/limitations.md` for a complete, honest
accounting of what actually runs versus what's a documented deployment path.

## Architecture

```
Frontend (React/TS/Vite)
   │  REST
   ▼
FastAPI backend (backend/api/main.py)
   ├── Experiment Engine        (backend/experiments/)   — loads experiments/*.json
   ├── Inference Manager        (backend/services/)       — picks Qualcomm NPU or CPU fallback
   │     ├── base/               — VisionBackend / SpeechBackend interfaces
   │     ├── fallback/           — CPU/OpenCV vision, honest "unavailable" speech
   │     └── qualcomm/           — device detection, runtime status, Snapdragon backends
   ├── Verification Engine      (backend/verification/)  — deterministic evidence fusion
   ├── Telemetry Service        (backend/telemetry/)      — Arduino serial or simulated readings
   └── Demo/Simulation Service  (backend/services/simulation.py) — 4 scripted, labeled demo scenarios
```

Full detail in `docs/architecture.md`.

## Repository structure

```
anvesha-ai/
├── frontend/                  React + TypeScript + Vite UI
├── backend/
│   ├── api/                   FastAPI app (main.py)
│   ├── inference/
│   │   ├── base/               VisionBackend / SpeechBackend interfaces
│   │   ├── fallback/           CPU/OpenCV vision backend, speech stub
│   │   └── qualcomm/           Device detection, runtime, Snapdragon backends
│   ├── experiments/            Experiment engine (loader)
│   ├── verification/           Verification engine (rule-based fusion)
│   ├── telemetry/               Arduino serial + simulation service
│   ├── preprocessing/           (reserved for image preprocessing helpers)
│   ├── schemas/                 Pydantic models shared across the backend
│   └── services/                Inference manager, demo/simulation service
├── experiments/                 ldr_sensor.json, ultrasonic_sensor.json, led_resistor_circuit.json
├── demo/                        (demo assets — see docs/demo_guide.md)
├── benchmarks/                  benchmark.py + results/
├── models/                      (place downloaded/exported model artifacts here; gitignored)
├── docs/                        architecture, problem statement, Qualcomm deployment, etc.
├── scripts/
│   ├── run_tests.sh             single test command
│   └── arduino/telemetry_sketch.ino
├── tests/                       pytest suite (94 tests)
├── assets/
├── submission/                  competition submission materials
├── README.md
├── requirements.txt
├── package.json
├── .gitignore
└── LICENSE
```

## Running it locally

Requires Python 3.10+ and Node 18+.

```bash
git clone <this-repo>
cd anvesha-ai

# Backend
python3 -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (default `http://127.0.0.1:5173`). The backend
must be running on `http://127.0.0.1:8000` (configurable via
`VITE_API_BASE_URL`).

### Simulation mode

No camera or Arduino required. On the Live Verification screen, choose
**Demo Scenario** and pick one of the four scripted scenarios
(`demo_1_correct`, `demo_2_wrong_connection` → `demo_2b_corrected`,
`demo_3_bad_measurement`, `demo_4_insufficient_evidence`). Every value in
these scenarios is tagged `simulated: true` in the raw API response — see
`docs/demo_guide.md`.

### With a real camera

Use the **Camera** or **Upload Frame** tab. This calls the real CPU
fallback vision backend (`backend/inference/fallback/vision_backend.py`),
which does genuine frame-quality analysis via OpenCV. See
`docs/limitations.md` for exactly what it can and can't detect without the
Qwen3-VL/Qualcomm backend.

### With a real Arduino

Flash `scripts/arduino/telemetry_sketch.ino` (uncomment the block matching
your experiment), connect over USB, and configure
`TelemetryService(port=...)` in `backend/telemetry/service.py` with the
correct serial port. Not verified against physical hardware in this
snapshot — see `docs/limitations.md`.

### On Snapdragon hardware

Follow `docs/qualcomm_deployment.md` end to end: install `qai_hub_models`
under x64 Python, export Qwen3-VL-4B-Instruct / Whisper-Small through
Qualcomm AI Hub, point `QUALCOMM_VISION_MODEL_PATH` /
`QUALCOMM_SPEECH_MODEL_PATH` at the resulting artifacts, and complete the
`analyze()`/`transcribe()` implementations in `backend/inference/qualcomm/`.
The Settings screen will then show `Qualcomm NPU` as the active backend.

## Testing

```bash
bash scripts/run_tests.sh
```

Runs the full pytest suite (94 tests: experiment engine, verification,
evidence fusion, perception adapter, evaluation, telemetry, inference
backends, API) and the frontend production
build/type-check in one command.

## Benchmarking

```bash
python benchmarks/benchmark.py --runs 30
```

Produces `benchmarks/results/benchmark_report.{json,md}` with real local
CPU latency/memory numbers, and a clearly separate, unmeasured "Qualcomm AI
Hub reference metrics" section. See `docs/benchmarking.md`.

Objective 2 perception contracts, labeled test fixtures, and the
provenance-aware evaluation harness are documented in
`docs/vision_evaluation.md` and `datasets/ldr/`. No real LDR photographs or
real-world perception metrics are included.

The Qwen3-VL provider foundation is documented in `docs/ai_models.md`. It is
not an active runtime: no Qwen3-VL weights have been downloaded and no actual
Qwen inference has been validated.

## Safety

ANVEṢHA only supports low-voltage (5V logic), low-risk experiments and
displays: *"AI-generated guidance is educational. Verify procedures against
the official experiment manual and follow appropriate lab safety
procedures."* It does not support high-voltage work, explosives, weapons,
hazardous chemicals, or dangerous machinery.

## Documentation index

- `docs/architecture.md`
- `docs/problem_statement.md`
- `docs/qualcomm_deployment.md`
- `docs/ai_models.md`
- `docs/experiment_engine.md`
- `docs/verification_engine.md`
- `docs/benchmarking.md`
- `docs/demo_guide.md`
- `docs/limitations.md`

## Future work

More experiments (motors, digital logic gates, op-amp circuits);
better/real component recognition once Qwen3-VL is wired up on Snapdragon;
automatic PDF experiment reports; additional sensor types; a dedicated
"Experiment Report" export screen; microphone UI for the voice interaction
already stubbed in the backend.

## License

MIT — see `LICENSE`.
