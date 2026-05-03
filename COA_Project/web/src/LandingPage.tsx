import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import FeatureNav from "./FeatureNav";

const FEATURE_CARDS = [
  {
    to: "/dashboard",
    title: "فحص / لوحة الأداء",
    desc: "تشغيل الفحص، التهديدات، العمليات، الشبكة، تبويب OT/ICS المختصر، السجلات، وتصدير التقارير.",
  },
  {
    to: "/defense-context",
    title: "سياق دفاعي (الوكيل #5)",
    desc: "إسناد استرشادي من فحص الجهاز، ملفات APT، playbooks، موقف دفاعي، وبيانات heatmap خام — بعد فحص واحد.",
  },
  {
    to: "/mitre-deep",
    title: "MITRE عميق",
    desc: "سلسلة القتل، فجوات الكشف، سياق ICS، تقرير ASCII، وتصدير طبقة Navigator من الجلسة.",
  },
  {
    to: "/mitre-heatmap",
    title: "خريطة MITRE الحرارية",
    desc: "شبكة تقنيات ملوّنة وفلترة تقنيات أعلى APT أو فجوات النص.",
  },
  {
    to: "/ot-dashboard",
    title: "OT / ICS (الوكيل #6)",
    desc: "مخزون تقريبي، تنبيهات منافذ صناعية، سيناريوهات OT، تقييم ICS Specialist، أمثلة MITRE ICS.",
  },
] as const;

type SeedPayload = {
  ok?: boolean;
  error?: string;
  defense_context?: unknown;
  mitre_deep?: unknown;
  ot_ics?: unknown;
};

export default function LandingPage() {
  const [seedLoading, setSeedLoading] = useState(false);
  const [seedMsg, setSeedMsg] = useState<string | null>(null);

  const loadDemoSession = useCallback(async () => {
    setSeedLoading(true);
    setSeedMsg(null);
    try {
      const res = await fetch("/api/demo/seed-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const json = (await res.json()) as SeedPayload;
      if (!res.ok || !json.ok) {
        throw new Error(json.error || res.statusText || "فشل التحميل");
      }
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
      setSeedMsg(
        "تم تحميل بيانات تجريبية (تهديدات، سياق دفاعي، MITRE، OT/ICS). افتح لوحة الأداء أو أي صفحة ميزة.",
      );
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setSeedMsg(`تعذر التحميل — تأكد أن الخادم يعمل (python web_api.py). ${msg}`);
    } finally {
      setSeedLoading(false);
    }
  }, []);

  return (
    <div className="page-shell page-shell--hero">
      <header className="page-header">
        <div className="page-header__row">
          <span className="page-title" style={{ fontSize: "1.25rem" }}>
            C.O.A
          </span>
          <span className="page-subtitle" style={{ fontSize: "0.88rem" }}>
            Council of Agents
          </span>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main page-main--marketing">
        <div style={{ width: "100%" }}>
          <h1
            style={{
              margin: "0 0 0.5rem",
              fontSize: "clamp(1.75rem, 4vw, 2.35rem)",
              fontWeight: 700,
              color: "var(--fg)",
              letterSpacing: "-0.02em",
            }}
          >
            مرحباً بك في C.O.A
          </h1>
          <p style={{ margin: "0 0 0.35rem", color: "var(--muted)", fontSize: "1rem", lineHeight: 1.55 }}>
            يمكنك <strong>فحص الجهاز الحقيقي</strong> من لوحة الأداء، أو زر «تحميل بيانات تجريبية» أدناه لملء الواجهات فوراً
            دون فحص. صفحات الدفاع وMITRE وOT تقرأ آخر جلسة من المتصفح.
          </p>
          <p style={{ margin: "0 0 1.25rem", color: "var(--muted)", fontSize: "0.82rem" }}>
            التوثيق: <code style={{ color: "var(--cyan)" }}>docs/React_Additions_AR.md</code>
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.65rem", alignItems: "center", marginBottom: "1.25rem" }}>
            <Link
              to="/dashboard"
              className="btn-primary landing-cta"
              style={{
                display: "inline-block",
                textDecoration: "none",
                padding: "0.75rem 1.5rem",
                fontSize: "1rem",
              }}
            >
              تشغيل الفحص أولاً ← لوحة الأداء
            </Link>
            <button
              type="button"
              className="btn-accent"
              style={{ padding: "0.65rem 1.15rem", fontSize: "0.92rem" }}
              disabled={seedLoading}
              onClick={() => void loadDemoSession()}
            >
              {seedLoading ? "جاري التحميل…" : "تحميل بيانات تجريبية للواجهات"}
            </button>
          </div>

          {seedMsg && (
            <p
              style={{
                margin: "0 0 1rem",
                fontSize: "0.88rem",
                color: seedMsg.startsWith("تم ") ? "var(--green)" : "var(--orange)",
                lineHeight: 1.5,
              }}
            >
              {seedMsg}
            </p>
          )}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
              gap: "0.75rem",
              textAlign: "right",
            }}
          >
            {FEATURE_CARDS.map((c) => (
              <Link
                key={c.to}
                to={c.to}
                style={{
                  display: "block",
                  padding: "1rem",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--bg3)",
                  background: "var(--bg2)",
                  textDecoration: "none",
                  color: "inherit",
                  transition: "border-color 0.15s",
                }}
              >
                <div style={{ fontWeight: 700, color: "var(--cyan)", fontSize: "0.95rem", marginBottom: "0.35rem" }}>
                  {c.title}
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--muted)", lineHeight: 1.45 }}>{c.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      </main>

      <footer className="page-footer page-footer--center">
        شغّل الخادم: <code style={{ color: "var(--cyan)" }}>python web_api.py</code> و Vite:{" "}
        <code style={{ color: "var(--cyan)" }}>npm run dev</code> — التفاصيل في docs/React_Additions_AR.md
      </footer>
    </div>
  );
}
