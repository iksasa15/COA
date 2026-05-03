import { Link } from "react-router-dom";
import FeatureNav from "./FeatureNav";
import { useI18n } from "./i18n";

const FEATURE_CARD_KEYS = [
  { to: "/dashboard", titleKey: "landing.card.dash.title" as const, descKey: "landing.card.dash.desc" as const },
  { to: "/defense-context", titleKey: "landing.card.dc.title" as const, descKey: "landing.card.dc.desc" as const },
  { to: "/mitre-deep", titleKey: "landing.card.md.title" as const, descKey: "landing.card.md.desc" as const },
  { to: "/mitre-heatmap", titleKey: "landing.card.mh.title" as const, descKey: "landing.card.mh.desc" as const },
  { to: "/ot-dashboard", titleKey: "landing.card.ot.title" as const, descKey: "landing.card.ot.desc" as const },
];

export default function LandingPage() {
  const { t } = useI18n();
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
            {t("landing.hero")}
          </h1>
          <p style={{ margin: "0 0 1.25rem", color: "var(--muted)", fontSize: "1rem", lineHeight: 1.55 }}>
            {t("landing.p1")}
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
              {t("landing.cta")}
            </Link>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
              gap: "0.75rem",
              textAlign: "right",
            }}
          >
            {FEATURE_CARD_KEYS.map((c) => (
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
                  {t(c.titleKey)}
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--muted)", lineHeight: 1.45 }}>{t(c.descKey)}</div>
              </Link>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
