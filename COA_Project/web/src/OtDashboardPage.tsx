import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { Link, useLocation } from "react-router-dom";
import FeatureNav from "./FeatureNav";
import { useI18n } from "./i18n";

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
  const { locale, t } = useI18n();
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
          setFetchErr(json.error || t("common.serverError"));
        }
      }
    } catch {
      setOt(null);
      setFetchErr(t("common.connectError"));
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

  const impactFields: Array<{ key: "cyber_impact" | "operational_impact" | "safety_impact"; label: string }> = [
    { key: "cyber_impact", label: t("ot.pillCyber") },
    { key: "operational_impact", label: t("ot.pillOperational") },
    { key: "safety_impact", label: t("ot.pillSafety") },
  ];

  return (
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__row">
          <h1 className="page-title">{t("ot.title")}</h1>
          <span className="page-subtitle">{t("ot.subtitle")}</span>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main">
        {fetchErr && (
          <p style={{ color: "var(--red)", fontSize: "0.88rem", marginBottom: "0.75rem" }}>{fetchErr}</p>
        )}
        {loading && !ot && !fetchErr && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6, marginBottom: "1rem" }}>{t("common.loadingServer")}</p>
        )}
        {!ot && !loading && !fetchErr && (
          <p style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            {t("ot.noDataPart1")}
            <Link to="/dashboard" style={{ color: "var(--cyan)" }}>
              {t("ot.noDataLink")}
            </Link>
            {t("ot.noDataPart2")}
          </p>
        )}

        {ot && (
          <>
            <p className="panel">{t("ot.intro")}</p>
            {(!ot.ics_protocol_hits || ot.ics_protocol_hits.length === 0) && (
              <div className="panel panel--info" style={{ marginBottom: "1rem", fontSize: "0.86rem", lineHeight: 1.55 }}>
                <strong style={{ color: "var(--green)" }}>{t("ot.emptyHitsTitle")}</strong> {t("ot.emptyHitsBody")}
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
                <div style={kpiLabel}>{t("ot.kpiProtocols")}</div>
              </div>
              <div style={kpiBox}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--fg)" }}>
                  {(ot.ics_protocol_hits || []).length}
                </div>
                <div style={kpiLabel}>{t("ot.kpiPortHits")}</div>
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
                <div style={kpiLabel}>{t("ot.kpiContinuity")}</div>
              </div>
            </div>

            {ot.disclaimer?.trim() ? (
              <p style={{ fontSize: "0.82rem", color: "var(--muted)", margin: "0 0 1rem", lineHeight: 1.5 }}>
                {ot.disclaimer}
              </p>
            ) : null}

            {sp && (
              <section style={section}>
                <h2 style={h2}>{t("ot.icsSpecialistTitle")}</h2>
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
                  {impactFields.map(({ key, label }) => (
                    <span key={key} style={pill}>
                      {label}: {String((sp as Record<string, string>)[key] ?? "—")}
                    </span>
                  ))}
                </div>
              </section>
            )}

            {(ot.ot_playbooks_triggered || []).length > 0 && (
              <section style={section}>
                <h2 style={h2}>{t("ot.otPlaybooks")}</h2>
                <ul
                  style={{
                    margin: 0,
                    paddingInlineStart: "1.1rem",
                    color: "var(--muted)",
                    fontSize: "0.88rem",
                  }}
                >
                  {ot.ot_playbooks_triggered!.map((p) => {
                    const name =
                      locale === "ar"
                        ? (p.name_ar || p.name_en || p.id)
                        : (p.name_en || p.name_ar || p.id);
                    return (
                      <li key={String(p.id)} style={{ marginBottom: "0.35rem" }}>
                        <strong style={{ color: "var(--fg)" }}>{name}</strong>
                        {p.reason ? ` — ${p.reason}` : ""}
                      </li>
                    );
                  })}
                </ul>
              </section>
            )}

            <section style={section}>
              <h2 style={h2}>{t("ot.mitreSectionTitle")}</h2>
              <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0 0 0.75rem" }}>
                <a href={ot.ics_mitre_matrix_url || "https://attack.mitre.org/matrices/ics/"} style={{ color: "var(--cyan)" }}>
                  {t("ot.mitreMatrixLink")}
                </a>
                {" · "}
                {t("ot.mitreHint")}
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {mitreCounts.length === 0 && (
                  <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{t("ot.noMitreThisSession")}</span>
                )}
                {mitreCounts.map(([id, n]) => (
                  <span
                    key={id}
                    title={t("ot.mitreObserved").replace("{n}", String(n))}
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
              <h2 style={h2}>{t("ot.inventoryTitle")}</h2>
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
                    <div>
                      {t("ot.invProtocols")}: {(inv.protocols_observed || []).join(", ") || "—"}
                    </div>
                    <div>
                      {t("ot.invProcesses")}: {(inv.processes || []).join(", ") || "—"}
                    </div>
                    {inv.note && <div style={{ marginTop: "0.35rem", fontSize: "0.78rem" }}>{inv.note}</div>}
                  </div>
                ))}
              </div>
            </section>

            <section style={section}>
              <h2 style={h2}>{t("ot.protocolAlertsTitle")}</h2>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>{t("ot.thProcess")}</th>
                      <th>{t("ot.thLocal")}</th>
                      <th>{t("ot.thRemote")}</th>
                      <th>{t("ot.thPort")}</th>
                      <th>{t("ot.thProtocol")}</th>
                      <th>{t("ot.thMitreExamples")}</th>
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
  background: "var(--panel-bg)",
  borderRadius: "var(--radius)",
  padding: "0.75rem",
  border: "1px solid var(--panel-border)",
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
