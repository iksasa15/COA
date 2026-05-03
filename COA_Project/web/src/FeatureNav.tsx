import { Link, useLocation } from "react-router-dom";
import { useI18n } from "./i18n";

const LINK_KEYS = [
  { to: "/", key: "nav.home" as const },
  { to: "/dashboard", key: "nav.dashboard" as const },
  { to: "/defense-context", key: "nav.defenseContext" as const },
  { to: "/mitre-deep", key: "nav.mitreDeep" as const },
  { to: "/mitre-heatmap", key: "nav.mitreHeatmap" as const },
  { to: "/ot-dashboard", key: "nav.otIcs" as const },
];

export default function FeatureNav() {
  const { pathname } = useLocation();
  const { locale, setLocale, t } = useI18n();

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
      aria-label={t("nav.aria")}
    >
      <span style={{ fontSize: "0.72rem", color: "var(--muted)", marginInlineEnd: "0.25rem" }}>
        {t("nav.testPrefix")}
      </span>
      {LINK_KEYS.map(({ to, key }) => {
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
            {t(key)}
          </Link>
        );
      })}
      <span
        className="feature-nav__lang"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.2rem",
          marginInlineStart: "auto",
          flexWrap: "wrap",
        }}
      >
        <span style={{ fontSize: "0.68rem", color: "var(--muted)" }}>{t("nav.langLabel")}</span>
        <button
          type="button"
          className={locale === "ar" ? "btn-primary" : "btn-ghost"}
          style={{ padding: "0.15rem 0.45rem", fontSize: "0.72rem" }}
          onClick={() => setLocale("ar")}
          aria-pressed={locale === "ar"}
        >
          {t("nav.langAr")}
        </button>
        <button
          type="button"
          className={locale === "en" ? "btn-primary" : "btn-ghost"}
          style={{ padding: "0.15rem 0.45rem", fontSize: "0.72rem" }}
          onClick={() => setLocale("en")}
          aria-pressed={locale === "en"}
        >
          {t("nav.langEn")}
        </button>
      </span>
    </nav>
  );
}
