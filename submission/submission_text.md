# ANVEṢHA AI — Submission Text

## 1. Full description

ANVEṢHA AI is an on-device, multimodal AI system that verifies physical
engineering experiments by fusing camera observation, the experiment
procedure, and sensor measurements against an explicit, structured
definition of what the experiment should look like. Where existing digital
lab material only tells a student what to do, ANVEṢHA continuously checks
what they actually built, reporting PASS, WARNING, DEVIATION, or
INSUFFICIENT_EVIDENCE with a plain-language explanation: what was observed,
what was expected, why it matters, and what to check next.

The system's core design decision is separating perception from
verification. A vision-language model (targeting Qwen3-VL-4B-Instruct) and
a speech model (targeting Whisper-Small) answer only "what do I see or
hear," deployed to run locally via Qualcomm AI Hub on a Snapdragon NPU. A
fully deterministic, rule-based verification engine separately answers
"does that satisfy the experiment" by comparing detected connections and
measurements against the experiment's expected connections, tolerances, and
validation rules. This keeps every verdict auditable — traceable to a
specific rule and a specific piece of evidence — rather than resting on an
unexplainable model opinion, and makes the engine fully unit-testable
without any model dependency at all.

Three low-risk, well-defined experiments ship with the system: an LDR
light-sensor voltage divider, an HC-SR04 ultrasonic distance sensor, and an
LED current-limiting resistor circuit, each defined in an extensible JSON
schema covering components, connections, procedure steps, expected
measurement ranges, and validation rules. An optional Arduino telemetry
path reads real sensor values over a documented USB-serial protocol, with a
clearly labeled simulation mode for development and demo purposes when
hardware isn't attached.

The inference layer is built behind a clean abstraction — `base`,
`fallback` (CPU/OpenCV, runs anywhere), and `qualcomm` (Snapdragon NPU via
Qualcomm AI Hub) — so the UI and verification engine never depend on
Qualcomm APIs directly, and the system automatically and verifiably falls
back to CPU when NPU hardware isn't present, reporting the true active
backend rather than assuming acceleration. No cloud AI APIs are used for
inference anywhere in the system.

A deterministic demo mode reproduces the full verification loop — a
correct circuit, an intentionally wrong connection, the same circuit
corrected, an out-of-range measurement, and an insufficiently clear
frame — without requiring a camera or Arduino at judging time, with every
simulated value clearly tagged as such throughout the API and UI.

This submission is built with an explicit commitment to not fabricating
capability: no Snapdragon NPU hardware or downloadable model weights were
available during development, so the Qualcomm integration is implemented as
a correct, honestly-failing abstraction and a deployment guide sourced from
Qualcomm's public documentation, clearly distinguished throughout the
codebase and documentation from what was actually built and tested (28
passing automated tests, a live-tested FastAPI backend, a building
React/TypeScript frontend, and a real local benchmark harness).

## 2. 500-word description

Engineering students learn by following lab manuals, but nothing in
today's digital lab material checks whether the physical circuit a student
builds actually matches the procedure. A wire on the wrong pin, a reversed
component, or an unexpected reading is normally caught only by a TA walking
the room, or by hours of undirected trial and error — costing lab time and
the debugging intuition the exercise is meant to build.

ANVEṢHA AI closes that gap. It's an on-device, multimodal AI system that
continuously verifies a physical experiment by combining three evidence
sources against an explicit procedure definition: visual evidence from a
camera, procedural evidence from a structured experiment schema, and
measurement evidence from real or simulated sensor telemetry. It reports
one of four states — PASS, WARNING, DEVIATION, or INSUFFICIENT_EVIDENCE —
with a specific, plain-language explanation of what was observed, what was
expected, why the difference matters, and what to check next. When a
student fixes the issue and presses Verify Again, the state flips from
DEVIATION to PASS live — the central demonstration the product is built
around.

The core innovation is a deliberate separation between AI perception and
verification logic. Vision and speech models (targeting Qwen3-VL-4B-Instruct
and Whisper-Small, deployed via Qualcomm AI Hub to run on a Snapdragon NPU)
answer only "what do I see or hear." A fully deterministic, rule-based
verification engine separately answers "does that satisfy the experiment,"
comparing detected connections and measurements against the experiment's
expected values. Every verdict is therefore auditable, traceable to a
specific rule and evidence item, and the engine is fully unit-testable
without any model dependency — which is why its logic has 28 passing
automated tests despite this development environment having no GPU or NPU
available.

Three low-risk, well-defined experiments ship with the system today — an
LDR light sensor, an HC-SR04 ultrasonic sensor, and an LED/resistor
circuit — loaded from an extensible JSON schema so new experiments can be
added without code changes. An optional Arduino integration reads real
sensor values over a documented serial protocol, alongside a clearly
labeled simulation mode used for development and for a deterministic demo
that works even without a camera or hardware attached at judging time.

The inference layer is built behind a clean abstraction so the UI and
verification engine never depend on Qualcomm APIs directly, and the system
transparently falls back to a real CPU/OpenCV vision backend — which
performs genuine frame-quality gating, not fabricated detections — when NPU
hardware isn't present. No cloud AI APIs are used anywhere; all data stays
on-device by design, which is also why Snapdragon's on-device NPU
acceleration matters architecturally, not just as a checkbox.

This submission is explicit about its current limitations: no Snapdragon
hardware was available during development, so the Qualcomm/NPU path is a
correct, tested abstraction and a sourced deployment guide rather than
something executed end-to-end here — clearly documented in
`docs/limitations.md` rather than concealed behind invented benchmarks or
APIs.

## 3. 250-word description

ANVEṢHA AI is an on-device, multimodal AI system that verifies physical
engineering experiments — checking not just what a lab manual says to do,
but what a student actually built. It fuses camera observation, the
experiment procedure, and sensor measurements into a single verdict: PASS,
WARNING, DEVIATION, or INSUFFICIENT_EVIDENCE, each with a plain-language
explanation of what was observed, what was expected, why it matters, and
what to check next.

Its core innovation is separating perception from verification: vision and
speech models (targeting Qwen3-VL-4B-Instruct and Whisper-Small, deployed
via Qualcomm AI Hub for Snapdragon NPU execution) only answer "what do I
see or hear." A deterministic, rule-based verification engine separately
answers "does that satisfy the experiment," making every verdict auditable
rather than resting on an unexplainable model opinion.

Three low-risk experiments ship today — an LDR light sensor, an HC-SR04
ultrasonic sensor, and an LED/resistor circuit — defined in an extensible
JSON schema, with optional real Arduino telemetry and a clearly labeled
simulation mode for demos. A clean inference abstraction lets the system
run on CPU today and fall back automatically and honestly when Snapdragon
NPU hardware isn't present — no cloud AI APIs are used anywhere.

Built and tested in this snapshot: 28 passing automated tests, a live-tested
FastAPI backend, a building React/TypeScript frontend across ten screens,
and a real local benchmark harness. Not yet executable: NPU inference
itself, since no Snapdragon hardware was available during development —
documented honestly rather than faked.

## 4. 100-word description

ANVEṢHA AI verifies physical engineering experiments on-device, fusing
camera observation, the experiment procedure, and sensor measurements to
report PASS, WARNING, DEVIATION, or INSUFFICIENT_EVIDENCE — explaining what
was observed, expected, and what to fix next. A deterministic verification
engine, kept separate from the vision/speech models (targeting Qwen3-VL and
Whisper-Small via Qualcomm AI Hub), makes every verdict auditable. Three
low-risk experiments ship today, with real Arduino telemetry and a labeled
simulation mode for demos. No cloud AI APIs are used. Built with 28 passing
tests, a working backend and frontend, and complete honesty about what
hasn't yet run on real Snapdragon hardware.

## 5. Short tagline

Observe. Investigate. Verify. — AI that checks what you built, not just
what you typed.

## 6. Key innovation

Separating AI perception from verification logic: models answer "what do I
see," a deterministic rule engine answers "does that satisfy the
experiment" — making every verdict auditable and independently testable.

## 7. Technology stack

- **Backend:** Python, FastAPI, Pydantic, pytest
- **Frontend:** React, TypeScript, Vite
- **Vision (target):** Qwen3-VL-4B-Instruct via Qualcomm AI Hub / QNN runtime
- **Vision (implemented fallback):** OpenCV-based frame-quality heuristics
- **Speech (target):** Whisper-Small (quantized) via Qualcomm AI Hub / QNN runtime
- **Hardware:** Arduino (USB serial telemetry), documented sketch included
- **Benchmarking:** custom harness (`benchmarks/benchmark.py`) — real local
  latency/memory measurement, no fabricated NPU numbers

## 8. Qualcomm integration explanation

The backend implements a clean `base` / `fallback` / `qualcomm` inference
abstraction so the UI and verification engine never touch Qualcomm APIs
directly. `backend/inference/qualcomm/` includes real device detection
(OS/architecture + `qai_hub`/`qai_hub_models` package presence), a runtime
status reporter surfaced in the Settings screen, and vision/speech backend
classes that correctly report themselves unavailable — rather than
fabricate output — on any host without confirmed Snapdragon hardware and a
configured model artifact. `docs/qualcomm_deployment.md` documents the full,
sourced deployment path (model export via `qai_hub_models`, QNN runtime
installation, the Windows-ARM64 Python gotcha, NPU verification, and
troubleshooting) for completing the integration on real hardware — none of
which was available during development of this submission.

## 9. Problem statement

Lab procedures describe what should happen; nothing digital checks what a
student actually built. Wiring mistakes and misread diagrams are caught
today only by a TA's manual inspection or by unguided trial and error,
costing lab time and the debugging intuition labs are meant to teach —
especially in large classes or remote/asynchronous formats without
real-time supervision.

## 10. Demo description

A deterministic, reproducible demo requiring no camera or Arduino: select
the LDR experiment, run the "wrong connection" scenario (sensor output
wired to A1 instead of A0) to see a DEVIATION with the exact expected-vs-
observed pin mismatch, then run the "corrected" scenario and press Verify
Again to watch the state flip to PASS live. Additional scenarios demonstrate
a measurement-based DEVIATION (an out-of-range ultrasonic reading with
correct wiring) and an INSUFFICIENT_EVIDENCE result from a deliberately
low-quality frame. Every scenario is clearly labeled SIMULATED end-to-end
in the raw API response, kept structurally separate from the production
camera-based verification path.
