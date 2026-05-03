import { Link, useLocation } from "react-router-dom";
import DefensethonLogo from "./DefensethonLogo";

const LINKS = [
  { to: "/", label: "الرئيسية" },
  { to: "/dashboard", label: "فحص / لوحة" },
  { to: "/defense-context", label: "سياق دفاعي (#5)" },
  { to: "/mitre-deep", label: "MITRE عميق" },
  { to: "/mitre-heatmap", label: "خريطة MITRE" },
  { to: "/ot-dashboard", label: "OT/ICS (#6)" },
  { to: "/dev-tests", label: "pytest" },
  { to: "/cli-commands", label: "أوامر التشغيل" },
] as const;

export default function FeatureNav() {
  const { pathname } = useLocation();
  return (
    <nav
      className="feature-nav"
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: "0.35rem 0.65rem",
        padding: "0.35rem 0 0",
      }}
      aria-label="تنقل ميزات الاختبار"
    >
      <DefensethonLogo height={30} />
      <span
        style={{
          width: "1px",
          height: "1.25rem",
          background: "var(--surface-border)",
          flexShrink: 0,
        }}
        aria-hidden
      />
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
              background: active ? "var(--nav-active-bg)" : "transparent",
            }}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
