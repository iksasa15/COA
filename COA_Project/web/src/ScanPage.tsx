import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { DEMO_COUNCIL_REPORT_FALLBACK } from "./demoCouncilReport";
import FeatureNav from "./FeatureNav";
import { useI18n } from "./i18n";

type LogEvent = { timestamp: string; type: string; details: string };

type DefenseContextPayload = {
  agent?: string;
  attribution?: Record<string, unknown>;
  mitre_heatmap?: Array<{
    technique_id: string;
    name: string;
    tactic: string;
    heat: number;
  }>;
  disclaimer?: string;
  playbooks_triggered?: Array<Record<string, unknown>>;
  strategic_intent?: Record<string, string>;
  sophistication?: Record<string, unknown>;
  campaign?: Record<string, string>;
};

type MitreDeepPayload = {
  kill_chain_phases?: unknown[];
  navigator_layer?: Record<string, unknown>;
  ascii_report?: string;
  ics_context?: { ics_relevant?: boolean; note?: string };
  detection_gap_hints?: string[];
};

type OtIcsPayload = {
  presentation_demo?: boolean;
  passive_by_default?: boolean;
  disclaimer?: string;
  ics_protocol_hits?: Array<Record<string, unknown>>;
  inventory_sketch?: Array<Record<string, unknown>>;
  distinct_ics_protocols?: number;
  ot_playbooks_triggered?: Array<Record<string, unknown>>;
  production_continuity_score?: number;
  ics_specialist?: { ascii_report?: string };
};

type ScanPayload = {
  ok: boolean;
  error?: string;
  defense_context?: DefenseContextPayload;
  mitre_deep?: MitreDeepPayload;
  ot_ics?: OtIcsPayload;
  system_info?: Record<string, unknown>;
  analysis?: {
    total_threats: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    threats: Array<Record<string, unknown>>;
  };
  classification?: Record<string, unknown>;
  summary?: string;
  collection_duration?: number;
  processes?: Array<Record<string, unknown>>;
  processes_total?: number;
  network_connections?: Array<Record<string, unknown>>;
  connections_total?: number;
  events?: LogEvent[];
  council?: { ok?: boolean; report?: string | null; error?: string | null } | null;
  demo_seed?: boolean;
};

type TabId = "threats" | "processes" | "network" | "ot_ics" | "council" | "logs";

type CouncilAgentsHealth = {
  ok?: boolean;
  ollama?: {
    ollama_running?: boolean;
    model_available?: boolean;
    model_name?: string;
    base_url?: string;
    error?: string | null;
    suggestion?: string | null;
  };
  crewai_agents_ready?: boolean;
  error?: string;
  message?: string;
};

function appendLocalLog(
  lines: { ts: string; level: string; text: string }[],
  level: string,
  text: string,
) {
  const ts = new Date().toLocaleTimeString();
  return [...lines, { ts, level, text }];
}

async function downloadFromApi(path: string, fallbackName: string) {
  const res = await fetch(path);
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error((j as { error?: string }).error || res.statusText);
  }
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition");
  let name = fallbackName;
  if (cd) {
    const m = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(cd);
    if (m?.[1]) name = m[1].replace(/['"]/g, "");
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ScanPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState<TabId>("threats");
  // CrewAI agents (1–3): on by default; backend LLM from .env (Ollama local). User can turn off for faster scans.
  const [useCouncil, setUseCouncil] = useState(true);
  const [loading, setLoading] = useState(false);
  const [synthLoading, setSynthLoading] = useState(false);
  const [councilCheckLoading, setCouncilCheckLoading] = useState(false);
  const [councilCheckResult, setCouncilCheckResult] = useState<CouncilAgentsHealth | null>(null);
  const [data, setData] = useState<ScanPayload | null>(null);
  const [logLines, setLogLines] = useState<{ ts: string; level: string; text: string }[]>([]);
  const [status, setStatus] = useState(() => t("scan.statusReady"));

  const runScan = useCallback(async () => {
    setLoading(true);
    setLogLines([{ ts: new Date().toLocaleTimeString(), level: "INFO", text: t("scan.logStarting") }]);
    setStatus(t("scan.scanning"));
    setData(null);
    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          presentation_demo: false,
          use_council: useCouncil,
        }),
      });
      const json = (await res.json()) as ScanPayload;
      if (!res.ok || !json.ok) {
        throw new Error(json.error || "Scan failed");
      }
      setData(json);
      try {
        if (json.defense_context) {
          sessionStorage.setItem("coa_defense_context", JSON.stringify(json.defense_context));
        }
        sessionStorage.setItem(
          "coa_last_scan_extras",
          JSON.stringify({
            defense_context: json.defense_context ?? null,
            mitre_deep: json.mitre_deep ?? null,
            ot_ics: json.ot_ics ?? null,
          }),
        );
        window.dispatchEvent(new Event("coa-scan-complete"));
      } catch {
        /* ignore quota */
      }
      const serverLines = (json.events || []).map((ev) => ({
        ts: ev.timestamp,
        level: ev.type === "ERROR" ? "ERROR" : "INFO",
        text: `[${ev.type}] ${ev.details}`,
      }));
      const endTs = new Date().toLocaleTimeString();
      setLogLines((prev) => [
        ...prev,
        ...serverLines,
        {
          ts: endTs,
          level: "SUCCESS",
          text:
            `Scan complete — ${json.analysis?.total_threats ?? 0} threats, ` +
            `${(json.collection_duration ?? 0).toFixed(2)}s collection`,
        },
      ]);
      setStatus(
        t("scan.statusDone")
          .replace("{threats}", String(json.analysis?.total_threats ?? 0))
          .replace("{conns}", String(json.connections_total ?? 0))
          .replace("{procs}", String(json.processes_total ?? 0)),
      );
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setLogLines((L) => appendLocalLog(L, "ERROR", msg));
      setStatus(t("scan.errApi"));
    } finally {
      setLoading(false);
    }
  }, [useCouncil, t]);

  const loadSyntheticSession = useCallback(async () => {
    setSynthLoading(true);
    setLogLines([{ ts: new Date().toLocaleTimeString(), level: "INFO", text: t("scan.logSynthLoad") }]);
    setStatus(t("scan.synthLoading"));
    setData(null);
    try {
      const res = await fetch("/api/demo/seed-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const json = (await res.json()) as ScanPayload;
      if (!res.ok || !json.ok) {
        throw new Error(json.error || res.statusText || "Failed to load synthetic session");
      }
      const reportFromApi =
        json.council?.ok === true &&
        typeof json.council.report === "string" &&
        json.council.report.trim()
          ? json.council.report.trim()
          : DEMO_COUNCIL_REPORT_FALLBACK;
      const normalized: ScanPayload = {
        ...json,
        demo_seed: true,
        council: { ok: true, error: null, report: reportFromApi },
      };
      setData(normalized);
      try {
        if (normalized.defense_context) {
          sessionStorage.setItem("coa_defense_context", JSON.stringify(normalized.defense_context));
        }
        sessionStorage.setItem(
          "coa_last_scan_extras",
          JSON.stringify({
            defense_context: normalized.defense_context ?? null,
            mitre_deep: normalized.mitre_deep ?? null,
            ot_ics: normalized.ot_ics ?? null,
          }),
        );
        window.dispatchEvent(new Event("coa-scan-complete"));
      } catch {
        /* ignore quota */
      }
      const serverLines = (normalized.events || []).map((ev) => ({
        ts: ev.timestamp,
        level: ev.type === "ERROR" ? "ERROR" : "INFO",
        text: `[${ev.type}] ${ev.details}`,
      }));
      const endTs = new Date().toLocaleTimeString();
      setLogLines((prev) => [
        ...prev,
        ...serverLines,
        {
          ts: endTs,
          level: "SUCCESS",
          text: t("scan.logSynthDone").replace("{n}", String(normalized.analysis?.total_threats ?? 0)),
        },
      ]);
      setStatus(
        t("scan.statusSynth")
          .replace("{threats}", String(normalized.analysis?.total_threats ?? 0))
          .replace("{conns}", String(normalized.connections_total ?? 0))
          .replace("{procs}", String(normalized.processes_total ?? 0)),
      );
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setLogLines((L) => appendLocalLog(L, "ERROR", msg));
      setStatus(t("scan.statusSynthFail"));
    } finally {
      setSynthLoading(false);
    }
  }, [t]);

  const verifyCouncilAgents = useCallback(async () => {
    setCouncilCheckLoading(true);
    setCouncilCheckResult(null);
    try {
      const r = await fetch("/api/health/council-agents");
      const j = (await r.json()) as CouncilAgentsHealth;
      setCouncilCheckResult(j);
    } catch (e) {
      setCouncilCheckResult({
        ok: false,
        error: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setCouncilCheckLoading(false);
    }
  }, []);

  const stats = useMemo(() => {
    const a = data?.analysis;
    const conns = data?.connections_total ?? 0;
    const procs = data?.processes_total ?? 0;
    return [
      { label: t("scan.statConnections"), value: String(conns), color: "var(--cyan)" },
      { label: t("scan.statProcesses"), value: String(procs), color: "var(--green)" },
      { label: t("scan.statCritical"), value: String(a?.critical ?? "—"), color: "var(--red)" },
      { label: t("scan.statHigh"), value: String(a?.high ?? "—"), color: "var(--orange)" },
      { label: t("scan.statMedium"), value: String(a?.medium ?? "—"), color: "var(--yellow)" },
      { label: t("scan.statTotalThreats"), value: String(a?.total_threats ?? "—"), color: "var(--purple)" },
    ];
  }, [data, t]);

  return (
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__row">
          <h1 className="page-title">C.O.A</h1>
          <span className="page-subtitle">{t("scan.subtitle")}</span>
          <Link to="/" className="page-header__home">
            {t("scan.home")}
          </Link>
        </div>
        <FeatureNav />
      </header>

      <div className="page-toolbar">
        <button type="button" className="btn-primary" disabled={loading || synthLoading} onClick={runScan}>
          {loading ? t("scan.scanning") : t("scan.startScan")}
        </button>
        <button
          type="button"
          className="btn-ghost"
          disabled={loading || synthLoading}
          title={t("scan.synthTitle")}
          onClick={() => void loadSyntheticSession()}
        >
          {synthLoading ? t("scan.synthLoading") : t("scan.synthBtn")}
        </button>
        <label className="checkbox" title={t("scan.councilTitle")}>
          <input
            type="checkbox"
            checked={useCouncil}
            onChange={(e) => setUseCouncil(e.target.checked)}
          />
          {t("scan.councilLabel")}
        </label>
        <button
          type="button"
          className="btn-ghost"
          disabled={councilCheckLoading || loading || synthLoading}
          title={t("scan.councilCheckTitle")}
          onClick={() => void verifyCouncilAgents()}
        >
          {councilCheckLoading ? t("scan.councilCheckLoading") : t("scan.councilCheckBtn")}
        </button>
        <div className="page-toolbar-spacer" />
        <button
          type="button"
          className="btn-ghost"
          disabled={!data?.ok}
          onClick={() => downloadFromApi("/api/reports/txt", "COA_Report.txt")}
        >
          {t("scan.exportTxt")}
        </button>
        <button
          type="button"
          className="btn-ghost"
          disabled={!data?.ok}
          onClick={() => downloadFromApi("/api/reports/html", "COA_Report.html")}
        >
          {t("scan.exportHtml")}
        </button>
        <button
          type="button"
          className="btn-accent"
          disabled={!data?.ok}
          onClick={() => downloadFromApi("/api/reports/incident", "COA_Incident_Report.txt")}
        >
          {t("scan.exportIncident")}
        </button>
        <button
          type="button"
          className="btn-ghost"
          disabled={!data?.ok}
          onClick={() => downloadFromApi("/api/reports/mitre-navigator.json", "coa_mitre_navigator_layer.json")}
        >
          {t("scan.exportNav")}
        </button>
      </div>

      {councilCheckResult && (
        <div
          className="page-section"
          style={{
            marginTop: "-0.25rem",
            marginBottom: "0.5rem",
            padding: "0.65rem 0.85rem",
            borderRadius: "var(--radius)",
            border: `1px solid ${councilCheckResult.ok && councilCheckResult.crewai_agents_ready ? "var(--green)" : "var(--orange)"}`,
            background: "var(--bg2)",
            fontSize: "0.86rem",
          }}
        >
          {councilCheckResult.ok && councilCheckResult.crewai_agents_ready ? (
            <strong style={{ color: "var(--green)" }}>{t("scan.councilOk")}</strong>
          ) : (
            <strong style={{ color: "var(--orange)" }}>{t("scan.councilBad")}</strong>
          )}{" "}
          {councilCheckResult.message && <span style={{ color: "var(--muted)" }}>{councilCheckResult.message}</span>}
          {councilCheckResult.error && (
            <span style={{ color: "var(--muted)", display: "block", marginTop: "0.35rem" }}>{councilCheckResult.error}</span>
          )}
          {councilCheckResult.ollama?.suggestion && !councilCheckResult.ok && (
            <pre
              style={{
                margin: "0.4rem 0 0",
                fontSize: "0.75rem",
                color: "var(--muted)",
                whiteSpace: "pre-wrap",
                direction: "ltr",
                textAlign: "left",
              }}
            >
              {councilCheckResult.ollama.suggestion}
            </pre>
          )}
        </div>
      )}

      <div className="page-section">
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
            gap: "0.5rem",
          }}
        >
          {stats.map((s) => (
            <div
              key={s.label}
              style={{
                background: "var(--bg2)",
                borderRadius: "var(--radius)",
                padding: "0.75rem",
                textAlign: "center",
                border: "1px solid var(--surface-border)",
              }}
            >
              <div style={{ fontSize: "1.35rem", fontWeight: 700, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: "0.78rem", color: "var(--muted)" }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {data?.summary && (
        <div
          className="page-outset"
          style={{
            padding: "0.85rem 1rem",
            background: "var(--bg2)",
            borderRadius: "var(--radius)",
            border: "1px solid var(--bg3)",
            fontSize: "0.9rem",
            color: "var(--muted)",
          }}
        >
          <strong style={{ color: "var(--fg)" }}>{t("scan.execSummary")}</strong>
          <p style={{ margin: "0.5rem 0 0", whiteSpace: "pre-wrap" }}>{data.summary}</p>
        </div>
      )}

      {data?.defense_context?.attribution && (
        <div
          className="page-outset"
          style={{
            padding: "0.85rem 1rem",
            background: "var(--bg2)",
            borderRadius: "var(--radius)",
            border: "1px solid var(--purple)",
            fontSize: "0.88rem",
            color: "var(--muted)",
          }}
        >
          <strong style={{ color: "var(--purple)" }}>{t("scan.defenseCard")}</strong>
          <p style={{ margin: "0.4rem 0 0" }}>
            {String((data.defense_context.attribution as { likely_actor?: string }).likely_actor ?? "")}{" "}
            <span style={{ opacity: 0.85 }}>
              — {t("scan.confidence")}{" "}
              {String((data.defense_context.attribution as { confidence_percent?: number }).confidence_percent ?? 0)}%
            </span>
          </p>
          <p style={{ margin: "0.35rem 0 0", fontSize: "0.82rem" }}>
            {String((data.defense_context.attribution as { reasoning?: string }).reasoning ?? "")}
          </p>
          {(data.defense_context.playbooks_triggered?.length ?? 0) > 0 && (
            <p style={{ margin: "0.5rem 0 0", fontSize: "0.82rem" }}>
              {t("scan.playbooks")}{" "}
              {data.defense_context.playbooks_triggered!.map((p) => String(p.id ?? p)).join(", ")}
            </p>
          )}
        </div>
      )}

      <main className="page-main page-main--scan">
        <div className="tabs">
          {(
            [
              ["threats", "scan.tab.threats"],
              ["processes", "scan.tab.processes"],
              ["network", "scan.tab.network"],
              ["ot_ics", "scan.tab.otIcs"],
              ["council", "scan.tab.council"],
              ["logs", "scan.tab.logs"],
            ] as const
          ).map(([id, key]) => (
            <button
              key={id}
              type="button"
              className={`tab ${tab === id ? "active" : ""}`}
              onClick={() => setTab(id)}
            >
              {t(key)}
            </button>
          ))}
        </div>

        {tab === "threats" && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Severity</th>
                  <th>Confidence</th>
                  <th>Score</th>
                  <th>Source</th>
                  <th>Details</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {(data?.analysis?.threats || []).map((t, i) => {
                  const sev = String(t.severity ?? "");
                  return (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td className={`sev-${sev}`}>{sev}</td>
                      <td>{String(t.confidence ?? "")}</td>
                      <td>{String(t.score ?? "")}</td>
                      <td>{String(t.source ?? "")}</td>
                      <td>{String(t.details ?? "")}</td>
                      <td>{String(t.recommended_action ?? "")}</td>
                    </tr>
                  );
                })}
                {!data?.analysis?.threats?.length && (
                  <tr>
                    <td colSpan={7} style={{ color: "var(--muted)", padding: "1.5rem" }}>
                      No scan yet, or no threats detected.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {tab === "processes" && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>PID</th>
                  <th>Name</th>
                  <th>CPU%</th>
                  <th>RAM%</th>
                  <th>Path</th>
                </tr>
              </thead>
              <tbody>
                {(data?.processes || []).map((p, i) => (
                  <tr key={i}>
                    <td>{String(p.pid ?? "")}</td>
                    <td>{String(p.name ?? "")}</td>
                    <td>{String(p.cpu_percent ?? 0)}%</td>
                    <td>{String(p.memory_percent ?? 0)}%</td>
                    <td style={{ wordBreak: "break-all" }}>{String(p.path ?? "")}</td>
                  </tr>
                ))}
                {!data?.processes?.length && (
                  <tr>
                    <td colSpan={5} style={{ color: "var(--muted)", padding: "1.5rem" }}>
                      Run a scan to load processes (first {250} shown).
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {tab === "network" && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>PID</th>
                  <th>Process</th>
                  <th>Local</th>
                  <th>Remote</th>
                  <th>Status</th>
                  <th>Proto</th>
                </tr>
              </thead>
              <tbody>
                {(data?.network_connections || []).map((c, i) => (
                  <tr key={i}>
                    <td>{String(c.pid ?? "")}</td>
                    <td>{String(c.process_name ?? "")}</td>
                    <td>{String(c.local_address ?? "")}</td>
                    <td>{String(c.remote_address ?? "")}</td>
                    <td>{String(c.status ?? "")}</td>
                    <td>{String(c.protocol ?? "")}</td>
                  </tr>
                ))}
                {!data?.network_connections?.length && (
                  <tr>
                    <td colSpan={6} style={{ color: "var(--muted)", padding: "1.5rem" }}>
                      Run a scan to load connections.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {tab === "ot_ics" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {!data?.ot_ics ? (
              <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--muted)", lineHeight: 1.5 }}>
                {t("scan.ot.runScanHint")}
              </p>
            ) : data.ot_ics.disclaimer?.trim() ? (
              <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--muted)", lineHeight: 1.5 }}>
                {data.ot_ics.disclaimer}
              </p>
            ) : null}
            {data?.ot_ics && (
              <>
                {(data.ot_ics.ics_protocol_hits || []).length === 0 && (
                  <p
                    style={{
                      margin: 0,
                      padding: "0.5rem 0.65rem",
                      background: "rgba(20, 184, 166, 0.1)",
                      border: "1px solid rgba(20, 184, 166, 0.35)",
                      borderRadius: "var(--radius)",
                      fontSize: "0.82rem",
                      color: "var(--fg)",
                      lineHeight: 1.45,
                    }}
                  >
                    <strong>{t("scan.ot.zeroHitsStrong")}</strong> {t("scan.ot.zeroHits")}
                  </p>
                )}
                <div style={{ fontSize: "0.85rem", color: "var(--fg)" }}>
                  <strong>{t("scan.ot.distinctProtocols")}</strong> {data.ot_ics.distinct_ics_protocols ?? 0} ·{" "}
                  <strong>{t("scan.ot.hits")}</strong> {(data.ot_ics.ics_protocol_hits || []).length} ·{" "}
                  <strong>{t("scan.ot.continuity")}</strong> {data.ot_ics.production_continuity_score ?? "—"}
                </div>
                {(data.ot_ics.ot_playbooks_triggered || []).length > 0 && (
                  <div style={{ fontSize: "0.85rem", color: "var(--orange)" }}>
                    <strong>{t("scan.ot.playbooks")}</strong>{" "}
                    {data.ot_ics.ot_playbooks_triggered!.map((p) => String(p.id ?? p)).join(", ")}
                  </div>
                )}
                <pre
                  style={{
                    margin: 0,
                    padding: "0.75rem 1rem",
                    background: "var(--bg2)",
                    borderRadius: "var(--radius)",
                    border: "1px solid var(--bg3)",
                    color: "var(--muted)",
                    fontSize: "0.78rem",
                    whiteSpace: "pre-wrap",
                    maxHeight: "320px",
                    overflow: "auto",
                  }}
                >
                  {data.ot_ics.ics_specialist?.ascii_report || t("scan.ot.noSpecialist")}
                </pre>
                <Link
                  to="/ot-dashboard"
                  style={{ color: "var(--cyan)", fontWeight: 600, fontSize: "0.9rem", textDecoration: "none" }}
                >
                  {t("scan.ot.openFull")}
                </Link>
              </>
            )}
          </div>
        )}

        {tab === "council" && (
          <div style={{ fontSize: "0.88rem", color: "var(--muted)", lineHeight: 1.55 }}>
            {data?.demo_seed ? (
              <pre
                style={{
                  margin: 0,
                  padding: "0.75rem 1rem",
                  background: "var(--bg2)",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--bg3)",
                  color: "var(--fg)",
                  whiteSpace: "pre-wrap",
                  fontSize: "0.8rem",
                  maxHeight: "min(70vh, 520px)",
                  overflow: "auto",
                }}
              >
                {(() => {
                  const r = data.council?.report;
                  return typeof r === "string" && r.trim() ? r.trim() : DEMO_COUNCIL_REPORT_FALLBACK;
                })()}
              </pre>
            ) : data?.council?.ok === true &&
              typeof data.council.report === "string" &&
              data.council.report.trim() ? (
              <pre
                style={{
                  margin: 0,
                  padding: "0.75rem 1rem",
                  background: "var(--bg2)",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--bg3)",
                  color: "var(--fg)",
                  whiteSpace: "pre-wrap",
                  fontSize: "0.8rem",
                  maxHeight: "min(70vh, 520px)",
                  overflow: "auto",
                }}
              >
                {data.council.report.trim()}
              </pre>
            ) : data?.council && data.council.ok === false ? (
              <pre
                style={{
                  margin: "0.75rem 0 0",
                  padding: "0.75rem 1rem",
                  background: "rgba(239, 68, 68, 0.08)",
                  border: "1px solid rgba(239, 68, 68, 0.35)",
                  borderRadius: "var(--radius)",
                  color: "var(--fg)",
                  whiteSpace: "pre-wrap",
                  fontSize: "0.82rem",
                }}
              >
                {data.council.error || "Council run failed"}
              </pre>
            ) : data?.council?.ok === true && !data.council.report?.trim() ? (
              <p style={{ margin: 0 }}>اكتمل المجلس لكن لا يوجد نص في الاستجابة.</p>
            ) : (
              <p style={{ margin: 0 }}>
                فعّل خيار «مجلس الوكلاء» قبل المسح، أو راجع{" "}
                <code style={{ color: "var(--cyan)" }}>GET /api/health/ollama</code> للتأكد أن Ollama يعمل والنموذج
                مثبت.
              </p>
            )}
          </div>
        )}

        {tab === "logs" && (
          <div className="log-box">
            {logLines.map((line, i) => (
              <div key={i} className={`log-${line.level}`}>
                [{line.ts}] [{line.level}] {line.text}
              </div>
            ))}
            {!logLines.length && (
              <span style={{ color: "var(--muted)" }}>Logs appear after a scan.</span>
            )}
          </div>
        )}
      </main>

      <footer className="page-footer">
        {status}
      </footer>
    </div>
  );
}
