import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import FeatureNav from "./FeatureNav";

type EnabledResponse = { ok?: boolean; enabled?: boolean };
type RunResponse = {
  ok?: boolean;
  enabled?: boolean;
  error?: string;
  exit_code?: number;
  scope?: string;
  command?: string[];
  output?: string;
};

export default function DevTestsPage() {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RunResponse | null>(null);

  const refreshEnabled = useCallback(async () => {
    try {
      const r = await fetch("/api/dev/tests-enabled");
      const j = (await r.json()) as EnabledResponse;
      setEnabled(Boolean(j.enabled));
    } catch {
      setEnabled(false);
    }
  }, []);

  useEffect(() => {
    void refreshEnabled();
  }, [refreshEnabled]);

  const run = async (scope: "all" | "quick") => {
    setLoading(true);
    setResult(null);
    try {
      const r = await fetch("/api/dev/run-tests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scope }),
      });
      const j = (await r.json()) as RunResponse;
      setResult({ ...j, ok: r.ok && Boolean(j.ok) });
    } catch (e) {
      setResult({ ok: false, error: e instanceof Error ? e.message : String(e) });
    } finally {
      setLoading(false);
      void refreshEnabled();
    }
  };

  return (
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__stack">
          <h1 className="page-title page-title--green">تشغيل pytest من الواجهة</h1>
          <p className="page-subtitle">
            للأمان: الميزة معطّلة افتراضياً. شغّل الخادم بـ{" "}
            <code style={{ color: "var(--cyan)" }}>COA_ALLOW_DEV_TESTS=1 python web_api.py</code> ثم اضغط أحد الأزرار.
          </p>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main">
        <div style={{ marginBottom: "1rem", fontSize: "0.9rem", color: "var(--muted)" }}>
          حالة التفعيل:{" "}
          {enabled === null ? (
            "…"
          ) : enabled ? (
            <strong style={{ color: "var(--green)" }}>مفعّل — يمكن التشغيل</strong>
          ) : (
            <strong style={{ color: "var(--orange)" }}>معطّل — عيّن COA_ALLOW_DEV_TESTS=1</strong>
          )}
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
          <button type="button" className="btn-primary" disabled={loading || !enabled} onClick={() => void run("quick")}>
            {loading ? "جاري التشغيل…" : "pytest سريع (ملفات الوحدة الحالية)"}
          </button>
          <button type="button" className="btn-accent" disabled={loading || !enabled} onClick={() => void run("all")}>
            {loading ? "جاري التشغيل…" : "pytest — مجلد tests/ كامل"}
          </button>
          <button type="button" className="btn-ghost" disabled={loading} onClick={() => void refreshEnabled()}>
            تحديث الحالة
          </button>
        </div>

        <p style={{ fontSize: "0.82rem", color: "var(--muted)", marginBottom: "1rem" }}>
          نفس الأمر محلياً:{" "}
          <code style={{ color: "var(--cyan)" }}>cd COA_Project && python -m pytest tests/ -q</code>
        </p>

        {result && (
          <div>
            {result.error && (
              <p style={{ color: "var(--red)", fontSize: "0.9rem", whiteSpace: "pre-wrap" }}>{result.error}</p>
            )}
            {result.exit_code !== undefined && (
              <p style={{ fontSize: "0.88rem", color: result.exit_code === 0 ? "var(--green)" : "var(--orange)" }}>
                exit_code: {result.exit_code}
                {result.scope ? ` · scope: ${result.scope}` : ""}
              </p>
            )}
            {result.command && (
              <pre
                style={{
                  fontSize: "0.72rem",
                  color: "var(--muted)",
                  background: "var(--bg2)",
                  padding: "0.5rem",
                  borderRadius: "var(--radius)",
                  overflow: "auto",
                }}
              >
                {result.command.join(" ")}
              </pre>
            )}
            {result.output && (
              <pre
                style={{
                  marginTop: "0.75rem",
                  padding: "0.85rem 1rem",
                  background: "var(--surface-deep)",
                  color: "var(--pre-fg)",
                  borderRadius: "var(--radius)",
                  fontSize: "0.78rem",
                  whiteSpace: "pre-wrap",
                  maxHeight: "min(65vh, 480px)",
                  overflow: "auto",
                  border: "1px solid var(--bg3)",
                }}
              >
                {result.output}
              </pre>
            )}
          </div>
        )}

        <p style={{ marginTop: "1.5rem", fontSize: "0.82rem", color: "var(--muted)" }}>
          <Link to="/" style={{ color: "var(--cyan)" }}>
            الرئيسية
          </Link>
        </p>
      </main>
    </div>
  );
}
