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
    <nav className="feature-nav" aria-label={t("nav.aria")}>
      <span className="feature-nav__prefix">{t("nav.testPrefix")}</span>
      {LINK_KEYS.map(({ to, key }) => {
        const active = to === "/" ? pathname === "/" : pathname === to || pathname.startsWith(`${to}/`);
        return (
          <Link key={to} to={to} className={`feature-nav__link${active ? " feature-nav__link--active" : ""}`}>
            {t(key)}
          </Link>
        );
      })}
      <span className="feature-nav__lang">
        <span className="feature-nav__lang-label">{t("nav.langLabel")}</span>
        <button
          type="button"
          className={`feature-nav__lang-btn${locale === "ar" ? " feature-nav__lang-btn--on" : ""}`}
          onClick={() => setLocale("ar")}
          aria-pressed={locale === "ar"}
        >
          {t("nav.langAr")}
        </button>
        <button
          type="button"
          className={`feature-nav__lang-btn${locale === "en" ? " feature-nav__lang-btn--on" : ""}`}
          onClick={() => setLocale("en")}
          aria-pressed={locale === "en"}
        >
          {t("nav.langEn")}
        </button>
      </span>
    </nav>
  );
}
