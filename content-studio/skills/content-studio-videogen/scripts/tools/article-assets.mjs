// Reusable article-asset fetcher for source-driven videos.
//
//   videogen source fetch <url> [--slug name] [--out <dir>] [--min-short-edge N] [--slugs a,b] [--all]
//
// Output (default: <sourceCacheDir>/<slug>):
//
//   article.html        raw source page
//   metadata.json       title, publisher, date, canonical url, extracted links
//   images/             downloaded image assets (png/jpg/webp/gif/svg/avif)
//   videos/             downloaded video assets (mp4/webm)
//   screenshots/        (empty; filled by the caller when it captures renders)
//   manifest.json       per-asset provenance, intrinsic size, hash, status
//
// External source media is RUNTIME-ONLY: it is fetched into a gitignored cache
// (sourceCacheDir in videogen.config.ts) and resolved at render time through a committed
// source manifest. Downloaded binaries must never be committed. Pass --out to
// reuse the tool for any article; --slug names the cache folder (defaults to a
// slug derived from the URL).
//
// The tool is dependency-free (Node 20+ global fetch) and deterministic: it
// records, for every asset, the page it came from, the upstream owner, the
// intrinsic pixel size, a sha256, and whether the asset clears the minimum
// raster short edge so a video's media-quality gate can reason about it.
//
// By default site chrome (nav/icon/logo SVGs) is skipped and lower-resolution
// `width-*` variants are superseded by their largest sibling, so the cache holds
// content media only. Pass --all to keep everything.

import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const USAGE = `Usage: videogen source fetch <url> [--slug name] [--out <dir>] [--min-short-edge N] [--slugs name,name] [--all]`;

const argv = process.argv.slice(2);
const command = argv[0];
if (command !== 'fetch') {
  console.error(USAGE);
  process.exit(1);
}

function flag(name, fallback = null) {
  const prefix = `--${name}=`;
  const index = argv.findIndex((a) => a === `--${name}` || a.startsWith(prefix));
  if (index < 0) return fallback;
  const arg = argv[index];
  if (arg.startsWith(prefix)) return arg.slice(prefix.length);
  const value = argv[index + 1];
  return value && !value.startsWith('--') ? value : fallback;
}

const sourceUrl = argv[1];
if (!sourceUrl || !/^https?:/.test(sourceUrl)) {
  console.error(USAGE);
  process.exit(1);
}
// Slug for the cache folder: --slug wins, else a readable stem from the URL.
function slugFromUrl(url) {
  try {
    const u = new URL(url);
    const parts = u.pathname.split('/').filter(Boolean);
    const stem = (parts[parts.length - 1] ?? u.hostname).replace(/\.[a-z0-9]+$/i, '');
    const slug = stem.replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 48);
    return slug || u.hostname.replace(/[^A-Za-z0-9._-]+/g, '-');
  } catch {
    return 'article';
  }
}
const explicitOut = flag('out', null);
const slug = flag('slug', slugFromUrl(sourceUrl));
const outDir = path.resolve(explicitOut ?? path.join(process.env.VIDEOGEN_SOURCE_CACHE_DIR ?? 'tmp/source-assets', slug));
const minShortEdge = Number(flag('min-short-edge', '1200'));
const onlySlugs = (flag('slugs', '') || '').split(',').map((s) => s.trim()).filter(Boolean);
const keepAll = argv.includes('--all');

const decode = (value) =>
  String(value)
    .replace(/&amp;/g, '&')
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&nbsp;/g, ' ')
    .replace(/&#x2F;/g, '/');

const meta = (html, name) => {
  const patterns = [
    new RegExp(`<meta[^>]+property=["']${name}["'][^>]+content=["']([^"']+)["']`, 'i'),
    new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+property=["']${name}["']`, 'i'),
    new RegExp(`<meta[^>]+name=["']${name}["'][^>]+content=["']([^"']+)["']`, 'i'),
    new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]+name=["']${name}["']`, 'i'),
  ];
  for (const re of patterns) {
    const m = html.match(re);
    if (m) return decode(m[1]).trim();
  }
  return null;
};

function tagAttr(tag, attr) {
  const m = tag.match(new RegExp(`${attr}=["']([^"']+)["']`, 'i'));
  return m ? decode(m[1]).trim() : null;
}

function extensionFor(url, contentType) {
  const clean = url.split('?')[0].split('#')[0];
  const ext = path.extname(clean).toLowerCase();
  if (['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.avif', '.mp4', '.webm', '.mov'].includes(ext)) return ext;
  const type = (contentType || '').split(';')[0].trim();
  const byType = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/webp': '.webp',
    'image/gif': '.gif',
    'image/svg+xml': '.svg',
    'image/avif': '.avif',
    'video/mp4': '.mp4',
    'video/webm': '.webm',
  };
  return byType[type] ?? '.bin';
}

// Build a stable, human-readable file name: host path stem + short hash, so
// repeated fetches never collide and duplicates remain detectable by hash.
function fileNameFor(url, contentType) {
  const ext = extensionFor(url, contentType);
  const clean = url.split('?')[0].split('#')[0];
  const stem = decodeURIComponent(path.basename(clean, path.extname(clean)))
    .replace(/[^A-Za-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60) || 'asset';
  const hash = crypto.createHash('sha1').update(url).digest('hex').slice(0, 8);
  return `${stem}-${hash}${ext}`;
}

function intrinsicSize(buf, ext) {
  try {
    if (ext === '.svg') {
      const text = buf.toString('utf8', 0, Math.min(buf.length, 4000));
      const viewBox = text.match(/viewBox=["']\s*([-\d.]+)[ ,]+([-\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)/i);
      const width = text.match(/\bwidth=["']([\d.]+)/i);
      const height = text.match(/\bheight=["']([\d.]+)/i);
      const embedded = text.match(/<image[^>]+width=["']([\d.]+)["'][^>]*height=["']([\d.]+)["']/i);
      if (embedded) return {w: Number(embedded[1]), h: Number(embedded[2]), vector: true, embeddedRaster: true};
      if (width && height) return {w: Number(width[1]), h: Number(height[1]), vector: true};
      if (viewBox) return {w: Number(viewBox[3]), h: Number(viewBox[4]), vector: true};
      return null;
    }
    if (buf.length > 24 && buf.readUInt32BE(0) === 0x89504e47) return {w: buf.readUInt32BE(16), h: buf.readUInt32BE(20)};
    if (buf.length > 4 && buf[0] === 0xff && buf[1] === 0xd8) {
      let offset = 2;
      while (offset + 9 < buf.length) {
        if (buf[offset] !== 0xff) {
          offset += 1;
          continue;
        }
        const marker = buf[offset + 1];
        const size = buf.readUInt16BE(offset + 2);
        if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
          return {w: buf.readUInt16BE(offset + 7), h: buf.readUInt16BE(offset + 5)};
        }
        offset += 2 + size;
      }
      return null;
    }
    if (buf.length > 30 && buf.toString('ascii', 0, 4) === 'RIFF' && buf.toString('ascii', 8, 12) === 'WEBP') {
      const kind = buf.toString('ascii', 12, 16);
      if (kind === 'VP8X') {
        const w = 1 + ((buf[24] << 16) | (buf[25] << 8) | buf[26]);
        const h = 1 + ((buf[27] << 16) | (buf[28] << 8) | buf[29]);
        return {w, h};
      }
      if (kind === 'VP8 ') return {w: buf.readUInt16LE(26) & 0x3fff, h: buf.readUInt16LE(28) & 0x3fff};
      if (kind === 'VP8L') {
        const bits = buf.readUInt32LE(21);
        return {w: (bits & 0x3fff) + 1, h: ((bits >> 14) & 0x3fff) + 1};
      }
      return null;
    }
    if (buf.length > 10 && buf.readUInt16BE(0) === 0x4749) return {w: buf.readUInt16LE(6), h: buf.readUInt16LE(8)};
    return null;
  } catch {
    return null;
  }
}

async function download(url, referer) {
  const response = await fetch(url, {
    headers: {
      'user-agent': 'Mozilla/5.0 (compatible; ReviseLabsArticleAssets/1.0; +https://reviselabs.local)',
      accept: '*/*',
      ...(referer ? {referer} : {}),
    },
    redirect: 'follow',
  });
  if (!response.ok) return {ok: false, status: response.status};
  const buffer = Buffer.from(await response.arrayBuffer());
  return {ok: true, status: response.status, buffer, contentType: response.headers.get('content-type')};
}

const response = await download(sourceUrl);
if (!response.ok) {
  console.error(`Failed to fetch ${sourceUrl} (HTTP ${response.status})`);
  process.exit(1);
}
const html = response.buffer.toString('utf8');

// ---- metadata --------------------------------------------------------------

const titleText = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]?.trim();
const canonical = html.match(/<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']+)["']/i)?.[1] ?? sourceUrl;
const published = meta(html, 'article:published_time') ?? meta(html, 'datePublished') ?? meta(html, 'date');
const metadata = {
  url: sourceUrl,
  canonical: decode(canonical),
  title: meta(html, 'og:title') ?? (titleText ? decode(titleText) : null),
  description: meta(html, 'og:description') ?? meta(html, 'description'),
  siteName: meta(html, 'og:site_name'),
  publisher: meta(html, 'og:site_name') ?? meta(html, 'author'),
  published,
  author: meta(html, 'author') ?? meta(html, 'article:author'),
  fetchedFrom: sourceUrl,
  fetchedAt: new Date().toISOString(),
  minShortEdge,
};

// ---- asset discovery -------------------------------------------------------

const candidates = new Map(); // absolute url -> {kind, tag, alt, note}
const addCandidate = (rawUrl, kind, info = {}) => {
  if (!rawUrl) return;
  let absolute;
  try {
    absolute = new URL(rawUrl, sourceUrl).href;
  } catch {
    return;
  }
  if (!/^https?:/.test(absolute)) return;
  if (/\.(css|js|json|woff2?|ttf|ico)(\?|$)/i.test(absolute)) return;
  if (!candidates.has(absolute)) candidates.set(absolute, {kind, ...info});
};

for (const tag of html.match(/(<(?:img|source|video|iframe)\b[^>]*>)/gi) ?? []) {
  const src = tagAttr(tag, 'src');
  const poster = tagAttr(tag, 'poster');
  const alt = tagAttr(tag, 'alt');
  const dataSrc = tagAttr(tag, 'data-src');
  const srcset = tagAttr(tag, 'srcset');
  const type = tagAttr(tag, 'type');
  const isVideo = /^<video/i.test(tag) || (type ?? '').startsWith('video') || /\.(mp4|webm)(\?|$)/i.test(src ?? '');
  for (const value of [src, dataSrc, poster]) addCandidate(value, value === poster ? 'image' : isVideo ? 'video' : 'image', {alt, fromTag: tag.slice(0, 80)});
  if (srcset) {
    const best = srcset
      .split(',')
      .map((part) => part.trim().split(/\s+/))
      .map(([u, d]) => ({u, w: Number((d ?? '').replace(/\D/g, '')) || 0}))
      .sort((a, b) => b.w - a.w)[0];
    addCandidate(best?.u, 'image', {alt, fromTag: 'srcset'});
  }
}
addCandidate(meta(html, 'og:image'), 'image', {alt: 'og:image'});
addCandidate(meta(html, 'twitter:image'), 'image', {alt: 'twitter:image'});

const assets = [];
fs.mkdirSync(path.join(outDir, 'images'), {recursive: true});
fs.mkdirSync(path.join(outDir, 'videos'), {recursive: true});
fs.mkdirSync(path.join(outDir, 'screenshots'), {recursive: true});

const hashSeen = new Map();

// Site chrome (navigation icons, logos, favicons, sprite sheets) is not article
// content. It is skipped by default so the cache holds media the video could
// actually cite; --all keeps everything.
const CHROME = /(^|[\/_.-])(nav|navigation|logo|icon|icons|sprite|favicon|wordmark|googleg|hamburger|search)([\/_.-]|$)/i;
const isChrome = (url, alt) => {
  const clean = decodeURIComponent(url.split('?')[0].split('#')[0]);
  const base = clean.split('/').pop() ?? '';
  return CHROME.test(base) || CHROME.test(String(alt ?? ''));
};

// Lower-resolution `width-*`/`format-*` variants of the same image share a stem
// once the hash and variant segments are stripped, so they collapse to the
// largest sibling. This is a filename heuristic, not pixel comparison.
const variantStem = (relFile) => {
  const dir = path.dirname(relFile).replace(/\\/g, '/');
  const base = path.basename(relFile, path.extname(relFile));
  const stem = base
    .replace(/-[0-9a-f]{8}$/i, '')
    .replace(/\.(width|height|format|quality)-\S+$/i, '')
    .replace(/-[0-9a-f]{8}$/i, '');
  return `${dir}/${stem}`.toLowerCase();
};

for (const [url, info] of candidates) {
  if (onlySlugs.length > 0 && !onlySlugs.some((slug) => url.includes(slug))) continue;
  if (!keepAll && isChrome(url, info.alt)) {
    assets.push({url, kind: info.kind, status: 'skipped', reason: 'site chrome (nav/icon/logo)'});
    continue;
  }
  let result;
  try {
    result = await download(url, sourceUrl);
  } catch (error) {
    assets.push({url, kind: info.kind, status: 'failed', error: String(error?.message ?? error)});
    continue;
  }
  if (!result.ok) {
    assets.push({url, kind: info.kind, status: 'failed', httpStatus: result.status});
    continue;
  }
  const ext = extensionFor(url, result.contentType);
  const dir = info.kind === 'video' || ['.mp4', '.webm', '.mov'].includes(ext) ? 'videos' : 'images';
  if (!['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.avif'].includes(ext)) {
    assets.push({url, kind: info.kind, status: 'skipped', reason: `unsupported type ${result.contentType ?? ext}`});
    continue;
  }
  const name = fileNameFor(url, result.contentType);
  const file = path.join(outDir, dir, name);
  fs.writeFileSync(file, result.buffer);

  const size = intrinsicSize(result.buffer, ext);
  const sha256 = crypto.createHash('sha256').update(result.buffer).digest('hex');
  const duplicateOf = hashSeen.get(sha256) ?? null;
  if (!duplicateOf) hashSeen.set(sha256, path.relative(outDir, file).replace(/\\/g, '/'));
  const shortEdge = size ? Math.min(size.w, size.h) : null;
  assets.push({
    url,
    kind: info.kind,
    status: 'downloaded',
    file: path.relative(outDir, file).replace(/\\/g, '/'),
    bytes: result.buffer.length,
    contentType: result.contentType ?? null,
    intrinsic: size ? `${size.w}x${size.h}${size.vector ? ' (vector)' : ''}` : null,
    shortEdge,
    minShortEdgeOk: shortEdge == null ? null : shortEdge >= minShortEdge || Boolean(size?.vector),
    sha256,
    duplicateOf,
    alt: info.alt ?? null,
  });
  console.log(`${dir === 'images' ? 'image' : 'video'}  ${name}  ${size ? `${size.w}x${size.h}` : 'size unknown'}  ${Math.round(result.buffer.length / 1024)}KB`);
}

// Collapse resolution variants: within a stem group keep the largest sibling
// (by short edge) and delete the rest, so the cache holds one copy per image.
const variantGroups = new Map();
for (const a of assets) {
  if (a.status !== 'downloaded' || !a.file) continue;
  const key = variantStem(a.file);
  const list = variantGroups.get(key) ?? [];
  list.push(a);
  variantGroups.set(key, list);
}
for (const list of variantGroups.values()) {
  if (list.length < 2) continue;
  const ranked = [...list].sort((a, b) => (b.shortEdge ?? -1) - (a.shortEdge ?? -1));
  const winner = ranked[0];
  for (const a of ranked.slice(1)) {
    a.status = 'superseded';
    a.supersededBy = winner.file;
    const abs = path.join(outDir, a.file);
    if (fs.existsSync(abs)) fs.rmSync(abs);
    a.removed = true;
  }
}

fs.writeFileSync(path.join(outDir, 'article.html'), html);
fs.writeFileSync(path.join(outDir, 'metadata.json'), JSON.stringify(metadata, null, 2) + '\n');
fs.writeFileSync(
  path.join(outDir, 'manifest.json'),
  JSON.stringify(
    {
      article: metadata,
      slug,
      cacheDir: path.relative(process.cwd(), outDir).replace(/\\/g, '/'),
      note: 'Runtime-only source cache. Binaries are gitignored; only the curated manifest is committed.',
      minShortEdge,
      duplicates: [...hashSeen.values()].length !== assets.filter((a) => a.status === 'downloaded').length ? 'see duplicateOf per asset' : 'none',
      assets,
    },
    null,
    2,
  ) + '\n',
);

const downloaded = assets.filter((a) => a.status === 'downloaded');
const usable = downloaded.filter((a) => a.minShortEdgeOk);
const skipped = assets.filter((a) => a.status === 'skipped');
const superseded = assets.filter((a) => a.status === 'superseded');
console.log(`\nFetched ${downloaded.length} assets (${usable.length} clear the ${minShortEdge}px short-edge floor) from ${sourceUrl}`);
if (skipped.length) console.log(`Skipped ${skipped.length} (site chrome / unsupported)`);
if (superseded.length) console.log(`Superseded ${superseded.length} lower-resolution variant(s)`);
console.log(`Output: ${path.relative(process.cwd(), outDir)}  (gitignored cache)`);
