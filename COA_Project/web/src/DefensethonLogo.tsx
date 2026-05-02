/** شعار Defensethon — نسخة محلية من https://defensethon.tuwaiq.edu.sa/images/logo.svg (ملف `public/defensethon-logo.svg`) */

const LOGO_SRC = "/defensethon-logo.svg";
const EVENT_HREF = "https://defensethon.tuwaiq.edu.sa/";

type Props = {
  /** ارتفاع الشعار بالبكسل؛ العرض يُحسب تلقائياً حسب نسبة الـ SVG (161×48) */
  height?: number;
};

export default function DefensethonLogo({ height = 32 }: Props) {
  const w = Math.round((161 / 48) * height);
  return (
    <a
      href={EVENT_HREF}
      target="_blank"
      rel="noopener noreferrer"
      title="Defensethon — أكاديمية طويق"
      style={{ display: "inline-flex", alignItems: "center", lineHeight: 0, flexShrink: 0 }}
    >
      <img
        src={LOGO_SRC}
        alt="Defensethon ديفنسثون"
        width={w}
        height={height}
        style={{ height, width: "auto", maxWidth: "min(100%, 200px)", objectFit: "contain" }}
        decoding="async"
      />
    </a>
  );
}
