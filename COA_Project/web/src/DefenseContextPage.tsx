import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { Link, useLocation } from "react-router-dom";
import FeatureNav from "./FeatureNav";
import { useI18n } from "./i18n";

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

/** Keep other pages that read sessionStorage in sync after a server fetch. */
function mirrorDcToSessionStorage(next: DefenseContext) {
  try {
    sessionStorage.setItem("coa_defense_context", JSON.stringify(next));
    let extras: Record<string, unknown> = {};
    const extrasRaw = sessionStorage.getItem("coa_last_scan_extras");
    if (extrasRaw) {
      try {
        extras = JSON.parse(extrasRaw) as Record<string, unknown>;
      } catch {
        extras = {};
      }
    }
    extras.defense_context = next;
    sessionStorage.setItem("coa_last_scan_extras", JSON.stringify(extras));
  } catch {
    /* quota / private mode */
  }
}

export default function DefenseContextPage() {
  const { locale, t } = useI18n();
  const [dc, setDc] = useState<DefenseContext | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const location = useLocation();

  const refresh = useCallback(async () => {
    setErr(null);
    const local = loadDc();
    if (local) {
      setLoading(false);
      setDc(local);
      return;
    }
    setLoading(true);
    setDc(null);
    try {
      const res = await fetch("/api/last/defense-context");
      const json = (await res.json()) as {
        ok?: boolean;
        defense_context?: DefenseContext;
        error?: string;
      };
      if (res.ok && json.ok && json.defense_context) {
        mirrorDcToSessionStorage(json.defense_context);
        setDc(json.defense_context);
      } else {
        setDc(null);
        if (res.status >= 500) {
          setErr(json.error || t("common.serverError"));
        }
        /* 400 = no last scan — leave empty state without error */
      }
    } catch {
      setDc(null);
      setErr(t("common.connectError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void refresh();
  }, [location.key, refresh]);

  useEffect(() => {
    const onScan = () => {
      void refresh();
    };
    const onStorage = (e: StorageEvent) => {
      if (e.key === "coa_last_scan_extras" || e.key === "coa_defense_context") void refresh();
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
          <h1 className="page-title page-title--purple">{t("dc.title")}</h1>
          <span className="page-subtitle">{t("dc.subtitle")}</span>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main">
        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
        {loading && !dc && !err && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>{t("common.loadingServer")}</p>
        )}
        {!dc && !err && !loading && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            {t("dc.emptyPart1")}
            <Link to="/dashboard" style={{ color: "var(--cyan)" }}>
              {t("dc.emptyLink")}
            </Link>
            {t("dc.emptyPart2")}
          </p>
        )}

        {dc && (
          <>
            <p className="panel">{t("dc.intro")}</p>
            {dc.disclaimer && <p className="panel panel--disclaimer">{dc.disclaimer}</p>}

            <section style={sec}>
              <h2 style={h2}>{t("dc.attribution")}</h2>
              <dl style={dl}>
                <dt>{t("dc.dtActor")}</dt>
                <dd>{String(att.likely_actor ?? "—")}</dd>
                <dt>{t("dc.dtConfidence")}</dt>
                <dd>{String(att.confidence_percent ?? "—")}%</dd>
                <dt>{t("dc.dtReasoning")}</dt>
                <dd style={{ whiteSpace: "pre-wrap" }}>{String(att.reasoning ?? "—")}</dd>
                <dt>{t("dc.dtSourceNote")}</dt>
                <dd>{String(att.source_note ?? "—")}</dd>
              </dl>
            </section>

            <section style={sec}>
              <h2 style={h2}>{t("dc.profilesTitle")}</h2>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>{t("dc.thId")}</th>
                      <th>{t("dc.thName")}</th>
                      <th>{t("dc.thSimilarity")}</th>
                      <th>{t("dc.thReasons")}</th>
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
                  <p style={{ color: "var(--muted)", padding: "0.75rem" }}>{t("dc.noRanks")}</p>
                )}
              </div>
            </section>

            <section style={sec}>
              <h2 style={h2}>{t("dc.strategicBlock")}</h2>
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
              <h2 style={h2}>{t("dc.playbooksTitle")}</h2>
              <ul style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                {(dc.playbooks_triggered || []).map((p, i) => {
                  const pr = p as { id?: string; name_ar?: string; name_en?: string; reason?: string };
                  const name =
                    locale === "ar"
                      ? (pr.name_ar || pr.name_en || "")
                      : (pr.name_en || pr.name_ar || "");
                  return (
                    <li key={i} style={{ marginBottom: "0.35rem" }}>
                      <strong style={{ color: "var(--fg)" }}>{String(pr.id ?? "")}</strong> — {name}{" "}
                      {pr.reason ? <span style={{ opacity: 0.9 }}>({String(pr.reason)})</span> : null}
                    </li>
                  );
                })}
              </ul>
              {!dc.playbooks_triggered?.length && <p style={{ color: "var(--muted)" }}>{t("dc.noPlaybooks")}</p>}
            </section>

            <section style={sec}>
              <h2 style={h2}>{t("dc.postureTitle")}</h2>
              <ul style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                {(dc.recommended_defense_posture || []).map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
              </ul>
            </section>

            <section style={sec}>
              <h2 style={h2}>{t("dc.heatmapRaw")}</h2>
              <p style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                {t("dc.heatmapBefore")}
                <Link to="/mitre-heatmap" style={{ color: "var(--cyan)" }}>
                  {t("dc.heatmapLink")}
                </Link>
                {t("dc.heatmapAfter")}
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
