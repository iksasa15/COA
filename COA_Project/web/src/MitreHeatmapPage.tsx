import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

type HeatCell = {
  technique_id: string;
  name: string;
  tactic: string;
  heat: number;
};

const HEAT_COLORS: Record<number, string> = {
  0: "#334155",
  1: "#ca8a04",
  2: "#ea580c",
  3: "#991b1b",
};

const HEAT_LABELS: Record<number, string> = {
  0: "لم يُرصد",
  1: "إقليمي / ملف تعريف APT",
  2: "شوهد في هذا الفحص",
  3: "شوهد + تطابق ملف تعريف",
};

export default function MitreHeatmapPage() {
  const [cells, setCells] = useState<HeatCell[]>([]);
  const [disclaimer, setDisclaimer] = useState<string | null>(null);
  const [attribution, setAttribution] = useState<string>("");

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("coa_defense_context");
      if (!raw) {
        setDisclaimer("لا توجد بيانات. نفّذ فحصاً من لوحة الأداء أولاً.");
        return;
      }
      const dc = JSON.parse(raw) as {
        mitre_heatmap?: HeatCell[];
        disclaimer?: string;
        attribution?: { likely_actor?: string; confidence_percent?: number };
      };
      setCells(dc.mitre_heatmap || []);
      setDisclaimer(dc.disclaimer || null);
      const a = dc.attribution;
      if (a) {
        setAttribution(`${a.likely_actor ?? ""} (${a.confidence_percent ?? 0}% confidence)`);
      }
    } catch {
      setDisclaimer("تعذّر قراءة بيانات السياق الدفاعي.");
    }
  }, []);

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          padding: "1rem 1.5rem",
          borderBottom: "1px solid var(--bg3)",
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          flexWrap: "wrap",
        }}
      >
        <Link
          to="/dashboard"
          style={{ color: "var(--cyan)", textDecoration: "none", fontWeight: 600, fontSize: "0.9rem" }}
        >
          ← لوحة الأداء
        </Link>
        <h1 style={{ margin: 0, fontSize: "1.35rem", color: "var(--fg)" }}>خريطة MITRE ATT&CK الحرارية</h1>
        <Link to="/" style={{ marginLeft: "auto", color: "var(--muted)", fontSize: "0.88rem" }}>
          الرئيسية
        </Link>
      </header>

      <div style={{ padding: "1rem 1.5rem", flex: 1 }}>
        {attribution && (
          <p style={{ color: "var(--muted)", marginTop: 0 }}>
            <strong style={{ color: "var(--fg)" }}>الإسناد (فرضي):</strong> {attribution}
          </p>
        )}
        {disclaimer && (
          <p style={{ color: "var(--yellow)", fontSize: "0.9rem", maxWidth: "48rem" }}>{disclaimer}</p>
        )}

        <p style={{ color: "var(--muted)", fontSize: "0.85rem", maxWidth: "52rem" }}>
          الألوان: أحمر داكن = تطابق قوي مع تكتيكات ملفات APT المحمّلة + مؤشرات الفحص؛ برتقالي = شوهد في
          الفحص؛ أصفر = تأكيد إقليمي من الملفات فقط؛ رمادي = لا خلية لهذا الفحص.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: "0.65rem",
            marginTop: "1rem",
          }}
        >
          {cells.length === 0 && !disclaimer?.includes("نفّذ") && (
            <span style={{ color: "var(--muted)" }}>لا توجد تقنيات مسجّلة لهذا الفحص.</span>
          )}
          {cells.map((c) => (
            <div
              key={c.technique_id}
              title={`${c.tactic} — ${HEAT_LABELS[c.heat] ?? ""}`}
              style={{
                borderRadius: "var(--radius)",
                padding: "0.75rem",
                background: HEAT_COLORS[c.heat] ?? HEAT_COLORS[0],
                color: "#f8fafc",
                border: "1px solid #1e293b",
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
      </div>
    </div>
  );
}
