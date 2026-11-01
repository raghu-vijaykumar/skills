#!/usr/bin/env node
// Objective frame inspection for rendered output, for workflows with no image
// input. Extracts a single frame with ffmpeg and answers concrete questions
// about it:
//
//   - probes: is an expected colour at an expected coordinate? (design space)
//   - edges: did anything paint into the outer frame border (clipping)?
//   - dead space: how much of the content box is still background?
//   - palette: which of the active theme accents are actually on screen?
//
// Coordinates use the declared design space; the tool scales them to the render.
//
// Usage:
//   videogen probe <file.mp4> <seconds> [options]
//     --probe x,y,#hex[,tol]   expect a colour at a design-space coordinate
//     --region x,y,w,h         region for the dead-space/palette report
//     --scale 0.5              decode scale (default 0.5, keeps decoding cheap)
//     --quiet                  probes only
//
// Example:
//   videogen probe out.mp4 16.5 \
//     --probe 731,580,#f0883e,40 --probe 373,495,#f0b562,70

import {execFileSync} from 'node:child_process';
const themeColors = JSON.parse(process.env.VIDEOGEN_PROBE_THEME ?? '{}');

const args = process.argv.slice(2);
const file = args[0];
const at = Number(args[1]);
if (!file || !Number.isFinite(at)) {
  console.error('Usage: videogen probe <file> <seconds> [--design WxH] [--probe x,y,#hex[,tol]] [--region x,y,w,h] [--scale s] [--quiet]');
  process.exit(1);
}

const valueOf = (flag) => {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : null;
};
const allOf = (flag) => args.reduce((acc, a, i) => (a === flag ? [...acc, args[i + 1]] : acc), []);
const quiet = args.includes('--quiet');
const scale = Number(valueOf('--scale') ?? 0.5);
const design = (valueOf('--design') ?? '1080x1920').split('x').map(Number);
const [DESIGN_W, DESIGN_H] = design;
if (!(DESIGN_W > 0 && DESIGN_H > 0)) throw new Error('--design requires positive WxH');

const hexToRgb = (hex) => {
  const h = hex.trim().replace(/^#/, '');
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
};
const BG = hexToRgb(themeColors.background ?? '#000000');
const rgbToHex = ([r, g, b]) => `#${[r, g, b].map((v) => Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0')).join('')}`;

const probeDim = execFileSync(
  'ffprobe',
  ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', file],
  {encoding: 'utf8'},
).trim().split(',').map(Number);
const [frameW, frameH] = probeDim;
const outW = Math.max(8, Math.round(frameW * scale));
const outH = Math.max(8, Math.round(frameH * scale));
const sx = outW / DESIGN_W;
const sy = outH / DESIGN_H;

const raw = execFileSync(
  'ffmpeg',
  ['-hide_banner', '-loglevel', 'error', '-ss', String(at), '-i', file, '-frames:v', '1', '-vf', `scale=${outW}:${outH}`, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
  {maxBuffer: 512 * 1024 * 1024, encoding: 'buffer'},
);
if (raw.length < outW * outH * 3) {
  console.error(`No frame decoded at ${at}s (got ${raw.length} bytes, need ${outW * outH * 3}).`);
  process.exit(1);
}

// Sample the average of a small patch so one antialiased pixel cannot decide it.
const patch = (dx, dy, radius = 1) => {
  const cx = Math.round(dx * sx);
  const cy = Math.round(dy * sy);
  const r = Math.max(1, Math.round(radius * sx));
  const sum = [0, 0, 0];
  let n = 0;
  for (let y = Math.max(0, cy - r); y <= Math.min(outH - 1, cy + r); y += 1) {
    for (let x = Math.max(0, cx - r); x <= Math.min(outW - 1, cx + r); x += 1) {
      const i = (y * outW + x) * 3;
      sum[0] += raw[i];
      sum[1] += raw[i + 1];
      sum[2] += raw[i + 2];
      n += 1;
    }
  }
  return sum.map((v) => Math.round(v / Math.max(1, n)));
};

const dist = (a, b) => Math.max(Math.abs(a[0] - b[0]), Math.abs(a[1] - b[1]), Math.abs(a[2] - b[2]));

console.log(`Frame ${file} @ ${at}s  (${frameW}x${frameH}, decoded ${outW}x${outH})`);

// --- colour probes ----------------------------------------------------------
const probes = allOf('--probe');
let failed = 0;
for (const spec of probes) {
  const [x, y, hex, tol] = spec.split(',');
  const expect = hexToRgb(hex);
  const got = patch(Number(x), Number(y));
  const d = dist(expect, got);
  const ok = d <= Number(tol ?? 30);
  if (!ok) failed += 1;
  console.log(`  ${ok ? '✓' : '✗'} probe (${Number(x).toFixed(0)},${Number(y).toFixed(0)}) want ${hex.toUpperCase()} tol ${tol ?? 30} → got ${rgbToHex(got).toUpperCase()} (Δ${d})`);
}

if (quiet) {
  process.exit(failed > 0 ? 1 : 0);
}

// --- edge contamination ----------------------------------------------------
// Nothing should be painted in the outer 6 design px of the canvas.
const border = Math.max(1, Math.round(6 * sx));
let brightest = {lum: -1, x: 0, y: 0, color: [0, 0, 0]};
for (let y = 0; y < outH; y += 1) {
  for (let x = 0; x < outW; x += 1) {
    if (x >= border && x < outW - border && y >= border && y < outH - border) continue;
    const i = (y * outW + x) * 3;
    const px = [raw[i], raw[i + 1], raw[i + 2]];
    const lum = 0.2126 * px[0] + 0.7152 * px[1] + 0.0722 * px[2];
    if (lum > brightest.lum) brightest = {lum, x: Math.round(x / sx), y: Math.round(y / sy), color: px};
  }
}
console.log(`  edge: brightest pixel in outer ${6}px = ${rgbToHex(brightest.color)} at (${brightest.x},${brightest.y}) lum ${brightest.lum.toFixed(0)}${brightest.lum > 40 ? '  ← contamination' : '  (clean)'}`);

// --- dead space + palette over a region ------------------------------------
const region = (valueOf('--region') ?? `${Math.round(DESIGN_W * 0.045)},${Math.round(DESIGN_H * 0.05)},${Math.round(DESIGN_W * 0.91)},${Math.round(DESIGN_H * 0.9)}`).split(',').map(Number);
const [rx, ry, rw, rh] = region;
let total = 0;
let dead = 0;
const buckets = new Map();
for (let y = Math.max(0, Math.round(ry * sy)); y < Math.min(outH, Math.round((ry + rh) * sy)); y += 1) {
  for (let x = Math.max(0, Math.round(rx * sx)); x < Math.min(outW, Math.round((rx + rw) * sx)); x += 1) {
    const i = (y * outW + x) * 3;
    const px = [raw[i], raw[i + 1], raw[i + 2]];
    total += 1;
    if (dist(px, BG) <= 14) dead += 1;
    const key = `${px[0] >> 5},${px[1] >> 5},${px[2] >> 5}`;
    const bucket = buckets.get(key) ?? {n: 0, sum: [0, 0, 0]};
    bucket.n += 1;
    bucket.sum[0] += px[0];
    bucket.sum[1] += px[1];
    bucket.sum[2] += px[2];
    buckets.set(key, bucket);
  }
}
console.log(`  region (${rx},${ry},${rw},${rh}): background ${((dead / Math.max(1, total)) * 100).toFixed(1)}% of ${total} px`);
const top = [...buckets.values()]
  .sort((a, b) => b.n - a.n)
  .slice(0, 6)
  .map((b) => `${rgbToHex(b.sum.map((v) => Math.round(v / b.n)))} ${((b.n / Math.max(1, total)) * 100).toFixed(1)}%`);
console.log(`  palette: ${top.join('  ')}`);

// Report accents from the selected project theme rather than a channel palette.
const TOKENS = Object.fromEntries(Object.entries(themeColors).filter(([name, hex]) => !['background', 'elevated', 'border'].includes(name) && /^#[0-9a-f]{6}$/i.test(hex)));
const counts = Object.fromEntries(Object.keys(TOKENS).map((k) => [k, 0]));
for (let y = Math.max(0, Math.round(ry * sy)); y < Math.min(outH, Math.round((ry + rh) * sy)); y += 1) {
  for (let x = Math.max(0, Math.round(rx * sx)); x < Math.min(outW, Math.round((rx + rw) * sx)); x += 1) {
    const i = (y * outW + x) * 3;
    const px = [raw[i], raw[i + 1], raw[i + 2]];
    for (const [name, hex] of Object.entries(TOKENS)) {
      if (dist(px, hexToRgb(hex)) <= 40) counts[name] += 1;
    }
  }
}
const present = Object.entries(counts)
  .filter(([, n]) => n > total * 0.0002)
  .map(([k, n]) => `${k} ${((n / Math.max(1, total)) * 100).toFixed(1)}%`);
const absent = Object.entries(counts).filter(([, n]) => n <= total * 0.0002).map(([k]) => k);
console.log(`  accents present: ${present.join('  ') || 'none'}`);
if (absent.length) console.log(`  accents absent:  ${absent.join(' ')}`);

process.exit(failed > 0 ? 1 : 0);
