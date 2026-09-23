import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { DemoScenario, Experiment, VerificationResult, VisualObservation } from "../types";
import { VerificationPanel } from "../components/VerificationPanel";

type Mode = "camera" | "upload" | "demo";

export default function LiveVerification() {
  const { id } = useParams<{ id: string }>();
  const [exp, setExp] = useState<Experiment | null>(null);
  const [mode, setMode] = useState<Mode>("demo");
  const [demoScenarios, setDemoScenarios] = useState<DemoScenario[]>([]);
  const [selectedDemo, setSelectedDemo] = useState<string>("demo_2_wrong_connection");
  const [observation, setObservation] = useState<VisualObservation | null>(null);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [history, setHistory] = useState<VerificationResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!id) return;
    api.getExperiment(id).then(setExp).catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    api.listDemoScenarios().then(setDemoScenarios).catch(() => {});
  }, []);

  useEffect(() => {
    return () => {
      videoStream?.getTracks().forEach((t) => t.stop());
    };
  }, [videoStream]);

  async function startCamera() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      setVideoStream(stream);
      setMode("camera");
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch (e: any) {
      setError(`Could not access camera: ${e.message}. This is common in a sandboxed/headless environment — try Upload Frame instead.`);
    }
  }

  async function captureAndAnalyze() {
    if (!exp || !videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx?.drawImage(video, 0, 0);
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      await analyzeBlob(blob);
    }, "image/jpeg", 0.9);
  }

  async function analyzeBlob(blob: Blob) {
    if (!exp) return;
    setBusy(true);
    setError(null);
    try {
      const obs = await api.analyzeFrame(exp.experiment_id, blob);
      setObservation(obs);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  function onFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setMode("upload");
      analyzeBlob(file);
    }
  }

  async function runVerify() {
    if (!exp) return;
    setBusy(true);
    setError(null);
    try {
      if (mode === "demo") {
        // The only path allowed to use scripted/simulated evidence — it is
        // explicitly labeled as such in the UI (see the SIMULATED notice
        // below) and never runs silently.
        const r = await api.runDemoScenario(selectedDemo);
        setResult(r);
        setHistory((h) => [...h, r]);
      } else {
        // Real camera/upload verification: only the actual analyzed frame
        // is sent. No telemetry is fabricated here — with no real sensor
        // connected, sensor_readings is empty and the verification engine
        // will honestly report missing measurement evidence rather than a
        // manufactured PASS.
        const r = await api.verify(exp.experiment_id, observation, []);
        setResult(r);
        setHistory((h) => [...h, r]);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!exp) return <div className="container" style={{ paddingTop: 48, color: "var(--ink-3)" }}>Loading…</div>;

  const currentStepIndex = Math.min(history.length, exp.steps.length - 1);

  return (
    <div className="container" style={{ paddingTop: 40, paddingBottom: 72 }}>
      <div style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: 13, marginBottom: 8 }}>
        LIVE VERIFICATION · {exp.title.toUpperCase()}
      </div>
      <div style={{ display: "flex", gap: 8, marginBottom: 28 }}>
        <ModeButton active={mode === "camera"} onClick={startCamera}>Camera</ModeButton>
        <ModeButton active={mode === "upload"} onClick={() => fileInputRef.current?.click()}>Upload Frame</ModeButton>
        <ModeButton active={mode === "demo"} onClick={() => setMode("demo")}>Demo Scenario</ModeButton>
        <input ref={fileInputRef} type="file" accept="image/*" style={{ display: "none" }} onChange={onFileChosen} />
      </div>

      {error && (
        <div className="panel" style={{ padding: 14, marginBottom: 20, borderColor: "var(--state-deviation)", color: "var(--state-deviation)", fontSize: 13.5 }}>
          {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.1fr", gap: 20 }}>
        {/* LEFT: capture surface */}
        <div>
          <div className="panel" style={{ padding: 16, marginBottom: 16 }}>
            {mode === "camera" && (
              <>
                <video ref={videoRef} autoPlay playsInline style={{ width: "100%", borderRadius: 6, background: "#000" }} />
                <canvas ref={canvasRef} style={{ display: "none" }} />
                <button className="btn btn-primary" style={{ marginTop: 12, width: "100%", justifyContent: "center" }} onClick={captureAndAnalyze} disabled={busy}>
                  Capture Frame
                </button>
              </>
            )}
            {mode === "upload" && (
              <div style={{ padding: 40, textAlign: "center", color: "var(--ink-3)", fontSize: 13.5 }}>
                {observation ? "Frame analyzed — see evidence panel." : "Choose an image file with Upload Frame."}
              </div>
            )}
            {mode === "demo" && (
              <div>
                <div style={{ fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--ink-3)", marginBottom: 10 }}>
                  SCRIPTED DEMO SCENARIO
                </div>
                <select
                  value={selectedDemo}
                  onChange={(e) => setSelectedDemo(e.target.value)}
                  style={{
                    width: "100%", padding: 10, background: "var(--bg-inset)", color: "var(--ink-1)",
                    border: "1px solid var(--line)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 13,
                  }}
                >
                  {demoScenarios.map((s) => (
                    <option key={s.id} value={s.id}>{s.id}</option>
                  ))}
                </select>
                <p style={{ fontSize: 12.5, color: "var(--state-warn)", marginTop: 10 }}>
                  SIMULATED — this scenario uses scripted evidence, not a live camera, for reproducible presentation.
                </p>
              </div>
            )}
          </div>

          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} onClick={runVerify} disabled={busy}>
            {busy ? "Verifying…" : history.length === 0 ? "Verify" : "Verify Again"}
          </button>

          {exp.steps.length > 0 && (
            <div style={{ marginTop: 20, fontSize: 12.5, color: "var(--ink-3)", fontFamily: "var(--font-mono)" }}>
              STEP {currentStepIndex + 1} / {exp.steps.length} — {exp.steps[currentStepIndex]?.title}
            </div>
          )}
        </div>

        {/* RIGHT: verification result */}
        <div>
          {result ? (
            <VerificationPanel result={result} />
          ) : (
            <div className="panel" style={{ padding: 40, textAlign: "center", color: "var(--ink-3)", fontSize: 13.5 }}>
              No verification run yet. Capture a frame or select a demo scenario, then press Verify.
            </div>
          )}

          {history.length > 1 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--ink-3)", marginBottom: 8 }}>
                HISTORY (BEFORE → AFTER)
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                {history.map((h, i) => (
                  <span key={i} className={`state-tag ${h.experiment_state}`}>{h.experiment_state}</span>
                )).reduce((acc, el, i) => (i === 0 ? [el] : [...acc, <span key={`arrow-${i}`} style={{ color: "var(--ink-3)" }}>→</span>, el]), [] as React.ReactNode[])}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ModeButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      className="btn"
      style={{
        background: active ? "var(--bg-panel-raised)" : "transparent",
        borderColor: active ? "var(--accent-dim)" : "var(--line)",
        color: active ? "var(--ink-1)" : "var(--ink-2)",
      }}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
