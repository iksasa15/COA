import { useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import FeatureNav from "./FeatureNav";
import { useI18n } from "./i18n";

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

function mirrorMitreDeepToSessionStorage(next: MitreDeep) {
  try {
    let extras: Record<string, unknown> = {};
    const extrasRaw = sessionStorage.getItem("coa_last_scan_extras");
    if (extrasRaw) {
      try {
        extras = JSON.parse(extrasRaw) as Record<string, unknown>;
      } catch {
        extras = {};
      }
    }
    extras.mitre_deep = next;
    sessionStorage.setItem("coa_last_scan_extras", JSON.stringify(extras));
  } catch {
    /* quota */
  }
}

export default function MitreDeepPage() {
  const { t } = useI18n();
  const [deep, setDeep] = useState<MitreDeep | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const location = useLocation();

  const refresh = useCallback(async () => {
    setErr(null);
    const local = loadDeep();
    if (local) {
      setLoading(false);
      setDeep(local);
      return;
    }
    setLoading(true);
    setDeep(null);
    try {
      const res = await fetch("/api/last/mitre-deep");
      const json = (await res.json()) as { ok?: boolean; mitre_deep?: MitreDeep; error?: string };
      if (res.ok && json.ok && json.mitre_deep) {
        mirrorMitreDeepToSessionStorage(json.mitre_deep);
        setDeep(json.mitre_deep);
      } else {
        setDeep(null);
        if (res.status >= 500) {
          setErr(json.error || t("common.serverError"));
        }
      }
    } catch {
      setDeep(null);
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
      if (e.key === "coa_last_scan_extras") void refresh();
    };
    window.addEventListener("coa-scan-complete", onScan);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("coa-scan-complete", onScan);
      window.removeEventListener("storage", onStorage);
    };
  }, [refresh]);

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
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__row">
          <h1 className="page-title">{t("md.title")}</h1>
          <span className="page-subtitle">{t("md.subtitle")}</span>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main">
        {err && <p style={{ color: "var(--red)" }}>{err}</p>}
        {loading && !deep && !err && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>{t("common.loadingServer")}</p>
        )}
        {!deep && !err && !loading && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            {t("md.emptyPart1")}{" "}
            <Link to="/dashboard" style={{ color: "var(--cyan)" }}>
              {t("md.emptyLink")}
            </Link>{" "}
            {t("md.emptyPart2")}
          </p>
        )}

        {deep && (
          <>
            <p className="panel">{t("md.intro")}</p>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
              <button type="button" className="btn-accent" disabled={!deep.navigator_layer} onClick={downloadNavigatorLayer}>
                {t("md.exportNav")}
              </button>
              <span style={{ fontSize: "0.8rem", color: "var(--muted)", alignSelf: "center" }}>
                {t("md.exportHint")} <code>/api/reports/mitre-navigator.json</code>
              </span>
            </div>

            {deep.ics_context && (
              <section
                className={`panel${deep.ics_context.ics_relevant ? " panel--warn" : ""}`}
                style={{ marginBottom: "1rem", fontSize: "0.88rem" }}
              >
                <strong>
                  {deep.ics_context.ics_relevant ? t("md.icsRelevant") : t("md.icsNeutral")}:
                </strong>{" "}
                {deep.ics_context.note}
              </section>
            )}

            <section style={{ marginBottom: "1.25rem" }}>
              <h2 style={{ fontSize: "1rem", color: "var(--fg)", margin: "0 0 0.5rem" }}>{t("md.gapsTitle")}</h2>
              <ul style={{ color: "var(--muted)", fontSize: "0.88rem" }}>
                {(deep.detection_gap_hints || []).length === 0 && <li>{t("md.noGaps")}</li>}
                {(deep.detection_gap_hints || []).map((g, i) => (
                  <li key={i} style={{ marginBottom: "0.35rem" }}>
                    {g}
                  </li>
                ))}
              </ul>
            </section>

            <section style={{ marginBottom: "1.25rem" }}>
              <h2 style={{ fontSize: "1rem", color: "var(--fg)", margin: "0 0 0.5rem" }}>{t("md.killChainTitle")}</h2>
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
                <p style={{ color: "var(--muted)", fontSize: "0.88rem" }}>{t("md.noPhases")}</p>
              )}
            </section>

            <section>
              <h2 style={{ fontSize: "1rem", color: "var(--fg)", margin: "0 0 0.5rem" }}>{t("md.asciiTitle")}</h2>
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
                {deep.ascii_report || t("md.noAscii")}
              </pre>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
