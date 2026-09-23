# ANVEṢHA AI — Pitch Script

## 3-minute pitch

Every engineering student has had this moment: you followed the lab manual
exactly, but your circuit doesn't work, and you have no idea which step
went wrong.

That's the gap ANVEṢHA AI closes. Lab manuals tell you what should happen.
They never check what you actually built.

ANVEṢHA is an on-device AI system that watches your physical setup through
a camera, reads the experiment procedure, checks your sensor readings, and
tells you — in plain language — exactly where reality diverges from the
manual.

Here's how it works. Three sources of evidence come together: what the
camera sees, what the procedure expects, and what the sensors measure. A
verification engine compares them and returns one of four states — PASS,
WARNING, DEVIATION, or INSUFFICIENT EVIDENCE — with a specific explanation:
what we observed, what was expected, why it matters, and what to check
next.

Let me show you. This is an LDR light sensor circuit. The procedure expects
the sensor output on pin A0. Here, it's actually wired to A1.
[Demo: DEVIATION appears, with the exact pin mismatch shown.]
The student moves the wire, presses Verify Again —
[Demo: PASS.]
— and that's it. That before-and-after moment is the whole product.

Critically, the AI's perception and the verification logic are separate.
The vision model only answers "what do I see." A deterministic rule engine
answers "does that satisfy the experiment." That separation means every
verdict is auditable — you can trace it back to a specific rule and a
specific piece of evidence, not an unexplainable model opinion.

We built this for Snapdragon. Privacy, low latency, and offline operation
aren't marketing lines here — they're why the architecture puts inference
on-device by design, with a clean abstraction that runs on CPU today and
is built to run through Qualcomm AI Hub on a Snapdragon NPU.

We're honest about where we are: no Snapdragon hardware was available while
building this, so the NPU path is a fully documented, verified deployment
guide rather than something we've run ourselves. Everything we claim to
have measured, we've actually measured — and everything we haven't, we say
so.

That's ANVEṢHA AI — observe, investigate, verify.

---

## 5-minute pitch

Every engineering student has had this moment: you followed the lab manual
exactly, but your circuit doesn't work, and you have no idea which step
went wrong. Was it a wire? A component? A misread diagram? Today, the only
way to find out is a TA walking the room, or hours of undirected trial and
error. In large classes, or remote and asynchronous lab formats, that TA
often isn't there.

Digital lab material — PDFs, slide decks, even interactive tutorials — is
one-directional. It tells; it doesn't check. That's the gap ANVEṢHA AI
closes.

ANVEṢHA is an on-device, multimodal AI system for physical experiment
verification. It combines four things: camera observation of your physical
setup, the experiment procedure, sensor measurements, and optional voice
interaction. It fuses these into a single verdict — PASS, WARNING,
DEVIATION, or INSUFFICIENT EVIDENCE — and explains exactly what it observed,
what was expected, why the difference matters, and what to check next.

Let's walk through the architecture. At the base is an experiment engine —
a structured, machine-readable definition of each experiment: its
components, its expected connections, its measurement ranges, its
validation rules. Right now we support three low-risk, well-defined
experiments: an LDR light sensor, an HC-SR04 ultrasonic sensor, and an
LED/resistor circuit. We chose depth over breadth — a system that
confidently understands three experiments is more useful than one that
vaguely gestures at understanding everything.

On top of that sits the inference layer — vision and speech models whose
only job is perception: "what do I see, what did you say." We're targeting
Qwen3-VL-4B-Instruct for vision and Whisper-Small for speech, both designed
to run through Qualcomm AI Hub on a Snapdragon NPU.

And separate from both of those is the verification engine — the part we
think is the real innovation. It's fully deterministic, rule-based logic
that compares what the vision model saw against what the procedure expects,
and what the sensors measured against the expected range. It never asks a
language model "is this circuit correct" — because that answer would be
unauditable. Instead, every verdict traces back to a specific rule and a
specific piece of evidence. We think that's what makes this trustworthy
enough to actually use in a lab.

Let me show you the core loop. [Demo: wrong-pin DEVIATION → correction →
Verify Again → PASS.] That transition — DEVIATION to PASS, live — is the
moment that makes the whole concept click.

Now, why Snapdragon specifically? Three reasons that are architectural, not
just marketing. Privacy — a camera pointed at a student's desk should never
need to leave that desk. Latency — this is a tight loop of capture, verify,
correct, re-verify; round-tripping to a cloud API would kill that
interaction. And reliability — university labs and maker spaces don't
always have solid network access, and this needs to work regardless.

We want to be upfront about where this stands today. We built and tested
the full application — the experiment schema, the verification engine with
twenty-eight passing automated tests, a working FastAPI backend we
booted and hit live, and a complete React/TypeScript frontend across ten
screens. What we could not do in this development environment is run
anything on actual Snapdragon NPU hardware or download the Qwen3-VL and
Whisper model weights — no Snapdragon device and no hub access were
available to us while building. So the Qualcomm integration is a correct,
tested abstraction layer plus a deployment guide sourced from Qualcomm's
own documentation, not something we've executed ourselves yet. We'd rather
tell you that clearly than show you a fabricated benchmark.

Where this goes: more experiments, real on-device component recognition
once deployed to Snapdragon hardware, automatic report generation, and a
voice interface that's already stubbed into the backend.

ANVEṢHA AI — observe, investigate, verify. Thank you.
