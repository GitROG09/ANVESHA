# Demo Guide

## Recommended flow (3-5 minutes)

1. **Home screen** — show the tagline, runtime status bar (CPU Fallback or
   Qualcomm NPU depending on the machine), and the OBSERVE → INVESTIGATE →
   VERIFY strip.
2. **Experiments → LDR Light Sensor Calibration** — show the procedure
   screen: components, expected connections, steps, expected measurement
   range. This is the "what should happen" baseline.
3. **Start Live Verification.**
4. Select **Demo Scenario → demo_2_wrong_connection** and press **Verify**.
   - Result: `DEVIATION`. The panel shows the exact expected vs. observed
     pin (`A0` vs `A1`), why it matters, and the recommended action.
   - Say out loud: "This scenario is deliberately scripted for a
     reproducible demo — it's clearly labeled SIMULATED in the evidence
     notes. The same code path runs for a real camera frame; see the CPU
     fallback backend live in the Upload Frame / Camera tabs."
5. Switch the scenario dropdown to **demo_2b_corrected** and press
   **Verify Again**.
   - Result: `PASS`. Point at the History row at the bottom of the result
     panel: `DEVIATION → PASS`. This before/after transition is the core
     demonstration the whole product is built around.
6. Optionally show **demo_3_bad_measurement** (wiring correct, but the
   HC-SR04 reading of 650cm is outside the sensor's valid 2-400cm range →
   `DEVIATION` on the measurement, not the connection) to show the engine
   catches a different failure mode with the same mechanism.
7. Optionally show **demo_4_insufficient_evidence** (a scripted blurry
   frame) to demonstrate the system refuses to guess when evidence is weak.
8. **Performance tab** — show the real local benchmark numbers, and point
   out the clearly separated "not measured here" Qualcomm reference section
   — this is a deliberate, honesty-first design choice worth calling out to
   judges.
9. **Settings tab** — show the runtime status detail and privacy statement
   (no cloud AI APIs, local processing, network not required for inference).

## Live camera / real hardware variant (if available on the demo machine)

Instead of steps 4-5, use **Camera** or **Upload Frame** with a real LDR
breadboard circuit:
1. Wire the LDR to A1 instead of A0 on purpose.
2. Capture a frame → the CPU fallback backend runs real OpenCV quality
   checks (this is genuine inference, not scripted) but — per
   `docs/ai_models.md` — will not attempt pin-level tracing without the
   Qwen3-VL/Qualcomm backend, so for a full live wrong-pin catch on
   real hardware, the Qualcomm backend from `docs/qualcomm_deployment.md`
   needs to be completed first. Until then, the live camera path
   demonstrates the honest frame-quality gate (reject blurry/dark frames)
   and the demo-scenario path demonstrates the full connection-level
   verification loop.
3. Fix the wire, capture again, press Verify Again.

## Why demo mode exists at all

The project brief requires the demo to work even if physical hardware or a
reliable camera setup isn't available at judging time. `backend/services/
simulation.py` provides four fixed scenarios reachable only through
`/api/demo/*` endpoints — structurally separate from the production
`/api/vision/analyze` + `/api/verify` path, and every simulated observation
is tagged `simulated: true` end to end (visible in the raw API response),
so nothing here is presented as if it came from a real camera.
