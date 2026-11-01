// Screen-space camera clearance audit.
//
// The canvas-space layout gate (`check-layout-video.mts`) validates boxes before
// the camera transform. It cannot see that a camera pan/zoom lifts an otherwise
// valid box up under the fixed title or caption band mid-scene, then brings it
// back. This audit resolves the real camera program over time and checks the
// screen-space footprint of every layout box against the reserved title and
// caption bands.
//
// Rule: a box may pass through a band briefly while the scene is entering or
// transitioning, but a *sustained* overlap (the content sits under the band, or
// drifts up into it and back) is an error. A box that is genuinely entering the
// scene only clips the band for a moment.
//
// Usage: node scripts/check-camera-clearance.mts <video-id> [stepSeconds]

import * as fs from 'node:fs';
import * as path from 'node:path';
import * as url from 'node:url';
import {parse} from 'yaml';
import {applyTransform, cameraTransformAt} from '@raghu-vijaykumar/videogen/runtime/animation/camera';

type NarrationCue = {id: string; text: string; startSeconds: number; endSeconds: number};
type Rect = {x: number; y: number; w: number; h: number};

const video = process.argv[2];
if (!video) {
  console.error('Usage: node scripts/check-camera-clearance.mts <video-id>');
  process.exit(1);
}
const root = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', video);
if (!fs.existsSync(root)) {
  console.error(`Video not found: videos/${video}`);
  process.exit(1);
}

const narrationPath = path.resolve(root, 'assets/generated/narration.ts');
if (!fs.existsSync(narrationPath)) {
  console.log(`Camera clearance: ${video} skipped (no generated narration)`);
  process.exit(0);
}
const nsrc = fs.readFileSync(narrationPath, 'utf8');
const nmatch = nsrc.match(/export const narrationCues = (\[[\s\S]*\]) as const;/);
if (!nmatch) {
  console.error(`Could not parse narration cues: ${narrationPath}`);
  process.exit(1);
}
const cues = JSON.parse(nmatch[1]) as NarrationCue[];
const duration = cues[cues.length - 1]?.endSeconds ?? 0;
if (!Number.isFinite(duration) || duration <= 0) {
  console.error('Camera clearance requires a positive finite narration runtime.');
  process.exit(1);
}

// A video is in scope only when it authors a camera program AND a layout spec.
const timelinePath = path.resolve(root, 'timeline.ts');
if (!fs.existsSync(timelinePath)) {
  console.log(`Camera clearance: ${video} skipped (no timeline.ts)`);
  process.exit(0);
}
const timeline = (await import(url.pathToFileURL(timelinePath).href)) as Record<string, unknown>;
if (typeof timeline.cameraProgram !== 'function') {
  console.log(`Camera clearance: ${video} skipped (no cameraProgram)`);
  process.exit(0);
}

const layoutDir = path.resolve(root, 'layout');
let spec: Record<string, unknown> | null = null;
if (fs.existsSync(layoutDir)) {
  const candidates = ['layoutSpec.ts', ...fs.readdirSync(layoutDir).filter((f) => f.endsWith('.ts')).sort()];
  for (const cand of candidates) {
    try {
      const candidate = (await import(url.pathToFileURL(path.resolve(layoutDir, cand)).href)) as Record<string, unknown>;
      if (typeof candidate.layoutFor === 'function') {
        spec = candidate;
        break;
      }
    } catch {
      // try the next candidate
    }
  }
}
if (!spec || typeof spec.layoutFor !== 'function') {
  console.log(`Camera clearance: ${video} skipped (no layoutFor)`);
  process.exit(0);
}

const program = (timeline.cameraProgram as (cues: NarrationCue[]) => {shots: never[]; width: number; height: number})(cues);
const width = program.width;
const height = program.height;
const shots = program.shots;
const layoutFor = spec.layoutFor as (t: number, w: number, h: number, cues: NarrationCue[]) => {boxes: {label: string; x: number; y: number; w: number; h: number; kind?: string; space?:'world'|'screen'}[]; name: string};

// Reserved bands, in screen space (the same geometry the layout gate reserves).
const CAPTION_BAND: Rect = {x: width * 0.05, y: height * 0.115, w: width * 0.9, h: 90};
const TITLE_BAND: Rect = {x: 72, y: 40, w: width - 144, h: 135};

const overlaps = (a: Rect, b: Rect) => !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y);

function screenRect(b: {x: number; y: number; w: number; h: number}, cam: {cx: number; cy: number; scale: number}): Rect {
  const corners = [
    [b.x, b.y],
    [b.x + b.w, b.y],
    [b.x, b.y + b.h],
    [b.x + b.w, b.y + b.h],
  ].map(([x, y]) => applyTransform({x, y}, cam, width, height));
  const xs = corners.map((c) => c.x);
  const ys = corners.map((c) => c.y);
  const x0 = Math.min(...xs);
  const y0 = Math.min(...ys);
  return {x: x0, y: y0, w: Math.max(...xs) - x0, h: Math.max(...ys) - y0};
}

const step = Number(process.argv[3] ?? '0.1');
// Invalid arguments previously produced a NaN loop bound and a false pass;
// zero or negative intervals could hang the audit. Fail before sampling.
if (!Number.isFinite(step) || step <= 0) {
  console.error('Camera clearance stepSeconds must be a positive finite number. Usage: <video-id> [stepSeconds]');
  process.exit(1);
}
// A sustained overlap longer than this is a defect; a brief pass (entering the
// scene) is tolerated.
const SUSTAINED = 0.5;

type Issue = {start: number; end: number; duration: number; scene: string; label: string; band: string};
const issues: Issue[] = [];
const open = new Map<string, {start: number; scene: string; label: string; band: string}>();

for (let t = 0; t <= duration + 1e-9; t += step) {
  const layout = layoutFor(t, width, height, cues);
  const cam = cameraTransformAt(t, shots as never, width, height);
  const active = new Set<string>();
  for (const b of layout.boxes) {
    if (b.kind === 'text' && b.label === 'caption') continue;
    // Scientific plots and crisp annotations can live on the actual screen
    // plane. Audit their real rectangles without applying a hidden world cam.
    const sr = b.space === 'screen' ? b : screenRect(b, cam);
    const inCaption = overlaps(sr, CAPTION_BAND);
    const inTitle = overlaps(sr, TITLE_BAND);
    const key = `${layout.name}|${b.label}`;
    if (inCaption || inTitle) {
      active.add(key);
      if (!open.has(key)) open.set(key, {start: t, scene: layout.name, label: b.label, band: inTitle ? 'title' : 'caption'});
    }
  }
  // Close any interval that is no longer overlapping.
  for (const [key, o] of [...open]) {
    if (active.has(key)) continue;
    const dur = t - o.start;
    if (dur >= SUSTAINED) issues.push({...o, end: t, duration: dur});
    open.delete(key);
  }
}
for (const [, o] of open) {
  const dur = duration - o.start;
  if (dur >= SUSTAINED) issues.push({...o, end: duration, duration: dur});
}

// Strictness is opt-in: a video declares `content.cameraClearance: strict` in
// its video.yaml. Other videos still get the report as warnings so the gate can
// be adopted incrementally without blocking their renders.
let strict = false;
const metaPath = path.resolve(root, 'content', 'video.yaml');
if (fs.existsSync(metaPath)) {
  try {
    const meta = parse(fs.readFileSync(metaPath, 'utf8'));
    const declared = meta?.content?.cameraClearance;
    strict = declared === 'strict' || declared === true;
  } catch {
    strict = false;
  }
}

console.log(`\nCamera clearance audit: ${video}, ${(duration).toFixed(1)}s, ${Math.round(duration / step)} samples${strict ? ' (strict)' : ''}`);
if (issues.length === 0) {
  console.log('  ✓ No box crosses the title or caption band on screen');
  process.exit(0);
}
console.log(`  ${strict ? '✗' : '⚠'} ${issues.length} sustained band crossing(s)`);
const shown = new Set<string>();
for (const i of issues) {
  const key = `${i.scene}|${i.label}|${i.band}`;
  if (shown.has(key)) continue;
  shown.add(key);
  console.log(`  [${strict ? '✗' : '⚠'}] ${i.scene}: "${i.label}" sits under the ${i.band} band on screen from t=${i.start.toFixed(1)}s to t=${i.end.toFixed(1)}s (${i.duration.toFixed(1)}s)`);
}
if (!strict) {
  console.log('  (warning only; add content.cameraClearance: strict to video.yaml to enforce)');
}
process.exit(strict ? 1 : 0);
