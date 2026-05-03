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
          <div style={{ display: "flex", flexDirection: "column", gap: "0.08rem" }}>
            <span className="coa-brand coa-brand--compact">C.O.A</span>
            <span className="coa-brand__sub">{t("landing.brandSub")}</span>
          </div>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main page-main--marketing">
        <div className="landing-hero">
          <div className="landing-hero__brand" style={{ marginBottom: "0.5rem" }}>
            <div className="coa-brand">C.O.A</div>
            <div className="coa-brand__sub">{t("landing.brandSub")}</div>
          </div>
          <p className="coa-tagline">{t("landing.tagline")}</p>
          <h1 className="landing-hero__title">{t("landing.hero")}</h1>
          <p className="landing-hero__lead">{t("landing.p1")}</p>
          <div className="landing-cta-row">
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
        </div>

        <div className="feature-card-grid">
          {FEATURE_CARD_KEYS.map((c) => (
            <Link key={c.to} to={c.to} className="feature-card">
              <div className="feature-card__title">{t(c.titleKey)}</div>
              <div className="feature-card__desc">{t(c.descKey)}</div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
