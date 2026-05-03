import { useLocation } from "react-router-dom";
import { useCallback, useEffect, useMemo, useState } from "react";
import FeatureNav from "./FeatureNav";

type HeatCell = {
  technique_id: string;
  name: string;
  tactic: string;
  heat: number;
};

type ProfileRank = {
  profile_id?: string;
  display_name?: string;
  similarity?: number;
  ttps?: string[];
};

type MitreDeepExtras = {
  navigator_layer?: Record<string, unknown>;
  detection_gap_hints?: string[];
  ics_context?: { ics_relevant?: boolean; note?: string };
};

const HEAT_COLORS: Record<number, string> = {
  0: "var(--heat-0)",
  1: "var(--heat-1)",
  2: "var(--heat-2)",
  3: "var(--heat-3)",
};

const HEAT_LABELS: Record<number, string> = {
  0: "لم يُرصد",
  1: "إقليمي / ملف تعريف APT",
  2: "شوهد في هذا الفحص",
  3: "شوهد + تطابق ملف تعريف",
};

type ViewFilter = "all" | "apt_top" | "gaps_only";

export default function MitreHeatmapPage() {
  const [cells, setCells] = useState<HeatCell[]>([]);
  const [disclaimer, setDisclaimer] = useState<string | null>(null);
  const [attribution, setAttribution] = useState<string>("");
  const [profiles, setProfiles] = useState<ProfileRank[]>([]);
  const [mitreDeep, setMitreDeep] = useState<MitreDeepExtras | null>(null);
  const [viewFilter, setViewFilter] = useState<ViewFilter>("all");
  const location = useLocation();

  type DcShape = {
    mitre_heatmap?: HeatCell[];
    disclaimer?: string;
    attribution?: { likely_actor?: string; confidence_percent?: number };
    profiles_ranked?: ProfileRank[];
  };

  const refresh = useCallback(() => {
    try {
      const extrasRaw = sessionStorage.getItem("coa_last_scan_extras");
      let dc: DcShape | null = null;
      let mitreFromExtras: MitreDeepExtras | null = null;

      if (extrasRaw) {
        const x = JSON.parse(extrasRaw) as {
          defense_context?: DcShape | null;
          mitre_deep?: MitreDeepExtras | null;
        };
        dc = x.defense_context ?? null;
        mitreFromExtras = x.mitre_deep ?? null;
        setMitreDeep(mitreFromExtras);
      } else {
        setMitreDeep(null);
      }

      if (!dc) {
        const raw = sessionStorage.getItem("coa_defense_context");
        if (raw) {
          dc = JSON.parse(raw) as DcShape;
        }
      }

      if (!dc) {
        setCells([]);
        setProfiles([]);
        setAttribution("");
        setDisclaimer(
          extrasRaw
            ? "لا يوجد defense_context في آخر فحص. نفّذ فحصاً من لوحة الأداء أو راجع استجابة الـ API."
            : "لا توجد بيانات. نفّذ فحصاً من لوحة الأداء أولاً.",
        );
        return;
      }

      setCells(dc.mitre_heatmap || []);
      setDisclaimer(dc.disclaimer || null);
      setProfiles(dc.profiles_ranked || []);
      const a = dc.attribution;
      if (a) {
        setAttribution(`${a.likely_actor ?? ""} (${a.confidence_percent ?? 0}% confidence)`);
      } else {
        setAttribution("");
      }
    } catch {
      setDisclaimer("تعذّر قراءة بيانات السياق الدفاعي.");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [location.key, refresh]);

  useEffect(() => {
    const onScan = () => refresh();
    const onStorage = (e: StorageEvent) => {
      if (e.key === "coa_last_scan_extras" || e.key === "coa_defense_context") refresh();
    };
    window.addEventListener("coa-scan-complete", onScan);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener("coa-scan-complete", onScan);
      window.removeEventListener("storage", onStorage);
    };
  }, [refresh]);

  const topAptTtps = useMemo(() => {
    const p = profiles[0];
    if (!p?.ttps?.length) return new Set<string>();
    return new Set(p.ttps.map((t) => String(t).trim()));
  }, [profiles]);

  const displayCells = useMemo(() => {
    if (viewFilter === "apt_top" && topAptTtps.size > 0) {
      return cells.filter((c) => topAptTtps.has(c.technique_id));
    }
    if (viewFilter === "gaps_only") {
      return [];
    }
    return cells;
  }, [cells, viewFilter, topAptTtps]);

  function downloadNavigatorLayer() {
    const layer = mitreDeep?.navigator_layer;
    if (!layer) return;
    const blob = new Blob([JSON.stringify(layer, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "coa_mitre_navigator_layer.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="page-shell">
      <header className="page-header">
        <div className="page-header__row">
          <h1 className="page-title page-title--fg">MITRE ATT&CK Coverage — تغطية وخريطة حرارية</h1>
        </div>
        <FeatureNav />
      </header>

      <main className="page-main">
        {attribution && (
          <p style={{ color: "var(--muted)" }}>
            <strong style={{ color: "var(--fg)" }}>الإسناد الاسترشادي:</strong> {attribution}
          </p>
        )}
        {disclaimer && (
          <p style={{ color: "var(--yellow)", fontSize: "0.9rem", maxWidth: "48rem" }}>{disclaimer}</p>
        )}

        {mitreDeep?.ics_context?.ics_relevant && (
          <div
            style={{
              padding: "0.75rem 1rem",
              background: "var(--warn-banner-bg)",
              borderRadius: "var(--radius)",
              border: "1px solid var(--warn-banner-border)",
              color: "var(--warn-banner-fg)",
              fontSize: "0.88rem",
              maxWidth: "56rem",
              marginBottom: "0.75rem",
            }}
          >
            <strong>ICS / OT:</strong> {mitreDeep.ics_context.note}
          </div>
        )}

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "0.5rem",
            alignItems: "center",
            marginBottom: "0.75rem",
          }}
        >
          <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>فلتر العرض:</span>
          {(["all", "apt_top", "gaps_only"] as const).map((k) => (
            <button
              key={k}
              type="button"
              className={viewFilter === k ? "btn-primary" : "btn-ghost"}
              style={{ padding: "0.4rem 0.75rem", fontSize: "0.82rem" }}
              onClick={() => setViewFilter(k)}
            >
              {k === "all" ? "الكل" : k === "apt_top" ? "تقنيات أعلى APT (ملف YAML)" : "فجوات كشف (نص)"}
            </button>
          ))}
          <button
            type="button"
            className="btn-accent ms-auto"
            style={{ fontSize: "0.82rem" }}
            disabled={!mitreDeep?.navigator_layer}
            onClick={downloadNavigatorLayer}
          >
            تصدير Navigator JSON
          </button>
        </div>

        {viewFilter === "gaps_only" ? (
          <ul style={{ color: "var(--fg)", maxWidth: "48rem" }}>
            {(mitreDeep?.detection_gap_hints?.length ? mitreDeep.detection_gap_hints : ["لا توجد تلميحات فجوات بعد الفحص الأخير."]).map(
              (g, i) => (
                <li key={i} style={{ marginBottom: "0.35rem" }}>
                  {g}
                </li>
              ),
            )}
          </ul>
        ) : (
          <>
            <p style={{ color: "var(--muted)", fontSize: "0.85rem", maxWidth: "52rem" }}>
              الألوان: أحمر داكن = تطابق قوي؛ برتقالي = شوهد في الفحص؛ أصفر = إقليمي من الملفات؛ رمادي = لا
              خلية.
            </p>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                gap: "0.65rem",
                marginTop: "0.5rem",
              }}
            >
              {displayCells.length === 0 && !disclaimer?.includes("نفّذ") && (
                <span style={{ color: "var(--muted)" }}>
                  {viewFilter === "apt_top"
                    ? "لا تقاطع بين تقنيات الفحص وأعلى ملف APT — جرّب «الكل»."
                    : "لا توجد تقنيات مسجّلة لهذا الفحص."}
                </span>
              )}
              {displayCells.map((c) => (
                <div
                  key={c.technique_id}
                  title={`${c.tactic} — ${HEAT_LABELS[c.heat] ?? ""}`}
                  style={{
                    borderRadius: "var(--radius)",
                    padding: "0.75rem",
                    background: HEAT_COLORS[c.heat] ?? HEAT_COLORS[0],
                    color: "var(--heat-cell-text)",
                    border: "1px solid var(--heat-cell-border)",
                    minHeight: "5.5rem",
                  }}
                >
                  <div style={{ fontFamily: "var(--mono)", fontSize: "0.78rem", opacity: 0.95 }}>
                    {c.technique_id}
                  </div>
                  <div style={{ fontWeight: 600, fontSize: "0.88rem", marginTop: "0.25rem" }}>{c.name}</div>
                  <div style={{ fontSize: "0.75rem", opacity: 0.88, marginTop: "0.35rem" }}>{c.tactic}</div>
                  <div style={{ fontSize: "0.72rem", marginTop: "0.35rem", opacity: 0.85 }}>
                    Heat: {c.heat} — {HEAT_LABELS[c.heat] ?? ""}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
