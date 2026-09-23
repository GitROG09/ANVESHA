import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Experiment } from "../types";

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();
  const [exp, setExp] = useState<Experiment | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getExperiment(id).then(setExp).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="container" style={{ paddingTop: 48 }}>Error: {error}</div>;
  if (!exp) return <div className="container" style={{ paddingTop: 48, color: "var(--ink-3)" }}>Loading…</div>;

  return (
    <div className="container" style={{ paddingTop: 48, paddingBottom: 72 }}>
      <div style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: 13, marginBottom: 10 }}>
        PROCEDURE
      </div>
      <h1 style={{ fontSize: 30, margin: "0 0 8px", fontWeight: 600 }}>{exp.title}</h1>
      <p style={{ color: "var(--ink-2)", maxWidth: 640, marginBottom: 28 }}>{exp.objective}</p>

      {exp.safety_notes.length > 0 && (
        <div
          className="panel"
          style={{ padding: 16, marginBottom: 28, borderColor: "rgba(251,191,36,.3)", background: "var(--state-warn-bg)" }}
        >
          <div style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--state-warn)", marginBottom: 8 }}>
            SAFETY NOTES
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, color: "var(--ink-1)", fontSize: 13.5 }}>
            {exp.safety_notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 32 }}>
        <div>
          <SectionLabel>Required components</SectionLabel>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
            {exp.components.map((c) => (
              <li key={c} style={{ marginBottom: 4 }}>{c}</li>
            ))}
          </ul>
        </div>
        <div>
          <SectionLabel>Expected connections</SectionLabel>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 13 }}>
            {exp.connections.map((c, i) => (
              <div key={i} style={{ marginBottom: 6, color: "var(--ink-2)" }}>
                <span style={{ color: "var(--ink-1)" }}>{c.from} {c.from_pin}</span> → <span style={{ color: "var(--ink-1)" }}>{c.to} {c.to_pin}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 32 }}>
        <SectionLabel>Steps</SectionLabel>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {exp.steps.map((s, i) => (
            <div key={s.step_id} className="panel" style={{ padding: 14, display: "flex", gap: 14 }}>
              <div style={{ fontFamily: "var(--font-mono)", color: "var(--ink-3)", fontSize: 13, minWidth: 22 }}>
                {i + 1}
              </div>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 3 }}>{s.title}</div>
                <div style={{ fontSize: 13.5, color: "var(--ink-2)" }}>{s.instruction}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 40 }}>
        <SectionLabel>Expected measurements</SectionLabel>
        {exp.expected_measurements.map((m) => (
          <div key={m.sensor} className="mono" style={{ fontSize: 13.5, color: "var(--ink-2)" }}>
            {m.sensor}: {m.min_value}–{m.max_value} {m.unit} — {m.description}
          </div>
        ))}
      </div>

      <Link to={`/verify/${exp.experiment_id}`} className="btn btn-primary">
        Start Live Verification
      </Link>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--ink-3)", marginBottom: 10 }}>
      {String(children).toUpperCase()}
    </div>
  );
}
