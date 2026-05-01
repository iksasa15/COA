import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";

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
};

type TabId = "threats" | "processes" | "network" | "ot_ics" | "logs";

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
  const [loading, setLoading] = useState(false);
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
        body: JSON.stringify({ dry_run: dryRun }),
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
  }, [dryRun]);

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

  const linkHome = {
    marginLeft: "auto",
    color: "var(--cyan)",
    fontSize: "0.9rem",
    textDecoration: "none",
    fontWeight: 600,
  } as const;

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          padding: "1.25rem 1.5rem",
          borderBottom: "1px solid var(--bg3)",
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          flexWrap: "wrap",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "1.75rem", color: "var(--cyan)" }}>C.O.A</h1>
        <span style={{ color: "var(--muted)", fontSize: "0.95rem" }}>
          Council of Agents — لوحة الأداء
        </span>
        <Link
          to="/mitre-heatmap"
          style={{
            color: "var(--purple)",
            fontSize: "0.9rem",
            textDecoration: "none",
            fontWeight: 600,
          }}
        >
          خريطة MITRE الحرارية
        </Link>
        <Link
          to="/ot-dashboard"
          style={{
            color: "#64748b",
            fontSize: "0.9rem",
            textDecoration: "none",
            fontWeight: 600,
          }}
        >
          OT/ICS Dashboard
        </Link>
        <Link to="/" style={linkHome}>
          الرئيسية
        </Link>
      </header>

      <div
        style={{
          padding: "1rem 1.5rem",
          background: "var(--bg2)",
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
          alignItems: "center",
        }}
      >
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
        <div style={{ flex: 1 }} />
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

      <div style={{ padding: "0.75rem 1.5rem" }}>
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
                border: "1px solid #33415560",
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
          style={{
            margin: "0 1.5rem 0.75rem",
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
          style={{
            margin: "0 1.5rem 0.75rem",
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

      <main style={{ flex: 1, padding: "0 1.5rem 1.25rem", display: "flex", flexDirection: "column" }}>
        <div className="tabs">
          {(
            [
              ["threats", "Threats"],
              ["processes", "Processes"],
              ["network", "Network"],
              ["ot_ics", "OT/ICS"],
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

      <footer
        style={{
          padding: "0.6rem 1.5rem",
          background: "var(--bg2)",
          fontSize: "0.82rem",
          color: "var(--muted)",
          borderTop: "1px solid var(--bg3)",
        }}
      >
        {status}
      </footer>
    </div>
  );
}
