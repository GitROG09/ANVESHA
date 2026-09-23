import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Experiment } from "../types";

export default function Experiments() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listExperiments().then(setExperiments).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="container" style={{ paddingTop: 48, paddingBottom: 72 }}>
      <div style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: 13, marginBottom: 10 }}>
        SELECT EXPERIMENT
      </div>
      <h1 style={{ fontSize: 30, margin: "0 0 8px", fontWeight: 600 }}>Supported experiments</h1>
      <p style={{ color: "var(--ink-2)", maxWidth: 640, marginBottom: 36 }}>
        ANVEṢHA intentionally supports a small set of well-defined, low-risk experiments rather than pretending to
        understand every engineering setup. Each one has an explicit connection map, expected measurement range,
        and validation rules.
      </p>

      {error && (
        <div className="panel" style={{ padding: 16, borderColor: "var(--state-deviation)", color: "var(--state-deviation)" }}>
          Could not reach backend: {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16 }}>
        {experiments.map((exp) => (
          <Link key={exp.experiment_id} to={`/experiments/${exp.experiment_id}`} style={{ textDecoration: "none" }}>
            <div className="panel" style={{ padding: 22, height: "100%" }}>
              <div style={{ fontSize: 11.5, color: "var(--ink-3)", fontFamily: "var(--font-mono)", marginBottom: 10 }}>
                {exp.difficulty.toUpperCase()}
              </div>
              <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 8, color: "var(--ink-1)" }}>{exp.title}</div>
              <div style={{ fontSize: 13.5, color: "var(--ink-2)", marginBottom: 16 }}>{exp.objective}</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {exp.components.map((c) => (
                  <span
                    key={c}
                    style={{
                      fontSize: 11.5,
                      fontFamily: "var(--font-mono)",
                      padding: "3px 8px",
                      borderRadius: 4,
                      background: "var(--bg-inset)",
                      color: "var(--ink-2)",
                      border: "1px solid var(--line-soft)",
                    }}
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
