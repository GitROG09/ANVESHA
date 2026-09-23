import type { StepResult, VerificationResult } from "../types";

export function StateTag({ state }: { state: string }) {
  return <span className={`state-tag ${state}`}>{state.replace("_", " ")}</span>;
}

export function StepRow({ step }: { step: StepResult }) {
  const color =
    step.status === "verified" ? "var(--state-pass)" : step.status === "failed" ? "var(--state-deviation)" : "var(--state-warn)";
  const symbol = step.status === "verified" ? "✓" : step.status === "failed" ? "✗" : "!";
  return (
    <div style={{ padding: "12px 0", borderBottom: "1px solid var(--line-soft)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: step.why_it_matters ? 8 : 0 }}>
        <span style={{ color, fontFamily: "var(--font-mono)", fontWeight: 700, width: 14 }}>{symbol}</span>
        <span style={{ fontSize: 13.5, fontWeight: 500 }}>{step.title}</span>
      </div>
      {(step.expected || step.observed) && (
        <div style={{ marginLeft: 24, fontFamily: "var(--font-mono)", fontSize: 12.5, color: "var(--ink-2)" }}>
          {step.expected && <div>Expected: <span style={{ color: "var(--ink-1)" }}>{step.expected}</span></div>}
          {step.observed && <div>Observed: <span style={{ color: "var(--ink-1)" }}>{step.observed}</span></div>}
        </div>
      )}
      {step.why_it_matters && (
        <div style={{ marginLeft: 24, marginTop: 6, fontSize: 12.5, color: "var(--ink-2)" }}>{step.why_it_matters}</div>
      )}
      {step.recommended_action && (
        <div style={{ marginLeft: 24, marginTop: 4, fontSize: 12.5, color: "var(--accent)" }}>
          → {step.recommended_action}
        </div>
      )}
    </div>
  );
}

export function VerificationPanel({ result }: { result: VerificationResult }) {
  return (
    <div className="panel" style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <StateTag state={result.experiment_state} />
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12.5, color: "var(--ink-3)" }}>
          confidence {Math.round(result.confidence * 100)}%
        </span>
      </div>

      {result.observations.length > 0 && (
        <div style={{ fontSize: 13, color: "var(--ink-2)", marginBottom: 16 }}>
          {result.observations.map((o, i) => (
            <p key={i} style={{ margin: "0 0 6px" }}>{o}</p>
          ))}
        </div>
      )}

      {result.failed_steps.length > 0 && (
        <Section title="Deviations">
          {result.failed_steps.map((s) => <StepRow key={s.step_id} step={s} />)}
        </Section>
      )}
      {result.warnings.length > 0 && (
        <Section title="Warnings">
          {result.warnings.map((s) => <StepRow key={s.step_id} step={s} />)}
        </Section>
      )}
      {result.verified_steps.length > 0 && (
        <Section title="Verified">
          {result.verified_steps.map((s) => <StepRow key={s.step_id} step={s} />)}
        </Section>
      )}

      {result.evidence.length > 0 && (
        <Section title="Evidence">
          {result.evidence.map((item, index) => (
            <div key={`${item.source}-${index}`} style={{ padding: "7px 0", borderBottom: "1px solid var(--line-soft)", fontSize: 12.5, color: "var(--ink-2)" }}>
              <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{item.source}</span> {item.summary}
            </div>
          ))}
        </Section>
      )}

      {result.recommended_actions.length > 0 && (
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--line-soft)" }}>
          <div style={{ fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--ink-3)", marginBottom: 8 }}>
            NEXT ACTIONS
          </div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "var(--ink-1)" }}>
            {result.recommended_actions.map((a, i) => <li key={i} style={{ marginBottom: 4 }}>{a}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ fontSize: 11.5, fontFamily: "var(--font-mono)", color: "var(--ink-3)", marginBottom: 2 }}>
        {title.toUpperCase()}
      </div>
      {children}
    </div>
  );
}
