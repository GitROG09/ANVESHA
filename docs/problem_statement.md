# Problem Statement

## The gap

Engineering students and makers learn by following procedures — lab sheets,
datasheets, manuals. These documents describe what *should* happen:
"connect the sensor output to A0," "the divider should read 400-800 ADC in
normal light."

None of them check whether what the student actually built matches that
description. A student can:

- connect a wire to the wrong pin (A1 instead of A0),
- use the wrong component value (a 1k resistor instead of 10k),
- wire a component with reversed polarity,
- misread a diagram and mirror a connection,
- get a plausible-looking but out-of-range measurement and not know why.

Today, the feedback loop for these mistakes is entirely manual: a TA walks
the room, or the student debugs by trial and error, often not realizing
*which* assumption was wrong. Digital lab materials — PDFs, slide decks,
even interactive tutorials — are one-directional. They tell; they don't
check.

## Why this matters

- **Time.** Hours of lab time are lost to wiring mistakes that a five-second
  visual check would catch.
- **Learning.** A student who never learns *why* their circuit failed
  doesn't build the debugging intuition the lab is meant to teach.
- **Scale.** In large classes or remote/asynchronous lab formats, there
  often isn't a TA available to check every setup in real time.

## What ANVEṢHA AI does about it

ANVEṢHA closes the loop by continuously comparing three sources of evidence
against the experiment procedure:

1. **Visual evidence** — what the camera actually sees of the physical setup.
2. **Procedural evidence** — the structured, machine-readable experiment
   definition (components, connections, expected measurements).
3. **Measurement evidence** — real or simulated sensor telemetry.

It reports one of four states — `PASS`, `WARNING`, `DEVIATION`, or
`INSUFFICIENT_EVIDENCE` — with a specific explanation of what was expected,
what was observed, why it matters, and what to check next. When the student
fixes the issue, they press **Verify Again** and see the state flip from
`DEVIATION` to `PASS` in front of them — the core "before/after" moment the
whole product is built around.

## Scope and honesty about limitations

ANVEṢHA deliberately supports a **small number of well-defined, low-risk
experiments** (LDR light sensor, HC-SR04 ultrasonic sensor, LED/resistor
circuit) rather than claiming to understand arbitrary engineering setups.
See `docs/limitations.md` for a full accounting of what is and isn't
implemented in this snapshot of the project.
