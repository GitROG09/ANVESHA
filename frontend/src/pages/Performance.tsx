import { useEffect, useState } from "react";
import { BASE_URL } from "../api/client";

interface BenchmarkReport {
  meta: { timestamp: string; backend: string; model: string; image_resolution: string; number_of_runs: number; host: string };
  load_time_ms: number;
  first_inference_latency_ms: number;
  vision_latency_ms: { mean: number; p50: number; p95: number; min: number; max: number };
  verification_engine_latency_ms: { mean: number; p50: number; p95: number };
  end_to_end_latency_ms: { mean: number; p50: number; p95: number };
  memory_usage_kb: { current: number; peak: number };
  qualcomm_ai_hub_reference_metrics: { measurement_type: string; note: string; value: null };
}

export default function Performance() {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${BASE_URL.replace(/\/$/, "")}/api/benchmarks`)
      .catch(() => null)
      .then(async (r) => {
        if (!r || !r.ok) {
          setError("No benchmark report found yet. Run `python benchmarks/benchmark.py` from the repo root to generate one.");
          return;
        }
        setReport(await r.json());
      });
  }, []);

  return (
    <div className="container" style={{ paddingTop: 48, paddingBottom: 72 }}>
      <div style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: 13, marginBottom: 10 }}>
        PERFORMANCE
      </div>
      <h1 style={{ fontSize: 30, margin: "0 0 8px", fontWeight: 600 }}>Benchmarks</h1>
      <p style={{ color: "var(--ink-2)", maxWidth: 640, marginBottom: 32 }}>
        Local measurements are taken on whatever machine is currently running the backend. Qualcomm AI Hub reference
        figures are kept in a clearly separate section and are never merged with our own numbers.
      </p>

      {error && (
        <div className="panel" style={{ padding: 16, fontSize: 13.5, color: "var(--ink-2)" }}>{error}</div>
      )}

      {report && (
        <>
          <div className="panel" style={{ padding: 20, marginBottom: 20 }}>
            <div style={{ fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--accent)", marginBottom: 12 }}>
              LOCAL MEASUREMENT
            </div>
            <div style={{ fontSize: 13, color: "var(--ink-2)", marginBottom: 16 }}>
              {report.meta.host} · backend <code>{report.meta.backend}</code> · {report.meta.image_resolution} ·
              {" "}{report.meta.number_of_runs} runs
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              <Metric label="Load time" value={`${report.load_time_ms} ms`} />
              <Metric label="First inference" value={`${report.first_inference_latency_ms} ms`} />
              <Metric label="Vision p50 / p95" value={`${report.vision_latency_ms.p50} / ${report.vision_latency_ms.p95} ms`} />
              <Metric label="End-to-end p50 / p95" value={`${report.end_to_end_latency_ms.p50} / ${report.end_to_end_latency_ms.p95} ms`} />
              <Metric label="Verification engine mean" value={`${report.verification_engine_latency_ms.mean} ms`} />
              <Metric label="Peak memory" value={`${report.memory_usage_kb.peak} KB`} />
            </div>
          </div>

          <div className="panel" style={{ padding: 20, borderColor: "rgba(251,191,36,.25)" }}>
            <div style={{ fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--state-warn)", marginBottom: 12 }}>
              QUALCOMM AI HUB REFERENCE METRICS — NOT MEASURED HERE
            </div>
            <p style={{ fontSize: 13, color: "var(--ink-2)", margin: 0 }}>{report.qualcomm_ai_hub_reference_metrics.note}</p>
          </div>
        </>
      )}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: "var(--ink-3)", fontFamily: "var(--font-mono)", marginBottom: 4 }}>
        {label.toUpperCase()}
      </div>
      <div style={{ fontSize: 16, fontFamily: "var(--font-mono)" }}>{value}</div>
    </div>
  );
}
