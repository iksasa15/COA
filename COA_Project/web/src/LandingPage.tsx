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
    desc: "إسناد فرضي، ملفات APT، playbooks، موقف دفاعي، وبيانات heatmap خام — بعد فحص واحد.",
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

export default function LandingPage() {
  return (
    <div
      style={{
        minHeight: "100%",
        display: "flex",
        flexDirection: "column",
        background:
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(56, 189, 248, 0.18), transparent), var(--bg)",
      }}
    >
      <header
        style={{
          padding: "1rem 1.5rem",
          borderBottom: "1px solid var(--bg3)",
          display: "flex",
          flexDirection: "column",
          alignItems: "stretch",
          gap: "0.25rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--cyan)" }}>C.O.A</span>
          <span style={{ color: "var(--muted)", fontSize: "0.88rem" }}>Council of Agents</span>
        </div>
        <FeatureNav />
      </header>

      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "1.5rem 1.5rem 2rem",
          textAlign: "center",
        }}
      >
        <div style={{ maxWidth: "42rem", width: "100%" }}>
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
            ابدأ بـ <strong>فحص واحد</strong> من لوحة الأداء، ثم افتح أي صفحة أدناه لاختبار ميزة منفردة (كل صفحة تقرأ آخر
            فحص من المتصفح).
          </p>
          <p style={{ margin: "0 0 1.25rem", color: "var(--bg3)", fontSize: "0.82rem" }}>
            التوثيق: <code style={{ color: "var(--cyan)" }}>docs/React_Additions_AR.md</code>
          </p>
          <Link
            to="/dashboard"
            className="btn-primary landing-cta"
            style={{
              display: "inline-block",
              textDecoration: "none",
              padding: "0.75rem 1.5rem",
              fontSize: "1rem",
              marginBottom: "1.75rem",
            }}
          >
            تشغيل الفحص أولاً ← لوحة الأداء
          </Link>

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

      <footer
        style={{
          padding: "0.75rem 1.5rem",
          borderTop: "1px solid var(--bg3)",
          fontSize: "0.8rem",
          color: "var(--muted)",
          textAlign: "center",
        }}
      >
        شغّل الخادم: <code style={{ color: "var(--cyan)" }}>python web_api.py</code> و Vite:{" "}
        <code style={{ color: "var(--cyan)" }}>npm run dev</code> — التفاصيل في docs/React_Additions_AR.md
      </footer>
    </div>
  );
}
