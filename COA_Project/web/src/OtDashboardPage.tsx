import { useMemo, type CSSProperties } from "react";
import { Link } from "react-router-dom";
import FeatureNav from "./FeatureNav";

type OtIcsHit = {
  process?: string;
  local?: string;
  remote?: string;
  port?: number;
  protocol?: string;
  ics_mitre_examples?: string[];
  risk_note?: string;
};

type OtIcsPayload = {
  mode?: string;
  passive_by_default?: boolean;
  disclaimer?: string;
  ics_protocol_hits?: OtIcsHit[];
  inventory_sketch?: Array<{
    endpoint?: string;
    processes?: string[];
    protocols_observed?: string[];
    note?: string;
  }>;
  distinct_ics_protocols?: number;
  ics_ports_observed?: number[];
  ot_playbooks_triggered?: Array<{ id?: string; name_ar?: string; name_en?: string; reason?: string }>;
  production_continuity_score?: number;
  ics_mitre_matrix_url?: string;
  ics_specialist?: {
    ascii_report?: string;
    cyber_impact?: string;
    operational_impact?: string;
    safety_impact?: string;
    do_list?: string[];
    dont_list?: string[];
    mitre_ics_examples?: string[];
  };
};

function loadOtFromSession(): OtIcsPayload | null {
  try {
    const raw = sessionStorage.getItem("coa_last_scan_extras");
    if (!raw) return null;
    const j = JSON.parse(raw) as { ot_ics?: OtIcsPayload };
    return j.ot_ics ?? null;
  } catch {
    return null;
  }
}

export default function OtDashboardPage() {
  const ot = useMemo(() => loadOtFromSession(), []);

  const mitreCounts = useMemo(() => {
    const m = new Map<string, number>();
    for (const h of ot?.ics_protocol_hits || []) {
      for (const id of h.ics_mitre_examples || []) {
        m.set(id, (m.get(id) || 0) + 1);
      }
    }
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  }, [ot]);

  const pcs = ot?.production_continuity_score ?? null;
  const sp = ot?.ics_specialist;

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column", background: "var(--bg)" }}>
      <header
        style={{
          padding: "1rem 1.5rem",
          borderBottom: "1px solid #334155",
          display: "flex",
          flexDirection: "column",
          alignItems: "stretch",
          background: "#0c1929",
        }}
      >
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "0.75rem", marginBottom: "0.25rem" }}>
          <h1 style={{ margin: 0, fontSize: "1.35rem", color: "#94a3b8" }}>OT / ICS</h1>
          <span style={{ color: "#64748b", fontSize: "0.9rem" }}>Passive-by-default · مراقبة فقط</span>
        </div>
        <FeatureNav />
      </header>

      <main style={{ flex: 1, padding: "1.25rem 1.5rem", maxWidth: "1100px", margin: "0 auto", width: "100%" }}>
        {!ot && (
          <p style={{ color: "#94a3b8", lineHeight: 1.6 }}>
            لا توجد بيانات OT بعد. شغّل فحصاً من{" "}
            <Link to="/dashboard" style={{ color: "#38bdf8" }}>
              لوحة الأداء
            </Link>{" "}
            ثم ارجع هنا.
          </p>
        )}

        {ot && (
          <>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: "0.65rem",
                marginBottom: "1.25rem",
              }}
            >
              <div style={kpiBox}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#e2e8f0" }}>
                  {ot.distinct_ics_protocols ?? 0}
                </div>
                <div style={kpiLabel}>بروتوكولات ICS مميّزة (من الجدول)</div>
              </div>
              <div style={kpiBox}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#e2e8f0" }}>
                  {(ot.ics_protocol_hits || []).length}
                </div>
                <div style={kpiLabel}>ملاحظات اتصال على منافذ صناعية</div>
              </div>
              <div style={{ ...kpiBox, borderColor: pcs != null && pcs < 70 ? "#b91c1c40" : "#334155" }}>
                <div
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 700,
                    color: pcs != null && pcs < 70 ? "#f87171" : "#e2e8f0",
                  }}
                >
                  {pcs ?? "—"}
                </div>
                <div style={kpiLabel}>Production continuity (تجريبي)</div>
              </div>
            </div>

            <p style={{ fontSize: "0.82rem", color: "#64748b", margin: "0 0 1rem", lineHeight: 1.5 }}>
              {ot.disclaimer}
            </p>

            {sp && (
              <section style={section}>
                <h2 style={h2}>ICS Specialist (Agent #6)</h2>
                <pre
                  style={{
                    margin: 0,
                    padding: "0.85rem 1rem",
                    background: "#0f172a",
                    borderRadius: "8px",
                    border: "1px solid #1e293b",
                    color: "#cbd5e1",
                    fontSize: "0.78rem",
                    overflow: "auto",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {sp.ascii_report}
                </pre>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginTop: "0.65rem" }}>
                  {["cyber_impact", "operational_impact", "safety_impact"].map((k) => (
                    <span key={k} style={pill}>
                      {k.replace("_", " ")}: {String((sp as Record<string, string>)[k] ?? "—")}
                    </span>
                  ))}
                </div>
              </section>
            )}

            {(ot.ot_playbooks_triggered || []).length > 0 && (
              <section style={section}>
                <h2 style={h2}>سيناريوهات OT (تنبيه تجريبي)</h2>
                <ul style={{ margin: 0, paddingLeft: "1.1rem", color: "#94a3b8", fontSize: "0.88rem" }}>
                  {ot.ot_playbooks_triggered!.map((p) => (
                    <li key={String(p.id)} style={{ marginBottom: "0.35rem" }}>
                      <strong style={{ color: "#e2e8f0" }}>{p.name_ar || p.id}</strong>
                      {p.reason ? ` — ${p.reason}` : ""}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section style={section}>
              <h2 style={h2}>MITRE ATT&CK for ICS (أمثلة من المرجع)</h2>
              <p style={{ fontSize: "0.8rem", color: "#64748b", margin: "0 0 0.75rem" }}>
                <a href={ot.ics_mitre_matrix_url || "https://attack.mitre.org/matrices/ics/"} style={{ color: "#38bdf8" }}>
                  المصفوفة الرسمية
                </a>
                {" · "}تظليل حسب تكرار الربط في هذه الجلسة:
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {mitreCounts.length === 0 && (
                  <span style={{ color: "#64748b", fontSize: "0.85rem" }}>لا توجد تقنيات مرتبطة في هذه الجلسة.</span>
                )}
                {mitreCounts.map(([id, n]) => (
                  <span
                    key={id}
                    title={`observed ${n}x (passive port hint)`}
                    style={{
                      padding: "0.25rem 0.5rem",
                      borderRadius: "4px",
                      fontSize: "0.75rem",
                      fontFamily: "ui-monospace, monospace",
                      background: heatBg(n),
                      color: "#f1f5f9",
                      border: "1px solid #334155",
                    }}
                  >
                    {id} ({n})
                  </span>
                ))}
              </div>
            </section>

            <section style={section}>
              <h2 style={h2}>خريطة أصول تقريبية (من جدول الاتصالات)</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {(ot.inventory_sketch || []).map((inv) => (
                  <div
                    key={String(inv.endpoint)}
                    style={{
                      padding: "0.65rem 0.85rem",
                      background: "#0f172a",
                      border: "1px solid #1e293b",
                      borderRadius: "8px",
                      fontSize: "0.82rem",
                      color: "#94a3b8",
                    }}
                  >
                    <div style={{ color: "#e2e8f0", fontWeight: 600, marginBottom: "0.25rem" }}>{inv.endpoint}</div>
                    <div>Protocols: {(inv.protocols_observed || []).join(", ") || "—"}</div>
                    <div>Processes: {(inv.processes || []).join(", ") || "—"}</div>
                    {inv.note && <div style={{ marginTop: "0.35rem", fontSize: "0.78rem" }}>{inv.note}</div>}
                  </div>
                ))}
              </div>
            </section>

            <section style={section}>
              <h2 style={h2}>تنبيهات بروتوكول (اتصالات ذات منفذ ICS)</h2>
              <div className="table-wrap" style={{ borderColor: "#1e293b" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Process</th>
                      <th>Local</th>
                      <th>Remote</th>
                      <th>Port</th>
                      <th>Protocol</th>
                      <th>MITRE ICS (مثال)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(ot.ics_protocol_hits || []).map((h, i) => (
                      <tr key={i}>
                        <td>{h.process}</td>
                        <td style={{ wordBreak: "break-all" }}>{String(h.local)}</td>
                        <td style={{ wordBreak: "break-all" }}>{String(h.remote)}</td>
                        <td>{h.port}</td>
                        <td>{h.protocol}</td>
                        <td style={{ fontSize: "0.75rem" }}>{(h.ics_mitre_examples || []).join(", ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

const kpiBox: CSSProperties = {
  background: "#0f172a",
  borderRadius: "8px",
  padding: "0.75rem",
  border: "1px solid #1e293b",
  textAlign: "center",
};

const kpiLabel: CSSProperties = { fontSize: "0.72rem", color: "#64748b", marginTop: "0.25rem" };

const section: CSSProperties = { marginBottom: "1.35rem" };

const h2: CSSProperties = {
  fontSize: "1rem",
  color: "#94a3b8",
  margin: "0 0 0.5rem",
  fontWeight: 600,
};

const pill: CSSProperties = {
  fontSize: "0.75rem",
  padding: "0.2rem 0.5rem",
  borderRadius: "999px",
  background: "#1e293b",
  color: "#cbd5e1",
  border: "1px solid #334155",
};

function heatBg(n: number): string {
  if (n >= 3) return "#7f1d1d";
  if (n === 2) return "#991b1b90";
  return "#1e3a5f";
}
