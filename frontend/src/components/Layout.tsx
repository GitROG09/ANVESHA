import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { api } from "../api/client";
import type { RuntimeStatus } from "../types";

const NAV = [
  { to: "/", label: "Home" },
  { to: "/experiments", label: "Experiments" },
  { to: "/performance", label: "Performance" },
  { to: "/settings", label: "Settings" },
];

export default function Layout() {
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();

  useEffect(() => {
    api
      .runtime()
      .then(setRuntime)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          borderBottom: "1px solid var(--line)",
          background: "var(--bg-panel)",
        }}
      >
        <div className="container" style={{ display: "flex", alignItems: "center", height: 60, gap: 32 }}>
          <Link to="/" style={{ textDecoration: "none", display: "flex", alignItems: "baseline", gap: 8 }}>
            <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 17, letterSpacing: "-0.01em" }}>
              ANVEṢHA<span style={{ color: "var(--accent)" }}>AI</span>
            </span>
          </Link>
          <nav style={{ display: "flex", gap: 4, flex: 1 }}>
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                style={{
                  textDecoration: "none",
                  padding: "8px 12px",
                  borderRadius: 6,
                  fontSize: 14,
                  color: location.pathname === item.to ? "var(--ink-1)" : "var(--ink-2)",
                  background: location.pathname === item.to ? "var(--bg-panel-raised)" : "transparent",
                }}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, fontFamily: "var(--font-mono)" }}>
            {error ? (
              <span style={{ color: "var(--state-deviation)" }}>backend unreachable</span>
            ) : runtime ? (
              <>
                <span className={`dot ${runtime.active_backend === "qualcomm-npu" ? "on" : "off"}`} />
                <span style={{ color: "var(--ink-2)" }}>
                  {runtime.active_backend === "qualcomm-npu" ? "Qualcomm NPU" : "CPU Fallback"} · {runtime.device_os}
                </span>
              </>
            ) : (
              <span style={{ color: "var(--ink-3)" }}>checking runtime…</span>
            )}
          </div>
        </div>
      </header>
      <main style={{ flex: 1 }}>
        <Outlet context={{ runtime } satisfies { runtime: RuntimeStatus | null }} />
      </main>
      <footer style={{ borderTop: "1px solid var(--line-soft)", padding: "18px 0", marginTop: 40 }}>
        <div className="container" style={{ fontSize: 12.5, color: "var(--ink-3)" }}>
          AI-generated guidance is educational. Verify procedures against the official experiment manual and follow
          appropriate lab safety procedures.
        </div>
      </footer>
    </div>
  );
}
