import {getText} from './http.mjs';

// Generic listing scraper. Mirrors the approach in raghu-vijaykumar/tools
// (newsletter/src/newsletter/scraper.py): load a listing page, collect article
// links that match the source's `urlPrefixes` (minus `excludePrefixes` /
// `excludePatterns`), then resolve a title and date for each link. Unlike the
// Python version we only need title + link, so static fetch is usually enough;
// an article is only fetched when the listing gives no usable title or date.

const MONTHS = {
  jan: 0, feb: 1, mar: 2, apr: 3, may: 4, jun: 5,
  jul: 6, aug: 7, sep: 8, oct: 9, nov: 10, dec: 11,
};

const GENERIC_TITLE =
  /^(read more|read now|learn more|view|view all|details|more|see more|continue reading|next|previous|subscribe|all posts|archive|blog|publications|home|news|categories|topics)$/i;

function decodeEntities(text) {
  return String(text)
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCodePoint(parseInt(code, 16)))
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&nbsp;/g, ' ');
}

function stripTags(html) {
  return decodeEntities(String(html).replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim();
}

function metaContent(html, property) {
  const patterns = [
    new RegExp(`<meta[^>]+(?:property|name)=["']${property}["'][^>]*content=["']([^"']+)["']`, 'i'),
    new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]*(?:property|name)=["']${property}["']`, 'i'),
  ];
  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match) return decodeEntities(match[1]).trim();
  }
  return null;
}

function metaTitle(html) {
  return (
    metaContent(html, 'og:title') ??
    metaContent(html, 'twitter:title') ??
    (html.match(/<title[^>]*>([\s\S]*?)<\/title>/i) ?? [])[1] ??
    (html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i) ?? [])[1] ??
    null
  );
}

function toDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function dateFromText(text) {
  if (!text) return null;
  let match = text.match(/\b(20\d{2})-(\d{2})-(\d{2})\b/);
  if (match) return toDate(`${match[1]}-${match[2]}-${match[3]}T00:00:00Z`);
  match = text.match(/\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d{2})\b/);
  if (match && MONTHS[match[1].slice(0, 3).toLowerCase()] !== undefined) {
    return new Date(Date.UTC(Number(match[3]), MONTHS[match[1].slice(0, 3).toLowerCase()], Number(match[2])));
  }
  match = text.match(/\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(20\d{2})\b/);
  if (match && MONTHS[match[2].slice(0, 3).toLowerCase()] !== undefined) {
    return new Date(Date.UTC(Number(match[3]), MONTHS[match[2].slice(0, 3).toLowerCase()], Number(match[1])));
  }
  return null;
}

function dateFromUrl(url) {
  let match = url.match(/\/(20\d{2})\/(\d{1,2})\/(\d{1,2})(?:[/-]|$)/);
  if (match) return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  match = url.match(/\/(20\d{2})\/(\d{1,2})(?:[/-]|$)/);
  if (match) return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, 1));
  return null;
}

function metaDate(html) {
  for (const property of ['article:published_time', 'og:published_time', 'datePublished', 'date', 'pubdate', 'DC.date']) {
    const value = metaContent(html, property);
    const date = toDate(value);
    if (date) return date;
  }
  const jsonLd = html.match(/"datePublished"\s*:\s*"([^"]+)"/i);
  if (jsonLd) {
    const date = toDate(jsonLd[1]);
    if (date) return date;
  }
  const datetime = html.match(/<time[^>]+datetime=["']([^"']+)["']/i);
  return datetime ? toDate(datetime[1]) : null;
}

function titleFromInner(inner) {
  const heading = inner.match(/<h[1-6][^>]*>([\s\S]*?)<\/h[1-6]>/i);
  let candidate = stripTags(heading ? heading[1] : inner);
  candidate = candidate
    .replace(/^\[[^\]]{1,12}\]\s*/, '')
    .replace(/^\d{4}[.-]\d{1,2}[.-]\d{1,2}\s+/, '')
    .trim();
  if (!candidate || candidate.length < 8 || GENERIC_TITLE.test(candidate)) return null;
  return candidate;
}

function extractLinks(html, source) {
  const urlPrefixes = source.urlPrefixes ?? [];
  const excludePrefixes = source.excludePrefixes ?? [];
  const excludePatterns = (source.excludePatterns ?? []).map((pattern) => new RegExp(pattern, 'i'));
  const base = source.baseUrl;
  const links = [];
  const seen = new Set();
  const anchor = /<a\b[^>]*href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let match;
  while ((match = anchor.exec(html)) !== null) {
    let url;
    try {
      const parsed = new URL(match[1], base);
      parsed.hash = '';
      parsed.search = '';
      url = parsed.toString();
    } catch {
      continue;
    }
    if (url === base || url === base.replace(/\/$/, '') || seen.has(url)) continue;
    // Skip section/index pages that are just the prefix itself.
    if (urlPrefixes.some((prefix) => url === prefix || url === `${prefix}/`)) continue;
    if (urlPrefixes.length && !urlPrefixes.some((prefix) => url.startsWith(prefix))) continue;
    const excluded = (list) =>
      list.some((prefix) => url === prefix || url === prefix.replace(/\/$/, '') || url.startsWith(prefix));
    if (excluded(excludePrefixes)) continue;
    if (excludePatterns.some((pattern) => pattern.test(url))) continue;
    seen.add(url);
    const window = html.slice(Math.max(0, match.index - 300), match.index + match[0].length + 400);
    links.push({
      url,
      title: titleFromInner(match[2]),
      published: dateFromUrl(url) ?? dateFromText(stripTags(window)),
    });
  }
  return links;
}

async function mapLimit(items, limit, worker) {
  const results = new Array(items.length);
  let cursor = 0;
  async function run() {
    while (cursor < items.length) {
      const index = cursor;
      cursor += 1;
      results[index] = await worker(items[index], index);
    }
  }
  await Promise.all(Array.from({length: Math.min(limit, items.length)}, run));
  return results;
}

function matches(url, source) {
  const urlPrefixes = source.urlPrefixes ?? [];
  const excludePrefixes = source.excludePrefixes ?? [];
  const excludePatterns = (source.excludePatterns ?? []).map((pattern) => new RegExp(pattern, 'i'));
  if (urlPrefixes.some((prefix) => url === prefix || url === `${prefix}/`)) return false;
  if (urlPrefixes.length && !urlPrefixes.some((prefix) => url.startsWith(prefix))) return false;
  if (excludePrefixes.some((prefix) => url === prefix || url === prefix.replace(/\/$/, '') || url.startsWith(prefix))) {
    return false;
  }
  if (excludePatterns.some((pattern) => pattern.test(url))) return false;
  return true;
}

function parseUrlset(xml) {
  const entries = [];
  const blockRe = /<url>([\s\S]*?)<\/url>/gi;
  let match;
  while ((match = blockRe.exec(xml)) !== null) {
    const loc = (match[1].match(/<loc>\s*([^<]+?)\s*<\/loc>/i) ?? [])[1];
    if (!loc) continue;
    const lastmod = (match[1].match(/<lastmod>\s*([^<]+?)\s*<\/lastmod>/i) ?? [])[1];
    entries.push({loc: decodeEntities(loc), lastmod: toDate(lastmod)});
  }
  return entries;
}

// Sitemap-based discovery for sites whose listings are rendered in JavaScript
// (Uber, Apple ML, Anthropic, …): read the sitemap (following a sitemap index),
// filter by the source's urlPrefixes, then fetch the newest articles for titles.
export async function fetchSitemap(source, {since, maxItems = source.maxItems ?? 15} = {}) {
  const root = await getText(source.sitemapUrl, {timeoutMs: 25000});
  let entries;
  if (/<sitemapindex[\s>]/i.test(root)) {
    const children = [...root.matchAll(/<loc>\s*([^<]+?)\s*<\/loc>/gi)].map((match) => match[1].trim());
    const chosen = children.slice(0, source.maxSitemaps ?? 10);
    const docs = await Promise.all(chosen.map((url) => getText(url, {timeoutMs: 25000}).catch(() => '')));
    entries = docs.flatMap(parseUrlset);
  } else {
    entries = parseUrlset(root);
  }

  const seen = new Set();
  const clean = (loc) => loc.split('#')[0].split('?')[0];
  const candidates = entries
    .map((entry) => clean(entry.loc))
    .filter((url) => matches(url, source) && !seen.has(url) && seen.add(url));

  const datedMatches = entries
    .filter((entry) => entry.lastmod && matches(clean(entry.loc), source))
    .sort((a, b) => b.lastmod - a.lastmod)
    .map((entry) => clean(entry.loc));
  const ordered = datedMatches.length ? datedMatches : candidates;
  const selected = [...new Set(ordered)].slice(0, maxItems);

  const items = await mapLimit(selected, 6, async (url) => {
    let title = null;
    let published = (entries.find((entry) => entry.loc.startsWith(url)) ?? {}).lastmod ?? null;
    try {
      const article = await getText(url, {timeoutMs: 15000});
      title = stripTags(metaTitle(article) ?? '') || null;
      published = published ?? metaDate(article);
    } catch {
      // fall through to URL/title fallback
    }
    if (since && published && published < since) return null;
    return {title: title || url, url, source: source.name, topic: source.topic, published};
  });

  return items.filter(Boolean);
}

export async function scrapeSource(source, {since, maxItems = source.maxItems ?? 15} = {}) {
  const html = await getText(source.baseUrl, {timeoutMs: 25000});
  const links = extractLinks(html, source).slice(0, maxItems);

  const items = await mapLimit(links, 6, async (link) => {
    let title = link.title;
    let published = link.published;
    if (!title || !published) {
      try {
        const article = await getText(link.url, {timeoutMs: 15000});
        if (!title) title = stripTags(metaTitle(article) ?? '') || null;
        if (!published) published = metaDate(article) ?? dateFromText(stripTags(article).slice(0, 2000));
      } catch {
        // keep whatever the listing gave us
      }
    }
    if (since && published && published < since) return null;
    return {title: title || link.url, url: link.url, source: source.name, topic: source.topic, published};
  });

  return items.filter(Boolean);
}
