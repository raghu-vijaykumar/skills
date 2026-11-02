import Parser from 'rss-parser';
import {getText} from './http.mjs';

const parser = new Parser();

function decodeEntities(text) {
  return text.replace(/&(#\d+|#x[0-9a-f]+|[a-z]+);/gi, (match, entity) => {
    const named = {
      amp: '&',
      lt: '<',
      gt: '>',
      quot: '"',
      apos: "'",
      nbsp: ' ',
    };
    if (entity[0] === '#') {
      const code = entity[1].toLowerCase() === 'x'
        ? parseInt(entity.slice(2), 16)
        : parseInt(entity.slice(1), 10);
      return Number.isFinite(code) ? String.fromCodePoint(code) : match;
    }
    return named[entity.toLowerCase()] ?? match;
  });
}

function cleanTitle(raw) {
  if (!raw) return '';
  return decodeEntities(String(raw))
    .replace(/<[^>]+>/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function parseDate(item) {
  const candidate = item.isoDate ?? item.pubDate ?? item.published ?? item.updated;
  if (!candidate) return null;
  const date = new Date(candidate);
  return Number.isNaN(date.getTime()) ? null : date;
}

export async function fetchFeed(source, {since, timeoutMs = 15000} = {}) {
  const xml = await getText(source.url, {
    timeoutMs,
    headers: {Accept: 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'},
  });
  const feed = await parser.parseString(xml);
  const items = [];
  for (const item of feed.items ?? []) {
    const title = cleanTitle(item.title);
    const url = item.link ?? item.guid;
    if (!title || !url) continue;
    const published = parseDate(item);
    // Undated items (rare) are kept only when no window is set; they sort last.
    if (since && published && published < since) continue;
    items.push({title, url, source: source.name, topic: source.topic, published});
  }
  return items;
}
