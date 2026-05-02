import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { Link, useLocation } from "react-router-dom";
import FeatureNav from "./FeatureNav";

type DefenseContext = {
  agent?: string;
  disclaimer?: string;
  attribution?: Record<string, unknown>;
  profiles_ranked?: Array<Record<string, unknown>>;
  strategic_intent?: Record<string, string>;
  sophistication?: Record<string, unknown>;
  campaign?: Record<string, string>;
  playbooks_triggered?: Array<Record<string, unknown>>;
  mitre_heatmap?: Array<Record<string, unknown>>;
  recommended_defense_posture?: string[];
};

function loadDc(): DefenseContext | null {
  try {
    const extrasRaw = sessionStorage.getItem("coa_last_scan_extras");
    if (extrasRaw) {
      const x = JSON.parse(extrasRaw) as { defense_context?: DefenseContext };
      if (x.defense_context) return x.defense_context;
    }
    const raw = sessionStorage.getItem("coa_defense_context");
    if (raw) return JSON.parse(raw) as DefenseContext;
  } catch {
    return null;
  }
  return null;
}

export default function DefenseContextPage() {
  const [dc, setDc] = useState<DefenseContext | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const location = useLocation();

  const refresh = useCallback(() => {
    try {
      setErr(null);
      setDc(loadDc());
    } catch {
      setErr("تعذّر قراءة البيانات.");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [location.key, refresh]);

  useEffect(() => {
    const onScan = () => refresh();
    const onStorage = (e: StorageEvent) => {
      if (e.key === "coa_last_scan_extras" || e.key === "coa_defense_context") refresh();
    };
    window.addEventListener("coa-scan-complete", onScan);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("coa-scan-complete", onScan);
      window.removeEventListener("storage", onStorage);
    };
  }, [refresh]);

  const att = dc?.attribution || {};

  return (
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__row">
          <h1 className="page-title page-title--purple">سياق دفاعي — الوكيل #5</h1>
          <span className="page-subtitle">APT profiles · Playbooks · Heatmap بيانات</span>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main">
        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
        {!dc && !err && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            لا توجد بيانات. نفّذ{" "}
            <Link to="/dashboard" style={{ color: "var(--cyan)" }}>
              فحصاً من لوحة الأداء
            </Link>{" "}
            ثم ارجع لهذه الصفحة.
          </p>
        )}

        {dc && (
          <>
            {dc.disclaimer && (
              <p style={{ color: "var(--yellow)", fontSize: "0.9rem", padding: "0.75rem", background: "var(--bg2)", borderRadius: "var(--radius)" }}>
                {dc.disclaimer}
              </p>
            )}

            <section style={sec}>
              <h2 style={h2}>الإسناد (فرضي)</h2>
              <dl style={dl}>
                <dt>جهة مرجّحة</dt>
                <dd>{String(att.likely_actor ?? "—")}</dd>
                <dt>الثقة</dt>
                <dd>{String(att.confidence_percent ?? "—")}%</dd>
                <dt>التبرير</dt>
                <dd style={{ whiteSpace: "pre-wrap" }}>{String(att.reasoning ?? "—")}</dd>
                <dt>ملاحظة المصدر</dt>
                <dd>{String(att.source_note ?? "—")}</dd>
              </dl>
            </section>

            <section style={sec}>
              <h2 style={h2}>ملفات APT المرتبة (أعلى تشابه)</h2>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>المعرّف</th>
                      <th>الاسم</th>
                      <th>التشابه</th>
                      <th>أسباب</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(dc.profiles_ranked || []).map((p, i) => (
                      <tr key={i}>
                        <td>{String(p.profile_id ?? "")}</td>
                        <td>{String(p.display_name ?? "")}</td>
                        <td>{String(p.similarity ?? "")}</td>
                        <td style={{ fontSize: "0.8rem", maxWidth: "22rem" }}>
                          {Array.isArray(p.reasons) ? (p.reasons as string[]).join(" · ") : String(p.reasons ?? "")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!dc.profiles_ranked?.length && (
                  <p style={{ color: "var(--muted)", padding: "0.75rem" }}>لا توجد ترتيبات.</p>
                )}
              </div>
            </section>

            <section style={sec}>
              <h2 style={h2}>نية استراتيجية / تعقيد / حملة</h2>
              <pre
                style={{
                  ...preBox,
                  fontSize: "0.82rem",
                }}
              >
                {JSON.stringify(
                  {
                    strategic_intent: dc.strategic_intent,
                    sophistication: dc.sophistication,
                    campaign: dc.campaign,
                  },
                  null,
                  2,
                )}
              </pre>
            </section>

            <section style={sec}>
              <h2 style={h2}>Playbooks مفعّلة</h2>
              <ul style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                {(dc.playbooks_triggered || []).map((p, i) => (
                  <li key={i} style={{ marginBottom: "0.35rem" }}>
                    <strong style={{ color: "var(--fg)" }}>{String(p.id ?? "")}</strong> — {String(p.name_ar ?? p.name_en ?? "")}{" "}
                    {p.reason ? <span style={{ opacity: 0.9 }}>({String(p.reason)})</span> : null}
                  </li>
                ))}
              </ul>
              {!dc.playbooks_triggered?.length && <p style={{ color: "var(--muted)" }}>لم يُفعّل playbook في هذا الفحص.</p>}
            </section>

            <section style={sec}>
              <h2 style={h2}>موقف دفاعي مقترح</h2>
              <ul style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                {(dc.recommended_defense_posture || []).map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </section>

            <section style={sec}>
              <h2 style={h2}>خلايا Heatmap (بيانات خام)</h2>
              <p style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                للعرض الحراري استخدم{" "}
                <Link to="/mitre-heatmap" style={{ color: "var(--cyan)" }}>
                  صفحة خريطة MITRE
                </Link>
                .
              </p>
              <pre style={{ ...preBox, maxHeight: "200px", overflow: "auto", fontSize: "0.72rem" }}>
                {JSON.stringify(dc.mitre_heatmap || [], null, 2)}
              </pre>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

const sec: CSSProperties = { marginBottom: "1.5rem" };
const h2: CSSProperties = { fontSize: "1rem", color: "var(--fg)", margin: "0 0 0.5rem" };
const dl: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "140px 1fr",
  gap: "0.35rem 0.75rem",
  fontSize: "0.88rem",
  color: "var(--muted)",
};
const preBox: CSSProperties = {
  margin: 0,
  padding: "0.75rem 1rem",
  background: "var(--bg2)",
  borderRadius: "var(--radius)",
  border: "1px solid var(--bg3)",
  color: "var(--muted)",
  overflow: "auto",
};
