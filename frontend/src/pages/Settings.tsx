import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { RuntimeStatus } from "../types";

export default function Settings() {
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.runtime().then(setRuntime).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="container" style={{ paddingTop: 48, paddingBottom: 72, maxWidth: 720 }}>
      <div style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: 13, marginBottom: 10 }}>
        SETTINGS / RUNTIME
      </div>
      <h1 style={{ fontSize: 30, margin: "0 0 24px", fontWeight: 600 }}>Runtime & privacy</h1>

      {error && <div className="panel" style={{ padding: 16, color: "var(--state-deviation)" }}>{error}</div>}

      {runtime && (
        <div className="panel" style={{ padding: 22, marginBottom: 20 }}>
          <Row label="Active backend" value={runtime.active_backend === "qualcomm-npu" ? "Qualcomm NPU" : "CPU Fallback"} />
          <Row label="Vision backend" value={runtime.vision_backend} />
          <Row label="Speech backend" value={runtime.speech_backend} />
          <Row label="Device OS / arch" value={`${runtime.device_os} / ${runtime.device_machine}`} />
          <Row label="Qualcomm hardware detected" value={runtime.qualcomm_hardware_detected ? "Yes" : "No"} />
          <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--line-soft)", fontSize: 13, color: "var(--ink-2)" }}>
            {runtime.notes}
          </div>
        </div>
      )}

      <div className="panel" style={{ padding: 22 }}>
        <div style={{ fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--ink-3)", marginBottom: 12 }}>
          PRIVACY
        </div>
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13.5, color: "var(--ink-1)", lineHeight: 1.8 }}>
          <li>No cloud AI APIs are used for inference — no OpenAI, Gemini, or Claude API calls.</li>
          <li>Camera frames, audio, and experiment data are processed locally and are not uploaded anywhere.</li>
          <li>Network access is not required for AI inference; it is only used for the local frontend ↔ backend connection.</li>
          <li>If Arduino telemetry is used, data travels over a local USB serial connection only.</li>
        </ul>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", fontSize: 14 }}>
      <span style={{ color: "var(--ink-2)" }}>{label}</span>
      <span style={{ fontFamily: "var(--font-mono)" }}>{value}</span>
    </div>
  );
}
