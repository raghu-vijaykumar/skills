import {getJson, getText} from './http.mjs';
import {applyLimit} from './util.mjs';

function decodeEntities(text) {
  return String(text)
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&nbsp;/g, ' ');
}

function stripTags(html) {
  return decodeEntities(html.replace(/<[^>]+>/g, ' '))
    .replace(/\s+/g, ' ')
    .trim();
}

function toNumber(text) {
  const digits = String(text).replace(/[^\d]/g, '');
  return digits ? Number(digits) : null;
}

export async function fetchTrending({limit = 10, since = 'daily'} = {}) {
  const html = await getText(`https://github.com/trending?since=${since}`, {timeoutMs: 20000});
  const blocks = html.split('<article class="Box-row">').slice(1);
  const repos = [];
  for (const block of blocks) {
    const repoMatch = block.match(/<h2[\s\S]*?<a[^>]+href="\/([^"/]+\/[^"/]+)"/);
    if (!repoMatch) continue;
    const fullName = repoMatch[1];
    const text = stripTags(block);
    const description = (block.match(/<p class="col-9[^"]*"[^>]*>([\s\S]*?)<\/p>/) ?? [])[1];
    const language = (block.match(/<span itemprop="programmingLanguage">([^<]+)<\/span>/) ?? [])[1];
    const starsToday = (text.match(/([\d,]+)\s*stars?\s*today/i) ?? [])[1];
    const totalStars = (block.match(/href="\/[^"]+\/stargazers"[^>]*>([\s\S]*?)<\/a>/) ?? [])[1];
    repos.push({
      fullName,
      url: `https://github.com/${fullName}`,
      description: description ? stripTags(description) : '',
      language: language ? stripTags(language) : '',
      starsToday: starsToday ? toNumber(starsToday) : null,
      stars: totalStars ? toNumber(stripTags(totalStars)) : null,
    });
  }
  if (repos.length === 0) {
    console.log('digest: GitHub trending returned no rows (markup may have changed); skipping.');
  }
  return applyLimit(repos, limit);
}

export async function fetchNewRepos({since, token, limit = 0} = {}) {
  const from = since.toISOString().slice(0, 10);
  // stars:>500 filters the bot-farmed "pre-activated app" spam cluster that
  // sits at a few hundred stars, while keeping genuinely fast-rising repos.
  const query = `created:>=${from} stars:>500`;
  const perPage = limit && limit > 0 ? Math.min(limit, 100) : 100;
  const api =
    `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}` +
    `&sort=stars&order=desc&per_page=${perPage}`;
  const headers = token ? {Authorization: `Bearer ${token}`} : {};
  const json = await getJson(api, {headers, timeoutMs: 20000});
  return (json.items ?? []).map((repo) => ({
    fullName: repo.full_name,
    url: repo.html_url,
    description: repo.description ?? '',
    language: repo.language ?? '',
    stars: repo.stargazers_count ?? null,
    createdAt: repo.created_at ? new Date(repo.created_at) : null,
  }));
}
