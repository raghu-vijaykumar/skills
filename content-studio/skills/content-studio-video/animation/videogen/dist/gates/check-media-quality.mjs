import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
const MIN_RASTER_SHORT_EDGE = 1200;
const DEFAULT_MIN_SCALE_RATIO = 1;
const SUPPORTED = /* @__PURE__ */ new Set([".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]);
const ASPECT_TOLERANCE = 0.2;
const video = process.argv[2];
if (!video) {
  console.error("Usage: node scripts/check-media-quality.mts <video-id>");
  process.exit(1);
}
const dir = path.resolve(process.env.VIDEOGEN_VIDEOS_DIR ?? "videos", video, "assets", "media");
const manifestPath = path.join(dir, "manifest.json");
if (!fs.existsSync(manifestPath)) {
  console.log(`Media quality: ${video} skipped (no media manifest)`);
  process.exit(0);
}
const issues = [];
const warnings = [];
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
if (!Array.isArray(manifest.assets) || manifest.assets.length === 0) {
  issues.push("manifest has no assets");
}
if (!manifest.policy || manifest.policy.trim().length < 20) {
  warnings.push("manifest has no stated sourcing policy");
}
function pngSize(buf) {
  if (buf.length < 24 || buf.readUInt32BE(0) !== 2303741511) return null;
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}
function jpegSize(buf) {
  if (buf.length < 4 || buf.readUInt16BE(0) !== 65496) return null;
  let o = 2;
  while (o + 9 < buf.length) {
    if (buf[o] !== 255) {
      o += 1;
      continue;
    }
    const marker = buf[o + 1];
    const len = buf.readUInt16BE(o + 2);
    if (marker >= 192 && marker <= 207 && marker !== 196 && marker !== 200 && marker !== 204) {
      return { h: buf.readUInt16BE(o + 5), w: buf.readUInt16BE(o + 7) };
    }
    o += 2 + len;
  }
  return null;
}
function svgInfo(src, dir2) {
  const rasters = [];
  let unresolved = 0;
  const re = /<image\b[^>]*>/g;
  let m;
  while (m = re.exec(src)) {
    const tag = m[0];
    const data = /data:image\/(png|jpe?g|webp);base64,([A-Za-z0-9+/=]+)/.exec(tag);
    if (data) {
      const buf = Buffer.from(data[2], "base64");
      const size = data[1] === "png" ? pngSize(buf) : data[1] === "webp" ? null : jpegSize(buf);
      if (size) {
        rasters.push({ ...size, how: "decoded base64" });
        continue;
      }
    }
    const ext = /(?:xlink:)?href="([^"]+\.(?:png|jpe?g|webp))"/i.exec(tag);
    if (ext) {
      const abs = path.join(dir2, path.basename(ext[1]));
      if (fs.existsSync(abs)) {
        const buf = fs.readFileSync(abs);
        const size = abs.toLowerCase().endsWith(".png") ? pngSize(buf) : jpegSize(buf);
        if (size) {
          rasters.push({ ...size, how: "external file" });
          continue;
        }
      }
    }
    const w = Number(/width="([\d.]+)"/.exec(tag)?.[1] ?? 0);
    const h = Number(/height="([\d.]+)"/.exec(tag)?.[1] ?? 0);
    if (w > 0 && h > 0) rasters.push({ w, h, how: "declared size (unverified)" });
    else unresolved += 1;
  }
  return { rasters, unresolved };
}
const hashes = /* @__PURE__ */ new Map();
const seen = /* @__PURE__ */ new Set();
const minRatio = typeof manifest.min_scale_ratio === "number" ? manifest.min_scale_ratio : DEFAULT_MIN_SCALE_RATIO;
for (const a of manifest.assets ?? []) {
  const file = a.file;
  if (!file) {
    issues.push('asset entry without a "file"');
    continue;
  }
  if (seen.has(file)) issues.push(`duplicate manifest entry: ${file}`);
  seen.add(file);
  for (const field of ["type", "source", "owner", "attribution", "use"]) {
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
  const hash = crypto.createHash("sha256").update(buf).digest("hex");
  const prior = hashes.get(hash);
  if (prior) issues.push(`${file}: byte-identical duplicate of ${prior}`);
  else hashes.set(hash, file);
  if (buf.length === 0) issues.push(`${file}: zero-byte file`);
  let intrinsic = null;
  let isVector = false;
  if (ext === ".svg") {
    const info = svgInfo(buf.toString("utf8"), dir);
    if (info.unresolved > 0) issues.push(`${file}: ${info.unresolved} embedded image(s) could not be resolved`);
    const unverified = info.rasters.filter((r) => r.how.includes("unverified"));
    for (const u of unverified) {
      warnings.push(`${file}: embedded raster size not provable (used declared ${u.w}x${u.h}); decode the data URI to verify`);
    }
    const proven = info.rasters.filter((r) => !r.how.includes("unverified"));
    if (proven.length === 0 && unverified.length === 0) {
      isVector = true;
    } else {
      intrinsic = (proven.length ? proven : unverified).reduce((m, d) => Math.min(d.w, d.h) > Math.min(m.w, m.h) ? d : m);
    }
  } else {
    intrinsic = ext === ".png" ? pngSize(buf) : jpegSize(buf);
    if (!intrinsic) warnings.push(`${file}: could not read raster dimensions (format probe failed)`);
  }
  if (intrinsic && Math.min(intrinsic.w, intrinsic.h) < MIN_RASTER_SHORT_EDGE) {
    issues.push(`${file}: ${intrinsic.w}x${intrinsic.h} is below the ${MIN_RASTER_SHORT_EDGE}px short-edge floor`);
  }
  if (a.rendered === null) {
  } else if (a.rendered === void 0) {
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
for (const r of manifest.rejected ?? []) {
  if (!r.reason) warnings.push(`rejected asset ${r.file ?? "(unnamed)"} has no reason recorded`);
}
console.log(`Media quality: ${video}, ${(manifest.assets ?? []).length} asset(s), ${hashes.size} unique`);
for (const w of warnings) console.log(`  [warn] ${w}`);
for (const i of issues) console.log(`  [error] ${i}`);
console.log(`  errors=${issues.length}  warnings=${warnings.length}`);
process.exit(issues.length > 0 ? 1 : 0);
