// Per-second sampled layout audit over the real timeline — no render needed.
// Samples every `step` seconds (default 1s = 1 frame/sec) for the whole duration
// and validates each active scene's boxes (on-screen, no overlap, link lengths).
//
// Usage:
//   node scripts/check-layout-video.ts                            # 00001-airbnb-double-payment @1920x1080
//   node scripts/check-layout-video.ts --video 00001-...          # explicit video
//   node scripts/check-layout-video.ts 1280x720                   # resolution (video default)
//   node scripts/check-layout-video.ts --video 00001-... 1280x720 0.5

import * as fs from 'node:fs';
import * as path from 'node:path';
import * as url from 'node:url';
import {parse} from 'yaml';

type NarrationCue = {id: string; text: string; startSeconds: number; endSeconds: number};

// Resolve video id (--video=<id> or first arg that names an existing videos/<id> dir),
// then positional dims/step.
const argv = process.argv.slice(2);
let videoId = '00001-airbnb-double-payment';
let rest: string[] = [];
const flagVideo = argv.find((a) => a.startsWith('--video='));
if (flagVideo) {
  videoId = flagVideo.slice('--video='.length);
  rest = argv.filter((a) => !a.startsWith('--video='));
} else if (argv[0] && fs.existsSync(path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', argv[0]))) {
  videoId = argv[0];
  rest = argv.slice(1);
} else {
  rest = argv;
}

const dims = (rest[0] || '1920x1080').toLowerCase().split('x').map(Number);
const width = dims[0];
const height = dims[1];
const step = Number(rest[1] || '1');

if (!fs.existsSync(path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', videoId))) {
  console.error(`Video not found: videos/${videoId}`);
  process.exit(1);
}

// Narrated films use generated cue timing; music-only identities use their
// declared fixed duration and an empty cue list.
const narrationPath = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', videoId, 'assets/generated/narration.ts');
const narrationSourcePath = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', videoId, 'content/narration.yaml');
let narrationCues: NarrationCue[] = [];
let duration: number;
if (fs.existsSync(narrationSourcePath)) {
  const src = fs.readFileSync(narrationPath, 'utf8');
  const match = src.match(/export const narrationCues = (\[[\s\S]*\]) as const;/);
  if (!match) {
    console.error(`Could not parse narration cues: ${narrationPath}`);
    process.exit(1);
  }
  narrationCues = JSON.parse(match[1]) as NarrationCue[];
  duration = narrationCues[narrationCues.length - 1].endSeconds;
} else {
  const metadata = parse(fs.readFileSync(path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', videoId, 'content/video.yaml'), 'utf8')) as {video?: {durationSeconds?: number}};
  duration = Number(metadata?.video?.durationSeconds);
  if (!Number.isFinite(duration) || duration <= 0) {
    console.error(`Music-only video '${videoId}' needs a positive video.durationSeconds in content/video.yaml.`);
    process.exit(1);
  }
}

// Dynamic import of the video's layout spec (single source of truth) and timeline.
// Specs export either a generic `layoutFor(t, w, h, cues)` (new videos) or the
// named scene layouts used by the Airbnb reference. We scan the video's
// layout/ directory for a `layoutFor` export, falling back to the legacy named
// scene layouts (activeScene + baseLayout/scaleLayout/...).
let spec;
const layoutDir = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', videoId, 'layout');
if (fs.existsSync(layoutDir)) {
  const specCandidates = [
    'layoutSpec.ts',
    ...fs.readdirSync(layoutDir).filter((f) => f.endsWith('.ts')).sort(),
  ];
  let legacy = null;
  for (const cand of specCandidates) {
    try {
      const specUrl = url.pathToFileURL(path.resolve(layoutDir, cand)).href;
      const candidate = await import(specUrl);
      if (typeof candidate.layoutFor === 'function') {
        spec = candidate;
        break;
      }
      if (!legacy && typeof candidate.activeScene === 'function') legacy = candidate;
    } catch {
      // try the next candidate
    }
  }
  if (!spec && legacy) spec = legacy;
}
if (!spec) {
  console.error(`No layout spec with layoutFor found for video '${videoId}'.`);
  process.exit(1);
}
type Box = (typeof spec)['Box'];
type LinkEndpoint = (typeof spec)['LinkEndpoint'];
type LayoutRule = (typeof spec)['LayoutRule'];

let layoutFor: (t: number) => ReturnType<(typeof spec)['layoutFor']>;
if (typeof spec.layoutFor === 'function') {
  layoutFor = (t: number) => spec.layoutFor(t, width, height, narrationCues);
} else {
  const {activeScene, baseLayout, scaleLayout, leaseLayout, errorsLayout, orpheusLayout} = spec;
  layoutFor = (t: number) => {
    const scene = activeScene(t, narrationCues);
    if (scene === 'scale') return scaleLayout(t, width, height, narrationCues);
    if (scene === 'lease') return leaseLayout(t, width, height, narrationCues);
    if (scene === 'errors') return errorsLayout(t, width, height, narrationCues);
    if (scene === 'orpheus') return orpheusLayout(t, width, height, narrationCues);
    return baseLayout(t, width, height, narrationCues);
  };
}

type Issue = {t: number; scene: string; msg: string; kind: 'error' | 'warn'};
const issues: Issue[] = [];

// Content must stay inside a padding zone on all sides so it never collides
// with the white glowing border drawn at the canvas edge.
const CONTENT_PADDING = 48;

function checkBox(b: Box, t: number, scene: string) {
  const right = b.x + b.w;
  const bottom = b.y + b.h;
  if (b.x < 0 || b.y < 0) issues.push({t, scene, msg: `${b.label} off-screen top-left (${b.x.toFixed(0)},${b.y.toFixed(0)})`, kind: 'error'});
  if (right > width) issues.push({t, scene, msg: `${b.label} past right edge (right=${right.toFixed(0)} > ${width})`, kind: 'error'});
  if (bottom > height) issues.push({t, scene, msg: `${b.label} past bottom edge (bottom=${bottom.toFixed(0)} > ${height})`, kind: 'error'});
  // Padding zone: text/header overlays (kind:'text') are exempt — they are the
  // scene titles/badges that intentionally sit near the top edge under the title.
  if (b.kind === 'text') return;
  if (b.x < CONTENT_PADDING) issues.push({t, scene, msg: `${b.label} intrudes left padding (x=${b.x.toFixed(0)} < ${CONTENT_PADDING})`, kind: 'warn'});
  if (b.y < CONTENT_PADDING) issues.push({t, scene, msg: `${b.label} intrudes top padding (y=${b.y.toFixed(0)} < ${CONTENT_PADDING})`, kind: 'warn'});
  if (right > width - CONTENT_PADDING) issues.push({t, scene, msg: `${b.label} intrudes right padding (right=${right.toFixed(0)} > ${width - CONTENT_PADDING})`, kind: 'warn'});
  if (bottom > height - CONTENT_PADDING) issues.push({t, scene, msg: `${b.label} intrudes bottom padding (bottom=${bottom.toFixed(0)} > ${height - CONTENT_PADDING})`, kind: 'warn'});
}

function overlap(a: Box, b: Box) {
  return !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y);
}

function checkLink(l: LinkEndpoint, t: number, scene: string) {
  const len = Math.hypot(l.x2 - l.x1, l.y2 - l.y1);
  if (len <= 20) issues.push({t, scene, msg: `${l.label} link too short (${len.toFixed(0)}px)`, kind: 'warn'});
  if (l.x1 < 0 || l.x2 > width || l.y1 < 0 || l.y2 > height) {
    issues.push({t, scene, msg: `${l.label} link endpoint off-screen`, kind: 'warn'});
  }
}

// Every connection must attach each end to its box — either the border midpoint
// or, for boxes with a custom anchor (e.g. LB circle circumference), that anchor.
// Sharing the same midpoint across links is intended, so only border/off-box
// misattachment is flagged.
function checkConnections(layout: {boxes: Box[]; links: LinkEndpoint[]; connections?: {label: string; from: string; to: string}[]}, t: number) {
  if (!layout.connections) return;
  const boxFor = (label: string) => layout.boxes.find((b) => b.label === label);
  // Attach point is valid if it lies on a border edge, or equals a custom anchor
  // (e.g. the LB circle circumference midpoint, which is inside the box).
  const onBorder = (p: {x: number; y: number}, box: Box) => {
    const onX = Math.abs(p.x - box.x) < 3 || Math.abs(p.x - (box.x + box.w)) < 3;
    const onY = Math.abs(p.y - box.y) < 3 || Math.abs(p.y - (box.y + box.h)) < 3;
    const inside = p.x >= box.x - 3 && p.x <= box.x + box.w + 3 && p.y >= box.y - 3 && p.y <= box.y + box.h + 3;
    const onAnchor = box.anchors ? Object.values(box.anchors).some((a) => Math.abs(a.x - p.x) < 3 && Math.abs(a.y - p.y) < 3) : false;
    return (inside && (onX || onY)) || onAnchor;
  };
  for (const c of layout.connections) {
    const a = boxFor(c.from);
    const b = boxFor(c.to);
    const link = layout.links.find((l) => l.label === c.label);
    if (!a || !b || !link) continue;
    if (!onBorder({x: link.x1, y: link.y1}, a)) {
      issues.push({t, scene: layout.name, msg: `${c.label}: start (${link.x1.toFixed(0)},${link.y1.toFixed(0)}) not on ${c.from} border`, kind: 'error'});
    }
    if (!onBorder({x: link.x2, y: link.y2}, b)) {
      issues.push({t, scene: layout.name, msg: `${c.label}: end (${link.x2.toFixed(0)},${link.y2.toFixed(0)}) not on ${c.to} border`, kind: 'error'});
    }
  }
}

// Symmetry constraint: a mirror pair's center-x offsets from the canvas center
// should match within a tolerance (default 24px).
function checkSymmetry(layout: {boxes: Box[]; symmetry?: {left: string; right: string; tol?: number}[]}, t: number) {
  if (!layout.symmetry) return;
  for (const rule of layout.symmetry) {
    const a = layout.boxes.find((b) => b.label === rule.left);
    const b = layout.boxes.find((b) => b.label === rule.right);
    if (!a || !b) {
      issues.push({t, scene: layout.name, msg: `symmetry: missing box ${rule.left} or ${rule.right}`, kind: 'warn'});
      continue;
    }
    const aMid = a.x + a.w / 2;
    const bMid = b.x + b.w / 2;
    const offA = Math.abs(width / 2 - aMid);
    const offB = Math.abs(bMid - width / 2);
    const tol = rule.tol ?? 24;
    const diff = Math.abs(offA - offB);
    if (diff > tol) {
      issues.push({
        t,
        scene: layout.name,
        msg: `symmetry: ${rule.left} offset ${offA.toFixed(0)}px vs ${rule.right} offset ${offB.toFixed(0)}px differ by ${diff.toFixed(0)}px (>${tol})`,
        kind: 'warn',
      });
    }
  }
}

// Collinear: the listed boxes' centers must lie on one straight line. Uses the
// max perpendicular distance of any point from the best-fit line through the
// first and last center (works for monotonic sequences).
function checkCollinear(layout: {boxes: Box[]; rules?: LayoutRule[]}, t: number) {
  const collinear = layout.rules?.filter((r) => r.type === 'collinear') ?? [];
  for (const rule of collinear) {
    if (rule.type !== 'collinear') continue;
    const centers = rule.labels
      .map((label) => layout.boxes.find((b) => b.label === label))
      .filter((b): b is Box => Boolean(b))
      .map((b) => ({x: b.x + b.w / 2, y: b.y + b.h / 2}));
    if (centers.length < 3) {
      issues.push({t, scene: layout.name, msg: `collinear: needs >=3 boxes (${rule.labels.join(', ')})`, kind: 'warn'});
      continue;
    }
    const p0 = centers[0];
    const p1 = centers[centers.length - 1];
    const tol = rule.tol ?? 6;
    const dx = p1.x - p0.x;
    const dy = p1.y - p0.y;
    const len = Math.hypot(dx, dy);
    let maxDist = 0;
    let worst = '';
    for (const c of centers) {
      const dist = len === 0 ? Math.hypot(c.x - p0.x, c.y - p0.y) : Math.abs(dy * c.x - dx * c.y + p1.x * p0.y - p1.y * p0.x) / len;
      if (dist > maxDist) {
        maxDist = dist;
        const idx = centers.indexOf(c);
        worst = rule.labels[idx] ?? '?';
      }
    }
    if (maxDist > tol) {
      issues.push({
        t,
        scene: layout.name,
        msg: `collinear: '${worst}' deviates ${maxDist.toFixed(1)}px from the line (${rule.labels.join(' -> ')})`,
        kind: 'warn',
      });
    }
  }
}

// Center: the group bounding box should sit near the canvas center.
function checkCenter(layout: {boxes: Box[]; rules?: LayoutRule[]}, t: number) {
  const center = layout.rules?.find((r) => r.type === 'center');
  if (!center || center.type !== 'center') return;
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const b of layout.boxes) {
    minX = Math.min(minX, b.x);
    minY = Math.min(minY, b.y);
    maxX = Math.max(maxX, b.x + b.w);
    maxY = Math.max(maxY, b.y + b.h);
  }
  const gx = (minX + maxX) / 2;
  const gy = (minY + maxY) / 2;
  const tolX = center.tolX ?? 48;
  const tolY = center.tolY ?? 48;
  if (Math.abs(gx - width / 2) > tolX) {
    issues.push({t, scene: layout.name, msg: `center: group center-x ${gx.toFixed(0)} is ${Math.abs(gx - width / 2).toFixed(0)}px off canvas center (${width / 2})`, kind: 'warn'});
  }
  if (Math.abs(gy - height / 2) > tolY) {
    issues.push({t, scene: layout.name, msg: `center: group center-y ${gy.toFixed(0)} is ${Math.abs(gy - height / 2).toFixed(0)}px off canvas center (${height / 2})`, kind: 'warn'});
  }
}

// The stage Title sits top-left (top:58, left:72, right:72) with a tall header.
// Scene content must not overlap that band — only the title-band zone itself
// (marked kind:'text') is allowed there.
function checkTitleClearance(layout: {boxes: Box[]; name: string}, t: number) {
  const bandTop = 40;
  const bandBottom = 175;
  for (const b of layout.boxes) {
    if (b.kind === 'text') continue;
    const overlapsVert = b.y < bandBottom && b.y + b.h > bandTop;
    if (!overlapsVert) continue;
    const overlapsHoriz = b.x < width - 72 && b.x + b.w > 72;
    if (overlapsHoriz) {
      issues.push({t, scene: layout.name, msg: `${b.label} overlaps the title band (top ${bandTop}-${bandBottom}px)`, kind: 'error'});
    }
  }
}

// Short videos reserve a caption band under the title (label:'caption',
// y=0.115h). Scene content must start below it so it never collides with the
// narration captions. This enforces the "where should the infographic start"
// rule for shorts.
function checkCaptionClearance(layout: {boxes: Box[]; name: string}, t: number) {
  const cap = layout.boxes.find((b) => b.label === 'caption' && b.kind === 'text');
  if (!cap) return;
  for (const b of layout.boxes) {
    if (b.kind === 'text' || b === cap) continue;
    const overlaps = !(b.x + b.w <= cap.x || cap.x + cap.w <= b.x || b.y + b.h <= cap.y || cap.y + cap.h <= b.y);
    if (overlaps) {
      issues.push({
        t,
        scene: layout.name,
        msg: `${b.label} overlaps the caption band (caption y ${cap.y.toFixed(0)}-${(cap.y + cap.h).toFixed(0)}); move the infographic below it`,
        kind: 'error',
      });
    }
  }
  // Spacing: captions must sit a clear minimum gap below the title band so the
  // narration never crowds the scene title.
  const TITLE_BAND_BOTTOM = 175;
  const MIN_TITLE_CAPTION_GAP = 40;
  if (cap.y < TITLE_BAND_BOTTOM + MIN_TITLE_CAPTION_GAP) {
    issues.push({
      t,
      scene: layout.name,
      msg: `caption band too close to the title (y ${cap.y.toFixed(0)}px < ${TITLE_BAND_BOTTOM + MIN_TITLE_CAPTION_GAP}px); keep at least ${MIN_TITLE_CAPTION_GAP}px below the title band`,
      kind: 'error',
    });
  }
}

let samples = 0;
const perScene: Record<string, number> = {};
for (let t = 0; t <= duration + 1e-9; t += step) {
  const layout = layoutFor(t);
  perScene[layout.name] = (perScene[layout.name] ?? 0) + 1;
  samples += 1;

  for (const b of layout.boxes) checkBox(b, t, layout.name);
  checkTitleClearance(layout, t);
  checkCaptionClearance(layout, t);
  const solidBoxes = layout.boxes.filter((b) => b.kind !== 'trie-edge');
  for (let i = 0; i < solidBoxes.length; i++) {
    for (let j = i + 1; j < solidBoxes.length; j++) {
      if (overlap(solidBoxes[i], solidBoxes[j])) {
        issues.push({t, scene: layout.name, msg: `OVERLAP ${solidBoxes[i].label} <-> ${solidBoxes[j].label}`, kind: 'warn'});
      }
    }
  }
  for (const l of layout.links) checkLink(l, t, layout.name);
  checkSymmetry(layout, t);
  checkCollinear(layout, t);
  checkCenter(layout, t);
  checkConnections(layout, t);
}

const errors = issues.filter((i) => i.kind === 'error');
const warns = issues.filter((i) => i.kind === 'warn');

console.log(`\nLayout audit: ${width}x${height}, ${(duration).toFixed(1)}s, ${samples} samples (${step}s step)`);
console.log(`Scenes sampled: ${Object.entries(perScene).map(([k, v]) => `${k}=${v}`).join(', ')}`);

if (issues.length === 0) {
  console.log('  ✓ No layout issues');
} else {
  console.log(`  ✗ errors=${errors.length}  ⚠ warnings=${warns.length}`);
  const shown = new Set<string>();
  for (const issue of [...errors, ...warns]) {
    const key = `${issue.scene}|${issue.msg}`;
    if (shown.has(key)) continue;
    shown.add(key);
    console.log(`  [${issue.kind === 'error' ? '✗' : '⚠'}] t=${issue.t.toFixed(1)}s ${issue.scene}: ${issue.msg}`);
  }
}

process.exit(errors.length > 0 ? 1 : 0);
