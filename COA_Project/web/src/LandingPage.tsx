import { Link } from "react-router-dom";

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
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <span style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--cyan)" }}>C.O.A</span>
        <span style={{ color: "var(--muted)", fontSize: "0.88rem" }}>Council of Agents</span>
      </header>

      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "2rem 1.5rem",
          textAlign: "center",
        }}
      >
        <div style={{ maxWidth: "32rem" }}>
          <h1
            style={{
              margin: "0 0 0.5rem",
              fontSize: "clamp(2rem, 5vw, 2.75rem)",
              fontWeight: 700,
              color: "var(--fg)",
              letterSpacing: "-0.02em",
            }}
          >
            مرحباً بك في C.O.A
          </h1>
          <p style={{ margin: "0 0 0.35rem", color: "var(--muted)", fontSize: "1.05rem", lineHeight: 1.55 }}>
            منصة مجلس الوكلاء لفحص النظام والتهديدات محلياً. ابدأ من الصفحة الرئيسية، ثم انتقل إلى لوحة
            الأداء لتشغيل الفحص وعرض النتائج والتقارير.
          </p>
          <p style={{ margin: "0 0 2rem", color: "var(--bg3)", fontSize: "0.85rem" }}>
            Welcome — use the dashboard to run scans (API on port 5050).
          </p>
          <Link
            to="/dashboard"
            className="btn-primary landing-cta"
            style={{
              display: "inline-block",
              textDecoration: "none",
              padding: "0.85rem 1.75rem",
              fontSize: "1.05rem",
            }}
          >
            الانتقال إلى صفحة الأداء
          </Link>
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
        شغّل الخادم: <code style={{ color: "var(--cyan)" }}>python web_api.py</code> ثم من لوحة الأداء اضغط Start scan
      </footer>
    </div>
  );
}
