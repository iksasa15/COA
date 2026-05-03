import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import FeatureNav from "./FeatureNav";

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
  const [tab, setTab] = useState<TabId>("threats");
  const [dryRun, setDryRun] = useState(false);
  const [presentationDemo, setPresentationDemo] = useState(false);
  // CrewAI agents (1–3): on by default; backend LLM from .env (Ollama local). User can turn off for faster scans.
  const [useCouncil, setUseCouncil] = useState(true);
  const [loading, setLoading] = useState(false);
  const [councilCheckLoading, setCouncilCheckLoading] = useState(false);
  const [councilCheckResult, setCouncilCheckResult] = useState<CouncilAgentsHealth | null>(null);
  const [data, setData] = useState<ScanPayload | null>(null);
  const [logLines, setLogLines] = useState<{ ts: string; level: string; text: string }[]>([]);
  const [status, setStatus] = useState("Ready — start the API (python web_api.py) then scan.");

  const runScan = useCallback(async () => {
    setLoading(true);
    setLogLines([{ ts: new Date().toLocaleTimeString(), level: "INFO", text: "Starting scan…" }]);
    setStatus("Scanning…");
    setData(null);
    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dry_run: dryRun,
          presentation_demo: presentationDemo,
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
        `Done — ${json.analysis?.total_threats ?? 0} threats · ` +
          `${json.connections_total ?? 0} connections · ` +
          `${json.processes_total ?? 0} processes`,
      );
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setLogLines((L) => appendLocalLog(L, "ERROR", msg));
      setStatus("Error — check API is running on port 5050");
    } finally {
      setLoading(false);
    }
  }, [dryRun, presentationDemo, useCouncil]);

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
      { label: "Connections", value: String(conns), color: "var(--cyan)" },
      { label: "Processes", value: String(procs), color: "var(--green)" },
      { label: "Critical", value: String(a?.critical ?? "—"), color: "var(--red)" },
      { label: "High", value: String(a?.high ?? "—"), color: "var(--orange)" },
      { label: "Medium", value: String(a?.medium ?? "—"), color: "var(--yellow)" },
      { label: "Total threats", value: String(a?.total_threats ?? "—"), color: "var(--purple)" },
    ];
  }, [data]);

  return (
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__row">
          <h1 className="page-title">C.O.A</h1>
          <span className="page-subtitle">Council of Agents — لوحة الأداء</span>
          <Link to="/" className="page-header__home">
            الرئيسية
          </Link>
        </div>
        <FeatureNav />
      </header>

      <div className="page-toolbar">
        <button type="button" className="btn-primary" disabled={loading} onClick={runScan}>
          {loading ? "Scanning…" : "Start scan"}
        </button>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={dryRun}
            onChange={(e) => setDryRun(e.target.checked)}
          />
          Dry run (remediation simulation)
        </label>
        <label className="checkbox" title="بيانات OT محاكاة من fixtures — للعرض أمام المحكّمين">
          <input
            type="checkbox"
            checked={presentationDemo}
            onChange={(e) => setPresentationDemo(e.target.checked)}
          />
          عرض OT للمحكّمين (محاكاة)
        </label>
        <label
          className="checkbox"
          title="المجلس يستخدم Ollama من إعدادات الخادم (.env). عطّل المربع لتسريع الفحص بدون وكلاء LLM."
        >
          <input
            type="checkbox"
            checked={useCouncil}
            onChange={(e) => setUseCouncil(e.target.checked)}
          />
          مجلس الوكلاء (CrewAI + LLM من .env) — افتراضي: تشغيل
        </label>
        <button
          type="button"
          className="btn-ghost"
          disabled={councilCheckLoading || loading}
          title="يتحقق من إعداد LLM + إنشاء وكيل CrewAI (بدون تشغيل فحص كامل)"
          onClick={() => void verifyCouncilAgents()}
        >
          {councilCheckLoading ? "جاري التحقق…" : "التحقق من وكلاء الذكاء"}
        </button>
        <div className="page-toolbar-spacer" />
        <button
          type="button"
          className="btn-ghost"
          disabled={!data?.ok}
          onClick={() => downloadFromApi("/api/reports/txt", "COA_Report.txt")}
        >
          Export TXT
        </button>
        <button
          type="button"
          className="btn-ghost"
          disabled={!data?.ok}
          onClick={() => downloadFromApi("/api/reports/html", "COA_Report.html")}
        >
          Export HTML
        </button>
        <button
          type="button"
          className="btn-accent"
          disabled={!data?.ok}
          onClick={() => downloadFromApi("/api/reports/incident", "COA_Incident_Report.txt")}
        >
          Incident report
        </button>
        <button
          type="button"
          className="btn-ghost"
          disabled={!data?.ok}
          onClick={() => downloadFromApi("/api/reports/mitre-navigator.json", "coa_mitre_navigator_layer.json")}
        >
          Navigator JSON
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
            <strong style={{ color: "var(--green)" }}>وكلاء الذكاء جاهزة:</strong>
          ) : (
            <strong style={{ color: "var(--orange)" }}>وكلاء الذكاء غير جاهزة:</strong>
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
        {data?.ot_ics?.presentation_demo && (
          <div
            style={{
              marginBottom: "0.75rem",
              padding: "0.65rem 0.85rem",
              borderRadius: "var(--radius)",
              border: "1px solid rgba(251, 191, 36, 0.45)",
              background: "rgba(0, 40, 35, 0.92)",
              color: "var(--warn-banner-fg)",
              fontSize: "0.86rem",
            }}
          >
            <strong>عرض توضيحي:</strong> قسم OT/ICS يعرض بيانات محاكاة من المشروع (للهاكاثون) — بقية الفحص من
            الجهاز الحقيقي.
          </div>
        )}
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
          <strong style={{ color: "var(--fg)" }}>Executive summary</strong>
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
          <strong style={{ color: "var(--purple)" }}>Defense Context (Agent #5)</strong>
          <p style={{ margin: "0.4rem 0 0" }}>
            {String((data.defense_context.attribution as { likely_actor?: string }).likely_actor ?? "")}{" "}
            <span style={{ opacity: 0.85 }}>
              — confidence{" "}
              {String((data.defense_context.attribution as { confidence_percent?: number }).confidence_percent ?? 0)}%
            </span>
          </p>
          <p style={{ margin: "0.35rem 0 0", fontSize: "0.82rem" }}>
            {String((data.defense_context.attribution as { reasoning?: string }).reasoning ?? "")}
          </p>
          {(data.defense_context.playbooks_triggered?.length ?? 0) > 0 && (
            <p style={{ margin: "0.5rem 0 0", fontSize: "0.82rem" }}>
              Playbooks:{" "}
              {data.defense_context.playbooks_triggered!.map((p) => String(p.id ?? p)).join(", ")}
            </p>
          )}
        </div>
      )}

      <main className="page-main page-main--scan">
        <div className="tabs">
          {(
            [
              ["threats", "Threats"],
              ["processes", "Processes"],
              ["network", "Network"],
              ["ot_ics", "OT/ICS"],
              ["council", "Multi-AI"],
              ["logs", "Logs"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={`tab ${tab === id ? "active" : ""}`}
              onClick={() => setTab(id)}
            >
              {label}
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
            <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--muted)", lineHeight: 1.5 }}>
              {data?.ot_ics?.disclaimer ||
                "Run a scan to load passive OT/ICS correlation (known industrial ports + processes)."}
            </p>
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
                    <strong>0 hits طبيعي</strong> على جهاز بدون اتصالات صناعية — الفحص نفسه ناجح؛ راجع تبويب
                    Threats وصفحات MITRE/السياق الدفاعي لبقية النتائج.
                  </p>
                )}
                <div style={{ fontSize: "0.85rem", color: "var(--fg)" }}>
                  <strong>Distinct ICS protocols:</strong> {data.ot_ics.distinct_ics_protocols ?? 0} ·{" "}
                  <strong>Hits:</strong> {(data.ot_ics.ics_protocol_hits || []).length} ·{" "}
                  <strong>Production continuity (demo):</strong>{" "}
                  {data.ot_ics.production_continuity_score ?? "—"}
                </div>
                {(data.ot_ics.ot_playbooks_triggered || []).length > 0 && (
                  <div style={{ fontSize: "0.85rem", color: "var(--orange)" }}>
                    <strong>OT playbooks:</strong>{" "}
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
                  {data.ot_ics.ics_specialist?.ascii_report || "(no specialist output)"}
                </pre>
                <Link
                  to="/ot-dashboard"
                  style={{ color: "var(--cyan)", fontWeight: 600, fontSize: "0.9rem", textDecoration: "none" }}
                >
                  فتح لوحة OT/ICS الكاملة →
                </Link>
              </>
            )}
          </div>
        )}

        {tab === "council" && (
          <div style={{ fontSize: "0.88rem", color: "var(--muted)", lineHeight: 1.55 }}>
            {!data?.council && (
              <p style={{ margin: 0 }}>
                فعّل خيار «مجلس الوكلاء» قبل المسح، أو راجع{" "}
                <code style={{ color: "var(--cyan)" }}>GET /api/health/ollama</code> للتأكد أن Ollama يعمل والنموذج
                مثبت.
              </p>
            )}
            {data?.council && !data.council.ok && (
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
            )}
            {data?.council?.ok && data.council.report && (
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
                {data.council.report}
              </pre>
            )}
            {data?.council?.ok && !data.council.report && (
              <p style={{ margin: "0.5rem 0 0" }}>اكتمل المجلس لكن لا يوجد نص في الاستجابة.</p>
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
