import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { Link, useLocation } from "react-router-dom";
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
  presentation_demo?: boolean;
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

function mirrorOtToSessionStorage(next: OtIcsPayload) {
  try {
    let extras: Record<string, unknown> = {};
    const raw = sessionStorage.getItem("coa_last_scan_extras");
    if (raw) {
      try {
        extras = JSON.parse(raw) as Record<string, unknown>;
      } catch {
        extras = {};
      }
    }
    extras.ot_ics = next;
    sessionStorage.setItem("coa_last_scan_extras", JSON.stringify(extras));
  } catch {
    /* quota */
  }
}

export default function OtDashboardPage() {
  const [ot, setOt] = useState<OtIcsPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchErr, setFetchErr] = useState<string | null>(null);
  const location = useLocation();

  const refresh = useCallback(async () => {
    setFetchErr(null);
    const local = loadOtFromSession();
    if (local) {
      setLoading(false);
      setOt(local);
      return;
    }
    setLoading(true);
    setOt(null);
    try {
      const res = await fetch("/api/last/ot-ics");
      const json = (await res.json()) as { ok?: boolean; ot_ics?: OtIcsPayload; error?: string };
      if (res.ok && json.ok && json.ot_ics) {
        mirrorOtToSessionStorage(json.ot_ics);
        setOt(json.ot_ics);
      } else {
        setOt(null);
        if (res.status >= 500) {
          setFetchErr(json.error || "خطأ في الخادم.");
        }
      }
    } catch {
      setOt(null);
      setFetchErr("تعذّر الاتصال بالخادم. تأكد أن API يعمل (python web_api.py على المنفذ 5050).");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [location.key, refresh]);

  useEffect(() => {
    const onScan = () => {
      void refresh();
    };
    const onStorage = (e: StorageEvent) => {
      if (e.key === "coa_last_scan_extras") void refresh();
    };
    window.addEventListener("coa-scan-complete", onScan);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("coa-scan-complete", onScan);
      window.removeEventListener("storage", onStorage);
    };
  }, [refresh]);

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
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__row">
          <h1 className="page-title">OT / ICS</h1>
          <span className="page-subtitle">Passive-by-default · مراقبة فقط</span>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main">
        {fetchErr && (
          <p style={{ color: "var(--red)", fontSize: "0.88rem", marginBottom: "0.75rem" }}>{fetchErr}</p>
        )}
        {loading && !ot && !fetchErr && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6, marginBottom: "1rem" }}>جاري التحميل من الخادم…</p>
        )}
        {!ot && !loading && !fetchErr && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            لا توجد بيانات OT بعد. شغّل فحصاً من{" "}
            <Link to="/dashboard" style={{ color: "var(--cyan)" }}>
              لوحة الأداء
            </Link>{" "}
            ثم ارجع هنا، أو افتح الصفحة في تبويب جديد بعد إتمام الفحص (يُجلب آخر فحص من الخادم).
          </p>
        )}

        {ot && (
          <>
            <p
              style={{
                fontSize: "0.88rem",
                color: "var(--muted)",
                lineHeight: 1.65,
                margin: "0 0 1rem",
                padding: "0.75rem 1rem",
                background: "var(--bg2)",
                borderRadius: "var(--radius)",
                border: "1px solid var(--bg3)",
              }}
            >
              التحليل هنا <strong style={{ color: "var(--fg)" }}>فعلي وسلبي</strong>: يُبنى من{" "}
              <strong style={{ color: "var(--fg)" }}>جدول اتصالات وعمليات</strong> جُمعت أثناء الفحص، ويُطابق منافذ
              ICS شائعة فقط — لا يُفترض اختراق منشأة ولا يُحلّل PCAP. الأصفار على حاسوب تطوير{" "}
              <strong style={{ color: "var(--fg)" }}>طبيعية</strong>.
            </p>
            {(!ot.ics_protocol_hits || ot.ics_protocol_hits.length === 0) && (
              <div
                style={{
                  marginBottom: "1rem",
                  padding: "0.75rem 1rem",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--info-banner-border)",
                  background: "var(--info-banner-bg)",
                  color: "var(--info-banner-fg)",
                  fontSize: "0.86rem",
                  lineHeight: 1.55,
                }}
              >
                <strong style={{ color: "var(--green)" }}>الفحص يعمل — OT فارغ لسبب متوقع:</strong> التحليل هنا يربط
                جدول اتصالات المضيف بمنافذ ICS شائعة (مثل 502، 102، 4840). على حاسوب تطوير عادي غالباً{" "}
                <strong>لا</strong> تظهر مثل هذه الاتصالات، فيبقى العدد 0 وهذا ليس عطلاً. جرّب من جهاز يصل لشبكة OT،
                أو لاحقاً PCAP/Scapy. أقسام <strong>MITRE</strong> و<strong>السياق الدفاعي</strong> تعتمد إشارات أخرى وقد
                تُظهر نتائج حتى بدون OT.
              </div>
            )}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: "0.65rem",
                marginBottom: "1.25rem",
              }}
            >
              <div style={kpiBox}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--fg)" }}>
                  {ot.distinct_ics_protocols ?? 0}
                </div>
                <div style={kpiLabel}>بروتوكولات ICS مميّزة (من الجدول)</div>
              </div>
              <div style={kpiBox}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--fg)" }}>
                  {(ot.ics_protocol_hits || []).length}
                </div>
                <div style={kpiLabel}>ملاحظات اتصال على منافذ صناعية</div>
              </div>
              <div
                style={{
                  ...kpiBox,
                  borderColor: pcs != null && pcs < 70 ? "rgba(248, 113, 113, 0.35)" : "var(--surface-border)",
                }}
              >
                <div
                  style={{
                    fontSize: "1.5rem",
                    fontWeight: 700,
                    color: pcs != null && pcs < 70 ? "var(--red)" : "var(--fg)",
                  }}
                >
                  {pcs ?? "—"}
                </div>
                <div style={kpiLabel}>Production continuity (تجريبي)</div>
              </div>
            </div>

            {ot.disclaimer?.trim() ? (
              <p style={{ fontSize: "0.82rem", color: "var(--muted)", margin: "0 0 1rem", lineHeight: 1.5 }}>
                {ot.disclaimer}
              </p>
            ) : null}

            {sp && (
              <section style={section}>
                <h2 style={h2}>ICS Specialist (Agent #6)</h2>
                <pre
                  style={{
                    margin: 0,
                    padding: "0.85rem 1rem",
                    background: "var(--surface-deep)",
                    borderRadius: "var(--radius)",
                    border: "1px solid var(--bg3)",
                    color: "var(--pre-fg)",
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
                <ul style={{ margin: 0, paddingLeft: "1.1rem", color: "var(--muted)", fontSize: "0.88rem" }}>
                  {ot.ot_playbooks_triggered!.map((p) => (
                    <li key={String(p.id)} style={{ marginBottom: "0.35rem" }}>
                      <strong style={{ color: "var(--fg)" }}>{p.name_ar || p.id}</strong>
                      {p.reason ? ` — ${p.reason}` : ""}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <section style={section}>
              <h2 style={h2}>MITRE ATT&CK for ICS (أمثلة من المرجع)</h2>
              <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0 0 0.75rem" }}>
                <a href={ot.ics_mitre_matrix_url || "https://attack.mitre.org/matrices/ics/"} style={{ color: "var(--cyan)" }}>
                  المصفوفة الرسمية
                </a>
                {" · "}تظليل حسب تكرار الربط في هذه الجلسة:
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {mitreCounts.length === 0 && (
                  <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>لا توجد تقنيات مرتبطة في هذه الجلسة.</span>
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
                      color: "var(--heat-cell-text)",
                      border: "1px solid var(--heat-cell-border)",
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
                      background: "var(--surface-deep)",
                      border: "1px solid var(--bg3)",
                      borderRadius: "var(--radius)",
                      fontSize: "0.82rem",
                      color: "var(--muted)",
                    }}
                  >
                    <div style={{ color: "var(--fg)", fontWeight: 600, marginBottom: "0.25rem" }}>{inv.endpoint}</div>
                    <div>Protocols: {(inv.protocols_observed || []).join(", ") || "—"}</div>
                    <div>Processes: {(inv.processes || []).join(", ") || "—"}</div>
                    {inv.note && <div style={{ marginTop: "0.35rem", fontSize: "0.78rem" }}>{inv.note}</div>}
                  </div>
                ))}
              </div>
            </section>

            <section style={section}>
              <h2 style={h2}>تنبيهات بروتوكول (اتصالات ذات منفذ ICS)</h2>
              <div className="table-wrap">
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
  background: "var(--surface-deep)",
  borderRadius: "var(--radius)",
  padding: "0.75rem",
  border: "1px solid var(--surface-border)",
  textAlign: "center",
};

const kpiLabel: CSSProperties = { fontSize: "0.72rem", color: "var(--muted)", marginTop: "0.25rem" };

const section: CSSProperties = { marginBottom: "1.35rem" };

const h2: CSSProperties = {
  fontSize: "1rem",
  color: "var(--cyan)",
  margin: "0 0 0.5rem",
  fontWeight: 600,
};

const pill: CSSProperties = {
  fontSize: "0.75rem",
  padding: "0.2rem 0.5rem",
  borderRadius: "999px",
  background: "var(--bg2)",
  color: "var(--pre-fg)",
  border: "1px solid var(--surface-border)",
};

function heatBg(n: number): string {
  if (n >= 3) return "var(--heat-3)";
  if (n === 2) return "color-mix(in srgb, var(--heat-2) 85%, transparent)";
  return "var(--heat-0)";
}
