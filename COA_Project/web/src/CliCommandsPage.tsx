import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import FeatureNav from "./FeatureNav";

const PROJECT_ROOT = "/Users/ahmed/Desktop/COA/COA_Project";

const BLOCK_ACTIVATE = `cd ${PROJECT_ROOT}
source venv/bin/activate`;

const BLOCK_CLI_LINES = [
  { action: "main" as const, line: "python main.py" },
  { action: "main_council" as const, line: "python main.py --council" },
  { action: "main_vt" as const, line: "python main.py --vt" },
  { action: "main_yara" as const, line: "python main.py --yara" },
  { action: "main_dry_run" as const, line: "python main.py --dry-run" },
  {
    action: "main_reports" as const,
    line: "python main.py --html --json --markdown --csv",
  },
  { action: "main_all" as const, line: "python main.py --all" },
];

const BLOCK_COUNCIL_TEST = `python -m agents.council`;

const BLOCK_WEB = `python main.py --gui`;

const BLOCK_WEB_ALT = `python web_api.py`;

const BLOCK_WEB_NPM = `cd ${PROJECT_ROOT}/web
npm install
npm run dev`;

const BLOCK_OTHER = `python gui.py
python helpdesk_api.py
python main.py --helpdesk`;

const FULL_SCRIPT = `${BLOCK_ACTIVATE}

# فحص CLI
${BLOCK_CLI_LINES.map((x) => x.line).join("\n")}

# اختبار Ollama + المجلس فقط
${BLOCK_COUNCIL_TEST}

# واجهة الويب (API + React)
${BLOCK_WEB}
# أو:
${BLOCK_WEB_ALT}
# ثم في طرفية أخرى:
${BLOCK_WEB_NPM}

# أخرى
${BLOCK_OTHER}`;

type RunCliResponse = {
  ok?: boolean;
  enabled?: boolean;
  error?: string;
  background?: boolean;
  action?: string;
  pid?: number;
  log?: string;
  command?: string[];
  exit_code?: number;
  output?: string;
};

function CodeBlock({
  title,
  lines,
  id,
}: {
  title: string;
  lines: string;
  id: string;
}) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(lines);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, [lines]);

  return (
    <section style={{ marginBottom: "1.35rem" }} aria-labelledby={`h-${id}`}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem", flexWrap: "wrap" }}>
        <h2 id={`h-${id}`} style={{ margin: 0, fontSize: "1rem", color: "var(--cyan)" }}>
          {title}
        </h2>
        <button type="button" className="btn-primary" style={{ fontSize: "0.82rem", padding: "0.35rem 0.75rem" }} onClick={() => void copy()}>
          {copied ? "تم النسخ" : "نسخ الأوامر"}
        </button>
      </div>
      <pre
        style={{
          marginTop: "0.5rem",
          padding: "0.85rem 1rem",
          borderRadius: "var(--radius)",
          border: "1px solid var(--bg3)",
          background: "var(--bg1)",
          color: "var(--fg)",
          fontSize: "0.78rem",
          lineHeight: 1.5,
          overflowX: "auto",
          textAlign: "left",
          direction: "ltr",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {lines}
      </pre>
    </section>
  );
}

function RunButton({
  action,
  label,
  enabled,
  busy,
  onRun,
}: {
  action: string;
  label?: string;
  enabled: boolean;
  busy: boolean;
  onRun: (action: string) => Promise<void>;
}) {
  return (
    <button
      type="button"
      className="btn-primary"
      style={{ fontSize: "0.78rem", padding: "0.3rem 0.65rem", minWidth: "4.5rem" }}
      disabled={!enabled || busy}
      title={!enabled ? "فعّل COA_ALLOW_DEV_TESTS=1 على خادم web_api" : undefined}
      onClick={() => void onRun(action)}
    >
      {busy ? "…" : label ?? "تشغيل"}
    </button>
  );
}

export default function CliCommandsPage() {
  const [fullCopied, setFullCopied] = useState(false);
  const [runEnabled, setRunEnabled] = useState<boolean | null>(null);
  const [running, setRunning] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<RunCliResponse | null>(null);

  const refreshRunEnabled = useCallback(async () => {
    try {
      const r = await fetch("/api/dev/cli-run-enabled");
      const j = (await r.json()) as { enabled?: boolean };
      setRunEnabled(Boolean(j.enabled));
    } catch {
      setRunEnabled(false);
    }
  }, []);

  useEffect(() => {
    void refreshRunEnabled();
  }, [refreshRunEnabled]);

  const runCli = useCallback(async (action: string) => {
    setRunning(action);
    setLastResult(null);
    try {
      const r = await fetch("/api/dev/run-cli", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const j = (await r.json()) as RunCliResponse;
      setLastResult({ ...j, ok: r.ok && Boolean(j.ok) });
    } catch (e) {
      setLastResult({ ok: false, error: e instanceof Error ? e.message : String(e) });
    } finally {
      setRunning(null);
      void refreshRunEnabled();
    }
  }, [refreshRunEnabled]);

  const copyFull = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(FULL_SCRIPT);
      setFullCopied(true);
      window.setTimeout(() => setFullCopied(false), 2000);
    } catch {
      setFullCopied(false);
    }
  }, []);

  const runOk = runEnabled === true;

  return (
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__stack">
          <h1 className="page-title page-title--green">أوامر التشغيل (CLI)</h1>
          <p className="page-subtitle">
            نسخ للصق يدوياً، أو — عند التفعيل — أزرار <strong>تشغيل</strong> تنفّذ على الجهاز الذي يشغّل{" "}
            <code style={{ color: "var(--cyan)" }}>web_api.py</code>.
          </p>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main">
        <p style={{ margin: "0 0 1rem", fontSize: "0.88rem", color: "var(--muted)" }}>
          <Link to="/" style={{ color: "var(--cyan)" }}>
            ← الرئيسية
          </Link>
        </p>

        <div
          style={{
            marginBottom: "1rem",
            padding: "0.65rem 0.85rem",
            borderRadius: "var(--radius)",
            border: "1px solid var(--bg3)",
            background: "var(--bg2)",
            fontSize: "0.84rem",
            color: "var(--muted)",
          }}
        >
          حالة أزرار التشغيل:{" "}
          {runEnabled === null ? (
            "…"
          ) : runOk ? (
            <strong style={{ color: "var(--green)" }}>مفعّلة</strong>
          ) : (
            <strong style={{ color: "var(--orange)" }}>معطّلة — شغّل الخادم بـ COA_ALLOW_DEV_TESTS=1</strong>
          )}
          <div style={{ marginTop: "0.35rem", fontSize: "0.78rem" }}>
            الأوامر الطويلة تُشغَّل في الخلفية؛ راجع ملف السجل في <code style={{ color: "var(--cyan)" }}>reports/ui_cli_*.log</code>. لا يُشغَّل{" "}
            <code>web_api.py</code> أو <code>main.py --gui</code> من هنا لتعارض المنفذ مع الخادم الحالي.
          </div>
        </div>

        <div style={{ marginBottom: "1.25rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          <button type="button" className="btn-primary" style={{ fontSize: "0.9rem" }} onClick={() => void copyFull()}>
            {fullCopied ? "تم النسخ" : "نسخ كل أوامر التشغيل (دفعة واحدة)"}
          </button>
        </div>

        <CodeBlock id="activate" title="تهيئة الطرفية" lines={BLOCK_ACTIVATE} />

        <section style={{ marginBottom: "1.35rem" }}>
          <h2 style={{ margin: "0 0 0.5rem", fontSize: "1rem", color: "var(--cyan)" }}>فحص CLI</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {BLOCK_CLI_LINES.map(({ action, line }) => (
              <div
                key={action}
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  alignItems: "center",
                  gap: "0.5rem",
                  padding: "0.45rem 0.65rem",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--bg3)",
                  background: "var(--bg1)",
                }}
              >
                <code style={{ flex: "1 1 200px", fontSize: "0.78rem", textAlign: "left", direction: "ltr" }}>{line}</code>
                <button
                  type="button"
                  style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem", borderRadius: "6px", border: "1px solid var(--bg3)", background: "var(--bg2)", color: "var(--fg)" }}
                  onClick={() => void navigator.clipboard.writeText(line)}
                >
                  نسخ
                </button>
                <RunButton action={action} enabled={runOk} busy={running === action} onRun={runCli} />
              </div>
            ))}
          </div>
        </section>

        <section style={{ marginBottom: "1.35rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem", flexWrap: "wrap" }}>
            <h2 style={{ margin: 0, fontSize: "1rem", color: "var(--cyan)" }}>اختبار Ollama + المجلس فقط</h2>
            <div style={{ display: "flex", gap: "0.35rem" }}>
              <button
                type="button"
                style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem", borderRadius: "6px", border: "1px solid var(--bg3)", background: "var(--bg2)", color: "var(--fg)" }}
                onClick={() => void navigator.clipboard.writeText(BLOCK_COUNCIL_TEST)}
              >
                نسخ
              </button>
              <RunButton action="council_test" enabled={runOk} busy={running === "council_test"} onRun={runCli} />
            </div>
          </div>
          <pre
            style={{
              marginTop: "0.5rem",
              padding: "0.65rem 0.85rem",
              borderRadius: "var(--radius)",
              border: "1px solid var(--bg3)",
              background: "var(--bg1)",
              fontSize: "0.78rem",
              direction: "ltr",
              textAlign: "left",
            }}
          >
            {BLOCK_COUNCIL_TEST}
          </pre>
          <p style={{ margin: "0.35rem 0 0", fontSize: "0.75rem", color: "var(--muted)" }}>
            هذا الأمر متزامن: قد ينتظر حتى ~5 دقائق ثم يعرض المخرجات أدناه.
          </p>
        </section>

        <CodeBlock id="web1" title="واجهة الويب — تشغيل API (خيار 1)" lines={BLOCK_WEB} />
        <CodeBlock id="web2" title="واجهة الويب — تشغيل API (خيار 2)" lines={BLOCK_WEB_ALT} />

        <section style={{ marginBottom: "1.35rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.5rem", flexWrap: "wrap" }}>
            <h2 style={{ margin: 0, fontSize: "1rem", color: "var(--cyan)" }}>واجهة الويب — Vite (npm run dev)</h2>
            <RunButton action="npm_run_dev" label="تشغيل Vite" enabled={runOk} busy={running === "npm_run_dev"} onRun={runCli} />
          </div>
          <pre
            style={{
              marginTop: "0.5rem",
              padding: "0.85rem 1rem",
              borderRadius: "var(--radius)",
              border: "1px solid var(--bg3)",
              background: "var(--bg1)",
              fontSize: "0.78rem",
              direction: "ltr",
              textAlign: "left",
              whiteSpace: "pre-wrap",
            }}
          >
            {BLOCK_WEB_NPM}
          </pre>
        </section>

        <section style={{ marginBottom: "1.35rem" }}>
          <h2 style={{ margin: "0 0 0.5rem", fontSize: "1rem", color: "var(--cyan)" }}>أخرى</h2>
          {[
            { line: "python gui.py", action: "gui" as const },
            { line: "python helpdesk_api.py", action: "helpdesk_api" as const },
            { line: "python main.py --helpdesk", action: "helpdesk_main" as const },
          ].map(({ line, action }) => (
            <div
              key={action}
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                gap: "0.5rem",
                marginBottom: "0.4rem",
                padding: "0.45rem 0.65rem",
                borderRadius: "var(--radius)",
                border: "1px solid var(--bg3)",
                background: "var(--bg1)",
              }}
            >
              <code style={{ flex: "1 1 200px", fontSize: "0.78rem", textAlign: "left", direction: "ltr" }}>{line}</code>
              <button
                type="button"
                style={{ fontSize: "0.75rem", padding: "0.25rem 0.5rem", borderRadius: "6px", border: "1px solid var(--bg3)", background: "var(--bg2)", color: "var(--fg)" }}
                onClick={() => void navigator.clipboard.writeText(line)}
              >
                نسخ
              </button>
              <RunButton action={action} enabled={runOk} busy={running === action} onRun={runCli} />
            </div>
          ))}
        </section>

        {lastResult && (
          <section
            style={{
              marginTop: "0.5rem",
              padding: "0.85rem",
              borderRadius: "var(--radius)",
              border: `1px solid ${lastResult.ok ? "var(--green)" : "var(--orange)"}`,
              background: "var(--bg2)",
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: "0.35rem", color: lastResult.ok ? "var(--green)" : "var(--orange)" }}>
              {lastResult.ok ? "نتيجة التشغيل" : "فشل أو خطأ"}
            </div>
            {lastResult.error && (
              <pre style={{ fontSize: "0.78rem", color: "var(--fg)", whiteSpace: "pre-wrap", direction: "ltr", textAlign: "left" }}>{lastResult.error}</pre>
            )}
            {lastResult.background && lastResult.log && (
              <p style={{ fontSize: "0.82rem", color: "var(--muted)", margin: "0.25rem 0" }}>
                PID: {lastResult.pid} — السجل: <code style={{ color: "var(--cyan)" }}>{lastResult.log}</code>
              </p>
            )}
            {lastResult.output != null && lastResult.output !== "" && (
              <pre
                style={{
                  maxHeight: "280px",
                  overflow: "auto",
                  fontSize: "0.72rem",
                  padding: "0.5rem",
                  background: "var(--bg1)",
                  borderRadius: "6px",
                  direction: "ltr",
                  textAlign: "left",
                  whiteSpace: "pre-wrap",
                }}
              >
                {lastResult.output}
              </pre>
            )}
            {lastResult.exit_code != null && lastResult.background !== true && (
              <p style={{ fontSize: "0.8rem", color: "var(--muted)" }}>exit code: {lastResult.exit_code}</p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
