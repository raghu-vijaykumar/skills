import * as fs from "node:fs";
import * as path from "node:path";
import * as url from "node:url";
import { parse } from "yaml";
import { applyTransform, cameraTransformAt } from "@raghu-vijaykumar/videogen/runtime/animation/camera";
const video = process.argv[2];
if (!video) {
  console.error("Usage: node scripts/check-camera-clearance.mts <video-id>");
  process.exit(1);
}
const root = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? "videos", video);
if (!fs.existsSync(root)) {
  console.error(`Video not found: videos/${video}`);
  process.exit(1);
}
const narrationPath = path.resolve(root, "assets/generated/narration.ts");
if (!fs.existsSync(narrationPath)) {
  console.log(`Camera clearance: ${video} skipped (no generated narration)`);
  process.exit(0);
}
const nsrc = fs.readFileSync(narrationPath, "utf8");
const nmatch = nsrc.match(/export const narrationCues = (\[[\s\S]*\]) as const;/);
if (!nmatch) {
  console.error(`Could not parse narration cues: ${narrationPath}`);
  process.exit(1);
}
const cues = JSON.parse(nmatch[1]);
const duration = cues[cues.length - 1]?.endSeconds ?? 0;
if (!Number.isFinite(duration) || duration <= 0) {
  console.error("Camera clearance requires a positive finite narration runtime.");
  process.exit(1);
}
const timelinePath = path.resolve(root, "timeline.ts");
if (!fs.existsSync(timelinePath)) {
  console.log(`Camera clearance: ${video} skipped (no timeline.ts)`);
  process.exit(0);
}
const timeline = await import(url.pathToFileURL(timelinePath).href);
if (typeof timeline.cameraProgram !== "function") {
  console.log(`Camera clearance: ${video} skipped (no cameraProgram)`);
  process.exit(0);
}
const layoutDir = path.resolve(root, "layout");
let spec = null;
if (fs.existsSync(layoutDir)) {
  const candidates = ["layoutSpec.ts", ...fs.readdirSync(layoutDir).filter((f) => f.endsWith(".ts")).sort()];
  for (const cand of candidates) {
    try {
      const candidate = await import(url.pathToFileURL(path.resolve(layoutDir, cand)).href);
      if (typeof candidate.layoutFor === "function") {
        spec = candidate;
        break;
      }
    } catch {
    }
  }
}
if (!spec || typeof spec.layoutFor !== "function") {
  console.log(`Camera clearance: ${video} skipped (no layoutFor)`);
  process.exit(0);
}
const program = timeline.cameraProgram(cues);
const width = program.width;
const height = program.height;
const shots = program.shots;
const layoutFor = spec.layoutFor;
const CAPTION_BAND = { x: width * 0.05, y: height * 0.115, w: width * 0.9, h: 90 };
const TITLE_BAND = { x: 72, y: 40, w: width - 144, h: 135 };
const overlaps = (a, b) => !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y);
function screenRect(b, cam) {
  const corners = [
    [b.x, b.y],
    [b.x + b.w, b.y],
    [b.x, b.y + b.h],
    [b.x + b.w, b.y + b.h]
  ].map(([x, y]) => applyTransform({ x, y }, cam, width, height));
  const xs = corners.map((c) => c.x);
  const ys = corners.map((c) => c.y);
  const x0 = Math.min(...xs);
  const y0 = Math.min(...ys);
  return { x: x0, y: y0, w: Math.max(...xs) - x0, h: Math.max(...ys) - y0 };
}
const step = Number(process.argv[3] ?? "0.1");
if (!Number.isFinite(step) || step <= 0) {
  console.error("Camera clearance stepSeconds must be a positive finite number. Usage: <video-id> [stepSeconds]");
  process.exit(1);
}
const SUSTAINED = 0.5;
const issues = [];
const open = /* @__PURE__ */ new Map();
for (let t = 0; t <= duration + 1e-9; t += step) {
  const layout = layoutFor(t, width, height, cues);
  const cam = cameraTransformAt(t, shots, width, height);
  const active = /* @__PURE__ */ new Set();
  for (const b of layout.boxes) {
    if (b.kind === "text" && b.label === "caption") continue;
    const sr = b.space === "screen" ? b : screenRect(b, cam);
    const inCaption = overlaps(sr, CAPTION_BAND);
    const inTitle = overlaps(sr, TITLE_BAND);
    const key = `${layout.name}|${b.label}`;
    if (inCaption || inTitle) {
      active.add(key);
      if (!open.has(key)) open.set(key, { start: t, scene: layout.name, label: b.label, band: inTitle ? "title" : "caption" });
    }
  }
  for (const [key, o] of [...open]) {
    if (active.has(key)) continue;
    const dur = t - o.start;
    if (dur >= SUSTAINED) issues.push({ ...o, end: t, duration: dur });
    open.delete(key);
  }
}
for (const [, o] of open) {
  const dur = duration - o.start;
  if (dur >= SUSTAINED) issues.push({ ...o, end: duration, duration: dur });
}
let strict = false;
const metaPath = path.resolve(root, "content", "video.yaml");
if (fs.existsSync(metaPath)) {
  try {
    const meta = parse(fs.readFileSync(metaPath, "utf8"));
    const declared = meta?.content?.cameraClearance;
    strict = declared === "strict" || declared === true;
  } catch {
    strict = false;
  }
}
console.log(`
Camera clearance audit: ${video}, ${duration.toFixed(1)}s, ${Math.round(duration / step)} samples${strict ? " (strict)" : ""}`);
if (issues.length === 0) {
  console.log("  \u2713 No box crosses the title or caption band on screen");
  process.exit(0);
}
console.log(`  ${strict ? "\u2717" : "\u26A0"} ${issues.length} sustained band crossing(s)`);
const shown = /* @__PURE__ */ new Set();
for (const i of issues) {
  const key = `${i.scene}|${i.label}|${i.band}`;
  if (shown.has(key)) continue;
  shown.add(key);
  console.log(`  [${strict ? "\u2717" : "\u26A0"}] ${i.scene}: "${i.label}" sits under the ${i.band} band on screen from t=${i.start.toFixed(1)}s to t=${i.end.toFixed(1)}s (${i.duration.toFixed(1)}s)`);
}
if (!strict) {
  console.log("  (warning only; add content.cameraClearance: strict to video.yaml to enforce)");
}
process.exit(strict ? 1 : 0);
