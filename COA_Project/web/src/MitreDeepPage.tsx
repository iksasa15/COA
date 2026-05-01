import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import FeatureNav from "./FeatureNav";

type Phase = {
  tactic?: string;
  ta_id?: string;
  techniques?: Array<{
    technique?: string;
    name?: string;
    confidence?: string;
    sources?: string[];
  }>;
};

type MitreDeep = {
  ascii_report?: string;
  kill_chain_phases?: Phase[];
  navigator_layer?: Record<string, unknown>;
  ics_context?: { ics_relevant?: boolean; note?: string };
  detection_gap_hints?: string[];
};

function loadDeep(): MitreDeep | null {
  try {
    const extrasRaw = sessionStorage.getItem("coa_last_scan_extras");
    if (!extrasRaw) return null;
    const x = JSON.parse(extrasRaw) as { mitre_deep?: MitreDeep };
    return x.mitre_deep ?? null;
  } catch {
    return null;
  }
}

export default function MitreDeepPage() {
  const [deep, setDeep] = useState<MitreDeep | null>(null);

  useEffect(() => {
    setDeep(loadDeep());
  }, []);

  function downloadNavigatorLayer() {
    const layer = deep?.navigator_layer;
    if (!layer) return;
    const blob = new Blob([JSON.stringify(layer, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "coa_mitre_navigator_layer.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          padding: "1rem 1.5rem",
          borderBottom: "1px solid var(--bg3)",
          background: "var(--bg2)",
        }}
      >
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "baseline", gap: "0.75rem" }}>
          <h1 style={{ margin: 0, fontSize: "1.35rem", color: "var(--cyan)" }}>MITRE — تحليل عميق</h1>
          <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Kill chain · D3FEND hints · ICS · Navigator</span>
        </div>
        <FeatureNav />
      </header>

      <main style={{ flex: 1, padding: "1rem 1.5rem", maxWidth: "960px", margin: "0 auto", width: "100%" }}>
        {!deep && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            لا توجد بيانات. نفّذ{" "}
            <Link to="/dashboard" style={{ color: "var(--cyan)" }}>
              فحصاً
            </Link>{" "}
            ثم ارجع هنا. (يُحفظ في <code>sessionStorage</code> مفتاح <code>coa_last_scan_extras</code>.)
          </p>
        )}

        {deep && (
          <>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
              <button type="button" className="btn-accent" disabled={!deep.navigator_layer} onClick={downloadNavigatorLayer}>
                تصدير Navigator JSON (من الجلسة)
              </button>
              <span style={{ fontSize: "0.8rem", color: "var(--muted)", alignSelf: "center" }}>
                نفس الملف يمكن جلبه من الـ API: <code>/api/reports/mitre-navigator.json</code> بعد فحص من الخادم.
              </span>
            </div>

            {deep.ics_context && (
              <section
                style={{
                  marginBottom: "1rem",
                  padding: "0.75rem 1rem",
                  background: deep.ics_context.ics_relevant ? "#422006" : "var(--bg2)",
                  borderRadius: "var(--radius)",
                  border: `1px solid ${deep.ics_context.ics_relevant ? "#b45309" : "var(--bg3)"}`,
                  color: deep.ics_context.ics_relevant ? "#ffedd5" : "var(--muted)",
                  fontSize: "0.88rem",
                }}
              >
                <strong>{deep.ics_context.ics_relevant ? "ICS / OT — ذو صلة" : "ICS / OT"}:</strong> {deep.ics_context.note}
              </section>
            )}

            <section style={{ marginBottom: "1.25rem" }}>
              <h2 style={{ fontSize: "1rem", color: "var(--fg)", margin: "0 0 0.5rem" }}>فجوات كشف (تلميحات)</h2>
              <ul style={{ color: "var(--muted)", fontSize: "0.88rem" }}>
                {(deep.detection_gap_hints || []).length === 0 && <li>لا تلميحات في هذا الفحص.</li>}
                {(deep.detection_gap_hints || []).map((g, i) => (
                  <li key={i} style={{ marginBottom: "0.35rem" }}>
                    {g}
                  </li>
                ))}
              </ul>
            </section>

            <section style={{ marginBottom: "1.25rem" }}>
              <h2 style={{ fontSize: "1rem", color: "var(--fg)", margin: "0 0 0.5rem" }}>سلسلة القتل (مراحل مرتّبة)</h2>
              {(deep.kill_chain_phases || []).map((ph, i) => (
                <div
                  key={i}
                  style={{
                    marginBottom: "0.75rem",
                    padding: "0.65rem 0.85rem",
                    background: "var(--bg2)",
                    borderRadius: "var(--radius)",
                    border: "1px solid var(--bg3)",
                  }}
                >
                  <div style={{ fontWeight: 700, color: "var(--cyan)", fontSize: "0.9rem" }}>
                    {ph.ta_id} — {ph.tactic}
                  </div>
                  <ul style={{ margin: "0.35rem 0 0", paddingLeft: "1.1rem", color: "var(--muted)", fontSize: "0.82rem" }}>
                    {(ph.techniques || []).map((t, j) => (
                      <li key={j} style={{ marginBottom: "0.25rem" }}>
                        <strong style={{ color: "var(--fg)" }}>{t.technique}</strong> — {t.name}{" "}
                        <span style={{ opacity: 0.85 }}>
                          ({t.confidence}) {t.sources?.length ? `— ${t.sources.join(", ")}` : ""}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              {!deep.kill_chain_phases?.length && (
                <p style={{ color: "var(--muted)", fontSize: "0.88rem" }}>لا مراحل مرتبطة بهذا الفحص.</p>
              )}
            </section>

            <section>
              <h2 style={{ fontSize: "1rem", color: "var(--fg)", margin: "0 0 0.5rem" }}>تقرير ASCII كامل</h2>
              <pre
                style={{
                  margin: 0,
                  padding: "0.85rem 1rem",
                  background: "var(--bg2)",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--bg3)",
                  color: "var(--muted)",
                  fontSize: "0.78rem",
                  whiteSpace: "pre-wrap",
                  maxHeight: "min(70vh, 520px)",
                  overflow: "auto",
                }}
              >
                {deep.ascii_report || "(لا يوجد نص)"}
              </pre>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
