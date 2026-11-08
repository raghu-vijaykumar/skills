import {getJson} from './http.mjs';
import {applyLimit} from './util.mjs';
import {fail, ok} from './pretty.mjs';

const ARXIV_LINK = /https?:\/\/arxiv\.org\/(?:abs|pdf)\/([0-9]{4}\.[0-9]{4,5})(v\d+)?/i;

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
  return decodeEntities(String(html).replace(/<[^>]+>/g, ' '))
    .replace(/\s+/g, ' ')
    .trim();
}

function arxivFrom(text) {
  const match = String(text ?? '').match(ARXIV_LINK);
  return match ? {id: match[1], url: `https://arxiv.org/abs/${match[1]}`} : null;
}

function floorToDay(date) {
  const floored = new Date(date);
  floored.setHours(0, 0, 0, 0);
  return floored;
}

// Hugging Face Daily Papers: community-upvoted papers, the de-facto "viral AI
// papers" list. The endpoint returns the most recent ~50 entries (about two
// days) with no auth. Sorted by upvotes descending.
export async function fetchHuggingFacePapers({since, limit = 0, minUpvotes = 0} = {}) {
  const data = await getJson('https://huggingface.co/api/daily_papers', {timeoutMs: 20000});
  const entries = Array.isArray(data) ? data : (data.papers ?? []);
  const from = since ? floorToDay(since) : null;
  const papers = [];
  for (const entry of entries) {
    const paper = entry.paper ?? {};
    const id = paper.id;
    const title = paper.title ?? entry.title;
    if (!id || !title) continue;
    const featuredRaw = paper.submittedOnDailyAt ?? paper.publishedAt ?? entry.publishedAt;
    const featured = featuredRaw ? new Date(featuredRaw) : null;
    if (from && featured && featured < from) continue;
    const upvotes = paper.upvotes ?? 0;
    if (minUpvotes && upvotes < minUpvotes) continue;
    const authors = (paper.authors ?? []).map((author) => author.name).filter(Boolean);
    papers.push({
      title: stripTags(title),
      url: `https://huggingface.co/papers/${id}`,
      arxivId: id,
      score: upvotes,
      metric: `⭐ ${upvotes} upvotes · 💬 ${entry.numComments ?? 0} comments`,
      source: 'HF Daily Papers',
      author: authors[0] ?? '',
      published: featured,
    });
  }
  papers.sort((a, b) => b.score - a.score || (b.published?.getTime() ?? 0) - (a.published?.getTime() ?? 0));
  return applyLimit(papers, limit);
}

// Hacker News: papers going viral in discussion. Search recent stories that
// mention arXiv, keep the ones that actually link a paper, rank by points.
export async function fetchHnPapers({since, limit = 0, minPoints = 0} = {}) {
  const from = Math.floor((since?.getTime() ?? Date.now() - 24 * 60 * 60 * 1000) / 1000);
  // The relevance-ranked endpoint surfaces the highest-point stories in the
  // window; search_by_date only returns the most recent ones (often low-point).
  const url =
    'https://hn.algolia.com/api/v1/search?query=arxiv&tags=story' +
    `&numericFilters=${encodeURIComponent(`created_at_i>${from}`)}&hitsPerPage=100`;
  const json = await getJson(url, {timeoutMs: 20000});
  const papers = [];
  const seen = new Set();
  for (const hit of json.hits ?? []) {
    const link = arxivFrom(hit.url) ?? arxivFrom(hit.story_text);
    if (!link || seen.has(link.id)) continue;
    const points = hit.points ?? 0;
    if (minPoints && points < minPoints) continue;
    seen.add(link.id);
    papers.push({
      title: stripTags(hit.title ?? ''),
      url: link.url,
      arxivId: link.id,
      score: points,
      metric: `▲ ${points} points · 💬 ${hit.num_comments ?? 0} comments`,
      source: 'Hacker News',
      author: '',
      published: hit.created_at ? new Date(hit.created_at) : null,
    });
  }
  papers.sort((a, b) => b.score - a.score || (b.published?.getTime() ?? 0) - (a.published?.getTime() ?? 0));
  return applyLimit(papers, limit);
}

export async function collectPapers({config, since, failures = []}) {
  if (!config?.enabled) return [];
  const jobs = [];
  if (config.huggingface) {
    jobs.push(
      fetchHuggingFacePapers({since, limit: config.limit, minUpvotes: config.minUpvotes}).catch((error) => {
        failures.push({source: 'HF Daily Papers', topic: 'research', error: error.message});
        console.log(`  ${fail} HF Daily Papers: ${error.message}`);
        return [];
      }),
    );
  }
  if (config.hackernews) {
    jobs.push(
      fetchHnPapers({since, limit: config.limit, minPoints: config.minPoints}).catch((error) => {
        failures.push({source: 'Hacker News papers', topic: 'research', error: error.message});
        console.log(`  ${fail} Hacker News papers: ${error.message}`);
        return [];
      }),
    );
  }
  const results = await Promise.all(jobs);
  const papers = results.flat();
  console.log(`  ${ok} viral papers (${papers.length})`);
  return papers;
}
