import { Link, useLocation } from "react-router-dom";

const LINKS = [
  { to: "/", label: "الرئيسية" },
  { to: "/dashboard", label: "فحص / لوحة" },
  { to: "/defense-context", label: "سياق دفاعي (#5)" },
  { to: "/mitre-deep", label: "MITRE عميق" },
  { to: "/mitre-heatmap", label: "خريطة MITRE" },
  { to: "/ot-dashboard", label: "OT/ICS (#6)" },
] as const;

export default function FeatureNav() {
  const { pathname } = useLocation();
  return (
    <nav
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: "0.35rem 0.65rem",
        padding: "0.5rem 0",
        borderBottom: "1px solid var(--bg3)",
        marginBottom: "0.75rem",
      }}
      aria-label="تنقل ميزات الاختبار"
    >
      <span style={{ fontSize: "0.72rem", color: "var(--muted)", marginRight: "0.25rem" }}>اختبار:</span>
      {LINKS.map(({ to, label }) => {
        const active = to === "/" ? pathname === "/" : pathname === to || pathname.startsWith(`${to}/`);
        return (
          <Link
            key={to}
            to={to}
            style={{
              fontSize: "0.78rem",
              fontWeight: active ? 700 : 500,
              textDecoration: "none",
              color: active ? "var(--cyan)" : "var(--muted)",
              padding: "0.2rem 0.45rem",
              borderRadius: "6px",
              border: active ? "1px solid var(--cyan)" : "1px solid transparent",
              background: active ? "rgba(56, 189, 248, 0.08)" : "transparent",
            }}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
