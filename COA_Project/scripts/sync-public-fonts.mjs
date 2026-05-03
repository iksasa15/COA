/**
 * Copies @fontsource woff2 (DM Sans + JetBrains Mono) into web/src/assets/font/.
 * Tajawal يُحمّل من main.tsx عبر @fontsource/tajawal/*.css
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.join(__dirname, "..", "web");
const outDir = path.join(webRoot, "src", "assets", "font");
const nm = path.join(webRoot, "node_modules", "@fontsource");

/** [packageRelativePathFrom@fontsource, destFileName] */
const COPIES = [
  ["dm-sans/files/dm-sans-latin-400-normal.woff2", "dm-sans-400.woff2"],
  ["dm-sans/files/dm-sans-latin-600-normal.woff2", "dm-sans-600.woff2"],
  ["dm-sans/files/dm-sans-latin-700-normal.woff2", "dm-sans-700.woff2"],
  ["jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2", "jetbrains-mono-400.woff2"],
  ["jetbrains-mono/files/jetbrains-mono-latin-500-normal.woff2", "jetbrains-mono-500.woff2"],
];

fs.mkdirSync(outDir, { recursive: true });
for (const f of fs.readdirSync(outDir)) {
  if (f.endsWith(".woff2")) {
    fs.unlinkSync(path.join(outDir, f));
  }
}

let ok = 0;
for (const [rel, destName] of COPIES) {
  const src = path.join(nm, rel);
  const dest = path.join(outDir, destName);
  if (!fs.existsSync(src)) {
    console.error(`[sync-public-fonts] missing: ${src}`);
    process.exitCode = 1;
    continue;
  }
  fs.copyFileSync(src, dest);
  ok += 1;
}

if (process.exitCode === 1) {
  console.error("[sync-public-fonts] Install web deps: cd web && npm install");
  process.exit(1);
}

console.log(`[sync-public-fonts] copied ${ok} files → ${outDir}`);
