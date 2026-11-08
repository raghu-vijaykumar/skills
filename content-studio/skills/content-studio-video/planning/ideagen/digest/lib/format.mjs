const MAX_MESSAGE_LENGTH = 4000;

export function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function formatStars(count) {
  if (count == null) return '';
  if (count >= 1000) return `${(count / 1000).toFixed(count >= 10000 ? 0 : 1)}k`;
  return String(count);
}

export function formatDate(date, timezone) {
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: timezone,
  }).format(date);
}

function formatDay(date) {
  if (!date) return '';
  return new Intl.DateTimeFormat('en-US', {month: 'short', day: 'numeric'}).format(date);
}

function truncate(text, max = 140) {
  const flat = String(text).replace(/\s+/g, ' ').trim();
  return flat.length > max ? `${flat.slice(0, max - 1).trimEnd()}…` : flat;
}

function link(url, label) {
  return `<a href="${escapeHtml(url)}">${escapeHtml(label)}</a>`;
}

function renderFeedItems(items) {
  return items
    .map((item, index) => {
      const title = link(item.url, item.title);
      const meta = item.source ? `   <i>${escapeHtml(item.source)}</i>` : '';
      return `${index + 1}. ${title}${meta ? `\n${meta}` : ''}`;
    })
    .join('\n');
}

function renderPapers(papers) {
  return papers
    .map((paper, index) => {
      const title = link(paper.url, paper.title);
      const meta = [paper.metric, paper.source, paper.author ? `${paper.author} et al.` : '']
        .filter(Boolean)
        .join(' · ');
      return `${index + 1}. ${title}\n   <i>${escapeHtml(meta)}</i>`;
    })
    .join('\n');
}

function renderTrending(repos) {
  return repos
    .map((repo, index) => {
      const title = link(repo.url, repo.fullName);
      const meta = [];
      if (repo.language) meta.push(escapeHtml(repo.language));
      if (repo.starsToday) meta.push(`⭐ ${formatStars(repo.starsToday)} today`);
      else if (repo.stars) meta.push(`⭐ ${formatStars(repo.stars)}`);
      const metaLine = meta.length ? `\n   <i>${meta.join(' · ')}</i>` : '';
      const desc = repo.description ? `\n   <i>${escapeHtml(truncate(repo.description))}</i>` : '';
      return `${index + 1}. ${title}${metaLine}${desc}`;
    })
    .join('\n');
}

function renderNewRepos(repos) {
  return repos
    .map((repo, index) => {
      const title = link(repo.url, repo.fullName);
      const meta = [];
      if (repo.stars) meta.push(`⭐ ${formatStars(repo.stars)}`);
      if (repo.language) meta.push(escapeHtml(repo.language));
      if (repo.createdAt) meta.push(`created ${formatDay(repo.createdAt)}`);
      const metaLine = meta.length ? `\n   <i>${meta.join(' · ')}</i>` : '';
      const desc = repo.description ? `\n   <i>${escapeHtml(truncate(repo.description))}</i>` : '';
      return `${index + 1}. ${title}${metaLine}${desc}`;
    })
    .join('\n');
}

export function buildMessage({settings, sections, papers, github, since}) {
  const parts = [];
  parts.push(`<b>📡 ${escapeHtml(settings.title ?? 'Video Idea Digest')}</b>`);
  parts.push(`<i>${formatDate(new Date(), settings.timezone)}${since ? ` · since ${formatDate(since, settings.timezone)}` : ''}</i>`);

  for (const {topic, items} of sections) {
    if (items.length === 0) continue;
    const heading = [topic.emoji, escapeHtml(topic.label)].filter(Boolean).join(' ');
    parts.push('');
    parts.push(`<b>${heading}</b> <i>(${items.length})</i>`);
    parts.push(renderFeedItems(items));
  }

  if (papers?.length) {
    parts.push('');
    parts.push(`<b>🔥 Viral Research Papers</b> <i>(${papers.length})</i>`);
    parts.push(renderPapers(papers));
  }

  if (github) {
    if (github.trending?.length) {
      parts.push('');
      parts.push(`<b>🔥 GitHub Trending Today</b> <i>(${github.trending.length})</i>`);
      parts.push(renderTrending(github.trending));
    }
    if (github.newRepos?.length) {
      parts.push('');
      parts.push(`<b>🚀 New &amp; Viral Repos</b> <i>(${github.newRepos.length})</i>`);
      parts.push(renderNewRepos(github.newRepos));
    }
  }

  return parts.join('\n').trim();
}

export function splitMessage(text, maxLength = MAX_MESSAGE_LENGTH) {
  if (text.length <= maxLength) return [text];
  const chunks = [];
  let current = '';
  for (const line of text.split('\n')) {
    if (line.length > maxLength) {
      if (current) {
        chunks.push(current);
        current = '';
      }
      for (let i = 0; i < line.length; i += maxLength) {
        chunks.push(line.slice(i, i + maxLength));
      }
      continue;
    }
    const candidate = current ? `${current}\n${line}` : line;
    if (candidate.length > maxLength) {
      chunks.push(current);
      current = line;
    } else {
      current = candidate;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

export function countItems(sections, papers, github) {
  const feedCount = sections.reduce((sum, section) => sum + section.items.length, 0);
  const paperCount = papers?.length ?? 0;
  const githubCount = (github?.trending?.length ?? 0) + (github?.newRepos?.length ?? 0);
  return feedCount + paperCount + githubCount;
}
