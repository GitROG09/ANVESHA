const pptxgen = require("pptxgenjs");

const C = {
  bg: "0F1214",
  panel: "171B1E",
  line: "2A3136",
  ink1: "EEF1F2",
  ink2: "AAB3B8",
  ink3: "6D787E",
  accent: "5EEAD4",
  accentDim: "2F6E63",
  pass: "4ADE80",
  warn: "FBBF24",
  deviation: "F87171",
  insufficient: "7DD3FC",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5

function bgSlide() {
  const s = pres.addSlide();
  s.background = { color: C.bg };
  return s;
}

function kicker(s, text, opts = {}) {
  s.addText(text.toUpperCase(), {
    x: 0.6, y: opts.y ?? 0.5, w: 8, h: 0.4,
    fontFace: "Consolas", fontSize: 13, color: C.accent, charSpacing: 2, isTextBox: true, margin: 0,
  });
}

function pageNum(s, n) {
  s.addText(`${n} / 10`, {
    x: 12.4, y: 7.05, w: 0.8, h: 0.35, fontFace: "Consolas", fontSize: 10, color: C.ink3,
    align: "right", isTextBox: true, margin: 0,
  });
}

// ---------- Slide 1: Title ----------
{
  const s = bgSlide();
  s.addText("OBSERVE  ·  INVESTIGATE  ·  VERIFY", {
    x: 0.9, y: 2.15, w: 10, h: 0.5, fontFace: "Consolas", fontSize: 15, color: C.accent, charSpacing: 3, isTextBox: true, margin: 0,
  });
  s.addText([
    { text: "ANVEṢHA", options: { color: C.ink1 } },
    { text: "AI", options: { color: C.accent } },
  ], {
    x: 0.85, y: 2.6, w: 11.5, h: 1.6, fontFace: "IBM Plex Sans", fontSize: 64, bold: true, isTextBox: true, margin: 0,
  });
  s.addText("On-Device Intelligence for Physical Experiment Verification", {
    x: 0.9, y: 4.15, w: 10.5, h: 0.6, fontFace: "IBM Plex Sans", fontSize: 20, color: C.ink2, isTextBox: true, margin: 0,
  });
  s.addText("\u201CAI that verifies what you built, not just what you typed.\u201D", {
    x: 0.9, y: 4.9, w: 10.5, h: 0.5, fontFace: "IBM Plex Sans", fontSize: 15, italic: true, color: C.ink3, isTextBox: true, margin: 0,
  });
  s.addText("Snapdragon AI Lab Build & Present Challenge", {
    x: 0.9, y: 6.7, w: 8, h: 0.4, fontFace: "Consolas", fontSize: 12, color: C.ink3, isTextBox: true, margin: 0,
  });
}

// ---------- Slide 2: The Problem ----------
{
  const s = bgSlide();
  kicker(s, "The Problem");
  s.addText("Procedures tell you what to do. Nothing checks what you built.", {
    x: 0.6, y: 1.0, w: 11.5, h: 0.9, fontFace: "IBM Plex Sans", fontSize: 30, bold: true, color: C.ink1, isTextBox: true, margin: 0,
  });

  const steps = ["Procedure", "Physical setup", "Human assumption", "Wrong connection /\nunexpected result", "Trial and error"];
  const startX = 0.6, boxW = 2.1, gap = 0.35, y = 2.6, boxH = 1.1;
  steps.forEach((label, i) => {
    const x = startX + i * (boxW + gap);
    s.addShape("roundRect", { x, y, w: boxW, h: boxH, rectRadius: 0.08, fill: { color: C.panel }, line: { color: C.line, width: 1 } });
    s.addText(label, { x, y, w: boxW, h: boxH, align: "center", valign: "middle", fontFace: "IBM Plex Sans", fontSize: 12.5, color: i === 3 ? C.deviation : C.ink1, isTextBox: true, margin: 0 });
    if (i < steps.length - 1) {
      s.addText("\u2192", { x: x + boxW, y, w: gap, h: boxH, align: "center", valign: "middle", fontSize: 16, color: C.ink3, isTextBox: true, margin: 0 });
    }
  });

  s.addText([
    { text: "A wrong pin, a reversed component, an out-of-range reading \u2014 caught today only by a TA walking the room, or by hours of undirected debugging.", options: {} },
  ], { x: 0.6, y: 4.3, w: 10.8, h: 1.2, fontFace: "IBM Plex Sans", fontSize: 16, color: C.ink2, isTextBox: true, margin: 0 });
  pageNum(s, 2);
}

// ---------- Slide 3: The Insight ----------
{
  const s = bgSlide();
  kicker(s, "The Insight");
  s.addText("Digital instructions know what should happen.", {
    x: 0.6, y: 2.3, w: 11.5, h: 0.8, fontFace: "IBM Plex Sans", fontSize: 28, color: C.ink2, isTextBox: true, margin: 0,
  });
  s.addText("ANVEṢHA understands what is actually happening.", {
    x: 0.6, y: 3.15, w: 11.5, h: 0.9, fontFace: "IBM Plex Sans", fontSize: 32, bold: true, color: C.accent, isTextBox: true, margin: 0,
  });
  pageNum(s, 3);
}

// ---------- Slide 4: How it works ----------
{
  const s = bgSlide();
  kicker(s, "How ANVEṢHA Works");
  s.addText("Evidence fusion, not model opinion", {
    x: 0.6, y: 1.0, w: 11.5, h: 0.7, fontFace: "IBM Plex Sans", fontSize: 28, bold: true, color: C.ink1, isTextBox: true, margin: 0,
  });

  const inputs = ["Camera", "Procedure", "Measurements", "Voice"];
  inputs.forEach((label, i) => {
    const x = 0.6 + i * 2.85, y = 2.15, w = 2.55, h = 0.85;
    s.addShape("roundRect", { x, y, w, h, rectRadius: 0.08, fill: { color: C.panel }, line: { color: C.accentDim, width: 1 } });
    s.addText(label, { x, y, w, h, align: "center", valign: "middle", fontFace: "Consolas", fontSize: 14, color: C.accent, isTextBox: true, margin: 0 });
  });
  s.addText("\u2193", { x: 0.6, y: 3.15, w: 11.5, h: 0.4, align: "center", fontSize: 18, color: C.ink3, isTextBox: true, margin: 0 });

  const pipeline = [
    ["Multimodal AI\n(perception)", C.ink1],
    ["Evidence Fusion", C.ink1],
    ["Verification Engine\n(rule-based)", C.accent],
  ];
  pipeline.forEach(([label, color], i) => {
    const x = 1.9 + i * 3.4, y = 3.75, w = 3.0, h = 1.0;
    s.addShape("roundRect", { x, y, w, h, rectRadius: 0.08, fill: { color: C.bg }, line: { color: C.line, width: 1.25 } });
    s.addText(label, { x, y, w, h, align: "center", valign: "middle", fontFace: "IBM Plex Sans", fontSize: 13, color, isTextBox: true, margin: 0 });
    if (i < pipeline.length - 1) {
      s.addText("\u2192", { x: x + w, y, w: 0.4, h, align: "center", valign: "middle", fontSize: 16, color: C.ink3, isTextBox: true, margin: 0 });
    }
  });

  s.addText("Perception answers \u201Cwhat do I see?\u201D  \u2014  the verification engine answers \u201Cdoes that satisfy the experiment?\u201D", {
    x: 0.6, y: 5.15, w: 11.5, h: 0.6, fontFace: "IBM Plex Sans", fontSize: 14, italic: true, color: C.ink2, isTextBox: true, margin: 0,
  });
  pageNum(s, 4);
}

// ---------- Slide 5: Live Experiment ----------
{
  const s = bgSlide();
  kicker(s, "Live Experiment");
  s.addText("Wrong pin to verified \u2014 live", {
    x: 0.6, y: 1.0, w: 11.5, h: 0.7, fontFace: "IBM Plex Sans", fontSize: 28, bold: true, color: C.ink1, isTextBox: true, margin: 0,
  });

  const flow = [
    ["Incorrect\nconnection", C.deviation],
    ["Detection", C.ink1],
    ["Correction", C.ink1],
    ["Re-verification", C.ink1],
    ["PASS", C.pass],
  ];
  flow.forEach(([label, color], i) => {
    const x = 0.6 + i * 2.5, y = 2.8, w = 2.15, h = 1.0;
    s.addShape("roundRect", { x, y, w, h, rectRadius: 0.08, fill: { color: C.panel }, line: { color: C.line, width: 1 } });
    s.addText(label, { x, y, w, h, align: "center", valign: "middle", fontFace: "Consolas", fontSize: 13, bold: i === 0 || i === 4, color, isTextBox: true, margin: 0 });
    if (i < flow.length - 1) {
      s.addText("\u2192", { x: x + w, y, w: 0.35, h, align: "center", valign: "middle", fontSize: 16, color: C.ink3, isTextBox: true, margin: 0 });
    }
  });

  s.addText("LDR sensor OUT wired to A1 instead of A0. ANVEṢHA flags the deviation, names the exact pin mismatch, and confirms PASS the moment it's corrected.", {
    x: 0.6, y: 4.4, w: 11, h: 0.8, fontFace: "IBM Plex Sans", fontSize: 15, color: C.ink2, isTextBox: true, margin: 0,
  });
  pageNum(s, 5);
}

// ---------- Slide 6: Technical Architecture ----------
{
  const s = bgSlide();
  kicker(s, "Technical Architecture");
  s.addText("Clean separation: perception vs. verification", {
    x: 0.6, y: 1.0, w: 11.5, h: 0.7, fontFace: "IBM Plex Sans", fontSize: 26, bold: true, color: C.ink1, isTextBox: true, margin: 0,
  });

  const items = ["Camera", "Whisper-Small", "Qwen3-VL-4B", "Experiment Engine", "Verification Engine", "Arduino Telemetry", "Snapdragon NPU"];
  items.forEach((label, i) => {
    const col = i % 4, row = Math.floor(i / 4);
    const x = 0.6 + col * 3.0, y = 2.15 + row * 1.15, w = 2.7, h = 0.85;
    const isNpu = label.includes("Snapdragon");
    s.addShape("roundRect", { x, y, w, h, rectRadius: 0.08, fill: { color: isNpu ? "1A3B35" : C.panel }, line: { color: isNpu ? C.accent : C.line, width: 1 } });
    s.addText(label, { x, y, w, h, align: "center", valign: "middle", fontFace: "Consolas", fontSize: 12, color: isNpu ? C.accent : C.ink1, isTextBox: true, margin: 0 });
  });
  pageNum(s, 6);
}

// ---------- Slide 7: Why Snapdragon ----------
{
  const s = bgSlide();
  kicker(s, "Why Snapdragon");
  s.addText("Local AI is the product, not a feature flag", {
    x: 0.6, y: 1.0, w: 11.5, h: 0.7, fontFace: "IBM Plex Sans", fontSize: 26, bold: true, color: C.ink1, isTextBox: true, margin: 0,
  });
  const reasons = [
    ["Privacy", "Camera, audio, and experiment data never leave the device."],
    ["Low latency", "A tight capture \u2192 verify \u2192 correct loop needs fast, local inference."],
    ["Offline inference", "Works in labs and classrooms with no reliable network."],
    ["Efficient continuous inference", "NPU acceleration for repeated frame-by-frame checks."],
    ["Combine multiple AI workloads", "Vision + speech running together without cloud round-trips."],
  ];
  reasons.forEach(([title, body], i) => {
    const y = 2.05 + i * 0.92;
    s.addText(title, { x: 0.6, y, w: 3.3, h: 0.8, fontFace: "IBM Plex Sans", fontSize: 15, bold: true, color: C.accent, isTextBox: true, margin: 0 });
    s.addText(body, { x: 4.0, y, w: 8.1, h: 0.8, fontFace: "IBM Plex Sans", fontSize: 13.5, color: C.ink2, isTextBox: true, margin: 0 });
  });
  pageNum(s, 7);
}

// ---------- Slide 8: Qualcomm AI Hub ----------
{
  const s = bgSlide();
  kicker(s, "Qualcomm AI Hub");
  s.addText("Model \u2192 AI Hub \u2192 NPU \u2192 Local Inference", {
    x: 0.6, y: 1.0, w: 11.5, h: 0.7, fontFace: "IBM Plex Sans", fontSize: 26, bold: true, color: C.ink1, isTextBox: true, margin: 0,
  });

  const chain = ["Qwen3-VL-4B /\nWhisper-Small", "Qualcomm AI Hub\n(export + profile)", "Snapdragon-optimized\nruntime (QNN)", "NPU", "Local Inference"];
  chain.forEach((label, i) => {
    const x = 0.6 + i * 2.5, y = 2.6, w = 2.15, h = 1.15;
    s.addShape("roundRect", { x, y, w, h, rectRadius: 0.08, fill: { color: C.panel }, line: { color: C.line, width: 1 } });
    s.addText(label, { x, y, w, h, align: "center", valign: "middle", fontFace: "Consolas", fontSize: 11.5, color: C.ink1, isTextBox: true, margin: 0 });
    if (i < chain.length - 1) {
      s.addText("\u2192", { x: x + w, y, w: 0.35, h, align: "center", valign: "middle", fontSize: 15, color: C.ink3, isTextBox: true, margin: 0 });
    }
  });

  s.addText("This repository implements the full backend abstraction (device detection, runtime selection, honest unavailability) and a verified, sourced deployment guide (docs/qualcomm_deployment.md). NPU execution itself requires physical Snapdragon hardware not available during development \u2014 no APIs or benchmarks are fabricated.", {
    x: 0.6, y: 4.3, w: 11.2, h: 1.4, fontFace: "IBM Plex Sans", fontSize: 13, color: C.ink2, isTextBox: true, margin: 0,
  });
  pageNum(s, 8);
}

// ---------- Slide 9: Performance + Demo ----------
{
  const s = bgSlide();
  kicker(s, "Performance + Demo");
  s.addText("Measured results vs. AI Hub reference metrics", {
    x: 0.6, y: 1.0, w: 11.5, h: 0.7, fontFace: "IBM Plex Sans", fontSize: 26, bold: true, color: C.ink1, isTextBox: true, margin: 0,
  });

  s.addShape("roundRect", { x: 0.6, y: 2.0, w: 5.6, h: 3.9, rectRadius: 0.08, fill: { color: C.panel }, line: { color: C.accentDim, width: 1 } });
  s.addText("MEASURED (this repo)", { x: 0.95, y: 2.25, w: 5, h: 0.4, fontFace: "Consolas", fontSize: 12, color: C.accent, isTextBox: true, margin: 0 });
  s.addText([
    { text: "CPU fallback vision backend\n", options: { bold: true, color: C.ink1 } },
    { text: "Real OpenCV frame-quality gating\n\u2022 Load time\n\u2022 First-inference latency\n\u2022 p50 / p95 vision latency\n\u2022 Verification engine latency\n\u2022 Peak memory\n\nSee benchmarks/results/benchmark_report.md\nfor exact current numbers.", options: { color: C.ink2 } },
  ], { x: 0.95, y: 2.75, w: 5.0, h: 3.0, fontFace: "IBM Plex Sans", fontSize: 12.5, isTextBox: true, margin: 0 });

  s.addShape("roundRect", { x: 6.6, y: 2.0, w: 6.1, h: 3.9, rectRadius: 0.08, fill: { color: C.panel }, line: { color: "5A4A1F", width: 1 } });
  s.addText("AI HUB REFERENCE (not ours)", { x: 6.95, y: 2.25, w: 5.6, h: 0.4, fontFace: "Consolas", fontSize: 12, color: C.warn, isTextBox: true, margin: 0 });
  s.addText("No Snapdragon NPU is available in this development environment. Qualcomm's own on-device profiling (run automatically during model export via qai_hub_models) is the correct source for NPU figures \u2014 kept in a clearly separate report section, never merged with our measurements.", {
    x: 6.95, y: 2.75, w: 5.6, h: 2.9, fontFace: "IBM Plex Sans", fontSize: 12.5, color: C.ink2, isTextBox: true, margin: 0,
  });
  pageNum(s, 9);
}

// ---------- Slide 10: Impact + Future ----------
{
  const s = bgSlide();
  kicker(s, "Impact + Future");
  s.addText("Where this goes next", {
    x: 0.6, y: 1.0, w: 11.5, h: 0.7, fontFace: "IBM Plex Sans", fontSize: 28, bold: true, color: C.ink1, isTextBox: true, margin: 0,
  });

  s.addText("APPLICATIONS", { x: 0.6, y: 2.0, w: 5, h: 0.4, fontFace: "Consolas", fontSize: 12, color: C.accent, isTextBox: true, margin: 0 });
  s.addText(
    ["Engineering education", "University laboratories", "Maker spaces", "Technical training", "Equipment setup verification", "Remote / asynchronous learning"]
      .map((t) => ({ text: t, options: { bullet: true, breakLine: true, color: C.ink1 } })),
    { x: 0.6, y: 2.45, w: 5.6, h: 2.8, fontFace: "IBM Plex Sans", fontSize: 14, isTextBox: true, margin: 0 }
  );

  s.addText("FUTURE WORK", { x: 6.6, y: 2.0, w: 5, h: 0.4, fontFace: "Consolas", fontSize: 12, color: C.accent, isTextBox: true, margin: 0 });
  s.addText(
    ["More experiments", "Better component recognition (Qwen3-VL on-device)", "Automatic report generation", "Additional sensors", "Advanced multimodal reasoning"]
      .map((t) => ({ text: t, options: { bullet: true, breakLine: true, color: C.ink1 } })),
    { x: 6.6, y: 2.45, w: 6.0, h: 2.8, fontFace: "IBM Plex Sans", fontSize: 14, isTextBox: true, margin: 0 }
  );

  s.addText("ANVEṢHA AI  \u2014  Observe. Investigate. Verify.", {
    x: 0.6, y: 6.6, w: 11, h: 0.5, fontFace: "Consolas", fontSize: 13, color: C.ink3, isTextBox: true, margin: 0,
  });
  pageNum(s, 10);
}

pres.writeFile({ fileName: "/home/claude/anvesha-ai/submission/short_pitch.pptx" }).then(() => {
  console.log("wrote short_pitch.pptx");
});
