import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="container" style={{ paddingTop: 72, paddingBottom: 72 }}>
      <div style={{ maxWidth: 660 }}>
        <div style={{ fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: 13, marginBottom: 18 }}>
          Observe · Investigate · Verify
        </div>
        <h1 style={{ fontSize: 44, lineHeight: 1.1, margin: "0 0 20px", fontWeight: 600, letterSpacing: "-0.02em" }}>
          AI that verifies what you built, not just what you typed.
        </h1>
        <p style={{ fontSize: 17, color: "var(--ink-2)", margin: "0 0 36px" }}>
          ANVEṢHA AI is on-device multimodal intelligence for physical experiment verification. It watches your
          setup, reads the procedure, checks the measurements, and tells you exactly where reality diverges from
          the manual.
        </p>
        <div style={{ display: "flex", gap: 12, marginBottom: 56 }}>
          <Link to="/experiments" className="btn btn-primary">Start Experiment</Link>
          <Link to="/experiments?demo=1" className="btn">Demo Experiments</Link>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, maxWidth: 900 }}>
        <StatusCard label="AI Runtime" value="Qualcomm Accelerated / Local Development" />
        <StatusCard label="Processing" value="On-device" />
        <StatusCard label="Network" value="Not required for AI inference" />
      </div>

      <div className="panel" style={{ marginTop: 48, padding: 24, maxWidth: 900 }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 12.5, color: "var(--ink-3)", marginBottom: 14 }}>
          HOW IT WORKS
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 14, color: "var(--ink-2)", flexWrap: "wrap" }}>
          <Step>Camera + Procedure + Measurements</Step>
          <Arrow />
          <Step>Evidence Fusion</Step>
          <Arrow />
          <Step>Verification Engine</Step>
          <Arrow />
          <Step accent>PASS / WARNING / DEVIATION</Step>
        </div>
      </div>
    </div>
  );
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel" style={{ padding: 18 }}>
      <div style={{ fontSize: 11.5, color: "var(--ink-3)", fontFamily: "var(--font-mono)", marginBottom: 8 }}>
        {label.toUpperCase()}
      </div>
      <div style={{ fontSize: 14.5 }}>{value}</div>
    </div>
  );
}

function Step({ children, accent }: { children: React.ReactNode; accent?: boolean }) {
  return (
    <span
      style={{
        padding: "6px 12px",
        borderRadius: 6,
        border: "1px solid var(--line)",
        background: accent ? "var(--bg-inset)" : "transparent",
        color: accent ? "var(--accent)" : "var(--ink-2)",
      }}
    >
      {children}
    </span>
  );
}

function Arrow() {
  return <span style={{ color: "var(--ink-3)" }}>→</span>;
}
