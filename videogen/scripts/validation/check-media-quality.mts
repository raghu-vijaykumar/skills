// Media-quality gate. Reusable across every media-driven video.
//
// Usage: node scripts/check-media-quality.mts <video-id>
//
// Reads videos/<video-id>/assets/media/manifest.json (if present) and proves
// the philosophy the manifest states: every raster asset is genuinely large
// enough for the render, every asset records its provenance, nothing is
// duplicated, and nothing is an unsupported format.
//
// Exits 0 and prints a skip line when a video has no manifest, so it can be
// wired into the shared render pipeline without affecting animation-only
// videos.

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

type Asset = {
  file?: string;
  type?: string;
  intrinsic?: string;
  source?: string;
  page?: string;
  owner?: string;
  attribution?: string;
  use?: string;
  notes?: string;
  // Where the asset actually lands in the composition, in px. `null` means the
  // asset is catalogued but not placed on screen, so no scale check applies.
  rendered?: {w: number; h: number} | null;
};

type Manifest = {
  video?: string;
  min_scale_ratio?: number;
  assets?: Asset[];
  rejected?: {file?: string; reason?: string}[];
  policy?: string;
};

// A 1080-wide portrait render wants a source that is never enlarged past its
// own pixels: intrinsic short edge / rendered short edge must clear the ratio.
const MIN_RASTER_SHORT_EDGE = 1200;
const DEFAULT_MIN_SCALE_RATIO = 1.0;
const SUPPORTED = new Set(['.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif']);
// object-fit: contain never crops, so a rendered aspect far from the intrinsic
// aspect means something is being cropped somewhere.
const ASPECT_TOLERANCE = 0.2;

const video = process.argv[2];
if (!video) {
  console.error('Usage: node scripts/check-media-quality.mts <video-id>');
  process.exit(1);
}

const dir = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? 'videos', video, 'assets', 'media');
const manifestPath = path.join(dir, 'manifest.json');
if (!fs.existsSync(manifestPath)) {
  console.log(`Media quality: ${video} skipped (no media manifest)`);
  process.exit(0);
}

const issues: string[] = [];
const warnings: string[] = [];

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8')) as Manifest;
if (!Array.isArray(manifest.assets) || manifest.assets.length === 0) {
  issues.push('manifest has no assets');
}
if (!manifest.policy || manifest.policy.trim().length < 20) {
  warnings.push('manifest has no stated sourcing policy');
}

// ---- dimension probes -----------------------------------------------------

function pngSize(buf: Buffer): {w: number; h: number} | null {
  if (buf.length < 24 || buf.readUInt32BE(0) !== 0x89504e47) return null;
  return {w: buf.readUInt32BE(16), h: buf.readUInt32BE(20)};
}

function jpegSize(buf: Buffer): {w: number; h: number} | null {
  if (buf.length < 4 || buf.readUInt16BE(0) !== 0xffd8) return null;
  let o = 2;
  while (o + 9 < buf.length) {
    if (buf[o] !== 0xff) {
      o += 1;
      continue;
    }
    const marker = buf[o + 1];
    const len = buf.readUInt16BE(o + 2);
    if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
      return {h: buf.readUInt16BE(o + 5), w: buf.readUInt16BE(o + 7)};
    }
    o += 2 + len;
  }
  return null;
}

// SVG may wrap a high-resolution raster. What matters for sharpness is the
// real pixel dimensions of the embedded bitmap, not the SVG presentation size:
// a 400x400 JPEG can be declared as <image width="2000" height="2000">. So we
// decode the embedded data URI and probe the bitmap itself, and resolve any
// external reference against the local asset.
function svgInfo(src: string, dir: string): {rasters: {w: number; h: number; how: string}[]; unresolved: number} {
  const rasters: {w: number; h: number; how: string}[] = [];
  let unresolved = 0;
  const re = /<image\b[^>]*>/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(src))) {
    const tag = m[0];
    const data = /data:image\/(png|jpe?g|webp);base64,([A-Za-z0-9+/=]+)/.exec(tag);
    if (data) {
      const buf = Buffer.from(data[2], 'base64');
      const size = data[1] === 'png' ? pngSize(buf) : data[1] === 'webp' ? null : jpegSize(buf);
      if (size) {
        rasters.push({...size, how: 'decoded base64'});
        continue;
      }
    }
    const ext = /(?:xlink:)?href="([^"]+\.(?:png|jpe?g|webp))"/i.exec(tag);
    if (ext) {
      const abs = path.join(dir, path.basename(ext[1]));
      if (fs.existsSync(abs)) {
        const buf = fs.readFileSync(abs);
        const size = abs.toLowerCase().endsWith('.png') ? pngSize(buf) : jpegSize(buf);
        if (size) {
          rasters.push({...size, how: 'external file'});
          continue;
        }
      }
    }
    // Fall back to the declared presentation size, but flag that we could not
    // prove the real bitmap resolution.
    const w = Number(/width="([\d.]+)"/.exec(tag)?.[1] ?? 0);
    const h = Number(/height="([\d.]+)"/.exec(tag)?.[1] ?? 0);
    if (w > 0 && h > 0) rasters.push({w, h, how: 'declared size (unverified)'});
    else unresolved += 1;
  }
  return {rasters, unresolved};
}

// ---- checks ---------------------------------------------------------------

const hashes = new Map<string, string>();
const seen = new Set<string>();

const minRatio = typeof manifest.min_scale_ratio === 'number' ? manifest.min_scale_ratio : DEFAULT_MIN_SCALE_RATIO;

for (const a of manifest.assets ?? []) {
  const file = a.file;
  if (!file) {
    issues.push('asset entry without a "file"');
    continue;
  }
  if (seen.has(file)) issues.push(`duplicate manifest entry: ${file}`);
  seen.add(file);

  for (const field of ['type', 'source', 'owner', 'attribution', 'use'] as const) {
    if (!a[field]) issues.push(`${file}: missing "${field}"`);
  }
  if (a.source && !/^https:\/\//.test(a.source)) issues.push(`${file}: source is not an https URL`);

  const abs = path.join(dir, file);
  if (!fs.existsSync(abs)) {
    issues.push(`${file}: file missing on disk`);
    continue;
  }
  const ext = path.extname(file).toLowerCase();
  if (!SUPPORTED.has(ext)) issues.push(`${file}: unsupported format ${ext}`);

  const buf = fs.readFileSync(abs);
  const hash = crypto.createHash('sha256').update(buf).digest('hex');
  const prior = hashes.get(hash);
  if (prior) issues.push(`${file}: byte-identical duplicate of ${prior}`);
  else hashes.set(hash, file);

  if (buf.length === 0) issues.push(`${file}: zero-byte file`);

  // ---- intrinsic resolution ----------------------------------------------
  // For an SVG we care about the real bitmap it wraps, not the viewBox.
  let intrinsic: {w: number; h: number} | null = null;
  let isVector = false;
  if (ext === '.svg') {
    const info = svgInfo(buf.toString('utf8'), dir);
    if (info.unresolved > 0) issues.push(`${file}: ${info.unresolved} embedded image(s) could not be resolved`);
    const unverified = info.rasters.filter((r) => r.how.includes('unverified'));
    for (const u of unverified) {
      warnings.push(`${file}: embedded raster size not provable (used declared ${u.w}x${u.h}); decode the data URI to verify`);
    }
    const proven = info.rasters.filter((r) => !r.how.includes('unverified'));
    if (proven.length === 0 && unverified.length === 0) {
      isVector = true;
    } else {
      intrinsic = (proven.length ? proven : unverified).reduce((m, d) => (Math.min(d.w, d.h) > Math.min(m.w, m.h) ? d : m));
    }
  } else {
    intrinsic = ext === '.png' ? pngSize(buf) : jpegSize(buf);
    if (!intrinsic) warnings.push(`${file}: could not read raster dimensions (format probe failed)`);
  }

  if (intrinsic && Math.min(intrinsic.w, intrinsic.h) < MIN_RASTER_SHORT_EDGE) {
    issues.push(`${file}: ${intrinsic.w}x${intrinsic.h} is below the ${MIN_RASTER_SHORT_EDGE}px short-edge floor`);
  }

  // ---- rendered scale and crop -------------------------------------------
  if (a.rendered === null) {
    // Catalogued but not placed; nothing to prove.
  } else if (a.rendered === undefined) {
    warnings.push(`${file}: no "rendered" size declared, so upscaling cannot be checked`);
  } else if (intrinsic) {
    const ratio = Math.min(intrinsic.w / a.rendered.w, intrinsic.h / a.rendered.h);
    if (ratio < minRatio) {
      issues.push(`${file}: rendered ${a.rendered.w}x${a.rendered.h} from ${intrinsic.w}x${intrinsic.h} is ${ratio.toFixed(2)}x, below the ${minRatio}x floor (upscaled)`);
    }
    const ia = intrinsic.w / intrinsic.h;
    const ra = a.rendered.w / a.rendered.h;
    if (Math.abs(ia - ra) / ia > ASPECT_TOLERANCE) {
      warnings.push(`${file}: rendered aspect ${ra.toFixed(2)} vs intrinsic ${ia.toFixed(2)} suggests cropping`);
    }
  } else if (!isVector) {
    warnings.push(`${file}: rendered scale not verified (no intrinsic size)`);
  }
}

// A manifest that rejects an asset should say why.
for (const r of manifest.rejected ?? []) {
  if (!r.reason) warnings.push(`rejected asset ${r.file ?? '(unnamed)'} has no reason recorded`);
}

// ---- report ---------------------------------------------------------------

console.log(`Media quality: ${video}, ${(manifest.assets ?? []).length} asset(s), ${hashes.size} unique`);
for (const w of warnings) console.log(`  [warn] ${w}`);
for (const i of issues) console.log(`  [error] ${i}`);
console.log(`  errors=${issues.length}  warnings=${warnings.length}`);
process.exit(issues.length > 0 ? 1 : 0);
