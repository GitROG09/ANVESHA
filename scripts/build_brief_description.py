"""Generates submission/brief_project_description.pdf"""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors

ACCENT = colors.HexColor("#0F766E")
INK = colors.HexColor("#14171A")
INK2 = colors.HexColor("#4B5563")
LINE = colors.HexColor("#D1D5DB")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=22, textColor=INK, spaceAfter=4, leading=26))
styles.add(ParagraphStyle("Tagline", fontName="Helvetica-Oblique", fontSize=12, textColor=ACCENT, spaceAfter=14))
styles.add(ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12.5, textColor=ACCENT, spaceBefore=14, spaceAfter=6))
styles.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=10, textColor=INK, leading=14.5, alignment=TA_LEFT))
styles.add(ParagraphStyle("Small", fontName="Helvetica", fontSize=8.5, textColor=INK2, leading=12))
styles.add(ParagraphStyle("MyBullet", fontName="Helvetica", fontSize=10, textColor=INK, leading=14, leftIndent=14, bulletIndent=2))

def h2(t): return Paragraph(t, styles["H2"])
def body(t): return Paragraph(t, styles["Body"])
def bullets(items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{i}", styles["MyBullet"]) for i in items]

doc = SimpleDocTemplate(
    "/home/claude/anvesha-ai/submission/brief_project_description.pdf",
    pagesize=LETTER,
    topMargin=0.65 * inch, bottomMargin=0.65 * inch,
    leftMargin=0.75 * inch, rightMargin=0.75 * inch,
)

story = []
story.append(Paragraph("ANVESHA AI", styles["H1"]))
story.append(Paragraph("Observe. Investigate. Verify. &mdash; On-Device Intelligence for Physical Experiment Verification", styles["Tagline"]))
story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceAfter=10))

story.append(h2("PROBLEM"))
story.append(body(
    "Engineering students follow lab manuals and datasheets to build circuits, but nothing digital checks whether "
    "the physical setup actually matches the procedure. A wire on the wrong pin, a reversed component, or an "
    "out-of-range reading is normally caught only by a TA walking the room, or by hours of undirected trial and "
    "error &mdash; costing lab time and the debugging intuition the exercise is meant to build."
))

story.append(h2("SOLUTION"))
story.append(body(
    "ANVESHA AI is an on-device multimodal system that continuously verifies a physical experiment by fusing "
    "three evidence sources against an explicit procedure definition: visual evidence (camera), procedural "
    "evidence (a structured experiment schema), and measurement evidence (real or simulated sensor telemetry). "
    "It reports PASS, WARNING, DEVIATION, or INSUFFICIENT_EVIDENCE with a plain-language explanation of what was "
    "observed, what was expected, why it matters, and what to check next. When the student corrects the issue and "
    "presses Verify Again, the state flips from DEVIATION to PASS live &mdash; the core demonstration of the product."
))

story.append(h2("TARGET USERS"))
story.append(body("Engineering students, lab instructors/TAs, and makers working through guided low-voltage electronics experiments in university labs, maker spaces, and remote/asynchronous learning settings."))

story.append(h2("CORE INNOVATION"))
story.append(body(
    "A deliberate separation between perception and verification. The vision/speech models answer only "
    "&ldquo;what do I see or hear&rdquo;; a deterministic, rule-based verification engine separately answers "
    "&ldquo;does that satisfy the experiment.&rdquo; This keeps every verdict auditable &mdash; traceable to a "
    "specific rule and a specific piece of evidence &mdash; rather than resting on an unexplainable model opinion."
))

story.append(h2("MULTIMODAL ARCHITECTURE & QUALCOMM AI HUB"))
story.append(body(
    "Vision (target: Qwen3-VL-4B-Instruct) and speech (target: Whisper-Small, quantized) are designed to run via "
    "Qualcomm AI Hub, exported to a QNN context binary and executed on the Snapdragon NPU. The backend implements "
    "a clean inference abstraction (base / fallback / qualcomm) so the UI never depends on Qualcomm APIs directly, "
    "with automatic, verified fallback to a CPU/OpenCV backend when NPU hardware isn&rsquo;t present. Device "
    "detection and runtime status are reported honestly &mdash; the system never claims NPU acceleration it "
    "cannot verify."
))

story.append(h2("PHYSICAL EXPERIMENT VERIFICATION"))
story.append(body(
    "Three low-risk, well-defined experiments ship with the system &mdash; an LDR light-sensor voltage divider, "
    "an HC-SR04 ultrasonic distance sensor, and an LED current-limiting resistor circuit &mdash; each with an "
    "explicit connection map, expected measurement range, and validation rules, loaded from an extensible JSON schema."
))

story.append(h2("PRIVACY"))
story.append(body(
    "No cloud AI APIs are used for inference (no OpenAI, Gemini, or Claude API calls). Camera frames, audio, and "
    "experiment data are processed locally; network access is not required for AI inference."
))

story.append(h2("HARDWARE INTEGRATION"))
story.append(body(
    "An optional Arduino telemetry path reads real sensor values over a documented USB-serial protocol "
    "(see scripts/arduino/telemetry_sketch.ino). A clearly labeled simulation mode provides the same data shape "
    "for development and demo purposes when hardware isn&rsquo;t attached &mdash; simulated values are tagged "
    "end-to-end and never presented as real."
))

story.append(h2("DEMO"))
story.append(body(
    "A deterministic demo mode reproduces the core loop without requiring a camera or Arduino at judging time: "
    "a correct circuit (PASS), an intentionally wrong connection (DEVIATION), the same circuit corrected "
    "(PASS again), an out-of-range measurement (DEVIATION), and an insufficiently clear frame "
    "(INSUFFICIENT_EVIDENCE) &mdash; each scenario clearly labeled SIMULATED and structurally separate from the "
    "production verification path."
))

story.append(h2("TECHNICAL IMPLEMENTATION"))
story.extend(bullets([
    "Backend: Python, FastAPI, Pydantic schemas, pytest (28 automated tests, passing)",
    "Frontend: React, TypeScript, Vite &mdash; ten screens covering the full experiment workflow",
    "Verification engine: deterministic rule evaluation, fully unit-tested independent of any model",
    "Benchmark harness with real local CPU latency/memory numbers, kept explicitly separate from unmeasured "
    "Qualcomm AI Hub reference figures",
]))

story.append(h2("LIMITATIONS"))
story.append(body(
    "No Snapdragon NPU hardware was available during development, so on-device Qwen3-VL/Whisper inference is "
    "implemented as a correct, honestly-failing abstraction rather than executed end-to-end; the CPU fallback "
    "vision backend performs real frame-quality analysis but does not attempt pin-level wire tracing without a "
    "trained model. Full details in docs/limitations.md."
))

story.append(h2("FUTURE SCOPE"))
story.append(body(
    "Additional experiments, on-device Qwen3-VL component/connection recognition once deployed to Snapdragon "
    "hardware, automatic PDF experiment reports, additional sensor types, and a voice-interaction UI."
))

story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=0.75, color=LINE, spaceAfter=6))
story.append(Paragraph(
    "AI-generated guidance is educational. Verify procedures against the official experiment manual and follow "
    "appropriate lab safety procedures.", styles["Small"]
))

doc.build(story)
print("wrote brief_project_description.pdf")
